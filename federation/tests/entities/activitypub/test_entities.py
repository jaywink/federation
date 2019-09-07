from unittest.mock import patch

from Crypto.PublicKey.RSA import RsaKey

from federation.entities.activitypub.constants import (
    CONTEXTS_DEFAULT, CONTEXT_MANUALLY_APPROVES_FOLLOWERS, CONTEXT_LD_SIGNATURES)
from federation.entities.activitypub.entities import ActivitypubAccept
from federation.tests.fixtures.keys import PUBKEY
from federation.types import UserType


class TestEntitiesConvertToAS2:
    def test_accept_to_as2(self, activitypubaccept):
        result = activitypubaccept.to_as2()
        assert result == {
            "@context": CONTEXTS_DEFAULT,
            "id": "https://localhost/accept",
            "type": "Accept",
            "actor": "https://localhost/profile",
            "object": {
                "@context": CONTEXTS_DEFAULT,
                "id": "https://localhost/follow",
                "type": "Follow",
                "actor": "https://localhost/profile",
                "object": "https://example.com/profile",
            },
        }

    def test_accounce_to_as2(self, activitypubannounce):
        result = activitypubannounce.to_as2()
        assert result == {
            "@context": CONTEXTS_DEFAULT,
            "id": "http://127.0.0.1:8000/post/123456/#create",
            "type": "Announce",
            "actor": "http://127.0.0.1:8000/profile/123456/",
            "object": "http://127.0.0.1:8000/post/012345/",
            'published': '2019-08-05T00:00:00',
        }

    def test_comment_to_as2(self, activitypubcomment):
        result = activitypubcomment.to_as2()
        assert result == {
            '@context': [
                'https://www.w3.org/ns/activitystreams',
                {"pyfed": "https://docs.jasonrobinson.me/ns/python-federation"},
                {'Hashtag': 'as:Hashtag'},
                'https://w3id.org/security/v1',
                {'sensitive': 'as:sensitive'},
            ],
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Note',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<p>raw_content</p>',
                'published': '2019-04-27T00:00:00',
                'inReplyTo': 'http://127.0.0.1:8000/post/012345/',
                'sensitive': False,
                'summary': None,
                'tag': [],
                'url': '',
                'source': {
                    'content': 'raw_content',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    def test_follow_to_as2(self, activitypubfollow):
        result = activitypubfollow.to_as2()
        assert result == {
            "@context": CONTEXTS_DEFAULT,
            "id": "https://localhost/follow",
            "type": "Follow",
            "actor": "https://localhost/profile",
            "object": "https://example.com/profile"
        }

    def test_follow_to_as2__undo(self, activitypubundofollow):
        result = activitypubundofollow.to_as2()
        result["object"]["id"] = "https://localhost/follow"  # Real object will have a random UUID postfix here
        assert result == {
            "@context": CONTEXTS_DEFAULT,
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
        result = activitypubpost.to_as2()
        assert result == {
            '@context': [
                'https://www.w3.org/ns/activitystreams',
                {"pyfed": "https://docs.jasonrobinson.me/ns/python-federation"},
                {'Hashtag': 'as:Hashtag'},
                'https://w3id.org/security/v1',
                {'sensitive': 'as:sensitive'},
            ],
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Note',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<h1>raw_content</h1>',
                'published': '2019-04-27T00:00:00',
                'inReplyTo': None,
                'sensitive': False,
                'summary': None,
                'tag': [],
                'url': '',
                'source': {
                    'content': '# raw_content',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    def test_post_to_as2__with_tags(self, activitypubpost_tags):
        result = activitypubpost_tags.to_as2()
        assert result == {
            '@context': [
                'https://www.w3.org/ns/activitystreams',
                {"pyfed": "https://docs.jasonrobinson.me/ns/python-federation"},
                {'Hashtag': 'as:Hashtag'},
                'https://w3id.org/security/v1',
                {'sensitive': 'as:sensitive'},
            ],
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Note',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<h1>raw_content</h1>\n<p>#foobar\n#barfoo</p>',
                'published': '2019-04-27T00:00:00',
                'inReplyTo': None,
                'sensitive': False,
                'summary': None,
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
                'url': '',
                'source': {
                    'content': '# raw_content\n#foobar\n#barfoo',
                    'mediaType': 'text/markdown',
                },
            },
            'published': '2019-04-27T00:00:00',
        }

    def test_post_to_as2__with_images(self, activitypubpost_images):
        result = activitypubpost_images.to_as2()
        assert result == {
            '@context': [
                'https://www.w3.org/ns/activitystreams',
                {"pyfed": "https://docs.jasonrobinson.me/ns/python-federation"},
                {'Hashtag': 'as:Hashtag'},
                'https://w3id.org/security/v1',
                {'sensitive': 'as:sensitive'},
            ],
            'type': 'Create',
            'id': 'http://127.0.0.1:8000/post/123456/#create',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/',
                'type': 'Note',
                'attributedTo': 'http://127.0.0.1:8000/profile/123456/',
                'content': '<p>raw_content</p>',
                'published': '2019-04-27T00:00:00',
                'inReplyTo': None,
                'sensitive': False,
                'summary': None,
                'tag': [],
                'url': '',
                'attachment': [
                    {
                        'type': 'Image',
                        'mediaType': 'image/jpeg',
                        'name': '',
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

    @patch("federation.entities.base.fetch_content_type", return_value="image/jpeg")
    def test_profile_to_as2(self, mock_fetch, activitypubprofile):
        result = activitypubprofile.to_as2()
        assert result == {
            "@context": CONTEXTS_DEFAULT + [
                CONTEXT_LD_SIGNATURES,
                CONTEXT_MANUALLY_APPROVES_FOLLOWERS,
            ],
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
            "type": "Person",
            "url": "https://example.com/bob-bobertson",
            "summary": "foobar",
            "icon": {
                "type": "Image",
                "url": "urllarge",
                "mediaType": "image/jpeg",
                "name": "",
                "pyfed:inlineImage": False,
            }
        }

    def test_retraction_to_as2(self, activitypubretraction):
        result = activitypubretraction.to_as2()
        assert result == {
            '@context': [
                'https://www.w3.org/ns/activitystreams',
                {"pyfed": "https://docs.jasonrobinson.me/ns/python-federation"},
            ],
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
            '@context': [
                'https://www.w3.org/ns/activitystreams',
                {"pyfed": "https://docs.jasonrobinson.me/ns/python-federation"},
            ],
            'type': 'Undo',
            'id': 'http://127.0.0.1:8000/post/123456/#delete',
            'actor': 'http://127.0.0.1:8000/profile/123456/',
            'object': {
                'id': 'http://127.0.0.1:8000/post/123456/activity',
                'type': 'Announce',
            },
            'published': '2019-04-27T00:00:00',
        }


class TestEntitiesPostReceive:
    @patch("federation.utils.activitypub.retrieve_and_parse_profile", autospec=True)
    @patch("federation.entities.activitypub.entities.handle_send", autospec=True)
    def test_follow_post_receive__sends_correct_accept_back(
            self, mock_send, mock_retrieve, activitypubfollow, profile
    ):
        mock_retrieve.return_value = profile
        activitypubfollow.post_receive()
        args, kwargs = mock_send.call_args_list[0]
        assert isinstance(args[0], ActivitypubAccept)
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

    def test_post__post_receive__cleans_linkified_tags(self, activitypubpost_linkified_tags):
        activitypubpost_linkified_tags.post_receive()
        assert activitypubpost_linkified_tags.raw_content == '<p>👁️foobar</p><p>barfoo!<br>#fanart #mastoart</p>'


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
