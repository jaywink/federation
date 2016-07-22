## [unreleased]

## Added
- `Relationship` base entity which represents relationships between two handles. Types can be following, sharing, ignoring and blocking. The Diaspora counterpart, `DiasporaRequest`, which represents a sharing/following request is outwards a single entity, but incoming a double entity, handled by creating both a sharing and following version of  the relationship.
- `Profile` base entity and Diaspora counterpart `DiasporaProfile`. Represents a user profile.
- `federation.utils.network.fetch_document` utility function to fetch a remote document. Returns document, status code and possible exception. Takes either `url` or a `host` + `path` combination. With `host`, https is first tried and optionally fall back to http.
- Utility methods to retrieve Diaspora user discovery related documents. These include the host-meta, webfinger and hCard documents. The utility methods are in `federation.utils.diaspora`.

## Changed
- Unlock most of the direct dependencies to a certain version range. Unlock all of test requirements to any version.
- Entities passed to `federation.controllers.handle_create_payload` are now converted from the base entity types (Post, Comment, Reaction, etc) to Diaspora entity types (DiasporaPost, DiasporaComment, DiasporaLike, etc). This ensures actual payload generation has the correct methods available (for example `to_xml`) whatever entity is passed in.

### Fixes
- Fix fetching sender handle from Diaspora protocol private messages. As it is not contained in the header, it needs to be read from the message content itself.

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
