ENCRYPTED_LEGACY_DIASPORA_PAYLOAD = """<?xml version='1.0'?>
            <diaspora xmlns="https://joindiaspora.com/protocol" xmlns:me="http://salmon-protocol.org/ns/magic-env">
                <encrypted_header>{encrypted_header}</encrypted_header>
                <me:env>
                    <me:data type='application/xml'>{data}</me:data>
                    <me:encoding>base64url</me:encoding>
                    <me:alg>RSA-SHA256</me:alg>
                    <me:sig>{signature}</me:sig>
                </me:env>
            </diaspora>
        """


UNENCRYPTED_LEGACY_DIASPORA_PAYLOAD = """<?xml version='1.0'?>
            <diaspora xmlns="https://joindiaspora.com/protocol" xmlns:me="http://salmon-protocol.org/ns/magic-env">
                <header>
                    <author_id>bob@example.com</author_id>
                </header>
                <me:env>
                    <me:data type='application/xml'>{data}</me:data>
                    <me:encoding>base64url</me:encoding>
                    <me:alg>RSA-SHA256</me:alg>
                    <me:sig>{signature}</me:sig>
                </me:env>
            </diaspora>
        """


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


DIASPORA_ENCRYPTED_PAYLOAD = """{
  "aes_key": "...",
  "encrypted_magic_envelope": "..."
}
"""


DIASPORA_POST_LEGACY = """<XML>
      <post>
        <status_message>
          <raw_message>((status message))</raw_message>
          <guid>((guidguidguidguidguidguidguid))</guid>
          <diaspora_handle>alice@alice.diaspora.example.org</diaspora_handle>
          <public>false</public>
          <created_at>2011-07-20T01:36:07Z</created_at>
          <provider_display_name>Socialhome</provider_display_name>
        </status_message>
      </post>
    </XML>
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


DIASPORA_POST_LEGACY_TIMESTAMP = """
    <status_message>
      <text>((status message))</text>
      <guid>((guidguidguidguidguidguidguid))</guid>
      <author>alice@alice.diaspora.example.org</author>
      <public>false</public>
      <created_at>2011-07-20 01:36:07 UTC</created_at>
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


DIASPORA_POST_WITH_PHOTOS_2 = """
    <status_message>
        <diaspora_handle>xxxxxxxxxxxxxxx@diasp.org</diaspora_handle>
        <guid>fewhefihefifhwihfwehfwehfiuwehfiuwhif</guid>
        <created_at>2017-06-10T14:41:47Z</created_at>
        <provider_display_name>mobile</provider_display_name>
        <raw_message>#foo #bar (fewfefewfwfewfwe)</raw_message>
        <photo>
            <guid>fjwjewiofjoiwjfiowefewew</guid>
            <diaspora_handle>xxxxxxxxxxxxxxx@diasp.org</diaspora_handle>
            <public>true</public>
            <created_at>2017-06-10T14:41:28Z</created_at>
            <remote_photo_path>https://diasp.org/uploads/images/</remote_photo_path>
            <remote_photo_name>fewhuwehiufhuiefhuiwee.jpg</remote_photo_name>
            <text/>
            <status_message_guid>fewhefihefifhwihfwehfwehfiuwehfiuwhif</status_message_guid>
            <height>4032</height>
            <width>3024</width>
        </photo>
        <public>true</public>
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

DIASPORA_REQUEST = """
    <request>
      <author>bob@example.com</author>
      <recipient>alice@alice.diaspora.example.org</recipient>
    </request>
"""

DIASPORA_PROFILE = """
    <profile>
        <author>bob@example.com</author>
        <first_name>Bob Bobertson</first_name>
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
        <first_name>Bob Bobertson</first_name>
        <last_name></last_name>
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

DIASPORA_LEGACY_REQUEST_RETRACTION = """
    <retraction>
        <diaspora_handle>jaywink@iliketoast.net</diaspora_handle>
        <post_guid>7ed1555bc6ae03db</post_guid>
        <type>Person</type>
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
        <provider_display_name/>
        <root_author>bob@example.com</root_author>
        <root_guid>a0b53bc029f6013487753131731751e9</root_guid>
        <public>true</public>
    </reshare>
"""

DIASPORA_RESHARE_LEGACY = """
    <reshare>
        <diaspora_handle>alice@example.org</diaspora_handle>
        <guid>a0b53e5029f6013487753131731751e9</guid>
        <created_at>2016-07-12T00:36:42Z</created_at>
        <provider_display_name/>
        <root_diaspora_id>bob@example.com</root_diaspora_id>
        <root_guid>a0b53bc029f6013487753131731751e9</root_guid>
        <public>true</public>
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
