from calamus import fields
from calamus.schema import JsonLDSchema
from calamus.utils import normalize_value
from marshmallow import pre_load, post_load, pre_dump, post_dump
from marshmallow.fields import Integer
from pyld import jsonld, documentloader
import json
import requests_cache

from federation.entities.mixins import BaseEntity
from federation.entities.activitypub.entities import ActivitypubAccept, ActivitypubPost, ActivitypubComment, ActivitypubProfile, ActivitypubImage, ActivitypubFollow, ActivitypubShare, ActivitypubRetraction

# This is required to workaround a bug in pyld that has the Accept header
# accept other content types. From what I understand, precedence handling
# is broken
def myloader(*args, **kwargs):
    requests_cache.install_cache('ld_cache', backend='redis') # this will require some configuration mechanism
    requests_loader = documentloader.requests.requests_document_loader(*args, **kwargs)
    
    def loader(url, options={}):
        options['headers']['Accept'] = 'application/ld+json'
        return requests_loader(url, options)
    
    return loader
jsonld.set_document_loader(myloader())


# Not sure how exhaustive this needs to be...
as2 = fields.Namespace("https://www.w3.org/ns/activitystreams#")
toot = fields.Namespace("http://joinmastodon.org/ns#")
ostatus = fields.Namespace("http://ostatus.org#")
schema = fields.Namespace("http://schema.org#")
sec = fields.Namespace("https://w3id.org/security#")
dc = fields.Namespace("http://purl.org/dc/terms/")
xsd = fields.Namespace("http://www.w3.org/2001/XMLSchema#")
ldp = fields.Namespace("http://www.w3.org/ns/ldp#")
vcard = fields.Namespace("http://www.w3.org/2006/vcard/ns#")
pt = fields.Namespace("https://joinpeertube.org/ns#")
pyfed = fields.Namespace("https://docs.jasonrobinson.me/ns/python-federation#")
diaspora = fields.Namespace("https://diasporafoundation.org/ns/")


# Maybe this is food for an issue with calamus. pyld expands IRIs in an array,
# marshmallow then barfs with an invalid string value.
# Workaround: get rid of the array.
class IRI(fields.IRI):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, list) and len(value) == 0: return None
        value = normalize_value(value)
        if isinstance(value, list):
            # no call to super() in list comprehensions...
            ret = []
            for val in value:
                v = super()._deserialize(val, attr, data, **kwargs)
                ret.append(v)
            return ret

        return super()._deserialize(value, attr, data, **kwargs)

# calamus sets a XMLSchema#integer type, but different definitions
# maybe used, hence the flavor property
# TODO: handle non negative types
class Integer(fields._JsonLDField, Integer):
    flavor = None # add fields.IRIReference type hint 

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
class LanguageMap(fields.Dict):
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
        if isinstance(value, str):
            return self.iri._serialize(value, attr, obj, **kwargs)
        else:
            return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, list) and value[0].get('@type'):
            return super()._deserialize(value, attr, data, **kwargs)
        else:
            return self.iri._deserialize(value, attr, data, **kwargs)
        

'''
The fed_instance method is used to handle cases where an AP object type matches multiple
classes depending on the existence/value of specific propertie(s) or
when the same class is used both as an object or an activity or
when a property can't be directly deserialized from the payload.
calamus Nested field can't handle using the same model
or the same type in multiple schemas
'''
class Entity:
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    # noop to avoid isinstance tests
    def fed_instance(self):
        return self

'''
A node without an id isn't true json-ld, but many payloads have
id-less nodes. Since calamus forces random ids on such nodes, 
this mixin removes it.
'''
class NoIdMixin:
    def dump(self, obj):
        ret = super().dump(obj)
        ret.pop('@id', None)
        return ret

class ObjectMixin:
    #_children = fields.Nested(as2.attachment, nested=[PropertyValueSchema], many=True)
    #audience
    content_map = LanguageMap(as2.content) # language maps are not implemented in calamus
    #contentMap = fields.Dict(as2.contentMap, many=True)
    context = IRI(as2.context)
    guid = fields.String(diaspora.guid)
    name = fields.String(as2.name)
    #endtime
    generator = fields.Dict(as2.generator)
    #location
    #preview
    created_at = fields.DateTime(as2.published, add_value_types=True)
    replies = fields.Dict(as2.replies) # todo: define Collection schema
    startTime = fields.DateTime(as2.startTime, add_value_types=True)
    summary = fields.String(as2.summary)
    updated = fields.DateTime(as2.updated, add_value_types=True)
    #to = fields.List(as2.to, cls_or_instance=IRI(as2.to))
    to = IRI(as2.to, many=True)
    #bto
    #cc = fields.List(as2.cc, cls_or_instance=IRI(as2.cc))
    cc = IRI(as2.cc, many=True)
    #bcc
    media_type = fields.String(as2.mediaType)
    #duration
    sensitive = fields.Boolean(as2.sensitive)
    source = fields.Dict(as2.source)

    @pre_load
    def pre_load(self, data, **kwargs):
        # add a # at the end of the python-federation string
        # for socialhome payloads
        s = json.dumps(data.get('@context'))
        if 'python-federation"' in s:
            data['@context'] = json.loads(s.replace('python-federation', 'python-federation#', 1))
        return data

    @post_load
    def make_instance(self, data, **kwargs):
        for k, v in data.items():
            if isinstance(v, dict):
                # don't want expanded IRIs to be exposed as dict keys
                data[k] = jsonld.compact(v, self.context)
                data[k].pop('@context')
        data['schema'] = self.__class__
        return super().make_instance(data, **kwargs).fed_instance()
    
