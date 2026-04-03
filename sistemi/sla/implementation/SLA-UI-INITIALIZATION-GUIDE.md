# SLA UI - Initialization Guide

**Date**: 2025-11-07
**Purpose**: Initialize test SLA definitions for UI development/testing
**API**: oci-api (port 8080) - unauthenticated endpoints for development

---

## 📋 Prerequisites

1. **Backend running**: `oci-api` on port 8080
   ```bash
   cd oci-api
   mvn spring-boot:run -Dspring-boot.run.profiles=local
   ```

2. **Database running**: MySQL on port 3306
   ```bash
   docker ps | grep mysql
   ```

3. **Frontend running** (optional): React UI on port 5173
   ```bash
   cd references/oci-sla-management-ui
   npm run dev
   ```

---

## 🔍 Step 1: Get Required IDs from Database

### Get Tenant IDs

```bash
mysql -h 127.0.0.1 -u root -pmyrootsecret ociapp -e "
SELECT
    id,
    name
FROM tenant
ORDER BY name
LIMIT 5;" -sN
```

**Example Output**:
```
48316996-1cd2-4e29-a3fb-f7c21f117547	Testni tenant 1
89973218-0791-4058-b2a2-34ed2618523a	Republički geodetski zavod
aaaaa000-bb96-11ee-8ce6-0242c0a85004	Kancelarija za informacione tehnologije i elektronsku upravu
```

### Get Resource IDs

```bash
mysql -h 127.0.0.1 -u root -pmyrootsecret ociapp -e "
SELECT
    id,
    name,
    LEFT(ocid, 40) as ocid_preview,
    resource_type
FROM resource
WHERE is_active = 1
ORDER BY created_at DESC
LIMIT 5;" -sN
```

**Example Output**:
```
018e0f36-678f-7042-98fe-a369475040b3	vm-prod-web-01	ocid1.instance.oc1.eu-frankfurt-1.an...	INSTANCE
019a1234-5678-7042-98fe-b369475040c4	db-prod-mysql-01	ocid1.dbsystem.oc1.eu-frankfurt-1.an...	DATABASE
```

### Set Environment Variables

```bash
# Use tenant ID from query results
export TENANT_ID="aaaaa000-bb96-11ee-8ce6-0242c0a85004"

# Use resource ID from query results
export RESOURCE_ID="018e0f36-678f-7042-98fe-a369475040b3"

# API endpoint (oci-api, not oci-monitor!)
export API_URL="http://localhost:8080/api/sla"
```

---

## 🔨 Step 2: Create Test SLA Definitions

### Example 1: DAILY CPU Utilization SLA

This SLA monitors daily CPU and requires ≤80% CPU for at least 95% of the time.

```bash
curl -X POST $API_URL/definitions \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"DAILY CPU - Test SLA for UI\",
    \"description\": \"Test SLA: CPU should stay below 80% for at least 95% of daily measurements\",
    \"tenantId\": \"$TENANT_ID\",
    \"resourceId\": \"$RESOURCE_ID\",
    \"metricNamespace\": \"oci_computeagent\",
    \"metricName\": \"CpuUtilization\",
    \"statisticType\": \"mean()\",
    \"comparator\": \"LTE\",
    \"targetType\": \"PERCENT\",
    \"targetValue\": 95.00,
    \"alertThresholdPercent\": 90.00,
    \"metricThreshold\": 80.00,
    \"periodType\": \"DAILY\",
    \"activeFrom\": \"2025-01-01T00:00:00\",
    \"activeTo\": null,
    \"graceToleranceMinutes\": 15,
    \"isActive\": true,
    \"notificationRecipientEmails\": \"ops@sistemi.rs\"
  }" | jq '.'
```

**Expected Response** (200 OK):
```json
{
  "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "name": "DAILY CPU - Test SLA for UI",
  "description": "Test SLA: CPU should stay below 80% for at least 95% of daily measurements",
  "periodType": "DAILY",
  "metricName": "CpuUtilization",
  "targetValue": 95.0,
  "metricThreshold": 80.0,
  "isActive": true,
  "createdAt": "2025-11-07T...",
  "createdBy": "system"
}
```

---

### Example 2: WEEKLY Memory Utilization SLA

Weekly memory monitoring with 98% compliance target.

