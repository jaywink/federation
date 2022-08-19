from copy import copy
import json
import logging

from calamus import fields
from calamus.schema import JsonLDAnnotation, JsonLDSchema, JsonLDSchemaOpts
from calamus.utils import normalize_value
from marshmallow import pre_load, post_load, pre_dump, post_dump
from marshmallow.fields import Integer
from pyld import jsonld, documentloader

from federation.entities.activitypub.constants import NAMESPACE_PUBLIC
from federation.entities.activitypub.entities import (ActivitypubAccept, ActivitypubPost, ActivitypubComment, 
        ActivitypubProfile, ActivitypubImage, ActivitypubFollow, ActivitypubShare, ActivitypubRetraction)
from federation.entities.base import Image as BaseImage
from federation.entities.mixins import BaseEntity
from federation.utils.text import with_slash, validate_handle

logger = logging.getLogger("federation")


# This is required to workaround a bug in pyld that has the Accept header
# accept other content types. From what I understand, precedence handling
# is broken
# from https://github.com/digitalbazaar/pyld/issues/133
def myloader(*args, **kwargs):
    requests_loader = documentloader.requests.requests_document_loader(*args, **kwargs)
    
    def loader(url, options={}):
        options['headers']['Accept'] = 'application/ld+json'
        return requests_loader(url, options)
    
    return loader

jsonld.set_document_loader(myloader())


class AddedSchemaOpts(JsonLDSchemaOpts):
    def __init__(self, meta, *args, **kwargs):
        super().__init__(meta, *args, **kwargs)
        self.inherit_parent_types = False

JsonLDSchema.OPTIONS_CLASS = AddedSchemaOpts


# Not sure how exhaustive this needs to be...
as2 = fields.Namespace("https://www.w3.org/ns/activitystreams#")
dc = fields.Namespace("http://purl.org/dc/terms/")
diaspora = fields.Namespace("https://diasporafoundation.org/ns/")
ldp = fields.Namespace("http://www.w3.org/ns/ldp#")
litepub = fields.Namespace("http://litepub.social/ns#")
misskey = fields.Namespace("https://misskey-hub.net/ns#")
ostatus = fields.Namespace("http://ostatus.org#")
pt = fields.Namespace("https://joinpeertube.org/ns#")
pyfed = fields.Namespace("https://docs.jasonrobinson.me/ns/python-federation#")
schema = fields.Namespace("http://schema.org#")
sec = fields.Namespace("https://w3id.org/security#")
toot = fields.Namespace("http://joinmastodon.org/ns#")
vcard = fields.Namespace("http://www.w3.org/2006/vcard/ns#")
xsd = fields.Namespace("http://www.w3.org/2001/XMLSchema#")
zot = fields.Namespace("https://hubzilla.org/apschema#")


# Maybe this is food for an issue with calamus. pyld expands IRIs in an array,
# marshmallow then barfs with an invalid string value.
# Workaround: get rid of the array.
# Also, this implements the many attribute for IRI fields, sort of
class IRI(fields.IRI):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, list) and len(value) == 0: return value
        value = normalize_value(value)
        if isinstance(value, list):
            # no call to super() in list comprehensions...
            ret = []
            for val in value:
                v = super()._deserialize(val, attr, data, **kwargs)
                ret.append(v)
            return ret

        return super()._deserialize(value, attr, data, **kwargs)


# Don't want expanded IRIs to be exposed as dict keys
class Dict(fields.Dict):
    ctx = ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1"]

    # may or may not be needed
    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, dict):
            value['@context'] = self.ctx
            value = jsonld.expand(value)[0]
        return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        ret = super()._deserialize(value, attr, data, **kwargs)
        ret = jsonld.compact(ret, self.ctx)
        ret.pop('@context')
        return ret