# This mimics that federation currently handles AP Document as AP Image
# May need to be extended
class DocumentMixin(ObjectMixin):
    inline = fields.Boolean(pyfed.inlineImage)
    height = Integer(as2.height, flavor=xsd.nonNegativeInteger, add_value_types=True)
    width = Integer(as2.width, flavor=xsd.nonNegativeInteger, add_value_types=True)
    url = IRI(as2.url)
    blurhash = fields.String(toot.blurhash)

class Document(Entity):
    def fed_instance(self):
        return ActivitypubImage(**self.__dict__)

class DocumentSchema(DocumentMixin, NoIdMixin, JsonLDSchema):

    class Meta:
        #fields = ('inline', 'url', 'media_type', 'name')
        unknown = 'INCLUDE'
        rdf_type = as2.Document
        model = Document

class Image(Document):
    pass

class ImageSchema(DocumentMixin, NoIdMixin, JsonLDSchema):

    class Meta:
        fields = ('inline', 'url', 'media_type', 'name')
        unknown = 'INCLUDE'
        rdf_type = as2.Image
        model = Image

class Infohash(Entity):
    pass

class InfohashSchema(NoIdMixin, JsonLDSchema):
    name = fields.String(as2.name)

    class Meta:
        rdf_type = pt.Infohash
        model = Infohash

class LinkMixin:
    href = IRI(as2.href)
    rel = fields.List(as2.rel, cls_or_instance=fields.String(as2.rel))
    mediaType = fields.String(as2.mediaType)
    name = fields.String(as2.name)
    hrefLang = fields.String(as2.hrefLang)
    height = Integer(as2.height, flavor=xsd.nonNegativeInteger, add_value_types=True)
    width = Integer(as2.width, flavor=xsd.nonNegativeInteger, add_value_types=True)
    fps = Integer(pt.fps, flavor=schema.Number, add_value_types=True)
    size = Integer(pt.size, flavor=schema.Number, add_value_types=True)
    #preview : variable type?
    
class Link(Entity):
    pass

class LinkSchema(LinkMixin, NoIdMixin, JsonLDSchema):
    tag = fields.Nested(as2.tag, nested=[InfohashSchema, 'LinkSchema'], many=True)

    class Meta:
        rdf_type = as2.Link
        model = Link

class Hashtag(Entity):
    pass

class HashtagSchema(LinkMixin, NoIdMixin, JsonLDSchema):

    class Meta:
        rdf_type = as2.Hashtag
        model = Hashtag

class Mention(Entity):
    pass

class MentionSchema(LinkMixin, NoIdMixin, JsonLDSchema):

    class Meta:
        rdf_type = as2.Mention
        model = Mention

class ObjectSchema(ObjectMixin, JsonLDSchema):
    id = fields.Id()
    icon = fields.Nested(as2.icon, nested=ImageSchema, many=True)
    image = fields.Nested(as2.image, nested=ImageSchema, many=True)
    tag_list = fields.Nested(as2.tag, nested=[HashtagSchema,MentionSchema], many=True)
    _children = fields.Nested(as2.attachment, nested=[ImageSchema, DocumentSchema], many=True)

class PropertyValue(Entity):
    pass

class PropertyValueSchema(NoIdMixin, JsonLDSchema):
    name = fields.String(as2.name)
    value = fields.String(schema.value)

    class Meta:
        rdf_type = schema.PropertyValue
        model = PropertyValue

