from typing import Dict

from federation.entities.activitypub.constants import CONTEXTS_DEFAULT
from federation.entities.activitypub.enums import ActorType
from federation.entities.activitypub.mixins import ActivitypubEntityMixin
from federation.entities.base import Profile


class ActivitypubProfile(ActivitypubEntityMixin, Profile):
    _type = ActorType.PERSON.value

    def to_as2(self) -> Dict:
        as2 = {
            "@context": CONTEXTS_DEFAULT + [
                {"manuallyApprovesFollowers": "as:manuallyApprovesFollowers"},
            ],
            "type": self._type,
            "name": self.name,
            "url": self.url,
            "id": self.id,
            "inbox": f"{self.id}inbox/",  # TODO add slash if none at end
            "outbox": f"{self.id}outbox/",  # TODO add slash if none at end
            "manuallyApprovesFollowers": False,
            "publicKey": {
                "id": f"{self.id}#main-key",
                "owner": self.id,
                "publicKeyPem": self.public_key,
            },
            "endpoints": {
                "sharedInbox": f"{self.base_url}/ap/inbox/",
            },
        }
        if self.username:
            as2['preferredUsername'] = self.username
        if self.raw_content:
            as2['summary'] = self.raw_content
        if self.image_urls.get('large'):
            as2['icon'] = self.image_urls.get('large')
        return as2
