import json
import re
from copy import deepcopy
from typing import Dict

from federation.utils.network import fetch_document, send_document

WEEKLY_USERS_HALFYEAR_MULTIPLIER = 10.34
WEEKLY_USERS_MONTHLY_MULTIPLIER = 3.17
MONTHLY_USERS_WEEKLY_MULTIPLIER = 0.316
HALFYEAR_USERS_WEEKLY_MULTIPLIER = 0.097

defaults = {
    'organization': {
        'account': '',
        'contact': '',
        'name': '',
    },
    'host': '',
    'name': '',
    'open_signups': False,
    'protocols': [],
    'relay': '',
    'server_meta': {},
    'services': [],
    'platform': '',
    'version': '',
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


def int_or_none(value):
    if isinstance(value, dict):
        return None
    if value is None or value == '':
        return None
    try:
        result = int(value)
        if result < 0:
            return None
        return result
    except ValueError:
        return None


def parse_mastodon_document(doc, host):
    # Check first this is not actually Pleroma or Misskey
    if doc.get('version', '').find('Pleroma') > -1 or doc.get('version', '').find('Pixelfed') > -1 or \
            doc.get('version', '').find('Kibou') > -1 or doc.get('version', '').find('Kroeg') > -1:
        # Use NodeInfo instead, otherwise this is logged as Mastodon
        from federation.hostmeta.fetchers import fetch_nodeinfo_document
        return fetch_nodeinfo_document(host)
    elif doc.get('version', '').find('misskey') > -1:
        # Use Misskey instead, otherwise this is logged as Mastodon
        from federation.hostmeta.fetchers import fetch_misskey_document
        return fetch_misskey_document(host, mastodon_document=doc)

    result = deepcopy(defaults)
    result['host'] = host
    result['name'] = doc.get('title', host)
    result['platform'] = 'mastodon'
    result['version'] = doc.get('version', '')

    # Awkward parsing of signups from about page
    # TODO remove if fixed, issue logged: https://github.com/tootsuite/mastodon/issues/9350
    about_doc, _status_code, _error = fetch_document(host=host, path='/about')
    if about_doc:
        result['open_signups'] = about_doc.find("<div class='closed-registrations-message'>") == -1

    version = re.sub(r'[^0-9.]', '', doc.get('version', ''))
    version = [int(part) for part in version.split('.')]
    if version >= [1, 6, 0]:
        result['protocols'] = ['ostatus', 'activitypub']
    else:
        result['protocols'] = ['ostatus']
    result['relay'] = False

    result['activity']['users']['total'] = int_or_none(doc.get('stats', {}).get('user_count'))
    result['activity']['local_posts'] = int_or_none(doc.get('stats', {}).get('status_count'))

    if "contact_account" in doc and doc.get('contact_account') is not None:
        contact_account = doc.get('contact_account', {})
    else:
        contact_account = {}
    result['organization']['account'] = contact_account.get('url', '')
    result['organization']['contact'] = doc.get('email', '')
    result['organization']['name'] = contact_account.get('display_name', '')

    activity_doc, _status_code, _error = fetch_document(host=host, path='/api/v1/instance/activity')
    if activity_doc:
        try:
            activity_doc = json.loads(activity_doc)
        except json.JSONDecodeError:
            return result
        else:
            try:
                logins = activity_doc[1].get('logins')
            except KeyError:
                logins = activity_doc[0].get('logins')
            weekly_count = int_or_none(logins)
            if weekly_count and result['activity']['users']['total']:
                result['activity']['users']['weekly'] = weekly_count
                # Ensure multiplied counts from weekly count don't go over total user count
                result['activity']['users']['half_year'] = min(
                    int(weekly_count * WEEKLY_USERS_HALFYEAR_MULTIPLIER),
                    result['activity']['users']['total'],
                )
                result['activity']['users']['monthly'] = min(
                    int(weekly_count * WEEKLY_USERS_MONTHLY_MULTIPLIER),
                    result['activity']['users']['total'],
                )

    return result


def parse_matrix_document(doc: Dict, host: str) -> Dict:
    result = deepcopy(defaults)
    host_without_port = host.split(':')[0]
    result['host'] = host_without_port
    result['name'] = host_without_port
    result['protocols'] = ['matrix']
    result['platform'] = f'matrix|{doc["server"]["name"].lower()}'
    result['version'] = doc["server"]["version"]

    # Get signups status by posting to register endpoint and analyzing the status code coming back
    status_code, _error = send_document(
        f'https://{host}/_matrix/client/r0/register',
        data=json.dumps({'auth': {}}),
    )
    if status_code == 401:
        result['open_signups'] = True
    elif status_code == 403:
        result['open_signups'] = False

    return result


def parse_misskey_document(doc: Dict, host: str, mastodon_document: Dict=None) -> Dict:
    result = deepcopy(defaults)
    result['host'] = host

    result['organization']['name'] = doc.get('maintainer', {}).get('name', '')
    result['organization']['contact'] = doc.get('maintainer', {}).get('email', '')

    result['name'] = doc.get('name', host)
    result['open_signups'] = doc.get('features', {}).get('registration', False)
    result['protocols'] = ['activitypub']

    if doc.get('features', {}).get('twitter', False):
        result['services'].append('twitter')
    if doc.get('features', {}).get('github', False):
        result['services'].append('github')
    if doc.get('features', {}).get('discord', False):
        result['services'].append('discord')

    result['platform'] = 'misskey'
    result['version'] = doc.get('version', '')
    result['features'] = doc.get('features', {})

    if not mastodon_document:
        # Fetch also Mastodon API doc to get some counts...
        api_doc, _status_code, _error = fetch_document(host=host, path='/api/v1/instance')
        if api_doc:
            try:
                mastodon_document = json.loads(api_doc)
            except json.JSONDecodeError:
                pass
    if mastodon_document:
        result['activity']['users']['total'] = int_or_none(mastodon_document.get('stats', {}).get('user_count'))
        result['activity']['local_posts'] = int_or_none(mastodon_document.get('stats', {}).get('status_count'))

        if "contact_account" in mastodon_document and mastodon_document.get('contact_account') is not None:
            contact_account = mastodon_document.get('contact_account', {})
        else:
            contact_account = {}
        result['organization']['account'] = contact_account.get('url', '')

    return result


def parse_nodeinfo_document(doc, host):
    result = deepcopy(defaults)
    nodeinfo_version = doc.get('version', '1.0')
    result['host'] = host
    result['name'] = doc.get('metadata', {}).get('nodeName', host)
    result['version'] = doc.get('software', {}).get('version', '')
    result['platform'] = doc.get('software', {}).get('name', 'unknown').lower()
    if nodeinfo_version in ('1.0', '1.1'):
        inbound = doc.get('protocols', {}).get('inbound', [])
        outbound = doc.get('protocols', {}).get('outbound', [])
        protocols = sorted(list(set(inbound + outbound)))
        result['protocols'] = protocols
    else:
        result['protocols'] = doc.get('protocols', [])
    inbound = doc.get('services', {}).get('inbound', [])
    outbound = doc.get('services', {}).get('outbound', [])
    services = sorted(list(set(inbound + outbound)))
    result['services'] = services
    result['open_signups'] = doc.get('openRegistrations', False)
    result['activity']['users']['total'] = int_or_none(doc.get('usage', {}).get('users', {}).get('total'))
    result['activity']['users']['half_year'] = int_or_none(doc.get('usage', {}).get('users', {}).get('activeHalfyear'))
    monthly = int_or_none(doc.get('usage', {}).get('users', {}).get('activeMonth'))
    result['activity']['users']['monthly'] = monthly
    if monthly:
        result['activity']['users']['weekly'] = int(monthly * MONTHLY_USERS_WEEKLY_MULTIPLIER)
    result['activity']['local_posts'] = int_or_none(doc.get('usage', {}).get('localPosts'))
    result['activity']['local_comments'] = int_or_none(doc.get('usage', {}).get('localComments'))
    result['features'] = doc.get('metadata', {})
    admin_handle = doc.get('metadata', {}).get('adminAccount', None)
    if admin_handle:
        result['organization']['account'] = f"{admin_handle}@{host}"
    return result


def parse_nodeinfo2_document(doc, host):
    result = deepcopy(defaults)
    result['platform'] = doc.get('server', {}).get('software', 'unknown').lower()
    result['version'] = doc.get('server', {}).get('version', '') or ''
    # Ensure baseUrl is reported as the host we called
    base_url = doc.get('server', {}).get('baseUrl', '').rstrip('/')
    cleaned_base_url = re.sub(r'https?://', '', base_url).split(':')[0]
    if cleaned_base_url.startswith(host):
        result['host'] = cleaned_base_url
    else:
        raise ValueError('NodeInfo2 baseUrl is outside called host.')
    result['name'] = doc.get('server', {}).get('name', '') or ''
    if not result['name']:
        result['name'] = result['host']
    result['open_signups'] = doc.get('openRegistrations', False)
    inbound = doc.get('services', {}).get('inbound', [])
    outbound = doc.get('services', {}).get('outbound', [])
    services = sorted(list(set(inbound + outbound)))
    result['services'] = services
    result['protocols'] = sorted(doc.get('protocols', []))
    result['relay'] = doc.get('relay', '') or ''
    result['organization']['contact'] = doc.get('organization', {}).get('contact', '') or ''
    result['organization']['name'] = doc.get('organization', {}).get('name', '') or ''
    result['organization']['account'] = doc.get('organization', {}).get('account', '') or ''
    result['features'] = doc.get('otherFeatures', {})
    result['activity']['users']['total'] = int_or_none(doc.get('usage', {}).get('users', {}).get('total'))
    result['activity']['users']['half_year'] = int_or_none(doc.get('usage', {}).get('users', {}).get('activeHalfyear'))
    result['activity']['users']['monthly'] = int_or_none(doc.get('usage', {}).get('users', {}).get('activeMonth'))
    result['activity']['users']['weekly'] = int_or_none(doc.get('usage', {}).get('users', {}).get('activeWeek'))
    result['activity']['local_posts'] = int_or_none(doc.get('usage', {}).get('localPosts'))
    result['activity']['local_comments'] = int_or_none(doc.get('usage', {}).get('localComments'))
    return result


def parse_statisticsjson_document(doc, host):
    result = deepcopy(defaults)
    result['host'] = host
    result['name'] = doc.get('name', '')
    result['platform'] = doc.get('network', 'unknown').lower()
    result['version'] = doc.get('version', '')
    result['open_signups'] = doc.get('registrations_open', False)
    result['services'] = sorted(doc.get('services', []))
    result['protocols'] = ['diaspora']  # Reasonable default
    result['activity']['users']['total'] = int_or_none(doc.get('total_users'))
    result['activity']['users']['half_year'] = int_or_none(doc.get('active_users_halfyear'))
    monthly = int_or_none(doc.get('active_users_monthly'))
    result['activity']['users']['monthly'] = monthly
    if monthly:
        result['activity']['users']['weekly'] = int(monthly * MONTHLY_USERS_WEEKLY_MULTIPLIER)
    result['activity']['local_posts'] = int_or_none(doc.get('local_posts'))
    result['activity']['local_comments'] = int_or_none(doc.get('local_comments'))
    return result
