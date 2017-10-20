from lxml import etree

from federation.protocols.diaspora.signatures import create_relayable_signature, verify_relayable_signature
from federation.tests.fixtures.keys import PUBKEY, SIGNATURE, SIGNATURE2, SIGNATURE3, XML, XML2, get_dummy_private_key


def test_verify_relayable_signature():
    doc = etree.XML(XML)
    assert verify_relayable_signature(PUBKEY, doc, SIGNATURE)


def test_verify_relayable_signature_with_unicode():
    doc = etree.XML(XML2)
    assert verify_relayable_signature(PUBKEY, doc, SIGNATURE2)


def test_create_relayable_signature():
    doc = etree.XML(XML)
    signature = create_relayable_signature(get_dummy_private_key(), doc)
    assert signature == SIGNATURE3
