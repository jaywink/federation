import copy
import json
import logging
import re
import uuid
from operator import attrgetter
from typing import List, Dict, Union
from unicodedata import normalize
from urllib.parse import unquote, urlparse

import bleach
from bs4 import BeautifulSoup
from calamus import fields
from calamus.schema import JsonLDAnnotation, JsonLDSchema, JsonLDSchemaOpts
from calamus.utils import normalize_value
from cryptography.exceptions import InvalidSignature
from marshmallow import exceptions, pre_load, post_load, post_dump
from marshmallow.fields import Integer
from marshmallow.utils import EXCLUDE, missing
from pyld import jsonld

import federation.entities.base as base
from federation.entities.activitypub.constants import CONTEXT_ACTIVITYSTREAMS, CONTEXT_SECURITY, NAMESPACE_PUBLIC
from federation.entities.activitypub.ldcontext import LdContextManager
from federation.entities.activitypub.ldsigning import create_ld_signature, verify_ld_signature
from federation.entities.mixins import BaseEntity, RawContentMixin
from federation.entities.utils import get_base_attributes, get_profile
from federation.outbound import handle_send
from federation.types import UserType, ReceiverVariant
from federation.utils.activitypub import retrieve_and_parse_document, retrieve_and_parse_profile, \
    get_profile_id_from_webfinger, get_profile_finger_from_webfinger
from federation.utils.text import with_slash, validate_handle

logger = logging.getLogger("federation")


def get_profile_or_entity(**kwargs):
    obj = get_profile(**kwargs)
    if not obj and kwargs.get('fid'):
        obj = retrieve_and_parse_document(kwargs['fid'])
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
lemmy = fields.Namespace("https://join-lemmy.org/ns#")
litepub = fields.Namespace("http://litepub.social/ns#")
misskey = fields.Namespace("https://misskey-hub.net/ns#")
mitra = fields.Namespace("http://jsonld.mitra.social#")
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

    def _serialize(self, value, attr, obj, **kwargs):
        if not value and isinstance(self.dump_derived, dict):
            fields = {f: getattr(obj, f) for f in self.dump_derived['fields']}
            value = self.dump_derived['fmt'].format(**fields)

        return super()._serialize(value, attr, obj, **kwargs)

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
    ctx = [CONTEXT_ACTIVITYSTREAMS, CONTEXT_SECURITY]

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
class MixedInteger(fields._JsonLDField, Integer):
    flavor = None  # add fields.IRIReference type hint 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flavor = self.metadata.get('flavor')

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
        if isinstance(obj, str): return self.iri._serialize(obj, None, None, **kwargs)
        return super()._serialize_single_obj(obj, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, str): return self.iri._serialize(value, attr, obj, **kwargs)
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
                try:
                    res = super()._deserialize(item, attr, data, **kwargs)
                except KeyError as ex:
                    logger.warning("nested field: undefined JSON-LD type %s", ex)
                    continue
                ret.append(res if not isinstance(res, list) else res[0])
            else:
                ret.append(self.iri._deserialize(item, attr, data, **kwargs))

        if not ret: ret.append(None)
        return ret if len(ret) > 1 or self.many else ret[0]
        

OBJECTS = [
        'AnnounceSchema',
        'ApplicationSchema',
        'ArticleSchema',
        'CreateSchema',
        'FollowSchema',
        'GroupSchema',
        'LikeSchema',
        'NoteSchema',
        'OrganizationSchema',
        'PageSchema',
        'PersonSchema',
        'ServiceSchema',
        'TombstoneSchema',
        'UpdateSchema',
        'VideoSchema'
]

def set_public(entity):
    for attr in [entity.to, entity.cc]:
        if isinstance(attr, list):
            if NAMESPACE_PUBLIC in attr: entity.public = True
        elif attr == NAMESPACE_PUBLIC: entity.public = True


