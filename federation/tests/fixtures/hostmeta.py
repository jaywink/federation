MASTODON_DOC = """
{"uri": "mastodon.local", "title": "Mastodon",
 "description": "This page describes the mastodon.local",
 "email": "hello@mastodon.local", "version": "2.4.0", "urls": {"streaming_api": "wss://mastodon.local"},
 "stats": {"user_count": 159726, "status_count": 6059606, "domain_count": 4703},
 "thumbnail": "https://files.mastodon.local/site_uploads/files/000/000/001/original/file.jpeg",
 "languages": ["en"],
 "contact_account": {"id": "1", "username": "Admin", "acct": "Admin", "display_name": "Admin dude", "locked": false,
                     "bot": false, "created_at": "2016-03-16T14:34:26.392Z",
                     "note": "\u003cp\u003eSuperuser\u003c/p\u003e",
                     "url": "https://mastodon.local/@Admin",
                     "avatar": "https://files.mastodon.local/accounts/avatars/000/000/001/original/file.png",
                     "avatar_static": "https://files.mastodon.local/accounts/avatars/000/000/001/original/file.png",
                     "header": "https://files.mastodon.local/accounts/headers/000/000/001/original/file.jpeg",
                     "header_static": "https://files.mastodon.local/accounts/headers/000/000/001/original/file.jpeg",
                     "followers_count": 81779, "following_count": 506, "statuses_count": 36722, "emojis": [],
                     "fields": []}}
"""

MASTODON_RC_DOC = """
{"uri": "mastodon.local", "title": "Mastodon",
 "description": "This page describes the mastodon.local",
 "email": "hello@mastodon.local", "version": "2.4.1rc1", "urls": {"streaming_api": "wss://mastodon.local"},
 "stats": {"user_count": 159726, "status_count": 6059606, "domain_count": 4703},
 "thumbnail": "https://files.mastodon.local/site_uploads/files/000/000/001/original/file.jpeg",
 "languages": ["en"],
 "contact_account": {"id": "1", "username": "Admin", "acct": "Admin", "display_name": "Admin dude", "locked": false,
                     "bot": false, "created_at": "2016-03-16T14:34:26.392Z",
                     "note": "\u003cp\u003eSuperuser\u003c/p\u003e",
                     "url": "https://mastodon.local/@Admin",
                     "avatar": "https://files.mastodon.local/accounts/avatars/000/000/001/original/file.png",
                     "avatar_static": "https://files.mastodon.local/accounts/avatars/000/000/001/original/file.png",
                     "header": "https://files.mastodon.local/accounts/headers/000/000/001/original/file.jpeg",
                     "header_static": "https://files.mastodon.local/accounts/headers/000/000/001/original/file.jpeg",
                     "followers_count": 81779, "following_count": 506, "statuses_count": 36722, "emojis": [],
                     "fields": []}}
"""

MASTODON_ACTIVITY_DOC = """
    [
        {"week":"1526256000","statuses":"200229","logins":"10034","registrations":"1379"},
        {"week":"1526860800","statuses":"121188","logins":"8779","registrations":"1143"}
    ]
"""

NODEINFO_10_DOC = '{"version":"1.0","software":{"name":"diaspora","version":"0.7.4.0-pd0313756"},"protocols":' \
                  '{"inbound":["diaspora"],"outbound":["diaspora"]},"services":{"inbound":[],"outbound":["twi' \
                  'tter","tumblr"]},"openRegistrations":true,"usage":{"users":{"total":348,"activeHalfyear":1' \
                  '23,"activeMonth":62},"localPosts":8522,"localComments":17671},"metadata":{"nodeName":"I Li' \
                  'ke Toast","xmppChat":false,"camo":{"markdown":false,"opengraph":false,"remotePods":false},' \
                  '"adminAccount":"podmin"}}'

NODEINFO_20_DOC = '{"version":"2.0","software":{"name":"diaspora","version":"0.7.4.0-pd0313756"},"protocols":' \
                  '["diaspora"],"services":{"inbound":[],"outbound":["twitter","tumblr"]},"openRegistrations"' \
                  ':true,"usage":{"users":{"total":348,"activeHalfyear":123,"activeMonth":62},"localPosts":85' \
                  '22,"localComments":17671},"metadata":{"nodeName":"I Like Toast","xmppChat":false,"camo":{"' \
                  'markdown":false,"opengraph":false,"remotePods":false},"adminAccount":"podmin"}}'

# Buggy NodeInfo well known found in certain older Hubzilla versions
NODEINFO_WELL_KNOWN_BUGGY = '{"links":{"rel":"http:\/\/nodeinfo.diaspora.software\/ns\/schema\/1.0","href":"h' \
                            'ttps:\/\/example.com\/nodeinfo\/1.0"},"0":{"rel":"http:\/\/nodeinfo.diaspo' \
                            'ra.software\/ns\/schema\/2.0","href":"https:\/\/example.com\/nodeinfo\/2.0"}}'

# Another buggy old NodeInfo
NODEINFO_WELL_KNOWN_BUGGY_2 = '{"links":{"rel":"http:\/\/nodeinfo.diaspora.software\/ns\/schema\/1.0","href":' \
                              '"https:\/\/example.com\/nodeinfo\/1.0"}}'

NODEINFO2_10_DOC = """
{
  "version": "1.0",
  "server": {
    "baseUrl": "https://example.com/",
    "name": "Example server",
    "software": "example",
    "version": "0.5.0"
  },
  "organization": {
    "name": "Example organization",
    "contact": "foobar@example.com",
    "account": "https://example.com/u/admin"
  },
  "protocols": ["diaspora", "zot"],
  "relay": "tags",
  "services": {
    "inbound": ["gnusocial"],
    "outbound": ["facebook", "twitter"]
  },
  "openRegistrations": true,
  "usage": {
    "users": {
      "total": 123,
      "activeHalfyear": 42,
      "activeMonth": 23,
      "activeWeek": 10
    },
    "localPosts": 500,
    "localComments": 1000
  }
}
"""

STATISTICS_JSON_DOC = '{"name":"diaspora*","network":"Diaspora","version":"0.5.7.0-p56ebcc76","registrations_open"' \
                      ':true,"services":[],"twitter":false,"tumblr":false,"facebook":false,"wordpress":false}'
