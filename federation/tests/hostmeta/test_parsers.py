import json
from unittest.mock import patch

from federation.hostmeta.parsers import parse_nodeinfo_document, parse_nodeinfo2_document, parse_statisticsjson_document
from federation.tests.fixtures.hostmeta import NODEINFO2_10_DOC, NODEINFO_10_DOC, NODEINFO_20_DOC, STATISTICS_JSON_DOC


@patch('federation.hostmeta.parsers.fetch_host_ip_and_country', return_value=("", ""))
class TestParseNodeInfoDocument:
    def test_parse_nodeinfo_10_document(self, mock_ip):
        result = parse_nodeinfo_document(json.loads(NODEINFO_10_DOC), 'iliketoast.net')
        assert result == {
            'organization': {
                'account': 'diaspora://podmin@iliketoast.net/profile/',
                'contact': '',
                'name': '',
            },
            'host': 'iliketoast.net',
            'ip': '',
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
            'country': '',
            'activity': {
                'users': {
                    'total': 348,
                    'half_year': 123,
                    'monthly': 62,
                    'weekly': None,
                },
                'local_posts': 8522,
                'local_comments': 17671,
            },
        }

    def test_parse_nodeinfo_20_document(self, mock_ip):
        result = parse_nodeinfo_document(json.loads(NODEINFO_20_DOC), 'iliketoast.net')
        assert result == {
            'organization': {
                'account': 'diaspora://podmin@iliketoast.net/profile/',
                'contact': '',
                'name': '',
            },
            'host': 'iliketoast.net',
            'ip': '',
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
            'country': '',
            'activity': {
                'users': {
                    'total': 348,
                    'half_year': 123,
                    'monthly': 62,
                    'weekly': None,
                },
                'local_posts': 8522,
                'local_comments': 17671,
            },
        }


@patch('federation.hostmeta.parsers.fetch_host_ip_and_country', return_value=("", ""))
class TestParseNodeInfo2Document:
    def test_parse_nodeinfo2_10_document(self, mock_ip):
        result = parse_nodeinfo2_document(json.loads(NODEINFO2_10_DOC), 'example.com')
        assert result == {
            'organization': {
                'account': 'https://example.com/u/admin',
                'contact': 'foobar@example.com',
                'name': 'Example organization',
            },
            'host': 'example.com',
            'ip': '',
            'name': 'Example server',
            'open_signups': True,
            'protocols': ["diaspora", "zot"],
            'relay': "tags",
            'server_meta': {},
            'services': ["facebook", "gnusocial", "twitter"],
            'platform': 'example',
            'version': '0.5.0',
            'features': {},
            'country': '',
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


@patch('federation.hostmeta.parsers.fetch_host_ip_and_country', return_value=("", ""))
class TestParseStatisticsJSONDocument:
    def test_parse_statisticsjson_document(self, mock_ip):
        result = parse_statisticsjson_document(json.loads(STATISTICS_JSON_DOC), 'example.com')
        assert result == {
            'organization': {
                'account': '',
                'contact': '',
                'name': '',
            },
            'host': 'example.com',
            'ip': '',
            'name': 'diaspora*',
            'open_signups': True,
            'protocols': ["diaspora"],
            'relay': '',
            'server_meta': {},
            'services': [],
            'platform': 'diaspora',
            'version': '0.5.7.0-p56ebcc76',
            'features': {},
            'country': '',
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
