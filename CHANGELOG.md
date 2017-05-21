# Changelog

## [unreleased]

### Backwards incompatible changes
* Removed exception class `NoHeaderInMessageError`. New style Diaspora protocol does not have a custom header in the Salmon magic envelope and thus there is no need to raise this anywhere.

### Added
* New style Diaspora public payloads are now supported (see [here](https://github.com/diaspora/diaspora_federation/issues/30)). Old style payloads are still supported. Payloads are also still sent out old style.
* Add new `Follow` base entity and support for the new Diaspora "contact" payload. The simple `Follow` maps to Diaspora contact entity with following/sharing both true or false. Sharing as a separate concept is not currently supported.
* Added `_receiving_guid` to all entities. This is filled with `user.guid` if `user` is passed to `federation.inbound.handle_receive` and it has a `guid`. Normally in for example Diaspora, this will always be done in private payloads.

### Fixed
* Legacy Diaspora retraction of sharing/following is now supported correctly. The end result is a `DiasporaRetraction` for entity type `Profile`. Since the payload doesn't contain the receiving user for a sharing/following retraction in legacy Diaspora protocol, we store the guid of the user in the entity as `_receiving_guid`, assuming it was passed in for processing.


## [0.11.0] - 2017-05-08

### Backwards incompatible changes

Diaspora protocol support added for `comment` and `like` relayable types. On inbound payloads the signature included in the payload will be verified against the sender public key. A failed verification will raise `SignatureVerificationError`. For outbound entities, the author private key will be used to add a signature to the payload.

This introduces some backwards incompatible changes to the way entities are processed. Diaspora entity mappers `get_outbound_entity` and entity utilities `get_full_xml_representation` now requires the author `private_key` as a parameter. This is required to sign outgoing `Comment` and `Reaction` (like) entities. 

Additionally, Diaspora entity mappers `message_to_objects` and `element_to_objects` now take an optional `sender_key_fetcher` parameter. This must be a function that when called with the sender handle will return the sender public key. This allows using locally cached public keys instead of fetching them as needed. NOTE! If the function is not given, each processed payload will fetch the public key over the network. 

A failed payload signature verification now raises a `SignatureVerificationError` instead of a less specific `AssertionError`.

### Added
* Three new attributes added to entities.
    * Add protocol name to all entities to attribute `_source_protocol`. This might be useful for applications to know which protocol payload the entity was created from once multiple protocols are implemented.
    * Add source payload object to the entity at `_source_object` when processing it.
    * Add sender public key to the entity at `_sender_key`, but only if it was used for validating signatures.
* Add support for the new Diaspora payload properties coming in the next protocol version. Old XML payloads are and will be still supported.
* `DiasporaComment` and `DiasporaLike` will get the order of elements in the XML payload as a list in `xml_tags`. For implementers who want to recreate payloads for these relayables, this list should be saved for later use.
* High level `federation.outbound.handle_send` helper function now allows sending entities to a list of recipients without having to deal with payload creation or caring about the protocol (in preparation of being a multi-protocol library).
    * The function takes three parameters, `entity` that will be sent, `from_user` that is sending (note, not necessarely authoring, this user will be used to sign the payload for Diaspora for example) and a list of recipients as tuples of recipient handle/domain and optionally protocol. In the future, if protocol is not given, it will be guessed from the recipient handle, and if necessary a network lookup will be made to see what protocols the receiving identity supports.
    * Payloads will be delivered to each receiver only once. Currently only public messages are supported through this helper, so multiple recipients on a single domain will cause only one delivery.

### Changed
* Refactor processing of Diaspora payload XML into entities. Diaspora protocol is dropping the `<XML><post></post></XML>` wrapper for the payloads. Payloads with the wrapper will still be parsed as before.

## [0.10.1] - 2017-03-09

### Fixes
* Ensure tags are lower cased after collecting them from entity `raw_content`. 

## [0.10.0] - 2017-01-28

### Added
* Add support for new Diaspora protocol ISO 8601 timestamp format introduced in protocol version 0.1.6.
* Tests are now executed also against Python 3.6.

### Fixes
* Don't crash `federation.utils.diaspora.retrieve_diaspora_webfinger` if XRD parse raises an `xml.parsers.expat.ExpatError`.

## [0.9.1] - 2016-12-10

### Fixes
* Made `Profile.raw_content` optional. This fixes validating profiles parsed from Diaspora hCard's.

## [0.9.0] - 2016-12-10

### Backwards incompatible changes
* `Image` no longer has a `text` attribute. It is replaced by `raw_content`, the same attribute as `Post` and `Comment` have. Unlike the latter two, `Image.raw_content` is not mandatory.

### Added
* Entities can now have a children. These can be accessed using the `_children` list. Acceptable children depends on the entity. Currently, `Post`, `Comment` and `Profile` can have children of entity type `Image`. Child types are validated in the `.validate()` entity method call.

### Fixed
* Diaspora protocol `message_to_objects` method (called through inbound high level methods) now correctly parses Diaspora `<photo>` elements and creates `Image` entities from them. If they are children of status messages, they will be available through the `Post._children` list.

## [0.8.2] - 2016-10-23

### Fixed
* Remove legacy splitting of payload to 60 chars when creating Diaspora payloads. Diaspora 0.6 doesn't understand these any more.


## [0.8.1] - 2016-10-18

### Fixed
* `federation.utils.network.send_document` incorrectly passed in `kwargs` to `requests.post`, causing an error when sending custom headers.
* Make sure `federation.utils.network.send_document` headers are treated case insensitive before passing then onwards to `requests.post`.

## [0.8.0] - 2016-10-09

### Library is now called `federation`

The name Social-Federation was really only an early project name which stuck. Since the beginning, the main module has been `federation`. It makes sense to unify these and also shorter names are generally nicer.

#### What do you need to do? 

Mostly nothing since the module was already called `federation`. Some things to note below:

* Update your requirements with the new library name `federation`.
* If you hook to the old logger `social-federation`, update those to listen to `federation`, which is now the standard logger name used throughout.

### Other backwards incompatible changes
* `federation.utils.diaspora.retrieve_and_parse_profile` will now return `None` if the `Profile` retrieved doesn't validate. This will affect also the output of `federation.fetchers.retrieve_remote_profile` which is the high level function to retrieve profiles.
* Remove unnecessary `protocol` parameter from `federation.fetchers.retrieve_remote_profile`. We're miles away from including other protocols and ideally the caller shouldn't have to pass in the protocol anyway.

### Added
* Added `Retraction` entity with `DiasporaRetraction` counterpart.

## [0.7.0] - 2016-09-15

### Backwards incompatible changes
* Made `guid` mandatory for `Profile` entity. Library users should always be able to get a full validated object as we consider `guid` a core attribute of a profile.
* Always validate entities created through `federation.entities.diaspora.mappers.message_to_objects`. This is the code that transforms federation messages for the Diaspora protocol to actual entity objects. Previously no validation was done and callers of `federation.inbound.handle_receive` received entities that were not always valid, for example they were missing a `guid`. Now validation is done in the conversion stage and errors are pushed to the `federation` logger in the event of invalid messages.
    * Note Diaspora Profile XML messages do not provide a GUID. This is handled internally by fetching the guid from the remote hCard so that a valid `Profile` entity can be created.

### Added
* Raise a warning if unknown parameters are passed to entities.
* Ensure entity required attributes are validated for `None` or empty string values. Required attributes must not only exist but also have a value.
* Add validation to entities with the attribute `public`. Only `bool` values are accepted.

### Changed
* Function `federation.utils.diaspora.parse_profile_from_hcard` now requires a second argument, `handle`. Since in the future Diaspora hCard is not guaranteed to have username and domain, we now pass handle to the parser directly.

## [0.6.1] - 2016-09-14

### Fixed
* New style Diaspora Magic Envelope didn't require or like payload data to be cut to 60 char lines, as the legacy protocol does. Fixed to not cut lines.

## [0.6.0] - 2016-09-13

### Added
* New style Diaspora Magic Envelope support. The magic envelope can be created using the class `federation.protocols.diaspora.magic_envelope.MagicEnvelope`. By default this will not wrap the payload message in `<XML><post></post></XML>`. To provide that functionality the class should be initialized with `wrap_payload=True`. No changes are made to the protocol send methods yet, if you need this new magic envelope you can initialize and render it directly.

### Changed
* Deprecate receiving user `key` attribute for Diaspora protocol. Instead correct attribute is now `private_key` for any user passed to `federation.inbound.handle_receive`. We already use `private_key` in the message creation code so this is just to unify the user related required attributes.
   * DEPRECATION: There is a fallback with `key` for user objects in the receiving payload part of the Diaspora protocol until 0.8.0.
   
### Fixes
* Loosen up hCard selectors when parsing profile from hCard document in `federation.utils.diaspora.parse_profile_from_hcard`. The selectors now match Diaspora upcoming federation documentation.

## [0.5.0] - 2016-09-05

### Breaking changes
- `federation.outbound.handle_create_payload` parameter `to_user` is now optional. Public posts don't need a recipient. This also affects Diaspora protocol `build_send` method where the change is reflected similarly. [#43](https://github.com/jaywink/federation/pull/43)
     - In practise this means the signature has changed for `handle_create_payload` and `build_send` from **`from_user, to_user, entity`** to **`entity, from_user, to_user=None`**.
     
### Added
- `Post.provider_display_name` is now supported in the entity outbound/inbound mappers. [#44](https://github.com/jaywink/federation/pull/44)
- Add utility method `federation.utils.network.send_document` which is just a wrapper around `requests.post`. User agent will be added to the headers and exceptions will be silently captured and returned instead. [#45](https://github.com/jaywink/federation/pull/45)
- Add Diaspora entity utility `federation.entities.diaspora.utils.get_full_xml_representation`. Renders the entity XML document and wraps it in `<XML><post>...</post></XML>`. [#46](https://github.com/jaywink/federation/pull/46)

## [0.4.1] - 2016-09-04

### Fixes

- Don't quote/encode `Protocol.build_send` payload. It was doing it wrongly in the first place and also it's not necessary since Diaspora 0.6 protocol changes. [#41](https://github.com/jaywink/federation/pull/41)
- Fix identification of Diaspora protocol messages. This was not working in the case that the attributes in the tag were in different order. [#41](https://github.com/jaywink/federation/pull/41)


## [0.4.0] - 2016-07-24

### Breaking changes
- While in early stages, doing some renaming of modules to suit the longer term. `federation.controllers` has been split into two, `federation.outbound` and `federation.inbound`. The following methods have new import locations:
   * `federation.controllers.handle_receive` -> `federation.inbound.handle_receive`
   * `federation.controllers.handle_create_payload` -> `federation.outbound.handle_create_payload`
- Class `federation.hostmeta.generators.DiasporaHCard` now requires `guid`, `public_key` and `username` for initialization. Leaving these out was a mistake in the initial implementation. Diaspora has these in at least 0.6 development branch.

### Added
- `Relationship` base entity which represents relationships between two handles. Types can be following, sharing, ignoring and blocking. The Diaspora counterpart, `DiasporaRequest`, which represents a sharing/following request is outwards a single entity, but incoming a double entity, handled by creating both a sharing and following version of  the relationship.
- `Profile` base entity and Diaspora counterpart `DiasporaProfile`. Represents a user profile.
- `federation.utils.network.fetch_document` utility function to fetch a remote document. Returns document, status code and possible exception. Takes either `url` or a `host` + `path` combination. With `host`, https is first tried and optionally fall back to http.
- Utility methods to retrieve Diaspora user discovery related documents. These include the host-meta, webfinger and hCard documents. The utility methods are in `federation.utils.diaspora`.
- Utility to fetch remote profile, `federation.fetchers.retrieve_remote_profile`. Currently always uses Diaspora protocol. Returns a `Profile` entity.

### Changed
- Unlock most of the direct dependencies to a certain version range. Unlock all of test requirements to any version.
- Entities passed to `federation.controllers.handle_create_payload` are now converted from the base entity types (Post, Comment, Reaction, etc) to Diaspora entity types (DiasporaPost, DiasporaComment, DiasporaLike, etc). This ensures actual payload generation has the correct methods available (for example `to_xml`) whatever entity is passed in.

### Fixes
- Fix fetching sender handle from Diaspora protocol private messages. As it is not contained in the header, it needs to be read from the message content itself.
- Fix various issues with `DiasporaHCard` template after comparing to some real world hCard templates from real pods. Old version was based on documentation in Diaspora project wiki.

## [0.3.2] - 2016-05-09

### Changed
- Test factories and other test files are now included in the package installation. Factories can be useful when creating project tests.
- Bump allowed `lxml` to 3.6.0
- Bump allowed `python-dateutil` to 2.5.3

### Fixes
- Don't raise on Post.tags if Post.raw_content is None

## [0.3.1] - 2016-04-13

### Added
- Support for generating `.well-known/nodeinfo` document, which was forgotten from the 0.3.0 release. Method `federation.hostmeta.generators.get_nodeinfo_well_known_document` does this task. It requires an `url` which should be the full base url of the host. Optionally `document_path` can be specified, but it is optional and defaults to the one in the NodeInfo spec.

## [0.3.0] - 2016-04-13

### Added
- Support for generating [NodeInfo](http://nodeinfo.diaspora.software) documents using the generator `federation.hostmeta.generators.NodeInfo`. Strict validation is skipped by default, but can be enabled by passing in `raise_on_validate` to the `NodeInfo` class. By default a warning will be generated on documents that don't conform with the strict NodeInfo values. This can be disabled by passing in `skip_validate` to the class.

## [0.2.0] - 2016-04-09

### Backwards incompatible changes
- Any implementations using the Diaspora protocol and `Post` entities must now use `DiasporaPost` instead. See "Changed" below.

### Added
- Support for using `validate_field()` methods for entity fields and checking missing fields against `_required`. To use this validation, `validate()` must specifically be called for the entity instance.
- Base entities `Comment` and `Reaction` which subclass the new `ParticipationMixin`.
- Diaspora entity `DiasporaComment`, a variant of `Comment`.
- Diaspora entity `DiasporaLike`, a variant of `Reaction` with the `reaction = "like"` default.

### Changed
- Refactored Diaspora XML generators into the Diaspora entities themselves. This introduces Diaspora versions of the base entities called `DiasporaPost`, `DiasporaComment` and `DiasporaLike`. **Any implementations using the Diaspora protocol and `Post` entities must now use `DiasporaPost` instead.**

### Fixes
- Entities which don't specifically get passed a `created_at` now get correct current time in `created_at` instead of always having the time part as `00:00`.

## [0.1.1] - 2016-04-03

### Initial package release

Supports well Post type object receiving over Diaspora protocol.

Untested support for crafting outgoing protocol messages.
