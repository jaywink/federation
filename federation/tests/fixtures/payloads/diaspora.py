DIASPORA_PUBLIC_PAYLOAD = """<?xml version='1.0' encoding='UTF-8'?>
<me:env xmlns:me="http://salmon-protocol.org/ns/magic-env">
    <me:encoding>base64url</me:encoding>
    <me:alg>RSA-SHA256</me:alg>
    <me:data type="application/xml">PHN0YXR1c19tZXNzYWdlPjxmb28-YmFyPC9mb28-PC9zdGF0dXNfbWVzc2FnZT4=</me:data>
    <me:sig key_id="Zm9vYmFyQGV4YW1wbGUuY29t">Cmk08MR4Tp8r9eVybD1hORcR_8NLRVxAu0biOfJbkI1xLx1c480zJ720cpVyKaF9""" \
    """CxVjW3lvlvRz5YbswMv0izPzfHpXoWTXH-4UPrXaGYyJnrNvqEB2UWn4iHKJ2Rerto8sJY2b95qbXD6Nq75EoBNub5P7DYc16ENhp3""" \
    """8YwBRnrBEvNOewddpOpEBVobyNB7no_QR8c_xkXie-hUDFNwI0z7vax9HkaBFbvEmzFPMZAAdWyjxeGiWiqY0t2ZdZRCPTezy66X6Q0""" \
    """qc4I8kfT-Mt1ctjGmNMoJ4Lgu-PrO5hSRT4QBAVyxaog5w-B0PIPuC-mUW5SZLsnX3_ZuwJww==</me:sig>
</me:env>
"""

DIASPORA_RESHARE_PAYLOAD = """<?xml version="1.0" encoding="UTF-8"?>
<me:env xmlns:me="http://salmon-protocol.org/ns/magic-env">
  <me:data type="application/xml">PHN0YXR1c19tZXNzYWdlPgogIDxhdXRob3I-YXJ0c291bmQyQGRpYXNwLmV1PC9hdXRob3I-CiAgPGd1aWQ-NjI2NGNjNzAyOGM5MDEzNzQyODk0MDYxODYyYjhlN2I8L2d1aWQ-CiAgPGNyZWF0ZWRfYXQ-MjAxOS0wMy0xNFQyMDo1NToxMlo8L2NyZWF0ZWRfYXQ-CiAgPHB1YmxpYz50cnVlPC9wdWJsaWM-CiAgPHRleHQ-KipQbGVhc2Ugc3RheSBvZmYgdGhlIGdyYXNzIC4uLiBvcioqJiN4RDsKIVtdKGh0dHBzOi8vNjYubWVkaWEudHVtYmxyLmNvbS9kNGViMTMyMTZlZWY5ODE1ZjMzNTBhZDk1OTk5MmYxYy90dW1ibHJfcG80aXRjNzJKbjF5M3F1d25vMV81MDAuanBnKSYjeEQ7CiNzdGF5b2ZmPC90ZXh0Pgo8L3N0YXR1c19tZXNzYWdlPg==</me:data>
  <me:encoding>base64url</me:encoding>
  <me:alg>RSA-SHA256</me:alg>
  <me:sig key_id="YXJ0c291bmQyQGRpYXNwLmV1">VWvuHE-HNgQGoCUqlNOEzl4qmrW3hl5qv4CwFu3-WXHeaB2ULGNDDbqO2sWE5R4TFjT-3WNLyma1QnL3dnozmnzdUT1DnL_Il2BwTTEUa3qHl1qaepikPWF_VKDTez-NJUzQCOFGENZcBSTfBy7yP0dErHhewaLXcXg37nCLyTN2elftE7x80BDXMZouApIMht2NvSwH91tIRw474Tuce2316JtVEdGhiGgzZ5iIF7BycUKw4Redxdc2RPvgJNWWqvgO6jYyc7rgzRtj1a_K7gA30Y280k6DkwNut8tCcUqU1FCN5AWT2S_vF8DIG3MWEBtqs7lDxDcjKBcQsXS9IY9sSwKr7kfT6wh6weHr2EbBv9ZPtbEL3_PY_orGLoz7MeJrO9bY2K59SptAs66esNJaqtQvlnbYXB8i6xLLWsTBc9t9WEx1EsBzLN5gak58evUoQVtVXQZ2kdR_rYR0U1dhVDWihL2fc_x7dkR2W8QTZKXPbdQwfday6msSOqQLWQ7NzJTh5djvkapY6Clu-ka_mMi7Avm0bzK5bEoGVUQidRM6Gq_e6hoPvq5J3-0SyAacQvP1sa9XEMHhvdumlnFPuwrcLHRb2utWlUS2L5BjXSlOt-k-HhSXFi5ClxFJL_-LqPeMOgCS07ogfeN_ZHfwNTMDdToVkBPi11sM0PY=</me:sig>
</me:env>
"""

