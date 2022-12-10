from copy import copy
import json
import logging
from typing import List, Callable, Dict, Union, Optional
from urllib.parse import urlparse
import uuid

import bleach
from calamus import fields
from calamus.schema import JsonLDAnnotation, JsonLDSchema, JsonLDSchemaOpts
from calamus.utils import normalize_value
from marshmallow import exceptions, pre_load, post_load, pre_dump, post_dump
from marshmallow.fields import Integer
from marshmallow.utils import EXCLUDE, missing
from pyld import jsonld
import requests_cache as rc

from federation.entities.activitypub.constants import CONTEXT, CONTEXT_SETS, NAMESPACE_PUBLIC
from federation.entities.mixins import BaseEntity, RawContentMixin
from federation.entities.utils import get_base_attributes, get_profile
from federation.outbound import handle_send
from federation.types import UserType, ReceiverVariant
from federation.utils.activitypub import retrieve_and_parse_document, retrieve_and_parse_profile, get_profile_id_from_webfinger
from federation.utils.text import with_slash, validate_handle
import federation.entities.base as base

logger = logging.getLogger("federation")
    
# Make django federation parameters globally available
# if possible
try:
    from federation.utils.django import get_configuration
    django_params = get_configuration()
except ImportError:
    django_params = {}

# try to obtain redis config from django and use as
# requests_cache backend if available
if django_params.get('redis'):
    backend = rc.RedisCache(namespace='fed_cache', **django_params['redis'])
else:
    backend = rc.SQLiteCache(db_path='fed_cache')
logger.info('Using %s for requests_cache', type(backend))
    

# This is required to workaround a bug in pyld that has the Accept header
# accept other content types. From what I understand, precedence handling
# is broken
# from https://github.com/digitalbazaar/pyld/issues/133
def get_loader(*args, **kwargs):
    requests_loader = jsonld.requests_document_loader(*args, **kwargs)
    
    def loader(url, options={}):
        options['headers']['Accept'] = 'application/ld+json'
        with rc.enabled(cache_name='fed_cache', backend=backend):
            return requests_loader(url, options)
    
    return loader

jsonld.set_document_loader(get_loader())


def get_profile_or_entity(fid):
    obj = get_profile(fid=fid)
    if not obj:
        with rc.enabled(cache_name='fed_cache', backend=backend):
            obj = retrieve_and_parse_document(fid)
    return obj
    

class AddedSchemaOpts(JsonLDSchemaOpts):
    def __init__(self, meta, *args, **kwargs):
        super().__init__(meta, *args, **kwargs)
        self.inherit_parent_types = False
        self.unknown = EXCLUDE

JsonLDSchema.OPTIONS_CLASS = AddedSchemaOpts


def isoformat(value):
    return value.isoformat(timespec='seconds')
fields.DateTime.SERIALIZATION_FUNCS['iso'] = isoformat


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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dump_derived = kwargs.get('dump_derived')

    def _serialize(self, value, attr, data, **kwargs):
        if not value and isinstance(self.dump_derived, dict):
            fields = {f: getattr(data, f) for f in self.dump_derived['fields']}
            value = self.dump_derived['fmt'].format(**fields)

        return super()._serialize(value, attr, data, **kwargs)

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


class NormalizedList(fields.List):
    def _deserialize(self,value, attr, data, **kwargs):
        value = normalize_value(value)
        ret = super()._deserialize(value,attr,data,**kwargs)
        return ret


# Don't want expanded IRIs to be exposed as dict keys
class CompactedDict(fields.Dict):
    ctx = ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1"]

    # may or may not be needed
    def _serialize(self, value, attr, obj, **kwargs):
        if value and isinstance(value, dict):
            value['@context'] = self.ctx
            value = jsonld.expand(value)
            if value and isinstance(value, list): value = value[0]
        return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        # HACK: "promote" a Pleroma source field by adding content
        # and mediaType as2 properties
        if attr == str(as2.source):
            if isinstance(value, list) and str(as2.content) not in value[0].keys():
                value = [{str(as2.content): value, str(as2.mediaType): 'text/plain'}]
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
class LanguageMap(CompactedDict):
    def _serialize(self, value, attr, obj, **kwargs):
        if not value: return None
        ret = []
        for k,v in value.items():
            if k == 'orig':
                ret.append(v)
            else:
                ret.append({'@language': k, '@value':v})
        return ret

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

    def _serialize_single_obj(self, obj, **kwargs):
        return super()._serialize_single_obj(obj, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, str) or (
                isinstance(value, list) and len(value) > 0 and isinstance(value[0], str)):
            return self.iri._serialize(value, attr, obj, **kwargs)
        else:
            #value = value[0] if isinstance(value, list) and len(value) == 1 else value
            if isinstance(value, list) and len(value) == 0: value = None
            return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        # this is just so the ACTIVITYPUB_POST_OBJECT_IMAGES test payload passes
        if len(value) == 0: return value

        if isinstance(value, list):
            if value[0] == {}: return {}
        else:
            value = [value]


        ret = []
        for item in value:
            if item.get('@type'):
                res = super()._deserialize(item, attr, data, **kwargs)
                ret.append(res if not isinstance(res, list) else res[0])
            else:
                ret.append(self.iri._deserialize(item, attr, data, **kwargs))

        return ret if len(ret) > 1 or self.many else ret[0]
        

