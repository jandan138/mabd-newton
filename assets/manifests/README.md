# Asset Manifests

Phase 6 introduces `paper_asset_sources.yaml` as the machine-checkable asset
source index referenced by the experiment matrix. It records source type, source
URI, license status, checksum status, reconstruction status, and whether the
asset can support full paper evidence.

Raw paper assets are not committed unless their license and size are acceptable.
Procedural entries use `not_applicable_procedural` checksums until a generator
emits concrete assets under a dated record.
