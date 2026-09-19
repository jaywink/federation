from email.utils import formatdate
import requests.auth
import base64, hashlib
import time
try:
    # Python 3
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse

from .sign import HeaderSigner


class HTTPSignatureAuth(requests.auth.AuthBase):
    """
    Sign a request using the http-signature scheme.
    https://github.com/joyent/node-http-signature/blob/master/http_signing.md

    `key_id` is the mandatory label indicating to the server which secret to
      use secret is the filename of a pem file in the case of rsa, a password
      string in the case of an hmac algorithm
    `algorithm` is one of the six specified algorithms
      headers is a list of http headers to be included in the signing string,
      defaulting to "Date" alone.
    """
    def __init__(self, key_id='', secret='', algorithm=None, sign_algorithm=None, headers=None, created=None, expires=None):
        headers = headers or []
        self.header_signer = HeaderSigner(
                                key_id=key_id, secret=secret,
                                algorithm=algorithm, sign_algorithm=sign_algorithm, headers=headers, created=created, expires=expires)
        self.uses_host = 'host' in [h.lower() for h in headers]
        self.created = created
        self.expires = expires

    async def __call__(self, r):
        date = r.headers.pop('date', formatdate(self.created, usegmt=True) if self.created else formatdate(time.time(), usegmt=True))
        r.headers['date'] = date

        if r.body is not None and "digest" in self.header_signer.headers:
            digest = hashlib.sha256(await r.body.as_bytes() if getattr(r.body, 'as_bytes', None) else r.body).digest()
            r.headers["digest"] = "SHA-256=" + base64.b64encode(digest).decode()

        headers = self.header_signer.sign(
                r.headers,
                # 'Host' header unavailable in request object at this point
                # if 'host' header is needed, extract it from the url
                host=urlparse(r.url).netloc if self.uses_host else None,
                method=r.method,
                path=r.path_url,
                created=self.created,
                expires=self.expires)
                
        r.headers.update(headers)
        return r
