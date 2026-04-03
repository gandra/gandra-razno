# OCI SLA Management System - Architecture Overview

**Purpose**: High-level system architecture and information flow
**Author**: Development Team
**Last Updated**: 2025-11-08
**Version**: 1.0

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Information Flow](#information-flow)
4. [Module Responsibilities](#module-responsibilities)
5. [Key Architectural Principles](#key-architectural-principles)
6. [Scheduler Orchestration](#scheduler-orchestration)
7. [Technology Stack](#technology-stack)
8. [Related Documentation](#related-documentation)

---

## 📖 System Overview

The OCI SLA Management System is a multi-module Spring Boot application that monitors Oracle Cloud Infrastructure (OCI) resources and tracks Service Level Agreement (SLA) compliance. The system operates on a **pull-and-cache** architecture where data is collected from OCI periodically and stored locally for analysis and reporting.

### System Goals

1. **Data Collection**: Automatically pull resource metadata, performance metrics, and cost data from OCI
2. **SLA Monitoring**: Track compliance against defined service level objectives
3. **Reporting**: Generate comprehensive compliance reports with export capabilities
4. **Alerting**: Notify stakeholders of SLA breaches and budget overruns

### Core Modules

| Module | Runtime | Purpose |
|--------|---------|---------|
| **oci-library** | Library JAR | Shared JPA entities, DTOs, repositories, utilities |
| **oci-monitor** | Background Worker | Data collection schedulers, SLA computation, OCI SDK integration |
| **oci-api** | REST API Server | User-facing API, SLA management, report generation, exports |
| **Frontend** | React Web App | User interface for SLA definition, monitoring, visualization |

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER LAYER                                                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Frontend (React + TypeScript)                                         │ │
│  │                                                                         │ │
│  │  - SLA Definition Wizard                                               │ │
│  │  - SLA List & Search                                                   │ │
│  │  - Report Generation                                                   │ │
│  │  - Chart Visualizations                                                │ │
│  │  - CSV/PDF Export                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                      │
│                                       │ HTTP/JSON                            │
└───────────────────────────────────────┼──────────────────────────────────────┘
                                        ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                                           │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  oci-api (REST API Server)                                             │ │
│  │                                                                         │ │
│  │  REST Controllers:                                                     │ │
│  │  ┌──────────────────────┐  ┌──────────────────────┐                   │ │
│  │  │ SlaDefinitionCtrl    │  │ SlaReportController  │                   │ │
│  │  │  ─────────────────   │  │  ──────────────────  │                   │ │
│  │  │  POST   /api/sla/def │  │  GET  /api/sla/rep   │                   │ │
│  │  │  GET    /api/sla/def │  │    /{id}             │                   │ │
│  │  │  PUT    /api/sla/def │  │  GET  /api/sla/rep   │                   │ │
│  │  │  DELETE /api/sla/def │  │    /{id}/export/csv  │                   │ │
│  │  │                      │  │  GET  /api/sla/rep   │                   │ │
│  │  │                      │  │    /{id}/export/pdf  │                   │ │
│  │  └──────────────────────┘  └──────────────────────┘                   │ │
│  │                                                                         │ │
│  │  Services:                                                             │ │
│  │  - SlaDefinitionService: CRUD operations for SLA definitions          │ │
│  │  - SlaReportService: Generate compliance reports from cached data     │ │
│  │  - SlaExportService: Export reports to CSV/PDF formats                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  oci-monitor (Background Worker)                                       │ │
│  │                                                                         │ │
│  │  Data Collection Schedulers:                                           │ │
│  │  ┌────────────────────┐  ┌────────────────────┐                       │ │
│  │  │ OciMetricsScheduler│  │ OciCostScheduler   │                       │ │
│  │  │  ────────────────  │  │  ────────────────  │                       │ │
│  │  │  Every 11 minutes  │  │  Configurable      │                       │ │
│  │  │  (prod)            │  │  (currently off)   │                       │ │
│  │  │  ────────────────  │  │  ────────────────  │                       │ │
│  │  │  Pulls:            │  │  Pulls:            │                       │ │
│  │  │  - CPU metrics     │  │  - Cost CSV files  │                       │ │
│  │  │  - Memory metrics  │  │  - from Object     │                       │ │
│  │  │  - Disk I/O        │  │    Storage         │                       │ │
│  │  │  - Network traffic │  │                    │                       │ │
│  │  └────────────────────┘  └────────────────────┘                       │ │
│  │                                                                         │ │
│  │  ┌────────────────────┐  ┌────────────────────────────────────────┐  │ │
│  │  │ OciBudgetScheduler │  │ SlaSchedulerService                    │  │ │
│  │  │  ────────────────  │  │  ────────────────────────────────────  │  │ │
│  │  │  Every 7 minutes   │  │  Daily:   0 5 0 * * * (00:05)          │  │ │
│  │  │  (prod)            │  │  Weekly:  0 10 0 * * MON (Mon 00:10)   │  │ │
│  │  │  ────────────────  │  │  Monthly: 0 15 0 1 * * (1st 00:15)     │  │ │
│  │  │  Pulls:            │  │  ────────────────────────────────────  │  │ │
│  │  │  - Budget status   │  │  Computes:                             │  │ │
│  │  │  - Budget alerts   │  │  - SLA compliance (from cached data)   │  │ │
│  │  │                    │  │  - Breach detection                    │  │ │
│  │  │                    │  │  - Penalty calculations                │  │ │
│  │  └────────────────────┘  └────────────────────────────────────────┘  │ │
│  │                                                                         │ │
│  │  Core Services:                                                        │ │
│  │  - SlaComputationService: Calculate SLA compliance percentages        │ │
│  │  - AvailabilityCalculatorService: Compute uptime/availability         │ │
│  │  - BreachDetectionService: Identify SLA violations                    │ │
│  │  - OciResourceManagerService: Resource discovery and management       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────┼──────────────────────────────────────┘
                                        │
                                        │ OCI SDK (com.oracle.bmc.*)
                                        ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  ORACLE CLOUD INFRASTRUCTURE (OCI)                                          │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐               │
│  │   Resources    │  │    Metrics     │  │  Object Storage│               │
│  │ (VM, DB, etc)  │  │  (CPU, Memory) │  │  (Cost Reports)│               │
│  └────────────────┘  └────────────────┘  └────────────────┘               │
│                                                                              │
│  SDK Clients Used:                                                          │
│  - ResourceSearchClient: Discover resources                                │
│  - MonitoringClient: Fetch performance metrics                             │
│  - ObjectStorageClient: Download cost/billing data                         │
│  - ComputeClient: Start/stop instances                                     │
│  - DatabaseClient: Manage databases                                        │
│  - IdentityClient: List compartments                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  DATA LAYER                                                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  MySQL Database                                                        │ │
│  │                                                                         │ │
│  │  Data Collection Tables:          SLA Management Tables:              │ │
│  │  ┌────────────────┐               ┌────────────────────┐              │ │
│  │  │ resource       │               │ sla_definition     │              │ │
│  │  │ metric_result  │               │ sla_breach         │              │ │
│  │  │ cost           │               │ sla_downtime_window│              │ │
│  │  │ tenant         │               │ sla_penalty_tier   │              │ │
│  │  │ oci_query      │               └────────────────────┘              │ │
│  │  └────────────────┘                                                    │ │
│  │                                                                         │ │
│  │  Control/Settings Tables:                                              │ │
│  │  ┌──────────────────────┐                                              │ │
│  │  │ scheduler_settings   │  - Global scheduler toggles                 │ │
│  │  │ tenant_settings      │  - Per-tenant data collection flags         │ │
│  │  └──────────────────────┘                                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Information Flow

### 1. Data Collection Flow (oci-monitor → OCI → Database)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  Scheduler   │ ───→  │   OCI SDK    │ ───→  │  Parse/      │ ───→  │   Database   │
│  Triggers    │       │   API Call   │       │  Transform   │       │   Storage    │
└──────────────┘       └──────────────┘       └──────────────┘       └──────────────┘

Examples:
- OciMetricsScheduler (every 11 min) → MonitoringClient.summarizeMetricsData()
  → Parse metric data points → Save to metric_result table

- OciCostScheduler (on-demand) → ObjectStorageClient.getObject()
  → Download & parse CSV/GZ → Save to cost table

- OciBudgetScheduler (every 7 min) → Read cost table
  → Calculate budget status → Save to budget entities
```

| Aspect | Details |
|--------|---------|
| **Trigger** | Fixed-rate scheduler with @Scheduled annotation |
| **Guard** | Global toggle (scheduler_settings.is_enabled) + Tenant settings |
| **Output** | Cached data in database tables |

---

### 2. SLA Computation Flow (oci-monitor reads Database only)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   CRON       │ ───→  │   Read       │ ───→  │  Compute     │ ───→  │   Save       │
│   Scheduler  │       │   Cached     │       │  Compliance  │       │   Breaches   │
│              │       │   Metrics    │       │              │       │              │
└──────────────┘       └──────────────┘       └──────────────┘       └──────────────┘

Examples:
- Daily SLA (0 5 0 * * *) → Read metric_result for last 24h
  → Calculate compliance % → Detect breaches → Save to sla_breach

- Weekly SLA (0 10 0 * * MON) → Read metric_result for last 7 days
  → Filter maintenance windows → Calculate compliance → Save results

- Monthly SLA (0 15 0 1 * *) → Read metric_result for last month
  → Apply penalty tiers → Calculate penalties → Save results
```

| Aspect | Details |
|--------|---------|
| **Trigger** | CRON expression (time-based) |
| **Input** | Cached metric_result data (no OCI API calls) |
| **Output** | sla_breach records, compliance statistics |

**IMPORTANT**: SLA computation does NOT call OCI APIs - it works entirely on cached data.

---

### 3. Report Generation Flow (oci-api reads Database only)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   User       │ ───→  │   REST       │ ───→  │   Query      │ ───→  │  Return      │
│   Request    │       │   Endpoint   │       │   Database   │       │  Report DTO  │
└──────────────┘       └──────────────┘       └──────────────┘       └──────────────┘
                                                                              │
                                                                              ↓
                                              ┌─────────────────────────────────────┐
                                              │  Optional Export                    │
                                              │  - CSV: Apache Commons CSV          │
                                              │  - PDF: Thymeleaf + Flying Saucer   │
                                              │  - Charts: Rendered client-side     │
                                              └─────────────────────────────────────┘

Examples:
- GET /api/sla/reports/{id}?periodType=MONTHLY&periodStart=2025-11-01
  → Read sla_definition → Read sla_breach for period → Calculate summary → Return JSON

- GET /api/sla/reports/{id}/export/csv
  → Generate report → Format as CSV (3 sections) → Download file

- GET /api/sla/reports/{id}/export/pdf
  → Generate report → Render HTML template → Convert to PDF → Download file
```

| Aspect | Details |
|--------|---------|
| **Trigger** | User HTTP request |
| **Input** | Cached data (sla_definition, sla_breach, metric_result) |
| **Output** | JSON report / CSV file / PDF file |

---

## 📦 Module Responsibilities

### oci-library (Shared Library)

**Purpose**: Common foundation shared by oci-api and oci-monitor

**Contents**:
- JPA Entities (SlaDefinition, SlaBreach, MetricResult, Resource, Tenant, etc.)
- Spring Data JPA Repositories
- DTOs for data transfer
- Utility classes
- Shared service logic

**Dependencies**: Spring Data JPA, Lombok, MapStruct, QueryDSL

**Build Requirement**: Must be built first (run mvn clean install in oci-library directory)

---

### oci-monitor (Background Worker)

**Purpose**: Scheduled data collection and SLA computation

**Key Components**:

| Component Type | Examples | Frequency |
|----------------|----------|-----------|
| **Schedulers** | OciMetricsScheduler, OciCostScheduler, SlaSchedulerService | Fixed-rate or CRON |
| **Services** | SlaComputationService, AvailabilityCalculatorService | Called by schedulers |
| **OCI Clients** | MonitoringClient, ObjectStorageClient, ResourceSearchClient | On-demand |

**Data Flow**:
1. Scheduler triggers (time-based)
2. Check global + tenant toggles
3. Call OCI SDK (for data collection) OR read DB (for SLA computation)
4. Parse/transform data
5. Save to database

**Does NOT**:
- Expose REST API endpoints
- Handle user requests
- Generate reports for users

---

### oci-api (REST API Server)

**Purpose**: User-facing API for SLA management and reporting

**Key Components**:

| Component Type | Examples | Purpose |
|----------------|----------|---------|
| **Controllers** | SlaDefinitionController, SlaReportController | REST endpoints |
| **Services** | SlaDefinitionService, SlaReportService, SlaExportService | Business logic |
| **Security** | JWT authentication, role-based access control | User authentication |

**Data Flow**:
1. User sends HTTP request
2. JWT authentication/authorization
3. Controller validates request
4. Service queries database (cached data)
5. Transform to DTO
6. Return JSON / CSV / PDF

**Does NOT**:
- Call OCI SDK directly (uses cached data)
- Run scheduled background jobs
- Collect metrics from OCI

---

### Frontend (React Web App)

**Purpose**: User interface for SLA management

**Key Features**:

| Feature | Components | Technology |
|---------|-----------|------------|
| **SLA Definition** | 5-step wizard, validation | React Hook Form, Zod |
| **SLA List** | Search, filter, navigation | React Table |
| **Report Generation** | Form, display, charts | Chart.js, react-chartjs-2 |
| **Export** | CSV/PDF download buttons | Blob API, file download |

**Data Flow**:
1. User interacts with UI
2. Call oci-api REST endpoints
3. Receive JSON responses
4. Render UI components
5. Display charts (client-side rendering)

---

## 🎯 Key Architectural Principles

### 1. Pull-and-Cache Pattern

**Principle**: All OCI data is pulled periodically and cached in the database. Analysis and reporting work on cached data.

**Benefits**:
- Reduces OCI API costs (fewer API calls)
- Improves performance (no API latency during reports)
- Enables historical analysis (data retention)
- Works offline (if OCI API unavailable)

**Implementation**:
- oci-monitor pulls data on schedule → saves to DB
- oci-api reads from DB → returns reports
- oci-monitor SLA computation reads from DB → saves breaches

---

### 2. Two-Level Control

**Principle**: Schedulers require BOTH global toggle AND tenant-specific settings to run.

**Global Toggle** (scheduler_settings table):
```sql
UPDATE scheduler_settings
SET is_enabled = 1
WHERE scheduler_task_name = 'metrics.scheduled.data.pull';
```

**Tenant Setting** (tenant_settings table):
```sql
UPDATE tenant_settings
SET is_metrics_data_accessible = 1
WHERE tenant_id = 'uuid';
```

**Logic**:
```java
// Step 1: Check global toggle
if (!schedulerToggleService.isTaskEnabled("metrics.scheduled.data.pull")) {
    return; // SKIP - disabled globally
}

// Step 2: Load only enabled tenants
List<Tenant> tenants = ociTenancyService.findAllMetricsTenants();
// Returns only tenants where is_metrics_data_accessible = 1
```

---

### 3. Separation of Concerns

| Concern | Module | Why |
|---------|--------|-----|
| **Data Collection** | oci-monitor | Schedulers, OCI SDK, batch processing |
| **User API** | oci-api | REST endpoints, real-time requests |
| **SLA Definition** | oci-api | User manages SLA rules via UI |
| **SLA Computation** | oci-monitor | Batch processing on schedule |
| **SLA Reporting** | oci-api | On-demand report generation |

**Communication**: Modules share database (no direct service-to-service calls)

---

### 4. No Real-Time OCI Calls for SLA

**Principle**: SLA computations and reports NEVER call OCI APIs in real-time.

**Why**:
- OCI API rate limits (costs, throttling)
- Performance (API latency 1-5 seconds)
- Reliability (works even if OCI API down)
- Historical analysis (need past data, not just current)

**How**:
- Metrics collected by OciMetricsScheduler → saved to metric_result
- SLA computation reads metric_result → calculates compliance
- Reports read sla_breach + metric_result → generate summary

---

## ⏰ Scheduler Orchestration

### Scheduler Hierarchy

```
Data Collection (oci-monitor)
├── OciMetricsScheduler: Every 11 minutes (prod)
│   ├── Pulls CPU, Memory, Disk, Network metrics
│   └── Saves to metric_result table
│
├── OciCostScheduler: Configurable (currently disabled)
│   ├── Downloads CSV/GZ cost reports from Object Storage
│   └── Parses and saves to cost table
│
└── OciBudgetScheduler: Every 7 minutes (prod)
    ├── Reads cost table
    └── Calculates budget status → saves to budget entities

SLA Processing (oci-monitor)
└── SlaSchedulerService: Three CRON schedules
    ├── Daily:   0 5 0 * * *      (Every day at 00:05)
    ├── Weekly:  0 10 0 * * MON   (Every Monday at 00:10)
    └── Monthly: 0 15 0 1 * *     (Every 1st of month at 00:15)
        ├── Reads metric_result (cached data)
        ├── Calculates SLA compliance
        ├── Detects breaches
        └── Saves to sla_breach table
```

### Execution Order

```
Time: 00:00 (midnight)
│
├─ 00:05 → SlaSchedulerService.processDailySlas()
│          - Process all DAILY SLAs
│          - Calculate yesterday's compliance
│
├─ 00:10 → SlaSchedulerService.processWeeklySlas() [Monday only]
│          - Process all WEEKLY SLAs
│          - Calculate last week's compliance
│
├─ 00:15 → SlaSchedulerService.processMonthlySlas() [1st of month]
│          - Process all MONTHLY SLAs
│          - Calculate last month's compliance
│
└─ 00:XX → OciMetricsScheduler continues running every 11 minutes
           - Collecting fresh metric data for today
```

**Key Insight**: SLA schedulers run AFTER midnight to compute previous period's compliance using already-collected metric data.

---

## 🛠️ Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Java | 17 | Programming language |
| Spring Boot | 3.2.1 | Application framework |
| Maven | Multi-module | Build tool |
| MySQL | 8.0 | Database |
| Flyway | Latest | Database migrations |
| OCI Java SDK | 3.x | Oracle Cloud integration |
| Lombok | Latest | Reduce boilerplate |
| MapStruct | Latest | DTO mapping |
| QueryDSL | Latest | Dynamic queries |
| Apache Commons CSV | 1.10.0 | CSV export |
| Thymeleaf | 3.x | PDF template engine |
| Flying Saucer | 9.5.1 | HTML to PDF conversion |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | Latest | Build tool |
| React Hook Form | 7.x | Form management |
| Zod | 3.x | Validation |
| Chart.js | 4.5.1 | Data visualization |
| react-chartjs-2 | 5.3.1 | React bindings for Chart.js |
| TailwindCSS | 3.x | Styling |
| date-fns | Latest | Date manipulation |

---

## 📚 Related Documentation

For detailed implementation information, see:

### Data Collection Details
**File**: docs/implementation/OCI-DATA-COLLECTION-ARCHITECTURE.md

**Contents**:
- Detailed scheduler configurations
- OCI SDK client usage examples
- Metric collection workflows
- Cost report parsing
- Database schema for data collection tables
- Troubleshooting data collection issues