class Object(BaseEntity, metaclass=JsonLDAnnotation):
    atom_url = fields.String(ostatus.atomUri)
    also_known_as = IRI(as2.alsoKnownAs,
                        metadata={'ctx':[{ 'alsoKnownAs':{'@id':'as:alsoKnownAs','@type':'@id'}}]})
    icon = MixedField(as2.icon, nested='ImageSchema')
    image = MixedField(as2.image, nested='ImageSchema')
    tag_objects = MixedField(as2.tag, nested=['NoteSchema', 'HashtagSchema','MentionSchema','PropertyValueSchema','EmojiSchema'], many=True)
    attachment = MixedField(as2.attachment, nested=['LinkSchema', 'NoteSchema', 'ImageSchema', 'AudioSchema', 'DocumentSchema','PropertyValueSchema','IdentityProofSchema'],
                               many=True, default=[])
    content_map = LanguageMap(as2.content)  # language maps are not implemented in calamus
    context = fields.RawJsonLD(as2.context)
    name = fields.String(as2.name, default='')
    generator = MixedField(as2.generator, nested=['ApplicationSchema','ServiceSchema'])
    created_at = fields.DateTime(as2.published, add_value_types=True)
    replies = MixedField(as2.replies, nested=['CollectionSchema','OrderedCollectionSchema'])
    signature = MixedField(sec.signature, nested = 'RsaSignature2017Schema',
                           metadata={'ctx': [CONTEXT_SECURITY,
                                             {'RsaSignature2017':'sec:RsaSignature2017'}]})
    start_time = fields.DateTime(as2.startTime, add_value_types=True)
    updated = fields.DateTime(as2.updated, add_value_types=True)
    to = fields.List(as2.to, cls_or_instance=IRI(as2.to), default=[])
    cc = fields.List(as2.cc, cls_or_instance=IRI(as2.cc), default=[])
    media_type = fields.String(as2.mediaType)
    source = CompactedDict(as2.source)
    signable = False
    url = MixedField(as2.url, nested='LinkSchema', many=True)

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
        return context_manager.compact(obj)

    def sign_as2(self, sender=None):
        obj = self.to_as2()
        if self.signable and sender: create_ld_signature(obj, sender)
        return obj

    @classmethod
    def from_base(cls, entity):
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    # This is to ensure the original payload is relayed in order
    # to preserve the validity of the LD signature.
    # Note: the function name comes from the Diaspora logic and does
    # not reflect what is actually happening here. For AP, the parent
    # user's key is used for the http signature.
    def sign_with_parent(self, private_key):
        self.outbound_doc = getattr(self, '_source_object', None)

    # Before validation, assign None to fields that are set to marshmallow.missing
    # Setting missing fields to marshmallow.missing starts with calamus 0.4.1
    # TODO: rework validation
    def validate(self, direction='inbound'):
        if direction == 'inbound':
            # ensure marshmallow.missing is not sent to the client app
            for attr in type(self).schema().load_fields.keys():
                if getattr(self, attr) is missing:
                    setattr(self, attr, None)

        super().validate(direction)

    def _validate_signatures(self):
        # Objects extracted from collections don't have a source object.
        # To avoid infinite recursion, only verify a profile signature
        # if it was sent, not retrieved.
        if not self._source_object or (not self._sender and isinstance(self, Person)):
            return
        # Always verify inbound LD signature, for monitoring purposes
        actor = verify_ld_signature(self._source_object)
        if not self._sender:
            return
        if self.signable and self._sender not in (self.id, getattr(self, 'actor_id', None)):
            # Relayed payload
            if not actor:
                raise InvalidSignature('no or invalid signature for %s, a relayed payload', self.id)

    def to_string(self):
        # noinspection PyUnresolvedReferences
        return str(self.to_as2())

    class Meta:
        rdf_type = as2.Object

        @pre_load
        def patch_context(self, data, **kwargs):
            if not data.get('@context'): return data
            ctx = copy.copy(data['@context'])
            data['@context'] = context_manager.merge_context(ctx)
            return data

        # JSONLD specs states it is case sensitive.
        # Ensure type names for which we have an implementation have the proper case
        # for platforms that ignore the spec.
        @pre_load
        def patch_types(self, data, **kwargs):
            def walk_payload(payload):
                for key,val in copy.copy(payload).items():
                    if isinstance(val, dict):
                        walk_payload(val)
                    if key == 'type':
                        payload[key] = MODEL_NAMES.get(val.lower(), val)
                return payload
            return walk_payload(data)

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
    total_items = MixedInteger(as2.totalItems, metadata={'flavor':xsd.nonNegativeInteger}, add_value_types=True)

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
    start_index = MixedInteger(as2.startIndex, metadata={'flavor':xsd.nonNegativeInteger}, add_value_types=True)

    class Meta:
        rdf_type = as2.OrderedCollectionPage
        