# calamus sets a XMLSchema#integer type, but different definitions
# maybe used, hence the flavor property
# TODO: handle non negative types
class Integer(fields._JsonLDField, Integer):
    flavor = None  # add fields.IRIReference type hint 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flavor = kwargs.get('flavor')

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        flavor = str(self.flavor) if self.flavor else "http://www.w3.org/2001/XMLSchema#integer"
        if self.parent.opts.add_value_types or self.add_value_types:
            value = {"@value": value, "@type": flavor}
        return value


# calamus doesn't implement json-ld langage maps
class LanguageMap(Dict):
    def _serialize(self, value, attr, obj, **kwargs):
        ret = super()._serialize(value, attr, obj, **kwargs)
        if not ret: return ret
        value = []
        for k,v in ret.items():
            if k == 'orig':
                value.append({'@value':v})
            else:
                value.append({'@language': k, '@value':v})

        return value

    def _deserialize(self, value, attr, data, **kwargs):
        ret = {}
        for i,c in enumerate(value):
            lang = c.pop('@language', None)
            lang = '_:'+lang if lang else '_:orig' 
            ret[lang] = [c]
        return super()._deserialize(ret, attr, data, **kwargs)


class MixedField(fields.Nested):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iri = IRI(self.field_name, add_value_types=False)

    def _bind_to_schema(self, field_name, schema):
        super()._bind_to_schema(field_name, schema)
        self.iri.parent = self.parent

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, str) or (
                isinstance(value, list) and len(value) > 0 and isinstance(value[0], str)):
            return self.iri._serialize(value, attr, obj, **kwargs)
        else:
            return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        # this is just so the ACTIVITYPUB_POST_OBJECT_IMAGES test payload passes
        if len(value) == 0: return value

        if value[0] == {}: return None
        if value[0].get('@type'):
            return super()._deserialize(value, attr, data, **kwargs)
        return self.iri._deserialize(value, attr, data, **kwargs)
        

OBJECTS = [
        'AnnounceSchema',
        'ArticleSchema',
        'FollowSchema',
        'LikeSchema',
        'NoteSchema',
        'PageSchema',
        'TombstoneSchema',
        'VideoSchema'
]


def set_public(entity):
    for attr in [getattr(entity, 'to', []), getattr(entity, 'cc' ,[])]:
        if isinstance(attr, list):
            if NAMESPACE_PUBLIC in attr: entity.public = True
        elif attr == NAMESPACE_PUBLIC: entity.public = True


