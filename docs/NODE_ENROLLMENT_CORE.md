# Javid Node Enrollment — Offline Core

The files in `src/javid_panel/nodes/enrollment.py` implement a **minimal standalone persistence primitive** for future secure node registration. This is not yet an API, a full daemon, an SSH installer or a VPN service.

## Implemented and unit-tested

- SQLite persistence for pending nodes and enrollment invites
- Cryptographically random one-time tokens; SHA-256 digest only at rest
- Short expiry with strict min/max TTL (60–1800 seconds)
- Single-use claim under SQLite `BEGIN IMMEDIATE` transactions (concurrent claims cannot all succeed)
- Separate revocation and validation of IPv4/IPv6 and FQDN names
- Restricted database-file permissions (0600 on POSIX)
- Basic fake-clock tests and concurrency tests

Run the offline tests:

```bash
python3 -m unittest discover -s tests -p 'test_node_enrollment.py' -v
```

## Security requirements **before** enabling this in production

1. Put all calls behind authenticated administrator service with RBAC and CSRF protection.
2. Require proof-of-possession for the node's private key, with TLS certificate verification and CA trust.
3. Integrate proper certificate issuance, rotation, revocation and agent identity lifecycle.
4. Add API endpoint rate limits, audit logs, request size limits, replay protection and deletion policy.
5. Never print token in an HTTP URL, shell arguments, query parameters, screenshots or logs. Deliver tokens once through a protected response.
6. Implement real Javid Node daemon and signed heartbeats with expiry to determine node health.
7. Run integration tests on **two isolated VPS** before asserting nodes function.
8. Store the SQLite database in a protected 0700 directory; arrange reliable backups and migrations.

No interface should show “connected” just because the `claim()` method returned; that only means a one-time enrollment record was consumed. **The fingerprint argument here is not verified key possession and cannot be trusted without the missing network-authentication layer.**

See [node UX blueprint](NODE_ENROLLMENT.md) and [feature matrix](FEATURES.md).
