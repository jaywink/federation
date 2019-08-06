ACTIVITYPUB_COMMENT = {
  '@context': ['https://www.w3.org/ns/activitystreams',
  {'ostatus': 'http://ostatus.org#',
   'atomUri': 'ostatus:atomUri',
   'inReplyToAtomUri': 'ostatus:inReplyToAtomUri',
   'conversation': 'ostatus:conversation',
   'sensitive': 'as:sensitive',
   'Hashtag': 'as:Hashtag',
   'toot': 'http://joinmastodon.org/ns#',
   'Emoji': 'toot:Emoji',
   'focalPoint': {'@container': '@list', '@id': 'toot:focalPoint'},
   'blurhash': 'toot:blurhash'}],
 'id': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237/activity',
 'type': 'Create',
 'actor': 'https://diaspodon.fr/users/jaywink',
 'published': '2019-06-29T21:08:45Z',
 'to': ['https://www.w3.org/ns/activitystreams#Public'],
 'cc': ['https://diaspodon.fr/users/jaywink/followers',
  'https://dev.jasonrobinson.me/p/d4574854-a5d7-42be-bfac-f70c16fcaa97/'],
 'object': {'id': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237',
  'type': 'Note',
  'summary': None,
  'inReplyTo': 'https://dev.jasonrobinson.me/content/653bad70-41b3-42c9-89cb-c4ee587e68e4/',
  'published': '2019-06-29T21:08:45Z',
  'url': 'https://diaspodon.fr/@jaywink/102356911717767237',
  'attributedTo': 'https://diaspodon.fr/users/jaywink',
  'to': ['https://www.w3.org/ns/activitystreams#Public'],
  'cc': ['https://diaspodon.fr/users/jaywink/followers',
   'https://dev.jasonrobinson.me/p/d4574854-a5d7-42be-bfac-f70c16fcaa97/'],
  'sensitive': False,
  'atomUri': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237',
  'inReplyToAtomUri': 'https://dev.jasonrobinson.me/content/653bad70-41b3-42c9-89cb-c4ee587e68e4/',
  'conversation': 'tag:diaspodon.fr,2019-06-28:objectId=2347687:objectType=Conversation',
  'content': '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" class="u-url mention">@<span>jaywink</span></a></span> boom</p>',
  'contentMap': {'en': '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" class="u-url mention">@<span>jaywink</span></a></span> boom</p>'},
  'attachment': [],
  'tag': [{'type': 'Mention',
    'href': 'https://dev.jasonrobinson.me/p/d4574854-a5d7-42be-bfac-f70c16fcaa97/',
    'name': '@jaywink@dev.jasonrobinson.me'}],
  'replies': {'id': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237/replies',
   'type': 'Collection',
   'first': {'type': 'CollectionPage',
    'partOf': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237/replies',
    'items': []}}},
 'signature': {'type': 'RsaSignature2017',
  'creator': 'https://diaspodon.fr/users/jaywink#main-key',
  'created': '2019-06-29T21:08:45Z',
  'signatureValue': 'SjDACS7Z/Cb1SEC3AtxEokID5SHAYl7kpys/hhmaRbpXuFKCxfj2P9BmH8QhLnuam3sENZlrnBOcB5NlcBhIfwo/Xh242RZBmPQf+edTVYVCe1j19dihcftNCHtnqAcKwp/51dNM/OlKu2730FrwvOUXVIPtB7iVqkseO9TRzDYIDj+zBTksnR/NAYtq6SUpmefXfON0uW3N3Uq6PGfExJaS+aeqRf8cPGkZFSIUQZwOLXbIpb7BFjJ1+y1OMOAJueqvikUprAit3v6BiNWurAvSQpC7WWMFUKyA79/xtkO9kIPA/Q4C9ryqdzxZJ0jDhXiaIIQj2JZfIADdjLZHJA=='}
}

ACTIVITYPUB_FOLLOW = {
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/security/v1",
  ],
  "id": "https://example.com/follow",
  "type": "Follow",
  "actor": "https://example.com/actor",
  "object": "https://example.org/actor",
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

ACTIVITYPUB_PROFILE_INVALID = {
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/security/v1",
  ],
  "id": None,
  "type": "Person",
  "name": "Jason Robinson",
  "url": "https://diaspodon.fr/@jaywink",
  "publicKey": {
    "id": "https://diaspodon.fr/users/jaywink#main-key",
    "owner": "https://diaspodon.fr/users/jaywink",
    "publicKeyPem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwVbaT5wvaZobfIB044ai\nhJg/XooEn2jSTnTY1K4mPmhdqYUmszpdXKp64OwA+f3SBuIUIkLAYUSB9Fu19zh+\nzOsoGI5gvA32DHY1vaqdKnT9gt3jKS5AdQ3bl0t9f4pPkO2I5YtQOWV1FvBcwPXG\nB0dIqj0fTqNK37FmyybrRD6uhjySddklN9gNsULTqYVDa0QSXVswTIW2jQudnNlp\nnEf3SfjlK9J8eKPF3hFK3PNXBTTZ4NydBSL3cVBinU0cFg8lUJOK8RI4qaetrVoQ\neKd7gCTSQ7RZh8kmkYmdlweb+ZtORT6Y5ZsotR8jwhAOFAqCt36B5+LX2UIw68Pk\nOwIDAQAB\n-----END PUBLIC KEY-----\n"
  },
}

