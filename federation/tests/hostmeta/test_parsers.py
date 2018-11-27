import json
from unittest.mock import patch

from federation.hostmeta.parsers import (
    parse_nodeinfo_document, parse_nodeinfo2_document, parse_statisticsjson_document, int_or_none,
    parse_mastodon_document, parse_matrix_document)
from federation.tests.fixtures.hostmeta import (
    NODEINFO2_10_DOC, NODEINFO_10_DOC, NODEINFO_20_DOC, STATISTICS_JSON_DOC, MASTODON_DOC, MASTODON_ACTIVITY_DOC,
    MASTODON_RC_DOC, MASTODON_DOC_NULL_CONTACT, MATRIX_SYNAPSE_DOC, PLEROMA_MASTODON_API_DOC)


class TestIntOrNone:
    def test_returns_negative_values_as_none(self):
        assert int_or_none(-1) is None


class TestParseMastodonDocument:
    @patch('federation.hostmeta.fetchers.fetch_nodeinfo_document', autospec=True)
    def test_calls_nodeinfo_fetcher_if_pleroma(self, mock_fetch):
        parse_mastodon_document(json.loads(PLEROMA_MASTODON_API_DOC), 'example.com')
        mock_fetch.assert_called_once_with('example.com')

    @patch('federation.hostmeta.parsers.fetch_document')
    def test_parse_mastodon_document(self, mock_fetch):
        mock_fetch.return_value = MASTODON_ACTIVITY_DOC, 200, None
        result = parse_mastodon_document(json.loads(MASTODON_DOC), 'example.com')
        assert result == {
            'organization': {
                'account': 'https://mastodon.local/@Admin',
                'contact': 'hello@mastodon.local',
                'name': 'Admin dude',
            },
            'host': 'example.com',
            'name': 'Mastodon',
            'open_signups': True,
            'protocols': ["ostatus", "activitypub"],
            'relay': False,
            'server_meta': {},
            'services': [],
            'platform': 'mastodon',
            'version': '2.4.0',
            'features': {},
            'activity': {
                'users': {
                    'total': 159726,
                    'half_year': 90774,
                    'monthly': 27829,
                    'weekly': 8779,
                },
                'local_posts': 6059606,
                'local_comments': None,
            },
        }

    @patch('federation.hostmeta.parsers.fetch_document')
    def test_parse_mastodon_document__null_contact_account(self, mock_fetch):
        mock_fetch.return_value = MASTODON_ACTIVITY_DOC, 200, None
        result = parse_mastodon_document(json.loads(MASTODON_DOC_NULL_CONTACT), 'example.com')
        assert result == {
            'organization': {
                'account': '',
                'contact': '',
                'name': '',
            },
            'host': 'example.com',
            'name': 'Mastodon',
            'open_signups': True,
            'protocols': ["ostatus", "activitypub"],
            'relay': False,
            'server_meta': {},
            'services': [],
            'platform': 'mastodon',
            'version': '2.4.0',
            'features': {},
            'activity': {
                'users': {
                    'total': 159726,
                    'half_year': 90774,
                    'monthly': 27829,
                    'weekly': 8779,
                },
                'local_posts': 6059606,
                'local_comments': None,
            },
        }

    @patch('federation.hostmeta.parsers.fetch_document')
    def test_parse_mastodon_document__rc_version(self, mock_fetch):
        mock_fetch.return_value = MASTODON_ACTIVITY_DOC, 200, None
        result = parse_mastodon_document(json.loads(MASTODON_RC_DOC), 'example.com')
        assert result == {
            'organization': {
                'account': 'https://mastodon.local/@Admin',
                'contact': 'hello@mastodon.local',
                'name': 'Admin dude',
            },
            'host': 'example.com',
            'name': 'Mastodon',
            'open_signups': True,
            'protocols': ["ostatus", "activitypub"],
            'relay': False,
            'server_meta': {},
            'services': [],
            'platform': 'mastodon',
            'version': '2.4.1rc1',
            'features': {},
            'activity': {
                'users': {
                    'total': 159726,
                    'half_year': 90774,
                    'monthly': 27829,
                    'weekly': 8779,
                },
                'local_posts': 6059606,
                'local_comments': None,
            },
        }