class Object(metaclass=JsonLDAnnotation):
    atom_url = fields.String(ostatus.atomUri)
    also_known_as = IRI(as2.alsoKnownAs)
    icon = MixedField(as2.icon, nested='ImageSchema', many=True)
    image = MixedField(as2.image, nested='ImageSchema', many=True)
    tag_list = MixedField(as2.tag, nested=['HashtagSchema','MentionSchema','PropertyValueSchema','EmojiSchema'], many=True)
    _children = MixedField(as2.attachment, nested=['ImageSchema', 'DocumentSchema','PropertyValueSchema','IdentityProofSchema'], many=True)
    #audience
    content_map = LanguageMap(as2.content)  # language maps are not implemented in calamus
    context = IRI(as2.context)
    guid = fields.String(diaspora.guid)
    name = fields.String(as2.name)
    #endtime
    generator = MixedField(as2.generator, nested='ServiceSchema')
    #generator = Dict(as2.generator)
    #location
    #preview
    created_at = fields.DateTime(as2.published, add_value_types=True)
    replies = MixedField(as2.replies, nested=['CollectionSchema','OrderedCollectionSchema'])
    signature = MixedField(sec.signature, nested = 'SignatureSchema')
    start_time = fields.DateTime(as2.startTime, add_value_types=True)
    updated = fields.DateTime(as2.updated, add_value_types=True)
    to = IRI(as2.to)
    #bto
    cc = IRI(as2.cc)
    #bcc
    media_type = fields.String(as2.mediaType)
    #duration
    sensitive = fields.Boolean(as2.sensitive)
    source = Dict(as2.source)

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k): 
                setattr(self, k, v)
        self.has_schema = True

    # noop to avoid isinstance tests
    def to_base(self):
        return self

    class Meta:
        rdf_type = as2.Object

        @pre_load
        def update_context(self, data, **kwargs):
            if not data.get('@context'): return data
            ctx = data['@context']

            # add a # at the end of the python-federation string
            # for socialhome payloads
            s = json.dumps(ctx)
            if 'python-federation"' in s:
                ctx = json.loads(s.replace('python-federation', 'python-federation#', 1))
                data['@context'] = ctx
        
            if not isinstance(ctx, list):
                ctx = [ctx, {}]
            saved_ctx = copy(ctx)

            # AP activities may be signed, but most platforms don't
            # define RsaSignature2017. add it to the context
            # hubzilla doesn't define the discoverable property in its context
            to_add = {'signature': ['https://w3id.org/security/v1', {'sec':'https://w3id.org/security#','RsaSignature2017':'sec:RsaSignature2017'}],
                    'discoverable': [{'toot':'http://joinmastodon.org/ns#','discoverable': 'toot:discoverable'}], #for hubzilla
                    'copiedTo': [{'toot':'http://joinmastodon.org/ns#','copiedTo': 'toot:copiedTo'}], #for hubzilla
                    'featured': [{'toot':'http://joinmastodon.org/ns#','featured': 'toot:featured'}] #for litepub
                    }

            idx = [i for i,v in enumerate(ctx) if isinstance(v, dict)]

            for key,val in to_add.items():
                if not data.get(key): continue
                for item in val:
                    if isinstance(item, str) and item not in ctx:
                        ctx.append(item)
                    elif isinstance(item, dict):
                        for akey, aval in item.items():
                            found = False
                            for i in idx:
                                if ctx[i].get(aval):
                                    found = True
                                    break
                            if not found: 
                                ctx[idx[0]][akey] = aval

            if saved_ctx != ctx: 
                data['@context'] = ctx
            return data

        # A node without an id isn't true json-ld, but many payloads have
        # id-less nodes. Since calamus forces random ids on such nodes, 
        # this removes it.
        @post_dump
        def noid(self, data, **kwargs):
            if data['@id'].startswith('_:'): data.pop('@id')
            return data


class Home(metaclass=JsonLDAnnotation):
    country_name = fields.String(fields.IRIReference("http://www.w3.org/2006/vcard/ns#","country-name"))
    region = fields.String(vcard.region)
    locality = fields.String(vcard.locality)

    class Meta:
        rdf_type = vcard.Home


class List(fields.List):
    def _deserialize(self,value, attr, data, **kwargs):
        value = normalize_value(value)
        return super()._deserialize(value,attr,data,**kwargs)


class Collection(Object):
    #items = MixedField(as2.items, nested=OBJECTS, many=True)
    items = List(as2.items, cls_or_instance=IRI())
    first = MixedField(as2.first, nested=['CollectionPageSchema', 'OrderedCollectionPageSchema'])
    current = IRI(as2.current)
    last = IRI(as2.last)
    total_items = Integer(as2.totalItems, flavor=xsd.nonNegativeInteger, add_value_types=True)

    class Meta:
        rdf_type = as2.Collection


class OrderedCollection(Collection):
    class Meta:
        rdf_type = as2.OrderedCollection


class CollectionPage(Collection):
    part_of = IRI(as2.partOf)
    next_ = IRI(as2.next)
    prev = IRI(as2.prev)

    class Meta:
        rdf_type = as2.CollectionPage


