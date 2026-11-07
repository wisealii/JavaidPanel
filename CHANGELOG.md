## 1.1.110-dev — existing-features audit and explicit install access mode
- Inventory existing integrated core, embedded modules, standalone Javid Node/API and maintenance tools with source evidence; no new protocols or speculative features.
- Block unattended first install without an explicit access mode: no implicit self-signed HTTPS fallback when there is no controlling TTY.
- Add regression coverage for the noninteractive safety guard and repeatable source-inventory checks.
- Clarify that the standalone Javid Node service is **not installed** by the current one-command main installer.
- Live VPS, admin login, Let's Encrypt, protocol connectivity and restore remain unverified.

## 1.1.109-dev — priority gates and safer certificate preflight
- Treat missing A/AAAA DNS as a hard SSL preflight error (previously warned and continued).
- Support IPv6-only DNS in the guided preflight and reject unavailable socket inspection instead of incorrectly assuming TCP 80 is unused.
- Add regression tests for IPv4, IPv6-only, absent DNS, occupied TCP 80, and failed socket inspection.
- Document prioritized P0/P1/P2/P3 dependency roadmap and explicit acceptance gates.
- Does not configure webserver TLS or claim a live ACME issuance; no VPS install test yet.

## 1.1.108-dev — remove misleading production compose
- Remove the root Docker Compose file that could not build because Dockerfile and Nginx configuration were missing.
- Archive the old design as a clearly non-executable reference under docs/EXPERIMENTAL_COMPOSE.md.
- Keep the only documented installation path as the pinned installer until VPS acceptance tests are available.
- Update regression tests and release status; this does **not** confer production readiness.

## 1.1.108-dev — readiness audit before VPS release
- Synchronize VERSION with install.sh bootstrap metadata (previously drifted).
- Add executable read-only readiness audit with JSON/strict modes and explicit live-VPS, SSL, node, protocol, restore and Gateway blockers.
- Detect incomplete production Docker Compose inputs instead of labeling the setup ready.
- Add CI tests for version drift, SHA-256, false readiness claims, and machine-readable output.
- **No real VPS has been provisioned or tested; production readiness remains blocked.**

## 1.1.107-dev — Controller upgrade safeguards
- Introduce dedicated safe source-upgrade command for Javid Node Controller.
- Verify installed config, source completeness, Python syntax, service unit and pre-upgrade loopback health.
- Stage new source, retain old code under unique backup, restart and check health, and attempt automatic rollback on restart/health failure.
- Do not modify node credentials, database, TLS/SSL, API routes or the panel Gateway.
- Add isolated unit tests for successful upgrade, rollback, unsafe permissions, missing sources and unhealthy old service.
- Public Gateway admin identity integration **still requires real auth contracts and migration review**, and live VPS upgrade tests remain pending.

## 1.1.106-dev — Private Javid Node management dashboard

- Add a real RTL node-admin dashboard served by the existing control API on loopback only, intended for SSH port forwarding.
- Connect UI to authenticated JSON API for node creation, install-command generation, single-display invitation token, heartbeat status and revocation.
- Add static-asset whitelist, loopback + Host checks, restrictive Content Security Policy, no-store caching and DOM textContent rendering for untrusted node names.
- Install dashboard assets alongside node-control API and add dedicated live HTTP integration tests.
- Do not expose management dashboard through the public HTTPS reverse proxy. No VPN tunnel is installed and the dashboard is not integrated with the legacy gateway.

## 1.1.105-dev — Experimental Javid Node API and SSL assistant
- Added standalone JSON node-control API with one-time enrollment, node credentials, signed heartbeats, revocation and stale-state monitoring.
- Added systemd installer for local-only control service and Javid Node health agent; no VPN tunnel is deployed.
- Added local node-management CLI generating a per-node one-command installer without putting the secret token in shell args.
- Added step-by-step interactive Let's Encrypt wizard; certificate issuance is separate from HTTPS webserver deployment.
- Added isolated API and SSL regression suites, including replay rejection, revocation, expiry, admin authorization and heartbeat transitions.
- **Not yet integrated into the main UI/Gateway; real VPS SSL/mTLS/node-tunnel testing still required.**

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