# This mimics that federation currently handles AP Document as AP Image
# AP defines [Ii]mage and [Aa]udio objects/properties, but only a Video object
# seen with Peertube payloads only so far
class Document(Object):
    inline = fields.Boolean(pyfed.inlineImage, default=False,
                            metadata={'ctx':[{'pyfed':str(pyfed)}]})
    height = MixedInteger(as2.height, default=0, metadata={'flavor':xsd.nonNegativeInteger}, add_value_types=True)
    width = MixedInteger(as2.width, default=0, metadata={'flavor':xsd.nonNegativeInteger}, add_value_types=True)
    blurhash = fields.String(toot.blurHash,
                             metadata={'ctx':[{'toot':str(toot),'blurHash':'toot:blurHash'}]})
    url = MixedField(as2.url, nested='LinkSchema')

    def to_base(self):
        if self.media_type is missing:
            return self
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
    height = MixedInteger(as2.height, metadata={'flavor':xsd.nonNegativeInteger}, add_value_types=True)
    width = MixedInteger(as2.width, metadata={'flavor':xsd.nonNegativeInteger}, add_value_types=True)
    fps = MixedInteger(pt.fps, metadata={'flavor':schema.Number}, add_value_types=True)
    size = MixedInteger(pt.size, metadata={'flavor':schema.Number}, add_value_types=True)
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
    ctx = [{'Hashtag': 'as:Hashtag'}]
    id = fields.Id() # Hubzilla uses id instead of href

    class Meta:
        rdf_type = as2.Hashtag


class Mention(Link):

    class Meta:
        rdf_type = as2.Mention


class PropertyValue(Object):
    value = fields.RawJsonLD(schema.value,
                          metadata={'ctx':[{'schema':str(schema),'value':'schema:value'}]})
    ctx = [{'schema':str(schema),'PropertyValue':'schema:PropertyValue'}]

    class Meta:
        rdf_type = schema.PropertyValue


class IdentityProof(Object):
    signature_value = fields.String(sec.signatureValue)
    signing_algorithm = fields.String(sec.signingAlgorithm)
    ctx = [CONTEXT_SECURITY]

    class Meta:
        rdf_type = toot.IdentityProof


class Emoji(Object):
    ctx = [{'toot':'http://joinmastodon.org/ns#','Emoji':'toot:Emoji'}]

    class Meta:
        rdf_type = toot.Emoji


