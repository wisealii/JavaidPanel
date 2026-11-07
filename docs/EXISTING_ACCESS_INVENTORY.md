# Existing capability and access inventory (source audit)

**Baseline:** main at `0d23d7458801d1b984d5d660ad0491cefed125ce` / `1.1.113-dev` (2026-11-07). **Scope:** documentation only; no engine, gateway, database, UI or access behavior changed. Source evidence does not establish live VPS readiness.

## Capability categories (existing code only)

| Category | Existing implementation / evidence | Access boundary known from source |
| --- | --- | --- |
| Install, SSL, admin account, VPN/DNS core, gateway | `install.sh`, `installer/core.sh`; see `docs/CURRENT_FEATURES.json` | Embedded gateway admin/session implementation; verify effective routes before changing authorization |
| Gateway navigation and monitoring | Embedded `Gateway`, `insights.py`, `dns_clients.py` in `installer/core.sh` | Main gateway session; precise per-route role matrix not yet verified |
| Core node management | Embedded `nodes.py` in `installer/core.sh` | Main gateway; distinct from standalone Javid Node |
| Maintenance, backup and repair | `installer/core.sh`, generated CLI | Privileged local administration; no confirmed full restore test |
| Standalone Javid Node control | `src/javid_panel/nodes/api.py`, `runtime.py` | Separate admin bearer token and signed node heartbeats; **not integrated** with gateway login |
| Standalone node dashboard | `src/javid_panel/nodes/dashboard.html`, `dashboard.js`, `dashboard.css` | Loopback-only static UI via SSH tunnel; management API separately requires bearer token |
| Existing feature/release audit | `docs/CURRENT_FEATURES.json`, `docs/CURRENT_FEATURES_AUDIT.md`, release tools | Developer documentation, not a live capability guarantee |

The current catalog does **not** establish working Google login, commercial subscriptions, purchase validation or a cross-platform Javaid VPN client. Do not claim these exist or add substitutes without source verification and owner approval.

## Verified standalone node API permission matrix

Evidence: `src/javid_panel/nodes/api.py` (`make_handler`, `require_admin`, `authenticated`, `serve_admin_dashboard`).

| Route | Admin bearer | Node enrollment secret / signature | Anonymous | Notes |
| --- | --- | --- | --- | --- |
| `GET /healthz` | Not required | Not required | Allowed | Service liveness only |
| `GET /admin/nodes` and whitelisted assets | Not required for static files | Not required | Loopback + Host restricted | UI files alone do not authorize API calls |
| `GET /api/v1/nodes` | Required | No | Denied | Returns node list |
| `POST /api/v1/nodes/enrollments` | Required | No | Denied | Creates invitation |
| `POST /api/v1/nodes/{id}/revoke` | Required | No | Denied | Revokes node |
| `POST /api/v1/nodes/claim` | No | Enrollment ID + one-time token | Endpoint reachable | Credential validated by registry; per-IP attempt limiter |
| `POST /api/v1/nodes/{id}/heartbeat` | No | Signed heartbeat | Endpoint reachable | Registry validates signature, counter and timestamp |

**Current role matrix (confirmed only for standalone node service):**

| Role | List/create/revoke node | Claim node | Heartbeat |
| --- | --- | --- | --- |
| Holder of standalone admin bearer | Yes | Only with enrollment credential | Only with valid node credential |
| Node agent | No | With valid enrollment credential | With valid node credential |
| Gateway administrator | **Not automatically authorized** | No inherited privilege | No inherited privilege |
| Server operator / support / end user | **No distinct RBAC roles implemented here** | No inherited privilege | No inherited privilege |

Do not interpret the single admin bearer as a fully implemented multi-role permission system. The gateway may have different identity/session handling; review its generated route handlers before defining any shared RBAC contract.

## Safe next actions

1. Map gateway route handlers, login/session checks, existing users and administrative functions directly in `installer/core.sh`. Record route-by-route evidence before granting or restricting anything.
2. Map the embedded core node features against the standalone node API to avoid a duplicate management flow.
3. Draft a compatibility mapping from existing gateway identity to the standalone node-control permissions **without exposing the loopback dashboard publicly or copying the admin bearer to end-user clients**.
4. Review the mapping with the owner before implementing authorization changes. Keep the existing gateway and node dashboard intact until tested.
5. Run existing offline tests and CI for any later implementation. VPS, real VPN connectivity and restore remain unverified.

This inventory is intentionally conservative: unknown permissions are **unknown**, not assumed absent or safe.
