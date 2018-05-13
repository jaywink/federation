import re
from copy import deepcopy

from federation.utils.diaspora import generate_diaspora_profile_id

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
    result['activity']['users']['monthly'] = int_or_none(doc.get('usage', {}).get('users', {}).get('activeMonth'))
    result['activity']['local_posts'] = int_or_none(doc.get('usage', {}).get('localPosts'))
    result['activity']['local_comments'] = int_or_none(doc.get('usage', {}).get('localComments'))
    result['features'] = doc.get('metadata', {})
    admin_handle = doc.get('metadata', {}).get('adminAccount', None)
    if admin_handle:
        result['organization']['account'] = generate_diaspora_profile_id("%s@%s" % (admin_handle, host))
    return result


def parse_nodeinfo2_document(doc, host):
    result = deepcopy(defaults)
    result['name'] = doc.get('server', {}).get('name', '') or ''
    result['platform'] = doc.get('server', {}).get('software', 'unknown').lower()
    result['version'] = doc.get('server', {}).get('version', '') or ''
    # Ensure baseUrl is reported as the host we called
    base_url = doc.get('server', {}).get('baseUrl', '')
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
    result['activity']['users']['monthly'] = int_or_none(doc.get('active_users_monthly'))
    result['activity']['local_posts'] = int_or_none(doc.get('local_posts'))
    result['activity']['local_comments'] = int_or_none(doc.get('local_comments'))
    return result