class ActorMixin(ObjectMixin):
    id = fields.Id()
    attachment = fields.Nested(as2.attachment, nested=[PropertyValueSchema], many=True)
    inbox = IRI(ldp.inbox)
    outbox = IRI(as2.outbox)
    following = IRI(as2.following)
    followers = IRI(as2.followers)
    #liked is a collection
    #streams
    username = fields.String(as2.preferredUsername)
    endpoints = fields.Dict(as2.endpoints)
    #proxyUrl
    #oauthAuthorizationEndpoint
    #oauthTokenEndpoint
    #provideClientKey
    #signClientKey
    url = IRI(as2.url)
    icon = fields.Nested(as2.icon, nested=ImageSchema, many=True)
    image = fields.Nested(as2.image, nested=ImageSchema, many=True)
    tag_list = fields.Nested(as2.tag, nested=[HashtagSchema], many=True)
    playlists = IRI(pt.playlists)
    featured = IRI(toot.featured)
    featuredTags = IRI(toot.featuredTags)
    manuallyApprovesFollowers = fields.Boolean(as2.manuallyApprovesFollowers)
    discoverable = fields.Boolean(toot.discoverable)
    devices = IRI(toot.devices)
    publicKey = fields.Dict(sec.publicKey)
    guid = fields.String(diaspora.guid)
    handle = fields.String(diaspora.handle)

class Person(Entity):
    def fed_instance(self):
        entity = ActivitypubProfile(**self.__dict__)
        if hasattr(self, 'inbox'):
            entity.inboxes = {'private': self.inbox, 'public':self.endpoints['sharedInbox']}
            entity.public_key = self.publicKey['publicKeyPem']
        entity.image_urls = {}
        if hasattr(self, 'icon'):
            entity.image_urls = {
                'small': self.icon[0].url,
                'medium': self.icon[0].url,
                'large': self.icon[0].url
                }

        return entity


class PersonSchema(ActorMixin, JsonLDSchema):
    class Meta:
        rdf_type = as2.Person
        model = Person

class Group(Person):
    pass

class GroupSchema(ActorMixin, JsonLDSchema):
    class Meta:
        rdf_type = as2.Group
        model = Group

class Application(Person):
    pass

class ApplicationSchema(ActorMixin, JsonLDSchema):
    class Meta:
        rdf_type = as2.Application
        model = Application

class Organization(Person):
    pass

class OrganizationSchema(ActorMixin, JsonLDSchema):
    class Meta:
        rdf_type = as2.Organization
        model = Organization

class Service(Person):
    pass

class ServiceSchema(ActorMixin, JsonLDSchema):
    class Meta:
        rdf_type = as2.Service
        model = Service

class NoteMixin:
    actor_id = IRI(as2.attributedTo, many=True)
    target_id = IRI(as2.inReplyTo)
    atom_url = IRI(ostatus.atomUri)
    conversation = fields.String(ostatus.conversation)
    inReplyToAtomUri = IRI(ostatus.inReplyToAtomUri)
    url = IRI(as2.url)

class Note(Entity):
    def fed_instance(self):
        entity = ActivitypubComment(**self.__dict__) if hasattr(self, 'target_id') else ActivitypubPost(**self.__dict__)

        if hasattr(self, 'content_map'):
            entity._rendered_content = self.content_map['orig'].strip()
            if hasattr(self, 'source') and self.source.get('mediaType') == 'text/markdown':
                entity._media_type = self.source['mediaType']
                entity.raw_content = self.source.get('content').strip()
            else:
                entity._media_type = 'text/html'
                entity.raw_content = self.content_map['orig']

        return entity

class NoteSchema(NoteMixin, ObjectSchema):
    class Meta:
        rdf_type = as2.Note
        model = Note

class Page(Note):
    pass

class PageSchema(NoteMixin, ObjectSchema):
    class Meta:
        rdf_type = as2.Page
        model = Page

class Article(Note):
    pass

class ArticleSchema(NoteMixin, ObjectSchema):
    class Meta:
        rdf_type = as2.Article
        model = Article

class Video(Entity):
    pass

# peertube uses a lot of properties differently...
class VideoSchema(ObjectSchema):
    urls = fields.Nested(as2.url, nested=LinkSchema, many=True)
    actor_id = fields.Nested(as2.attributedTo, nested=[PersonSchema, GroupSchema], many=True)

    class Meta:
        unknown = 'EXCLUDE' # required until all the pt fields are defined
        rdf_type = as2.Video
        model = Video

class Signature(Entity):
    pass

class SignatureSchema(NoIdMixin, JsonLDSchema):
    created = fields.DateTime(dc.created, add_value_types=True)
    creator = IRI(dc.creator)
    key = fields.String(sec.signatureValue)
    nonce = fields.String(sec.nonce)

    class Meta:
        rdf_type = sec.RsaSignature2017
        model = Signature

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