OBJECTS = [
        'AnnounceSchema',
        'ApplicationSchema',
        'ArticleSchema',
        'FollowSchema',
        'GroupSchema',
        'LikeSchema',
        'NoteSchema',
        'OrganizationSchema',
        'PageSchema',
        'PersonSchema',
        'ServiceSchema',
        'TombstoneSchema',
        'VideoSchema'
]


def set_public(entity):
    for attr in [getattr(entity, 'to', []), getattr(entity, 'cc' ,[])]:
        if isinstance(attr, list):
            if NAMESPACE_PUBLIC in attr: entity.public = True
        elif attr == NAMESPACE_PUBLIC: entity.public = True


def add_props_to_attrs(obj, props):
    return obj.__dict__
    attrs = copy(obj.__dict__)
    for prop in props:
        attrs.update({prop: getattr(obj, prop, None)})
        attrs.pop('_'+prop, None)
    attrs.update({'schema': True})
    return attrs


class Object(BaseEntity, metaclass=JsonLDAnnotation):
    atom_url = fields.String(ostatus.atomUri)
    also_known_as = IRI(as2.alsoKnownAs)
    icon = MixedField(as2.icon, nested='ImageSchema')
    image = MixedField(as2.image, nested='ImageSchema', default='')
    tag_objects = MixedField(as2.tag, nested=['HashtagSchema','MentionSchema','PropertyValueSchema','EmojiSchema'], many=True)
    attachment = fields.Nested(as2.attachment, nested=['ImageSchema', 'AudioSchema', 'DocumentSchema','PropertyValueSchema','IdentityProofSchema'], many=True)
    content_map = LanguageMap(as2.content)  # language maps are not implemented in calamus
    context = IRI(as2.context)
    guid = fields.String(diaspora.guid, default='')
    handle = fields.String(diaspora.handle, default='')
    name = fields.String(as2.name, default='')
    generator = MixedField(as2.generator, nested=['ApplicationSchema','ServiceSchema'])
    created_at = fields.DateTime(as2.published, add_value_types=True)
    replies = MixedField(as2.replies, nested=['CollectionSchema','OrderedCollectionSchema'])
    signature = MixedField(sec.signature, nested = 'SignatureSchema')
    start_time = fields.DateTime(as2.startTime, add_value_types=True)
    updated = fields.DateTime(as2.updated, add_value_types=True)
    to = fields.List(as2.to, cls_or_instance=fields.String(as2.to))
    cc = fields.List(as2.cc, cls_or_instance=fields.String(as2.cc))
    media_type = fields.String(as2.mediaType)
    source = CompactedDict(as2.source)

    # The following properties are defined by some platforms, but are not implemented yet
    #audience
    #endtime
    #location
    #preview
    #bto
    #bcc
    #duration

    def to_as2(self):
        obj = self.activity if isinstance(self.activity, Activity) else self
        return jsonld.compact(obj.dump(), CONTEXT)

    @classmethod
    def from_base(cls, entity):
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    # Before validation, assign None to fields that are set to marshmallow.missing
    # Setting missing fields to marshmallow.missing starts with calamus 0.4.1
    # TODO: rework validation
    def validate(self, direction='inbound'):
        if direction == 'inbound':
            for attr in type(self).schema().load_fields.keys():
                if getattr(self, attr) is missing:
                    setattr(self, attr, None)

        super().validate(direction)

    def to_string(self):
        # noinspection PyUnresolvedReferences
        return str(self.to_as2())

    class Meta:
        rdf_type = as2.Object

        @pre_load
        def patch_context(self, data, **kwargs):
            if not data.get('@context'): return data
            ctx = copy(data['@context'])

            # One platform send a single string context
            if isinstance(ctx, str): ctx = [ctx]

            # add a # at the end of the python-federation string
            # for socialhome payloads
            s = json.dumps(ctx)
            if 'python-federation"' in s:
                ctx = json.loads(s.replace('python-federation', 'python-federation#', 1))

            # some paltforms have http://joinmastodon.com/ns in @context. This
            # is not a json-ld document.
            try:
                ctx.pop(ctx.index('http://joinmastodon.org/ns'))
            except:
                pass

            # remove @language in context since this directive is not
            # processed by calamus. Pleroma adds a useless @language: 'und'
            # which is discouraged in best practices and in some cases makes 
            # calamus return dict where str is expected.
            # see https://www.rfc-editor.org/rfc/rfc5646, page 56
            idx = []
            for i,v in enumerate(ctx):
                if isinstance(v, dict): 
                    v.pop('@language',None)
                    if len(v) == 0: idx.insert(0, i)
            for i in idx: ctx.pop(i)

            # AP activities may be signed, but most platforms don't
            # define RsaSignature2017. add it to the context
            # hubzilla doesn't define the discoverable property in its context
            may_add = {'signature': ['https://w3id.org/security/v1', {'sec':'https://w3id.org/security#','RsaSignature2017':'sec:RsaSignature2017'}],
                    'publicKey': ['https://w3id.org/security/v1'],
                    'discoverable': [{'toot':'http://joinmastodon.org/ns#','discoverable': 'toot:discoverable'}], #for hubzilla
                    'copiedTo': [{'toot':'http://joinmastodon.org/ns#','copiedTo': 'toot:copiedTo'}], #for hubzilla
                    'featured': [{'toot':'http://joinmastodon.org/ns#','featured': 'toot:featured'}], #for litepub and pleroma
                    'tag': [{'Hashtag': 'as:Hashtag'}], #for epicyon
                    'attachment': [{'schema': 'http://schema.org#', 'PropertyValue': 'schema:PropertyValue'}] # for owncast
                    }

            to_add = [val for key,val in may_add.items() if data.get(key)]
            if to_add:
                idx = [i for i,v in enumerate(ctx) if isinstance(v, dict)]
                if idx:
                    upd = ctx[idx[0]]
                    # merge context dicts
                    if len(idx) > 1:
                        idx.reverse()
                        for i in idx[:-1]:
                            upd.update(ctx[i])
                            ctx.pop(i)
                else:
                    upd = {}

                for add in to_add:
                    for val in add:
                        if isinstance(val, str) and val not in ctx:
                            try:
                                ctx.append(val)
                            except AttributeError:
                                ctx = [ctx, val]
                        if isinstance(val, dict):
                            upd.update(val)
                if not idx and upd: ctx.append(upd)
            
            # for to and cc fields to be processed as strings
            ctx.append(CONTEXT_SETS)
            data['@context'] = ctx
            return data

        # A node without an id isn't true json-ld, but many payloads have
        # id-less nodes. Since calamus forces random ids on such nodes, 
        # this removes it.
        @post_dump
        def noid(self, data, **kwargs):
            if data['@id'].startswith('_:'): data.pop('@id')
            return data

        @post_dump
        def sanitize(self, data, **kwargs):
            return {k: v for k,v in data.items() if v or isinstance(v, bool)}

