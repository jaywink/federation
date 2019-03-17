import logging
import uuid
from typing import Dict

from federation.entities.activitypub.constants import (
    CONTEXTS_DEFAULT, CONTEXT_MANUALLY_APPROVES_FOLLOWERS, CONTEXT_SENSITIVE, CONTEXT_HASHTAG,
    CONTEXT_LD_SIGNATURES)
from federation.entities.activitypub.enums import ActorType, ObjectType, ActivityType
from federation.entities.activitypub.mixins import ActivitypubEntityMixin
from federation.entities.base import Profile, Post, Follow, Accept
from federation.outbound import handle_send
from federation.types import UserType
from federation.utils.text import with_slash

logger = logging.getLogger("federation")


class ActivitypubAccept(ActivitypubEntityMixin, Accept):
    _type = ActivityType.ACCEPT.value

    def to_as2(self) -> Dict:
        as2 = {
            "@context": CONTEXTS_DEFAULT,
            "id": self.activity_id,
            "type": self._type,
            "actor": self.actor_id,
            "object": self.target_id,
        }
        return as2


class ActivitypubFollow(ActivitypubEntityMixin, Follow):
    _type = ActivityType.FOLLOW.value

    def post_receive(self, attributes: Dict) -> None:
        """
        Post receive hook - send back follow ack.
        """
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
        )
        try:
            handle_send(accept, UserType(id=self.target_id, private_key=key), recipients=[self.actor_id])
        except Exception:
            logger.exception("ActivitypubFollow.post_receive - Failed to send Accept back")

    def to_as2(self) -> Dict:
        as2 = {
            "@context": CONTEXTS_DEFAULT,
            "id": self.activity_id,
            "type": self._type,
            "actor": self.actor_id,
            "object": self.target_id,
        }
        return as2


class ActivitypubPost(ActivitypubEntityMixin, Post):
    _type = ObjectType.NOTE.value

    def to_as2(self) -> Dict:
        # TODO add in sending phase:
        # - to
        # - cc
        # - bcc
        as2 = {
            "@context": CONTEXTS_DEFAULT + [
                CONTEXT_HASHTAG,
                CONTEXT_SENSITIVE,
            ],
            "attributedTo": self.actor_id,
            "content": self.raw_content,  # TODO render to html, add source markdown
            "id": self.id,
            "inReplyTo": None,
            "published": self.created_at.isoformat(),
            "sensitive": True if "nsfw" in self.tags else False,
            "summary": None,  # TODO Short text? First sentence? First line?
            "tag": [],  # TODO add tags
            "type": self._type,
            "url": self.url,
        }
        return as2


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
            as2['icon'] = self.image_urls.get('large')
        return as2
