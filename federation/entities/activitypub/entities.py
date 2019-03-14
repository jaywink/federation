from typing import Dict

from federation.entities.activitypub.constants import (
    CONTEXTS_DEFAULT, CONTEXT_MANUALLY_APPROVES_FOLLOWERS, CONTEXT_SENSITIVE, CONTEXT_HASHTAG,
    CONTEXT_LD_SIGNATURES)
from federation.entities.activitypub.enums import ActorType, ObjectType, ActivityType
from federation.entities.activitypub.mixins import ActivitypubEntityMixin
from federation.entities.base import Profile, Post, Follow
from federation.utils.text import with_slash


class ActivitypubFollow(ActivitypubEntityMixin, Follow):
    _type = ActivityType.FOLLOW.value

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
                "sharedInbox": f"{with_slash(self.base_url)}ap/inbox/",  # TODO just get from config
            },
            "followers": f"{with_slash(self.id)}followers/",
            "following": f"{with_slash(self.id)}following/",
            "id": self.id,
            "inbox": f"{with_slash(self.id)}inbox/",
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
