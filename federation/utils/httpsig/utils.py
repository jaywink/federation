import base64
import six
import re
import struct
import hashlib

try:
    # Python 3
    from urllib.request import parse_http_list
except ImportError:
    # Python 2
    from urllib2 import parse_http_list

from Crypto.Hash import SHA, SHA256, SHA512

ALGORITHMS = frozenset([
                'rsa-sha1',
                'rsa-sha256',
                'rsa-sha512',
                'hmac-sha1',
                'hmac-sha256',
                'hmac-sha512',
                'hs2019'])
HASHES = {'sha1':   SHA,
          'sha256': SHA256,
          'sha512': SHA512}


class HttpSigException(Exception):
    pass


def ct_bytes_compare(a, b):
    """
    Constant-time string compare.
    http://codahale.com/a-lesson-in-timing-attacks/
    """
    if not isinstance(a, six.binary_type):
        a = a.decode('utf8')
    if not isinstance(b, six.binary_type):
        b = b.decode('utf8')

    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a, b):
        if six.PY2:
            result |= ord(x) ^ ord(y)
        else:
            result |= x ^ y

    return (result == 0)


def generate_message(required_headers, headers, host=None, method=None,
                     path=None, created=None, expires=None):
    headers = CaseInsensitiveDict(headers)

    if not required_headers:
        required_headers = ['date']

    signable_list = []
    for h in required_headers:
        h = h.lower()
        if h == '(request-target)':
            if not method or not path:
                raise ValueError('method and path arguments required when ' +
                                'using "(request-target)"')
            signable_list.append('%s: %s %s' % (h, method.lower(), path))

        elif h == '(created)':
            if not created:
                raise ValueError('created argument required when ' +
                                'using "(created)"')
            signable_list.append('%s: %d' % (h, created))
        elif h == '(expires)':
            if not expires:
                raise ValueError('expires argument required when ' +
                                'using "(expires)"')
            signable_list.append('%s: %d' % (h, expires))
        elif h == 'host':
            # 'host' special case due to requests lib restrictions
            # 'host' is not available when adding auth so must use a param
            # if no param used, defaults back to the 'host' header
            if not host:
                if 'host' in headers:
                    host = headers[h]
                else:
                    raise ValueError('missing required header "%s"' % h)
            signable_list.append('%s: %s' % (h, host))
        else:
            if h not in headers:
                raise ValueError('missing required header "%s"' % h)

            signable_list.append('%s: %s' % (h, headers[h]))

    signable = '\n'.join(signable_list).encode("ascii")
    return signable


def parse_signature_header(sign_value):
    values = {}
    if sign_value:
        # This is tricky string magic.  Let urllib do it.
        fields = parse_http_list(sign_value)

        for item in fields:
            # Only include keypairs.
            if '=' in item:
                # Split on the first '=' only.
                key, value = item.split('=', 1)
                if not (len(key) and len(value)):
                    continue

                # Unquote values, if quoted.
                if value[0] == '"':
                    value = value[1:-1]

                values[key] = value
    return CaseInsensitiveDict(values)


def parse_authorization_header(header):
    if not isinstance(header, six.string_types):
        header = header.decode("ascii")  # HTTP headers cannot be Unicode.

    auth = header.split(" ", 1)
    if len(auth) > 2:
        raise ValueError('Invalid authorization header. (eg. Method ' +
                         'key1=value1,key2="value, \"2\"")')

    # Split up any args into a dictionary.
    values = {}
    if len(auth) == 2:
        values = parse_signature_header(auth[1])

    # ("Signature", {"headers": "date", "algorithm": "hmac-sha256", ... })
    return (auth[0], values)


def build_signature_template(key_id, algorithm, headers, created, expires, sign_header='Signature'):
    """
    Build the Signature template for use with the Authorization header.

    key_id is the mandatory label indicating to the server which secret to use
    algorithm is one of the six specified algorithms
    headers is a list of http headers to be included in the signing string.

    The signature must be interpolated into the template to get the final
    Authorization header value.
    """
    param_map = {'keyId': key_id,
                 'algorithm': algorithm,
                 'signature': '%s'}

    if created:
        param_map['created'] = created
    if expires:
        param_map['expires'] = expires

    if headers:
        headers = [h.lower() for h in headers]
        param_map['headers'] = ' '.join(headers)
    kv = map('{0[0]}="{0[1]}"'.format, param_map.items())
    kv_string = ','.join(kv)
    if sign_header.lower() == 'authorization':
        return '{0}'.format(kv_string)

    return kv_string


def lkv(d):
    parts = []
    while d:
            length = struct.unpack('>I', d[:4])[0]
            bits = d[4:length+4]
            parts.append(bits)
            d = d[length+4:]
    return parts


def sig(d):
    return lkv(d)[1]


def is_rsa(keyobj):
    return lkv(keyobj.blob)[0] == "ssh-rsa"


# based on http://stackoverflow.com/a/2082169/151401
class CaseInsensitiveDict(dict):
    """ A case-insensitive dictionary for header storage.
        A limitation of this approach is the inability to store
        multiple instances of the same header. If that is changed
        then we suddenly care about the assembly rules in sec 2.3.
    """
    def __init__(self, d=None, **kwargs):
        super(CaseInsensitiveDict, self).__init__(**kwargs)
        if d:
            self.update((k.lower(), v) for k, v in six.iteritems(d))

    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(key.lower())

    def __contains__(self, key):
        return super(CaseInsensitiveDict, self).__contains__(key.lower())


# currently busted...
def get_fingerprint(key):
    """
    Takes an ssh public key and generates the fingerprint.

    See: http://tools.ietf.org/html/rfc4716 for more info
    """
    if key.startswith('ssh-rsa'):
        key = key.split(' ')[1]
    else:
        regex = r'\-{4,5}[\w|| ]+\-{4,5}'
        key = re.split(regex, key)[1]

    key = key.replace('\n', '')
    key = key.strip().encode('ascii')
    key = base64.b64decode(key)
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a+b for a, b in zip(fp_plain[::2], fp_plain[1::2]))
