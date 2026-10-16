# ADR-001: Local legacy application stack

## Status
Accepted

## Context
The project needs a realistic but small "on-premises" system that can later be connected to and migrated into AWS.

## Options considered
1. Static website only
2. Python application + SQLite
3. Python application + PostgreSQL in Docker
4. Multi-VM environment

## Decision
Use a Python Flask API and PostgreSQL, orchestrated with Docker Compose.

## Rationale
- A real client/server database creates meaningful networking and authentication failure modes.
- Docker makes the environment reproducible.
- PostgreSQL maps naturally to a later migration to Amazon RDS for PostgreSQL.
- Flask keeps application complexity low so the project remains architecture-focused.

## Trade-offs
- Docker is simpler than a traditional physical on-prem estate.
- It does not perfectly emulate enterprise networking.
- The project will later add VM/network boundaries where necessary to make hybrid connectivity meaningful.