class Home(metaclass=JsonLDAnnotation):
    country_name = fields.String(fields.IRIReference("http://www.w3.org/2006/vcard/ns#","country-name"))
    region = fields.String(vcard.region)
    locality = fields.String(vcard.locality)

    class Meta:
        rdf_type = vcard.Home


class Collection(Object, base.Collection):
    id = fields.Id()
    items = MixedField(as2.items, nested=OBJECTS, many=True)
    first = MixedField(as2.first, nested=['CollectionPageSchema', 'OrderedCollectionPageSchema'])
    current = IRI(as2.current)
    last = IRI(as2.last)
    total_items = Integer(as2.totalItems, flavor=xsd.nonNegativeInteger, add_value_types=True)

    class Meta:
        rdf_type = as2.Collection


class OrderedCollection(Collection):
    items = NormalizedList(as2.items, cls_or_instance=MixedField(as2.items, nested=OBJECTS))

    class Meta:
        rdf_type = as2.OrderedCollection


class CollectionPage(Collection):
    part_of = IRI(as2.partOf)
    next_ = IRI(as2.next)
    prev = IRI(as2.prev)

    class Meta:
        rdf_type = as2.CollectionPage


class OrderedCollectionPage(OrderedCollection, CollectionPage):
    start_index = Integer(as2.startIndex, flavor=xsd.nonNegativeInteger, add_value_types=True)

    class Meta:
        rdf_type = as2.OrderedCollectionPage
        

