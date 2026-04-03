# OCI SLA Management Module - Detailed Architecture

**Module**: oci-api, oci-monitor
**Purpose**: Service Level Agreement (SLA) Monitoring and Compliance Tracking
**Author**: Development Team
**Last Updated**: 2025-11-13
**Version**: 2.2 (Complete SLA Module with Resource Filtering Logic)

---

## 📋 Table of Contents

1. [SLA Module Overview](#sla-module-overview)
2. [Resource Filtering and Selection Logic](#resource-filtering-and-selection-logic)
3. [Database Architecture](#database-architecture)
4. [Understanding SLA Thresholds and Targets](#understanding-sla-thresholds-and-targets)
5. [SLA Computation Workflow](#sla-computation-workflow)
6. [Scheduler Architecture](#scheduler-architecture)
7. [SLA Scheduled Reports](#sla-scheduled-reports)
8. [SLA Excluded Downtime Management](#sla-excluded-downtime-management)
9. [Manual Trigger API](#manual-trigger-api)
10. [Feature Implementation Matrix](#feature-implementation-matrix)
11. [PDF Export Technology Stack](#pdf-export-technology-stack)
12. [Configuration](#configuration)
13. [API Testing with cURL](#api-testing-with-curl)
14. [Troubleshooting](#troubleshooting)

---

## 📖 SLA Module Overview

The SLA module enables users to define service level agreements for OCI resources and automatically monitor compliance against those agreements. The system tracks metrics, detects breaches, calculates penalties, and generates comprehensive reports.

### Key Capabilities

1. **SLA Definition Management**: Create and manage SLA rules with thresholds, targets, and schedules
2. **Automated Monitoring**: Periodic compliance calculation on CRON schedules
3. **Breach Detection**: Automatic identification of SLA violations
4. **Penalty Calculation**: Tiered financial penalties based on compliance levels
5. **Report Generation**: On-demand reports with compliance statistics
6. **Multi-Format Export**: CSV and PDF export capabilities
7. **Visual Analytics**: Chart.js dashboard with compliance gauges and trend charts

### Module Split

| Feature | Module | Why |
|---------|--------|-----|
| **SLA Definition CRUD** | oci-api | User-facing REST API |
| **SLA Computation** | oci-monitor | Batch processing on schedule |
| **Report Generation** | oci-api | On-demand user requests |
| **CSV/PDF Export** | oci-api | On-demand file downloads |

---

## 🔍 Resource Filtering and Selection Logic

When creating an SLA Definition, the system implements sophisticated resource filtering to ensure only appropriate resources are available for SLA monitoring. This section explains the complete flow from frontend to database.

### Overview

**Key Filtering Criteria:**
1. **Organization ID** (Required) - Resources from selected organization/tenant
2. **SLA Monitoreable Flag** (Required) - Only resources with monitoreable resource types
3. **Tenant ID** (Optional) - Additional filtering within organization
4. **Compartment ID** (Optional) - Additional filtering by compartment

### Frontend Flow

#### Step 1: User Selects Organization

```typescript
// SlaFormPage.tsx
const { data: organizations } = useOrganizations()

// User selects organization from dropdown
formData.tenantId = selectedOrganizationId
```

#### Step 2: Automatic Resource Loading

```typescript
// SlaFormPage.tsx:100-103
const { data: resources = [], isLoading: isLoadingResources } = useResources(
    {
        organizationId: formData.tenantId,  // Selected organization
        slaMonitoreable: true                // Only SLA-capable resources
    },
    { enabled: Boolean(formData.tenantId) }  // Load only when org selected
)
```

**Parameters:**
- `organizationId`: UUID of selected organization
- `slaMonitoreable: true`: Filters only resources whose ResourceType has `sla_monitoreable = true`
- `enabled`: Query executes ONLY when organization is selected

#### Step 3: API Service Call

```typescript
// services/resourceService.ts
async search(params?: ResourceSearchParams): Promise<ResourceDto[]> {
    const response = await api.get<ResourceDto[]>(
        '/api/codebook/resources',
        { params }  // Query parameters
    )
    return response.data
}
```

**HTTP Request:**
```http
GET /api/codebook/resources?organizationId={uuid}&slaMonitoreable=true
Authorization: Bearer {jwt-token}
```

### Backend Flow

#### Step 1: REST Controller

```java
// ResourcesController.java
@GetMapping("/api/codebook/resources")
public List<ResourceDto> searchResources(
    @RequestParam(required = false) String organizationId,
    @RequestParam(required = false) String tenantId,
    @RequestParam(required = false) String compartmentId,
    @RequestParam(required = false) Boolean slaMonitoreable) {

    List<ResourceDtoInterface> resources = resourceService.search(
        organizationId, tenantId, compartmentId, slaMonitoreable
    );

    return ResourceInterfaceMapper.INSTANCE
        .resourceDtoInterfacesToResourceDtos(resources);
}
```

**Endpoint:** `GET /api/codebook/resources`

**Query Parameters:**
- `organizationId` (optional) - Filter by organization UUID
- `tenantId` (optional) - Filter by tenant UUID
- `compartmentId` (optional) - Filter by compartment UUID
- `slaMonitoreable` (optional) - Filter by SLA capability

#### Step 2: Service Layer - Authorization

```java
// ResourceService.java:46-57
public List<ResourceDtoInterface> search(
    String organizationId,
    String tenantId,
    String compartmentId,
    Boolean slaMonitoreable) {

    // SECURITY CHECK
    if (!AuthHelper.currentUserIsSuperadminOrSysadmin()) {
        String organization = AuthHelper.getCurrentUserPrincipal()
            .getUser()
            .getOrganization()
            .getId()
            .toString();

        if (organization != null) {
            // FORCE user's organization
            organizationId = organization;
        } else {
            throw new ApiValidationException(
                "User has no privileges to view resources from other organizations."
            );
        }
    }

    return resourceRepository.findAllData(
        organizationId, tenantId, compartmentId, slaMonitoreable
    );
}
```

**Authorization Logic:**
- ✅ **Superadmin/Sysadmin**: Can view resources from ANY organization
- ❌ **Regular User**: Can ONLY view resources from their own organization
  - `organizationId` is **forced** to user's organization
  - If user has no organization → Exception

#### Step 3: Repository Layer - SQL Query

```java
// ResourceRepository.java
@Query(value = """
    SELECT
        r.id AS id,
        r.ocid AS ocid,
        r.name AS name,
        r.description AS description,
        o.id AS organizationId,
        o.name AS organizationName,
        o.shortname AS organizationShortName,
        t.id AS tenantId,
        t.ocid AS tenantOcid,
        t.name AS tenantName,
        c.id AS compartmentId,
        c.ocid AS compartmentOcid,
        c.name AS compartmentName,
        rt.id AS resourceTypeId,
        rt.name AS resourceTypeName,
        r.created_at AS createdAt,
        r.updated_at AS updatedAt,
        r.created_by AS createdBy,
        r.updated_by AS updatedBy
    FROM ociapp.resource r
    LEFT JOIN ociapp.organization o ON r.organization_id = o.id
    LEFT JOIN ociapp.tenant t ON r.tenant_id = t.id
    LEFT JOIN ociapp.compartment c ON r.compartment_id = c.id
    LEFT JOIN ociapp.resource_type rt ON r.resourcetype_id = rt.id
    WHERE
        (:organizationId IS NULL OR r.organization_id = :organizationId) AND
        (:tenantId IS NULL OR r.tenant_id = :tenantId) AND
        (:compartmentId IS NULL OR r.compartment_id = :compartmentId) AND
        (:slaMonitoreable IS NULL OR rt.sla_monitoreable = :slaMonitoreable)
    """, nativeQuery = true)
List<ResourceDtoInterface> findAllData(
    @Param("organizationId") String organizationId,
    @Param("tenantId") String tenantId,
    @Param("compartmentId") String compartmentId,
    @Param("slaMonitoreable") Boolean slaMonitoreable
);
```

**SQL WHERE Clause Logic:**

```sql
WHERE
    -- Filter 1: Organization (Required in practice)
    (:organizationId IS NULL OR r.organization_id = :organizationId)

    AND

    -- Filter 2: SLA Monitoreable (Key filter for SLA creation)
    (:slaMonitoreable IS NULL OR rt.sla_monitoreable = :slaMonitoreable)

    AND

    -- Filter 3: Tenant (Optional)
    (:tenantId IS NULL OR r.tenant_id = :tenantId)

    AND

    -- Filter 4: Compartment (Optional)
    (:compartmentId IS NULL OR r.compartment_id = :compartmentId)
```

**Critical JOIN:**
```sql
LEFT JOIN ociapp.resource_type rt ON r.resourcetype_id = rt.id
```
This JOIN is essential for filtering by `rt.sla_monitoreable` flag!

### SLA Monitoreable Flag

#### What is SLA Monitoreable?

The `sla_monitoreable` flag in the `resource_type` table determines whether a specific resource type can be used for SLA monitoring. Only resources with monitoreable types appear in the SLA creation form.

#### Database Schema

```sql
-- resource_type table
CREATE TABLE resource_type (
    id                UUID PRIMARY KEY,
    name              VARCHAR(255) NOT NULL,
    description       TEXT,
    sla_monitoreable  BOOLEAN DEFAULT FALSE,  -- KEY COLUMN
    created_at        TIMESTAMP,
    created_by        VARCHAR(100)
);
```

#### Examples of SLA Monitoreable Resources

| Resource Type | SLA Monitoreable | Reason |
|---------------|------------------|--------|
| **AutonomousDatabase** | ✅ TRUE | Can monitor CPU, Storage, I/O |
| **ComputeInstance** | ✅ TRUE | Can monitor CPU, Memory, Network |
| **BlockVolume** | ✅ TRUE | Can monitor IOPS, Throughput |
| **ObjectStorage** | ✅ TRUE | Can monitor API availability |
| **VirtualCloudNetwork** | ❌ FALSE | No meaningful SLA metrics |
| **RouteTable** | ❌ FALSE | Cannot be monitored for SLA |
| **SecurityList** | ❌ FALSE | No metrics available |

#### Setting SLA Monitoreable Flag

```sql
-- Enable SLA monitoring for specific resource types
UPDATE resource_type
SET sla_monitoreable = TRUE
WHERE name IN (
    'AutonomousDatabase',
    'ComputeInstance',
    'BlockVolume',
    'ObjectStorage',
    'LoadBalancer'
);

-- Disable for non-monitoreable types
UPDATE resource_type
SET sla_monitoreable = FALSE
WHERE name IN (
    'VirtualCloudNetwork',
    'RouteTable',
    'SecurityList',
    'InternetGateway'
);
```

### Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
└──────────────────────────────────────────────────────────────┘
                              │
         User opens /sla/create
                              │
                              ↓
                 ┌────────────────────────┐
                 │  Load Organizations     │
                 │  useOrganizations()     │
                 └──────────┬──────────────┘
                            │
         User selects Organization
                            │
                            ↓
         ┌──────────────────────────────────────┐
         │  useResources({                      │
         │    organizationId: selected,         │
         │    slaMonitoreable: true             │
         │  })                                  │
         └──────────────┬───────────────────────┘
                        │
         GET /api/codebook/resources?
             organizationId={uuid}&
             slaMonitoreable=true
                        │
┌───────────────────────┼──────────────────────────────────────┐
│                       │        BACKEND (Spring Boot)         │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        ↓
         ┌──────────────────────────────────────┐
         │  ResourcesController                 │
         │  @GetMapping("/resources")           │
         └──────────────┬───────────────────────┘
                        │
                        ↓
         ┌──────────────────────────────────────┐
         │  ResourceService.search()            │
         │  - Check authorization               │
         │  - Force user's organization         │
         └──────────────┬───────────────────────┘
                        │
                        ↓
         ┌──────────────────────────────────────┐
         │  ResourceRepository.findAllData()    │
         │  - JOIN with resource_type           │
         │  - Filter by sla_monitoreable        │
         └──────────────┬───────────────────────┘
                        │
┌───────────────────────┼──────────────────────────────────────┐
│                       │        DATABASE (MySQL)              │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        ↓
         SELECT r.*, rt.name
         FROM resource r
         JOIN resource_type rt ON r.resourcetype_id = rt.id
         WHERE r.organization_id = ?
           AND rt.sla_monitoreable = TRUE
                        │
                        ↓
         Returns filtered resources
                        │
                        ↓
         Frontend displays in dropdown
```

### Security Considerations

#### Role-Based Access Control

```java
if (!AuthHelper.currentUserIsSuperadminOrSysadmin()) {
    // Regular users can only see their organization's resources
    organizationId = currentUser.getOrganization().getId();
}
```

**Privileges:**
- ✅ **SUPERADMIN**: View resources from ALL organizations
- ✅ **SYSADMIN**: View resources from ALL organizations
- ❌ **ORG_ADMIN**: View ONLY their organization's resources
- ❌ **USER**: View ONLY their organization's resources

#### Data Isolation

- Organization ID is **forced** at the service layer
- Cannot bypass via API manipulation
- Database queries always include organization filter
- JWT token contains user's organization

### Example API Response

**Request:**
```http
GET /api/codebook/resources?organizationId=550e8400-e29b-41d4-a716-446655440000&slaMonitoreable=true
```

**Response:**
```json
[
    {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "ocid": "ocid1.instance.oc1.eu-frankfurt-1.abcd1234",
        "name": "Production-DB-Instance",
        "description": "Main production database",
        "organizationId": "550e8400-e29b-41d4-a716-446655440000",
        "organizationName": "ACME Corporation",
        "organizationShortName": "ACME",
        "tenantId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "tenantOcid": "ocid1.tenancy.oc1..aaaaaaaaxxxxxx",
        "tenantName": "acme-production",
        "compartmentId": "8f14e45f-ceea-467a-9e4d-a716446655441",
        "compartmentOcid": "ocid1.compartment.oc1..aaaaaaaaxxxxxx",
        "compartmentName": "production-compartment",
        "resourceTypeId": "9a7b8c10-1234-5678-9abc-def012345678",
        "resourceTypeName": "AutonomousDatabase",
        "createdAt": "2025-01-15T10:30:00",
        "updatedAt": "2025-01-15T10:30:00",
        "createdBy": "admin@acme.com",
        "updatedBy": null
    },
    {
        "id": "8c9e6679-7425-40de-944b-e07fc1f90ae8",
        "ocid": "ocid1.instance.oc1.eu-frankfurt-1.efgh5678",
        "name": "Web-Server-01",
        "description": "Frontend web server",
        "organizationId": "550e8400-e29b-41d4-a716-446655440000",
        "organizationName": "ACME Corporation",
        "organizationShortName": "ACME",
        "tenantId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "tenantOcid": "ocid1.tenancy.oc1..aaaaaaaaxxxxxx",
        "tenantName": "acme-production",
        "compartmentId": "8f14e45f-ceea-467a-9e4d-a716446655441",
        "compartmentOcid": "ocid1.compartment.oc1..aaaaaaaaxxxxxx",
        "compartmentName": "production-compartment",
        "resourceTypeId": "1a2b3c10-1234-5678-9abc-def012345679",
        "resourceTypeName": "ComputeInstance",
        "createdAt": "2025-01-16T14:20:00",
        "updatedAt": "2025-01-16T14:20:00",
        "createdBy": "admin@acme.com",
        "updatedBy": null
    }
]
```

### Relevant Files

#### Frontend
```
src/pages/SlaFormPage.tsx           - SLA creation form (Step 1)
src/hooks/useResources.ts           - React Query hook for resources
src/services/resourceService.ts     - API service
src/constants.ts                    - API route definitions
```

#### Backend
```
ResourcesController.java            - REST endpoint
ResourceService.java                - Business logic + authorization
ResourceRepository.java             - SQL query with filters
```

#### Database
```sql
resource                            - Main resource table
resource_type                       - Contains sla_monitoreable flag
organization                        - Tenant/Organization table
tenant                              - OCI tenancy
compartment                         - OCI compartment
```

### Key Takeaways

1. **Two-Stage Filtering**: Organization selection triggers automatic resource loading with SLA filter
2. **Security First**: Organization ID is forced at service layer based on user role
3. **Resource Type Flag**: `sla_monitoreable` column determines which resources appear
4. **Performance**: React Query caching reduces unnecessary API calls
5. **User Experience**: Resources load automatically when organization is selected

---

## 🗄️ Database Architecture

The SLA module centers around 4 core tables that work together to define, monitor, and track service level agreements.

### Table Relationship Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          SLA Database Schema                                │
└────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   tenant             │
│  ──────────────────  │
│  - id (PK)           │
│  - ocid              │
│  - name              │
└───────────┬──────────┘
            │
            │ 1:N
            ↓
┌──────────────────────┐       ┌──────────────────────┐
│   resource           │       │   oci_query          │
│  ──────────────────  │       │  ──────────────────  │
│  - id (PK)           │       │  - id (PK)           │
│  - ocid              │       │  - tenant_id (FK)    │
│  - tenant_id (FK)    │       │  - metric_namespace  │
│  - freeform_tags     │       │  - metric_name       │
└───────────┬──────────┘       └──────────┬───────────┘
            │                              │
            │ 0..1                         │ 0..1
            │                              │
            └──────────┬───────────────────┘
                       │
                       │ Both are optional (one or the other)
                       ↓
            ┌──────────────────────┐
            │  sla_definition      │ ◄───────────────────┐
            │  ──────────────────  │                     │
            │  - id (PK)           │                     │
            │  - tenant_id (FK)    │                     │
            │  - resource_id (FK)  │ ← Single resource   │
            │  - oci_query_id (FK) │ ← Multi-resource    │
            │  - name              │                     │
            │  - metric_namespace  │                     │
            │  - metric_name       │                     │
            │  - metric_threshold  │                     │
            │  - comparator        │                     │
            │  - target_value      │                     │
            │  - period_type       │                     │
            │  - timezone          │                     │
            │  - schedule_mode     │                     │
            │  - is_active         │                     │
            └───────────┬──────────┘                     │
                        │                                │
                        │ 1:N                            │
                        ├────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬────────────────┐
        │               │               │                │
        │ 1:N           │ 1:N           │ 1:N            │ 0..1
        ↓               ↓               ↓                ↓
┌───────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────────────┐
│ sla_breach    │ │ sla_downtime_  │ │ sla_penalty_   │ │ metric_result    │
│               │ │   window       │ │   tier         │ │                  │
│  ───────────  │ │  ────────────  │ │  ────────────  │ │  ──────────────  │
│ - id (PK)     │ │ - id (PK)      │ │ - id (PK)      │ │ - id (PK)        │
│ - sla_def_id  │ │ - sla_def_id   │ │ - sla_def_id   │ │ - resource_ocid  │
│ - timestamp   │ │ - start_time   │ │ - threshold_%  │ │   (STRING)       │
│ - metric_value│ │ - end_time     │ │ - penalty_amt  │ │ - query_id       │
│ - threshold   │ │ - reason       │ │ - currency     │ │ - time           │
│ - duration_min│ │ - is_recurring │ │                │ │ - value          │
│ - severity    │ │                │ │                │ │                  │
│ - is_resolved │ │                │ │                │ │ (Source data for │
│ - resource_id │ │                │ │                │ │  SLA computation)│
└───────────────┘ └────────────────┘ └────────────────┘ └──────────────────┘

WORKFLOW:
1. User creates sla_definition (with thresholds, target, schedule)
2. User optionally adds sla_downtime_window (maintenance windows)
3. User optionally adds sla_penalty_tier (financial penalties)
4. Scheduler reads sla_definition + metric_result → calculates compliance
5. If breach detected → saves to sla_breach
6. Report generation reads sla_definition + sla_breach + applies penalties
```

---

### 1. **sla_definition** Table

**Purpose**: The heart of the SLA module. Defines SLA rules, thresholds, monitoring schedules, and compliance targets.

<details>
<summary>📋 Click to view table details</summary>

**Columns**:

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| **id** | VARCHAR(255) | UUID primary key | a1b2c3d4-e5f6-7890-abcd-ef1234567890 |
| **name** | VARCHAR(255) | User-friendly SLA name | Monthly CPU SLA |
| **description** | TEXT | Detailed explanation of SLA purpose | CPU utilization must stay below 80% |
| **tenant_id** | VARCHAR(255) | Which OCI tenant this SLA belongs to | FK to **tenant.id** |
| **resource_id** | VARCHAR(255) | **Single-resource SLA**: Specific resource to monitor | FK to **resource.id** (nullable) |
| **oci_query_id** | VARCHAR(255) | **Multi-resource SLA**: Query defining multiple resources | FK to **oci_query.id** (nullable) |
| **metric_namespace** | VARCHAR(255) | OCI metric namespace | oci_computeagent |
| **metric_name** | VARCHAR(255) | Metric to monitor | CpuUtilization |
| **statistic_type** | VARCHAR(50) | Aggregation function | MEAN, MAX, MIN, SUM, COUNT |
| **metric_threshold** | DECIMAL(10,2) | Threshold value that should not be crossed | 80.0 (80%) |
| **comparator** | VARCHAR(10) | How to compare metric vs threshold | LT (less than), GT, LTE, GTE, EQ |
| **target_value** | DECIMAL(5,2) | **SLO Target**: Minimum compliance percentage | 99.50 (99.5% uptime) |
| **period_type** | VARCHAR(50) | Reporting period | DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY |
| **start_date** | DATE | When SLA becomes active | 2025-11-01 |
| **end_date** | DATE | When SLA expires (optional) | 2026-11-01 (nullable) |
| **timezone** | VARCHAR(50) | Timezone for local time calculations | Europe/Belgrade, UTC |
| **schedule_mode** | VARCHAR(50) | When SLA is active | 24_7, BUSINESS_HOURS, CUSTOM |
| **custom_schedule** | JSON | Custom schedule configuration | {"days": [1,2,3,4,5], "hours": "09:00-17:00"} |
| **tag_filter_criteria** | JSON | Tag-based resource filtering (for multi-resource SLAs) | {"environment": "production"} |
| **alert_threshold_percent** | DECIMAL(5,2) | Early warning threshold (before breach) | 99.0 (alert if compliance < 99%) |
| **is_active** | TINYINT(1) | Whether SLA is currently active | 1 (active), 0 (inactive) |

**Indexes**:
- PRIMARY KEY (**id**)
- INDEX (**tenant_id**) - Fast queries by tenant
- INDEX (**resource_id**) - Fast queries by resource
- INDEX (**oci_query_id**) - Fast queries by query
- INDEX (**is_active**, **period_type**) - Fast scheduler queries (get active DAILY/WEEKLY/MONTHLY SLAs)

</details>

**How It Works**:

1. **Single-Resource SLA**: Set **resource_id**, leave **oci_query_id** NULL
   - Example: Monitor CPU of specific VM prod-vm-01

2. **Multi-Resource SLA**: Set **oci_query_id**, leave **resource_id** NULL
   - Example: Monitor CPU of all VMs with tag environment=production
   - Uses **tag_filter_criteria** JSON to filter resources from the query

3. **Threshold Logic**:
   - Comparator **LT** (less than): Metric value should be < threshold
   - Example: CpuUtilization LT 80.0 means CPU must stay below 80%
   - If metric value ≥ 80.0 → BREACH

4. **Target Value (SLO)**:
   - Defines minimum acceptable compliance percentage
   - Example: **target_value = 99.50** means 99.5% of data points must be compliant
   - Formula: **Compliance % = (Compliant Points / Counted Points) * 100**
   - If Compliance % < 99.50 → SLA FAILED (BREACHED status)
   - If Compliance % ≥ 99.50 → SLA PASSED (FULFILLED status)

5. **Schedule Mode**:
   - **24_7** - Monitor 24/7, all data points count
   - **BUSINESS_HOURS** - Monitor only during 09:00-17:00 Mon-Fri (others excluded)
   - **CUSTOM** - Use **custom_schedule** JSON to define specific days/hours

---

### 2. **sla_breach** Table

**Purpose**: Stores detected SLA breach events. Each row represents a single violation of the SLA threshold.

<details>
<summary>📋 Click to view table details</summary>

**Columns**:

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| **id** | VARCHAR(255) | UUID primary key | breach-uuid-123 |
| **sla_definition_id** | VARCHAR(255) | Which SLA was breached | FK to **sla_definition.id** |
| **timestamp** | DATETIME | **UTC timestamp** when breach occurred | 2025-11-15 14:30:00 |
| **timestamp_local** | DATETIME | **Local timezone timestamp** | 2025-11-15 15:30:00 (UTC+1) |
| **metric_value** | DECIMAL(10,2) | Actual metric value during breach | 85.5 (CPU was 85.5%) |
| **threshold** | DECIMAL(10,2) | SLA threshold that was violated | 80.0 (threshold was 80%) |
| **duration_minutes** | INT | How long breach lasted | 45 (breach lasted 45 minutes) |
| **severity** | VARCHAR(50) | Breach severity classification | LOW, MEDIUM, HIGH, CRITICAL |
| **resource_id** | VARCHAR(255) | Which resource had the breach | FK to **resource.id** |
| **resource_ocid** | VARCHAR(255) | OCI resource identifier | ocid1.instance.oc1... |
| **resource_name** | VARCHAR(255) | Resource display name (denormalized) | prod-vm-01 |
| **is_resolved** | TINYINT(1) | Whether breach has ended | 1 (resolved), 0 (still active) |
| **resolved_at** | DATETIME | When breach ended | 2025-11-15 15:15:00 |
| **description** | TEXT | Breach description | CPU exceeded 80% threshold |

**Indexes**:
- PRIMARY KEY (**id**)
- INDEX (**sla_definition_id**, **timestamp**) - Fast report queries
- INDEX (**resource_id**, **timestamp**) - Fast per-resource queries
- INDEX (**is_resolved**) - Fast active breach queries

</details>

**How It Works**:

1. **Breach Detection** (in **BreachDetectionService**):
   ```java
   // For each metric data point in period
   if (metricValue violates threshold) {
       // Create new sla_breach record
       SlaBreach breach = new SlaBreach();
       breach.setSlaDefinitionId(slaId);
       breach.setTimestamp(dataPointTime);
       breach.setMetricValue(metricValue);
       breach.setThreshold(slaThreshold);
       breach.setIsResolved(false);
       save(breach);
   }
   ```

2. **Duration Calculation**:
   - Consecutive breach points are grouped
   - Duration = time between first and last consecutive breaches
   - Example: Breach at 14:30, 14:35, 14:40, 14:45 → Duration = 15 minutes

3. **Severity Classification**:
   - Based on magnitude of violation and duration
   - **CRITICAL** - Value > threshold * 1.5 AND duration > 60 minutes
   - **HIGH** - Value > threshold * 1.2 AND duration > 30 minutes
   - **MEDIUM** - Value > threshold * 1.1 OR duration > 15 minutes
   - **LOW** - All other breaches

4. **Resolution Tracking**:
   - When metric returns to compliant state:
     - Set **is_resolved = 1**
     - Set **resolved_at = current_time**
   - Allows tracking of ongoing vs resolved breaches

**Query Examples**:

```sql
-- Get all unresolved breaches for an SLA
SELECT * FROM sla_breach
WHERE sla_definition_id = :slaId
  AND is_resolved = 0
ORDER BY timestamp DESC;

-- Get breach count for last month
SELECT COUNT(*) AS breach_count
FROM sla_breach
WHERE sla_definition_id = :slaId
  AND timestamp BETWEEN :monthStart AND :monthEnd;

-- Get total breach duration for penalty calculation
SELECT SUM(duration_minutes) AS total_breach_minutes
FROM sla_breach
WHERE sla_definition_id = :slaId
  AND timestamp BETWEEN :periodStart AND :periodEnd;
```

---

### 3. **sla_downtime_window** Table

**Purpose**: Defines planned maintenance windows that should be excluded from SLA calculations. Data points during these windows don't count toward compliance.

<details>
<summary>📋 Click to view table details</summary>

**Columns**:

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| **id** | VARCHAR(255) | UUID primary key | downtime-uuid-456 |
| **sla_definition_id** | VARCHAR(255) | Which SLA this downtime belongs to | FK to **sla_definition.id** |
| **start_time** | DATETIME | Maintenance window start | 2025-11-15 02:00:00 |
| **end_time** | DATETIME | Maintenance window end | 2025-11-15 04:00:00 |
| **timezone** | VARCHAR(50) | Timezone for start/end times | Europe/Belgrade |
| **reason** | VARCHAR(500) | Why this downtime is scheduled | Planned OS patching |
| **is_recurring** | TINYINT(1) | One-time or recurring | 1 (recurring), 0 (one-time) |
| **recurrence_pattern** | VARCHAR(255) | CRON expression for recurring | 0 2 * * SUN (every Sunday 2 AM) |

**Indexes**:
- PRIMARY KEY (**id**)
- INDEX (**sla_definition_id**) - Fast queries by SLA
- INDEX (**start_time**, **end_time**) - Fast time range queries

</details>

**How It Works**:

1. **One-Time Downtime** (**is_recurring = 0**):
   ```java
   // User creates one-time maintenance window
   SlaDowntimeWindow downtime = new SlaDowntimeWindow();
   downtime.setSlaDefinitionId(slaId);
   downtime.setStartTime(LocalDateTime.of(2025, 11, 15, 2, 0));
   downtime.setEndTime(LocalDateTime.of(2025, 11, 15, 4, 0));
   downtime.setReason("Planned OS patching");
   downtime.setIsRecurring(false);
   ```

2. **Recurring Downtime** (**is_recurring = 1**):
   ```java
   // User creates recurring maintenance (every Sunday 2-4 AM)
   SlaDowntimeWindow downtime = new SlaDowntimeWindow();
   downtime.setIsRecurring(true);
   downtime.setRecurrencePattern("0 2 * * SUN");
   // System expands this to actual date ranges during computation
   ```

3. **Exclusion Logic** (in **AvailabilityCalculatorService**):
   ```java
   // For each metric data point
   for (MetricResult dataPoint : metricData) {
       // Check if point falls within any downtime window
       boolean isInDowntime = downtimeWindows.stream()
           .anyMatch(window ->
               dataPoint.getTime().isAfter(window.getStartTime()) &&
               dataPoint.getTime().isBefore(window.getEndTime())
           );

       if (isInDowntime) {
           // EXCLUDE this point from SLA calculation
           excludedPoints++;
       } else {
           // COUNT this point toward compliance
           countedPoints++;
           if (dataPoint.getValue() meets threshold) {
               compliantPoints++;
           }
       }
   }

   // Final calculation
   compliancePercentage = (compliantPoints / countedPoints) * 100;
   ```

4. **Impact on Reports**:
   - Report shows: **Excluded Downtime Count: 2 maintenance windows**
   - Total Points = 8640
   - Excluded Points = 240 (during maintenance)
   - Counted Points = 8400 (8640 - 240)
   - Compliance % = (Compliant / 8400) * 100

**Use Cases**:

| Scenario | Configuration | Effect |
|----------|--------------|--------|
| **Monthly OS Patching** | Recurring: 0 2 1 * * (1st of month, 2 AM) | Excludes first Sunday of each month 2-4 AM from SLA |
| **Emergency Maintenance** | One-time: Specific date range | Excludes specific 2-hour window from SLA |
| **Weekly Backups** | Recurring: 0 1 * * * (daily 1 AM) | Excludes daily 1-3 AM backup window |

---

### 4. **sla_penalty_tier** Table

**Purpose**: Defines tiered financial penalties based on compliance levels. Enables automatic penalty calculation when SLA is breached.

<details>
<summary>📋 Click to view table details</summary>

**Columns**:

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| **id** | VARCHAR(255) | UUID primary key | penalty-uuid-789 |
| **sla_definition_id** | VARCHAR(255) | Which SLA this penalty tier belongs to | FK to **sla_definition.id** |
| **threshold_percent** | DECIMAL(5,2) | Compliance threshold for this tier | 99.0 (if compliance < 99%) |
| **penalty_amount** | DECIMAL(10,2) | Penalty amount in currency | 500.00 |
| **penalty_currency** | VARCHAR(10) | Currency code | USD, EUR |
| **description** | TEXT | Penalty tier description | Minor service credit |

**Indexes**:
- PRIMARY KEY (**id**)
- INDEX (**sla_definition_id**) - Fast queries by SLA
- INDEX (**threshold_percent**) - Fast tier lookup

</details>

**How It Works**:

1. **Multiple Tiers** (Configured by user):
   ```java
   // Tier 1: Compliance < 99.0% → $500 penalty
   SlapenaltyTier tier1 = new SlaPenaltyTier();
   tier1.setThresholdPercent(99.0);
   tier1.setPenaltyAmount(500.00);
   tier1.setPenaltyCurrency("USD");

   // Tier 2: Compliance < 95.0% → $2000 penalty
   SlaPenaltyTier tier2 = new SlaPenaltyTier();
   tier2.setThresholdPercent(95.0);
   tier2.setPenaltyAmount(2000.00);
   tier2.setPenaltyCurrency("USD");

   // Tier 3: Compliance < 90.0% → $5000 penalty
   SlaPenaltyTier tier3 = new SlaPenaltyTier();
   tier3.setThresholdPercent(90.0);
   tier3.setPenaltyAmount(5000.00);
   tier3.setPenaltyCurrency("USD");
   ```

2. **Penalty Application** (in **SlaReportService**):
   ```java
   // After calculating compliance percentage
   double compliancePercentage = 98.5; // Example: 98.5% compliance

   // Find applicable penalty tier (highest threshold that compliance falls below)
   SlaPenaltyTier applicableTier = penaltyTiers.stream()
       .filter(tier -> compliancePercentage < tier.getThresholdPercent())
       .max(Comparator.comparing(SlaPenaltyTier::getThresholdPercent))
       .orElse(null);

   if (applicableTier != null) {
       // Apply penalty
       summary.setPenaltyAmount(applicableTier.getPenaltyAmount());
       summary.setPenaltyCurrency(applicableTier.getPenaltyCurrency());
   }
   ```

3. **Penalty Logic**:
   - Penalties are evaluated in order of decreasing thresholds
   - Only the **most severe applicable** penalty is applied (not cumulative)
   - Example:
     - Target: 99.5%
     - Actual: 94.8%
     - Tier 1 (< 99.0%): $500 ✅ Applies
     - Tier 2 (< 95.0%): $2000 ✅ Applies (overrides Tier 1)
     - Tier 3 (< 90.0%): $5000 ❌ Does not apply (compliance ≥ 90%)
     - **Final Penalty**: $2000

4. **Report Display**:
   ```json
   {
     "summary": {
       "compliancePercentage": 94.8,
       "targetValue": 99.5,
       "complianceStatus": "BREACHED",
       "penaltyAmount": 2000.00,
       "penaltyCurrency": "USD"
     }
   }
   ```

**Real-World Example**:

| Tier | Threshold | Penalty | Scenario |
|------|-----------|---------|----------|
| 1 | < 99.0% | $500 | Minor degradation, partial service credit |
| 2 | < 95.0% | $2000 | Significant degradation, larger service credit |
| 3 | < 90.0% | $5000 | Severe degradation, major service credit |
| 4 | < 80.0% | $10000 | Critical failure, full month service credit |

---

### How Tables Work Together - Complete Workflow

```
STEP 1: User Creates SLA Definition
───────────────────────────────────────
INSERT INTO sla_definition (
  name = "Monthly CPU SLA",
  metric_namespace = "oci_computeagent",
  metric_name = "CpuUtilization",
  metric_threshold = 80.0,
  comparator = "LT",
  target_value = 99.5,
  period_type = "MONTHLY"
)
→ SLA ID: sla-uuid-abc


STEP 2: User Adds Downtime Windows
───────────────────────────────────────
INSERT INTO sla_downtime_window (
  sla_definition_id = "sla-uuid-abc",
  start_time = "2025-11-15 02:00:00",
  end_time = "2025-11-15 04:00:00",
  reason = "Monthly OS patching"
)


STEP 3: User Adds Penalty Tiers
───────────────────────────────────────
INSERT INTO sla_penalty_tier (sla_definition_id, threshold_percent, penalty_amount)
VALUES ("sla-uuid-abc", 99.0, 500.00),
       ("sla-uuid-abc", 95.0, 2000.00)


STEP 4: OciMetricsScheduler Collects Metrics (Every 11 minutes)
────────────────────────────────────────────────────────────────
INSERT INTO metric_result (resource_ocid, time, value)
VALUES ("ocid1.instance...", "2025-11-15 10:00:00", 75.5),
       ("ocid1.instance...", "2025-11-15 10:05:00", 82.3),  ← BREACH (> 80.0)
       ("ocid1.instance...", "2025-11-15 10:10:00", 85.1),  ← BREACH
       ("ocid1.instance...", "2025-11-15 10:15:00", 78.2)


STEP 5: SlaSchedulerService Computes Compliance (Monthly: 1st at 00:15)
────────────────────────────────────────────────────────────────────────
SlaComputationService.computeSla("sla-uuid-abc", MONTHLY, "2025-11-01"):

1. Load sla_definition
2. Load sla_downtime_window
3. Read metric_result for November 2025
4. Exclude points during downtime windows
5. Calculate:
   - Total points: 8640 (30 days * 24 hours * 12 per hour)
   - Excluded points: 24 (2-hour maintenance)
   - Counted points: 8616
   - Compliant points: 8572 (value < 80.0)
   - Breach points: 44 (value ≥ 80.0)
   - Compliance %: (8572 / 8616) * 100 = 99.49%

6. Compare: 99.49% < 99.5% target → BREACHED


STEP 6: Save Breach Events
────────────────────────────────────────
INSERT INTO sla_breach (
  sla_definition_id = "sla-uuid-abc",
  timestamp = "2025-11-15 10:05:00",
  metric_value = 82.3,
  threshold = 80.0,
  duration_minutes = 10,
  severity = "MEDIUM"
)


STEP 7: User Generates Report (On-demand)
────────────────────────────────────────
GET /api/sla/reports/sla-uuid-abc?periodType=MONTHLY&periodStart=2025-11-01

SlaReportService.generateReport():
1. Read sla_definition
2. Read sla_breach for November
3. Read sla_penalty_tier
4. Apply penalty tier:
   - Compliance 99.49% < 99.0% threshold → Apply $500 penalty
5. Return report:
   {
     "compliancePercentage": 99.49,
     "targetValue": 99.5,
     "complianceStatus": "BREACHED",
     "penaltyAmount": 500.00,
     "penaltyCurrency": "USD",
     "breaches": [...]
   }


STEP 8: User Exports PDF
────────────────────────────────────────
GET /api/sla/reports/sla-uuid-abc/export/pdf?periodType=MONTHLY&periodStart=2025-11-01

1. Generate report (same as Step 7)
2. Render HTML template with Thymeleaf
3. Convert to PDF with Flying Saucer
4. Download file: sla-report-Monthly-CPU-SLA-monthly-2025-11-01.pdf
```

---

## 📊 Understanding SLA Thresholds and Targets

### Overview

When creating an SLA Definition, you configure **three critical threshold values** that work together to monitor and report on service level compliance. Understanding the distinction between these values is essential for proper SLA configuration.

### The Three Threshold Concepts

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SLA Threshold Hierarchy                                    │
└──────────────────────────────────────────────────────────────────────────────┘

METRIC DATA POINTS (Individual measurements)
     ↓
1. METRIC THRESHOLD ──────> Defines what is "compliant" vs "breach"
     ↓
   Compliance % = (Compliant Points / Total Points) * 100
     ↓
2. ALERT THRESHOLD ───────> Early warning (yellow zone)
     ↓
3. TARGET SLO ────────────> Pass/Fail boundary (red zone)
     ↓
   SLA STATUS: FULFILLED, AT_RISK, or BREACHED
```

---

### 1. Metric Threshold (metric_threshold)

**What it is:** The **maximum or minimum acceptable value** for the monitored metric at each data point.

**Purpose:** Defines the boundary between "compliant" and "breach" at the **individual measurement level**.

**Database Column:** `sla_definition.metric_threshold` (DECIMAL)

**Used With:** `comparator` field (LT, GT, LTE, GTE, EQ)

**Example Configurations:**

| Metric | Comparator | Threshold | Meaning |
|--------|------------|-----------|---------|
| CpuUtilization | **LT** (Less Than) | 80.0 | CPU must stay **below** 80% |
| MemoryUtilization | **LT** | 90.0 | Memory must stay **below** 90% |
| HttpResponseTime | **LT** | 500.0 | Response time must stay **below** 500ms |
| ApiAvailability | **GT** (Greater Than) | 99.0 | Availability must stay **above** 99% |
| DiskSpace | **GT** | 20.0 | Free disk space must stay **above** 20% |

**How It Works:**

For **EACH** metric data point collected (e.g., every 5 minutes):

```java
// Example: CpuUtilization with threshold 80.0 and comparator LT (less than)

for (MetricResult dataPoint : metricData) {
    boolean isCompliant;

    if (comparator == "LT") {
        isCompliant = (dataPoint.value < metricThreshold);
        // Example: 75.5 < 80.0 → TRUE (compliant)
        // Example: 82.3 < 80.0 → FALSE (breach)
    } else if (comparator == "GT") {
        isCompliant = (dataPoint.value > metricThreshold);
    }

    if (isCompliant) {
        compliantCount++;
    } else {
        breachCount++;
        createSlaBreach(dataPoint);  // Save breach event
    }
}
```

**Real-World Example:**

You have a CPU SLA with threshold 80%:
- **09:00** - CPU = 75.5% → **✅ COMPLIANT** (75.5 < 80)
- **09:05** - CPU = 78.2% → **✅ COMPLIANT** (78.2 < 80)
- **09:10** - CPU = 82.3% → **❌ BREACH** (82.3 >= 80) - Creates `sla_breach` record
- **09:15** - CPU = 85.1% → **❌ BREACH** (85.1 >= 80) - Creates another `sla_breach` record
- **09:20** - CPU = 76.8% → **✅ COMPLIANT** (76.8 < 80)

Result after these 5 measurements:
- **Compliant points:** 3
- **Breach points:** 2
- **Point-level compliance:** 60% (3 out of 5)

---

### 2. Target SLO / Target Value (target_value)

**What it is:** The **minimum acceptable compliance percentage** for the entire reporting period (day/week/month).

**Purpose:** Defines the **Service Level Objective (SLO)** - the pass/fail boundary for the SLA.

**Database Column:** `sla_definition.target_value` (DECIMAL, stored as percentage like 99.50)

**Common Values:**
- **99.9%** (Three nines) - High availability (43 minutes downtime/month)
- **99.5%** (Two nines five) - Standard SLA (3.6 hours downtime/month)
- **99.0%** (Two nines) - Basic SLA (7.2 hours downtime/month)
- **95.0%** - Relaxed SLA (36 hours downtime/month)

**How It Works:**

After all data points are evaluated, calculate overall compliance:

```java
// Calculate period compliance
int totalPoints = 8640;        // 30 days * 24 hours * 12 points/hour
int excludedPoints = 240;      // During maintenance windows
int countedPoints = 8400;      // 8640 - 240
int compliantPoints = 8356;    // Points that met threshold
int breachPoints = 44;         // Points that violated threshold

double compliancePercent = (compliantPoints / countedPoints) * 100;
// = (8356 / 8400) * 100 = 99.48%

// Compare against target
double targetValue = 99.50;  // SLO target

if (compliancePercent >= targetValue) {
    status = "FULFILLED";  // ✅ SLA met
} else {
    status = "BREACHED";   // ❌ SLA failed
}

// In this example: 99.48% < 99.50% → BREACHED
```

**Real-World Example:**

Monthly SLA with 99.5% target:
- **Total data points in November:** 8,640 (30 days × 24 hours × 12 points/hour @ 5-min intervals)
- **Maintenance windows excluded:** 240 points (2 hours of planned maintenance)
- **Counted points:** 8,400
- **Compliant points:** 8,356 (CPU stayed below 80%)
- **Breach points:** 44 (CPU exceeded 80%)
- **Compliance percentage:** (8,356 / 8,400) × 100 = **99.48%**
- **Target SLO:** 99.50%
- **Result:** 99.48% < 99.50% → **❌ SLA BREACHED**

Even though 99.48% seems very high, it **failed to meet** the 99.50% target, so the SLA is considered breached.

**Key Insight:** The target value represents the **maximum allowed downtime/breach time** for the period. A 99.5% target means you can only afford 0.5% breach time (42 minutes in a month).

---

### 3. Alert Threshold (alert_threshold_percent)

**What it is:** An **early warning threshold** set slightly below the target SLO to provide advance notice of potential SLA risk.

**Purpose:** Triggers "AT_RISK" status **before** actual SLA breach occurs, allowing proactive intervention.

**Database Column:** `sla_definition.alert_threshold_percent` (DECIMAL, optional)

**Typical Configuration:** Set 0.5% - 1.0% below target SLO

**Common Patterns:**

| Target SLO | Alert Threshold | Buffer Zone |
|------------|-----------------|-------------|
| 99.9% | 99.5% | 0.4% buffer |
| 99.5% | 99.0% | 0.5% buffer |
| 99.0% | 98.5% | 0.5% buffer |
| 95.0% | 94.0% | 1.0% buffer |

**How It Works:**

The alert threshold creates a **three-tier status system**:

```java
double compliancePercent = 99.25;      // Calculated compliance
double targetValue = 99.50;            // SLO target
double alertThreshold = 99.00;         // Early warning

String status;

if (compliancePercent >= targetValue) {
    status = "FULFILLED";              // ✅ GREEN: All good
} else if (compliancePercent >= alertThreshold) {
    status = "AT_RISK";                // ⚠️ YELLOW: Warning zone
} else {
    status = "BREACHED";               // ❌ RED: SLA failed
}

// In this example: 99.00 <= 99.25 < 99.50 → AT_RISK
```

**Real-World Example:**

SLA with 99.5% target and 99.0% alert:

**Scenario 1: Healthy (GREEN)**
- Compliance: 99.8%
- Status: **FULFILLED** ✅
- Message: "SLA target met with 0.3% margin"

**Scenario 2: Warning (YELLOW)**
- Compliance: 99.25%
- Status: **AT_RISK** ⚠️
- Message: "SLA below target (99.5%) but above alert threshold (99.0%). Monitor closely."
- **Action:** Send notification to ops team, investigate cause

**Scenario 3: Breach (RED)**
- Compliance: 98.7%
- Status: **BREACHED** ❌
- Message: "SLA target NOT met: 98.7% < 99.5%. Alert threshold also breached."
- **Action:** Trigger incident, apply penalty, escalate to management

---

### How All Three Work Together

**Complete Example: Monthly CPU SLA**

**SLA Configuration:**
```yaml
SLA Name: "Production API - CPU Utilization"
Metric: oci_computeagent.CpuUtilization
Period: MONTHLY (November 2025)

1. Metric Threshold: 80.0%
   Comparator: LT (Less Than)
   Meaning: "CPU must stay BELOW 80% at each measurement"

2. Alert Threshold: 99.0%
   Meaning: "Warn if compliance drops below 99%"

3. Target SLO: 99.5%
   Meaning: "Pass/Fail at 99.5% compliance"
```

**Data Collection (November 2025):**
```
Total measurements: 8,640 (every 5 minutes for 30 days)
Maintenance windows: 240 points excluded (2 hours planned downtime)
Counted points: 8,400

Point-by-point evaluation:
- CPU < 80%: 8,356 points → COMPLIANT
- CPU >= 80%: 44 points → BREACH (saved to sla_breach table)
```

**Compliance Calculation:**
```
Compliance % = (8,356 / 8,400) × 100 = 99.48%
```

**Status Determination:**
```
Alert Threshold: 99.0%
Target SLO: 99.5%
Actual: 99.48%

Decision Tree:
99.48% >= 99.5% (target)? NO
99.48% >= 99.0% (alert)? YES
→ Status: AT_RISK ⚠️

However, since actual < target, final status = BREACHED ❌
```

**Report Output:**
```json
{
  "slaName": "Production API - CPU Utilization",
  "period": "November 2025",
  "summary": {
    "compliancePercent": 99.48,
    "targetValue": 99.5,
    "alertThreshold": 99.0,
    "complianceStatus": "BREACHED",
    "totalDataPoints": 8640,
    "countedDataPoints": 8400,
    "compliantDataPoints": 8356,
    "breachDataPoints": 44,
    "message": "SLA target NOT met: 99.48% < 99.50% (missed by 0.02%). Total breach time: 220 minutes."
  },
  "breaches": [
    {
      "timestamp": "2025-11-15 09:10:00",
      "metricValue": 82.3,
      "threshold": 80.0,
      "duration": 10,
      "severity": "MEDIUM"
    },
    // ... 43 more breach events
  ]
}
```

---

### Configuration Best Practices

**1. Set Realistic Thresholds**
- **Metric Threshold:** Based on infrastructure capacity and performance requirements
  - Don't set too aggressive (e.g., CPU < 50% is wasteful)
  - Don't set too loose (e.g., CPU < 95% is risky)
  - Recommended: CPU < 80%, Memory < 90%, Response time < 500ms

**2. Choose Appropriate Target SLO**
- **99.9%** (Three nines): Mission-critical systems, financial transactions
- **99.5%**: Standard production systems, customer-facing apps
- **99.0%**: Internal tools, non-critical services
- **95.0%**: Development/staging environments

**3. Configure Alert Buffer**
- Set alert threshold **0.5% - 1.0% below target**
- Provides early warning before actual breach
- Allows time for proactive intervention
- Example: Target 99.5% → Alert 99.0% (0.5% buffer)

**4. Account for Maintenance**
- Use `sla_downtime_window` to exclude planned maintenance
- Don't penalize SLA for scheduled work
- Typical: 2-4 hours/month for patching

**5. Align with Business Requirements**
- Match SLO to service tier agreements
- Consider financial penalties in `sla_penalty_tier`
- Document expectations in SLA description

---

### Common Scenarios Explained

**Q: Why did my SLA show BREACHED with 99.2% compliance when threshold is 95%?**

**A:** You're confusing **metric threshold** (individual measurement) with **target SLO** (overall compliance).
- **Metric threshold (95%)**: Defines what counts as "good" for EACH data point
- **Target SLO (99.5%)**: Defines PERCENTAGE of points that must be "good"
- **Your case**: 99.2% of points were good, but target requires 99.5% → BREACHED

**Q: What's the difference between "compliance percentage" and "metric threshold"?**

**A:**
- **Metric Threshold:** The VALUE that individual metrics shouldn't exceed (e.g., 80% CPU)
- **Compliance Percentage:** The PERCENTAGE of time the metric stayed within threshold (e.g., 99.48% uptime)

**Q: Why do I need an alert threshold if I have a target?**

**A:** **Proactive monitoring**. Alert threshold provides early warning:
- **Target (99.5%)**: Hard boundary, breach triggers penalties
- **Alert (99.0%)**: Soft boundary, triggers monitoring and investigation
- Without alert: You only know when it's too late (already breached)
- With alert: You have time to fix issues before actual breach

**Q: Can alert threshold be higher than target?**

**A:** **No, that doesn't make sense**. Alert should always be BELOW target:
- Correct: Target 99.5%, Alert 99.0%
- Wrong: Target 99.5%, Alert 99.9%
- If alert is higher, you'd never reach "FULFILLED" status

---

## 🔄 SLA Computation Workflow

### Scheduler Overview

Three separate CRON schedules in **SlaSchedulerService**:

```java
// oci-monitor/service/sla/SlaSchedulerService.java

@Scheduled(cron = "0 5 0 * * *")  // Every day at 00:05
public void processDailySlas() {
    List<SlaDefinition> dailySlas = slaDefinitionRepository
        .findByIsActiveTrueAndPeriodType(SlaPeriodType.DAILY);

    for (SlaDefinition sla : dailySlas) {
        slaComputationService.computeSla(sla, LocalDate.now().minusDays(1));
    }
}

@Scheduled(cron = "0 10 0 * * MON")  // Every Monday at 00:10
public void processWeeklySlas() {
    List<SlaDefinition> weeklySlas = slaDefinitionRepository
        .findByIsActiveTrueAndPeriodType(SlaPeriodType.WEEKLY);

    for (SlaDefinition sla : weeklySlas) {
        slaComputationService.computeSla(sla, getLastWeekStart());
    }
}

@Scheduled(cron = "0 15 0 1 * *")  // 1st of month at 00:15
public void processMonthlySlas() {
    List<SlaDefinition> monthlySlas = slaDefinitionRepository
        .findByIsActiveTrueAndPeriodType(SlaPeriodType.MONTHLY);

    for (SlaDefinition sla : monthlySlas) {
        slaComputationService.computeSla(sla, getLastMonthStart());
    }
}
```

### Detailed Computation Steps

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SLA Computation Workflow (SlaComputationService)                           │
└─────────────────────────────────────────────────────────────────────────────┘

INPUT: SlaDefinition, Period Start Date
─────────────────────────────────────────

STEP 1: Load SLA Configuration
───────────────────────────────────────
- Load sla_definition by ID
- Load sla_downtime_window for this SLA
- Load sla_penalty_tier for this SLA
- Determine period range (start/end in UTC and local timezone)


STEP 2: Load Metric Data (FROM CACHED DB)
───────────────────────────────────────
Query: SELECT * FROM metric_result mr
       WHERE mr.resource_ocid = :resourceOcid
         AND mr.time BETWEEN :periodStartUtc AND :periodEndUtc
       ORDER BY mr.time ASC

Result: List<MetricResult> (e.g., 8640 points for monthly @ 5-min intervals)

IMPORTANT: NO OCI API CALLS - uses cached data only


STEP 3: Filter Metric Data by Schedule Mode
───────────────────────────────────────
IF schedule_mode = "BUSINESS_HOURS":
  - Keep only points between 09:00-17:00 Mon-Fri
  - Exclude weekends and outside business hours

IF schedule_mode = "CUSTOM":
  - Parse custom_schedule JSON
  - Keep only points matching custom schedule

IF schedule_mode = "24_7":
  - Keep all points


STEP 4: Exclude Downtime Windows
───────────────────────────────────────
FOR EACH metric data point:
  FOR EACH downtime window:
    IF point.time BETWEEN window.start AND window.end:
      - EXCLUDE this point (mark as excluded)
      - excludedCount++

Result:
- Total Points: 8640
- Excluded Points: 240 (during downtime)
- Counted Points: 8400


STEP 5: Evaluate Compliance
───────────────────────────────────────
FOR EACH counted metric data point:
  IF point.value meets threshold (based on comparator):
    - compliantCount++
  ELSE:
    - breachCount++
    - CREATE sla_breach record

Example (comparator = "LT", threshold = 80.0):
  - point.value = 75.5 → COMPLIANT
  - point.value = 82.3 → BREACH
  - point.value = 85.1 → BREACH

Result:
- Compliant Points: 8356
- Breach Points: 44


STEP 6: Calculate Compliance Percentage
───────────────────────────────────────
compliancePercentage = (compliantCount / countedPoints) * 100
                     = (8356 / 8400) * 100
                     = 99.48%


STEP 7: Determine Compliance Status
───────────────────────────────────────
IF compliancePercentage >= targetValue:
  - complianceStatus = "FULFILLED"

ELSE IF compliancePercentage >= alertThreshold:
  - complianceStatus = "AT_RISK"

ELSE:
  - complianceStatus = "BREACHED"

Example (target = 99.5%, alert = 99.0%, actual = 99.48%):
  - 99.48% < 99.5% target → BREACHED
  - 99.48% >= 99.0% alert → AT_RISK (but target failed, so BREACHED takes precedence)


STEP 8: Apply Penalty Tiers
───────────────────────────────────────
Find highest penalty tier where compliance < threshold:

Penalty Tiers:
  - Tier 1: < 99.0% → $500
  - Tier 2: < 95.0% → $2000
  - Tier 3: < 90.0% → $5000

Actual Compliance: 99.48%
  - 99.48% >= 99.0% → Tier 1 does NOT apply
  - No penalty


STEP 9: Calculate Total Breach Duration
───────────────────────────────────────
SUM(breach.duration_minutes) for all breaches in period
= 220 minutes (44 breaches * 5 minutes each)


STEP 10: Save Results (if running from scheduler)
───────────────────────────────────────
- Save/update sla_breach records
- Optionally save summary snapshot
- Log computation results


OUTPUT: SlaComplianceSummaryDto
───────────────────────────────────────
{
  "totalDataPoints": 8640,
  "excludedDataPoints": 240,
  "countedDataPoints": 8400,
  "compliantDataPoints": 8356,
  "breachDataPoints": 44,
  "compliancePercentage": 99.48,
  "targetValue": 99.5,
  "complianceStatus": "BREACHED",
  "alertThresholdPercent": 99.0,
  "totalBreachDurationMinutes": 220,
  "penaltyAmount": 0.00,
  "penaltyCurrency": null
}
```

### Code Reference

**Main Service**: **oci-monitor/service/sla/SlaComputationService.java**

**Key Methods**:
- **computeSla(SlaDefinition sla, LocalDate periodStart)** - Main computation logic
- **loadMetricData(...)** - Query metric_result table
- **filterBySchedule(...)** - Apply schedule mode filtering
- **excludeDowntimeWindows(...)** - Remove maintenance windows
- **evaluateCompliance(...)** - Check each point against threshold
- **calculateCompliancePercentage(...)** - Compute final percentage
- **detectBreaches(...)** - Create sla_breach records
- **applyPenaltyTiers(...)** - Determine applicable penalties

---

## 🎯 Feature Implementation Matrix

### 1. SLA Definition Management

**Specification**: "Kreiranje, izmena i deaktivacija SLA pravila"

| Component | Location | Purpose |
|-----------|----------|---------|
| **Backend Controller** | oci-api/controller/sla/SlaDefinitionController.java | REST endpoints for CRUD operations on SLA definitions |
| **Backend Service** | oci-api/service/sla/SlaDefinitionService.java | Business logic for creating, updating, and managing SLA definitions |
| **Backend Entity** | oci-library/entity/sla/SlaDefinition.java | JPA entity representing SLA configuration |
| **Backend Repository** | oci-library/repository/sla/SlaDefinitionRepository.java | Database access for SLA definitions with custom queries |
| **Frontend Page - List** | src/pages/SlaListPage.tsx | UI for displaying list of SLA definitions |
| **Frontend Page - Form** | src/pages/SlaFormPage.tsx | UI form for creating/editing SLA definitions |
| **Frontend Service** | src/services/slaDefinitionService.ts | API client for SLA definition operations |

**REST Endpoints**:
```
POST   /api/sla/definitions              Create new SLA
GET    /api/sla/definitions              List all SLAs
GET    /api/sla/definitions/active       List active SLAs only
GET    /api/sla/definitions/{id}         Get SLA by ID
PUT    /api/sla/definitions/{id}         Update SLA
DELETE /api/sla/definitions/{id}         Delete SLA
```

**Database Tables**: **sla_definition**, **sla_downtime_window**, **sla_penalty_tier**

---

### 2. SLA Compliance Monitoring

**Specification**: "Praćenje SLA pravila i metrika", "Kontinuirano praćenje metrika"

| Component | Location | Purpose |
|-----------|----------|---------|
| **Scheduler** | oci-monitor/scheduler/SlaScheduler.java | Automated CRON-based execution of SLA computations |
| **Scheduler Service** | oci-monitor/service/sla/SlaSchedulerService.java | Batch processing of multiple SLA definitions by period type |
| **Computation Service** | oci-monitor/service/sla/SlaComputationService.java | Core logic for calculating SLA compliance and detecting breaches |
| **Breach Entity** | oci-library/entity/sla/SlaBreach.java | JPA entity storing individual breach events |
| **Breach Repository** | oci-library/repository/sla/SlaBreachRepository.java | Database access for breach records |

**CRON Schedules**:
```java
@Scheduled(cron = "0 5 0 * * *")      // Daily at 00:05
@Scheduled(cron = "0 10 0 * * MON")   // Weekly Monday at 00:10
@Scheduled(cron = "0 15 0 1 * *")     // Monthly 1st at 00:15
```

**Database Tables**: **sla_definition** (input), **metric_result** (input), **sla_breach** (output)

---

### 3. SLA Report Generation

**Specification**: "Generisanje dnevnih, mesečnih, kvartalnih i godišnjih izveštaja"

| Component | Location | Purpose |
|-----------|----------|---------|
| **Report Controller** | oci-api/controller/sla/SlaReportController.java | REST endpoints for generating and retrieving SLA reports |
| **Report Service** | oci-api/service/sla/SlaReportService.java | Business logic for report generation and formatting |
| **Report DTO** | oci-library/dto/sla/SlaReportDto.java | Data structure for report responses |
| **Frontend Page** | src/pages/SlaReportPage.tsx | UI for viewing SLA reports with charts and details |

**REST Endpoint**:
```
GET /api/sla/reports/{slaId}?periodType=MONTHLY&periodStart=2025-11-01
```

**Returns**: JSON report with compliance summary and breach list

---

### 4. CSV Export

**Specification**: "Mogućnost izvoza rezultata u CSV format"

| Component | Location | Purpose |
|-----------|----------|---------|
| **Export Controller** | oci-api/controller/sla/SlaReportController.java:exportCsv() | Endpoint for CSV download |
| **CSV Service** | oci-api/service/sla/SlaCsvExportService.java | Generates CSV files from SLA results |

**Technology**: Apache Commons CSV 1.10.0

**CSV Structure**: 3 sections (SLA Summary, Compliance Summary, Breach Events)

---

### 5. PDF Export

**Specification**: "Mogućnost izvoza rezultata u PDF format"

| Component | Location | Purpose |
|-----------|----------|---------|
| **Export Controller** | oci-api/controller/sla/SlaReportController.java:exportPdf() | Endpoint for PDF download |
| **PDF Service** | oci-api/service/sla/SlaPdfExportService.java | Generates PDF documents from SLA reports |
| **HTML Template** | oci-api/resources/templates/sla-report.html | Thymeleaf template for PDF rendering |
| **PDF Renderer** | Flying Saucer (xhtmlrenderer) | HTML to PDF conversion library |
| **PDF Library** | iText (via Flying Saucer) | Low-level PDF generation |

**Technology**: See [PDF Export Technology Stack](#pdf-export-technology-stack) section below

---

### 6. Graphical Visualization

**Specification**: "Vizuelni dashboard sa indikatorima usklađenosti i trendovima"

| Component | Location | Purpose |
|-----------|----------|---------|
| **Compliance Gauge** | src/components/charts/SlaComplianceGauge.tsx | Semi-doughnut chart showing compliance percentage |
| **Data Points Chart** | src/components/charts/SlaDataPointsChart.tsx | Horizontal bar showing compliant vs breach points |
| **Breach Timeline** | src/components/charts/SlaBreachTimelineChart.tsx | Timeline visualization of breach events |
| **Report Display** | src/components/SlaReportDisplay.tsx | Main component orchestrating all visualizations |

**Technology**: Chart.js 4.5.1 + react-chartjs-2 5.3.1

**Chart Types**: Doughnut gauge, Horizontal stacked bar, Vertical bar chart

---

## 📄 PDF Export Technology Stack

### Overview

PDF export uses a **server-side HTML-to-PDF** conversion approach:

1. **Template Engine** (Thymeleaf) renders HTML with report data
2. **PDF Renderer** (Flying Saucer) converts HTML to PDF bytes
3. **REST API** returns PDF as downloadable file

### Technology Stack

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| **Template Engine** | Thymeleaf (Spring Boot Starter) | 3.x | Server-side HTML templating |
| **PDF Renderer** | Flying Saucer (xhtmlrenderer) | 9.5.1 | HTML to PDF conversion |
| **PDF Library** | iText (via Flying Saucer) | 2.x | Low-level PDF generation |
| **CSS Support** | Flying Saucer CSS | Built-in | Inline CSS styling |

### Implementation Details

**HTML Template**: **oci-api/src/main/resources/templates/pdf_slareport.html**

**Template Structure**:
```html
<!DOCTYPE HTML>
<html xmlns:th="http://www.thymeleaf.org">
<head>
    <title>SLA Report</title>
    <style>
        /* Inline CSS styling */
        @page { size: A4 portrait; margin: 20mm; }
        body { font-family: Calibri, Arial, sans-serif; font-size: 11px; }
        .header { text-align: center; border-bottom: 2px solid #2563eb; }
        .section-title { background-color: #eff6ff; color: #1e40af; }
        .compliance-status { padding: 4px 12px; border-radius: 4px; }
        .status-fulfilled { background-color: #dcfce7; color: #166534; }
        .status-breached { background-color: #fee2e2; color: #991b1b; }
        /* ... more styles ... */
    </style>
</head>
<body>
    <!-- Header Section -->
    <div class="header">
        <h1 th:text="${report.slaName}">SLA Report</h1>
        <div class="subtitle" th:text="'Generated: ' + ${#temporals.format(report.generatedAt, 'yyyy-MM-dd HH:mm:ss')}"></div>
    </div>

    <!-- SLA Definition Section -->
    <div class="section">
        <div class="section-title">SLA Definition</div>
        <table class="info-table">
            <tr>
                <td>SLA Name:</td>
                <td th:text="${report.slaName}"></td>
            </tr>
            <tr>
                <td>Metric:</td>
                <td>
                    <span th:text="${report.metricNamespace}"></span> /
                    <span th:text="${report.metricName}"></span>
                </td>
            </tr>
            <!-- ... more rows ... -->
        </table>
    </div>

    <!-- Compliance Summary Section -->
    <div class="section">
        <div class="section-title">Compliance Summary</div>
        <table class="info-table">
            <tr>
                <td>Compliance Status:</td>
                <td>
                    <span class="compliance-status"
                          th:classappend="${report.summary.complianceStatus == 'FULFILLED' ? 'status-fulfilled' : 'status-breached'}"
                          th:text="${report.summary.complianceStatus}">
                    </span>
                </td>
            </tr>
            <!-- ... more rows ... -->
        </table>
    </div>

    <!-- Breach Events Section -->
    <div class="section">
        <div class="section-title">Breach Events</div>
        <table class="breach-table">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Metric Value</th>
                    <th>Threshold</th>
                    <th>Duration (min)</th>
                    <th>Severity</th>
                </tr>
            </thead>
            <tbody>
                <tr th:each="breach : ${report.breaches}">
                    <td th:text="${#temporals.format(breach.timestampLocal, 'yyyy-MM-dd HH:mm:ss')}"></td>
                    <td th:text="${#numbers.formatDecimal(breach.metricValue, 1, 2)}"></td>
                    <td th:text="${#numbers.formatDecimal(breach.threshold, 1, 2)}"></td>
                    <td th:text="${breach.durationMinutes}"></td>
                    <td th:text="${breach.severity}"></td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>
```

**Service Implementation**: **oci-api/service/sla/SlaExportService.java** (Lines 198-230)

```java
public byte[] exportToPdf(SlaReportDto report) throws IOException, DocumentException {
    log.info("Exporting SLA report to PDF: slaId={}, period={}, periodStart={}",
            report.getSlaId(), report.getPeriod(), report.getPeriodStart());

    try {
        // STEP 1: Create Thymeleaf context with report data
        Context context = new Context();
        context.setVariable("report", report);

        // STEP 2: Render HTML template with data
        String html = templateEngine.process("pdf_slareport", context);

        // STEP 3: Convert HTML to PDF using Flying Saucer
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        ITextRenderer renderer = new ITextRenderer(20f * 4f / 3f, 20);

        // Set document from HTML string
        renderer.setDocumentFromString(
            html,
            new ClassPathResource(PDF_RESOURCES).getURL().toExternalForm()
        );

        // Layout the PDF
        renderer.layout();

        // Generate PDF bytes
        renderer.createPDF(outputStream);
        outputStream.close();

        byte[] pdfBytes = outputStream.toByteArray();

        log.info("PDF export completed successfully for SLA: {} - Size: {} bytes",
                report.getSlaName(), pdfBytes.length);

        return pdfBytes;

    } catch (Exception e) {
        log.error("Failed to export SLA report to PDF", e);
        throw e;
    }
}
```

**Controller Endpoint**: **oci-api/controller/sla/SlaReportController.java** (Lines 225-273)

```java
@GetMapping("/{slaId}/export/pdf")
public ResponseEntity<byte[]> exportReportToPdf(
        @PathVariable String slaId,
        @RequestParam SlaPeriodType periodType,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate periodStart
) {
    log.info("GET /api/sla/reports/{}/export/pdf - Exporting to PDF", slaId);

    try {
        // Generate report
        SlaReportDto report = slaReportService.generateReport(
                UUID.fromString(slaId),
                periodType,
                periodStart
        );

        // Export to PDF
        byte[] pdfContent = slaExportService.exportToPdf(report);

        // Generate filename
        String sanitizedSlaName = report.getSlaName()
                .replaceAll("[^a-zA-Z0-9-_]", "_")
                .replaceAll("_+", "_");
        String formattedDate = periodStart.format(DateTimeFormatter.ISO_DATE);
        String filename = String.format("sla-report-%s-%s-%s.pdf",
                sanitizedSlaName,
                periodType.name().toLowerCase(),
                formattedDate);

        // Set headers for file download
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_PDF);
        headers.setContentDispositionFormData("attachment", filename);
        headers.setCacheControl("no-cache, no-store, must-revalidate");

        log.info("PDF export successful - Filename: {} - Size: {} bytes",
                filename, pdfContent.length);

        return ResponseEntity.ok()
                .headers(headers)
                .body(pdfContent);

    } catch (Exception e) {
        log.error("Failed to export SLA report to PDF", e);
        throw new RuntimeException("Failed to export SLA report to PDF", e);
    }
}
```

### PDF Generation Workflow

```
User clicks "Export PDF" button
        ↓
Frontend calls: GET /api/sla/reports/{id}/export/pdf
        ↓
SlaReportController.exportReportToPdf()
        ↓
1. SlaReportService.generateReport()
   - Reads sla_definition from DB
   - Reads sla_breach for period
   - Calculates summary statistics
   - Returns SlaReportDto
        ↓
2. SlaExportService.exportToPdf(reportDto)
   - Creates Thymeleaf Context
   - Sets context.setVariable("report", reportDto)
        ↓
3. TemplateEngine.process("pdf_slareport", context)
   - Loads pdf_slareport.html template
   - Replaces ${report.slaName}, ${report.summary.compliancePercentage}, etc.
   - Evaluates th:each loops for breaches
   - Applies th:classappend for styling
   - Returns HTML string
        ↓
4. ITextRenderer.setDocumentFromString(html)
   - Parses HTML structure
   - Applies inline CSS styles
   - Resolves fonts (Calibri, Arial fallback)
        ↓
5. ITextRenderer.layout()
   - Calculates page layout (A4 portrait)
   - Applies margins (20mm)
   - Breaks content into pages
        ↓
6. ITextRenderer.createPDF(outputStream)
   - Generates PDF bytes
   - Returns ByteArrayOutputStream
        ↓
7. Controller sets HTTP headers:
   - Content-Type: application/pdf
   - Content-Disposition: attachment; filename="sla-report-..."
        ↓
8. Returns ResponseEntity<byte[]>
        ↓
Frontend receives binary PDF data
        ↓
Creates blob URL: window.URL.createObjectURL(blob)
        ↓
Triggers download via <a> element
        ↓
User downloads PDF file
```

## ⚙️ Configuration

### SLA Scheduler CRON Expressions

**File**: **oci-monitor/service/sla/SlaSchedulerService.java**

**CRON Format**: **second minute hour day month weekday**

| Schedule | CRON Expression | When | Processing Window |
|----------|----------------|------|-------------------|
| **Daily** | **0 5 0 \* \* \*** | Every day at 00:05 | Yesterday (00:00-23:59) |
| **Weekly** | **0 10 0 \* \* MON** | Every Monday at 00:10 | Last week (Mon-Sun) |
| **Monthly** | **0 15 0 1 \* \*** | 1st of month at 00:15 | Last month (1st-last day) |

**Why these times?**
- Run AFTER midnight to ensure full day/week/month of data is available
- Stagger execution (05, 10, 15) to avoid database contention
- Process previous period's compliance (not current period)

---

## 🔍 Troubleshooting

### SLA Not Computing

**Symptoms**:
- No **sla_breach** records created
- Reports show 0 data points

**Checks**:

```sql
-- 1. Verify SLA is active and period type matches scheduler
SELECT id, name, is_active, period_type, start_date
FROM sla_definition
WHERE id = :slaId;

-- 2. Verify metric data exists for SLA resource
SELECT COUNT(*) AS metric_count, MIN(time) AS oldest, MAX(time) AS newest
FROM metric_result mr
WHERE mr.resource_ocid = (
    SELECT r.ocid FROM resource r
    JOIN sla_definition sd ON sd.resource_id = r.id
    WHERE sd.id = :slaId
);

-- 3. Check if scheduler ran recently
-- (Look for logs in oci-monitor)
grep "SlaSchedulerService" /var/log/oci-monitor/application.log | tail -20

-- 4. Verify start_date is not in future
SELECT name, start_date, CURDATE() AS today,
       CASE WHEN start_date > CURDATE() THEN 'Future' ELSE 'Active' END AS status
FROM sla_definition
WHERE id = :slaId;
```

**Common Causes**:
- **start_date** is in the future → SLA not yet active
- No metric data collected → OciMetricsScheduler not running
- Resource not linked to OciQuery → No data being collected
- Wrong period_type → Scheduler doesn't process this SLA

---

### Reports Show Wrong Compliance Percentage

**Symptoms**:
- Compliance % doesn't match expectations
- Too many/few data points counted

**Checks**:

```sql
-- 1. Count actual metric data points for period
SELECT COUNT(*) AS total_points
FROM metric_result mr
WHERE mr.resource_ocid = :resourceOcid
  AND mr.time BETWEEN :periodStart AND :periodEnd;

-- 2. Check downtime windows that might exclude points
SELECT * FROM sla_downtime_window
WHERE sla_definition_id = :slaId
  AND end_time >= :periodStart
  AND start_time <= :periodEnd;

-- 3. Check schedule mode (24/7 vs Business Hours)
SELECT schedule_mode, custom_schedule
FROM sla_definition
WHERE id = :slaId;
```

**Debug Steps**:
1. Verify period range (check timezone conversions)
2. Check downtime exclusions (are they correct?)
3. Verify schedule mode filtering (24/7 vs business hours)
4. Check comparator logic (LT vs GT vs LTE vs GTE)

---

### PDF Export Fails

**Symptoms**:
- HTTP 500 error on **/export/pdf**
- "DocumentException" in logs

**Checks**:

```bash
# Check logs
grep "exportToPdf" /var/log/oci-api/application.log | tail -20

# Common errors:
# - "Template not found" → Check pdf_slareport.html exists in resources/templates
# - "Font not found" → Use system fonts only (Arial, Calibri)
# - "CSS parse error" → Check CSS is valid CSS 2.1
```

**Solutions**:
- Verify **pdf_slareport.html** exists at **oci-api/src/main/resources/templates/pdf_slareport.html**
- Check Thymeleaf syntax is correct (**th:text**, **th:each**, etc.)
- Simplify CSS if errors occur (Flying Saucer supports CSS 2.1 only)
- Check report data is not null (all required fields populated)

---

## 🔧 Scheduler Architecture

### Overview

The SLA Scheduler system uses a **two-layer architecture** for clean separation of concerns:

1. **Scheduler Layer** (`@Component`) - Handles Spring scheduling and toggle logic
2. **Service Layer** (`@Service`) - Contains business logic for SLA computation

This architecture aligns with other schedulers in the OCI Backend system (Metrics, Budget, Cost schedulers).

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           SLA Scheduler Architecture                          │
└──────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│  SCHEDULER LAYER (oci-monitor/scheduler/)                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  SlaScheduler.java  (@Component)                                │     │
│  │                                                                  │     │
│  │  @Scheduled(cron = "0 5 0 * * *")                               │     │
│  │  scheduleDailySlas() {                                          │     │
│  │    if (!schedulerToggleService.isTaskEnabled("sla.scheduled     │     │
│  │       log.info("Daily SLA scheduler disabled");                 │     │
│  │       return;                                                    │     │
│  │    }                                                             │     │
│  │    slaSchedulerService.processPeriodType(DAILY, yesterday);     │     │
│  │  }                                                               │     │
│  │                                                                  │     │
│  │  @Scheduled(cron = "0 10 0 * * MON")                            │     │
│  │  scheduleWeeklySlas() { ... }                                   │     │
│  │                                                                  │     │
│  │  @Scheduled(cron = "0 15 0 1 * *")                              │     │
│  │  scheduleMonthlySlas() { ... }                                  │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                            ↓                                              │
│                   Calls                                                   │
│                            ↓                                              │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│  TOGGLE SERVICE (oci-monitor/service/scheduler/)                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  SchedulerToggleService.java  (@Service)                        │     │
│  │                                                                  │     │
│  │  isTaskEnabled(String taskName) {                               │     │
│  │    return schedulerSettingsRepository                           │     │
│  │        .findBySchedulerTaskName(taskName)                       │     │
│  │        .map(SchedulerSettings::isEnabled)                       │     │
│  │        .orElse(false);  // Default: disabled                    │     │
│  │  }                                                               │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                            ↓                                              │
│                   Queries                                                 │
│                            ↓                                              │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│  DATABASE (scheduler_settings table)                                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  scheduler_settings                                              │     │
│  │  ─────────────────────────────────────────────────────────────  │     │
│  │  | task_name             | is_enabled |                         │     │
│  │  | sla.scheduled.daily   | true       |  ← Daily SLA enabled    │     │
│  │  | sla.scheduled.weekly  | true       |  ← Weekly SLA enabled   │     │
│  │  | sla.scheduled.monthly | true       |  ← Monthly SLA enabled  │     │
│  │  | metrics.scheduled...  | true       |  ← Other schedulers     │     │
│  │  | cost.scheduled...     | false      |                         │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│  BUSINESS LOGIC LAYER (oci-monitor/service/sla/)                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  SlaSchedulerService.java  (@Service)                           │     │
│  │                                                                  │     │
│  │  processPeriodType(periodType, periodDate, now) {               │     │
│  │    // Business logic - NO @Scheduled here                       │     │
│  │    List<SlaDefinition> slas = repo.find...(periodType);         │     │
│  │    for (SlaDefinition sla : slas) {                             │     │
│  │        slaComputationService.computeSla(...);                   │     │
│  │    }                                                             │     │
│  │  }                                                               │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                            ↓                                              │
│                   Calls                                                   │
│                            ↓                                              │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  SlaComputationService.java  (@Service)                         │     │
│  │                                                                  │     │
│  │  computeSla(slaDefinitionId, periodDate, forceRecompute, by) { │     │
│  │    // Load SLA definition                                       │     │
│  │    // Load metric data from DB                                  │     │
│  │    // Calculate compliance                                      │     │
│  │    // Detect breaches                                           │     │
│  │    // Save results                                              │     │
│  │  }                                                               │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Location | Responsibility | Contains @Scheduled? |
|-----------|----------|----------------|----------------------|
| **SlaScheduler** | oci-monitor/scheduler/SlaScheduler.java | Spring scheduling, toggle checks | ✅ YES |
| **SchedulerToggleService** | oci-monitor/service/scheduler/SchedulerToggleService.java | Enable/disable logic | ❌ NO |
| **SlaSchedulerService** | oci-monitor/service/sla/SlaSchedulerService.java | Batch processing business logic | ❌ NO |
| **SlaComputationService** | oci-monitor/service/sla/SlaComputationService.java | Individual SLA computation | ❌ NO |

### Scheduler Toggle Mechanism

**How it works:**

1. **Scheduler starts** (Spring Boot initialization)
   ```java
   @Scheduled(cron = "0 5 0 * * *")
   public void scheduleDailySlas() { ... }
   ```

2. **First check: Is task enabled?**
   ```java
   if (!schedulerToggleService.isTaskEnabled("sla.scheduled.daily")) {
       log.info("Daily SLA scheduler disabled");
       return;  // Exit early, don't execute
   }
   ```

3. **Query database**
   ```sql
   SELECT is_enabled FROM scheduler_settings
   WHERE scheduler_task_name = 'sla.scheduled.daily';
   ```

4. **Decision:**
   - If is_enabled = true → Execute scheduler
   - If is_enabled = false → Skip execution
   - If row not found → Default to false (disabled)

5. **Execution continues** (if enabled)
   ```java
   slaSchedulerService.processPeriodType(SlaPeriodType.DAILY, yesterday, now);
   ```

**Runtime Control:**

Administrators can enable/disable schedulers without redeployment:

```sql
-- Disable daily SLA scheduler
UPDATE scheduler_settings
SET is_enabled = false
WHERE scheduler_task_name = 'sla.scheduled.daily';

-- Enable weekly SLA scheduler
UPDATE scheduler_settings
SET is_enabled = true
WHERE scheduler_task_name = 'sla.scheduled.weekly';
```

### Scheduler Task Names

| Period Type | Task Name | CRON Schedule | When Runs |
|-------------|-----------|---------------|-----------|
| **DAILY** | sla.scheduled.daily | 0 5 0 * * * | Every day at 00:05 |
| **WEEKLY** | sla.scheduled.weekly | 0 10 0 * * MON | Every Monday at 00:10 |
| **MONTHLY** | sla.scheduled.monthly | 0 15 0 1 * * | 1st of month at 00:15 |

### Scheduler vs Manual Trigger Mapping

This table shows how each scheduled SLA computation can be triggered manually via REST API, useful for testing and on-demand execution:

| Functionality | Scheduler Method | Manual Trigger Endpoint | Example Request | Scheduler Toggle |
|--------------|------------------|------------------------|-----------------|------------------|
| **Daily SLA Computation** | SlaScheduler.scheduleDailySlas()<br>📅 Every day at 00:05 | POST /api/sla/trigger | {"slaDefinitionId": "your-uuid", "periodStart": "2025-11-07", "forceRecompute": false} | sla.scheduled.daily |
| **Weekly SLA Computation** | SlaScheduler.scheduleWeeklySlas()<br>📅 Every Monday at 00:10 | POST /api/sla/trigger | {"slaDefinitionId": "your-uuid", "periodStart": "2025-11-04", "forceRecompute": false} | sla.scheduled.weekly |
| **Monthly SLA Computation** | SlaScheduler.scheduleMonthlySlas()<br>📅 1st of month at 00:15 | POST /api/sla/trigger | {"slaDefinitionId": "your-uuid", "periodStart": "2025-11-01", "forceRecompute": false} | sla.scheduled.monthly |

**Key Points:**

- **Same endpoint for all**: All three period types use the same POST /api/sla/trigger endpoint
- **Period detection**: The system automatically determines period type (DAILY/WEEKLY/MONTHLY) based on the SLA definition
- **Force recompute**: Set forceRecompute: true to override existing results
- **Scheduler toggle**: Use scheduler_settings table to enable/disable automatic execution
- **Testing workflow**:
  1. Create SLA definition with desired period type
  2. Use manual trigger to test immediately (no need to wait for scheduled time)
  3. Enable scheduler once tested

**Full API Documentation:** See [Manual Trigger API](#manual-trigger-api) section for complete details.

### Migration: Adding Scheduler Settings

**Database Migration:** V8__add_sla_scheduler_settings.sql

```sql
-- Ensure scheduler_settings table exists
CREATE TABLE IF NOT EXISTS scheduler_settings (
    id CHAR(36) NOT NULL,
    scheduler_task_name VARCHAR(255) NOT NULL UNIQUE,
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME(6) NOT NULL,
    created_by VARCHAR(255),
    updated_at DATETIME(6),
    updated_by VARCHAR(255),
    version BIGINT,
    deleted_at DATETIME(6),
    PRIMARY KEY (id),
    INDEX idx_scheduler_task_name (scheduler_task_name)
) ENGINE=InnoDB;

-- Insert SLA scheduler tasks (enabled by default)
INSERT INTO scheduler_settings
    (id, scheduler_task_name, is_enabled, created_at, created_by, version)
VALUES
    (UUID(), 'sla.scheduled.daily', true, NOW(), 'system', 1),
    (UUID(), 'sla.scheduled.weekly', true, NOW(), 'system', 1),
    (UUID(), 'sla.scheduled.monthly', true, NOW(), 'system', 1)
ON DUPLICATE KEY UPDATE
    scheduler_task_name = scheduler_task_name;
```

**Execution:** Flyway runs this migration automatically on application startup.

### Code Examples

**Scheduler Layer:**

```java
// oci-monitor/scheduler/SlaScheduler.java
@Slf4j
@Component
@RequiredArgsConstructor
public class SlaScheduler {

   private final SchedulerToggleService schedulerToggleService;
   private final SlaSchedulerService slaSchedulerService;

   @Scheduled(cron = "0 5 0 * * *")
   public void scheduleDailySlas() {
      // Check if enabled
      if (!schedulerToggleService.isTaskEnabled("sla.scheduled.daily")) {
         log.info("SlaScheduler:: Daily SLA scheduler is disabled. Skipping execution.");
         return;
      }

      log.info("=== DAILY SLA Scheduler Started ===");

      LocalDateTime now = LocalDateTime.now();
      LocalDate yesterday = LocalDate.now().minusDays(1);

      try {
         // Call business logic
         slaSchedulerService.processPeriodType(SlaPeriodType.DAILY, yesterday, now);
         log.info("=== DAILY SLA Scheduler Completed Successfully ===");
      } catch (Exception e) {
         log.error("=== DAILY SLA Scheduler Failed: {} ===", e.getMessage(), e);
      }
   }
}
```

**Service Layer:**

```java
// oci-monitor/service/sla/SlaSchedulerService.java
@Slf4j
@Service
@RequiredArgsConstructor
public class SlaSchedulerService {

    private final SlaDefinitionRepository slaDefinitionRepository;
    private final SlaComputationService slaComputationService;

    public void processPeriodType(SlaPeriodType periodType, LocalDate periodDate, LocalDateTime now) {
        log.info("Processing {} SLAs for period date: {}", periodType, periodDate);

        // Find all currently active SLA definitions for this period type
        List<SlaDefinition> slaDefinitions = slaDefinitionRepository
                .findCurrentlyActiveByPeriodType(periodType, now);

        if (slaDefinitions.isEmpty()) {
            log.info("No active {} SLA definitions found", periodType);
            return;
        }

        log.info("Found {} active {} SLA definitions to process", slaDefinitions.size(), periodType);

        // Process each SLA definition
        for (SlaDefinition slaDefinition : slaDefinitions) {
            try {
                slaComputationService.computeSla(
                    slaDefinition.getId(),
                    periodDate,
                    false,  // Don't force recompute
                    "scheduler"
                );
            } catch (Exception e) {
                log.error("Failed to process SLA definition {}: {}", 
                    slaDefinition.getId(), e.getMessage(), e);
            }
        }
    }
}
```

---

## 📅 SLA Scheduled Reports

### Overview

**SLA Scheduled Reports** (Pristup 1: Pre-Generated Reports sa Scheduler Storage) is an advanced feature that enables **automatic generation and storage** of SLA reports on predefined schedules. Unlike on-demand report generation, scheduled reports are:

- **Pre-generated** - Reports are created automatically by schedulers (weekly, monthly, quarterly)
- **Fully stored** - Complete report data (not just metadata) is saved in the database
- **Email-enabled** - Automatic notifications with PDF/CSV attachments
- **Archive-supported** - Old reports can be archived to manage database size
- **Historically tracked** - All generated reports are preserved for compliance and auditing

### Key Benefits

| Feature | On-Demand Reports | Scheduled Reports ✅ |
|---------|-------------------|----------------------|
| **Generation** | Manual, via API | Automatic, on schedule |
| **Storage** | Generated each time | Pre-generated, stored once |
| **Performance** | Slower (computes each time) | Faster (reads from storage) |
| **Historical Access** | Must regenerate | Instant access to past reports |
| **Email Notifications** | Manual | Automatic with attachments |
| **Compliance Tracking** | Requires regeneration | Complete audit trail |
| **Resource Usage** | High (repeats computation) | Low (computes once) |

### Database Architecture

The scheduled reports feature adds **3 new tables** to the SLA module:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SLA Scheduled Reports Schema                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  sla_definition      │
│  ──────────────────  │
│  - id (PK)           │
│  - name              │
│  - metric_threshold  │
│  - target_value      │
└───────┬──────────────┘
        │
        │ 1:N (one SLA can have multiple report schedules)
        ↓
┌──────────────────────────┐
│  sla_report_schedule     │ ← Configuration for automated report generation
│  ──────────────────────  │
│  - id (PK)               │
│  - sla_definition_id (FK)│
│  - schedule_name         │
│  - period_type           │ ← WEEKLY, MONTHLY, QUARTERLY
│  - frequency             │ ← WEEKLY, MONTHLY, QUARTERLY, CUSTOM
│  - cron_expression       │ ← Optional custom schedule
│  - timezone              │
│  - is_active             │
│  - email_recipients      │ ← Comma-separated emails
│  - include_pdf_attach    │
│  - include_csv_attach    │
│  - auto_archive_days     │ ← Auto-archive after N days
│  - last_run_at           │
│  - next_run_at           │
│  - total_reports_gen     │
└────────┬─────────────────┘
         │
         │ 1:N (one schedule generates many reports)
         ↓
┌────────────────────────────┐
│  sla_report                │ ← Stored/pre-generated SLA reports
│  ────────────────────────  │
│  - id (PK)                 │
│  - sla_definition_id (FK)  │
│  - report_schedule_id (FK) │ ← Link to schedule that generated it
│  - report_name             │
│  - period_type             │
│  - period_start_utc        │
│  - period_end_utc          │
│                            │
│  ── Compliance Summary ──  │
│  - compliance_percent      │
│  - compliance_status       │ ← FULFILLED, AT_RISK, BREACHED
│  - target_percent          │
│  - deviation_percent       │
│  - total_minutes_in_period │
│  - uptime_minutes          │
│  - downtime_minutes        │
│  - excluded_downtime_min   │
│                            │
│  ── Breach Summary ──      │
│  - total_breaches          │
│  - critical_breaches       │
│  - high_breaches           │
│  - medium_breaches         │
│  - low_breaches            │
│  - total_breach_duration   │
│  - longest_breach_duration │
│  - mttr_minutes            │ ← Mean Time To Recovery
│  - has_breaches            │
│                            │
│  ── Availability Metrics ── │
│  - availability_percent    │
│  - data_coverage_percent   │
│  - total_data_points       │
│  - missing_data_points     │
│                            │
│  ── Metadata ──            │
│  - report_status           │ ← DRAFT, PUBLISHED, ARCHIVED
│  - report_format           │ ← JSON, PDF, CSV, HYBRID
│  - generation_duration_ms  │
│  - generated_at            │
│  - generated_by            │
│                            │
│  ── Notification ──        │
│  - notification_sent       │
│  - notification_sent_at    │
│  - notification_recipients │
│                            │
│  ── Archive ──             │
│  - archived_at             │
│  - archived_by             │
└────────┬───────────────────┘
         │
         │ 1:N (one report has many breach events)
         ↓
┌──────────────────────────────┐
│  sla_report_breach_summary   │ ← Breach events within a report
│  ────────────────────────────│
│  - id (PK)                   │
│  - sla_report_id (FK)        │
│  - sla_breach_id (FK)        │ ← Link to original breach
│  - breach_detected_at        │
│  - breach_duration_minutes   │
│  - breach_severity           │ ← CRITICAL, HIGH, MEDIUM, LOW
│  - actual_value              │
│  - threshold_value           │
│  - deviation_percent         │
│  - breach_description        │
│  - is_resolved               │
│  - resolved_at               │
└──────────────────────────────┘

WORKFLOW:
1. Admin creates sla_report_schedule (e.g., "Generate monthly reports every 1st at 2 AM")
2. Scheduler wakes up at specified time (e.g., 2025-12-01 02:00)
3. Scheduler generates full SLA report for previous period (November)
4. Full report data saved to sla_report table (all metrics, compliance, breaches)
5. Breach summaries saved to sla_report_breach_summary (snapshot of breaches)
6. Email sent to recipients with PDF/CSV attachments (if configured)
7. Old reports auto-archived after N days (if auto_archive_days configured)
8. Users can view historical reports instantly (no regeneration needed)
```

---

### How It Works

#### 1. Create Report Schedule

**Via Frontend UI** or **REST API**:

```json
POST /api/sla/report-schedules
{
  "slaDefinitionId": "sla-uuid-abc",
  "scheduleName": "Monthly Production API Reports",
  "scheduleDescription": "Automated monthly SLA reports for production API",
  "periodType": "MONTHLY",
  "frequency": "MONTHLY",
  "timezone": "Europe/Belgrade",
  "isActive": true,
  "emailRecipients": "ops@sistemi.rs, management@sistemi.rs",
  "includePdfAttachment": true,
  "includeCsvAttachment": true,
  "autoArchiveAfterDays": 90
}
```

**What this creates:**
- A **schedule configuration** that tells the system:
  - **What:** Generate reports for SLA "sla-uuid-abc"
  - **When:** Monthly (1st of month at predetermined time)
  - **Format:** Both PDF and CSV
  - **Notify:** Send email to ops@sistemi.rs and management@sistemi.rs
  - **Archive:** Auto-archive reports older than 90 days

#### 2. Scheduler Executes

**Scheduler Types:**

| Frequency | CRON Expression | Runs At | Example |
|-----------|----------------|---------|---------|
| **WEEKLY** | 0 0 2 * * MON | Every Monday 02:00 | Generate report for last week (Mon-Sun) |
| **MONTHLY** | 0 0 3 1 * * | 1st of month 03:00 | Generate report for last month (1st-last day) |
| **QUARTERLY** | 0 0 4 1 1,4,7,10 * | 1st of Jan/Apr/Jul/Oct 04:00 | Generate report for last quarter |
| **CUSTOM** | User-defined | User-defined | e.g., "0 0 5 15 * *" (15th of month 05:00) |

**Execution Flow:**

```java
// oci-monitor/scheduler/SlaReportScheduler.java

@Scheduled(cron = "0 0 3 1 * *")  // 1st of month at 03:00
public void scheduleMonthlyReports() {
    log.info("=== MONTHLY SLA Report Scheduler Started ===");

    // 1. Find all active MONTHLY report schedules
    List<SlaReportSchedule> schedules = scheduleRepository
        .findActiveSchedulesDueForExecution(ScheduleFrequency.MONTHLY, LocalDateTime.now());

    for (SlaReportSchedule schedule : schedules) {
        try {
            // 2. Generate full SLA report for last month
            SlaReport report = slaReportGenerationService.generateAndStoreReport(
                schedule.getSlaDefinition().getId(),
                schedule.getPeriodType(),
                getLastMonthStart(),  // e.g., 2025-11-01
                schedule.getId()
            );

            // 3. Update schedule execution tracking
            schedule.recordSuccessfulExecution(report.getId(), calculateNextRun());
            scheduleRepository.save(schedule);

            // 4. Send email notification (if configured)
            if (schedule.hasEmailRecipients()) {
                emailService.sendReportNotification(report, schedule);
            }

            log.info("Generated report {} for schedule {}", report.getId(), schedule.getScheduleName());

        } catch (Exception e) {
            log.error("Failed to generate report for schedule {}: {}",
                schedule.getScheduleName(), e.getMessage(), e);
        }
    }

    log.info("=== MONTHLY SLA Report Scheduler Completed ===");
}
```

#### 3. Report Generation Process

```
STEP 1: Compute SLA Compliance
───────────────────────────────────────
- Call SlaComputationService.computeSla()
- Load metric data for period (e.g., November 2025)
- Calculate compliance percentage
- Detect breaches
- Apply penalties if applicable

Result: SlaComplianceSummaryDto
{
  compliancePercent: 99.48,
  targetValue: 99.50,
  complianceStatus: "BREACHED",
  totalBreaches: 44,
  totalBreachDurationMinutes: 220,
  ...
}


STEP 2: Create SlaReport Entity
───────────────────────────────────────
SlaReport report = new SlaReport();
report.setSlaDefinition(slaDefinition);
report.setReportSchedule(schedule);
report.setReportName("Monthly CPU SLA - November 2025");
report.setPeriodType(SlaPeriodType.MONTHLY);
report.setPeriodStartUtc(LocalDateTime.of(2025, 11, 1, 0, 0));
report.setPeriodEndUtc(LocalDateTime.of(2025, 12, 1, 0, 0));

// Compliance summary
report.setCompliancePercent(99.48);
report.setComplianceStatus("BREACHED");
report.setTargetPercent(99.50);
report.setDeviationPercent(-0.02);
report.setTotalMinutesInPeriod(43200);  // 30 days
report.setUptimeMinutes(42980);
report.setDowntimeMinutes(220);

// Breach summary
report.setTotalBreaches(44);
report.setCriticalBreaches(2);
report.setHighBreaches(8);
report.setMediumBreaches(18);
report.setLowBreaches(16);
report.setTotalBreachDurationMinutes(220);
report.setLongestBreachDurationMinutes(45);
report.setMttrMinutes(5);  // Mean Time To Recovery
report.setHasBreaches(true);

// Availability metrics
report.setAvailabilityPercent(99.49);
report.setDataCoveragePercent(100.0);
report.setTotalDataPoints(8640);
report.setMissingDataPoints(0);

// Metadata
report.setReportStatus(ReportStatus.PUBLISHED);
report.setReportFormat(ReportFormat.HYBRID);  // JSON + PDF + CSV
report.setGenerationDurationMs(1247);
report.setGeneratedAt(LocalDateTime.now());
report.setGeneratedBy("scheduler");

slaReportRepository.save(report);


STEP 3: Create Breach Summaries
───────────────────────────────────────
// For each breach in the period, create a summary snapshot
for (SlaBreach breach : breaches) {
    SlaReportBreachSummary breachSummary = new SlaReportBreachSummary();
    breachSummary.setSlaReport(report);
    breachSummary.setSlaBreach(breach);  // Link to original
    breachSummary.setBreachDetectedAt(breach.getTimestamp());
    breachSummary.setBreachDurationMinutes(breach.getDurationMinutes());
    breachSummary.setBreachSeverity(breach.getSeverity());
    breachSummary.setActualValue(breach.getMetricValue());
    breachSummary.setThresholdValue(breach.getThreshold());
    breachSummary.setIsResolved(breach.getIsResolved());
    breachSummary.setResolvedAt(breach.getResolvedAt());

    report.addBreachSummary(breachSummary);
}

slaReportRepository.save(report);  // Cascade saves breach summaries


STEP 4: Send Email Notification (Optional)
───────────────────────────────────────
if (schedule.hasEmailRecipients() && schedule.getIncludePdfAttachment()) {
    // Generate PDF from report
    byte[] pdfBytes = pdfExportService.generatePdf(report);

    // Generate CSV from report
    byte[] csvBytes = csvExportService.generateCsv(report);

    // Send email
    emailService.sendEmail(
        to: schedule.getEmailRecipients(),
        subject: "SLA Report: " + report.getReportName(),
        body: buildEmailBody(report),
        attachments: [
            {filename: "sla-report.pdf", content: pdfBytes},
            {filename: "sla-report.csv", content: csvBytes}
        ]
    );

    // Record notification
    report.recordNotificationSent(schedule.getEmailRecipients());
    slaReportRepository.save(report);
}


STEP 5: Update Schedule Tracking
───────────────────────────────────────
schedule.setLastRunAt(LocalDateTime.now());
schedule.setLastReportId(report.getId());
schedule.setNextRunAt(calculateNextRun());  // e.g., 2025-12-01 03:00
schedule.setTotalReportsGenerated(schedule.getTotalReportsGenerated() + 1);

scheduleRepository.save(schedule);
```

#### 4. Access Stored Reports

**Via Frontend UI:**

Users can browse all generated reports without triggering new computations:

```typescript
// List all reports
GET /api/sla/reports/scheduled
→ Returns: List of all stored reports (fast, no computation)

// Get specific report
GET /api/sla/reports/scheduled/{reportId}
→ Returns: Full report with all metrics and breaches

// Download PDF
GET /api/sla/reports/scheduled/{reportId}/pdf
→ Returns: Pre-generated PDF (instant download)

// Download CSV
GET /api/sla/reports/scheduled/{reportId}/csv
→ Returns: Pre-generated CSV (instant download)
```

**Via REST API:**

```bash
# Get latest monthly report for SLA
curl -X GET "http://localhost:8080/api/sla/reports/scheduled/latest?slaDefinitionId=sla-uuid&periodType=MONTHLY"

# Filter reports by date range
curl -X GET "http://localhost:8080/api/sla/reports/scheduled?slaDefinitionId=sla-uuid&startDate=2025-01-01&endDate=2025-12-31"

# Get reports with breaches only
curl -X GET "http://localhost:8080/api/sla/reports/scheduled?hasBreaches=true"
```

---

### Archive Management

**Automatic Archival:**

Reports can be automatically archived after a specified number of days to manage database size:

```java
// Configuration in schedule
schedule.setAutoArchiveAfterDays(90);  // Auto-archive after 90 days

// Archival scheduler (runs daily)
@Scheduled(cron = "0 0 1 * * *")  // Daily at 01:00
public void archiveOldReports() {
    LocalDateTime threshold = LocalDateTime.now().minusDays(90);

    List<SlaReport> eligibleReports = slaReportRepository
        .findReportsEligibleForArchive(threshold, ReportStatus.PUBLISHED);

    for (SlaReport report : eligibleReports) {
        report.archive("scheduler");  // Sets status to ARCHIVED
        slaReportRepository.save(report);
        log.info("Archived report: {}", report.getId());
    }
}
```

**Manual Archive:**

```bash
# Archive specific report
POST /api/sla/reports/scheduled/{reportId}/archive
→ Changes status from PUBLISHED to ARCHIVED
```

**Delete Archived Reports:**

```bash
# Delete archived report (only ARCHIVED reports can be deleted)
DELETE /api/sla/reports/scheduled/{reportId}
→ Permanently removes report from database
```

**Archive States:**

| Status | Can View? | Can Download? | Can Delete? | Description |
|--------|-----------|---------------|-------------|-------------|
| **DRAFT** | ✅ Yes | ❌ No | ✅ Yes | Report being generated |
| **PUBLISHED** | ✅ Yes | ✅ Yes | ❌ No | Active report |
| **ARCHIVED** | ✅ Yes | ✅ Yes | ✅ Yes | Old report, can be deleted |

---

### Frontend UI Components

**1. Report Schedules List Page** (`SlaReportScheduleListPage.tsx`)
- Lists all configured report schedules
- Shows: Schedule name, SLA definition, frequency, status, last/next run
- Actions: Create, Edit, Delete, Activate/Deactivate, Trigger Manual

**2. Schedule Form Page** (`SlaReportScheduleFormPage.tsx`)
- Create/Edit report schedule configuration
- Configure: Name, SLA, frequency, timezone, email settings, archive policy

**3. Stored Reports List Page** (Future)
- Browse all generated reports
- Filter by: SLA, date range, status, has breaches
- Actions: View, Download PDF/CSV, Archive, Delete

---

### REST API Endpoints

#### Schedule Management

```
GET    /api/sla/report-schedules                  List all schedules
GET    /api/sla/report-schedules/{id}             Get schedule by ID
POST   /api/sla/report-schedules                  Create new schedule
PUT    /api/sla/report-schedules/{id}             Update schedule
DELETE /api/sla/report-schedules/{id}             Delete schedule
PATCH  /api/sla/report-schedules/{id}/status      Activate/Deactivate
POST   /api/sla/report-schedules/{id}/trigger     Manual trigger generation
```

#### Report Access

```
GET    /api/sla/reports/scheduled                 List all reports (paginated)
GET    /api/sla/reports/scheduled/{id}            Get report by ID
GET    /api/sla/reports/scheduled/latest          Get latest report for SLA
GET    /api/sla/reports/scheduled/{id}/pdf        Download PDF
GET    /api/sla/reports/scheduled/{id}/csv        Download CSV
POST   /api/sla/reports/scheduled/{id}/archive    Archive report
DELETE /api/sla/reports/scheduled/{id}            Delete archived report
```

---

### Configuration Example

**Complete Schedule Setup:**

```json
{
  "slaDefinitionId": "550e8400-e29b-41d4-a716-446655440000",
  "scheduleName": "Monthly Production SLA Reports",
  "scheduleDescription": "Automated monthly reports for production API SLA compliance",
  "periodType": "MONTHLY",
  "frequency": "MONTHLY",
  "timezone": "Europe/Belgrade",
  "isActive": true,
  "emailRecipients": "ops-team@sistemi.rs, cto@sistemi.rs, compliance@sistemi.rs",
  "includePdfAttachment": true,
  "includeCsvAttachment": true,
  "autoArchiveAfterDays": 365
}
```

**What this does:**
1. **Every 1st of the month** at **03:00 Belgrade time**
2. Generates **full SLA report** for **last month**
3. Saves **complete report** to database (all metrics, breaches, compliance data)
4. Sends **email** to 3 recipients with **PDF and CSV** attachments
5. Reports older than **365 days** are automatically **archived**

---

### Benefits Over On-Demand Reports

**1. Performance:**
- **On-demand:** Computes each time (slow, 2-5 seconds)
- **Scheduled:** Pre-computed, instant access (< 100ms)

**2. Historical Tracking:**
- **On-demand:** Must regenerate past periods (data might change)
- **Scheduled:** Preserves exact state at time of generation

**3. Compliance Auditing:**
- **On-demand:** No audit trail of what was reported
- **Scheduled:** Complete history of all reports sent

**4. Automation:**
- **On-demand:** Manual effort required
- **Scheduled:** Fully automated, zero manual work

**5. Email Notifications:**
- **On-demand:** No email capability
- **Scheduled:** Automatic notifications with attachments

---

## 🕐 SLA Excluded Downtime Management

### Overview

**Excluded Downtime** (also called **Maintenance Windows**) allows you to define time periods when SLA monitoring should be paused. Data points collected during excluded downtime periods do NOT count toward SLA compliance calculations.

**Use Cases:**
- **Planned Maintenance** - Database migrations, system upgrades
- **Scheduled Downtime** - Approved service windows
- **Development/Testing** - Exclude non-production hours
- **Holiday Periods** - Exclude specific dates from SLA tracking

**Example Scenario:**
```
SLA: Database CPU should be < 80% for 99.5% of time

Without excluded downtime:
- Database maintenance at 2 AM causes CPU spikes to 95%
- This counts as SLA breach, even though it was planned

With excluded downtime:
- Create downtime period: 2024-12-15 02:00 - 2024-12-15 04:00
- Maintenance CPU spikes are excluded from compliance calculation
- SLA compliance percentage accurately reflects production performance
```

### Database Schema

**Table:** `sla_excluded_downtime`

```sql
CREATE TABLE `sla_excluded_downtime` (
     `id` binary(16) NOT NULL,
     `sla_definition_id` char(36) NOT NULL,
     `name` varchar(255) NOT NULL,
     `description` varchar(1000) NULL,
     `period_from` datetime(6) NOT NULL,
     `period_to` datetime(6) NOT NULL,
     `created_at` datetime(6) DEFAULT NULL,
     `created_by` varchar(100) DEFAULT NULL,
     `updated_at` datetime(6) DEFAULT NULL,
     `updated_by` varchar(100) DEFAULT NULL,
     PRIMARY KEY (`id`),
     KEY `idx_sla_excluded_downtime_definition_id` (`sla_definition_id`),
     KEY `idx_sla_excluded_downtime_updated_at` (`updated_at`),
     CONSTRAINT `fk_sla_excluded_downtime_definition_id`
         FOREIGN KEY (`sla_definition_id`) REFERENCES `sla_definition` (`id`)
);
```

**Relationship:** `sla_definition` 1 → N `sla_excluded_downtime`

### Backend Architecture

#### Layer 1: Entity (oci-library)

**File:** `oci-library/.../entity/sla/SlaExcludedDowntime.java`

```java
@Entity
@Table(name = "sla_excluded_downtime")
public class SlaExcludedDowntime {
    @Id
    @GeneratedValue
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sla_definition_id", nullable = false)
    private SlaDefinition slaDefinition;

    private String name;
    private String description;
    private LocalDateTime periodFrom;
    private LocalDateTime periodTo;

    // Audit fields
    private LocalDateTime createdAt;
    private String createdBy;
    private LocalDateTime updatedAt;
    private String updatedBy;

    // Helper methods
    public boolean contains(LocalDateTime timestamp) {
        return !timestamp.isBefore(periodFrom) && !timestamp.isAfter(periodTo);
    }

    public long getDurationMinutes() {
        return Duration.between(periodFrom, periodTo).toMinutes();
    }
}
```

#### Layer 2: DTOs (oci-library)

**Request DTOs:**

```java
// CreateSlaExcludedDowntimeRequest.java
public class CreateSlaExcludedDowntimeRequest {
    @NotBlank
    private String name;
    private String description;

    @NotNull
    private LocalDateTime periodFrom;

    @NotNull
    private LocalDateTime periodTo;

    public boolean isValid() {
        return name != null && !name.isBlank()
            && periodFrom != null && periodTo != null
            && periodTo.isAfter(periodFrom);
    }
}

// UpdateSlaExcludedDowntimeRequest.java
public class UpdateSlaExcludedDowntimeRequest {
    private String name;              // Optional
    private String description;       // Optional
    private LocalDateTime periodFrom; // Optional
    private LocalDateTime periodTo;   // Optional
}
```

**Response DTO:**

```java
// SlaExcludedDowntimeResponseDto.java
public class SlaExcludedDowntimeResponseDto {
    private UUID id;
    private UUID slaDefinitionId;
    private String slaDefinitionName;
    private String name;
    private String description;
    private LocalDateTime periodFrom;
    private LocalDateTime periodTo;
    private Long durationMinutes;
    private LocalDateTime createdAt;
    private String createdBy;
    private LocalDateTime updatedAt;
    private String updatedBy;
}
```

#### Layer 3: Repository (oci-api)

**File:** `oci-api/.../repository/sla/SlaExcludedDowntimeRepository.java`

**Key Query Methods:**

```java
@Repository
public interface SlaExcludedDowntimeRepository extends JpaRepository<SlaExcludedDowntime, UUID> {

    // Get all for SLA definition with relationship loaded
    @Query("SELECT ed FROM SlaExcludedDowntime ed " +
           "LEFT JOIN FETCH ed.slaDefinition " +
           "WHERE ed.slaDefinition.id = :slaDefinitionId " +
           "ORDER BY ed.periodFrom ASC")
    List<SlaExcludedDowntime> findBySlaDefinitionIdWithRelationship(
            @Param("slaDefinitionId") UUID slaDefinitionId);

    // Check for overlapping periods (for validation)
    @Query("SELECT CASE WHEN COUNT(ed) > 0 THEN true ELSE false END " +
           "FROM SlaExcludedDowntime ed " +
           "WHERE ed.slaDefinition.id = :slaDefinitionId " +
           "AND ed.periodTo >= :periodStart " +
           "AND ed.periodFrom <= :periodEnd " +
           "AND (:excludeId IS NULL OR ed.id <> :excludeId)")
    boolean existsOverlappingPeriods(
            @Param("slaDefinitionId") UUID slaDefinitionId,
            @Param("periodStart") LocalDateTime periodStart,
            @Param("periodEnd") LocalDateTime periodEnd,
            @Param("excludeId") UUID excludeId);

    // Find active downtimes (current time within period)
    @Query("SELECT ed FROM SlaExcludedDowntime ed " +
           "WHERE ed.slaDefinition.id = :slaDefinitionId " +
           "AND ed.periodFrom <= :now " +
           "AND ed.periodTo >= :now")
    List<SlaExcludedDowntime> findActiveDowntimesBySlaDefinition(
            @Param("slaDefinitionId") UUID slaDefinitionId,
            @Param("now") LocalDateTime now);
}
```

#### Layer 4: Service (oci-api)

**File:** `oci-api/.../service/sla/SlaExcludedDowntimeManagementService.java`

**Key Operations:**

```java
@Service
@RequiredArgsConstructor
public class SlaExcludedDowntimeManagementService {

    private final SlaExcludedDowntimeRepository repository;
    private final SlaDefinitionRepository slaDefinitionRepository;
    private final SlaExcludedDowntimeMapper mapper;

    /**
     * Create new excluded downtime with overlap validation.
     */
    @Transactional
    public SlaExcludedDowntimeResponseDto create(
            UUID slaDefinitionId,
            CreateSlaExcludedDowntimeRequest request,
            String createdBy) {

        // 1. Validate request
        if (!request.isValid()) {
            throw new IllegalArgumentException("Invalid request");
        }

        // 2. Load SLA definition
        SlaDefinition slaDefinition = slaDefinitionRepository.findById(slaDefinitionId)
                .orElseThrow(() -> new IllegalArgumentException("SLA not found"));

        // 3. Check for overlapping periods
        boolean hasOverlap = repository.existsOverlappingPeriods(
                slaDefinitionId,
                request.getPeriodFrom(),
                request.getPeriodTo(),
                null
        );

        if (hasOverlap) {
            throw new IllegalArgumentException("Period overlaps with existing downtime");
        }

        // 4. Create and save entity
        SlaExcludedDowntime downtime = SlaExcludedDowntime.builder()
                .slaDefinition(slaDefinition)
                .name(request.getName())
                .description(request.getDescription())
                .periodFrom(request.getPeriodFrom())
                .periodTo(request.getPeriodTo())
                .createdAt(LocalDateTime.now())
                .createdBy(createdBy)
                .build();

        SlaExcludedDowntime saved = repository.save(downtime);

        return mapper.toDto(saved);
    }

    /**
     * Update with overlap validation (excluding current downtime).
     */
    @Transactional
    public SlaExcludedDowntimeResponseDto update(
            UUID downtimeId,
            UpdateSlaExcludedDowntimeRequest request,
            String updatedBy) {
        // Similar logic with overlap check excluding current ID
    }

    // Additional methods: getById, getAllBySlaDefinition,
    // delete, getActiveBySlaDefinition, getUpcoming, count
}
```

#### Layer 5: Controller (oci-api)

**File:** `oci-api/.../controller/sla/SlaExcludedDowntimeController.java`

**REST Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sla/{slaDefinitionId}/excluded-downtimes` | List all for SLA |
| GET | `/api/sla/excluded-downtimes/{id}` | Get by ID |
| POST | `/api/sla/{slaDefinitionId}/excluded-downtimes` | Create new |
| PUT | `/api/sla/excluded-downtimes/{id}` | Update existing |
| DELETE | `/api/sla/excluded-downtimes/{id}` | Delete |
| GET | `/api/sla/{slaDefinitionId}/excluded-downtimes/active` | Get active periods |
| GET | `/api/sla/excluded-downtimes/upcoming` | Get upcoming periods |
| GET | `/api/sla/{slaDefinitionId}/excluded-downtimes/count` | Count for SLA |

**Example Controller Method:**

```java
@PostMapping("/{slaDefinitionId}/excluded-downtimes")
public ResponseEntity<SlaExcludedDowntimeResponseDto> create(
        @PathVariable UUID slaDefinitionId,
        @Valid @RequestBody CreateSlaExcludedDowntimeRequest request) {

    try {
        String createdBy = "system"; // TODO: Get from SecurityContext

        SlaExcludedDowntimeResponseDto created =
                excludedDowntimeService.create(slaDefinitionId, request, createdBy);

        return ResponseEntity.status(HttpStatus.CREATED).body(created);

    } catch (IllegalArgumentException e) {
        return ResponseEntity.badRequest().build();
    }
}
```

### Frontend Architecture

#### TypeScript Interfaces

**File:** `src/types/sla.types.ts`

```typescript
export interface CreateSlaExcludedDowntimeRequest {
    name: string
    description?: string
    periodFrom: string // ISO datetime
    periodTo: string // ISO datetime
}

export interface UpdateSlaExcludedDowntimeRequest {
    name?: string
    description?: string
    periodFrom?: string // ISO datetime
    periodTo?: string // ISO datetime
}

export interface SlaExcludedDowntimeResponseDto {
    id: string
    slaDefinitionId: string
    slaDefinitionName?: string
    name: string
    description?: string
    periodFrom: string // ISO datetime
    periodTo: string // ISO datetime
    durationMinutes: number
    createdAt: string
    createdBy: string
    updatedAt?: string
    updatedBy?: string
}

export type DowntimeStatus = 'active' | 'upcoming' | 'past'

export function getDowntimeStatus(
    downtime: SlaExcludedDowntimeResponseDto
): DowntimeStatus {
    const now = new Date()
    const periodFrom = new Date(downtime.periodFrom)
    const periodTo = new Date(downtime.periodTo)

    if (now >= periodFrom && now <= periodTo) return 'active'
    if (now < periodFrom) return 'upcoming'
    return 'past'
}
```

#### API Service

**File:** `src/services/slaExcludedDowntimeService.ts`

```typescript
export const slaExcludedDowntimeService = {
    async getAllBySlaDefinition(
        slaDefinitionId: string
    ): Promise<SlaExcludedDowntimeResponseDto[]> {
        const response = await api.get<SlaExcludedDowntimeResponseDto[]>(
            ApiRoutes.SlaExcludedDowntime.List(slaDefinitionId)
        )
        return response.data
    },

    async create(
        slaDefinitionId: string,
        data: CreateSlaExcludedDowntimeRequest
    ): Promise<SlaExcludedDowntimeResponseDto> {
        const response = await api.post<SlaExcludedDowntimeResponseDto>(
            ApiRoutes.SlaExcludedDowntime.Create(slaDefinitionId),
            data
        )
        return response.data
    },

    // ... update, delete, getActive, getUpcoming, count methods
}
```

#### API Routes

**File:** `src/constants.ts`

```typescript
export const ApiRoutes = {
    // ... other routes
    SlaExcludedDowntime: {
        List: (slaDefinitionId: string) =>
            `/sla/${slaDefinitionId}/excluded-downtimes`,
        ById: (id: string) =>
            `/sla/excluded-downtimes/${id}`,
        Create: (slaDefinitionId: string) =>
            `/sla/${slaDefinitionId}/excluded-downtimes`,
        Update: (id: string) =>
            `/sla/excluded-downtimes/${id}`,
        Delete: (id: string) =>
            `/sla/excluded-downtimes/${id}`,
        Active: (slaDefinitionId: string) =>
            `/sla/${slaDefinitionId}/excluded-downtimes/active`,
        Upcoming: () =>
            '/sla/excluded-downtimes/upcoming',
        Count: (slaDefinitionId: string) =>
            `/sla/${slaDefinitionId}/excluded-downtimes/count`,
    },
}
```

### UI Components (To Be Implemented)

#### 1. ExcludedDowntimeList Component

**Purpose:** Display list of excluded downtime periods with status badges

```tsx
interface Props {
    slaDefinitionId: string
}

export function ExcludedDowntimeList({ slaDefinitionId }: Props) {
    const [downtimes, setDowntimes] = useState<SlaExcludedDowntimeResponseDto[]>([])
    const [isLoading, setIsLoading] = useState(true)

    // Features:
    // - Load downtimes on mount
    // - Display in table/card format
    // - Status badges (active/upcoming/past)
    // - Edit and Delete buttons
    // - Duration display
    // - Sort by period start
}
```

**Visual Mockup:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ Excluded Downtime Periods                           [+ Add New]     │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 🟢 ACTIVE   Database Migration                                  │ │
│ │ From: 2024-12-15 02:00  To: 2024-12-15 04:00  (2h 0m)         │ │
│ │ Description: Monthly DB maintenance window                      │ │
│ │                                          [Edit]  [Delete]       │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 🔵 UPCOMING  Holiday Maintenance                                │ │
│ │ From: 2024-12-25 00:00  To: 2024-12-26 00:00  (24h 0m)        │ │
│ │                                          [Edit]  [Delete]       │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2. ExcludedDowntimeDialog Component

**Purpose:** Modal form for creating/editing downtime periods

```tsx
interface Props {
    slaDefinitionId: string
    downtime?: SlaExcludedDowntimeResponseDto // For edit mode
    isOpen: boolean
    onClose: () => void
    onSave: () => void
}

export function ExcludedDowntimeDialog({
    slaDefinitionId,
    downtime,
    isOpen,
    onClose,
    onSave
}: Props) {
    // Features:
    // - Form fields: name, description, periodFrom, periodTo
    // - Date-time pickers for period selection
    // - Client-side validation (periodTo > periodFrom)
    // - Server-side overlap validation
    // - Duration calculation display
    // - Create or Update mode
}
```

**Form Fields:**
```
┌──────────────────────────────────────────────────┐
│ Add Excluded Downtime Period           [X Close] │
├──────────────────────────────────────────────────┤
│                                                   │
│ Name *                                            │
│ ┌────────────────────────────────────────────┐   │
│ │ Database Migration                         │   │
│ └────────────────────────────────────────────┘   │
│                                                   │
│ Description (optional)                            │
│ ┌────────────────────────────────────────────┐   │
│ │ Monthly maintenance window for DB upgrade  │   │
│ └────────────────────────────────────────────┘   │
│                                                   │
│ Period From * (UTC)                               │
│ ┌───────────────────┬────────────┐              │
│ │ 2024-12-15       │ 02:00      │              │
│ └───────────────────┴────────────┘              │
│                                                   │
│ Period To * (UTC)                                 │
│ ┌───────────────────┬────────────┐              │
│ │ 2024-12-15       │ 04:00      │              │
│ └───────────────────┴────────────┘              │
│                                                   │
│ Duration: 2 hours                                 │
│                                                   │
│              [Cancel]  [Save]                     │
└──────────────────────────────────────────────────┘
```

#### 3. Integration in SLA Form

**Location:** `src/pages/SlaFormPage.tsx`

**Step 4 Enhancement:** Add Excluded Downtimes section in Advanced Options

```tsx
// In SlaFormPage, Step 4 (Advanced Options):

<div className="space-y-4">
    {/* Existing fields: grace tolerance, penalties, notifications */}

    {/* NEW SECTION: Excluded Downtimes */}
    <div className="border-t pt-4">
        <h3 className="text-lg font-semibold mb-2">
            Excluded Downtime Periods
        </h3>
        <p className="text-sm text-muted-foreground mb-4">
            Define maintenance windows or planned downtimes to exclude
            from SLA compliance calculations.
        </p>

        {formData.id && (
            <ExcludedDowntimeList slaDefinitionId={formData.id} />
        )}

        {!formData.id && (
            <div className="text-sm text-muted-foreground italic">
                Save the SLA definition first to add excluded downtime periods.
            </div>
        )}
    </div>
</div>
```

### How It Works in SLA Computation

**Scenario:** Calculate SLA compliance for period

```java
// In AvailabilityCalculatorService

// 1. Load excluded downtimes for SLA definition
List<SlaExcludedDowntime> excludedDowntimes =
    excludedDowntimeRepository.findOverlappingPeriods(
        slaDefinitionId,
        periodStart,
        periodEnd
    );

// 2. Filter data points
for (MetricDataPoint dataPoint : allDataPoints) {
    boolean isExcluded = excludedDowntimes.stream()
        .anyMatch(downtime -> downtime.contains(dataPoint.getTimestamp()));

    if (isExcluded) {
        excludedPoints++;
        continue; // Skip this data point
    }

    countedPoints++;
    if (dataPoint.meetsThreshold()) {
        compliantPoints++;
    } else {
        breachPoints++;
    }
}

// 3. Calculate compliance
double compliancePercent = (compliantPoints / countedPoints) * 100;

// 4. Return result
return AvailabilityMetrics.builder()
    .totalDataPoints(allDataPoints.size())
    .excludedDataPoints(excludedPoints)
    .countedDataPoints(countedPoints)
    .compliantDataPoints(compliantPoints)
    .breachDataPoints(breachPoints)
    .compliancePercentage(compliancePercent)
    .build();
```

### Key Features

✅ **Overlap Prevention:** Cannot create overlapping downtime periods
✅ **Status Tracking:** Active, Upcoming, Past periods
✅ **Audit Trail:** Created/updated by, timestamps
✅ **Duration Calculation:** Automatic duration in minutes
✅ **Relationship Management:** Cascade delete when SLA deleted
✅ **Query Optimization:** JOIN FETCH to prevent lazy loading issues
✅ **Flexible Updates:** Partial updates supported
✅ **Multi-Period Support:** Unlimited excluded downtime periods per SLA

### Benefits

1. **Accurate Compliance** - Excludes planned maintenance from SLA breaches
2. **Transparency** - Clear audit trail of all excluded periods
3. **Flexibility** - Add/update/delete periods as needed
4. **No Data Loss** - Data points still collected, just excluded from calculations
5. **Reporting** - Excluded downtime shown in SLA reports

### Example Usage

```bash
# Create excluded downtime
curl -X POST http://localhost:8080/api/sla/{slaId}/excluded-downtimes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Database Migration",
    "description": "Quarterly DB upgrade",
    "periodFrom": "2024-12-15T02:00:00",
    "periodTo": "2024-12-15T04:00:00"
  }'

# List all for SLA
curl -X GET http://localhost:8080/api/sla/{slaId}/excluded-downtimes

# Get active downtimes
curl -X GET http://localhost:8080/api/sla/{slaId}/excluded-downtimes/active

# Update
curl -X PUT http://localhost:8080/api/sla/excluded-downtimes/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "periodTo": "2024-12-15T05:00:00"
  }'

# Delete
curl -X DELETE http://localhost:8080/api/sla/excluded-downtimes/{id}
```

---

## 🎛️ Manual Trigger API

### Overview

In addition to automated scheduled execution, SLA computations can be **manually triggered** via REST API. This is useful for:

- **Testing** - Verify SLA computation without waiting for scheduled time
- **Debugging** - Recompute SLA to investigate issues
- **On-demand** - Compute SLA for specific date/period
- **Force recompute** - Override existing results

### Architecture

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend   │────────>│   oci-api    │────────>│ oci-monitor  │
│     (UI)     │  POST   │              │  POST   │              │
│              │ /api/sla│ SlaController│ /monitor│ SlaScheduler │
│              │ /trigger│              │ /sla/    │  Controller  │
└──────────────┘         └──────────────┘ trigger └──────────────┘
                                │                        │
                                │                        │
                                v                        v
                         MonitorApiService        SlaComputationService
                                                         │
                                                         v
                                                   Database
                                                   (sla_result,
                                                    sla_breach)
```

### API Endpoints

#### 1. Manual SLA Computation (oci-api)

**Endpoint:** POST /api/sla/trigger

**Purpose:** User-facing endpoint for manually triggering SLA computation

**Module:** oci-api

**Controller:** SlaController (oci-api/controller/sla/SlaController.java)

**Request:**
```json
{
  "slaDefinitionId": "uuid-of-sla-definition",
  "periodStart": "2025-11-01",
  "forceRecompute": true,
  "triggeredBy": "admin@company.com"
}
```

**Response:**
```json
{
  "success": true,
  "resultId": "generated-result-uuid",
  "slaDefinitionId": "uuid-of-sla-definition",
  "slaDefinitionName": "Monthly CPU SLA",
  "periodStart": "2025-11-01T00:00:00",
  "periodEnd": "2025-12-01T00:00:00",
  "status": "FULFILLED",
  "compliancePercent": 99.52,
  "computedAt": "2025-11-08T14:30:00",
  "message": "SLA target met: 99.52% compliance (target: 99.50%). Data coverage: 100.00%.",
  "wasRecomputed": true
}
```

#### 2. Internal Computation Endpoint (oci-monitor)

**Endpoint:** POST /monitoring/sla/trigger

**Purpose:** Internal endpoint called by oci-api (not exposed to frontend)

**Module:** oci-monitor

**Controller:** SlaSchedulerController (oci-monitor/controller/SlaSchedulerController.java)

**Request:** Same as above

**Response:** Same as above

### Request Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| **slaDefinitionId** | String (UUID) | ✅ Yes | SLA definition to compute | "a1b2c3d4-..." |
| **periodStart** | LocalDate | ⚠️ Optional | Period start date (defaults to yesterday) | "2025-11-01" |
| **periodEnd** | LocalDate | ❌ No | Period end (auto-calculated based on period type) | "2025-11-30" |
| **forceRecompute** | Boolean | ⚠️ Optional | Recompute even if result exists (default: false) | true |
| **triggeredBy** | String | ⚠️ Optional | User who triggered (for audit, default: "manual-trigger") | "admin@example.com" |

### Use Cases

#### Use Case 1: Test SLA Without Waiting

**Scenario:** You created a new SLA definition and want to test it immediately without waiting for the scheduled time (next day/week/month).

**Solution:**
```bash
POST /api/sla/trigger
{
  "slaDefinitionId": "new-sla-uuid",
  "periodStart": "2025-11-07",  # Yesterday
  "forceRecompute": false,
  "triggeredBy": "test-user@company.com"
}
```

#### Use Case 2: Recompute SLA After Fixing Data

**Scenario:** There was a bug in metric collection. You fixed it and added missing metric data. Now you need to recompute the SLA for November.

**Solution:**
```bash
POST /api/sla/trigger
{
  "slaDefinitionId": "existing-sla-uuid",
  "periodStart": "2025-11-01",
  "forceRecompute": true,  # Force overwrite existing result
  "triggeredBy": "admin@company.com"
}
```

#### Use Case 3: Debug Specific Period

**Scenario:** SLA shows breach for last month, but you want to investigate a specific week.

**Solution:**
```bash
POST /api/sla/trigger
{
  "slaDefinitionId": "sla-uuid",
  "periodStart": "2025-10-15",  # Specific week start
  "forceRecompute": true,
  "triggeredBy": "debug-user@company.com"
}
```

### Code Example (Frontend)

```typescript
// src/services/slaService.ts
export async function triggerSlComputation(
  slaDefinitionId: string,
  periodStart: string,
  forceRecompute: boolean = false
): Promise<SlaComputationResponse> {
  
  const response = await fetch('/api/sla/trigger', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify({
      slaDefinitionId,
      periodStart,
      forceRecompute,
      triggeredBy: getCurrentUser().email
    })
  })

  if (!response.ok) {
    throw new Error('Failed to trigger SLA computation')
  }

  return await response.json()
}

// Usage
const result = await triggerSlaComputation(
  'a1b2c3d4-...',
  '2025-11-01',
  true  // force recompute
)

console.log(`SLA computed: ${result.compliancePercent}% (${result.status})`)
```

### Error Handling

**Invalid SLA Definition ID:**
```json
{
  "success": false,
  "errorMessage": "Invalid request: SLA Definition not found: invalid-uuid"
}
```

**Response:** HTTP 400 Bad Request

**Inactive SLA:**
```json
{
  "success": false,
  "errorMessage": "Invalid request: SLA Definition is inactive: uuid"
}
```

**Response:** HTTP 400 Bad Request

**Computation Failure:**
```json
{
  "success": false,
  "errorMessage": "SLA computation failed: Insufficient metric data for period"
}
```

**Response:** HTTP 500 Internal Server Error

---

## 🧪 API Testing with cURL

### Prerequisites

#### Authentication

**oci-monitor** has optional authentication controlled by configuration:

| Environment | monitor.auth.enabled | Requires Token? |
|-------------|----------------------|-----------------|
| **Local (dev)** | false | ❌ NO |
| **DEV Server** | false | ❌ NO |
| **PROD Server** | true | ✅ YES |

**oci-api** always requires authentication.

#### Getting Bearer Token

**Method 1: Login via API**

```bash
# Login to oci-api
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@company.com",
    "password": "your-password"
  }'

# Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600
}

# Save token to variable
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Method 2: Extract from Browser**

1. Open browser DevTools (F12)
2. Go to **Application** → **Local Storage** → http://localhost:3000
3. Find authToken key
4. Copy value

```bash
export TOKEN="paste-token-here"
```

### Test Scenarios

#### Scenario 1: Trigger SLA Computation (via oci-api)

**Local (no auth):**
```bash
curl -X POST http://localhost:8080/api/sla/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "slaDefinitionId": "your-sla-uuid",
    "periodStart": "2025-11-01",
    "forceRecompute": false,
    "triggeredBy": "test-user"
  }'
```

**Production (with auth):**
```bash
curl -X POST https://oci-api.company.com/api/sla/trigger \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "slaDefinitionId": "your-sla-uuid",
    "periodStart": "2025-11-01",
    "forceRecompute": true,
    "triggeredBy": "admin@company.com"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "resultId": "generated-uuid",
  "slaDefinitionId": "your-sla-uuid",
  "slaDefinitionName": "Monthly CPU SLA",
  "periodStart": "2025-11-01T00:00:00",
  "periodEnd": "2025-12-01T00:00:00",
  "status": "FULFILLED",
  "compliancePercent": 99.52,
  "computedAt": "2025-11-08T14:30:00",
  "message": "SLA target met...",
  "wasRecomputed": false
}
```

#### Scenario 2: Direct Call to oci-monitor (Internal)

⚠️ **Note:** This endpoint should only be called from oci-api, not from frontend!

**Local (no auth):**
```bash
curl -X POST http://localhost:8081/monitoring/sla/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "slaDefinitionId": "your-sla-uuid",
    "periodStart": "2025-11-01",
    "forceRecompute": false,
    "triggeredBy": "test-user"
  }'
```

**Production (with auth):**
```bash
curl -X POST https://oci-monitor.internal.company.com/monitoring/sla/trigger \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "slaDefinitionId": "your-sla-uuid",
    "periodStart": "2025-11-01",
    "forceRecompute": true,
    "triggeredBy": "admin"
  }'
```

#### Scenario 3: Get SLA Report

**Local:**
```bash
curl -X GET "http://localhost:8080/api/sla/reports/your-sla-uuid?periodType=MONTHLY&periodStart=2025-11-01" \
  -H "Content-Type: application/json"
```

**Production:**
```bash
curl -X GET "https://oci-api.company.com/api/sla/reports/your-sla-uuid?periodType=MONTHLY&periodStart=2025-11-01" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN"
```

#### Scenario 4: Export SLA Report as PDF

**Local:**
```bash
curl -X GET "http://localhost:8080/api/sla/reports/your-sla-uuid/export/pdf?periodType=MONTHLY&periodStart=2025-11-01" \
  -H "Authorization: Bearer $TOKEN" \
  --output sla-report.pdf
```

**Production:**
```bash
curl -X GET "https://oci-api.company.com/api/sla/reports/your-sla-uuid/export/pdf?periodType=MONTHLY&periodStart=2025-11-01" \
  -H "Authorization: Bearer $TOKEN" \
  --output sla-report.pdf

# Verify PDF was downloaded
file sla-report.pdf
# Output: sla-report.pdf: PDF document, version 1.4
```

#### Scenario 5: Export SLA Report as CSV

**Local:**
```bash
curl -X GET "http://localhost:8080/api/sla/reports/your-sla-uuid/export/csv?periodType=MONTHLY&periodStart=2025-11-01" \
  --output sla-report.csv
```

**Production:**
```bash
curl -X GET "https://oci-api.company.com/api/sla/reports/your-sla-uuid/export/csv?periodType=MONTHLY&periodStart=2025-11-01" \
  -H "Authorization: Bearer $TOKEN" \
  --output sla-report.csv

# View CSV content
head -20 sla-report.csv
```

### Testing Checklist

**Before Testing:**
- [ ] Verify services are running (docker ps or ps aux | grep java)
- [ ] Check logs for errors (tail -f logs/oci-api.log)
- [ ] Confirm SLA definition exists in database
- [ ] Verify metric data available for test period

**Test Steps:**

1. **Test without auth (local):**
   ```bash
   curl -X POST http://localhost:8080/api/sla/trigger \
     -H "Content-Type: application/json" \
     -d '{"slaDefinitionId": "test-uuid", "periodStart": "2025-11-01"}'
   ```

2. **Test with auth (prod):**
   ```bash
   export TOKEN="your-token"
   curl -X POST https://oci-api.company.com/api/sla/trigger \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"slaDefinitionId": "test-uuid", "periodStart": "2025-11-01", "forceRecompute": true}'
   ```

3. **Verify result:**
   ```bash
   # Check database for new sla_result
   mysql> SELECT * FROM sla_result ORDER BY computed_at DESC LIMIT 1;
   
   # Check logs
   tail -f logs/oci-monitor.log | grep "SLA computation"
   ```

4. **Test error handling:**
   ```bash
   # Invalid UUID
   curl -X POST http://localhost:8080/api/sla/trigger \
     -H "Content-Type: application/json" \
     -d '{"slaDefinitionId": "invalid-uuid"}'
   # Expected: HTTP 400 with error message
   
   # Missing required field
   curl -X POST http://localhost:8080/api/sla/trigger \
     -H "Content-Type: application/json" \
     -d '{}'
   # Expected: HTTP 400 validation error
   ```

### Common Issues

**Issue 1: 401 Unauthorized**

**Error:**
```
{"error": "Unauthorized", "message": "Invalid or missing token"}
```

**Solution:** Get fresh token via /api/auth/login

**Issue 2: 403 Forbidden**

**Error:**
```
{"error": "Forbidden", "message": "Insufficient permissions"}
```

**Solution:** Ensure user has OCI_SCHEDULER authority

**Issue 3: 500 Internal Server Error**

**Error:**
```
{"success": false, "errorMessage": "SLA computation failed: ..."}
```

**Solution:** Check oci-monitor logs for details:
```bash
tail -100 logs/oci-monitor.log | grep ERROR
```

---