class TestParseMatrixDocument:
    @patch('federation.hostmeta.parsers.send_document', autospec=True, return_value=(403, None))
    def test_parse_matrix_document__signups_closed(self, mock_send):
        result = parse_matrix_document(json.loads(MATRIX_SYNAPSE_DOC), 'feneas.org')
        assert result == {
            'organization': {
                'account': '',
                'contact': '',
                'name': '',
            },
            'host': 'feneas.org',
            'name': 'feneas.org',
            'open_signups': False,
            'protocols': ['matrix'],
            'relay': '',
            'server_meta': {},
            'services': [],
            'platform': 'matrix|synapse',
            'version': '0.33.8',
            'features': {},
            'activity': {
                'users': {
                    'total': None,
                    'half_year': None,
                    'monthly': None,
                    'weekly': None,
                },
                'local_posts': None,
                'local_comments': None,
            },
        }

    @patch('federation.hostmeta.parsers.send_document', autospec=True, return_value=(401, None))
    def test_parse_matrix_document__signups_open(self, mock_send):
        result = parse_matrix_document(json.loads(MATRIX_SYNAPSE_DOC), 'feneas.org')
        assert result == {
            'organization': {
                'account': '',
                'contact': '',
                'name': '',
            },
            'host': 'feneas.org',
            'name': 'feneas.org',
            'open_signups': True,
            'protocols': ['matrix'],
            'relay': '',
            'server_meta': {},
            'services': [],
            'platform': 'matrix|synapse',
            'version': '0.33.8',
            'features': {},
            'activity': {
                'users': {
                    'total': None,
                    'half_year': None,
                    'monthly': None,
                    'weekly': None,
                },
                'local_posts': None,
                'local_comments': None,
            },
        }


class TestParseNodeInfoDocument:
    def test_parse_nodeinfo_10_document(self):
        result = parse_nodeinfo_document(json.loads(NODEINFO_10_DOC), 'iliketoast.net')
        assert result == {
            'organization': {
                'account': 'podmin@iliketoast.net',
                'contact': '',
                'name': '',
            },
            'host': 'iliketoast.net',
            'name': 'I Like Toast',
            'open_signups': True,
            'protocols': ["diaspora"],
            'relay': '',
            'server_meta': {},
            'services': ["tumblr", "twitter"],
            'platform': 'diaspora',
            'version': '0.7.4.0-pd0313756',
            'features': {
                "nodeName": "I Like Toast",
                "xmppChat": False,
                "camo": {
                    "markdown": False,
                    "opengraph": False,
                    "remotePods": False
                },
                "adminAccount": "podmin",
            },
            'activity': {
                'users': {
                    'total': 348,
                    'half_year': 123,
                    'monthly': 62,
                    'weekly': 19,
                },
                'local_posts': 8522,
                'local_comments': 17671,
            },
        }

    def test_parse_nodeinfo_20_document(self):
        result = parse_nodeinfo_document(json.loads(NODEINFO_20_DOC), 'iliketoast.net')
        assert result == {
            'organization': {
                'account': 'podmin@iliketoast.net',
                'contact': '',
                'name': '',
            },
            'host': 'iliketoast.net',
            'name': 'I Like Toast',
            'open_signups': True,
            'protocols': ["diaspora"],
            'relay': '',
            'server_meta': {},
            'services': ["tumblr", "twitter"],
            'platform': 'diaspora',
            'version': '0.7.4.0-pd0313756',
            'features': {
                "nodeName": "I Like Toast",
                "xmppChat": False,
                "camo": {
                    "markdown": False,
                    "opengraph": False,
                    "remotePods": False
                },
                "adminAccount": "podmin",
            },
            'activity': {
                'users': {
                    'total': 348,
                    'half_year': 123,
                    'monthly': 62,
                    'weekly': 19,
                },
                'local_posts': 8522,
                'local_comments': 17671,
            },
        }


class TestParseNodeInfo2Document:
    def test_parse_nodeinfo2_10_document(self):
        result = parse_nodeinfo2_document(json.loads(NODEINFO2_10_DOC), 'example.com')
        assert result == {
            'organization': {
                'account': 'https://example.com/u/admin',
                'contact': 'foobar@example.com',
                'name': 'Example organization',
            },
            'host': 'example.com',
            'name': 'Example server',
            'open_signups': True,
            'protocols': ["diaspora", "zot"],
            'relay': "tags",
            'server_meta': {},
            'services': ["facebook", "gnusocial", "twitter"],
            'platform': 'example',
            'version': '0.5.0',
            'features': {},
            'activity': {
                'users': {
                    'total': 123,
                    'half_year': 42,
                    'monthly': 23,
                    'weekly': 10,
                },
                'local_posts': 500,
                'local_comments': 1000,
            },
        }


class TestParseStatisticsJSONDocument:
    def test_parse_statisticsjson_document(self):
        result = parse_statisticsjson_document(json.loads(STATISTICS_JSON_DOC), 'example.com')
        assert result == {
            'organization': {
                'account': '',
                'contact': '',
                'name': '',
            },
            'host': 'example.com',
            'name': 'diaspora*',
            'open_signups': True,
            'protocols': ["diaspora"],
            'relay': '',
            'server_meta': {},
            'services': [],
            'platform': 'diaspora',
            'version': '0.5.7.0-p56ebcc76',
            'features': {},
            'activity': {
                'users': {
                    'total': None,
                    'half_year': None,
                    'monthly': None,
                    'weekly': None,
                },
                'local_posts': None,
                'local_comments': None,
            },
        }
