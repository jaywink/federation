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