class OrderedCollectionPage(CollectionPage):
    #orderedItems = MixedField(as2.orderedItems, nested=OBJECTS, many=True)
    #orderedItems = fields.List(as2.orderedItems, cls_or_instance=MixedField(as2.items, nested=OBJECTS), ordered=True)
    start_index = Integer(as2.startIndex, flavor=xsd.nonNegativeInteger, add_value_types=True)

    class Meta:
        rdf_type = as2.OrderedCollectionPage
        

# This mimics that federation currently handles AP Document as AP Image
# AP defines [Ii]mage and [Aa]udio objects/properties, but only a Video object
# seen with Peertube payloads only so far
class Document(Object):
    inline = fields.Boolean(pyfed.inlineImage)
    height = Integer(as2.height, flavor=xsd.nonNegativeInteger, add_value_types=True)
    width = Integer(as2.width, flavor=xsd.nonNegativeInteger, add_value_types=True)
    blurhash = fields.String(toot.blurhash)
    url = MixedField(as2.url, nested='LinkSchema', many=True)

    def to_base(self):
        if getattr(self, 'media_type', None) in BaseImage._valid_media_types:
            return ActivitypubImage(**self.__dict__)
        return None # until more medias are supported
        
    class Meta:
        rdf_type = as2.Document


class Image(Document):
    @classmethod
    def from_base(cls, entity):
        return cls(**entity.__dict__)

    class Meta:
        rdf_type = as2.Image


class Infohash(Object):
    name = fields.String(as2.name)

    class Meta:
        rdf_type = pt.Infohash


class Link(metaclass=JsonLDAnnotation):
    href = IRI(as2.href)
    rel = fields.List(as2.rel, cls_or_instance=fields.String(as2.rel))
    media_type = fields.String(as2.mediaType)
    name = fields.String(as2.name)
    href_lang = fields.String(as2.hrefLang)
    height = Integer(as2.height, flavor=xsd.nonNegativeInteger, add_value_types=True)
    width = Integer(as2.width, flavor=xsd.nonNegativeInteger, add_value_types=True)
    fps = Integer(pt.fps, flavor=schema.Number, add_value_types=True)
    size = Integer(pt.size, flavor=schema.Number, add_value_types=True)
    #preview : variable type?
    tag = MixedField(as2.tag, nested=['InfohashSchema', 'LinkSchema'], many=True)

    class Meta:
        rdf_type = as2.Link

        @post_load
        def make_instance(self, data, **kwargs):
            data.pop('@id', None)
            return super().make_instance(data, **kwargs)


class Hashtag(Link):

    class Meta:
        rdf_type = as2.Hashtag


class Mention(Link):

    class Meta:
        rdf_type = as2.Mention


class PropertyValue(Object):
    name = fields.String(as2.name)
    value = fields.String(schema.value)

    class Meta:
        rdf_type = schema.PropertyValue


class IdentityProof(Object):
    signature_value = fields.String(sec.signatureValue)
    signing_algorithm = fields.String(sec.signingAlgorithm)

    class Meta:
        rdf_type = toot.IdentityProof


class Emoji(Object):

    class Meta:
        rdf_type = toot.Emoji


