import datetime
import logging
import math
import re
from base64 import b64encode, b64decode
from copy import copy
from funcy import omit
from pyld import jsonld

from Crypto.Hash import SHA256
from Crypto.PublicKey.RSA import import_key
from Crypto.Signature import pkcs1_15

from federation.utils.activitypub import retrieve_and_parse_document


logger = logging.getLogger("federation")


def create_ld_signature(obj, author):
    # Use models.Signature? Maybe overkill...
    sig = {
        'created': datetime.datetime.now(tz=datetime.timezone.utc).isoformat(timespec='seconds'),
        'creator': f'{author.id}#main-key',
        '@context': 'https://w3id.org/security/v1'
    }

    try:
        private_key = import_key(author.private_key)
    except (ValueError, TypeError) as exc:
        logger.warning('ld_signature - %s', exc)
        return None
    signer = pkcs1_15.new(private_key)

    sig_digest = hash(sig)
    obj_digest = hash(obj)
    digest = (sig_digest + obj_digest).encode('utf-8')

    signature = signer.sign(SHA256.new(digest))
    sig.update({'type': 'RsaSignature2017', 'signatureValue': b64encode(signature).decode()})
    sig.pop('@context')

    obj.update({'signature': sig})


def verify_ld_signature(payload):
    """
    Verify inbound payload LD signature
    """
    signature = copy(payload.get('signature', None))
    if not signature:
        logger.warning('ld_signature - No signature in %s', payload.get("id", "the payload"))
        return None

    # retrieve the author's public key
    profile = retrieve_and_parse_document(signature.get('creator'))
    if not profile:

        logger.warning('ld_signature - Failed to retrieve profile for %s', signature.get("creator"))
        return None
    try:
        pkey = import_key(profile.public_key)
    except ValueError as exc:
        logger.warning('ld_signature - %s', exc)
        return None
    verifier = pkcs1_15.new(pkey)

    # Compute digests and verify signature
    sig = omit(signature, ('type', 'signatureValue'))
    sig.update({'@context': 'https://w3id.org/security/v1'})
    sig_digest = hash(sig)
    obj = omit(payload, 'signature')
    obj_digest = hash(obj)
    digest = (sig_digest + obj_digest).encode('utf-8')

    sig_value = b64decode(signature.get('signatureValue'))
    try:
        verifier.verify(SHA256.new(digest), sig_value)
        logger.debug('ld_signature - %s has a valid signature', payload.get("id"))
        return profile.id
    except ValueError:
        logger.warning('ld_signature - Invalid signature for %s', payload.get("id"))
        return None


def hash(obj):
    nquads = NormalizedDoubles().normalize(obj, options={'format': 'application/nquads', 'algorithm': 'URDNA2015'})
    return SHA256.new(nquads.encode('utf-8')).hexdigest()


# We need this to ensure the digests are identical.
class NormalizedDoubles(jsonld.JsonLdProcessor):
    def _object_to_rdf(self, item, issuer, triples, rdfDirection):
        value = item['@value'] if jsonld._is_value(item) else None
        # The ruby rdf_normalize library turns floats with a zero fraction into integers.
        if isinstance(value, float) and value == math.floor(value):
            item['@value'] = math.floor(value)
        obj = super()._object_to_rdf(item, issuer, triples, rdfDirection)
        # This is to address https://github.com/digitalbazaar/pyld/issues/175
        if obj.get('datatype') == jsonld.XSD_DOUBLE:
            obj['value'] = re.sub(r'(\d)0*E\+?(-)?0*(\d)', r'\1E\2\3', obj['value'])
        return obj