# This mimics that federation currently handles AP Document as AP Image
# AP defines [Ii]mage and [Aa]udio objects/properties, but only a Video object
# seen with Peertube payloads only so far
class Document(Object):
    inline = fields.Boolean(pyfed.inlineImage, default=False)
    height = Integer(as2.height, default=0, flavor=xsd.nonNegativeInteger, add_value_types=True)
    width = Integer(as2.width, default=0, flavor=xsd.nonNegativeInteger, add_value_types=True)
    blurhash = fields.String(toot.blurhash)
    url = MixedField(as2.url, nested='LinkSchema')

    def to_base(self):
        self.__dict__.update({'schema': True})
        if self.media_type.startswith('image'):
            return Image(**get_base_attributes(self))
        if self.media_type.startswith('audio'):
            return Audio(**get_base_attributes(self))
        if self.media_type.startswith('video'):
            return Video(**get_base_attributes(self))
        return self # what was that?
        
    class Meta:
        rdf_type = as2.Document
        fields = ('image', 'url', 'name', 'media_type', 'inline')


class Image(Document, base.Image):
    def to_base(self):
        return self

    class Meta:
        rdf_type = as2.Image
        fields = ('image', 'url', 'name', 'media_type', 'inline')

# haven't seen this one so far..
class Audio(Document, base.Audio):
    def to_base(self):
        return self

    class Meta:
        rdf_type = as2.Audio
        fields = ('image', 'url', 'name', 'media_type', 'inline')

class Infohash(Object):

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
    tag = MixedField(as2.tag, nested=['InfohashSchema', 'LinkSchema'], many=True)
    # Not implemented yet
    #preview : variable type?

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    class Meta:
        rdf_type = as2.Link

        @post_dump
        def noid(self, data, **kwargs):
            if data['@id'].startswith('_:'): data.pop('@id')
            return data

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


class Person(Object, base.Profile):
    id = fields.Id()
    inbox = IRI(ldp.inbox)
    outbox = IRI(as2.outbox)
    following = IRI(as2.following)
    followers = IRI(as2.followers)
    username = fields.String(as2.preferredUsername)
    endpoints = CompactedDict(as2.endpoints)
    shared_inbox = IRI(as2.sharedInbox) # misskey adds this
    url = IRI(as2.url)
    playlists = IRI(pt.playlists)
    featured = IRI(toot.featured)
    featuredTags = IRI(toot.featuredTags)
    manuallyApprovesFollowers = fields.Boolean(as2.manuallyApprovesFollowers, default=False)
    discoverable = fields.Boolean(toot.discoverable)
    devices = IRI(toot.devices)
    public_key_dict = CompactedDict(sec.publicKey)
    raw_content = fields.String(as2.summary, default="")
    has_address = MixedField(vcard.hasAddress, nested='HomeSchema')
    has_instant_message = fields.List(vcard.hasInstantMessage, cls_or_instance=fields.String)
    address = fields.String(vcard.Address)
    is_cat = fields.Boolean(misskey.isCat)
    moved_to = IRI(as2.movedTo)
    copied_to = IRI(toot.copiedTo)
    capabilities = CompactedDict(litepub.capabilities)
    suspended = fields.Boolean(toot.suspended)
    public = True
    _cached_inboxes = None
    _cached_public_key = None
    _cached_image_urls = None
    _media_type = 'text/plain' # embedded_images shouldn't parse the profile summary

    # Not implemented yet
    #liked is a collection
    #streams
    #proxyUrl
    #oauthAuthorizationEndpoint
    #oauthTokenEndpoint
    #provideClientKey
    #signClientKey

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._allowed_children += (PropertyValue, IdentityProof)

    # Set handle to username@host if not provided by the platform
    def post_receive(self):
        if not self.finger:
            domain = urlparse(self.id).netloc
            finger = f'{self.username.lower()}@{domain}'
            with rc.enabled(cache_name='fed_cache', backend=backend):
                if get_profile_id_from_webfinger(finger) == self.id:
                    self.finger = finger
        if self.guid and not self.handle:
            self.handle = self.finger

    def to_as2(self):
        self.followers = f'{with_slash(self.id)}followers/'
        self.following = f'{with_slash(self.id)}following/'
        self.outbox = f'{with_slash(self.id)}outbox/'

        if hasattr(self, 'times'):
            if self.times.get('updated',0) > self.times.get('created',0):
                self.updated = self.times.get('updated')
            if self.times.get('edited'):
                self.activity = Update(
                        activity_id=f'{self.id}#profile-{uuid.uuid4()}',
                        actor_id=self.id,
                        created_at=self.times.get('updated'),
                        object_=self,
                        to=self.to,
                        )
        return super().to_as2()

    @property
    def inboxes(self):
        self._cached_inboxes['private'] = getattr(self, 'inbox', None)
        if hasattr(self, 'endpoints') and isinstance(self.endpoints, dict):
            self._cached_inboxes['public'] = self.endpoints.get('sharedInbox', None)
        else:
            self._cached_inboxes['public'] = getattr(self,'shared_inbox',None)
        return self._cached_inboxes

    @inboxes.setter
    def inboxes(self, value):
        self._cached_inboxes = value
        if isinstance(value, dict):
            self.inbox = value.get('private', None)
            self.endpoints = {'sharedInbox': value.get('public', None)}

    @property
    def public_key(self):
        if self._cached_public_key: return self._cached_public_key

        if hasattr(self, 'public_key_dict') and isinstance(self.public_key_dict, dict):
            self._cached_public_key = self.public_key_dict.get('publicKeyPem', None)

        return self._cached_public_key

    @public_key.setter
    def public_key(self, value):
        if not value: return
        self._cached_public_key = value
        self.public_key_dict = {'id': self.id+'#main-key', 'owner': self.id, 'publicKeyPem': value}

    @property
    def image_urls(self):
        if getattr(self, 'icon', None):
            icon = self.icon if not isinstance(self.icon, list) else self.icon[0]
            self._cached_image_urls = {
                'small': icon.url,
                'medium': icon.url,
                'large': icon.url
                }
        return self._cached_image_urls

    @image_urls.setter
    def image_urls(self, value):
        self._cached_image_urls = value
        if value.get('large'):
            try:
                profile_icon = Image(url=value.get('large'))
                if profile_icon.media_type:
                    self.icon = profile_icon
            except Exception as ex:
                logger.warning("models.Person - failed to set profile icon: %s", ex)

    class Meta:
        rdf_type = as2.Person
        exclude = ('atom_url',)


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


