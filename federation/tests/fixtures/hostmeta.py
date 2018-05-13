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

NODEINFO2_10_DOC = """
{
  "version": "1.0",
  "server": {
    "baseUrl": "https://example.com",
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
