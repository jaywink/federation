from federation.utils.text import decode_if_bytes, encode_if_text, validate_handle, process_text_links, find_tags


def test_decode_if_bytes():
    assert decode_if_bytes(b"foobar") == "foobar"
    assert decode_if_bytes("foobar") == "foobar"


def test_encode_if_text():
    assert encode_if_text(b"foobar") == b"foobar"
    assert encode_if_text("foobar") == b"foobar"


class TestFindTags:
    @staticmethod
    def _replacer(text):
        return f"#{text}/{text.lower()}"

    def test_all_tags_are_parsed_from_text(self):
        source = "#starting and #MixED with some #line\nendings also tags can\n#start on new line"
        tags, text = find_tags(source)
        assert tags == {"starting", "mixed", "line", "start"}
        assert text == source
        tags, text = find_tags(source, replacer=self._replacer)
        assert text == "#starting/starting and #MixED/mixed with some #line/line\nendings also tags can\n" \
                       "#start/start on new line"

    def test_code_block_tags_ignored(self):
        source = "foo\n```\n#code\n```\n#notcode\n\n    #alsocode\n"
        tags, text = find_tags(source)
        assert tags == {"notcode"}
        assert text == source
        tags, text = find_tags(source, replacer=self._replacer)
        assert text == "foo\n```\n#code\n```\n#notcode/notcode\n\n    #alsocode\n"

    def test_endings_are_filtered_out(self):
        source = "#parenthesis) #exp! #list]"
        tags, text = find_tags(source)
        assert tags == {"parenthesis", "exp", "list"}
        assert text == source
        tags, text = find_tags(source, replacer=self._replacer)
        assert text == "#parenthesis/parenthesis) #exp/exp! #list/list]"

    def test_finds_tags(self):
        source = "#post **Foobar** #tag #OtherTag #third\n#fourth"
        tags, text = find_tags(source)
        assert tags == {"third", "fourth", "post", "othertag", "tag"}
        assert text == source
        tags, text = find_tags(source, replacer=self._replacer)
        assert text == "#post/post **Foobar** #tag/tag #OtherTag/othertag #third/third\n#fourth/fourth"

    def test_ok_with_html_tags_in_text(self):
        source = "<p>#starting and <span>#MixED</span> however not <#>this</#> or <#/>that"
        tags, text = find_tags(source)
        assert tags == {"starting", "mixed"}
        assert text == source
        tags, text = find_tags(source, replacer=self._replacer)
        assert text == "<p>#starting/starting and <span>#MixED/mixed</span> however not <#>this</#> or <#/>that"

    def test_postfixed_tags(self):
        source = "#foo) #bar] #hoo, #hee."
        tags, text = find_tags(source)
        assert tags == {"foo", "bar", "hoo", "hee"}
        assert text == source
        tags, text = find_tags(source, replacer=self._replacer)
        assert text == "#foo/foo) #bar/bar] #hoo/hoo, #hee/hee."

    def test_prefixed_tags(self):
        source = "(#foo [#bar"
        tags, text = find_tags(source)
        assert tags == {"foo", "bar"}
        assert text == source
        tags, text = find_tags(source, replacer=self._replacer)
        assert text == "(#foo/foo [#bar/bar"

    def test_invalid_text_returns_no_tags(self):
        source = "#a!a #a#a #a$a #a%a #a^a #a&a #a*a #a+a #a.a #a,a #a@a #a£a #a/a #a(a #a)a #a=a " \
                 "#a?a #a`a #a'a #a\\a #a{a #a[a #a]a #a}a #a~a #a;a #a:a #a\"a #a’a #a”a #\xa0cd"
        tags, text = find_tags(source)
        assert tags == set()
        assert text == source
        tags, text = find_tags(source, replacer=self._replacer)
        assert text == source


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
