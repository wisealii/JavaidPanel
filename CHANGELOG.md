## 1.1.104-dev — 2026-11-06
- Fix early installer checks: require a running systemd instance, supported resources and core dependencies before network download.
- Refuse repair/SSL/node maintenance when the corresponding installed service files are absent.
- Correct misleading root error instruction, reject unexpected CLI arguments, and safely probe an interactive terminal before redirecting stdin.
- Add automated regression tests for flags, offline preflight, checksum and installer self-test.
- This is a bootstrap reliability update only; live VPS installation and node connectivity remain unverified.

# JavaidPanel Changelog

## 1.1.103-dev — 2026-11-06
- Added genuine one-command installation bootstrap.
- Restored the legacy AlirezaPanel integration engine as pinned, checksummed source `installer/core.sh`, rather than using a placeholder container.
- Bootstrap checks OS, architecture, systemd, existing installations and executable SHA before running the engine.
- Supports `--self-test`, `--doctor`, `--check`, `--ssl`, `--repair`, `--enable-nodes` operations.
- Added GPLv3 license and upstream source provenance.
- Updated docs to distinguish legacy working installation logic from unfinished Javid-specific node/business modules.
- **Real VPS installation, SSL issuance and node connectivity are not yet verified.**

## 1.1.102-dev — 2026-11-06
- Disabled misleading placeholder installer and node agent pending a tested runtime.
- Added guarded preflight and TLS helper.
