"""
Thank you Funkwhale for inspiration on the HTTP signatures parts <3

https://funkwhale.audio/
"""
import datetime
import logging
from typing import Union
from urllib.parse import urlsplit

import pytz
from Crypto.PublicKey.RSA import RsaKey
from httpsig.sign_algorithms import PSS
from httpsig.requests_auth import HTTPSignatureAuth
from httpsig.verify import HeaderVerifier


from federation.types import RequestType
from federation.utils.network import parse_http_date
from federation.utils.text import encode_if_text

logger = logging.getLogger("federation")


def get_http_authentication(private_key: RsaKey, private_key_id: str, digest: bool=True) -> HTTPSignatureAuth:
    """
    Get HTTP signature authentication for a request.
    """
    key = private_key.exportKey()
    headers = ["(request-target)", "user-agent", "host", "date"]
    if digest: headers.append('digest')
    return HTTPSignatureAuth(
        headers=headers,
        algorithm="rsa-sha256",
        secret=key,
        key_id=private_key_id,
    )


def verify_request_signature(request: RequestType):
    """
    Verify HTTP signature in request against a public key.
    """
    from federation.utils.activitypub import retrieve_and_parse_document
    
    sig_struct = request.headers["Signature"]
    sig = {i.split("=", 1)[0]: i.split("=", 1)[1].strip('"') for i in sig_struct.split(",")}
    signer = retrieve_and_parse_document(sig.get('keyId'))
    if not signer:
        raise ValueError(f"Failed to retrieve keyId for {sig.get('keyId')}")

    if not getattr(signer, 'public_key_dict', None):
        raise ValueError(f"Failed to retrieve public key for {sig.get('keyId')}")

    key = encode_if_text(signer.public_key_dict['publicKeyPem'])

    date_header = request.headers.get("Date")
    if not date_header:
        raise ValueError("Request Date header is missing")

    ts = parse_http_date(date_header)
    dt = datetime.datetime.utcfromtimestamp(ts).replace(tzinfo=pytz.utc)
    past_delta = datetime.timedelta(hours=24)
    future_delta = datetime.timedelta(seconds=30)
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    if dt < now - past_delta or dt > now + future_delta:
        raise ValueError("Request Date is too far in future or past")

    path = getattr(request, 'path', urlsplit(request.url).path)
    if not HeaderVerifier(request.headers, key, method=request.method,
            path=path, sign_header='signature',
            sign_algorithm=PSS() if sig.get('algorithm',None) == 'hs2019' else None).verify():
        raise ValueError("Invalid signature")

    return signer.id
