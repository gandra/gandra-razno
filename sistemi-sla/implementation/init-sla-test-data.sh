#!/bin/bash

# Configuration
API_URL="http://localhost:8080/api/sla"
TENANT_ID="aaaaa000-bb96-11ee-8ce6-0242c0a85004"
RESOURCE_ID="018e0f36-678f-7042-98fe-a369475040b3"
TOKEN="eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJPQ0kgTW9uaXRvciBBcHAiLCJzdWIiOiJzdXBlcmFkbWluQHNpc3RlbWkucnMiLCJhdXRob3JpdGllcyI6IlNVUEVSQURNSU4iLCJwdXJwb3NlIjoiT0NJLkFwcC5BdXRoZW50aWNhdGUiLCJpYXQiOjE3NjI2MzQ1NDAsImV4cCI6MTc5ODYzNDU0MH0.PE6yYHbBRxShGft2e53xhGYqWa3yWEVyZ0yOIHui3Do"

# JWT Token (pass as environment variable: TOKEN="your-jwt-token" ./init-sla-test-data.sh)
if [ -z "$TOKEN" ]; then
    echo "ERROR: TOKEN environment variable not set"
    echo ""
    echo "Usage:"
    echo "  TOKEN=\"your-jwt-token\" ./init-sla-test-data.sh"
    echo ""
    echo "To get a token:"
    echo "  1. Login via API: POST http://localhost:8080/api/auth/login"
    echo "  2. Copy the 'token' from response"
    echo "  3. Run: TOKEN=\"eyJhbGc...\" ./init-sla-test-data.sh"
    echo ""
    echo "Or use curl to login and extract token:"
    echo "  TOKEN=\$(curl -s -X POST http://localhost:8080/api/auth/login \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"username\":\"your-user\",\"password\":\"your-pass\"}' | jq -r '.token')"
    echo ""
    exit 1
fi

echo "=========================================="
echo "SLA Test Data Initialization"
echo "=========================================="
echo "API URL: $API_URL"
echo "Tenant ID: $TENANT_ID"
echo "Resource ID: $RESOURCE_ID"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Function to create SLA
create_sla() {
    local name=$1
    local description=$2
    local metric_name=$3
    local period_type=$4
    local target=$5
    local threshold=$6

    echo "Creating: $name ($period_type)..."

    response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/definitions" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d "{
        \"name\": \"$name\",
        \"description\": \"$description\",
        \"tenantId\": \"$TENANT_ID\",
        \"resourceId\": \"$RESOURCE_ID\",
        \"metricNamespace\": \"oci_computeagent\",
        \"metricName\": \"$metric_name\",
        \"statisticType\": \"mean()\",
        \"comparator\": \"LTE\",
        \"targetType\": \"PERCENT\",
        \"targetValue\": $target,
        \"alertThresholdPercent\": $(echo "$target - 5" | bc),
        \"metricThreshold\": $threshold,
        \"periodType\": \"$period_type\",
        \"activeFrom\": \"2025-01-01T00:00:00\",
        \"graceToleranceMinutes\": 15,
        \"isActive\": true,
        \"notificationRecipientEmails\": \"ops@sistemi.rs\"
      }")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" == "201" || "$http_code" == "200" ]]; then
        sla_id=$(echo "$body" | jq -r '.id // "unknown"')
        echo "✓ Created successfully (ID: $sla_id)"
    else
        echo "✗ Failed (HTTP $http_code)"
        echo "  Response: $body"
    fi
    echo ""
}

# Create test SLAs
echo "1. Creating DAILY SLA..."
create_sla \
    "DAILY CPU - UI Test" \
    "Daily CPU utilization monitoring for UI testing" \
    "CpuUtilization" \
    "DAILY" \
    95.00 \
    80.00

echo "2. Creating WEEKLY SLA..."
create_sla \
    "WEEKLY Memory - UI Test" \
    "Weekly memory utilization monitoring for UI testing" \
    "MemoryUtilization" \
    "WEEKLY" \
    98.00 \
    85.00

echo "3. Creating MONTHLY SLA..."
create_sla \
    "MONTHLY Availability - UI Test" \
    "Monthly system availability monitoring for UI testing" \
    "CpuUtilization" \
    "MONTHLY" \
    99.90 \
    100.00

echo "=========================================="
echo "Verification"
echo "=========================================="

# Verify via API
echo "Active SLAs from API:"
verify_response=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/definitions/active")

if echo "$verify_response" | jq empty 2>/dev/null; then
    echo "$verify_response" | jq -r '.[] | "  - \(.name) (\(.periodType))"'
else
    echo "✗ Error retrieving SLAs:"
    echo "  $verify_response"
fi

echo ""
echo "✓ Initialization complete!"
echo ""
echo "Next steps:"
echo "1. Open UI: http://localhost:5173"
echo "2. Select an SLA from dropdown"
echo "3. Choose period and generate report"
echo ""