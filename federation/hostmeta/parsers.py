import json
import re
from copy import deepcopy
from typing import Dict

from federation.utils.network import fetch_document

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
    # TODO figure out what to do with posts vs comments vs statuses
    #result['activity']['users']['local_posts'] = int_or_none(doc.get('stats', {}).get('status_count'))

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
    result['host'] = host
    result['name'] = host
    result['protocols'] = ['matrix']
    result['platform'] = f'matrix|{doc["server"]["name"].lower()}'
    result['version'] = doc["server"]["version"]

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
    result['name'] = doc.get('server', {}).get('name', '') or ''
    result['platform'] = doc.get('server', {}).get('software', 'unknown').lower()
    result['version'] = doc.get('server', {}).get('version', '') or ''
    # Ensure baseUrl is reported as the host we called
    base_url = doc.get('server', {}).get('baseUrl', '').rstrip('/')
    cleaned_base_url = re.sub(r'https?://', '', base_url)
    if cleaned_base_url.startswith(host):
        result['host'] = cleaned_base_url
    else:
        raise ValueError('NodeInfo2 baseUrl is outside called host.')
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
