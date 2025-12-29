# Lyftr AI Backend Assignment

A production-ready, containerized FastAPI service for ingesting "WhatsApp-like" messages with HMAC validation, idempotency, and analytics. Built with Python 3.11, SQLite, and Docker.

## 🏗️ System Architecture

The system follows a containerized monolithic architecture using FastAPI and SQLite, designed for 12-factor compliance and high observability.

```mermaid
graph LR
    Client["Client / Webhook Sender"] -- "POST /webhook<br>(X-Signature)" --> LoadBalancer["Docker Port Map<br>(:8000)"]
    Client -. "GET /messages, /stats" .-> LoadBalancer
    
    subgraph "Lyftr API Container"
        direction TB
        LoadBalancer --> API["FastAPI Application"]
        
        subgraph "Middleware Layer"
            Auth["HMAC Validator"]
            Logger["JSON Structured Logger"]
            Metrics["Prometheus Collector"]
        end
        
        API --> Auth
        Auth --> Logger
        Logger --> Metrics
        
        subgraph "Business Logic"
            Ingest["Message Ingestion<br>(Idempotency Check)"]
            Query["Query Engine<br>(Filter/Pagination)"]
            Analytics["Stats Aggregator"]
        end
        
        Metrics --> Ingest
        Metrics --> Query
        Metrics --> Analytics
    end

    subgraph "Persistence Layer"
        SQLite[("SQLite Database<br>(/data/app.db)")]
    end

    Ingest -- "Insert (Transactional)" --> SQLite
    Query -- "Select" --> SQLite
    Analytics -- "Aggregation" --> SQLite

    subgraph "Observability"
        Prometheus["Prometheus (External)"] -- "Scrape /metrics" --> API
    end