ACTIVITYPUB_RETRACTION = {
    '@context': [
        'https://www.w3.org/ns/activitystreams',
        'https://w3id.org/security/v1',
        {
            'vcard': 'http://www.w3.org/2006/vcard/ns#',
            'dfrn': 'http://purl.org/macgirvin/dfrn/1.0/',
            'diaspora': 'https://diasporafoundation.org/ns/',
            'litepub': 'http://litepub.social/ns#',
            'manuallyApprovesFollowers': 'as:manuallyApprovesFollowers',
            'sensitive': 'as:sensitive',
            'Hashtag': 'as:Hashtag',
            'directMessage': 'litepub:directMessage',
        },
    ],
    'id': 'https://friendica.feneas.org/objects/76158462-165d-3386-aa23-ba2090614385#Delete',
    'type': 'Delete',
    'actor': 'https://friendica.feneas.org/profile/jaywink',
    'published': '2019-07-20T21:24:58Z',
    'instrument': {
        'type': 'Service',
        'name': "Friendica 'Dalmatian Bellflower' 2019.06-1313",
        'url': 'https://friendica.feneas.org',
    },
    'to': ['https://www.w3.org/ns/activitystreams#Public'],
    'cc': ['https://friendica.feneas.org/followers/jaywink'],
    'object': {
        'id': 'https://friendica.feneas.org/objects/76158462-165d-3386-aa23-ba2090614385',
        'type': 'Tombstone',
    },
    'signature': {
        'type': 'RsaSignature2017',
        'nonce': 'de299d5c8074548d8022d31059b4735870f29ea85d78c5214a423038273c5e5c',
        'creator': 'https://friendica.feneas.org/profile/jaywink#main-key',
        'created': '2019-07-20T21:39:13Z',
        'signatureValue': 'lotsoftext',
    },
}

ACTIVITYPUB_SHARE = {
    '@context': 'https://www.w3.org/ns/activitystreams',
    'id': 'https://mastodon.social/users/jaywink/statuses/102560701449465612/activity',
    'type': 'Announce',
    'actor': 'https://mastodon.social/users/jaywink',
    'published': '2019-08-04T20:55:09Z',
    'to': ['https://www.w3.org/ns/activitystreams#Public'],
    'cc': [
        'https://mastodon.social/users/Gargron',
        'https://mastodon.social/users/jaywink/followers',
    ],
    'object': 'https://mastodon.social/users/Gargron/statuses/102559779793316012',
    'atomUri': 'https://mastodon.social/users/jaywink/statuses/102560701449465612/activity',
    'signature': {
        'type': 'RsaSignature2017',
        'creator': 'https://mastodon.social/users/jaywink#main-key',
        'created': '2019-08-04T20:55:09Z',
        'signatureValue': 'fBW+hqP4ZslMf+1ZebqwuYAhQHvE5atsD/DLzda0eLY8xdf5XdROtoMHfVow5ZSq34w5CIPKOUUPo6aYx5bbLSd'
                          'JqwhoKOuwbtAmq3UvUp3vsiX671Cc4AL2b7sRL2sH0XfMtl5vpVaZM4LnpzGE3py91tQPCKY+azg6XUxJKOn6Kt'
                          'bo47LSpXZmzNacsfiiEmF48FlPojRZniz1wKNV+MIvvThIQlaahKAvPYHSF9INwMtlJpnVjc9T+9IkeSuHbNY4x'
                          'R9huLESZc3iZQk1OPIUsbqmMYVRm1G/WEnPpQwl4rH64YNptpxq8oxvtkECcK1ulT9+XxoCFaLg7pHr9Q==',
    },
}

ACTIVITYPUB_UNDO_FOLLOW = {
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/security/v1",
  ],
  "id": "https://example.com/undo",
  "type": "Undo",
  "actor": "https://example.com/actor",
  "object": {
    "id": "https://example.com/follow",
    "type": "Follow",
    "actor": "https://example.com/actor",
    "object": "https://example.org/actor",
  },
}