DIASPORA_ENCRYPTED_PAYLOAD = """{
  "aes_key": "...",
  "encrypted_magic_envelope": "..."
}
"""

DIASPORA_POST_SIMPLE = """
    <status_message>
      <text>((status message))</text>
      <guid>((guidguidguidguidguidguidguid))</guid>
      <author>alice@alice.diaspora.example.org</author>
      <public>false</public>
      <created_at>2011-07-20T01:36:07Z</created_at>
      <provider_display_name>Socialhome</provider_display_name>
    </status_message>
"""

DIASPORA_POST_SIMPLE_WITH_MENTION = """
    <status_message>
      <text>((status message)) @{Jason Robinson 🐍🍻; jaywink@jasonrobinson.me}</text>
      <guid>((guidguidguidguidguidguidguid))</guid>
      <author>alice@alice.diaspora.example.org</author>
      <public>false</public>
      <created_at>2011-07-20T01:36:07Z</created_at>
      <provider_display_name>Socialhome</provider_display_name>
    </status_message>
"""

DIASPORA_POST_WITH_PHOTOS = """
    <status_message>
      <text>((status message))</text>
      <guid>((guidguidguidguidguidguidguid))</guid>
      <author>alice@alice.diaspora.example.org</author>
      <public>false</public>
      <created_at>2011-07-20T01:36:07Z</created_at>
      <provider_display_name>Socialhome</provider_display_name>
      <photo>
        <guid>((guidguidguidguidguidguidguif))</guid>
        <author>alice@alice.diaspora.example.org</author>
        <public>false</public>
        <created_at>2011-07-20T01:36:07Z</created_at>
        <remote_photo_path>https://alice.diaspora.example.org/uploads/images/</remote_photo_path>
        <remote_photo_name>1234.jpg</remote_photo_name>
        <text/>
        <status_message_guid>((guidguidguidguidguidguidguid))</status_message_guid>
        <height>120</height>
        <width>120</width>
      </photo>
    </status_message>
"""

DIASPORA_POST_INVALID = """
    <status_message>
      <text>((status message))</text>
      <author>alice@alice.diaspora.example.org</author>
      <public>false</public>
      <created_at>2011-07-20T01:36:07Z</created_at>
      <provider_display_name>Socialhome</provider_display_name>
    </status_message>
"""

DIASPORA_POST_COMMENT = """
    <comment>
      <guid>((guidguidguidguidguidguid))</guid>
      <parent_guid>((parent_guidparent_guidparent_guidparent_guid))</parent_guid>
      <author_signature>((base64-encoded data))</author_signature>
      <text>((text))</text>
      <author>alice@alice.diaspora.example.org</author>
      <author_signature>((signature))</author_signature>
    </comment>
"""

DIASPORA_POST_COMMENT_NESTED = """
    <comment>
      <guid>((guidguidguidguidguidguid))</guid>
      <parent_guid>((parent_guidparent_guidparent_guidparent_guid))</parent_guid>
      <thread_parent_guid>((threadparentguid))</thread_parent_guid>
      <author_signature>((base64-encoded data))</author_signature>
      <text>((text))</text>
      <author>alice@alice.diaspora.example.org</author>
      <author_signature>((signature))</author_signature>
    </comment>
"""

DIASPORA_POST_LIKE = """
    <like>
      <parent_type>Post</parent_type>
      <guid>((guidguidguidguidguidguid))</guid>
      <parent_guid>((parent_guidparent_guidparent_guidparent_guid))</parent_guid>
      <author_signature>((base64-encoded data))</author_signature>
      <positive>true</positive>
      <author>alice@alice.diaspora.example.org</author>
      <author_signature>((signature))</author_signature>
    </like>
"""

DIASPORA_PROFILE = """
    <profile>
        <author>bob@example.com</author>
        <first_name>Bob</first_name>
        <last_name>Bobertson</last_name>
        <image_url>https://example.com/uploads/images/thumb_large_c833747578b5.jpg</image_url>
        <image_url_small>https://example.com/uploads/images/thumb_small_c8b147578b5.jpg</image_url_small>
        <image_url_medium>https://example.com/uploads/images/thumb_medium_c8b1aab04f3.jpg</image_url_medium>
        <gender></gender>
        <bio>A cool bio</bio>
        <location>Helsinki</location>
        <searchable>true</searchable>
        <nsfw>false</nsfw>
        <tag_string>#socialfederation #federation</tag_string>
    </profile>
"""

