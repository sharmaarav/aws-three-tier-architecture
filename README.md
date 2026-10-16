
Northstar is a hands-on AWS infrastructure project built to demonstrate secure network design, private application deployment, database integration, load balancing, troubleshooting, and recovery testing.

The application runs behind an internet-facing Application Load Balancer, uses a private EC2 application tier, and connects to a private Amazon RDS PostgreSQL database over SSL.

## Repository layout

```text
app/                  Flask application and templates
db/init.sql           PostgreSQL schema and sample customers
tests/                Checks against a running stack
docs/adr/             Architecture decision records
docs/incidents/       Incident write-up template
deploy/               Offline EC2 bundle (northstar-app.zip); not source
Dockerfile            Application image
docker-compose.yml    Local Flask and PostgreSQL stack
requirements.txt      Runtime dependencies
requirements-dev.txt  Test dependencies
```

Local stack:

```bash
docker compose up --build
pip install -r requirements-dev.txt
pytest
```

The Compose file publishes the app on port 8080. Tests use `BASE_URL` (default `http://localhost:8080`).

## Architecture

<img width="1672" height="941" alt="Northstar AWS Three-Tier Architecture (1)" src="https://github.com/user-attachments/assets/f3f7765d-0d6e-4688-ae00-324d37ee8467" />

Core request path:

```text
Internet
  |
  v
Application Load Balancer
  |
  v
Private EC2 instance
Flask + Gunicorn
  |
  v
Private RDS PostgreSQL
```

Supporting services include Amazon S3, an S3 Gateway VPC Endpoint, EC2 Instance Connect Endpoint, IAM, an Internet Gateway, route tables, and security groups.

## Design Goals

The project was designed around four requirements:

- Keep the application and database tiers private
- Expose the service only through a load balancer
- Restrict traffic between tiers using security group references
- Make failures diagnosable by separating DNS, network, authentication, and application checks

## Network Design

The environment uses a custom VPC:

```text
10.0.0.0/16
```

with separate subnet groups for each tier:

```text
Public:
10.0.1.0/24
10.0.2.0/24

Application:
10.0.11.0/24
10.0.12.0/24

Database:
10.0.21.0/24
10.0.22.0/24
```

The Application Load Balancer spans the two public subnets.

The EC2 application instance runs in a private application subnet with no public IPv4 address.

The RDS instance runs in a private database subnet group and is not publicly accessible.

## Security Model

Traffic is controlled with security group references rather than broad CIDR access.

```text
Internet
  |
  v
northstar-alb-sg
HTTP 80 from 0.0.0.0/0

ALB
  |
  v
northstar-app-sg
TCP 5000 only from northstar-alb-sg

EC2
  |
  v
northstar-db-sg
PostgreSQL 5432 only from northstar-app-sg
```

This design prevents direct internet access to the EC2 and RDS tiers.

## Private EC2 Access

The EC2 instance was launched without a public IP.

Administrative access was provided through an EC2 Instance Connect Endpoint, allowing the instance to remain private while still supporting browser-based SSH access.

## Private Deployment from S3

The application deployment package was stored in a private S3 bucket.

An S3 Gateway VPC Endpoint was associated with the application route table so the EC2 instance could retrieve the deployment package without requiring general outbound internet access.

## Application Stack

The application uses:

- Python
- Flask
- Gunicorn
- PostgreSQL
- psycopg2

Two health endpoints were used during validation:

```text
/health
/api/db-health
```

Expected responses:

```json
{"status":"ok"}
```

```json
{"database":"reachable","result":1}
```

## Database Integration

The application connects to Amazon RDS PostgreSQL using:

- Private DNS resolution
- TCP 5432
- SSL
- Environment variables for connection configuration
- Security group references between the app and database tiers

A test customer table was created and populated with sample records to confirm read and write access.

Example query output:

```text
(1, 'Alice Morgan', 'alice@example.com')
(2, 'Ben Carter', 'ben@example.com')
(3, 'Charlie Singh', 'charlie@example.com')
```

## Load Balancing and Health Checks

The Application Load Balancer uses:

```text
Listener: HTTP 80
Target protocol: HTTP
Target port: 5000
Health check path: /health
```

The EC2 instance registered as healthy and the application was successfully accessed through the ALB DNS endpoint.

End-to-end validation confirmed both application health and database connectivity through the public entry point.

## Failure Testing

### Application Process Failure

Gunicorn was deliberately stopped on the EC2 instance.

Observed behaviour:

- The ALB target changed from Healthy to Unhealthy
- Health checks failed
- Public requests returned a gateway error
- Restarting Gunicorn restored the target to Healthy

This confirmed that ALB health checks could detect an unavailable backend process.

### Database Network Failure

The PostgreSQL inbound rule was temporarily removed from the database security group.

Observed behaviour:

- `/health` remained available
- `/api/db-health` failed
- RDS DNS resolution still worked
- TCP 5432 timed out
- Restoring the security group rule recovered database connectivity

This separated an application availability issue from a downstream database network issue and demonstrated layer-by-layer troubleshooting.

## Disaster Recovery

A manual RDS snapshot was created as a recovery baseline.

The recovery approach was designed around restoring the snapshot to a new RDS instance and validating the recovered data before switching application connectivity.

```text
RDS snapshot
    |
    v
Restore new RDS instance
    |
    v
Validate recovered data
```

This provides a practical basis for RTO and RPO discussions and highlights the difference between backup availability and full service recovery.

## Key Technical Lessons

- Security group references provide tighter tier-to-tier controls than broad network ranges.
- Private EC2 instances can access AWS services without public internet access through VPC endpoints.
- ALB health checks detect backend process failures but do not remove the need for multiple application instances.
- DNS, TCP connectivity, authentication, and application behaviour should be tested separately during troubleshooting.
- A single EC2 backend remains a single point of failure even when it sits behind an ALB.
- Snapshot-based recovery protects data, but production resilience would require stronger availability and failover design.

## Production Improvements

The next production-focused improvements would be:

- Auto Scaling Group across multiple Availability Zones
- At least two EC2 application instances
- Multi-AZ RDS
- HTTPS with AWS Certificate Manager
- AWS Secrets Manager for credentials
- CloudWatch alarms and centralized logging
- Infrastructure as Code with Terraform or CloudFormation
- CI/CD pipeline
- Automated backup and restore testing

## Outcome

The final architecture successfully demonstrated:

- A segmented three-tier VPC
- Public-only access through an ALB
- Private EC2 and RDS tiers
- Secure communication between application layers
- Private deployment through S3 and VPC endpoints
- Working Flask to PostgreSQL integration
- End-to-end health validation
- Application and database failure isolation
- Recovery after injected faults
- A snapshot-based disaster recovery baseline