ACTIVITYPUB_POST = {
  '@context': ['https://www.w3.org/ns/activitystreams',
  {'ostatus': 'http://ostatus.org#',
   'atomUri': 'ostatus:atomUri',
   'inReplyToAtomUri': 'ostatus:inReplyToAtomUri',
   'conversation': 'ostatus:conversation',
   'sensitive': 'as:sensitive',
   'Hashtag': 'as:Hashtag',
   'toot': 'http://joinmastodon.org/ns#',
   'Emoji': 'toot:Emoji',
   'focalPoint': {'@container': '@list', '@id': 'toot:focalPoint'},
   'blurhash': 'toot:blurhash'}],
 'id': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237/activity',
 'type': 'Create',
 'actor': 'https://diaspodon.fr/users/jaywink',
 'published': '2019-06-29T21:08:45Z',
 'to': ['https://www.w3.org/ns/activitystreams#Public'],
 'cc': ['https://diaspodon.fr/users/jaywink/followers',
  'https://dev.jasonrobinson.me/p/d4574854-a5d7-42be-bfac-f70c16fcaa97/'],
 'object': {'id': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237',
  'type': 'Note',
  'summary': None,
  'inReplyTo': None,
  'published': '2019-06-29T21:08:45Z',
  'url': 'https://diaspodon.fr/@jaywink/102356911717767237',
  'attributedTo': 'https://diaspodon.fr/users/jaywink',
  'to': ['https://www.w3.org/ns/activitystreams#Public'],
  'cc': ['https://diaspodon.fr/users/jaywink/followers',
   'https://dev.jasonrobinson.me/p/d4574854-a5d7-42be-bfac-f70c16fcaa97/'],
  'sensitive': False,
  'atomUri': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237',
  'inReplyToAtomUri': None,
  'conversation': 'tag:diaspodon.fr,2019-06-28:objectId=2347687:objectType=Conversation',
  'content': '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" class="u-url mention">@<span>jaywink</span></a></span> boom</p>',
  'contentMap': {'en': '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" class="u-url mention">@<span>jaywink</span></a></span> boom</p>'},
  'attachment': [],
  'tag': [{'type': 'Mention',
    'href': 'https://dev.jasonrobinson.me/p/d4574854-a5d7-42be-bfac-f70c16fcaa97/',
    'name': '@jaywink@dev.jasonrobinson.me'}],
  'replies': {'id': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237/replies',
   'type': 'Collection',
   'first': {'type': 'CollectionPage',
    'partOf': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237/replies',
    'items': []}}},
 'signature': {'type': 'RsaSignature2017',
  'creator': 'https://diaspodon.fr/users/jaywink#main-key',
  'created': '2019-06-29T21:08:45Z',
  'signatureValue': 'SjDACS7Z/Cb1SEC3AtxEokID5SHAYl7kpys/hhmaRbpXuFKCxfj2P9BmH8QhLnuam3sENZlrnBOcB5NlcBhIfwo/Xh242RZBmPQf+edTVYVCe1j19dihcftNCHtnqAcKwp/51dNM/OlKu2730FrwvOUXVIPtB7iVqkseO9TRzDYIDj+zBTksnR/NAYtq6SUpmefXfON0uW3N3Uq6PGfExJaS+aeqRf8cPGkZFSIUQZwOLXbIpb7BFjJ1+y1OMOAJueqvikUprAit3v6BiNWurAvSQpC7WWMFUKyA79/xtkO9kIPA/Q4C9ryqdzxZJ0jDhXiaIIQj2JZfIADdjLZHJA=='}
}

ACTIVITYPUB_POST_OBJECT = {
    'id': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237',
    'type': 'Note',
    'summary': None,
    'inReplyTo': None,
    'published': '2019-06-29T21:08:45Z',
    'url': 'https://diaspodon.fr/@jaywink/102356911717767237',
    'attributedTo': 'https://diaspodon.fr/users/jaywink',
    'to': ['https://www.w3.org/ns/activitystreams#Public'],
    'cc': ['https://diaspodon.fr/users/jaywink/followers',
        'https://dev.jasonrobinson.me/p/d4574854-a5d7-42be-bfac-f70c16fcaa97/'],
    'sensitive': False,
    'atomUri': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237',
    'inReplyToAtomUri': None,
    'conversation': 'tag:diaspodon.fr,2019-06-28:objectId=2347687:objectType=Conversation',
    'content': '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" class="u-url mention">@<span>jaywink</span></a></span> boom</p>',
    'contentMap': {'en': '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" class="u-url mention">@<span>jaywink</span></a></span> boom</p>'},
    'attachment': [],
    'tag': [{'type': 'Mention',
        'href': 'https://dev.jasonrobinson.me/p/d4574854-a5d7-42be-bfac-f70c16fcaa97/',
        'name': '@jaywink@dev.jasonrobinson.me'}],
    'replies': {'id': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237/replies',
        'type': 'Collection',
        'first': {'type': 'CollectionPage',
        'partOf': 'https://diaspodon.fr/users/jaywink/statuses/102356911717767237/replies',
        'items': []}},
}