```bash
curl -X POST $API_URL/definitions \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"WEEKLY Memory - Test SLA for UI\",
    \"description\": \"Test SLA: Memory usage should stay below 85% for at least 98% of weekly measurements\",
    \"tenantId\": \"$TENANT_ID\",
    \"resourceId\": \"$RESOURCE_ID\",
    \"metricNamespace\": \"oci_computeagent\",
    \"metricName\": \"MemoryUtilization\",
    \"statisticType\": \"mean()\",
    \"comparator\": \"LTE\",
    \"targetType\": \"PERCENT\",
    \"targetValue\": 98.00,
    \"alertThresholdPercent\": 95.00,
    \"metricThreshold\": 85.00,
    \"periodType\": \"WEEKLY\",
    \"activeFrom\": \"2025-01-01T00:00:00\",
    \"activeTo\": null,
    \"graceToleranceMinutes\": 30,
    \"isActive\": true,
    \"notificationRecipientEmails\": \"ops@sistemi.rs\"
  }" | jq '.'
```

---

### Example 3: MONTHLY Availability SLA (with Penalty)

Monthly availability SLA with 99.9% uptime requirement and financial penalty.

```bash
curl -X POST $API_URL/definitions \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"MONTHLY Availability 99.9% - Production\",
    \"description\": \"Critical SLA: System must maintain 99.9% availability (max 43.2 min downtime per month)\",
    \"tenantId\": \"$TENANT_ID\",
    \"resourceId\": \"$RESOURCE_ID\",
    \"metricNamespace\": \"oci_computeagent\",
    \"metricName\": \"CpuUtilization\",
    \"statisticType\": \"count()\",
    \"comparator\": \"LTE\",
    \"targetType\": \"PERCENT\",
    \"targetValue\": 99.90,
    \"alertThresholdPercent\": 99.50,
    \"metricThreshold\": 100.00,
    \"periodType\": \"MONTHLY\",
    \"activeFrom\": \"2025-01-01T00:00:00\",
    \"activeTo\": null,
    \"graceToleranceMinutes\": 60,
    \"penaltyCurrency\": \"RSD\",
    \"penaltyAmount\": 50000.00,
    \"penaltyCalculationFormula\": \"FIXED\",
    \"isActive\": true,
    \"notificationRecipientEmails\": \"ops@sistemi.rs,admin@sistemi.rs,cto@sistemi.rs\"
  }" | jq '.'
```

---

### Example 4: QUARTERLY Business SLA

Quarterly SLA for long-term performance tracking.

```bash
curl -X POST $API_URL/definitions \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"QUARTERLY Performance - Q4 2025\",
    \"description\": \"Quarterly business SLA for Q4 2025 performance tracking\",
    \"tenantId\": \"$TENANT_ID\",
    \"resourceId\": \"$RESOURCE_ID\",
    \"metricNamespace\": \"oci_computeagent\",
    \"metricName\": \"CpuUtilization\",
    \"statisticType\": \"mean()\",
    \"comparator\": \"LTE\",
    \"targetType\": \"PERCENT\",
    \"targetValue\": 97.00,
    \"alertThresholdPercent\": 95.00,
    \"metricThreshold\": 75.00,
    \"periodType\": \"QUARTERLY\",
    \"activeFrom\": \"2025-10-01T00:00:00\",
    \"activeTo\": \"2025-12-31T23:59:59\",
    \"graceToleranceMinutes\": 120,
    \"penaltyCurrency\": \"RSD\",
    \"penaltyAmount\": 200000.00,
    \"isActive\": true,
    \"notificationRecipientEmails\": \"management@sistemi.rs\"
  }" | jq '.'
```

---

## 🔍 Step 3: Verify Created SLAs

### Check via API (active definitions)

```bash
curl -X GET $API_URL/definitions/active | jq '.'
```

**Expected Response**:
```json
[
  {
    "id": "...",
    "name": "DAILY CPU - Test SLA for UI",
    "periodType": "DAILY",
    "isActive": true
  },
  {
    "id": "...",
    "name": "WEEKLY Memory - Test SLA for UI",
    "periodType": "WEEKLY",
    "isActive": true
  },
  ...
]
```

### Check in Database

```bash
mysql -h 127.0.0.1 -u root -pmyrootsecret ociapp -e "
SELECT
    LEFT(id, 13) as sla_id,
    name,
    period_type,
    metric_name,
    ROUND(target_value, 2) as target,
    ROUND(metric_threshold, 2) as threshold,
    is_active,
    created_by,
    DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') as created
FROM sla_definition
WHERE created_by = 'system'
ORDER BY created_at DESC
LIMIT 10;
"
```

### Check in UI

1. Open browser: http://localhost:5173
2. Navigate to "SLA Report Generator"
3. Select SLA dropdown - you should see all active SLAs
4. Select period type and start date
5. Click "Generate Report"

