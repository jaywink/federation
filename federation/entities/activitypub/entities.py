import logging
import uuid
from typing import Dict

import attr
from commonmark import commonmark

from federation.entities.activitypub.constants import (
    CONTEXTS_DEFAULT, CONTEXT_MANUALLY_APPROVES_FOLLOWERS, CONTEXT_SENSITIVE, CONTEXT_HASHTAG,
    CONTEXT_LD_SIGNATURES)
from federation.entities.activitypub.enums import ActorType, ObjectType, ActivityType
from federation.entities.activitypub.mixins import ActivitypubEntityMixin, CleanContentMixin, AttachImagesMixin
from federation.entities.activitypub.objects import ImageObject
from federation.entities.base import Profile, Post, Follow, Accept, Comment, Retraction, Share
from federation.outbound import handle_send
from federation.types import UserType
from federation.utils.text import with_slash

logger = logging.getLogger("federation")


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


class ActivitypubNoteMixin(AttachImagesMixin, CleanContentMixin, ActivitypubEntityMixin):
    _type = ObjectType.NOTE.value

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
                "content": commonmark(self.raw_content).strip(),
                "published": self.created_at.isoformat(),
                "inReplyTo": None,
                "sensitive": True if "nsfw" in self.tags else False,
                "summary": None,  # TODO Short text? First sentence? First line?
                "tag": [],  # TODO add tags
                "url": self.url,
                'source': {
                    'content': self.raw_content,
                    'mediaType': 'text/markdown',
                },
            },
            "published": self.created_at.isoformat(),
        }
        if len(self._children):
            as2["object"]["attachment"] = []
            for child in self._children:
                image = ImageObject(url=child.url)
                if image.mediaType:
                    as2["object"]["attachment"].append({
                        "type": "Document",
                        "mediaType": image.mediaType,
                        "name": child.name,
                        "url": child.url,
                    })
        return as2


class ActivitypubComment(ActivitypubNoteMixin, Comment):
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
        if not self.following:
            return

        from federation.utils.activitypub import retrieve_and_parse_profile  # Circulars
        try:
            from federation.utils.django import get_function_from_config
        except ImportError:
            logger.warning("ActivitypubFollow.post_receive - Unable to send automatic Accept back, only supported on "
                           "Django currently")
            return
        get_private_key_function = get_function_from_config("get_private_key_function")
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
        try:
            profile = retrieve_and_parse_profile(self.actor_id)
        except Exception:
            profile = None
        if not profile:
            logger.warning("ActivitypubFollow.post_receive - Failed to fetch remote profile for sending back Accept")
            return
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


class ActivitypubPost(ActivitypubNoteMixin, Post):
    pass


class ActivitypubProfile(ActivitypubEntityMixin, Profile):
    _type = ActorType.PERSON.value
    public = True

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
                as2['icon'] = attr.asdict(ImageObject(url=self.image_urls.get('large')))
            except Exception as ex:
                logger.warning("ActivitypubProfile.to_as2 - failed to set profile icon: %s", ex)
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