class Application(Person):
    class Meta:
        rdf_type = as2.Application


# The to_base method is used to handle cases where an AP object type matches multiple
# classes depending on the existence/value of specific propertie(s) or
# when the same class is used both as an object or an activity or
# when a property can't be directly deserialized from the payload.
# calamus Nested field can't handle using the same model
# or the same type in multiple schemas
class Note(Object, RawContentMixin):
    id = fields.Id()
    actor_id = IRI(as2.attributedTo)
    target_id = IRI(as2.inReplyTo, default=None)
    conversation = fields.RawJsonLD(ostatus.conversation)
    entity_type = 'Post'
    in_reply_to_atom_uri = IRI(ostatus.inReplyToAtomUri)
    sensitive = fields.Boolean(as2.sensitive, default=False)
    summary = fields.String(as2.summary)
    url = IRI(as2.url)
    _cached_raw_content = ''
    _cached_children = []

    def __init__(self, *args, **kwargs):
        self.tag_objects = [] # mutable objects...
        super().__init__(*args, **kwargs)
        self._allowed_children += (base.Audio, base.Video)

    def to_as2(self):
        self.sensitive = 'nsfw' in self.tags

        edited = False
        if hasattr(self, 'times'):
            self.created_at = self.times['created']
            if self.times['edited']:
                self.updated = self.times['modified']
                edited = True

        if self.activity_id:
            activity = Update if edited else Create
            activity.schema().declared_fields['object_'].schema['to'][type(self)] = Note.schema()
            self.activity=activity(
                    activity_id=self.activity_id, 
                    created_at=self.created_at, 
                    actor_id=self.actor_id,
                    object_ = self,
                    to = self.to,
                    cc = self.cc
                    )

        as2 = super().to_as2()
        if self.activity_id: del activity.schema().declared_fields['object_'].schema['to'][type(self)]
        return as2

    def to_base(self):
        kwargs = get_base_attributes(self, keep=(
            '_mentions', '_media_type', '_rendered_content', '_cached_children', '_cached_raw_content'))
        entity = Comment(**kwargs) if getattr(self, 'target_id') else Post(**kwargs)

        set_public(entity)
        return entity

    def pre_send(self) -> None:
        """
        Attach any embedded images from raw_content.
        """
        super().pre_send()
        self._children = [
                Image(
                    url=image[0],
                    name=image[1],
                    inline=True,
                ) for image in self.embedded_images
                ]

        # Add other AP objects
        self.extract_mentions()
        self.content_map = {'orig': self.rendered_content}
        self.add_mention_objects()
        self.add_tag_objects()

    def post_receive(self) -> None:
        """
        Make linkified tags normal tags.
        """
        super().post_receive()

        if getattr(self, 'target_id'): self.entity_type = 'Comment'

        # noinspection PyUnusedLocal
        def remove_tag_links(attrs, new=False):

            # Mastodon
            rel = (None, "rel")
            if attrs.get(rel) == "tag":
                return
            
            # Friendica
            href = (None, "href")
            if attrs.get(href).endswith(f'tag={attrs.get("_text")}'):
                return

            return attrs

        if not self.raw_content or self._media_type == "text/markdown":
            # Skip when markdown
            return

        self.raw_content = bleach.linkify(
            self.raw_content,
            callbacks=[remove_tag_links],
            parse_email=False,
            skip_tags=["code", "pre"],
        )

    def add_tag_objects(self) -> None:
        """
        Populate tags to the object.tag list.
        """
        try:
            config = get_configuration()
        except ImportError:
            tags_path = None
        else:
            if config["tags_path"]:
                tags_path = f"{config['base_url']}{config['tags_path']}"
            else:
                tags_path = None
        for tag in self.tags:
            _tag = Hashtag(name=f'#{tag}')
            if tags_path:
                _tag.href = tags_path.replace(":tag:", tag)
            self.tag_objects.append(_tag)

    def add_mention_objects(self) -> None:
        """
        Populate mentions to the object.tag list.
        """
        if len(self._mentions):
            mentions = list(self._mentions)
            mentions.sort()
            for mention in mentions:
                if validate_handle(mention):
                    profile = get_profile(finger=mention)
                    # only add AP profiles mentions
                    if getattr(profile, 'id', None):
                        self.tag_objects.append(Mention(href=profile.id, name='@'+mention))
                        # some platforms only render diaspora style markdown if it is available
                        self.source['content'] = self.source['content'].replace(mention, '{'+mention+'}')

    def extract_mentions(self):
        """
        Extract mentions from the source object.
        """
        super().extract_mentions()

        if getattr(self, 'tag_objects', None):
            #tag_objects = self.tag_objects if isinstance(self.tag_objects, list) else [self.tag_objects]
            for tag in self.tag_objects:
                if isinstance(tag, Mention):
                    profile = get_profile_or_entity(fid=tag.href)
                    handle = getattr(profile, 'finger', None)
                    if handle: self._mentions.add(handle)

    @property
    def raw_content(self):

        if self._cached_raw_content: return self._cached_raw_content
        if self.content_map:
            orig = self.content_map.pop('orig')
            if len(self.content_map.keys()) > 1:
                logger.warning('Language selection not implemented, falling back to default')
                self._rendered_content = orig.strip()
            else:
                self._rendered_content = orig.strip() if len(self.content_map.keys()) == 0 else next(iter(self.content_map.values())).strip()
            self.content_map['orig'] = orig

            if isinstance(self.source, dict) and self.source.get('mediaType') == 'text/markdown':
                self._media_type = self.source['mediaType']
                self._cached_raw_content = self.source.get('content').strip()
            else:
                self._media_type = 'text/html'
                self._cached_raw_content = self._rendered_content
            # to allow for posts/replies with medias only.
            if not self._cached_raw_content: self._cached_raw_content = "<div></div>"
            return self._cached_raw_content
    
    @raw_content.setter
    def raw_content(self, value):
        if not value: return
        self._cached_raw_content = value
        if self._media_type == 'text/markdown':
            self.source = {'content': value, 'mediaType': self._media_type}

    @property
    def _children(self):
        if self._cached_children: return self._cached_children

        if isinstance(getattr(self, 'attachment', None), list):
            children = []
            for child in self.attachment:
                if isinstance(child, Document):
                    obj = child.to_base()
                    if isinstance(obj, Image):
                        if obj.inline or (obj.image and obj.image in self.raw_content):
                            continue
                    children.append(obj)
            self._cached_children = children

        return self._cached_children
    
    @_children.setter
    def _children(self, value):
        if not value: return
        self._cached_children = value
        self.attachment = [Image.from_base(i) for i in value]


    class Meta:
        rdf_type = as2.Note
        exclude = ('handle',)