DIASPORA_PROFILE_FIRST_NAME_ONLY = """
    <profile>
        <author>bob@example.com</author>
        <first_name>Bob</first_name>
        <last_name></last_name>
        <image_url>https://example.com/uploads/images/thumb_large_c833747578b5.jpg</image_url>
        <image_url_small>https://example.com/uploads/images/thumb_small_c8b147578b5.jpg</image_url_small>
        <image_url_medium>https://example.com/uploads/images/thumb_medium_c8b1aab04f3.jpg</image_url_medium>
        <gender></gender>
        <bio>A cool bio</bio>
        <location>Helsinki</location>
        <searchable>true</searchable>
        <nsfw>false</nsfw>
        <tag_string>#socialfederation #federation</tag_string>
    </profile>
"""

DIASPORA_PROFILE_EMPTY_TAGS = """
    <profile>
        <author>bob@example.com</author>
        <first_name>Bob</first_name>
        <last_name>Bobertson</last_name>
        <image_url>https://example.com/uploads/images/thumb_large_c833747578b5.jpg</image_url>
        <image_url_small>https://example.com/uploads/images/thumb_small_c8b147578b5.jpg</image_url_small>
        <image_url_medium>https://example.com/uploads/images/thumb_medium_c8b1aab04f3.jpg</image_url_medium>
        <gender></gender>
        <bio>A cool bio</bio>
        <location>Helsinki</location>
        <searchable>true</searchable>
        <nsfw>false</nsfw>
        <tag_string/>
    </profile>
"""

DIASPORA_RETRACTION = """
    <retraction>
        <author>bob@example.com</author>
        <target_guid>xxxxxxxxxxxxxxxx</target_guid>
        <target_type>Post</target_type>
    </retraction>
"""

DIASPORA_CONTACT = """
    <contact>
        <author>alice@example.com</author>
        <recipient>bob@example.org</recipient>
        <following>true</following>
        <sharing>true</sharing>
    </contact>
"""

DIASPORA_RESHARE = """
    <reshare>
        <author>alice@example.org</author>
        <guid>a0b53e5029f6013487753131731751e9</guid>
        <created_at>2016-07-12T00:36:42Z</created_at>
        <root_author>bob@example.com</root_author>
        <root_guid>a0b53bc029f6013487753131731751e9</root_guid>
        <text></text>
    </reshare>
"""

DIASPORA_RESHARE_WITH_EXTRA_PROPERTIES = """
    <reshare>
        <author>alice@example.org</author>
        <guid>a0b53e5029f6013487753131731751e9</guid>
        <created_at>2016-07-12T00:36:42Z</created_at>
        <provider_display_name/>
        <root_author>bob@example.com</root_author>
        <root_guid>a0b53bc029f6013487753131731751e9</root_guid>
        <public>true</public>
        <raw_content>Important note here</raw_content>
        <entity_type>Comment</entity_type>
    </reshare>
"""

DIASPORA_WEBFINGER_JSON = """{
  "subject": "acct:alice@example.org",
  "links": [
    {
      "rel": "http://microformats.org/profile/hcard",
      "type": "text/html",
      "href": "https://example.org/hcard/users/7dba7ca01d64013485eb3131731751e9"
    },
    {
      "rel": "http://joindiaspora.com/seed_location",
      "type": "text/html",
      "href": "https://example.org/"
    }
  ]
}
"""

DIASPORA_HOSTMETA = """<?xml version="1.0" encoding="UTF-8"?>
<XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0">
  <Link rel="lrdd" template="https://example.com/webfinger?q={uri}" type="application/xrd+xml"/>
</XRD>
"""

DIASPORA_WEBFINGER = """<?xml version="1.0" encoding="UTF-8"?>
<XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0">
  <Subject>acct:user@server.example</Subject>
  <Alias>https://server.example/people/0123456789abcdef</Alias>
  <Link href="https://server.example/hcard/users/0123456789abcdef" rel="http://microformats.org/profile/hcard" type="text/html"/>
  <Link href="https://server.example" rel="http://joindiaspora.com/seed_location" type="text/html"/>
  <Link href="0123456789abcdef" rel="http://joindiaspora.com/guid" type="text/html"/>
  <Link href="https://server.example/u/user" rel="http://webfinger.net/rel/profile-page" type="text/html"/>
  <Link href="https://server.example/public/user.atom" rel="http://schemas.google.com/g/2010#updates-from" type="application/atom+xml"/>
  <Link href="QUJDREVGPT0=" rel="diaspora-public-key" type="RSA"/>
</XRD>
"""
