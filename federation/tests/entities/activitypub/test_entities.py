import commonmark
import pytest
from unittest.mock import patch
from pprint import pprint

# noinspection PyPackageRequirements
from Crypto.PublicKey.RSA import RsaKey

from federation.entities.activitypub.models import context_manager
from federation.entities.activitypub.models import Accept
from federation.tests.fixtures.keys import PUBKEY
from federation.types import UserType
from federation.utils.text import process_text_links


class TestEntitiesConvertToAS2:
    def test_accept_to_as2(self, activitypubaccept):
        result = activitypubaccept.to_as2()
        assert result == {
            "@context": context_manager.build_context(activitypubaccept),
            "id": "https://localhost/accept",
            "type": "Accept",
            "actor": "https://localhost/profile",
            "object": {
                "id": "https://localhost/follow",
                "type": "Follow",
                "actor": "https://localhost/profile",
                "object": "https://example.com/profile",
            },
        }

    def test_announce_to_as2(self, activitypubannounce):
        result = activitypubannounce.to_as2()
        assert result == {
            "@context": context_manager.build_context(activitypubannounce),
            "id": "http://127.0.0.1:8000/post/123456/#create",
            "type": "Announce",
            "actor": "http://127.0.0.1:8000/profile/123456/",
            "object": "http://127.0.0.1:8000/post/012345/",
            'published': '2019-08-05T00:00:00',
        }

    def test_comment_to_as2(self, activitypubcomment):
        activitypubcomment.pre_send()
        result = activitypubcomment.to_as2()
        assert result == {
            '@context': context_manager.build_context(activitypubcomment),
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Note',
                'url': 'http://127.0.0.1:8000/post/123456/',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<p>raw_content</p>',
                'published': '2019-04-27T00:00:00',
                'inReplyTo': 'http://127.0.0.1:8000/post/012345/',
                'sensitive': False,
                'source': {
                    'content': 'raw_content',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    def test_comment_to_as2__url_in_raw_content(self, activitypubcomment):
        activitypubcomment.raw_content = 'raw_content http://example.com'
        activitypubcomment.rendered_content = process_text_links(
            commonmark.commonmark(activitypubcomment.raw_content).strip())
        activitypubcomment.pre_send()
        result = activitypubcomment.to_as2()
        assert result == {
            '@context': context_manager.build_context(activitypubcomment),
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Note',
                'url': 'http://127.0.0.1:8000/post/123456/',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<p>raw_content <a href="http://example.com" rel="nofollow" target="_blank">'
                           'http://example.com</a></p>',
                'published': '2019-04-27T00:00:00',
                'inReplyTo': 'http://127.0.0.1:8000/post/012345/',
                'sensitive': False,
                'source': {
                    'content': 'raw_content http://example.com',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    def test_follow_to_as2(self, activitypubfollow):
        result = activitypubfollow.to_as2()
        assert result == {
            "@context": context_manager.build_context(activitypubfollow),
            "id": "https://localhost/follow",
            "type": "Follow",
            "actor": "https://localhost/profile",
            "object": "https://example.com/profile"
        }

    def test_follow_to_as2__undo(self, activitypubundofollow):
        result = activitypubundofollow.to_as2()
        result["id"] = "https://localhost/undo"  # Real object will have a random UUID postfix here
        result["object"]["id"] = "https://localhost/follow"  # Real object will have a random UUID postfix here
        assert result == {
            "@context": context_manager.build_context(activitypubundofollow),
            "id": "https://localhost/undo",
            "type": "Undo",
            "actor": "https://localhost/profile",
            "object": {
                "id": "https://localhost/follow",
                "type": "Follow",
                "actor": "https://localhost/profile",
                "object": "https://example.com/profile",
            }
        }

    def test_post_to_as2(self, activitypubpost):
        activitypubpost.rendered_content = commonmark.commonmark(activitypubpost.raw_content).strip()
        activitypubpost.pre_send()
        result = activitypubpost.to_as2()
        assert result == {
            '@context': context_manager.build_context(activitypubpost),
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'cc': ['https://http://127.0.0.1:8000/profile/123456/followers/'],
            'to': ['https://www.w3.org/ns/activitystreams#Public'],
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'cc': ['https://http://127.0.0.1:8000/profile/123456/followers/'],
                'to': ['https://www.w3.org/ns/activitystreams#Public'],
                'type': 'Note',
                'url': 'http://127.0.0.1:8000/post/123456/',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<h1>raw_content</h1>',
                'published': '2019-04-27T00:00:00',
                'sensitive': False,
                'source': {
                    'content': '# raw_content',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    # TODO: fix this test.
    @pytest.mark.skip
    def test_post_to_as2__with_mentions(self, activitypubpost_mentions):
        activitypubpost_mentions.pre_send()
        result = activitypubpost_mentions.to_as2()
        assert result == {
            '@context': context_manager.build_context(activitypubpost_mentions),
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Note',
                'url': 'http://127.0.0.1:8000/post/123456/',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<h1>raw_content</h1>\n<p>@{someone@localhost.local} @<a class="mention" '
                           'href="http://localhost.local/someone" rel="nofollow" target="_blank">'
                           '<span>Bob Bobértson</span></a></p>',
                'published': '2019-04-27T00:00:00',
                'sensitive': False,
                'tag': [
                    {
                        "type": "Mention",
                        "href": "http://localhost.local/someone",
                        "name": "http://localhost.local/someone",
                    },
                    {
                        "type": "Mention",
                        "href": "jaywink@localhost.local",
                        "name": "jaywink@localhost.local",
                    },
                    {
                        "type": "Mention",
                        "href": "someone@localhost.local",
                        "name": "someone@localhost.local",
                    },
                ],
                'source': {
                    'content': '# raw_content\n\n@{someone@localhost.local} @{http://localhost.local/someone}',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    def test_post_to_as2__with_tags(self, activitypubpost_tags):
        activitypubpost_tags.rendered_content = '<h1>raw_content</h1>\n' \
            '<p><a class="hashtag" ' \
            'href="https://example.com/tag/foobar/" rel="noopener ' \
            'noreferrer nofollow" ' \
            'target="_blank">#<span>foobar</span></a>\n' \
            '<a class="hashtag" ' \
            'href="https://example.com/tag/barfoo/" rel="noopener ' \
            'noreferrer nofollow" ' \
            'target="_blank">#<span>barfoo</span></a></p>'
        activitypubpost_tags.pre_send()
        result = activitypubpost_tags.to_as2()
        assert result == {
            '@context': context_manager.build_context(activitypubpost_tags),
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Note',
                'url': 'http://127.0.0.1:8000/post/123456/',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<h1>raw_content</h1>\n'
                           '<p><a class="hashtag" '
                           'href="https://example.com/tag/foobar/" rel="noopener '
                           'noreferrer nofollow" '
                           'target="_blank">#<span>foobar</span></a>\n'
                           '<a class="hashtag" '
                           'href="https://example.com/tag/barfoo/" rel="noopener '
                           'noreferrer nofollow" '
                           'target="_blank">#<span>barfoo</span></a></p>',
                'published': '2019-04-27T00:00:00',
                'sensitive': False,
                'tag': [
                    {
                        "type": "Hashtag",
                        "href": "https://example.com/tag/barfoo/",
                        "name": "#barfoo",
                    },
                    {
                        "type": "Hashtag",
                        "href": "https://example.com/tag/foobar/",
                        "name": "#foobar",
                    },
                ],
                'source': {
                    'content': '# raw_content\n#foobar\n#barfoo',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    def test_post_to_as2__with_images(self, activitypubpost_images):
        activitypubpost_images.rendered_content = '<p>raw_content</p>'
        activitypubpost_images.pre_send()
        result = activitypubpost_images.to_as2()
        assert result == {
            '@context': context_manager.build_context(activitypubpost_images),
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Note',
                'url': 'http://127.0.0.1:8000/post/123456/',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<p>raw_content</p>',
                'published': '2019-04-27T00:00:00',
                'sensitive': False,
                'attachment': [
                    {
                        'type': 'Image',
                        'mediaType': 'image/jpeg',
                        'url': 'foobar',
                        'pyfed:inlineImage': False,
                    },
                    {
                        'type': 'Image',
                        'mediaType': 'image/jpeg',
                        'name': 'spam and eggs',
                        'url': 'barfoo',
                        'pyfed:inlineImage': False,
                    },
                ],
                'source': {
                    'content': 'raw_content',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    def test_post_to_as2__with_diaspora_guid(self, activitypubpost_diaspora_guid):
        activitypubpost_diaspora_guid.rendered_content = '<p>raw_content</p>'
        activitypubpost_diaspora_guid.pre_send()
        result = activitypubpost_diaspora_guid.to_as2()
        assert result == {
            '@context': context_manager.build_context(activitypubpost_diaspora_guid),
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'diaspora:guid': 'totallyrandomguid',
                'type': 'Note',
                'url': 'http://127.0.0.1:8000/post/123456/',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<p>raw_content</p>',
                'published': '2019-04-27T00:00:00',
                'sensitive': False,
                'source': {
                    'content': 'raw_content',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    # noinspection PyUnusedLocal
    def test_profile_to_as2(self, activitypubprofile):
        result = activitypubprofile.to_as2()
        assert result == {
            "@context": context_manager.build_context(activitypubprofile),
            "endpoints": {
                "sharedInbox": "https://example.com/public",
            },
            "followers": "https://example.com/bob/followers/",
            "following": "https://example.com/bob/following/",
            "id": "https://example.com/bob",
            "inbox": "https://example.com/bob/private",
            "manuallyApprovesFollowers": False,
            "name": "Bob Bobertson",
            "outbox": "https://example.com/bob/outbox/",
            "publicKey": {
                "id": "https://example.com/bob#main-key",
                "owner": "https://example.com/bob",
                "publicKeyPem": PUBKEY,
            },
            'published': '2022-09-06T00:00:00',
            "type": "Person",
            "url": "https://example.com/bob-bobertson",
            "summary": "foobar",
            "icon": {
                "type": "Image",
                "url": "urllarge",
                "mediaType": "image/jpeg",
                "pyfed:inlineImage": False,
            }
        }

    # noinspection PyUnusedLocal
    def test_profile_to_as2__with_diaspora_guid(self, activitypubprofile_diaspora_guid):
        result = activitypubprofile_diaspora_guid.to_as2()
        assert result == {
            "@context": context_manager.build_context(activitypubprofile_diaspora_guid),
            "endpoints": {
                "sharedInbox": "https://example.com/public",
            },
            "followers": "https://example.com/bob/followers/",
            "following": "https://example.com/bob/following/",
            "id": "https://example.com/bob",
            "diaspora:guid": "totallyrandomguid",
            "diaspora:handle": "bob@example.com",
            "inbox": "https://example.com/bob/private",
            "manuallyApprovesFollowers": False,
            "name": "Bob Bobertson",
            "outbox": "https://example.com/bob/outbox/",
            "publicKey": {
                "id": "https://example.com/bob#main-key",
                "owner": "https://example.com/bob",
                "publicKeyPem": PUBKEY,
            },
            'published': '2022-09-06T00:00:00',
            "type": "Person",
            "url": "https://example.com/bob-bobertson",
            "summary": "foobar",
            "icon": {
                "type": "Image",
                "url": "urllarge",
                "mediaType": "image/jpeg",
                "pyfed:inlineImage": False,
            }
        }

    def test_retraction_to_as2(self, activitypubretraction):
        result = activitypubretraction.to_as2()
        assert result == {
            '@context': context_manager.build_context(activitypubretraction),
            'type': 'Delete',
            'id': 'http://127.0.0.1:8000/post/123456/#delete',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Tombstone',
            },
            'published': '2019-04-27T00:00:00',
        }

    def test_retraction_to_as2__announce(self, activitypubretraction_announce):
        result = activitypubretraction_announce.to_as2()
        assert result == {
            '@context': context_manager.build_context(activitypubretraction_announce),
            'type': 'Undo',
            'id': 'http://127.0.0.1:8000/post/123456/#delete',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'actor': 'http://127.0.0.1:8000/profile/123456/',
                'id': 'http://127.0.0.1:8000/post/123456/activity',
                'object': 'http://127.0.0.1:8000/post/123456',
                'type': 'Announce',
                'published': '2019-04-27T00:00:00',
            },
        }


class TestEntitiesPostReceive:
    @patch("federation.entities.activitypub.models.retrieve_and_parse_profile", autospec=True)
    @patch("federation.entities.activitypub.models.handle_send", autospec=True)
    def test_follow_post_receive__sends_correct_accept_back(
            self, mock_send, mock_retrieve, activitypubfollow, profile
    ):
        mock_retrieve.return_value = profile
        activitypubfollow.post_receive()
        args, kwargs = mock_send.call_args_list[0]
        assert isinstance(args[0], Accept)
        assert args[0].activity_id.startswith("https://example.com/profile#accept-")
        assert args[0].actor_id == "https://example.com/profile"
        assert args[0].target_id == "https://localhost/follow"
        assert isinstance(args[1], UserType)
        assert args[1].id == "https://example.com/profile"
        assert isinstance(args[1].private_key, RsaKey)
        assert kwargs['recipients'] == [{
            "endpoint": "https://example.com/bob/private",
            "fid": "https://localhost/profile",
            "protocol": "activitypub",
            "public": False,
        }]


class TestEntitiesPreSend:
    def test_post_inline_images_are_attached(self, activitypubpost_embedded_images):
        activitypubpost_embedded_images.pre_send()
        assert len(activitypubpost_embedded_images._children) == 4
        image = activitypubpost_embedded_images._children[0]
        assert image.url == "https://example.com/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a902541476.jpeg"
        assert image.name == ""
        assert image.inline
        image = activitypubpost_embedded_images._children[1]
        assert image.url == "https://jasonrobinson.me/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a902541477.png"
        assert image.name == ""
        assert image.inline
        image = activitypubpost_embedded_images._children[2]
        assert image.url == "https://jasonrobinson.me/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a902541478.gif"
        assert image.name == "foobar"
        assert image.inline
        image = activitypubpost_embedded_images._children[3]
        assert image.url == "https://jasonrobinson.me/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a902541479.jpg"
        assert image.name == "foobar barfoo"
        assert image.inline