class Post(Note, base.Post):
    class Meta:
        rdf_type = as2.Note
        exclude = ('handle',)


class Comment(Note, base.Comment):
    class Meta:
        rdf_type = as2.Note
        exclude = ('handle',)


class Article(Note):
    class Meta:
        rdf_type = as2.Article


class Page(Note):
    class Meta:
        rdf_type = as2.Page


# peertube uses a lot of properties differently...
class Video(Document, base.Video):
    id = fields.Id()
    actor_id = MixedField(as2.attributedTo, nested=['PersonSchema', 'GroupSchema'], many=True)
    url = MixedField(as2.url, nested='LinkSchema')

    class Meta:
        unknown = EXCLUDE # required until all the pt fields are defined
        rdf_type = as2.Video

    def to_base(self):
        """Turn Peertube Video object into a Post
        Currently assumes Video objects with a content_map
        come from Peertube, but that's a bit weak
        """
        
        self.__dict__.update({'schema': True})
        if hasattr(self, 'content_map'):
            text = self.content_map['orig']
            if getattr(self, 'media_type', None) == 'text/markdown':
                url = ""
                for u in self.url:
                    if getattr(u, 'media_type', None) == 'text/html':
                        url = u.href
                        break
                text = f'[{self.name}]({url})\n\n'+text
                self.raw_content = text.strip()
                self._media_type = self.media_type

            if hasattr(self, 'actor_id'):
                act = self.actor_id
                new_act = []
                if not isinstance(act, list): act = [act]
                for a in act:
                    if isinstance(a, Person):
                        new_act.append(a.id)
                # TODO: fix extract_receivers which can't handle multiple actors!
                self.actor_id = new_act[0]
            
            entity = Post(**get_base_attributes(self,
                keep=('_mentions', '_media_type', '_rendered_content', '_cached_children', '_cached_raw_content')))
            set_public(entity)
            return entity
        #Some Video object
        else:
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
    instrument = MixedField(as2.instrument, nested='ServiceSchema')
    # Not implemented yet
    #result
    #origin

    def __init__(self, *args, **kwargs):
        self.activity = self
        super().__init__(*args, **kwargs)
        self.attachment = None

    class Meta:
        rdf_type = as2.Activity

    
