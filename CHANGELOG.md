## 1.1.104-dev — public repository documentation refresh

- Publish an independent JavaidPanel README and a static interactive UI demo, explicitly labeled as mock data.
- Add structured documentation for features, nodes, future secure node enrollment, SSL, architecture, troubleshooting, development and roadmap.
- Expand protocol/tunnel status definitions and add GitHub issue/PR templates.
- Remove comparison-project marketing references from user-facing documentation while retaining required open-source provenance and license notices.
- State clearly that the Docker Compose file is currently not deployable (missing Dockerfile and Nginx configuration).
- **No new runtime service, tested VPS install, or functioning node enrollment is claimed in this documentation update.**

## 1.1.104-dev — deployment follow-up
- Add offline tests simulating a piped `curl | bash` bootstrap with a correct engine and a tampered engine.
- Clarify remote one-command options for SSL, health checks and base node activation when the repository is not cloned.
- Distinguish legacy node support from unfinished Javid Node agent.

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
