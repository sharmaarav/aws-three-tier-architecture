# Northstar | AWS Three-Tier Architecture & Resilience Lab

A hands-on AWS infrastructure project focused on **secure network design, private application hosting, relational database connectivity, and systematic troubleshooting**.

I designed, deployed, and tested a three-tier application in AWS. An internet-facing Application Load Balancer (ALB) accepted public HTTP requests and routed them to a **private EC2 instance** running a Flask application with Gunicorn. The application connected to a **private Amazon RDS PostgreSQL database over SSL**. I then deliberately introduced two failures to test how the system behaved and how to diagnose and recover it.

> **Project scope:** This is a working architecture and resilience *lab*, not a production deployment. Although subnets span two Availability Zones, the application ran on **one EC2 instance** and the database on **one RDS instance**. Multi-instance failover, Multi-AZ RDS, infrastructure as code, HTTPS at the public endpoint, and a tested disaster-recovery restore were **not** implemented.

## Project at a glance

| Area | Implementation |
| --- | --- |
| AWS Region | `eu-west-2` (London) |
| Network | Custom VPC `10.0.0.0/16` |
| Subnets | Six `/24` subnets across two Availability Zones |
| Public entry point | Internet-facing Application Load Balancer, HTTP port `80` |
| Application | Private Amazon Linux 2023 EC2, Python Flask + Gunicorn, HTTP port `5000` |
| Database | Private Amazon RDS PostgreSQL, TCP port `5432`, SSL connection |
| Access control | Three tier-specific security groups |
| Private deployment access | Amazon S3 Gateway VPC Endpoint |
| Private administration | EC2 Instance Connect Endpoint |
| Validation | ALB target health, app/DB health endpoints, PostgreSQL write/read test |
| Fault injection | Application-process failure and database-network failure |
| Recovery baseline | Manual RDS snapshot captured; restore not tested |

## 1. Architecture

```text
                          Internet / Browser
                                 |
                              HTTP :80
                                 |
                      Internet-facing ALB
                       (public subnets)
                                 |
                        HTTP :5000 (ALB SG)
                                 |
                     Private EC2 application
                     Amazon Linux 2023
                       Flask + Gunicorn
                      (application subnet)
                                 |
                     PostgreSQL :5432 + SSL
                           (app SG only)
                                 |
                      Private RDS PostgreSQL
                        (database subnet)

        S3 deployment artifacts -- S3 Gateway VPC Endpoint --> EC2
        Administrator -- EC2 Instance Connect Endpoint --> EC2
```

The VPC uses six subnets distributed across two Availability Zones:

| Tier | Subnet | CIDR |
| --- | --- | --- |
| Public | `northstar-public-a` | `10.0.1.0/24` |
| Public | `northstar-public-b` | `10.0.2.0/24` |
| Application | `northstar-app-a` | `10.0.11.0/24` |
| Application | `northstar-app-b` | `10.0.12.0/24` |
| Database | `northstar-db-a` | `10.0.21.0/24` |
| Database | `northstar-db-b` | `10.0.22.0/24` |

**Why separate the tiers?** The ALB needs public reachability, but neither the application server nor the database needs a public IP address. Separating tiers into private subnets reduces direct exposure and makes traffic permissions easier to reason about.

**Why two Availability Zones?** The subnet layout provides a foundation for future multi-AZ deployments. **It does not by itself make the application highly available**: the implemented compute and database layers each had a single active instance.

> **Architecture image:** If you have exported the original diagram, add it at `docs/architecture.png` and uncomment the line below.
>
> `<!-- ![Northstar architecture](docs/architecture.png) -->`

## 2. AWS services and design decisions

### Amazon VPC, subnets and routing

I created a custom VPC to control the IP address space and isolate public, application, and database tiers. The public subnets support the internet-facing ALB; the application and database instances remain private.

### Application Load Balancer

The ALB is the **only public application entry point**. It receives HTTP traffic on port `80` and forwards requests to the application target on port `5000`. Its target health checks were also used to identify and verify recovery from an application-process failure.

An ALB provides a clean separation between external ingress and application hosting. In this lab it routed to **one** EC2 target; it did not provide multi-instance failover.

### Amazon EC2, Flask and Gunicorn