class Follow(Activity, base.Follow):
    activity_id = fields.Id()
    target_id = IRI(as2.object)

    def to_as2(self):
        if not self.following:
            self.activity = Undo(
                    activity_id = f"{self.actor_id}#follow-{uuid.uuid4()}",
                    actor_id = self.actor_id,
                    object_ = self
                    )

        return super().to_as2()

    def to_base(self):
        # This is assuming Follow can only be the object of an Undo activity. Lazy.
        if self.activity != self: 
            self.following = False

        return self

    def post_receive(self) -> None:
        """
        Post receive hook - send back follow ack.
        """
        super().post_receive()

        if not self.following:
            return

        try:
            from federation.utils.django import get_function_from_config
            get_private_key_function = get_function_from_config("get_private_key_function")
        except (ImportError, AttributeError):
            logger.warning("Activitypub Follow.post_receive - Unable to send automatic Accept back, only supported on "
                           "Django currently")
            return
        key = get_private_key_function(self.target_id)
        if not key:
            logger.warning("Activitypub Follow.post_receive - Failed to send automatic Accept back: could not find "
                           "profile to sign it with")
            return
        accept = Accept(
            activity_id=f"{self.target_id}#accept-{uuid.uuid4()}",
            actor_id=self.target_id,
            target_id=self.activity_id,
            object=self.to_as2(),
        )
        # noinspection PyBroadException
        try:
            profile = retrieve_and_parse_profile(self.actor_id)
        except Exception:
            profile = None
        if not profile:
            logger.warning("Activitypub Follow.post_receive - Failed to fetch remote profile for sending back Accept")
            return
        # noinspection PyBroadException
        try:
            handle_send(
                accept,
                UserType(id=self.target_id, private_key=key),
                recipients=[{
                    "endpoint": profile.inboxes["private"],
                    "fid": self.actor_id,
                    "protocol": "activitypub",
                    "public": False,
                }],
            )
        except Exception:
            logger.exception("Activitypub Follow.post_receive - Failed to send Accept back")

    class Meta:
        rdf_type = as2.Follow
        exclude = ('created_at', 'handle')


class Announce(Activity, base.Share):
    id = fields.Id()
    target_id = IRI(as2.object)

    def to_as2(self):
        if isinstance(self.activity, type):
            self.activity = self.activity(
                activity_id = self.activity_id if self.activity_id else f"{self.actor_id}#share-{uuid.uuid4()}",
                actor_id = self.actor_id,
                object_ = self,
                to = self.to,
                cc = self.cc
                )

        return super().to_as2()

    def to_base(self):

        if self.activity == self:
            entity = self
        else:
            self.target_id = self.id
            self.entity_type = 'Object'
            self.__dict__.update({'schema': True})
            entity = base.Retraction(**get_base_attributes(self))

        set_public(entity)
        return entity

    class Meta:
        rdf_type = as2.Announce
    

class Tombstone(Object, base.Retraction):
    target_id = fields.Id()

    def to_as2(self):
        if not isinstance(self.activity, type): return None
        self.activity = self.activity(
                activity_id = self.activity_id if self.activity_id else f"{self.actor_id}#delete-{uuid.uuid4()}",
                actor_id = self.actor_id,
                created_at = self.created_at,
                object_ = self,
                )

        return super().to_as2()
                    

    def to_base(self):
        if self.activity != self: self.actor_id = self.activity.actor_id
        self.entity_type = 'Object'
        return self

    class Meta:
        rdf_type = as2.Tombstone
        exclude = ('created_at',)


class Create(Activity):
    activity_id = fields.Id()
    object_ = MixedField(as2.object, nested=OBJECTS)

    class Meta:
        rdf_type = as2.Create


class Like(Announce):
    like = fields.String(diaspora.like)

    def to_base(self):
        return self

    class Meta:
        rdf_type = as2.Like


# inbound Accept is a noop...
class Accept(Create, base.Accept):
    class Meta:
        rdf_type = as2.Accept
        exclude = ('created_at',)


