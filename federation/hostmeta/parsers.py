import re
from copy import deepcopy

from federation.utils.diaspora import generate_diaspora_profile_id
from federation.utils.network import fetch_host_ip_and_country

defaults = {
    'organization': {
        'account': '',
        'contact': '',
        'name': '',
    },
    'host': '',
    'ip': '',
    'name': '',
    'open_signups': False,
    'protocols': [],
    'relay': False,
    'server_meta': {},
    'services': [],
    'platform': '',
    'version': '',
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
    result['activity']['users']['total'] = doc.get('usage', {}).get('users', {}).get('total', None)
    result['activity']['users']['half_year'] = doc.get('usage', {}).get('users', {}).get('activeHalfyear', None)
    result['activity']['users']['monthly'] = doc.get('usage', {}).get('users', {}).get('activeMonth', None)
    result['activity']['local_posts'] = doc.get('usage', {}).get('localPosts', None)
    result['activity']['local_comments'] = doc.get('usage', {}).get('localComments', None)
    result['features'] = doc.get('metadata', {})
    admin_handle = doc.get('metadata', {}).get('adminAccount', None)
    if admin_handle:
        result['organization']['account'] = generate_diaspora_profile_id("%s@%s" % (admin_handle, host))
    result['ip'], result['country'] = fetch_host_ip_and_country(host)
    return result


def parse_nodeinfo2_document(doc, host):
    result = deepcopy(defaults)
    result['name'] = doc.get('server', {}).get('name', '')
    result['platform'] = doc.get('server', {}).get('software', 'unknown').lower()
    result['version'] = doc.get('server', {}).get('version', '')
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
    result['relay'] = doc.get('relay', False)
    result['organization']['contact'] = doc.get('organization', {}).get('contact', '')
    result['organization']['name'] = doc.get('organization', {}).get('name', '')
    result['organization']['account'] = doc.get('organization', {}).get('account', '')
    result['features'] = doc.get('otherFeatures', {})
    result['activity']['users']['total'] = doc.get('usage', {}).get('users', {}).get('total', None)
    result['activity']['users']['half_year'] = doc.get('usage', {}).get('users', {}).get('activeHalfyear', None)
    result['activity']['users']['monthly'] = doc.get('usage', {}).get('users', {}).get('activeMonth', None)
    result['activity']['users']['weekly'] = doc.get('usage', {}).get('users', {}).get('activeWeek', None)
    result['activity']['local_posts'] = doc.get('usage', {}).get('localPosts', None)
    result['activity']['local_comments'] = doc.get('usage', {}).get('localComments', None)
    result['ip'], result['country'] = fetch_host_ip_and_country(host)
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
    result['activity']['users']['total'] = doc.get('total_users', None)
    result['activity']['users']['half_year'] = doc.get('active_users_halfyear', None)
    result['activity']['users']['monthly'] = doc.get('active_users_monthly', None)
    result['activity']['local_posts'] = doc.get('local_posts', None)
    result['activity']['local_comments'] = doc.get('local_comments', None)
    result['ip'], result['country'] = fetch_host_ip_and_country(host)
    return result
