import logging
import uuid
from typing import Dict, List

import bleach

from federation.entities.activitypub.constants import (
    CONTEXTS_DEFAULT, CONTEXT_MANUALLY_APPROVES_FOLLOWERS, CONTEXT_SENSITIVE, CONTEXT_HASHTAG,
    CONTEXT_LD_SIGNATURES, CONTEXT_DIASPORA)
from federation.entities.activitypub.enums import ActorType, ObjectType, ActivityType
from federation.entities.base import Profile, Post, Follow, Accept, Comment, Retraction, Share, Image, Audio, Video
from federation.entities.mixins import RawContentMixin, BaseEntity, PublicMixin, CreatedAtMixin
from federation.entities.utils import get_base_attributes
from federation.outbound import handle_send
from federation.types import UserType
from federation.utils.django import get_configuration
from federation.utils.text import with_slash, validate_handle

logger = logging.getLogger("federation")


class AttachImagesMixin(RawContentMixin):
    def pre_send(self) -> None:
        """
        Attach any embedded images from raw_content.
        """
        super().pre_send()
        self._children += [
                ActivitypubImage(
                    url=image[0],
                    name=image[1],
                    inline=True,
                ) for image in self.embedded_images
                ]


class ActivitypubEntityMixin():
    _type = None

    @classmethod
    def from_base(cls, entity):
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    def to_string(self):
        # noinspection PyUnresolvedReferences
        return str(self.to_as2())


class CleanContentMixin(RawContentMixin):
    def post_receive(self) -> None:
        """
        Make linkified tags normal tags.
        """
        super().post_receive()

        # noinspection PyUnusedLocal
        def remove_tag_links(attrs, new=False):
            rel = (None, "rel")
            if attrs.get(rel) == "tag":
                return
            return attrs

        if self._media_type == "text/markdown":
            # Skip when markdown
            return

        self.raw_content = bleach.linkify(
            self.raw_content,
            callbacks=[remove_tag_links],
            parse_email=False,
            skip_tags=["code", "pre"],
        )


class ActivitypubAccept(ActivitypubEntityMixin, Accept):
    _type = ActivityType.ACCEPT.value
    object: Dict = None

    def to_as2(self) -> Dict:
        as2 = {
            "@context": CONTEXTS_DEFAULT,
            "id": self.activity_id,
            "type": self._type,
            "actor": self.actor_id,
            "object": self.object,
        }
        return as2


class ActivitypubNoteMixin(AttachImagesMixin, CleanContentMixin, PublicMixin, CreatedAtMixin, ActivitypubEntityMixin):
    _type = ObjectType.NOTE.value
    url = ""

    def add_object_tags(self) -> List[Dict]:
        """
        Populate tags to the object.tag list.
        """
        tags = []
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
            _tag = {
                'type': 'Hashtag',
                'name': f'#{tag}',
            }
            if tags_path:
                _tag["href"] = tags_path.replace(":tag:", tag)
            tags.append(_tag)
        return tags

    def extract_mentions(self):
        """
        Extract mentions from the source object.
        """
        super().extract_mentions()

        if getattr(self, 'tag_list', None):
            from federation.entities.activitypub.models import Mention # Circulars
            tag_list = self.tag_list if isinstance(self.tag_list, list) else [self.tag_list]
            for tag in tag_list:
                if isinstance(tag, Mention):
                    self._mentions.add(tag.href)

        #if not isinstance(self._source_object, dict):
        #    return
        #source = self._source_object.get('object') if isinstance(self._source_object.get('object'), dict) else \
        #    self._source_object
        #for tag in source.get('tag', []):
        #    if tag.get('type') == "Mention" and tag.get('href'):
        #        self._mentions.add(tag.get('href'))

    def pre_send(self):
        super().pre_send()
        self.extract_mentions()

    def to_as2(self) -> Dict:
        as2 = {
            "@context": CONTEXTS_DEFAULT + [
                CONTEXT_HASHTAG,
                CONTEXT_LD_SIGNATURES,
                CONTEXT_SENSITIVE,
            ],
            "type": self.activity.value,
            "id": self.activity_id,
            "actor": self.actor_id,
            "object": {
                "id": self.id,
                "type": self._type,
                "attributedTo": self.actor_id,
                "content": self.rendered_content,
                "published": self.created_at.isoformat(),
                "inReplyTo": None,
                "sensitive": True if "nsfw" in self.tags else False,
                "summary": None,  # TODO Short text? First sentence? First line?
                "url": self.url,
                'source': {
                    'content': self.raw_content,
                    'mediaType': self._media_type,
                },
                "tag": [],
            },
            "published": self.created_at.isoformat(),
        }

        if len(self._children):
            as2["object"]["attachment"] = []
            for child in self._children:
                as2["object"]["attachment"].append(child.to_as2())

        if len(self._mentions):
            mentions = list(self._mentions)
            mentions.sort()
            for mention in mentions:
                if mention.startswith("http"):
                    as2["object"]["tag"].append({
                        'type': 'Mention',
                        'href': mention,
                        'name': mention,
                    })
                elif validate_handle(mention):
                    # Look up via WebFinger
                    as2["object"]["tag"].append({
                        'type': 'Mention',
                        'href': mention,  # TODO need to implement fetch via webfinger for AP handles first
                        'name': mention,
                    })

        as2["object"]["tag"].extend(self.add_object_tags())

        if self.guid:
            as2["@context"].append(CONTEXT_DIASPORA)
            as2["object"]["diaspora:guid"] = self.guid

        return as2