class Activity(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activity = self

class ActivityMixin(ObjectMixin):
    actor_id = IRI(as2.actor)
    #target_id = IRI(as2.target)
    #result
    #origin
    instrument = fields.Dict(as2.instrument)
    # don't have a clear idea of which activities are signed and which are not
    signature = fields.Nested(sec.signature, nested = SignatureSchema)

    @pre_load
    def pre_load(self, data, **kwargs):
        data = super().pre_load(data, **kwargs)
        
        # AP activities may be signed, but some platforms don't
        # define RsaSignature2017. add it to the context
        if data.get('signature'):
            ctx = data.get('@context')
            if not isinstance(ctx, list):
                ctx = [ctx, {}]
            w3id = 'https://w3id.org/security/v1'
            if w3id not in ctx: ctx.insert(0,w3id)
            idx = [i for i,v in enumerate(ctx) if isinstance(v, dict)]
            found = False
            for i in idx:
                if ctx[i].get('RsaSignature2017'):
                    found = True
                    break
            if not found: ctx[idx[0]]['RsaSignature2017'] = 'sec:RsaSignature2017'
            data['@context'] = ctx

        return data

class Follow(Activity):
    def fed_instance(self):
        entity = ActivitypubFollow(**self.__dict__)
        # This is assuming Follow can only be the object of an Undo activity. Lazy.
        if self.activity != self: 
            entity.following = False

        return entity

class FollowSchema(ActivityMixin, JsonLDSchema):
    activity_id = fields.Id()
    target_id = IRI(as2.object)

    class Meta:
        rdf_type = as2.Follow
        model = Follow

class Announce(Activity):
    def fed_instance(self):
        if self.activity == self:
            return ActivitypubShare(**self.__dict__)
        else:
            return ActivitypubRetraction(**self.__dict__)

class AnnounceSchema(ActivityMixin, JsonLDSchema):
    id = fields.Id()
    target_id = IRI(as2.object)

    class Meta:
        rdf_type = as2.Announce
        model = Announce
    
class Tombstone(Entity):
    def fed_instance(self):
        return ActivitypubRetraction(**self.__dict__)

class TombstoneSchema(ObjectMixin, JsonLDSchema):
    target_id = fields.Id()

    class Meta:
        rdf_type = as2.Tombstone
        model = Tombstone

class ActivityObjectMixin(ActivityMixin):
    object_ = MixedField(as2.object, nested=OBJECTS)

class Like(Activity):
    pass

class LikeSchema(ActivityObjectMixin, JsonLDSchema):
    activity_id = fields.Id()
    like = fields.String(diaspora.like)

    class Meta:
        rdf_type = as2.Like
        model = Like

# inbound Accept is a noop...
class Accept(Activity):
    def fed_instance(self):
        del self.object_
        return ActivitypubAccept(**self.__dict__)

class AcceptSchema(ActivityObjectMixin, JsonLDSchema):
    activity_id = fields.Id()

    class Meta:
        rdf_type = as2.Accept
        model = Accept

class Create(Activity):
    pass

class CreateSchema(ActivityObjectMixin, JsonLDSchema):
    activity_id = fields.Id()

    class Meta:
        rdf_type = as2.Create
        model = Create

class Delete(Activity):
    def fed_instance(self):
        if hasattr(self, 'object_') and not isinstance(self.object_, Entity):
            self.target_id = self.object_
            return ActivitypubRetraction(**self.__dict__)

class DeleteSchema(ActivityObjectMixin, JsonLDSchema):
    activity_id = fields.Id()

    class Meta:
        rdf_type = as2.Delete
        model = Delete

class Update(Activity):
    pass

class UpdateSchema(ActivityObjectMixin, JsonLDSchema):
    activity_id = fields.Id()

    class Meta:
        rdf_type = as2.Update
        model = Update

class Undo(Activity):
    pass

class UndoSchema(ActivityObjectMixin, JsonLDSchema):
    activity_id = fields.Id()

    class Meta:
        rdf_type = as2.Undo
        model = Undo

class View(Activity):
    pass

class ViewSchema(ActivityObjectMixin, JsonLDSchema):

    class Meta:
        rdf_type = as2.View
        model = View

SCHEMAMAP = {
        "Accept": AcceptSchema,
        "Announce": AnnounceSchema,
        "Application": ApplicationSchema,
        "Article": ArticleSchema,
        "Create": CreateSchema,
        "Delete": DeleteSchema,
        "Group": GroupSchema,
        "Follow": FollowSchema,
        "Like": LikeSchema,
        "Note": NoteSchema,
        "Organization": OrganizationSchema,
        "Page": PageSchema,
        "Person": PersonSchema,
        "Service": ServiceSchema,
        "Undo": UndoSchema,
        "Update": UpdateSchema,
        "View": ViewSchema
}

def schema_to_objects(payload):
    schema = SCHEMAMAP.get(payload.get('type'))
    if schema:
        entity = schema(context=payload.get('@context')).load(payload)

        if hasattr(entity, 'object_') and (isinstance(entity.object_, Entity) or isinstance(entity.object_, BaseEntity)):
            entity.object_.activity = entity
            entity = entity.object_
    
        return entity
    return None
