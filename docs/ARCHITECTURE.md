# System Architecture Design

## Overview
This system adopts a **Microservices Architecture** with an **Event-Driven Design**. The core principles are:
- **Scalability**: Horizontal scaling of services.
- **Availability**: No single point of failure (SPOF).
- **Consistency**: Strong consistency for financial transactions using Saga pattern and 2PC where necessary.
- **Observability**: Centralized logging and monitoring.

## 1. Microservices Structure

### Backend Services (Java / Spring Boot)
- **Account Service**: Manages customer accounts, balances, and history.
- **Transaction Service**: Orchestrates money transfers and payments. Implements Saga pattern.
- **Forex Service**: Handles currency exchange rates and SWIFT integration.
- **Loan Service**: Manages loan applications, repayments, and collaterals.
- **Audit Service**: Records all system activities securely.

### Data Processing Services (Python)
- **Analytics Service**: Real-time fraud detection and customer behavior analysis.
- **Risk Calculation Service**: Calculates credit risk, market risk (VaR), and liquidity risk.
- **Reporting Service**: Generates regulatory reports (Basel III, AML).

## 2. Event-Driven Architecture (EDA)
- **Message Broker**: Apache Kafka is used for asynchronous communication between services.
- **Topics**:
  - `transaction.created`: Triggered when a transaction is initiated.
  - `account.updated`: Triggered after balance changes.
  - `forex.rate.updated`: Triggered on new exchange rates.
  - `loan.approved`: Triggered after loan approval.

## 3. Data Persistence (CQRS + Event Sourcing)
- **Command Query Responsibility Segregation (CQRS)**:
  - **Write Model**: Optimized for high-throughput writes (PostgreSQL Master).
  - **Read Model**: Optimized for fast reads (PostgreSQL Read Replicas, Redis Cache).
- **Event Sourcing**: critical state changes are stored as a sequence of events in Kafka/EventStore to ensure auditability and replayability.

## 4. Infrastructure Diagram (Conceptual)

```mermaid
graph TD
    User[Client App / Web] -->|HTTPS| LB[Load Balancer]
    LB --> API_Gateway[API Gateway (Spring Cloud / Nginx)]

    API_Gateway --> Auth[Auth Service (OAuth2)]
    API_Gateway --> Account[Account Service]
    API_Gateway --> Transaction[Transaction Service]
    API_Gateway --> Loan[Loan Service]

    subgraph Data Layer
        Postgres_Master[(PostgreSQL Master)]
        Postgres_Slave[(PostgreSQL Replica)]
        Redis[(Redis Cache)]
    end

    subgraph Event Bus
        Kafka[Apache Kafka]
        Zookeeper[Zookeeper]
    end

    Account --> Postgres_Master
    Account --> Redis
    Transaction --> Kafka
    Transaction --> Postgres_Master

    Kafka -->|Consume| Audit[Audit Service]
    Kafka -->|Consume| Analytics[Python Analytics Service]

    Analytics -->|Read| Postgres_Slave
```

## 5. Technology Stack Details
- **Java**: 17 (LTS), Spring Boot 3.2.x, Spring Cloud
- **Python**: 3.11, FastAPI, Pandas, Scikit-learn
- **Database**: PostgreSQL 15 (Declarative Partitioning)
- **Cache**: Redis 7 (Cluster Mode)
- **Message Queue**: Apache Kafka 3.6
- **Containerization**: Docker, Kubernetes (Helm Charts)