class Delete(Create, base.Retraction):
    def to_base(self):
        if hasattr(self, 'object_') and not isinstance(self.object_, Tombstone):
            self.target_id = self.object_
            self.entity_type = 'Object'
        return self

    class Meta:
        rdf_type = as2.Delete


class Update(Create):
    class Meta:
        rdf_type = as2.Update


class Undo(Create):
    class Meta:
        rdf_type = as2.Undo
        exclude = ('created_at',)


class View(Create):
    class Meta:
        rdf_type = as2.View


def process_followers(obj, base_url):
    pass

def extract_receiver(profile, receiver):
    """
    Transform a single receiver ID to a UserType.
    """

    if receiver == NAMESPACE_PUBLIC:
        # Ignore since we already store "public" as a boolean on the entity
        return []

    # First try to get receiver entity locally or remotely
    obj = get_profile_or_entity(fid=receiver)

    if isinstance(obj, base.Profile):
        return [UserType(id=receiver, receiver_variant=ReceiverVariant.ACTOR)]
    # This doesn't handle cases where the actor is sending to other actors
    # followers (seen on PeerTube)
    if profile.followers == receiver:
        return [UserType(id=profile.id, receiver_variant=ReceiverVariant.FOLLOWERS)]


def extract_receivers(entity):
    """
    Extract receivers from a payload.
    """
    receivers = []
    profile = None
    # don't care about receivers for payloads without an actor_id    
    if getattr(entity, 'actor_id'):
        with rc.enabled(cache_name='fed_cache', backend=backend):
            profile = retrieve_and_parse_profile(entity.actor_id)
    if not profile: return receivers
    
    for attr in ("to", "cc"):
        receiver = getattr(entity, attr, None)
        if isinstance(receiver, str): receiver = [receiver]
        if isinstance(receiver, list):
            for item in receiver:
                extracted = extract_receiver(profile, item)
                if extracted:
                    receivers += extracted
    return receivers


def extract_and_validate(entity):
    # Add protocol name
    entity._source_protocol = "activitypub"
    # Extract receivers
    entity._receivers = extract_receivers(entity)
    if hasattr(entity, "post_receive"):
        entity.post_receive()

    if hasattr(entity, 'validate'): entity.validate()

    # Extract mentions
    if hasattr(entity, "extract_mentions"):
        entity.extract_mentions()


def extract_replies(replies):
    objs = []
    visited = []

    def walk_reply_collection(replies):
        items = getattr(replies, 'items', [])
        if items and not isinstance(items, list): items = [items]
        for obj in items:
            if isinstance(obj, Note):
                try:
                    obj = obj.to_base()
                    extract_and_validate(obj)
                except ValueError as ex:
                    logger.error("extract_replies - Failed to validate entity %s: %s", entity, ex)
                    continue
            elif not isinstance(obj, str): continue
            objs.append(obj)
        if getattr(replies, 'next_', None):
            if (replies.id != replies.next_) and (replies.next_ not in visited):
                resp = retrieve_and_parse_document(replies.next_)
                if resp:
                    visited.append(replies.next_)
                    walk_reply_collection(resp)

    walk_reply_collection(replies)
    return objs


def element_to_objects(element: Union[Dict, Object]) -> List:
    """
    Transform an Element to a list of entities.
    """

    # json-ld handling with calamus
    # Skips unimplemented payloads
    entity = model_to_objects(element) if not isinstance(element, Object) else element
    if entity and hasattr(entity, 'to_base'):
        entity = entity.to_base()
    if isinstance(entity, (
        base.Post, base.Comment, base.Profile, base.Share, base.Follow,
        base.Retraction, base.Accept,)
        ):
        try:
            extract_and_validate(entity)
        except ValueError as ex:
            logger.error("Failed to validate entity %s: %s", entity, ex)
            return None
        logger.info('Entity type "%s" was handled through the json-ld processor', entity.__class__.__name__)
        return [entity]
    elif entity:
        logger.info('Entity type "%s" was handled through the json-ld processor but is not a base entity', entity.__class__.__name__)
        entity._receivers = extract_receivers(entity)
        return [entity]
    else:
        logger.warning("Payload not implemented by the json-ld processor, skipping")
        return []


def model_to_objects(payload):
    model = globals().get(payload.get('type'))
    if model and issubclass(model, Object):
        try:
            entity = model.schema().load(payload)
        except (KeyError, jsonld.JsonLdError, exceptions.ValidationError) as exc :  # Just give up for now. This must be made robust
            logger.error(f"Error parsing jsonld payload ({exc})")
            return None

        if isinstance(getattr(entity, 'object_', None), Object):
            entity.object_.activity = entity
            entity = entity.object_
    
        return entity
    return None
