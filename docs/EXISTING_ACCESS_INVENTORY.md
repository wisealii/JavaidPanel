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



## Embedded Gateway authorization map (source inspection, 2026-11-07)

Evidence: `installer/core.sh` embedded `Gateway.is_admin`, `Gateway.validate_origin`, `Gateway.dispatch`, `Nodes.admin`, `Nodes.route`, `Insights.route`, `DNSClients.api`, `DNSClients.public`, and `Features.route`. This is a **source-based route map**, not a VPS authorization test. The upstream VPN backend is still responsible for its own proxied routes.

| Existing path / handler | Current server-side access check | Notes |
| --- | --- | --- |
| `_alireza/session` | Reports `Gateway.is_admin` status | Session probe; not itself an authorization grant |
| `panel/content`, `panel/dns`, `dns/*` | `Gateway.is_admin` | Uses existing `vpn-ui` cookie checked against upstream `panel/admins/permissions`; DNS backend uses a gateway-owned service session |
| `panel/nodes`, `_alireza/nodes-ui`, `_alireza/nodes/*`, `_alireza/remote/*` | `Nodes.admin` | Calls origin validation and `Gateway.is_admin`; `Gateway.is_admin` accepts a successful upstream permissions response with a non-empty permissions list; this alone does **not** prove super-admin status or per-node delegated RBAC |
| `_alireza/insights/*` | `Nodes.admin` | Read/configure require existing admin session |
| `_alireza/features/*` | `Nodes.admin` | Includes TLS metadata and client policy management |
| `_alireza/dns-clients/*` | `Gateway.is_admin` | Managed DNS client and plan operations; retired path returns HTTP 410 |
| Public managed DNS and node subscription routes | Credential/token and route-specific checks | Intentionally not general admin-session endpoints; inspect token/IP/HTTPS validation separately |
| Other VPN backend paths | Forwarded to pinned upstream VPN service | **Not proven safe for new roles by Gateway alone**; upstream authorization and API semantics need separate audit |

The gateway also validates Origin / `Sec-Fetch-Site` for applicable requests. `Nodes.route` and managed DNS public routing are dispatched before the common origin check, with their own route-specific authentication. Do **not** remove or reorder these controls without regression tests.

**Important distinction:** embedded core `Nodes` already has a management surface using the Gateway session, whereas standalone `src/javid_panel/nodes/api.py` has its own bearer-token administrator and loopback dashboard. These are **two existing code paths**, not evidence that a new role system is needed. Do not merge, expose, or replace either until their responsibilities, deployment paths and compatibility are verified.

**Current RBAC conclusion:** source confirms a shared `Gateway.is_admin` check for the embedded management routes above, but **does not establish a super-admin-only requirement**: the check accepts a non-empty upstream permission list. `Nodes.admin` reports `Super-admin access required` on rejection, which is a message/authorization-contract mismatch until the upstream role semantics are tested. It does **not** confirm delegated server-manager or support permissions, nor does it prove that upstream VPN admin roles map safely to those operations. Do not grant those roles by simply forwarding the administrator cookie or node-control bearer. A future design should enumerate exact allowed operations and be approved before implementation.

## Safe next actions

1. Map gateway route handlers, login/session checks, existing users and administrative functions directly in `installer/core.sh`. Record route-by-route evidence before granting or restricting anything.
2. Map the embedded core node features against the standalone node API to avoid a duplicate management flow.
3. Draft a compatibility mapping from existing gateway identity to the standalone node-control permissions **without exposing the loopback dashboard publicly or copying the admin bearer to end-user clients**.
4. Review the mapping with the owner before implementing authorization changes. Keep the existing gateway and node dashboard intact until tested.
5. Run existing offline tests and CI for any later implementation. VPS, real VPN connectivity and restore remain unverified.

This inventory is intentionally conservative: unknown permissions are **unknown**, not assumed absent or safe.
