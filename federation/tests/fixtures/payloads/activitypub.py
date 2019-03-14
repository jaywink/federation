ACTIVITYPUB_FOLLOW = {
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/security/v1",
  ],
  "id": "https://example.com/follow",
  "type": "Follow",
  "actor": "https://example.com/actor",
  "object": "https://example.org/actor",
  "signature": {
    "type": "RsaSignature2017",
    "creator": "https://example.com/actor#main-key",
    "created": "2018-10-11T15:59:32Z",
    "signatureValue": "foobar"
  }
}

ACTIVITYPUB_PROFILE = {
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/security/v1",
    {
      "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
      "sensitive": "as:sensitive",
      "movedTo": {
        "@id": "as:movedTo",
        "@type": "@id"
      },
      "alsoKnownAs": {
        "@id": "as:alsoKnownAs",
        "@type": "@id"
      },
      "Hashtag": "as:Hashtag",
      "ostatus": "http://ostatus.org#",
      "atomUri": "ostatus:atomUri",
      "inReplyToAtomUri": "ostatus:inReplyToAtomUri",
      "conversation": "ostatus:conversation",
      "toot": "http://joinmastodon.org/ns#",
      "Emoji": "toot:Emoji",
      "focalPoint": {
        "@container": "@list",
        "@id": "toot:focalPoint"
      },
      "featured": {
        "@id": "toot:featured",
        "@type": "@id"
      },
      "schema": "http://schema.org#",
      "PropertyValue": "schema:PropertyValue",
      "value": "schema:value"
    }
  ],
  "id": "https://diaspodon.fr/users/jaywink",
  "type": "Person",
  "following": "https://diaspodon.fr/users/jaywink/following",
  "followers": "https://diaspodon.fr/users/jaywink/followers",
  "inbox": "https://diaspodon.fr/users/jaywink/inbox",
  "outbox": "https://diaspodon.fr/users/jaywink/outbox",
  "featured": "https://diaspodon.fr/users/jaywink/collections/featured",
  "preferredUsername": "jaywink",
  "name": "Jason Robinson",
  "summary": "<p>Temp account while implementing AP for Socialhome.</p><p><a href=\"https://jasonrobinson.me\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">jasonrobinson.me</span><span class=\"invisible\"></span></a> / <a href=\"https://socialhome.network\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">socialhome.network</span><span class=\"invisible\"></span></a> / <a href=\"https://feneas.org\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">feneas.org</span><span class=\"invisible\"></span></a></p>",
  "url": "https://diaspodon.fr/@jaywink",
  "manuallyApprovesFollowers": False,
  "publicKey": {
    "id": "https://diaspodon.fr/users/jaywink#main-key",
    "owner": "https://diaspodon.fr/users/jaywink",
    "publicKeyPem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwVbaT5wvaZobfIB044ai\nhJg/XooEn2jSTnTY1K4mPmhdqYUmszpdXKp64OwA+f3SBuIUIkLAYUSB9Fu19zh+\nzOsoGI5gvA32DHY1vaqdKnT9gt3jKS5AdQ3bl0t9f4pPkO2I5YtQOWV1FvBcwPXG\nB0dIqj0fTqNK37FmyybrRD6uhjySddklN9gNsULTqYVDa0QSXVswTIW2jQudnNlp\nnEf3SfjlK9J8eKPF3hFK3PNXBTTZ4NydBSL3cVBinU0cFg8lUJOK8RI4qaetrVoQ\neKd7gCTSQ7RZh8kmkYmdlweb+ZtORT6Y5ZsotR8jwhAOFAqCt36B5+LX2UIw68Pk\nOwIDAQAB\n-----END PUBLIC KEY-----\n"
  },
  "tag": [],
  "attachment": [],
  "endpoints": {
    "sharedInbox": "https://diaspodon.fr/inbox"
  },
  "icon": {
    "type": "Image",
    "mediaType": "image/jpeg",
    "url": "https://diaspodon.fr/system/accounts/avatars/000/033/155/original/pnc__picked_media_be51984c-43e9-4266-9b9a-b74a61ae4167.jpg?1538505110"
  },
  "image": {
    "type": "Image",
    "mediaType": "image/png",
    "url": "https://diaspodon.fr/system/accounts/headers/000/033/155/original/45ae49a08ecc5f27.png?1537060098"
  }
}
