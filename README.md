# Hybrid Cloud Migration & Disaster-Recovery Lab

A portfolio project that simulates migrating a fictional company's legacy application from an on-premises environment into AWS through a staged hybrid architecture.

## Business scenario

Northstar Services runs a small internal CRM on a single on-premises server. The company has:
- a Python web/API application,
- a PostgreSQL database,
- locally stored operational data,
- no high availability,
- no formal monitoring,
- no tested disaster-recovery process.

The goal is to migrate the system to AWS with minimal downtime while documenting architectural decisions, tests, incidents, and recovery procedures.

## Project stages

1. Local legacy environment
2. Hybrid connectivity
3. Database migration to AWS
4. Application migration to AWS
5. Load balancing and private networking
6. Monitoring and alerting
7. Automated integration tests
8. Failure injection and troubleshooting
9. Backup/restore and DR testing
10. Architecture review, cost analysis, and lessons learned

## Stage 1: run locally

Requirements:
- Docker Desktop
- Python 3.11+ for local test execution

Start the environment:

```bash
docker compose up --build
```

Open:

- App: http://localhost:8080
- Health: http://localhost:8080/health
- DB health: http://localhost:8080/api/db-health
- Customers: http://localhost:8080/api/customers

Run tests in another terminal:

```bash
pip install -r requirements.txt
pytest -v
```

Stop:

```bash
docker compose down
```

Delete the local database volume and fully reset:

```bash
docker compose down -v
```

## What this stage proves

- Linux/container service operation
- web application and database networking
- ports and service discovery
- PostgreSQL connectivity
- health checks
- repeatable integration testing
- a realistic source environment for migration

## Security note

The credentials in docker-compose.yml are intentionally fake local-lab credentials. Do not reuse this pattern for AWS. Later stages move secrets into AWS Secrets Manager / Systems Manager Parameter Store.