class ActivitypubComment(ActivitypubNoteMixin, Comment):
    entity_type = "Comment"

    def to_as2(self) -> Dict:
        as2 = super().to_as2()
        as2["object"]["inReplyTo"] = self.target_id
        return as2


class ActivitypubFollow(ActivitypubEntityMixin, Follow):
    _type = ActivityType.FOLLOW.value

    def post_receive(self) -> None:
        """
        Post receive hook - send back follow ack.
        """
        super().post_receive()

        if not self.following:
            return

        from federation.utils.activitypub import retrieve_and_parse_profile  # Circulars
        try:
            from federation.utils.django import get_function_from_config
            get_private_key_function = get_function_from_config("get_private_key_function")
        except (ImportError, AttributeError):
            logger.warning("ActivitypubFollow.post_receive - Unable to send automatic Accept back, only supported on "
                           "Django currently")
            return
        key = get_private_key_function(self.target_id)
        if not key:
            logger.warning("ActivitypubFollow.post_receive - Failed to send automatic Accept back: could not find "
                           "profile to sign it with")
            return
        accept = ActivitypubAccept(
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
            logger.warning("ActivitypubFollow.post_receive - Failed to fetch remote profile for sending back Accept")
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
            logger.exception("ActivitypubFollow.post_receive - Failed to send Accept back")

    def to_as2(self) -> Dict:
        if self.following:
            as2 = {
                "@context": CONTEXTS_DEFAULT,
                "id": self.activity_id,
                "type": self._type,
                "actor": self.actor_id,
                "object": self.target_id,
            }
        else:
            as2 = {
                "@context": CONTEXTS_DEFAULT,
                "id": self.activity_id,
                "type": ActivityType.UNDO.value,
                "actor": self.actor_id,
                "object": {
                    "id": f"{self.actor_id}#follow-{uuid.uuid4()}",
                    "type": self._type,
                    "actor": self.actor_id,
                    "object": self.target_id,
                },
            }
        return as2


class ActivitypubImage(ActivitypubEntityMixin, Image):
    _type = ObjectType.IMAGE.value

    def to_as2(self) -> Dict:
        return {
            "type": self._type,
            "url": self.url,
            "mediaType": self.media_type,
            "name": self.name,
            "pyfed:inlineImage": self.inline,
        }

class ActivitypubAudio(ActivitypubEntityMixin, Audio):
    pass

class ActivitypubVideo(ActivitypubEntityMixin, Video):
    pass

class ActivitypubPost(ActivitypubNoteMixin, Post):
    pass


class ActivitypubProfile(ActivitypubEntityMixin, Profile):
    _type = ActorType.PERSON.value
    public = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_as2(self) -> Dict:
        as2 = {
            "@context": CONTEXTS_DEFAULT + [
                CONTEXT_LD_SIGNATURES,
                CONTEXT_MANUALLY_APPROVES_FOLLOWERS,
            ],
            "endpoints": {
                "sharedInbox": self.inboxes["public"],
            },
            "followers": f"{with_slash(self.id)}followers/",
            "following": f"{with_slash(self.id)}following/",
            "id": self.id,
            "inbox": self.inboxes["private"],
            "manuallyApprovesFollowers": False,
            "name": self.name,
            "outbox": f"{with_slash(self.id)}outbox/",
            "publicKey": {
                "id": f"{self.id}#main-key",
                "owner": self.id,
                "publicKeyPem": self.public_key,
            },
            "type": self._type,
            "url": self.url,
        }
        if self.username:
            as2['preferredUsername'] = self.username
        if self.raw_content:
            as2['summary'] = self.raw_content
        if self.image_urls.get('large'):
            try:
                profile_icon = ActivitypubImage(url=self.image_urls.get('large'))
                if profile_icon.media_type:
                    as2['icon'] = profile_icon.to_as2()
            except Exception as ex:
                logger.warning("ActivitypubProfile.to_as2 - failed to set profile icon: %s", ex)

        if self.guid or self.handle:
            as2["@context"].append(CONTEXT_DIASPORA)
            if self.guid:
                as2["diaspora:guid"] = self.guid
            if self.handle:
                as2["diaspora:handle"] = self.handle

        return as2


class ActivitypubRetraction(ActivitypubEntityMixin, Retraction):
    def resolve_object_type(self):
        return {
            "Comment": ObjectType.TOMBSTONE.value,
            "Post": ObjectType.TOMBSTONE.value,
            "Share": ActivityType.ANNOUNCE.value,
        }.get(self.entity_type)

    def resolve_type(self):
        return {
            "Comment": ActivityType.DELETE.value,
            "Post": ActivityType.DELETE.value,
            "Share": ActivityType.UNDO.value,
        }.get(self.entity_type)

    def to_as2(self) -> Dict:
        as2 = {
            "@context": CONTEXTS_DEFAULT,
            "id": self.activity_id,
            "type": self.resolve_type(),
            "actor": self.actor_id,
            "object": {
                "id": self.target_id,
                "type": self.resolve_object_type(),
            },
            "published": self.created_at.isoformat(),
        }
        return as2


class ActivitypubShare(ActivitypubEntityMixin, Share):
    _type = ActivityType.ANNOUNCE.value

    def to_as2(self) -> Dict:
        as2 = {
            "@context": CONTEXTS_DEFAULT,
            "id": self.activity_id,
            "type": self._type,
            "actor": self.actor_id,
            "object": self.target_id,
            "published": self.created_at.isoformat(),
        }
        return as2
