ENCRYPTED_DIASPORA_PAYLOAD = """<?xml version='1.0'?>
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


UNENCRYPTED_DIASPORA_PAYLOAD = """<?xml version='1.0'?>
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

DIASPORA_RETRACTION = """
    <retraction>
        <author>bob@example.com</author>
        <target_guid>xxxxxxxxxxxxxxxx</target_guid>
        <target_type>Post</target_type>
    </retraction>
"""
