"""
Thank you Funkwhale for inspiration on the HTTP signatures parts <3

https://funkwhale.audio/
"""
import datetime
import logging
import math
import re
from base64 import b64decode
from  copy import copy
from funcy import omit
from pyld import jsonld
from typing import Union
from urllib.parse import urlsplit

import pytz
from Crypto.Hash import SHA256
from Crypto.PublicKey.RSA import RsaKey, import_key
from Crypto.Signature import pkcs1_15
from httpsig.sign_algorithms import PSS
from httpsig.requests_auth import HTTPSignatureAuth
from httpsig.verify import HeaderVerifier

import federation.utils.jsonld_helper
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


def create_ld_signature(payload, private_key):
    pass


def verify_request_signature(request: RequestType, required: bool=True):
    """
    Verify HTTP signature in request against a public key.
    """
    from federation.utils.activitypub import retrieve_and_parse_document
    
    sig_struct = request.headers.get("Signature", None)
    if not sig_struct:
        if required:
            raise ValueError("A signature is required but was not provided")
        else:
            return None

    # this should return a dict populated with the following keys:
    # keyId, algorithm, headers and signature
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


def verify_ld_signature(payload):
    """
    Verify inbound payload LD signature
    """
    signature = copy(payload.get('signature'))
    if not signature:
        logger.warning('ld_signature - No LD signature in the payload')
        return None # Maybe False would be better?

    # retrieve the author's public key
    from federation.utils.activitypub import retrieve_and_parse_document

    profile = retrieve_and_parse_document(signature.get('creator'))
    if not profile:
        logger.warning(f'ld_signature - Failed to retrieve profile for {signature.get("creator")}')
        return None
    try:
        pkey = import_key(profile.public_key)
    except ValueError as exc:
        logger.warning(f'ld_signature - {exc}')
        return None
    verifier = pkcs1_15.new(pkey)

    # Compute digests and verify signature
    sig = omit(signature, ('type', 'signatureValue'))
    sig.update({'@context':'https://w3id.org/security/v1'})
    sig_nquads = normalize(sig, options={'format':'application/nquads','algorithm':'URDNA2015'}).encode('utf-8')
    sig_digest = SHA256.new(sig_nquads).hexdigest()
    obj = omit(payload, 'signature')
    obj_nquads = normalize(obj, options={'format':'application/nquads','algorithm':'URDNA2015'}).encode('utf-8')
    obj_digest = SHA256.new(obj_nquads).hexdigest()
    digest = (sig_digest + obj_digest).encode('utf-8')

    sig_value = b64decode(signature.get('signatureValue'))
    try:
        verifier.verify(SHA256.new(digest), sig_value)
        logger.debug(f'ld_signature - {payload.get("id")} has a valid signature')
    except ValueError as exc:
        logger.warning(f'ld_signature - invalid signature for {payload.get("id")}')


# We need this to ensure the digests are identical.
def normalize(input_, options):
    return NormalizedDoubles().normalize(input_, options)

class NormalizedDoubles(jsonld.JsonLdProcessor):
    def _object_to_rdf(self, item, issuer, triples, rdfDirection):
        value = item['@value'] if jsonld._is_value(item) else None
        # The ruby rdf_normalize library turns floats with a zero fraction to integers.
        if isinstance(value, float) and value == math.floor(value):
            item['@value'] = math.floor(value)
        obj = super()._object_to_rdf(item, issuer, triples, rdfDirection)
        # This is to address https://github.com/digitalbazaar/pyld/issues/175
        if obj.get('datatype') == jsonld.XSD_DOUBLE:
            obj['value'] = re.sub(r'(\d)0*E\+?(-)?0*(\d)', r'\1E\2\3', obj['value'])

        return obj
