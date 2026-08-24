# HKMA Open API mapping (sandbox)

This PoC maps **ideas** from the HKMA Open API Framework onto mock endpoints. It is **not** connected to a licensed bank, CDI, or production Open API portal.

Payloads are simplified JSON. They are not UK Open Banking or Berlin Group copies.

## Phases

| HKMA-shaped phase | Sandbox endpoint | Auth |
|-------------------|------------------|------|
| Phase 1 product information | `GET /open-api/v1/products` | Public |
| Phase 2 applications | `POST/GET /open-api/v1/applications` | Public (stub) |
| Phase 3 account information | `GET /open-api/v1/accounts/{customer_id}` | Bearer + `accounts.read` |
| Phase 3 transactions | `GET /open-api/v1/accounts/{customer_id}/transactions` | Bearer + `transactions.read` |
| Phase 4 payment initiation | `POST/GET /open-api/v1/payments` | Bearer + `payments.initiate` |

TPP convenience API (not a bank Open API phase): `GET /aggregate/{customer_id}` merges Phase 3-style accounts with FX.

## Consent / TPP

| Theme | What this repo shows |
|-------|----------------------|
| Customer consent | Bank-hosted `/oauth/authorize`, stored consent row, scoped JWT |
| TPP confidential client | `sandbox-tpp` secret used only on `/oauth/token` and `/tpp/oauth/exchange` |
| Revocation | `DELETE /consents/{id}` and `POST /oauth/revoke` → aggregate 403 |
| Customer match | Token `sub` must equal the requested customer id |

## Ops / operational resilience

[it-ops-monitor](https://github.com/turjoy18/it-ops-monitor) is the companion control plane. After sandbox `/health` and Phase 1 products exist, that service probes this API and opens incidents/tickets when it is down.

## Out of scope

- Live HKMA member-bank Open APIs or CDI connectivity
- FAPI, mTLS, PAR, JARM, or a production IdP
- Real payment rails, AML, or regulatory incident filing
- Kafka, Kubernetes, or a second ops UI

HS256 JWTs and in-process mocks are intentional so the demo runs without Docker or bank licenses.
