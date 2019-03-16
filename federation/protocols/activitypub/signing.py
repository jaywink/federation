"""
Thank you Funkwhale for inspiration on the HTTP signatures parts <3

https://funkwhale.audio/
"""
import datetime
import logging
from typing import Union

import pytz
from requests_http_signature import HTTPSignatureHeaderAuth

from federation.types import RequestType
from federation.utils.network import parse_http_date
from federation.utils.text import decode_if_bytes, encode_if_text

logger = logging.getLogger("federation")


def get_http_authentication(private_key: Union[str, bytes], private_key_id: str) -> HTTPSignatureHeaderAuth:
    """
    Get HTTP signature authentication for a request.
    """
    key = decode_if_bytes(private_key)
    return HTTPSignatureHeaderAuth(
        headers=["(request-target)", "user-agent", "host", "date"],
        algorithm="rsa-sha256",
        key=key.encode("utf-8"),
        key_id=private_key_id,
    )


def verify_request_signature(request: RequestType, public_key: Union[str, bytes]):
    """
    Verify HTTP signature in request against a public key.
    """
    key = encode_if_text(public_key)
    date_header = request.headers.get("Date")
    if not date_header:
        raise ValueError("Rquest Date header is missing")

    ts = parse_http_date(date_header)
    dt = datetime.datetime.utcfromtimestamp(ts).replace(tzinfo=pytz.utc)
    delta = datetime.timedelta(seconds=30)
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    if dt < now - delta or dt > now + delta:
        raise ValueError("Request Date is too far in future or past")

    HTTPSignatureHeaderAuth.verify(request, key_resolver=lambda **kwargs: key)
