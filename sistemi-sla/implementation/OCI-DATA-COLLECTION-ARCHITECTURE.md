# OCI Data Collection Architecture

**Module**: oci-monitor
**Purpose**: Oracle Cloud Infrastructure Data Synchronization & Caching
**Author**: Development Team
**Last Updated**: 2025-11-08
**Version**: 2.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [OCI Integration - Authentication](#oci-integration---authentication)
4. [Data Collection Schedulers](#data-collection-schedulers)
5. [What Data is Collected](#what-data-is-collected)
6. [Database Schema](#database-schema)
7. [OCI SDK Usage](#oci-sdk-usage)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Related Documentation](#related-documentation)

---

## 📖 Overview

The **oci-monitor** module is responsible for collecting data from Oracle Cloud Infrastructure (OCI) and storing it locally in a MySQL database. This implements a **pull-and-cache** architecture where data is periodically synchronized from OCI, enabling fast queries, historical analysis, and reduced API costs.

### Key Principle

**All data is PULLED from OCI and CACHED locally. Analysis, monitoring, and reporting work on cached data, NOT by calling OCI APIs in real-time.**

### Benefits of Pull-and-Cache Architecture

| Benefit | Description |
|---------|-------------|
| **Reduced API Costs** | Fewer OCI API calls (charged per request) |
| **Improved Performance** | No API latency during queries/reports (1-5 sec saved) |
| **Historical Analysis** | Data retention in database enables trend analysis |
| **Offline Capability** | System works even if OCI API temporarily unavailable |
| **Rate Limit Protection** | Avoids hitting OCI API rate limits |

### Data Types Collected

1. **Resources** (VM instances, databases, etc.)
2. **Metrics** (CPU, Memory, Disk I/O, Network traffic)
3. **Cost & Billing** (Usage reports from Object Storage)
4. **Budgets** (Budget status and alerts)

### How oci-monitor Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  OCI CLOUD                                                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                            │
│  │ Resources  │  │  Metrics   │  │  Object    │                            │
│  │            │  │            │  │  Storage   │                            │
│  └────────────┘  └────────────┘  └────────────┘                            │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │ OCI SDK (API Key Authentication)
                           ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  oci-monitor MODULE                                                          │
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│  │ Schedulers         │  │ Services           │  │ OCI SDK Clients    │   │
│  │  ────────────────  │  │  ────────────────  │  │  ────────────────  │   │
│  │ @Scheduled         │  │ Business logic     │  │ MonitoringClient   │   │
│  │ - Metrics (11 min) │  │ - Parse data       │  │ ObjectStorageClient│   │
│  │ - Cost (on-demand) │  │ - Transform data   │  │ ResourceSearchClient│  │
│  │ - Budget (7 min)   │  │ - Batch insert     │  │ ComputeClient      │   │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘   │
│                                       ↓                                      │
│                              Save to Database                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  MYSQL DATABASE                                                              │
│                                                                              │
│  ┌────────────┐  ┌───────────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  resource  │  │ metric_result │  │   cost   │  │  tenant_settings │   │
│  │            │  │               │  │          │  │                  │   │
│  │  - ocid    │  │  - resource_  │  │  - date  │  │  - is_metrics_   │   │
│  │  - name    │  │    ocid (str) │  │  - amount│  │    accessible    │   │
│  │  - tags    │  │  - time       │  │  - usage │  │  - is_cost_      │   │
│  │            │  │  - value      │  │          │  │    accessible    │   │
│  └────────────┘  └───────────────┘  └──────────┘  └──────────────────┘   │
│                                                                              │
│  (Used by oci-api for reports, dashboards, SLA monitoring, etc.)           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Oracle Cloud Infrastructure (OCI)                                          │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐               │
│  │   Resources    │  │    Metrics     │  │  Object Storage│               │
│  │ (VM, DB, etc)  │  │  (CPU, Memory) │  │  (Cost Reports)│               │
│  └────────────────┘  └────────────────┘  └────────────────┘               │
│         │                     │                    │                        │
│         └─────────────────────┴────────────────────┘                        │
│                                       │                                      │
│                            OCI SDK (com.oracle.bmc.*)                        │
│                            - ResourceSearchClient                            │
│                            - MonitoringClient                                │
│                            - ObjectStorageClient                             │
│                            - ComputeClient, DatabaseClient                   │
│                            - IdentityClient                                  │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          │ API Key Authentication
                                          │ (User OCID + Private Key + Fingerprint)
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  oci-monitor Module (Spring Boot Background Worker)                         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  DATA COLLECTION SCHEDULERS (@Scheduled)                               │ │
│  │                                                                         │ │
│  │  ┌──────────────────────┐  ┌───────────────────────────────────────┐  │ │
│  │  │  OciMetricsScheduler │  │  OciCostScheduler                     │  │ │
│  │  │  ────────────────────│  │  ───────────────────────────────────  │  │ │
│  │  │  Frequency: configur.│  │  Frequency: configurable              │  │ │
│  │  │  (prod: 11 minutes)  │  │  (disabled in current setup)          │  │ │
│  │  │  ────────────────────│  │  ───────────────────────────────────  │  │ │
│  │  │  Collects:           │  │  Collects:                            │  │ │
│  │  │  - CPU metrics       │  │  - Cost reports from Object Storage   │  │ │
│  │  │  - Memory metrics    │  │  - Parses CSV/GZ files locally        │  │ │
│  │  │  - Disk I/O          │  │  - MD5 validation                     │  │ │
│  │  │  - Network traffic   │  │  - Batch insert to DB                 │  │ │
│  │  └──────────────────────┘  └───────────────────────────────────────┘  │ │
│  │                                                                         │ │
│  │  ┌──────────────────────┐                                              │ │
│  │  │ OciBudgetScheduler   │                                              │ │
│  │  │  ────────────────────│                                              │ │
│  │  │  Frequency: configur.│                                              │ │
│  │  │  (prod: 7 minutes)   │                                              │ │
│  │  │  ────────────────────│                                              │ │
│  │  │  Collects:           │                                              │ │
│  │  │  - Budget status     │                                              │ │
│  │  │  - Budget alerts     │                                              │ │
│  │  │  - Notifications     │                                              │ │
│  │  └──────────────────────┘                                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                       ↓                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  SERVICES (Business Logic)                                             │ │
│  │                                                                         │ │
│  │  ┌──────────────────────────────┐  ┌─────────────────────────────┐   │ │
│  │  │ OciResourceManagerService    │  │ OciMetricsSchedulerService  │   │ │
│  │  │  ──────────────────────────  │  │  ─────────────────────────  │   │ │
│  │  │  - searchManagableResources()│  │  - pullMetricsData()        │   │ │
│  │  │  - Uses ResourceSearchClient │  │  - Uses MonitoringClient    │   │ │
│  │  │  - getResourceStatus()       │  │  - Save to metric_result    │   │ │
│  │  │  - startResource()           │  │                             │   │ │
│  │  │  - stopResource()            │  │                             │   │ │
│  │  └──────────────────────────────┘  └─────────────────────────────┘   │ │
│  │                                                                         │ │
│  │  ┌──────────────────────────────┐  ┌─────────────────────────────┐   │ │
│  │  │ OciCostSchedulerService      │  │ OciBudgetSchedulerService   │   │ │
│  │  │  ──────────────────────────  │  │  ─────────────────────────  │   │ │
│  │  │  - pullCostReports()         │  │  - calculateBudgetStatus()  │   │ │
│  │  │  - parseCostReports()        │  │  - Uses internal cost table │   │ │
│  │  │  - Uses ObjectStorageClient  │  │  - No OCI API calls         │   │ │
│  │  └──────────────────────────────┘  └─────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  DATABASE (MySQL)                                                           │
│                                                                              │
│  ┌────────────┐  ┌───────────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  resource  │  │ metric_result │  │   cost   │  │  tenant          │   │
│  │  ────────  │  │ ───────────── │  │  ──────  │  │  ──────          │   │
│  │  - ocid    │  │  - resource_  │  │  - date  │  │  - ocid          │   │
│  │  - name    │  │    ocid (str) │  │  - amount│  │  - name          │   │
│  │  - tags    │  │  - time       │  │  - usage │  │  - api_key_path  │   │
│  │            │  │  - value      │  │          │  │                  │   │
│  └────────────┘  └───────────────┘  └──────────┘  └──────────────────┘   │
│                                                                              │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │tenant_     │  │   oci_query   │  │cost_reports  │  │scheduler_    │   │
│  │settings    │  │  ───────────  │  │ ──────────── │  │settings      │   │
│  │  ────────  │  │  - namespace  │  │  - filename  │  │ ──────────── │   │
│  │  - tenant_id│  │  - metric_name│  │  - is_valid  │  │  - task_name │   │
│  │  - is_metr-│  │  - resources  │  │  - processed │  │  - is_enabled│   │
│  │    ics_acc │  │               │  │              │  │              │   │
│  └────────────┘  └───────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 OCI Integration - Authentication

### Authentication Method: API Key

oci-monitor uses **OCI API Key authentication** to connect to Oracle Cloud Infrastructure.

**Components Required:**

| Component | Description | Example Format |
|-----------|-------------|----------------|
| **User OCID** | Unique identifier for OCI user | ocid1.user.oc1...\<unique_id\> |
| **Tenancy OCID** | Unique identifier for OCI tenancy | ocid1.tenancy.oc1...\<unique_id\> |
| **Fingerprint** | Public key fingerprint (SHA-1 hash of public key) | aa:bb:cc:... |
| **Private Key** | RSA private key in PEM format | Stored in file system |
| **Region** | OCI region identifier | us-ashburn-1, eu-frankfurt-1 |

**Storage**:
- Tenant credentials stored in tenant table
- API key path configured per tenant (points to private key file on server)
- Authentication provider created dynamically per scheduler run

**Security**:
- Private key files must have restricted permissions (readable only by app user)
- Private key NOT stored in database (only file path)
- API key rotation supported (update file path in tenant record)

**Code Example**:
```java
// From OciAuthenticationDetailsProviderService
OciAuthenticationDetailsProvider authProvider =
    authenticationDetailsProviderService.getOciAuthenticationDetailsProvider(
        tenant,
        TenancyAccessType.SYSTEM,
        null
    );

// Creates OCI SDK client
MonitoringClient monitoringClient = MonitoringClient.builder()
    .region(authProvider.getRegion())
    .build(authProvider);
```

**Authentication Flow**:
```
1. Scheduler starts
        ↓
2. Load tenant from DB (tenant table)
        ↓
3. Load tenant settings (tenant_settings table)
        ↓
4. Read private key from file system (path from tenant.api_key_path)
        ↓
5. Create OciAuthenticationDetailsProvider
   - User OCID
   - Tenancy OCID
   - Fingerprint
   - Private key (from file)
   - Region
        ↓
6. Create OCI SDK client (MonitoringClient, ObjectStorageClient, etc.)
        ↓
7. Make API calls to OCI
        ↓
8. Parse and save data to DB
```

---

## ⏰ Data Collection Schedulers

### Scheduler Control Architecture

All schedulers use **two-level control**:

| Control Level | Table | Purpose |
|---------------|-------|---------|
| **Global Toggle** | scheduler_settings | Enable/disable scheduler globally |
| **Tenant Settings** | tenant_settings | Enable/disable per tenant |

**Execution Logic**:
```java
// STEP 1: Check global toggle
if (!schedulerToggleService.isTaskEnabled("metrics.scheduled.data.pull")) {
    log.info("Metrics scheduler is disabled globally. Skipping execution.");
    return; // EXIT - scheduler disabled globally
}

// STEP 2: Load only enabled tenants
// findAllMetricsTenants() returns tenants where:
//   tenant_settings.is_metrics_data_accessible = 1
List<Tenant> tenants = ociTenancyService.findAllMetricsTenants();

// STEP 3: Process each enabled tenant
for (Tenant tenant : tenants) {
    // Create auth provider
    OciAuthenticationDetailsProvider auth = createAuthProvider(tenant);

    // Pull metrics data
    ociMetricsSchedulerService.pullMetricsData(tenant, auth);
}
```

---

### 1. OciMetricsScheduler

**Purpose**: Collect resource performance metrics (CPU, Memory, Disk, Network)

**Frequency**: Configurable via property metrics.scheduled.data.pull.cron.fixedRateMinutes
- **Production**: 11 minutes (defined in application-prod.properties:58)
- **Local/Dev**: 5 minutes

**Configuration**:
```properties
# application-prod.properties
metrics.scheduled.data.pull.cron.initialDelayMinutes=2
metrics.scheduled.data.pull.cron.fixedRateMinutes=11
```

**Workflow**:
```
1. Check global toggle: scheduler_settings.is_enabled = 1 for "metrics.scheduled.data.pull"
        ↓
2. Load enabled tenants: tenant_settings.is_metrics_data_accessible = 1
        ↓
3. For each tenant:
   a. Create OCI authentication provider
   b. Load all oci_query definitions (what metrics to collect)
   c. Load resources linked to each query (via oci_query_resources join table)
   d. For each query + resource:
      - Build MQL query (Monitoring Query Language)
      - Call OCI Monitoring API: summarizeMetricsData()
      - Parse response (list of metric data points)
      - Save to metric_result table (using resource_ocid STRING field)
      - Update oci_query_reports (sync status, last processed interval)
        ↓
4. Log completion (metrics collected, errors, duration)
```

**OCI SDK Client Used**:
- MonitoringClient (see oci-monitor/service/scheduler/OciMetricsSchedulerService.java:303)

**OCI API Method**:
- summarizeMetricsData() - Returns aggregated metric data (mean, max, min, sum, count)

**Database Tables Updated**:
- metric_result - Stores individual metric data points
- oci_query_reports - Tracks sync status and intervals

**Example MQL Query**:
```java
SummarizeMetricsDataDetails details = SummarizeMetricsDataDetails.builder()
    .namespace("oci_computeagent")  // Metric namespace
    .query("CpuUtilization[5m]{resourceId = \"ocid1.instance..\"}.mean()")  // MQL query
    .startTime(startDate)
    .endTime(endDate)
    .build();
```

**Metrics Collected** (Current Configuration):
| Metric Name | Namespace | Statistic | Queries |
|-------------|-----------|-----------|---------|
| CpuUtilization | oci_computeagent | MEAN | 2 |
| MemoryUtilization | oci_computeagent | MEAN | 1 |
| DiskBytesRead | oci_computeagent | MEAN | 1 |
| DiskBytesWritten | oci_computeagent | MEAN | 1 |

**Data Point Interval**: 5 minutes (configurable via oci_query.interval_minutes column)

---

### 2. OciCostScheduler

**Purpose**: Collect cost/billing data from Object Storage

**Frequency**: Configurable via properties + DB toggle (currently disabled in most setups)

**Workflow**:
```
1. Check global toggle: scheduler_settings.is_enabled = 1 for "cost.scheduled.data.pull"
        ↓
2. Load enabled tenants: tenant_settings.is_cost_data_accessible = 1
        ↓
3. For each tenant:
   a. Read cost_report_settings (namespace, bucket, prefix)
   b. List objects in Object Storage bucket (by prefix)
      - Example prefix: "reports/cost-csv/"
      - Files: cost-2025-11.csv.gz, cost-2025-10.csv.gz, ...
        ↓
4. For each cost report file:
   a. Check if already processed (cost_reports.is_processed = 1)
   b. Download file from Object Storage (GetObject API)
   c. Validate MD5 checksum (Base64 of MD5 over stream)
   d. Decompress if GZ file (GZipInputStream)
   e. Parse CSV locally (OciCostParser)
      - Columns: lineItem/tenantId, lineItem/resourceId, usage/billedQuantity, cost/myCost, ...
   f. Batch insert rows into cost table (via BatchInsertUtil)
      - Upsert lookups (Product, Subscription, Resource, Compartment) via caches
   g. Update cost_reports (is_valid, is_processed, attempts, timestamps)
        ↓
5. Log completion (files processed, rows inserted, errors)
```

**OCI SDK Client Used**:
- ObjectStorageClient (see oci-monitor/service/scheduler/OciCostSchedulerService.java:114)

**OCI API Methods**:
- listObjects() - List cost report files in bucket
- getObject() - Download cost report file

**Database Tables Updated**:
- cost_report_settings - Configuration (namespace, prefix, etc.)
- cost_reports - File metadata + state (downloaded, valid, processed)
- cost - Parsed usage/cost data
- cost_aggregate_reports - Aggregated data

**CSV Format** (Oracle Cost Reports):
```csv
lineItem/tenantId,lineItem/resourceId,lineItem/compartmentPath,product/service,...
ocid1.tenancy...,ocid1.instance...,/root/prod/,Compute,OCI Compute,...
```

**Important Notes**:
- **Cost reports are NOT available via OCI UsageClient API** - Oracle does not expose full cost/usage reports through the UsageClient SDK. Instead, detailed cost reports are generated by OCI and uploaded to Object Storage buckets as CSV files. See [Why UsageClient is not used](#-not-currently-used) for more details.
- Reports must be configured in OCI Console to upload to Object Storage
- MD5 validation ensures file integrity
- Batch insert for performance (thousands of rows per file)

---

### 3. OciBudgetScheduler

**Purpose**: Collect budget status and alerts

**Frequency**: Configurable via properties
- **Production**: 7 minutes (defined in application-prod.properties:61)

**Configuration**:
```properties
# application-prod.properties
budget.scheduled.data.pull.cron.fixedRateMinutes=7
```

**Workflow**:
```
1. Check global toggle: scheduler_settings.is_enabled = 1 for "budget.scheduled.data.pull"
        ↓
2. Load enabled tenants: tenant_settings.is_budget_data_accessible = 1
        ↓
3. For each tenant:
   a. Find active subscriptions for organization (from subscription tables)
   b. Aggregate current month spend per tenant from cost table (CostRepository)
      - Query: SELECT SUM(cost) FROM cost WHERE tenant_id = :id AND date BETWEEN :start AND :end
   c. Evaluate BudgetNotification values (time-bounded thresholds)
      - Example: Budget = $10,000, Threshold = 80% → Alert if spend > $8,000
   d. Upsert BudgetNotificationReports (+ BudgetNotificationVerification for email targets)
        ↓
4. Log completion (budgets evaluated, alerts triggered)
```

**Database Entities**:
- BudgetNotification (see oci-library/entity/oci/BudgetNotification.java:45)
- BudgetNotificationEmail, BudgetNotificationValue
- BudgetNotificationReports, BudgetNotificationVerification
- BudgetCompartment (similar entities for compartment-level budgets)

**Important Notes**:
- Budgets are computed from internal cost table (NOT OCI Budgeting API)
- Two domains: Tenant-level budgets and Compartment-level budgets
- Notification delivery handled by separate scheduler (OciNotificationScheduler)

---

## 📊 What Data is Collected

### 1. Resources

**Source**: OCI Resource Search API

**OCI SDK Client Used**:
- ResourceSearchClient (see oci-monitor/service/OciResourceManagerService.java:17)

**Collection Method**:
```java
// OciResourceManagerService.searchManagableResources()
ResourceSearchClient searchClient = ResourceSearchClient.builder()
    .region(provider.getRegion())
    .build(provider);

StructuredSearchDetails searchDetails = StructuredSearchDetails.builder()
    .query("query instance, autonomousdatabase, exadata resources")
    .build();

SearchResourcesRequest searchRequest = SearchResourcesRequest.builder()
    .searchDetails(searchDetails)
    .tenantId(tenantOcid)
    .limit(1000)
    .build();

SearchResourcesResponse response = searchClient.searchResources(searchRequest);
List<ResourceSummary> resources = response.getResourceSummaryCollection().getItems();
```

**Data Collected**:
- **Resource OCID**: Unique identifier (e.g., ocid1.instance.oc1.eu-frankfurt-1.abc123...)
- **Resource Name**: Display name (e.g., prod-vm-01)
- **Resource Type**: Instance, Database, Exadata, etc.
- **Compartment ID**: OCI compartment OCID
- **Availability Domain**: Physical location
- **Lifecycle State**: RUNNING, STOPPED, TERMINATED, etc.
- **Freeform Tags**: Key-value pairs (JSON) - Used for SLA tag filtering
- **Defined Tags**: Namespace-based tags (JSON)
- **Creation Timestamp**: When resource was created

**Database Table**: **resource**

**Example Freeform Tags**:
```json
{
  "environment": "production",
  "service": "web-server",
  "team": "backend",
  "cost-center": "engineering"
}
```

**Usage**:
- Resources are linked to **oci_query** via **oci_query_resources** join table
- SLA module uses tags for multi-resource SLA filtering
- Resource lifecycle management (start/stop instances)

---

### 2. Metrics

**Source**: OCI Monitoring API (Metrics MQL)

**OCI SDK Client Used**:
- MonitoringClient (see oci-monitor/service/scheduler/OciMetricsSchedulerService.java:303)

**Collection Method**:
```java
// OciMetricsSchedulerService.pullMetricsData()
SummarizeMetricsDataDetails details = SummarizeMetricsDataDetails.builder()
    .namespace("oci_computeagent")  // Metric namespace
    .query("CpuUtilization[5m]{resourceId = \"ocid1.instance..\"}.mean()")  // MQL query
    .startTime(startDate)
    .endTime(endDate)
    .build();

SummarizeMetricsDataRequest request = SummarizeMetricsDataRequest.builder()
    .compartmentId(compartmentOcid)
    .summarizeMetricsDataDetails(details)
    .build();

SummarizeMetricsDataResponse response =
    monitoringClient.summarizeMetricsData(request);

// Parse response
for (MetricDataDetails metricData : response.getItems()) {
    for (AggregatedDatapoint datapoint : metricData.getAggregatedDatapoints()) {
        MetricResult result = new MetricResult();
        result.setResourceOcid(resourceOcid);  // STRING field
        result.setTime(datapoint.getTimestamp());
        result.setValue(datapoint.getValue());
        metricResultRepository.save(result);
    }
}
```

**Metric Namespaces** (Currently Configured):
| Namespace | Description | Metrics |
|-----------|-------------|---------|
| **oci_computeagent** | Compute instance metrics | CPU, Memory, Disk, Network |

**Metric Names** (Currently Monitored):
| Metric Name | Unit | Description |
|-------------|------|-------------|
| **CpuUtilization** | Percent | CPU usage percentage (0-100) |
| **MemoryUtilization** | Percent | Memory usage percentage (0-100) |
| **DiskBytesRead** | Bytes | Disk read throughput |
| **DiskBytesWritten** | Bytes | Disk write throughput |

**Statistic Types**:
- **mean()** - Average value over interval
- **max()** - Maximum value over interval
- **min()** - Minimum value over interval
- **sum()** - Sum of values over interval
- **count()** - Number of data points

**Data Collected**:
- **Timestamp**: When metric was measured (UTC)
- **Metric Value**: Numeric value (Double)
- **Resource OCID**: Which resource (STRING field, NOT FK)
- **Query ID**: Which OciQuery definition

**Database Table**: **metric_result**

**Table Structure**:
```sql
CREATE TABLE metric_result (
  id VARCHAR(255) PRIMARY KEY,
  resource_ocid VARCHAR(255),  -- STRING field (NOT foreign key)
  query_id VARCHAR(255),
  time DATETIME,
  value DOUBLE,
  created_at DATETIME,

  UNIQUE KEY idx_unique_metric (resource_ocid, query_id, time),
  INDEX idx_metric_result_resource_ocid_time (resource_ocid, time),
  INDEX idx_metric_result_query_time (query_id, time)
);
```

**Important**: **resource_ocid** is a STRING field, NOT a foreign key to **resource.id**. This allows metrics to exist even if resource is not yet synchronized.

**SQL Query Examples**:

```sql
-- 1) Count datapoints for a specific resource in a time window
SELECT COUNT(*)
FROM metric_result mr
WHERE mr.resource_ocid = 'ocid1.instance.oc1.eu-frankfurt-1.abc123...'
  AND mr.time BETWEEN '2025-11-01 00:00:00' AND '2025-11-30 23:59:59';

-- 2) Latest datapoint per resource for a given query
SELECT mr.*
FROM metric_result mr
JOIN (
  SELECT resource_ocid, MAX(time) AS max_time
  FROM metric_result
  WHERE query_id = 'query-uuid-123'
  GROUP BY resource_ocid
) t ON t.resource_ocid = mr.resource_ocid AND t.max_time = mr.time
WHERE mr.query_id = 'query-uuid-123';

-- 3) Join to resource table (via OCID string match)
SELECT mr.time, mr.value, r.name AS resource_name
FROM metric_result mr
LEFT JOIN resource r ON r.ocid = mr.resource_ocid
WHERE mr.time >= NOW() - INTERVAL 7 DAY
ORDER BY mr.time DESC;

-- WRONG (DO NOT USE):
-- SELECT ... FROM metric_result mr
-- JOIN resource r ON r.id = mr.resource_id  ← resource_id FK does not exist!
```

---

### 3. Cost & Billing

**Source**: OCI Object Storage (tenancy usage reports bucket/prefix)

**OCI SDK Client Used**:
- ObjectStorageClient (see oci-monitor/service/scheduler/OciCostSchedulerService.java:114)

**Collection Method**:
```java
// OciCostSchedulerService
ObjectStorageClient client = ObjectStorageClient.builder()
    .region(provider.getRegion())
    .build(provider);

// 1. List objects in bucket
ListObjectsRequest listRequest = ListObjectsRequest.builder()
    .namespaceName(costReportSettings.getNamespace())
    .bucketName(provider.getTenantId())
    .prefix(costReportSettings.getPrefix())
    .build();

ListObjectsResponse listResponse = client.listObjects(listRequest);

// 2. Download each cost report file
for (ObjectSummary obj : listResponse.getListObjects().getObjects()) {
    GetObjectRequest getRequest = GetObjectRequest.builder()
        .namespaceName(costReportSettings.getNamespace())
        .bucketName(provider.getTenantId())
        .objectName(obj.getName())
        .build();

    GetObjectResponse getResponse = client.getObject(getRequest);

    // 3. Validate MD5 checksum
    String expectedMd5 = obj.getMd5();
    String actualMd5 = calculateMd5(getResponse.getInputStream());
    if (!expectedMd5.equals(actualMd5)) {
        throw new ValidationException("MD5 mismatch");
    }

    // 4. Parse CSV/GZ file locally
    InputStream stream = getResponse.getInputStream();
    if (obj.getName().endsWith(".gz")) {
        stream = new GZIPInputStream(stream);
    }

    List<CostRow> rows = ociCostParser.parse(stream);

    // 5. Batch insert to database
    batchInsertUtil.insertCostRows(rows);
}
```

**Data Collected**:
- **Usage Date**: When service was used
- **Resource/Service Name**: Which OCI service (Compute, Storage, etc.)
- **Compartment ID**: OCI compartment
- **SKU**: Product code
- **Usage Amount**: Quantity used (e.g., 100 GB-hours)
- **Cost Amount**: Cost in currency
- **Currency Code**: USD, EUR, etc.

**Database Tables**:
- **cost_report_settings** - Configuration (namespace, bucket, prefix)
- **cost_reports** - File metadata (name, size, MD5, processed status)
- **cost** - Parsed usage/cost rows
- **cost_aggregate_reports** - Aggregated summaries

**CSV File Example**:
```csv
lineItem/tenantId,lineItem/resourceId,lineItem/compartmentPath,product/service,usage/billedQuantity,cost/myCost,...
ocid1.tenancy...,ocid1.instance...,/root/prod/,Compute - Standard - X7,100.0,12.50,...
```

**Update Frequency & Toggle**:
- Configurable via properties: **cost.scheduled.data.pull.*** and **cost.scheduled.data.parse.***
- Global toggle: **scheduler_settings.is_enabled** for **cost.scheduled.data.pull** and **cost.scheduled.data.parse**
- Tenant flag: **tenant_settings.is_cost_data_accessible**

---

### 4. Budgets

**Source**: Internal calculation from **cost** table (NOT OCI Budgeting API)

**What We Do**:
- Compute monthly spend from **cost** table (current month window)
- Compare to configured thresholds and produce budget reports/notifications
- Support two domains:
  - **Tenant-level budgets** (BudgetNotification)
  - **Compartment-level budgets** (BudgetCompartment)

**Schedulers & Toggles**:

| Scheduler | Property Key | DB Toggle | Tenant Flag |
|-----------|-------------|-----------|-------------|
| **Data Pull** | **budget.scheduled.data.pull.*** | **budget.scheduled.data.pull** | **is_budget_data_accessible** |
| **Data Pull (Compartment)** | **budget.compartment.scheduled.data.pull.*** | **budget.compartment.scheduled.data.pull** | **is_budget_compartment_data_accessible** |
| **Notification (Tenant)** | **budget.scheduled.notification.*** | **budget.scheduled.notification** | N/A |
| **Notification (Compartment)** | **budget.compartment.scheduled.notification.*** | **budget.compartment.scheduled.notification** | N/A |

**Data Flow (Tenant Budgets)**:
```
1. Find active subscriptions for organization
        ↓
2. Aggregate current month spend per tenant from cost table
   Query: SELECT SUM(cost) FROM cost WHERE tenant_id = :id AND date BETWEEN :monthStart AND :monthEnd
        ↓
3. Evaluate BudgetNotification values (time-bounded thresholds)
   - Budget = $10,000
   - Threshold = 80%
   - Actual Spend = $8,500
   - Result: ALERT (over 80% threshold)
        ↓
4. Upsert BudgetNotificationReports (+ BudgetNotificationVerification for email targets)
        ↓
5. Send email notifications (handled by OciNotificationScheduler)
```

**Database Entities**:

**Tenant Budgets**:
- **BudgetNotification** - Budget definition (amount, currency)
- **BudgetNotificationEmail** - Email recipients
- **BudgetNotificationValue** - Threshold values (e.g., 50%, 80%, 100%)
- **BudgetNotificationReports** - Computed budget status
- **BudgetNotificationVerification** - Email verification tracking

**Compartment Budgets**:
- **BudgetCompartment** - Budget definition per compartment
- **BudgetCompartmentEmail** - Email recipients
- **BudgetCompartmentValue** - Threshold values
- **BudgetCompartmentReports** - Computed budget status
- **BudgetCompartmentVerification** - Email verification tracking

**Code References**:
- oci-monitor/scheduler/OciBudgetScheduler.java
- oci-monitor/service/scheduler/OciBudgetSchedulerService.java
- oci-monitor/scheduler/OciBudgetCompartmentScheduler.java
- oci-monitor/service/scheduler/OciBudgetCompartmentSchedulerService.java

**Important**: There is NO **budget** table. Budgets are modeled via the entities above and computed from **cost** table.

---

## 🗄️ Database Schema

### Data Collection Tables

#### **tenant**

Stores OCI tenancy information and authentication details.

<details>
<summary>📋 Columns</summary>

**Columns**:
- **id** - VARCHAR(255) - UUID primary key
- **ocid** - VARCHAR(255) - OCI Tenancy OCID
- **name** - VARCHAR(255) - Tenant display name
- **organization_id** - VARCHAR(255) - Organization reference
- **api_key_path** - VARCHAR(500) - Path to private key file (e.g., /opt/oci/keys/tenant-123.pem)
- **fingerprint** - VARCHAR(255) - Public key fingerprint
- **user_ocid** - VARCHAR(255) - OCI user OCID
- **region** - VARCHAR(50) - OCI region (e.g., us-ashburn-1)
- **created_at**, **created_by**, **updated_at**, **updated_by** - Audit fields

</details>

<details>
<summary>🔍 Indexes</summary>

**Indexes**:
- PRIMARY KEY (**id**)
- UNIQUE KEY (**ocid**)

</details>

---

#### **tenant_settings**

Controls what data should be collected for each tenant. Acts as per-tenant toggle.

<details>
<summary>📋 Columns</summary>

**Columns**:
- **id** - VARCHAR(255) - UUID primary key
- **tenant_id** - VARCHAR(255) - FK to tenant
- **is_cost_data_accessible** - TINYINT(1) - Enable cost collection
- **is_aggregate_data_accessible** - TINYINT(1) - Enable aggregates
- **is_calculate_consumption_data_accessible** - TINYINT(1) - Enable consumption calculations
- **is_consumption_data_accessible** - TINYINT(1) - Enable consumption data
- **is_metrics_data_accessible** - TINYINT(1) - **Enable metrics collection** (required for SLA)
- **is_budget_data_accessible** - TINYINT(1) - Enable budget monitoring
- **is_budget_compartment_data_accessible** - TINYINT(1) - Enable compartment budgets
- **is_subscription_data_accessible** - TINYINT(1) - Enable subscription data
- **is_sc_notification_enabled** - TINYINT(1) - Enable service catalog notifications
- **created_at**, **created_by**, **updated_at**, **updated_by** - Audit fields

**Important**: Schedulers check BOTH global toggle (**scheduler_settings**) AND tenant-specific settings.

</details>

<details>
<summary>🔍 Indexes</summary>

**Indexes**:
- PRIMARY KEY (**id**)
- UNIQUE KEY (**tenant_id**)

</details>

**Example**:
```sql
-- Enable metrics collection for tenant
UPDATE tenant_settings
SET is_metrics_data_accessible = 1,
    updated_at = NOW(),
    updated_by = 'admin@example.com'
WHERE tenant_id = 'tenant-uuid-123';
```

---

#### **resource**

Stores OCI resources (VM instances, databases, etc.)

<details>
<summary>📋 Columns</summary>

**Columns**:
- **id** - VARCHAR(255) - UUID primary key
- **ocid** - VARCHAR(255) - OCI Resource OCID (e.g., ocid1.instance.oc1...)
- **name** - VARCHAR(255) - Resource display name
- **description** - TEXT - Resource description
- **organization_id** - VARCHAR(255) - Organization reference
- **tenant_id** - VARCHAR(255) - FK to tenant
- **compartment_id** - VARCHAR(255) - OCI compartment OCID
- **resourcetype_id** - VARCHAR(255) - Resource type reference
- **freeform_tags** - JSON - Freeform tags (key-value pairs)
- **defined_tags** - JSON - Defined tags (namespace-based)
- **lifecycle_state** - VARCHAR(50) - RUNNING, STOPPED, TERMINATED, etc.
- **availability_domain** - VARCHAR(255) - Physical location
- **created_at**, **created_by**, **updated_at**, **updated_by** - Audit fields

</details>

<details>
<summary>🔍 Indexes</summary>

**Indexes**:
- PRIMARY KEY (**id**)
- UNIQUE KEY (**ocid**)
- INDEX (**tenant_id**)
- INDEX (**compartment_id**)

</details>

**Example Freeform Tags**:
```json
{
  "environment": "production",
  "service": "web-server",
  "team": "backend",
  "cost-center": "engineering"
}
```

**Usage**:
- Resources linked to **oci_query** via **oci_query_resources** join table
- SLA module uses **freeform_tags** for multi-resource SLA filtering
- **resource.ocid** matched against **metric_result.resource_ocid** (STRING field)

---

#### **oci_query**

Defines which metrics to collect from OCI.

<details>
<summary>📋 Columns</summary>

**Columns**:
- **id** - VARCHAR(255) - UUID primary key
- **name** - VARCHAR(255) - Query display name
- **tenant_id** - VARCHAR(255) - FK to tenant
- **compartment_id** - VARCHAR(255) - OCI compartment OCID
- **metric_namespace** - VARCHAR(255) - Metric namespace (e.g., oci_computeagent)
- **metric_name** - VARCHAR(255) - Metric name (e.g., CpuUtilization)
- **statistic_type** - INT - Aggregation function (1=mean, 2=max, 3=min, 4=sum, 5=count)
- **unit_type** - INT - Unit type
- **start_time_offset** - INT - Hours back to start collecting
- **interval_minutes** - INT - Data point interval (e.g., 5 minutes)
- **is_active** - TINYINT(1) - Whether query is active
- **created_at**, **created_by**, **updated_at**, **updated_by** - Audit fields

</details>

<details>
<summary>🔍 Indexes</summary>

**Indexes**:
- PRIMARY KEY (**id**)
- INDEX (**tenant_id**)
- INDEX (**metric_namespace**, **metric_name**)

</details>

<details>
<summary>🔗 Many-to-Many Relationship</summary>

**Many-to-Many Relationship**:
- **oci_query** ↔ **resource** via **oci_query_resources** join table

</details>

**Example**:
```sql
INSERT INTO oci_query (id, name, tenant_id, metric_namespace, metric_name, statistic_type, interval_minutes, is_active)
VALUES ('query-uuid-123', 'CPU Utilization', 'tenant-uuid-456', 'oci_computeagent', 'CpuUtilization', 1, 5, 1);

-- Link query to resources
INSERT INTO oci_query_resources (oci_queries_id, oci_resources_id)
VALUES ('query-uuid-123', 'resource-uuid-789');
```

---

#### **metric_result**

Stores collected metric data points.

<details>
<summary>📋 Columns</summary>

**Columns**:
- **id** - VARCHAR(255) - UUID primary key
- **resource_ocid** - VARCHAR(255) - **STRING field, NOT FK** (OCI resource OCID)
- **query_id** - VARCHAR(255) - FK to oci_query
- **time** - DATETIME - Timestamp of metric data point (UTC)
- **value** - DOUBLE - Metric value
- **created_at** - DATETIME - When record was created in DB

</details>

<details>
<summary>🔍 Indexes</summary>

**Indexes**:
- PRIMARY KEY (**id**)
- UNIQUE KEY **idx_unique_metric** (**resource_ocid**, **query_id**, **time**) - Prevents duplicates
- INDEX **idx_metric_result_resource_ocid_time** (**resource_ocid**, **time**) - Fast SLA queries
- INDEX **idx_metric_result_query_time** (**query_id**, **time**) - Fast query-based queries

</details>

**Important**:
- **resource_ocid** is a **STRING field**, NOT a foreign key to **resource.id**
- This allows metrics to exist even if resource not yet synchronized
- Join to **resource** table via OCID string matching: LEFT JOIN resource r ON r.ocid = mr.resource_ocid

**SQL Examples**:

```sql
-- Filter by resource_ocid STRING
SELECT COUNT(*) AS total_datapoints, DATE(time) AS date
FROM metric_result mr
WHERE mr.resource_ocid = 'ocid1.instance.oc1.eu-frankfurt-1.abc123...'
  AND time > NOW() - INTERVAL 7 DAY
GROUP BY DATE(time)
ORDER BY date DESC;

-- Join with resource table via OCID string matching
SELECT
    r.name AS resource_name,
    mr.time,
    mr.value
FROM metric_result mr
LEFT JOIN resource r ON r.ocid = mr.resource_ocid
WHERE mr.time > NOW() - INTERVAL 7 DAY
ORDER BY mr.time DESC;

-- WRONG (DO NOT USE):
-- SELECT ... FROM metric_result mr
-- JOIN resource r ON r.id = mr.resource_id  ← resource_id FK does not exist!
```

---

#### **oci_query_reports**

Tracks sync status for each query + resource combination.

<details>
<summary>📋 Columns</summary>

**Columns**:
- **id** - VARCHAR(255) - UUID primary key
- **query_id** - VARCHAR(255) - FK to oci_query
- **resource_id** - VARCHAR(255) - FK to resource
- **start_date** - DATETIME - Sync window start
- **end_date** - DATETIME - Sync window end
- **status** - VARCHAR(50) - PROCESSED, ERROR, etc.
- **error_message** - TEXT - Error details if failed
- **created_at** - DATETIME - When sync started

</details>

<details>
<summary>🔍 Indexes</summary>

**Indexes**:
- PRIMARY KEY (**id**)
- INDEX (**query_id**, **resource_id**)
- INDEX (**end_date**)

</details>

**Purpose**: Prevents duplicate syncs, tracks last processed interval.

**Example**:
```sql
-- Check last sync status for a query + resource
SELECT * FROM oci_query_reports
WHERE query_id = 'query-uuid-123'
  AND resource_id = 'resource-uuid-789'
ORDER BY end_date DESC
LIMIT 1;
```

---

#### **scheduler_settings**

Global toggle for enabling/disabling schedulers.

<details>
<summary>📋 Columns</summary>

**Columns**:
- **scheduler_task_name** - VARCHAR(255) - Primary key (e.g., metrics.scheduled.data.pull)
- **is_enabled** - TINYINT(1) - 1 = enabled, 0 = disabled
- **created_at**, **created_by**, **updated_at**, **updated_by** - Audit fields
- **version** - INT - Optimistic locking

</details>

**Current Configuration**:

| Scheduler Task Name | Enabled | Purpose |
|---------------------|---------|---------|
| **metrics.scheduled.data.pull** | ✅ Yes (1) | Pull metrics from OCI Monitoring API |
| **budget.scheduled.data.pull** | ✅ Yes (1) | Pull budget information |
| **consumption.scheduled.data.pull** | ✅ Yes (1) | Pull consumption data |
| **metrics.scheduled.notification** | ✅ Yes (1) | Send metric notifications |
| **sc.scheduled.notification** | ✅ Yes (1) | Service catalog notifications |
| **budget.scheduled.notification** | ✅ Yes (1) | Send budget notifications |
| **cost.scheduled.data.pull** | ❌ No (0) | Pull cost reports (disabled) |
| **cost.scheduled.data.parse** | ❌ No (0) | Parse cost reports (disabled) |

**Usage in Code**:
```java
// oci-monitor/service/scheduler/SchedulerToggleService.java:15
if (!schedulerToggleService.isTaskEnabled("metrics.scheduled.data.pull")) {
    log.info("Metrics scheduler is disabled globally. Skipping execution.");
    return;
}
```

**SQL Examples**:
```sql
-- Enable global scheduler
UPDATE scheduler_settings
SET is_enabled = 1, updated_at = NOW(), updated_by = 'admin@example.com'
WHERE scheduler_task_name = 'metrics.scheduled.data.pull';

-- Disable global scheduler
UPDATE scheduler_settings
SET is_enabled = 0, updated_at = NOW(), updated_by = 'admin@example.com'
WHERE scheduler_task_name = 'cost.scheduled.data.pull';

-- Check all scheduler statuses
SELECT scheduler_task_name, is_enabled
FROM scheduler_settings
ORDER BY scheduler_task_name;
```

---

#### Cost & Billing Tables

**cost_report_settings**:
- Configuration for cost report location (namespace, bucket, prefix)

**cost_reports**:
- Metadata for each cost report file (name, size, MD5, processed status)

**cost**:
- Parsed cost/usage rows (date, resource, amount, cost, currency)

**cost_aggregate_reports**:
- Aggregated cost summaries

---

## 🔧 OCI SDK Usage

### Dependencies

**Maven** (oci-monitor/pom.xml):
```xml
<!-- Selected OCI SDK modules used by oci-monitor -->
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-monitoring</artifactId>
</dependency>
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-objectstorage</artifactId>
</dependency>
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-resourcesearch</artifactId>
</dependency>
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-identity</artifactId>
</dependency>
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-core</artifactId>
</dependency>
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-database</artifactId>
</dependency>
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-tenantmanagercontrolplane</artifactId>
</dependency>
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-onesubscription</artifactId>
</dependency>
```

### SDK Clients Used

#### ✅ Actively Used Clients

| Client | Purpose | Code Location |
|--------|---------|---------------|
| **MonitoringClient** | Fetch metrics (CPU, Memory, Disk, Network) | oci-monitor/service/scheduler/OciMetricsSchedulerService.java:303 |
| **ObjectStorageClient** | Download cost reports from Object Storage | oci-monitor/service/scheduler/OciCostSchedulerService.java:114 |
| **ResourceSearchClient** | Discover resources (VMs, databases, etc.) | oci-monitor/service/OciResourceManagerService.java:17 |
| **IdentityClient** | List compartments, users, groups | oci-monitor/service/OciQueryService.java:65 |
| **ComputeClient** | Start/stop compute instances | oci-monitor/service/ociresource/OciResourceInstance.java:25 |
| **DatabaseClient** | Manage autonomous databases, Exadata | oci-monitor/service/ociresource/OciResourceAutonomousDatabase.java:27 |
| **TenantManagerControlPlane Clients** | Organization and subscriptions (tenant manager) | oci-monitor/service/OciSubscriptionService.java:30,49 |
| **OneSubscription Clients** | Subscription and organization subscription (billing) | oci-monitor/service/scheduler/OciConsumptionSchedulerService.java:509,529 |

#### ❌ Not Currently Used

The following OCI SDK clients are available but **not currently used** in this application due to architectural decisions:

##### **UsageClient** (Oracle Usage API)

**What is it?**
- Part of OCI Java SDK (com.oracle.oci.sdk:oci-java-sdk-usage)
- Provides programmatic access to OCI Usage API for cost and usage data retrieval
- Alternative method for fetching billing/cost information

**Capabilities:**
- Query usage and cost data by date range, compartment, service
- Retrieve aggregated cost summaries
- Access usage statistics for resources
- Get detailed line-item cost breakdowns

**Why not used in this application?**
- **Cost reports are NOT available via UsageClient API** - Oracle does not expose full detailed cost reports through the API
- Instead, OCI generates **CSV cost reports** and uploads them to **Object Storage buckets**
- Our application uses **ObjectStorageClient** to download these pre-generated CSV files directly
- CSV approach provides:
  - ✅ Complete line-item detail (thousands of rows per day)
  - ✅ Historical data for entire billing period
  - ✅ Consistent format across tenancies
  - ✅ Better performance (batch file download vs many API calls)

**What we could potentially use it for:**
- Real-time cost monitoring dashboards
- Quick cost queries without downloading full CSV files
- Programmatic cost alerts based on thresholds

**Current implementation:** See OciCostReportScheduler.java:152 - uses ObjectStorageClient instead

---

##### **BudgetingClient** (Oracle Budgets API)

**What is it?**
- Part of OCI Java SDK (com.oracle.oci.sdk:oci-java-sdk-budget)
- Provides programmatic access to OCI Budgets service
- Enables creation and management of cost budgets

**Capabilities:**
- Create, update, delete budgets programmatically
- Set budget thresholds and alert rules
- Query budget status and spending vs budget
- Configure budget alert recipients
- Track historical budget performance

**Why not used in this application?**
- Our application **computes budgets internally** from the cost data already collected in the database
- Budget logic is handled by OciBudgetSchedulerService.java and OciBudgetCompartmentSchedulerService.java
- We use the **cost** table (populated from CSV reports) to calculate spending
- This approach provides:
  - ✅ Custom budget logic and calculations
  - ✅ Compartment-level budgets with custom rules
  - ✅ Integration with internal notification system
  - ✅ No dependency on OCI Budget service configuration

**What we could potentially use it for:**
- Syncing budgets created in OCI Console into our application
- Two-way budget synchronization (create budgets in app → push to OCI)
- Leveraging OCI's native budget alerting system
- Importing existing budget configurations from OCI tenancies

**Current implementation:** See OciBudgetSchedulerService.java:89 - computes from internal cost table

---

### Client Usage Examples

#### MonitoringClient

**Purpose**: Fetch performance metrics

**Code**:
```java
MonitoringClient client = MonitoringClient.builder()
    .region(Region.US_ASHBURN_1)
    .build(authProvider);

SummarizeMetricsDataRequest request = SummarizeMetricsDataRequest.builder()
    .compartmentId(compartmentOcid)
    .summarizeMetricsDataDetails(
        SummarizeMetricsDataDetails.builder()
            .namespace("oci_computeagent")
            .query("CpuUtilization[5m].mean()")
            .startTime(startTime)
            .endTime(endTime)
            .build()
    ).build();

SummarizeMetricsDataResponse response = client.summarizeMetricsData(request);
```

---

#### ObjectStorageClient

**Purpose**: Download cost report files

**Code**:
```java
ObjectStorageClient client = ObjectStorageClient.builder()
    .region(Region.US_ASHBURN_1)
    .build(authProvider);

// List objects
ListObjectsRequest listRequest = ListObjectsRequest.builder()
    .namespaceName(namespace)
    .bucketName(costReportsBucket)
    .build();

ListObjectsResponse listResponse = client.listObjects(listRequest);

// Download object
for (ObjectSummary obj : listResponse.getListObjects().getObjects()) {
    GetObjectRequest getRequest = GetObjectRequest.builder()
        .namespaceName(namespace)
        .bucketName(costReportsBucket)
        .objectName(obj.getName())
        .build();

    GetObjectResponse getResponse = client.getObject(getRequest);
    // Parse CSV/GZ file from getResponse.getInputStream()
}
```

---

#### ResourceSearchClient

**Purpose**: Discover and search resources

**Code**:
```java
ResourceSearchClient client = ResourceSearchClient.builder()
    .region(Region.US_ASHBURN_1)
    .build(authProvider);

StructuredSearchDetails searchDetails = StructuredSearchDetails.builder()
    .query("query instance, autonomousdatabase resources")
    .build();

SearchResourcesRequest request = SearchResourcesRequest.builder()
    .searchDetails(searchDetails)
    .tenantId(tenantOcid)
    .limit(1000)
    .build();

SearchResourcesResponse response = client.searchResources(request);
List<ResourceSummary> resources = response.getResourceSummaryCollection().getItems();
```

---

## ⚙️ Configuration

### Application Properties

**Metrics Scheduler**:
```properties
# application-prod.properties
metrics.scheduled.data.pull.cron.initialDelayMinutes=2
metrics.scheduled.data.pull.cron.fixedRateMinutes=11  # Production: 11 minutes

# application-local.properties
metrics.scheduled.data.pull.cron.fixedRateMinutes=5   # Local: 5 minutes
```

**Budget Scheduler**:
```properties
# application-prod.properties
budget.scheduled.data.pull.cron.fixedRateMinutes=7  # Production: 7 minutes
```

**Data Scheduler** (orchestrator):
```properties
# application.properties
data.scheduled.cron.initialDelayMinutes=5
data.scheduled.cron.fixedRateMinutes=360  # 6 hours
```

### Scheduler Toggle Logic

**Two-Level Control**:
1. **Global Toggle**: **scheduler_settings** table
2. **Tenant Settings**: **tenant_settings** table

**Example**:
```java
// STEP 1: Check global toggle
if (!schedulerToggleService.isTaskEnabled("metrics.scheduled.data.pull")) {
    return; // EXIT - scheduler disabled globally
}

// STEP 2: Load only enabled tenants
// findAllMetricsTenants() returns tenants where:
//   tenant_settings.is_metrics_data_accessible = 1
List<Tenant> tenants = ociTenancyService.findAllMetricsTenants();

// STEP 3: Process each enabled tenant
for (Tenant tenant : tenants) {
    ociMetricsSchedulerService.pullMetricsData(tenant, auth);
}
```

**SQL Examples**:
```sql
-- Enable global scheduler
UPDATE scheduler_settings
SET is_enabled = 1, updated_at = NOW(), updated_by = 'admin@example.com'
WHERE scheduler_task_name = 'metrics.scheduled.data.pull';

-- Enable metrics for specific tenant
UPDATE tenant_settings
SET is_metrics_data_accessible = 1,
    updated_at = NOW(),
    updated_by = 'admin@example.com'
WHERE tenant_id = 'tenant-uuid-123';
```

### Schedulers & Toggles Index

| Scheduler | Property Key | DB Toggle | Tenant Flag | Code |
|-----------|-------------|-----------|-------------|------|
| **Metrics Pull** | **metrics.scheduled.data.pull.cron.*** | **metrics.scheduled.data.pull** | **is_metrics_data_accessible** | **OciMetricsScheduler** |
| **Metrics Notification** | **metrics.scheduled.notification.cron.*** | **metrics.scheduled.notification** | N/A | **OciNotificationScheduler** |
| **Budget Pull** | **budget.scheduled.data.pull.cron.*** | **budget.scheduled.data.pull** | **is_budget_data_accessible** | **OciBudgetScheduler** |
| **Budget Compartment Pull** | **budget.compartment.scheduled.data.pull.cron.*** | **budget.compartment.scheduled.data.pull** | **is_budget_compartment_data_accessible** | **OciBudgetCompartmentScheduler** |
| **Cost Pull** | **cost.scheduled.data.pull.cron.*** | **cost.scheduled.data.pull** | **is_cost_data_accessible** | **OciCostScheduler** |
| **Cost Parse** | **cost.scheduled.data.parse.cron.*** | **cost.scheduled.data.parse** | **is_cost_data_accessible** | **OciCostScheduler** |

---

## 🔍 Troubleshooting

### Check Scheduler Status

**Via Logs**:
```bash
# Metrics scheduler
grep "OciMetricsScheduler" /var/log/oci-monitor/application.log | tail -20

# Cost scheduler
grep "OciCostScheduler" /var/log/oci-monitor/application.log | tail -20
```

**Via Database**:
```sql
-- Check global scheduler status
SELECT scheduler_task_name, is_enabled
FROM scheduler_settings
ORDER BY scheduler_task_name;

-- Check tenant monitoring settings
SELECT
    t.name AS tenant_name,
    ts.is_metrics_data_accessible,
    ts.is_cost_data_accessible,
    ts.is_budget_data_accessible
FROM tenant t
JOIN tenant_settings ts ON ts.tenant_id = t.id
ORDER BY t.name;

-- Check last sync for metrics
SELECT
    q.metric_namespace,
    q.metric_name,
    r.name AS resource_name,
    qr.end_date AS last_sync,
    qr.status
FROM oci_query_reports qr
JOIN oci_query q ON q.id = qr.query_id
JOIN resource r ON r.id = qr.resource_id
ORDER BY qr.end_date DESC
LIMIT 20;
```

### Current System Status (How to Query)

Environment state varies; use the queries below to inspect your setup.

**Schedulers (global)**:
```sql
SELECT
  SUM(CASE WHEN is_enabled THEN 1 ELSE 0 END) AS enabled,
  COUNT(*) AS total
FROM scheduler_settings;

-- Per-scheduler details
SELECT scheduler_task_name, is_enabled FROM scheduler_settings ORDER BY scheduler_task_name;
```

**Per-tenant monitoring flags**:
```sql
-- Metrics-enabled tenants
SELECT COUNT(*) AS metrics_enabled
FROM tenant_settings
WHERE is_metrics_data_accessible = 1;

-- Budget/Budget compartment/Cost flags
SELECT
  SUM(is_budget_data_accessible=1) AS budget_enabled,
  SUM(is_budget_compartment_data_accessible=1) AS budget_compartment_enabled,
  SUM(is_cost_data_accessible=1) AS cost_enabled
FROM tenant_settings;
```

**Metrics footprint**:
```sql
-- Distinct namespaces and metric names (based on collected data)
SELECT COUNT(DISTINCT metric_namespace) AS namespaces,
       COUNT(DISTINCT metric_name) AS metric_names
FROM metric_result;

-- Active OciQuery definitions
SELECT COUNT(*) AS active_queries FROM oci_query WHERE is_active = 1;
```

**Cost/Billing footprint**:
```sql
-- Available cost report files
SELECT COUNT(*) AS cost_files FROM cost_reports;

-- Parsed cost rows
SELECT COUNT(*) AS cost_rows FROM cost;
```

**Metric data points collected**:
```sql
-- Uses resource_ocid STRING field, not FK
SELECT COUNT(*) AS total_datapoints, DATE(time) AS date
FROM metric_result mr
WHERE time > NOW() - INTERVAL 7 DAY
GROUP BY DATE(time)
ORDER BY date DESC;

-- Join with resource table via OCID string matching
SELECT
    COUNT(*) AS total_datapoints,
    DATE(mr.time) AS date,
    r.name AS resource_name
FROM metric_result mr
LEFT JOIN resource r ON r.ocid = mr.resource_ocid
WHERE mr.time > NOW() - INTERVAL 7 DAY
GROUP BY DATE(mr.time), r.name
ORDER BY date DESC, resource_name;
```

---

### Common Issues

#### 1. No Metrics Being Collected

**Symptoms**:
- No rows in **metric_result** table
- Reports show 0 data points

**Checks**:
- ✅ Global scheduler enabled: **scheduler_settings.is_enabled = 1** for **metrics.scheduled.data.pull**
- ✅ Tenant settings: **tenant_settings.is_metrics_data_accessible = 1**
- ✅ OCI authentication: Valid API key and credentials
- ✅ OciQuery exists for the resource
- ✅ Resources are linked to OciQuery (via **oci_query_resources** join table)

**Logs**:
```
OciMetricsScheduler:: Metrics data pull scheduler is disabled. Skipping execution.
```

**Solution**:
```sql
-- Enable global toggle
UPDATE scheduler_settings SET is_enabled = 1 WHERE scheduler_task_name = 'metrics.scheduled.data.pull';

-- Enable tenant setting
UPDATE tenant_settings SET is_metrics_data_accessible = 1 WHERE tenant_id = 'tenant-uuid';
```

---

#### 2. Authentication Errors

**Symptoms**:
```
OciMetricsScheduler:: OciAuthenticationDetailsProvider cannot be created/found for Tenant: <ocid> reason: <error>
```

**Fixes**:
- Verify API key path is correct (**tenant.api_key_path**)
- Check private key file permissions (must be readable by app user: chmod 600 /path/to/key.pem)
- Verify user OCID, tenancy OCID, fingerprint are correct
- Check region is valid OCI region

---

#### 3. No Data in metric_result Table

**Checks**:
```sql
-- Check if OciQuery exists
SELECT COUNT(*) FROM oci_query WHERE is_active = 1;

-- Check if resources are linked to queries
SELECT
    q.id,
    q.metric_name,
    COUNT(DISTINCT r.id) AS resource_count
FROM oci_query q
LEFT JOIN oci_query_resources qr ON qr.oci_queries_id = q.id
LEFT JOIN resource r ON r.id = qr.oci_resources_id
GROUP BY q.id, q.metric_name;

-- Check sync status
SELECT * FROM oci_query_reports
WHERE status = 'ERROR'
ORDER BY created_at DESC
LIMIT 10;
```

**Solutions**:
- Create **oci_query** definitions for desired metrics
- Link resources to queries via **oci_query_resources** table
- Check **oci_query_reports** for error messages

---