class Person(Object, base.Profile):
    id = fields.Id()
    inbox = IRI(ldp.inbox)
    outbox = IRI(as2.outbox)
    following = IRI(as2.following)
    followers = IRI(as2.followers)
    guid = fields.String(diaspora.guid, metadata={'ctx':[{'diaspora':str(diaspora)}]})
    handle = fields.String(diaspora.handle, metadata={'ctx':[{'diaspora':str(diaspora)}]})
    username = fields.String(as2.preferredUsername)
    endpoints = CompactedDict(as2.endpoints)
    shared_inbox = IRI(as2.sharedInbox) # misskey adds this
    playlists = IRI(pt.playlists)
    featured = IRI(toot.featured,
                   metadata={'ctx':[{'toot':str(toot),
                                     'featured': {'@id':'toot:featured','@type':'@id'}}]})
    featured_tags = IRI(toot.featuredTags,
                        metadata={'ctx':[{'toot':str(toot),
                                          'featuredTags': {'@id':'toot:featuredTags','@type':'@id'}}]})
    manually_approves_followers = fields.Boolean(as2.manuallyApprovesFollowers, default=False,
                                                 metadata={'ctx':[{'manuallyApprovesFollowers':'as:manuallyApprovesFollowers'}]})
    discoverable = fields.Boolean(toot.discoverable,
                                  metadata={'ctx':[{'toot':str(toot),
                                                    'discoverable': 'toot:discoverable'}]})
    devices = IRI(toot.devices)
    public_key_dict = CompactedDict(sec.publicKey,
                                    metadata={'ctx':[CONTEXT_SECURITY]})
    raw_content = fields.String(as2.summary, default='')
    has_address = MixedField(vcard.hasAddress, nested='HomeSchema')
    has_instant_message = fields.List(vcard.hasInstantMessage, cls_or_instance=fields.String)
    address = fields.String(vcard.Address)
    is_cat = fields.Boolean(misskey.isCat)
    moved_to = IRI(as2.movedTo,
                   metadata={'ctx':[{'movedTo':{'@id':'as:movedTo','@type':'@id'}}]})
    copied_to = IRI(as2.copiedTo,
                    metadata={'ctx':[{'copiedTo':{'@id':'as:copiedTo','@type':'@id'}}]})
    capabilities = CompactedDict(litepub.capabilities)
    suspended = fields.Boolean(toot.suspended,
                               metadata={'ctx':[{'toot':str(toot),
                                                 'suspended': 'toot:suspended'}]})
    url = MixedField(as2.url, nested='LinkSchema')
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
        self._required += ['url']
        self._allowed_children += (Note, PropertyValue, IdentityProof)

    # Set finger to username@host if not provided by the platform
    def post_receive(self):
        profile = get_profile(fid=self.id)
        if getattr(profile, 'finger', None):
            self.finger = profile.finger
        else:
            self.finger = get_finger_from_webfinger(self.id)
            # maybe we don't need this as the AS2 profile id
            # should be the source of truth
            if not self.finger:
                domain = urlparse(self.id).netloc
                finger = f'{self.username}@{domain}'
                if get_profile_id_from_webfinger(finger) == self.id:
                    self.finger = finger
        # multi-protocol platform
        if self.finger and self.guid is not missing and self.handle is missing:
            self.handle = self.finger
        # Some platforms don't set this property.
        if self.url is missing:
            self.url = self.id
        # Bluesky bridge profiles do this
        if isinstance(self.url, list):
            self.url = self.url[0]
        if isinstance(self.image, list):
            self.image = self.image[0]

    def to_as2(self):
        self.followers = f'{with_slash(self.id)}followers/'
        self.following = f'{with_slash(self.id)}following/'
        self.outbox = f'{with_slash(self.id)}outbox/'
        if isinstance(self.to, str): self.to = [self.to]
        if isinstance(self.image, str): self.image = Image(url=self.image)

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
    def key_id(self):
        if isinstance(self.public_key_dict, dict):
            return self.public_key_dict.get('id', None)

    @property
    def public_key(self):
        if self._cached_public_key: return self._cached_public_key

        if isinstance(self.public_key_dict, dict):
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
            url = icon if isinstance(icon, str) else icon.url
            self._cached_image_urls = {
                'small': url,
                'medium': url,
                'large': url
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
    conversation = fields.RawJsonLD(ostatus.conversation,
                                    metadata={'ctx':[{'ostatus':str(ostatus),
                                                      'conversation':'ostatus:conversation'}]})
    entity_type = 'Post'
    guid = fields.String(diaspora.guid, metadata={'ctx':[{'diaspora':str(diaspora)}]})
    in_reply_to_atom_uri = IRI(ostatus.inReplyToAtomUri,
                               metadata={'ctx':[{'ostatus':str(ostatus),
                               'inReplyToAtomUri':'ostatus:inReplyToAtomUri'}]})
    sensitive = fields.Boolean(as2.sensitive, default=False,
                               metadata={'ctx':[{'sensitive':'as:sensitive'}]})
    summary = fields.String(as2.summary)

    _cached_raw_content = ''
    _cached_children = []
    _soup = None
    signable = True

    def __init__(self, *args, **kwargs):
        self.tag_objects = [] # mutable objects...
        super().__init__(*args, **kwargs)
        self.raw_content  # must be "primed" with source property for inbound payloads
        self.rendered_content # must be "primed" with content_map property for inbound payloads
        self._allowed_children += (base.Audio, base.Video, Link)
        self._required.remove('raw_content')
        self._required += ['rendered_content']

    def to_as2(self):
        self.url = self.id

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
            '_mentions', '_media_type', '_source_object',
            '_cached_children', '_cached_raw_content', '_soup'))
        entity = Comment(**kwargs) if getattr(self, 'target_id') else Post(**kwargs)
        # Plume (and maybe other platforms) send the attrbutedTo field as an array
        if isinstance(entity.actor_id, list): entity.actor_id = entity.actor_id[0]

        set_public(entity)
        return entity

    def pre_send(self) -> None:
        """
        Attach any embedded images from raw_content.
        Add Hashtag and Mention objects (the client app must define the class tag/mention property)
        """
        super().pre_send()
        self._children = [
                Image(
                    url=image[0],
                    name=image[1],
                    inline=True,
                ) for image in self.embedded_images
                ]

        # Add Hashtag objects
        for el in self._soup('a', attrs={'class':'hashtag'}):
            self.tag_objects.append(Hashtag(
                href = el.attrs['href'],
                name = el.text
            ))
            self.tag_objects = sorted(self.tag_objects, key=attrgetter('name'))
            if el.text == '#nsfw': self.sensitive = True

        # Add Mention objects
        mentions = []
        for el in self._soup('a', attrs={'class':'mention'}):
            mentions.append(el.text.lstrip('@'))

        mentions.sort()
        for mention in mentions:
            if validate_handle(mention):
                profile = get_profile(finger__iexact=mention)
                # only add AP profiles mentions
                if getattr(profile, 'id', None):
                    self.tag_objects.append(Mention(href=profile.id, name='@'+mention))
                    # some platforms only render diaspora style markdown if it is available
                    self.source['content'] = self.source['content'].replace(mention, '{' + mention + '}')


    def post_receive(self) -> None:
        """
        Mark linkified tags and mentions with a data-{mention, tag} attribute.
        """
        super().post_receive()

        if self._media_type == "text/markdown":
            # Skip when markdown
            return

        self._find_and_mark_hashtags()
        self._find_and_mark_mentions()

        if getattr(self, 'target_id'): self.entity_type = 'Comment'

    def _find_and_mark_hashtags(self):
        hrefs = set()
        for tag in self.tag_objects:
            if isinstance(tag, Hashtag):
                if tag.href is not missing:
                    hrefs.add(unquote(tag.href).lower())
                # Some platforms use id instead of href...
                elif tag.id is not missing:
                    hrefs.add(unquote(tag.id).lower())

        for link in self._soup.find_all('a', href=True):
            parsed = urlparse(unquote(link['href']).lower())
            # remove the query part and trailing garbage, if any
            path = parsed.path
            trunc = re.match(r'(/[\w/\-]+)', parsed.path)
            if trunc:
                path = trunc.group()
            url = f'{parsed.scheme}://{parsed.netloc}{path}'
            # convert accented characters to their ascii equivalent
            normalized_path = normalize('NFD', path).encode('ascii', 'ignore')
            normalized_url = f'{parsed.scheme}://{parsed.netloc}{normalized_path.decode()}'
            links = {link['href'].lower(), unquote(link['href']).lower(), url, normalized_url}
            if links.intersection(hrefs):
                tag = re.match(r'^#?([\w\-]+)', link.text)
                if tag:
                    link['data-hashtag'] = tag.group(1).lower()

    def _find_and_mark_mentions(self):
        mentions = [mention for mention in self.tag_objects if isinstance(mention, Mention)]
        # There seems to be consensus on using the profile url for
        # the link and the profile id for the Mention object href property,
        # but some platforms will set mention.href to the profile url, so
        # we check both.
        for mention in mentions:
            hrefs = []
            profile = get_profile_or_entity(fid=mention.href, remote_url=mention.href)
            if profile and not (profile.url and profile.finger):
                # This should be removed when we are confident that the remote_url and
                # finger properties have been populated for most profiles on the client app side.
                profile = retrieve_and_parse_profile(profile.id)
            if profile and profile.finger:
                hrefs.extend([profile.id, profile.url])
            else:
                continue
            for href in hrefs:
                links = self._soup.find_all(href=href)
                for link in links:
                    link['data-mention'] = profile.finger
                    self._mentions.add(profile.finger)
            if profile.finger not in self._mentions:
                # can't find some mentions using their href property value
                # try with the name property
                matches = self._soup.find_all(string=mention.name)
                for match in matches:
                    link = match.find_parent('a')
                    if link:
                        link['data-mention'] = profile.finger
                        self._mentions.add(profile.finger)

    def extract_mentions(self):
        """
        Attempt to extract mentions from raw_content if available
        """

        if self.raw_content:
            super().extract_mentions()
        return

    @property
    def rendered_content(self):
        if self._soup: return str(self._soup)
        content = ''
        if self.content_map:
            orig = self.content_map.pop('orig')
            if len(self.content_map.keys()) > 1:
                logger.warning('Language selection not implemented, falling back to default')
                content = orig.strip()
            else:
                content = orig.strip() if len(self.content_map.keys()) == 0 else next(iter(self.content_map.values())).strip()
            self.content_map['orig'] = orig
        # to allow for posts/replies with medias only.
        if not content: content = "<div></div>"
        self._soup = BeautifulSoup(content, 'html.parser')
        return str(self._soup)

    @rendered_content.setter
    def rendered_content(self, value):
        if not value: return
        self._soup = BeautifulSoup(value, 'html.parser')
        self.content_map = {'orig': value}

    @property
    def raw_content(self):
        if self._cached_raw_content: return self._cached_raw_content

        if isinstance(self.source, dict) and self.source.get('mediaType') == 'text/markdown':
            self._media_type = self.source['mediaType']
            self._cached_raw_content = self.source.get('content').strip()
        else:
            self._media_type = 'text/html'
            self._cached_raw_content = ""
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
                if isinstance(child, (Document, Link)):
                    if hasattr(child, 'to_base'):
                        child = child.to_base()
                    if isinstance(child, Image):
                        if child.inline or self._soup.find('img', src=child.url):
                            continue
                    children.append(child)
            self._cached_children = children

        return self._cached_children
    
    @_children.setter
    def _children(self, value):
        if not value: return
        self._cached_children = value
        self.attachment = [Image.from_base(i) for i in value]

    def validate_actor_id(self):
        if not self.actor_id.startswith('http'):
            raise ValueError(f'Invalid actor_id for activitypub ({self.actor_id})')

    class Meta:
        rdf_type = as2.Note


