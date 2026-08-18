# Canonical development bundle

`canonical/` is the only bundle source root. `source.toml` is the reviewed
developer declaration; `manifest.json` and `manifest.lock.json` are generated
outputs and must never be edited by hand. The current version is deliberately a
development version and carries no release or compatibility promise.

The content digest is SHA-256 over newline-delimited canonical JSON records,
sorted by canonical source path. Each record binds path, file type, mode and
content SHA-256. Inputs are `manifest.schema.json`, the generated
`manifest.json`, and every declared payload file. The lock is excluded from its
own digest by this rule, then binds the complete ordered input records.

An incompatible manifest shape increments `schema_version`. A development
bundle content change regenerates the manifest and lock without implying a
release. Release versioning and compatibility policy belong to a later
milestone.

The bootstrap installer has no production or user-home mode. Installation
requires an explicit existing system-temporary root and an explicit existing
target beneath it. The installed read-only `verify` and `version` surfaces are
foundation contracts, not a production doctor.