---

## 🧪 Quick Initialization Script

Make it executable and run:

```bash
chmod +x init-sla-test-data.sh
./init-sla-test-data.sh
```

---

## 🧹 Cleanup - Delete Test SLAs

### Delete specific SLA by ID

```bash
SLA_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
curl -X PATCH $API_URL/definitions/$SLA_ID/deactivate | jq '.'
```

### Delete all test SLAs (via database)

```bash
mysql -h 127.0.0.1 -u root -pmyrootsecret ociapp -e "
UPDATE sla_definition
SET is_active = 0,
    updated_at = NOW(),
    updated_by = 'cleanup-script'
WHERE created_by = 'system'
  AND name LIKE '%UI Test%';
"
```

### Verify cleanup

```bash
curl -X GET $API_URL/definitions/active | jq '. | length'
# Should return 0 if all test SLAs are deleted
```

---

## 📚 Field Reference Quick Guide

| Field | Required | Example | Notes |
|-------|----------|---------|-------|
| `name` | ✅ | "DAILY CPU - Test" | Unique descriptive name |
| `description` | ❌ | "Monitors daily CPU..." | Detailed explanation |
| `tenantId` | ✅ | "aaaaa000-bb96-..." | From tenant table |
| `resourceId` | ⚠️ | "018e0f36-678f-..." | XOR with ociQueryId |
| `metricNamespace` | ✅ | "oci_computeagent" | OCI metric namespace |
| `metricName` | ✅ | "CpuUtilization" | Metric to monitor |
| `statisticType` | ✅ | "mean()" | mean(), max(), sum(), count() |
| `comparator` | ✅ | "LTE" | LTE, GTE, LT, GT |
| `targetType` | ✅ | "PERCENT" | PERCENT, PENALTY |
| `targetValue` | ✅ | 95.00 | Target compliance % |
| `metricThreshold` | ✅ | 80.00 | Metric limit value |
| `periodType` | ✅ | "DAILY" | HOURLY, DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY |
| `activeFrom` | ✅ | "2025-01-01T00:00:00" | Start datetime |
| `activeTo` | ❌ | null | End datetime (null = indefinite) |
| `graceToleranceMinutes` | ❌ | 15 | Grace period before breach |
| `penaltyCurrency` | ❌ | "RSD" | Currency code |
| `penaltyAmount` | ❌ | 50000.00 | Penalty amount |
| `isActive` | ❌ | true | Default: true |
| `notificationRecipientEmails` | ❌ | "ops@sistemi.rs" | Comma-separated emails |

---

## ⚠️ Important Notes for Development

### Security Configuration (TEMPORARY)

The SLA endpoints are currently open without authentication for development:

```java
// SecurityConfig.java - Line 156
.requestMatchers("/api/sla/**").permitAll()
```

**⚠️ IMPORTANT**: This configuration is **ONLY for development/testing**.

For production:
1. Remove `.permitAll()` from SecurityConfig
2. Add proper role-based authentication:
   ```java
   .requestMatchers("/api/sla/**").hasAnyAuthority(SUPERADMIN.name(), SYS_ADMIN.name(), ORG_ADMIN.name())
   ```
3. Update frontend to include JWT token in requests
4. Test with authenticated users

### Development vs Production Behavior

**Development Mode** (no authentication):
- `getActiveSlaDefinitions()` returns ALL active SLA definitions (all tenants)
- `generateReport()` uses "system" as `generatedBy`
- Warning logged: "No authenticated user - returning all active SLA definitions"

**Production Mode** (with authentication):
- `getActiveSlaDefinitions()` filters by current user's tenant
- `generateReport()` uses actual username
- Tenant access validation enforced

---

## 🐛 Troubleshooting

### Error: "Empty list returned"

**Cause**: No SLA definitions in database
**Solution**: Run initialization script above

### Error: "CORS policy blocking"

**Cause**: CORS not configured for frontend port
**Solution**: Verify `application-local.properties` contains:
```properties
app.cors.allowed-origins=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

### Error: "Cannot find tenant"

**Cause**: Invalid tenant ID
**Solution**: Query database for valid tenant IDs (see Step 1)

### Error: "Cannot find resource"

**Cause**: Invalid resource ID
**Solution**: Query database for valid resource IDs (see Step 1)

### Error: "Either resourceId or ociQueryId must be provided"

**Cause**: Missing both resourceId and ociQueryId
**Solution**: Provide exactly ONE of resourceId or ociQueryId

---

**End of Guide**