class Post(Note, base.Post):
    class Meta:
        rdf_type = as2.Note


class Comment(Note, base.Comment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ['target_id']

    def validate_target_id(self):
        if not self.target_id.startswith('http'):
            raise ValueError(f'Invalid target_id for activitypub ({self.target_id})')

    class Meta:
        rdf_type = as2.Note


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
    signable = True
    views = fields.Integer(pt.views)

    class Meta:
        unknown = EXCLUDE # required until all the pt fields are defined
        rdf_type = as2.Video

    def to_base(self):
        """Turn Peertube Video object into a Post
        Is Peertube content if the views property is not missing
        """
        
        self.__dict__.update({'schema': True})
        if self.views is not missing:
            text = ""
            if self.content_map is not missing:
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

            if self.actor_id is not missing:
                act = self.actor_id
                new_act = []
                if not isinstance(act, list): act = [act]
                for a in act:
                    if isinstance(a, Person):
                        new_act.append(a.id)
                # TODO: fix extract_receivers which can't handle multiple actors!
                self.actor_id = new_act[0]
            
            entity = Post(**get_base_attributes(self,
                keep=('_mentions', '_media_type', '_soup',
                      '_cached_children', '_cached_raw_content', '_source_object')))
            set_public(entity)
            return entity
        #Some Video object
        else:
            return self


class RsaSignature2017(Object):
    created = fields.DateTime(dc.created, add_value_types=True)
    creator = IRI(dc.creator)
    key = fields.String(sec.signatureValue)
    nonce = fields.String(sec.nonce)

    class Meta:
        rdf_type = sec.RsaSignature2017


class Activity(Object):
    actor_id = IRI(as2.actor)
    instrument = MixedField(as2.instrument, nested='ServiceSchema')
    target = MixedField(as2.target, nested=['CollectionSchema', 'OrderedCollectionSchema'])
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
        if isinstance(self.activity, Undo):
            self.following = False

        # Ensure the Accept activity is returned to the client app.
        if isinstance(self.activity, Accept):
            return self.activity

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
            object_=self,
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
        exclude = ('created_at',)


class Announce(Activity, base.Share):
    id = fields.Id()
    target_id = IRI(as2.object)
    signable = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ['target_id']

    def validate_target_id(self):
        if not self.target_id.startswith('http'):
            raise ValueError(f'Invalid target_id for activitypub ({self.target_id})')

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
            entity = Retraction(**get_base_attributes(self, keep=('_source_object',)))

        set_public(entity)
        return entity

    class Meta:
        rdf_type = as2.Announce


# Only used for inbound share retraction (undo announce)
class Retraction(Announce, base.Retraction):
    class Meta:
        rdf_type = as2.Announce


class Tombstone(Object, base.Retraction):
    target_id = fields.Id()
    signable = True

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
        if self.activity and self.activity != self: self.actor_id = self.activity.actor_id
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

class Add(Create):
    class Meta:
        rdf_type = as2.Add

# this is only a placeholder until reactions are implemented
class Like(Activity, base.Reaction):
    id = fields.Id()
    reaction = fields.String(diaspora.like)

    def validate(self, direction='inbound'):
        pass

    class Meta:
        rdf_type = as2.Like


# inbound Accept is a noop...
class Accept(Create, base.Accept):
    def validate(self, direction='inbound'):
        pass

    class Meta:
        rdf_type = as2.Accept
        exclude = ('created_at',)


class Delete(Create, base.Retraction):
    signable = True

    def to_base(self):
        self.entity_type = 'Unsupported'
        if not isinstance(self.object_, Tombstone):
            self.target_id = self.object_
            self.entity_type = 'Profile'
        return self

    class Meta:
        rdf_type = as2.Delete


class Update(Create):
    class Meta:
        rdf_type = as2.Update


class Undo(Create, base.Retraction):
    class Meta:
        rdf_type = as2.Undo
        exclude = ('created_at',)


class View(Create):
    class Meta:
        rdf_type = as2.View


def process_followers(obj, base_url):
    pass

def extract_receiver(author, receiver):
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

    # This handles cases where the actor is sending to other actors
    # followers (seen on PeerTube)
    if isinstance(obj, base.Collection):
        profile = get_profile(followers_fid=obj.id)
        if profile:
            return [UserType(id=profile.id, receiver_variant=ReceiverVariant.FOLLOWERS)]

    if author.followers == receiver:
        return [UserType(id=author.id, receiver_variant=ReceiverVariant.FOLLOWERS)]

    return []

def extract_receivers(entity):
    """
    Extract receivers from a payload.
    """
    receivers = []
    profile = None
    # don't care about receivers for payloads without an actor_id    
    if getattr(entity, 'actor_id'):
        profile = get_profile_or_entity(fid=entity.actor_id)
    if not isinstance(profile, base.Profile):
        return receivers
    
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

    # Extract mentions
    if hasattr(entity, "extract_mentions"):
        entity.extract_mentions()

    if hasattr(entity, "post_receive"):
        entity.post_receive()

    if hasattr(entity, 'validate'): entity.validate()



def extract_replies(replies):
    objs = []
    visited = []

    def walk_reply_collection(replies):
        if isinstance(replies, str):
            # deal with gotosocial reply collections
            replies = retrieve_and_parse_document(replies, cache=False)
        if not hasattr(replies, 'items'): return
        items = replies.items if replies.items is not missing else []
        if not isinstance(items, list): items = [items]
        for obj in items:
            if isinstance(obj, Note):
                try:
                    obj = obj.to_base()
                    extract_and_validate(obj)
                except ValueError as ex:
                    logger.error("extract_replies - Failed to validate entity %s: %s", obj, ex)
                    continue
            elif not isinstance(obj, str): continue
            objs.append(obj)
        if getattr(replies, 'next_', None) not in (missing, None):
            if (replies.id != replies.next_) and (replies.next_ not in visited):
                resp = retrieve_and_parse_document(replies.next_, cache=False)
                if resp:
                    visited.append(replies.next_)
                    walk_reply_collection(resp)

    walk_reply_collection(replies)
    return objs


def element_to_objects(element: Union[Dict, Object], sender: str = "") -> List:
    """
    Transform an Element to a list of entities.
    """

    # json-ld handling with calamus
    # Skips unimplemented payloads
    entity = model_to_objects(element) if not isinstance(element, Object) else element
    if entity and hasattr(entity, 'to_base'):
        entity = entity.to_base()
        entity._sender = sender
    if isinstance(entity, (
        base.Post, base.Comment, base.Profile, base.Share, base.Follow,
        base.Retraction, base.Accept,)
        ):
        try:
            extract_and_validate(entity)
        except ValueError as ex:
            logger.error("Failed to validate entity %s: %s", entity, ex)
            return []
        except InvalidSignature as exc:
            if isinstance(entity, base.Retraction):
                logger.warning('Relayed retraction on %s, ignoring', entity.target_id)
                return []
            logger.info('%s, fetching from remote', exc)
            entity = retrieve_and_parse_document(entity.id)
            if not entity:
                return []
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
    original_payload = copy.copy(payload)
    model = globals().get(payload.get('type'))
    if model and issubclass(model, Object):
        try:
            entity = model.schema().load(payload)
        except (KeyError, jsonld.JsonLdError, exceptions.ValidationError) as exc :  # Just give up for now. This must be made robust
            logger.error("Error parsing jsonld payload (%s)", exc)
            return None

        # The activity property chains the payload activity objects in reverse order
        while isinstance(getattr(entity, 'object_', None), Object):
            entity.object_.activity = entity
            entity = entity.object_

        entity._source_object = original_payload
        return entity
    return None


CLASSES_WITH_CONTEXT_EXTENSIONS = (
    Document,
    Emoji,
    Hashtag,
    IdentityProof,
    Note,
    Person,
    PropertyValue
)
context_manager = LdContextManager(CLASSES_WITH_CONTEXT_EXTENSIONS)


MODEL_NAMES = {}
for key,val in copy.copy(globals()).items():
    if type(val) == JsonLDAnnotation and issubclass(val, (Object, Link)):
        MODEL_NAMES[key.lower()] = key
