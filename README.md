# NGX Advisory API Engine

An independent, self-hosted, and lightweight FastAPI backend service built to orchestrate, log, and serve financial advisory reports and buy signals for the Nigerian Exchange (NGX). 

This service acts as a decoupled data layer:
* **n8n Automation Pipelines** securely ingest and upsert daily engine runs using an internal token.
* **Public Consumers (e.g., Zod / NGX Pulse)** consume optimized read-only data endpoints via cryptographic API keys.

---

## 🏗️ Architecture Overview

Unlike monolithic setups, this engine is deployed completely standalone to maximize reliability and portability:
* **Application Framework:** FastAPI (Python 3.11-slim)
* **Database Layer:** Local SQLite (`ngx_advisory.db`) mapped to a persistent Docker named volume (`ngx_data`), isolating it completely from external heavy database instances.
* **Proxy Routing:** Integrates directly into an external `caddy_net` Docker bridge network, staying hidden from public ports while exposing cleanly via Caddy subdomains.

```text
  [ n8n Pipelines ] ──( Internal Write Token )──► │  Caddy Proxy  │
                                                   │ (caddy_net)  │
  [ Zod Frontend  ] ──( Secure Client API Key)──► │       │      │
                                                          ▼
                                                [ ngx_api_engine ]
                                                          │
                                                (Persistent Volume)
                                                          ▼
                                                [ SQLite Database ]


```
## 📁 Repsitory Directory Structure

```text
ngx-advisory/
├── docker-compose.yml
├── .env.example
├── README.md
├── app/
│   ├── Dockerfile             <-- Added here
│   ├── main.py
│   └── ngx_advisory_router.py
├── database/
│   └── ngx_advisory_schema.py
└── scripts/
    └── generate_api_key.py
```
