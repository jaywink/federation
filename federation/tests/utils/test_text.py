from federation.utils.text import decode_if_bytes, encode_if_text, validate_handle, process_text_links


def test_decode_if_bytes():
    assert decode_if_bytes(b"foobar") == "foobar"
    assert decode_if_bytes("foobar") == "foobar"


def test_encode_if_text():
    assert encode_if_text(b"foobar") == b"foobar"
    assert encode_if_text("foobar") == b"foobar"


class TestProcessTextLinks:
    def test_link_at_start_or_end(self):
        assert process_text_links('https://example.org example.org\nhttp://example.org') == \
               '<a href="https://example.org" rel="nofollow" target="_blank">https://example.org</a> ' \
               '<a href="http://example.org" rel="nofollow" target="_blank">example.org</a>\n' \
               '<a href="http://example.org" rel="nofollow" target="_blank">http://example.org</a>'

    def test_existing_links_get_attrs_added(self):
        assert process_text_links('<a href="https://example.org">https://example.org</a>') == \
               '<a href="https://example.org" rel="nofollow" target="_blank">https://example.org</a>'

    def test_code_sections_are_skipped(self):
        assert process_text_links('<code>https://example.org</code><code>\nhttps://example.org\n</code>') == \
               '<code>https://example.org</code><code>\nhttps://example.org\n</code>'

    def test_emails_are_skipped(self):
        assert process_text_links('foo@example.org') == 'foo@example.org'

    def test_does_not_add_target_blank_if_link_is_internal(self):
        assert process_text_links('<a href="/streams/tag/foobar">#foobar</a>') == \
               '<a href="/streams/tag/foobar">#foobar</a>'


def test_validate_handle():
    assert validate_handle("foo@bar.com")
    assert validate_handle("Foo@baR.com")
    assert validate_handle("foo@foo.bar.com")
    assert validate_handle("foo@bar.com:3000")
    assert not validate_handle("@bar.com")
    assert not validate_handle("foo@b/ar.com")
    assert not validate_handle("foo@bar")
    assert not validate_handle("fo/o@bar.com")
    assert not validate_handle("foobar.com")
    assert not validate_handle("foo@bar,com")