A private Amazon Linux 2023 EC2 instance hosted a Python Flask application served by Gunicorn. The instance had **no public IPv4 address**. It exposed application and database health endpoints for end-to-end testing.

### Amazon RDS for PostgreSQL

RDS provided a managed relational database in private database subnets. The application connected over **SSL** on PostgreSQL port `5432`. I verified connectivity with a database health query and a write/read operation.

### Amazon S3 and VPC endpoints

Application deployment artifacts were retrieved from S3 through an **S3 Gateway VPC Endpoint**, allowing private S3 access without exposing the application instance to the public internet. An **EC2 Instance Connect Endpoint** enabled administrative access to the private instance without assigning it a public IP address.

## 3. Security model

Traffic permissions were constrained using three security groups:

| Security group | Relevant permitted traffic |
| --- | --- |
| ALB SG | Inbound HTTP `80` from the internet; traffic onward to the application |
| Application SG | Inbound TCP `5000` **from the ALB security group** |
| Database SG | Inbound TCP `5432` **from the application security group** |

The intended request path was:

```text
Internet -> ALB security group -> Application security group -> Database security group
```

Using security-group references between tiers avoids opening application and database ports to broad internet CIDR ranges.

**Security limitations:** Public ingress used **HTTP, not HTTPS**. SSL was implemented for the **application-to-database** connection; that does not mean the browser-to-ALB connection was encrypted. A production design would add an ACM certificate and HTTPS listener, and would move sensitive configuration into a managed secrets service.

## 4. Implementation and deployment

The implementation was completed in the AWS London Region. At a high level, I:

1. Created the custom VPC, six subnets, routing resources, and tier-specific security groups.
2. Configured the public ALB and its target group.
3. Provisioned a private EC2 instance and a private RDS PostgreSQL database.
4. Set up private S3 access through a Gateway VPC Endpoint and administration through an EC2 Instance Connect Endpoint.
5. Deployed the Flask application and ran it behind Gunicorn on port `5000`.
6. Configured SSL-enabled PostgreSQL connectivity.
7. Validated the ALB-to-application and application-to-database request paths.
8. Injected failures and documented their symptoms, diagnosis, and recovery.

**Reproducibility note:** The infrastructure was built and validated as a hands-on lab. This repository does **not** claim to contain a one-command deployment or infrastructure-as-code implementation. Rebuilding it requires provisioning the AWS resources and supplying your own credentials and configuration.

### Application source and dependencies

The Flask source code and dependency manifest should be included in this repository once copied from the original project and reviewed for secrets. **Do not upload the Python virtual environment** (`venv/`, `.venv/`, `site-packages/`) or AWS credentials.

If the application source is available, document its exact filename and startup commands here. The portfolio confirms Flask/Gunicorn was used but does not establish a portable, one-command local setup, so no unverified run command is provided.

## 5. Validation and observed results

The deployed architecture was tested through the public ALB and from the application environment.

| Test | Observation |
| --- | --- |
| ALB target health | Target reported **Healthy** while Gunicorn was running |
| Application endpoint | `/health` returned a successful status (`ok`) |
| Database endpoint | `/api/db-health` reported the database reachable and query result `1` |
| Database operations | PostgreSQL insert and read operations completed successfully over SSL |
| Network exposure | Application EC2 and RDS had no direct public exposure |

These checks demonstrated the working request path:

```text
Browser -> ALB -> private Flask application -> private PostgreSQL database
```

The tests establish that the deployed lab worked at the time of validation. They are **not** evidence of a production availability SLA or load-tested performance.

## 6. Failure injection and troubleshooting

### Experiment A: Application-process failure

**Change introduced:** Stopped the Gunicorn application process on the private EC2 instance.

**Observed impact:** The ALB target became **Unhealthy** and the public application request failed (observed HTTP `502`).

**Diagnosis:** ALB target-health status helped isolate the problem to the application layer. The underlying instance and network configuration were not sufficient for successful requests if the application process was not running.

**Recovery:** Restarted Gunicorn and verified that the ALB target returned to **Healthy**.

**Lesson:** A load balancer can detect a failing application target, but with only one target it cannot maintain availability when that process is down.

### Experiment B: Database-network failure

**Change introduced:** Removed the inbound PostgreSQL TCP `5432` permission from the database security group.