class Person(Object):
    id = fields.Id()
    inbox = IRI(ldp.inbox)
    outbox = IRI(as2.outbox)
    following = IRI(as2.following)
    followers = IRI(as2.followers)
    #liked is a collection
    #streams
    username = fields.String(as2.preferredUsername)
    endpoints = Dict(as2.endpoints)
    shared_inbox = IRI(as2.sharedInbox) # misskey adds this
    #proxyUrl
    #oauthAuthorizationEndpoint
    #oauthTokenEndpoint
    #provideClientKey
    #signClientKey
    url = IRI(as2.url)
    playlists = IRI(pt.playlists)
    featured = IRI(toot.featured)
    featuredTags = IRI(toot.featuredTags)
    manuallyApprovesFollowers = fields.Boolean(as2.manuallyApprovesFollowers, dump_default=False)
    discoverable = fields.Boolean(toot.discoverable)
    devices = IRI(toot.devices)
    public_key_dict = Dict(sec.publicKey)
    guid = fields.String(diaspora.guid)
    handle = fields.String(diaspora.handle)
    raw_content = fields.String(as2.summary)
    has_address = MixedField(vcard.hasAddress, nested='HomeSchema')
    has_instant_message = fields.List(vcard.hasInstantMessage, cls_or_instance=fields.String)
    address = fields.String(vcard.Address)
    is_cat = fields.Boolean(misskey.isCat)
    moved_to = IRI(as2.movedTo)
    copied_to = IRI(toot.copiedTo)
    capabilities = Dict(litepub.capabilities)

    @classmethod
    def from_base(cls, entity):
        ret = cls(**entity.__dict__)
        if not hasattr(entity, 'inboxes'): return ret

        ret.inbox = entity.inboxes["private"]
        ret.outbox = f"{with_slash(ret.id)}outbox/"
        ret.followers = f"{with_slash(ret.id)}followers/"
        ret.following = f"{with_slash(ret.id)}following/"
        ret.endpoints = {'sharedInbox': entity.inboxes["public"]}
        ret.public_key_dict = {
                "id": f"{ret.id}#main-key",
                "owner": ret.id,
                "publicKeyPem": entity.public_key
                }
        if entity.image_urls.get('large'):
            try:
                profile_icon = ActivitypubImage(url=entity.image_urls.get('large'))
                if profile_icon.media_type:
                    ret.icon = [Image.from_base(profile_icon)]
            except Exception as ex:
                logger.warning("ActivitypubProfile.to_as2 - failed to set profile icon: %s", ex)

        return ret

    def to_base(self):
        entity = ActivitypubProfile(**self.__dict__)
        entity.inboxes = {
                'private': getattr(self, 'inbox', None), 
                'public': getattr(self,'endpoints',None).get('sharedInbox', None) or getattr(self,'shared_inbox',None)
                }
        entity.public_key = getattr(self,'public_key_dict',None).get('publicKeyPem', None)
        entity.image_urls = {}
        if hasattr(self, 'icon') and isinstance(self.icon, list):
            entity.image_urls = {
                'small': self.icon[0].url,
                'medium': self.icon[0].url,
                'large': self.icon[0].url
                }

        set_public(entity)
        return entity

    class Meta:
        rdf_type = as2.Person


class Group(Person):

    class Meta:
        rdf_type = as2.Group


class Application(Person):
    class Meta:
        rdf_type = as2.Application


class Organization(Person):
    class Meta:
        rdf_type = as2.Organization


class Service(Person):
    class Meta:
        rdf_type = as2.Service


# The to_base method is used to handle cases where an AP object type matches multiple
# classes depending on the existence/value of specific propertie(s) or
# when the same class is used both as an object or an activity or
# when a property can't be directly deserialized from the payload.
# calamus Nested field can't handle using the same model
# or the same type in multiple schemas
class Note(Object):
    id = fields.Id()
    actor_id = IRI(as2.attributedTo)
    target_id = IRI(as2.inReplyTo)
    conversation = fields.String(ostatus.conversation)
    in_reply_to_atom_uri = IRI(ostatus.inReplyToAtomUri)
    summary = fields.String(as2.summary)
    url = IRI(as2.url)

    def to_base(self):
        entity = ActivitypubComment(**self.__dict__) if getattr(self, 'target_id') else ActivitypubPost(**self.__dict__)

        if hasattr(self, 'content_map'):
            entity._rendered_content = self.content_map.get('orig', "").strip()
            if getattr(self, 'source') and self.source.get('mediaType') == 'text/markdown':
                entity._media_type = self.source['mediaType']
                entity.raw_content = self.source.get('content').strip()
            else:
                entity._media_type = 'text/html'
                entity.raw_content = self.content_map.get('orig', "")

        if isinstance(getattr(entity, '_children', None), list):
            children = []
            for child in entity._children:
                img = child.to_base()
                if img: children.append(img)
            entity._children = children

        set_public(entity)
        return entity

    class Meta:
        rdf_type = as2.Note


