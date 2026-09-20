# SlaySeason Market Agent

An enterprise-grade, cloud-native LangGraph/Streamlit AI agent designed to execute precise marketing intelligence queries via a secure PostgreSQL data warehouse.

## Architecture & Core Principles

- **Strict Answer Contract:** To eliminate large language model (LLM) hallucinations on financial and operational metrics, the agent never performs raw math or arithmetic in the prompt layer. Instead, it extracts user intent, invokes parameterized SQL tools, and queries the canonical database directly.
- **Multi-Tenant Isolation:** All database tables enforce explicit row-level filtering via `tenant_id`, ensuring secure data partitioning between sandbox environments and production client stores.
- **Cloud-Native Storage:** Built to run seamlessly on serverless PostgreSQL providers (such as Neon) and containerized workflows (GitHub Codespaces / Docker) with full IPv4 support.

---

## Tech Stack

* **Orchestration:** LangGraph, LangChain
* **Frontend UI:** Streamlit
* **Database & ORM:** PostgreSQL (Neon), Psycopg
* **Environment Management:** Python-Dotenv

---

## Local Development & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/ashandilgith/slayseason_market-agent.git](https://github.com/ashandilgith/slayseason_market-agent.git)
cd slayseason_market-agent