**Observed impact:** The application itself remained available, but the database health check failed.

**Diagnosis:** Comparing application health with database health narrowed the issue to the application-to-database path. Network connectivity and security-group rules were checked separately from database authentication.

**Recovery:** Restored the database security-group rule and confirmed that database connectivity recovered.

**Lesson:** Distinguishing application health from dependency health helps identify the failing layer rather than treating every error as an application outage.

## 7. Disaster-recovery baseline

After validating the database, I captured a **manual RDS snapshot** as a recovery-point baseline. The snapshot reached an available/completed state.

**Important limitation:** I did **not** perform a restore-and-cutover test, so I cannot claim a measured recovery time objective (RTO), recovery point objective (RPO), or demonstrated disaster-recovery failover.

## 8. Challenges and lessons learned

- **Layered diagnosis:** Distinguishing DNS resolution, TCP reachability, and PostgreSQL authentication made failures easier to isolate.
- **Private-by-default architecture:** A public web application does not require publicly accessible compute or database instances.
- **Security-group chaining:** Referencing source security groups makes the intended trust relationships between tiers explicit.
- **Health checks:** ALB and application-level health signals are useful for locating and confirming recovery from faults.
- **Python deployment packaging:** Binary dependencies and console scripts must match the target runtime environment and interpreter paths.
- **Resilience versus availability:** Successfully deploying into a VPC with two Availability Zones does not eliminate single-instance failure points.

## 9. Production improvements

These are **proposed enhancements**, not features completed in this lab:

| Improvement | Why it matters |
| --- | --- |
| Auto Scaling Group with EC2 instances in two AZs | Removes the single application-instance dependency |
| Multi-AZ RDS | Adds database standby/failover capability |
| HTTPS via AWS Certificate Manager | Encrypts browser-to-ALB traffic |
| AWS Secrets Manager or SSM Parameter Store | Improves handling of database credentials |
| CloudWatch alarms and centralised logs | Improves operational visibility and alerting |
| Terraform or CloudFormation | Makes infrastructure deployment repeatable and reviewable |
| CI/CD pipeline | Automates and standardises application releases |
| Snapshot restore exercise | Validates recovery procedures and allows recovery-time measurement |

## 10. Repository contents

A suggested structure for publishing the actual project files:

```text
aws-three-tier-architecture/
├── README.md
├── .gitignore
├── requirements.txt           # if available from the original application
├── app.py                     # replace with the real Flask source filename
└── docs/
    ├── architecture.png       # add the exported architecture diagram
    └── screenshots/           # selected, sanitised AWS console evidence
```

The structure above is a **publishing guide**, not a claim that every file has already been uploaded. Remove placeholders and update filenames to match the source you actually have.

### Suggested screenshots

Use a small number of redacted screenshots showing the VPC/subnets, ALB and target health, private EC2/RDS configuration, successful health endpoints, fault injection, and completed RDS snapshot. Avoid exposing account IDs, database endpoints, credentials, or other sensitive identifiers unnecessarily.

## 11. Cost and cleanup

AWS resources such as ALBs, EC2, RDS, and VPC endpoints can incur charges while provisioned. This lab was intended as a bounded learning exercise; verify resources are terminated after use and check the AWS Billing console for any remaining costs. Closing an account should not replace checking for outstanding usage and charges.

## 12. Interview summary

> I built a secure three-tier AWS application in a custom VPC with six subnets across two Availability Zones. An internet-facing Application Load Balancer routed requests to a private EC2 instance running Flask and Gunicorn, which connected over SSL to a private RDS PostgreSQL database. I used tier-specific security groups, a private S3 endpoint for deployment artifacts, and an EC2 Instance Connect Endpoint for administration. After validating the full request path and database operations, I deliberately caused an application-process failure and a database-network failure, then diagnosed and recovered both. The project taught me how to design private-by-default AWS architectures and troubleshoot failures systematically, while recognising the limitations of a single-instance deployment.

---

**Project type:** Independent AWS architecture and troubleshooting lab  
**Completed:** October 2026  
**Primary technologies:** AWS VPC, ALB, EC2, RDS PostgreSQL, S3, VPC Endpoints, Linux, Python, Flask, Gunicorn