class Article(Note):
    class Meta:
        rdf_type = as2.Article


class Page(Note):
    class Meta:
        rdf_type = as2.Page


# peertube uses a lot of properties differently...
class Video(Document):
    actor_id = MixedField(as2.attributedTo, nested=['PersonSchema', 'GroupSchema'], many=True)

    class Meta:
        unknown = 'EXCLUDE' # required until all the pt fields are defined
        rdf_type = as2.Video

    def to_base(self):
        return self


class Signature(Object):
    created = fields.DateTime(dc.created, add_value_types=True)
    creator = IRI(dc.creator)
    key = fields.String(sec.signatureValue)
    nonce = fields.String(sec.nonce)

    class Meta:
        rdf_type = sec.RsaSignature2017


class Activity(Object):
    actor_id = IRI(as2.actor)
    #target_id = IRI(as2.target)
    #result
    #origin
    instrument = MixedField(as2.instrument, nested='ServiceSchema')

    def __init__(self, *args, **kwargs):
        self.activity = self
        super().__init__(*args, **kwargs)

    class Meta:
        rdf_type = as2.Activity

    
class Follow(Activity):
    activity_id = fields.Id()
    target_id = IRI(as2.object)

    def to_base(self):
        entity = ActivitypubFollow(**self.__dict__)
        # This is assuming Follow can only be the object of an Undo activity. Lazy.
        if self.activity != self: 
            entity.following = False

        return entity

    class Meta:
        rdf_type = as2.Follow


class Announce(Activity):
    id = fields.Id()
    target_id = IRI(as2.object)

    def to_base(self):
        if self.activity == self:
            entity = ActivitypubShare(**self.__dict__)
        else:
            self.target_id = self.id
            self.entity_type = 'Object'
            entity = ActivitypubRetraction(**self.__dict__)

        set_public(entity)
        return entity

    class Meta:
        rdf_type = as2.Announce
    

class Tombstone(Object):
    target_id = fields.Id()

    def to_base(self):
        if self.activity != self: self.actor_id = self.activity.actor_id
        self.entity_type = 'Object'
        return ActivitypubRetraction(**self.__dict__)

    class Meta:
        rdf_type = as2.Tombstone


class Create(Activity):
    activity_id = fields.Id()
    object_ = MixedField(as2.object, nested=OBJECTS)

    class Meta:
        rdf_type = as2.Create


class Like(Create):
    like = fields.String(diaspora.like)

    class Meta:
        rdf_type = as2.Like


# inbound Accept is a noop...
class Accept(Create):
    def to_base(self):
        del self.object_
        return ActivitypubAccept(**self.__dict__)

    class Meta:
        rdf_type = as2.Accept


class Delete(Create):
    def to_base(self):
        if hasattr(self, 'object_') and not isinstance(self.object_, Tombstone):
            self.target_id = self.object_
            return ActivitypubRetraction(**self.__dict__)

    class Meta:
        rdf_type = as2.Delete


class Update(Create):
    class Meta:
        rdf_type = as2.Update


class Undo(Create):
    class Meta:
        rdf_type = as2.Undo


class View(Create):
    class Meta:
        rdf_type = as2.View


def model_to_objects(payload):
    model = globals().get(payload.get('type'))
    if model and issubclass(model, Object):
        try:
            entity = model.schema().load(payload)
        except jsonld.JsonLdError:  # Just give up for now. This must be made robust
            logger.warning("Invalid jsonld payload, falling through mappers for now")
            return None

        if hasattr(entity, 'object_') and (isinstance(entity.object_, Object) or isinstance(entity.object_, BaseEntity)):
            entity.object_.activity = entity
            entity = entity.object_
    
        return entity.to_base()
    return None
