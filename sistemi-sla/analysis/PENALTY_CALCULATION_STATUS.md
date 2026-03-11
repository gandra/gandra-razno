# SLA Penalty Calculation - Implementation Status Report

**Date:** 2025-11-14
**Status:** NOT IMPLEMENTED (TBD-2 - Phase 2)
**Priority:** High - Business Critical Feature

---

## Executive Summary

### Current Status: ❌ NOT IMPLEMENTED

**Penalty calculation logic is NOT implemented** despite having all the database schema and UI fields in place. The system can store penalty configuration (currency, amount, formula) but does **not calculate or apply penalties** when SLA breaches occur.

### What Exists Today

✅ **Database Schema** - Ready (V6__create_sla_tables.sql)
- `sla_definition.penalty_currency` (VARCHAR(3) - ISO 4217: USD, EUR, RSD)
- `sla_definition.penalty_amount` (DECIMAL(15,2))
- `sla_definition.penalty_calculation_formula` (VARCHAR(2000))
- `sla_result.penalty_amount` (DECIMAL(15,2)) - **NEVER populated**
- `sla_result.penalty_currency` (VARCHAR(3)) - **NEVER populated**

✅ **Entity Fields** - Ready
- `SlaDefinition.java:120-127` - Penalty configuration fields
- `SlaResult.java:92-97` - Penalty result fields

✅ **Frontend UI** - Ready
- `SlaFormPage.tsx` - Penalty input fields (Step 4: Advanced Options)
- `SlaReportDisplay.tsx` - Penalty display (shows null)
- `sla.types.ts` - TypeScript penalty types

✅ **SLA Target Type Enum** - Ready
- `SlaTargetType.PERCENT` - Compliance percentage target (currently used)
- `SlaTargetType.PENALTY` - Financial penalty target (NOT USED)

### What's Missing: ❌ BUSINESS LOGIC

❌ **Penalty Calculation Service** - Does NOT exist
❌ **Formula Parser** - Does NOT exist
❌ **Penalty Application Logic** - Does NOT exist
❌ **SlaComputationService** - Does NOT populate penalty fields (lines 115-130)

---

## Detailed Analysis

### 1. Database Schema Review

#### SLA Definition Table (Configuration Storage)

```sql
-- Line 30-32 in V6__create_sla_tables.sql
`penalty_amount` decimal(15,2) DEFAULT NULL,           -- Base penalty amount (e.g., 1000.00 USD)
`penalty_calculation_formula` varchar(2000) DEFAULT NULL,  -- Formula for dynamic calculation
`penalty_currency` varchar(3) DEFAULT NULL,            -- ISO 4217 (USD, EUR, RSD)
```

**Purpose:** Store the penalty **configuration** for an SLA definition.

**Examples:**
- Simple: `penalty_amount = 1000.00, penalty_currency = USD, formula = NULL` → Flat $1000 penalty
- Complex: `penalty_amount = 100.00, formula = "amount * breach_hours"` → $100 per hour of breach

#### SLA Result Table (Computed Penalty Storage)

```sql
-- Line 76-77 in V6__create_sla_tables.sql
`penalty_amount` decimal(15,2) DEFAULT NULL,   -- COMPUTED penalty for THIS result
`penalty_currency` varchar(3) DEFAULT NULL,    -- Currency of the penalty
```

**Purpose:** Store the **calculated penalty** for a specific SLA result.

**Current Behavior:** ❌ Always NULL - Never populated

**Expected Behavior:** ✅ Should be calculated and saved during SLA computation

#### Target Type Configuration

```sql
-- Line 37 in V6__create_sla_tables.sql
`target_type` enum('PERCENT','PENALTY') NOT NULL,
```

**Purpose:** Determines what the `target_value` represents:
- `PERCENT`: `target_value = 95.00` means 95% compliance target
- `PENALTY`: `target_value = 1000.00` means max acceptable penalty amount

**Current Usage:** ✅ Only `PERCENT` is used in production
**Future Usage:** ❌ `PENALTY` type needs penalty calculation logic

---

### 2. Entity Implementation Review

#### SlaDefinition Entity

**File:** `oci-library/src/main/java/com/sistemisolutions/oci/lib/entity/sla/SlaDefinition.java`

```java
// Lines 118-127
// ========== Penalty Configuration (TBD-2: Added now, logic in Phase 2) ==========

@Column(name = "penalty_currency", length = 3)
private String penaltyCurrency; // ISO 4217: USD, EUR, RSD

@Column(name = "penalty_amount", precision = 15, scale = 2)
private BigDecimal penaltyAmount;

@Column(name = "penalty_calculation_formula", length = 2000)
private String penaltyCalculationFormula; // Future: complex formulas
```

**Status:** ✅ Fields exist, can be configured via API/UI
**Validation:** ❌ No validation for currency codes (should be ISO 4217)
**Formula Support:** ❌ No parser or evaluator

#### SlaResult Entity

**File:** `oci-library/src/main/java/com/sistemisolutions/oci/lib/entity/sla/SlaResult.java`

```java
// Lines 91-97
// ========== Penalty (Phase 2) ==========

@Column(name = "penalty_amount", precision = 15, scale = 2)
private BigDecimal penaltyAmount;

@Column(name = "penalty_currency", length = 3)
private String penaltyCurrency;
```

**Status:** ✅ Fields exist
**Current Value:** ❌ Always NULL
**Population:** ❌ Never set in SlaComputationService

---

### 3. Backend Service Implementation Review

#### SlaComputationService - Core SLA Calculation

**File:** `oci-monitor/src/main/java/com/sistemisolutions/oci/monitor/service/sla/SlaComputationService.java`

**Method:** `computeSla()` (lines 52-143)

**Current Flow:**
```java
// Line 115-130: Populate SlaResult fields
slaResult.setComputedAt(LocalDateTime.now());
slaResult.setExpectedDatapoints(metrics.getExpectedDatapoints());
slaResult.setActualDatapoints(metrics.getActualDatapoints());
slaResult.setMatchedDatapoints(metrics.getMatchedDatapoints());
slaResult.setDataCoveragePercent(metrics.getDataCoveragePercent());
slaResult.setCompliancePercent(metrics.getCompliancePercent());
slaResult.setBreachDurationMinutes(metrics.getBreachDurationMinutes());
slaResult.setStatus(status);
slaResult.setMessage(message);
slaResult.setIsManuallyAdjusted(false);

// ❌ MISSING: Penalty calculation
// Should add here:
// BigDecimal penalty = calculatePenalty(slaDefinition, metrics, status);
// slaResult.setPenaltyAmount(penalty);
// slaResult.setPenaltyCurrency(slaDefinition.getPenaltyCurrency());
```

**What's Missing:**
1. Call to penalty calculation service
2. Conditional logic (only calculate penalty if BREACHED)
3. Currency propagation from definition to result
4. Formula evaluation support

---

### 4. Frontend Implementation Review

#### SLA Form Page

**File:** `references/oci-sla-management-ui/src/pages/SlaFormPage.tsx`

**Penalty Fields (Step 4: Advanced Options):**
```typescript
// Lines 83-85 - Form State
penaltyCurrency: '',
penaltyAmount: '',
penaltyCalculationFormula: '',
```

**Status:** ✅ UI fields exist, can be filled out
**Validation:** ⚠️ No frontend validation for currency format
**Formula Editor:** ❌ Plain text input (no syntax highlighting or validation)

#### SLA Report Display

**File:** `references/oci-sla-management-ui/src/components/SlaReportDisplay.tsx`

**Expected Behavior:** Should display calculated penalty from `slaResult.penaltyAmount`

**Current Behavior:** ❌ Always shows NULL or empty

---

## Business Impact Analysis

### What This Means for Users

1. **Configuration Without Action**
   - Users can configure penalty amounts and formulas
   - System accepts and stores this configuration
   - **But nothing happens** when SLA is breached

2. **Reporting Gap**
   - SLA reports show breaches
   - SLA reports show compliance percentages
   - **But no financial impact** is calculated or displayed

3. **Billing Integration Blocked**
   - Cannot generate invoices for SLA penalties
   - Cannot track total penalty amounts per tenant
   - Cannot automate penalty billing workflows

### Financial Impact

For production SLA monitoring, **penalty calculation is a critical business feature**:

- **Cloud Service Providers**: Contractual SLA penalties (e.g., 10% credit for < 99.9% uptime)
- **Managed Services**: Financial compensation for service disruptions
- **Enterprise Agreements**: Tiered penalty structures based on breach severity

**Example from AWS SLA:**
- 99.0% - 99.9% uptime: 10% service credit
- 95.0% - 99.0% uptime: 25% service credit
- < 95.0% uptime: 100% service credit

---

## Technical Implementation Gap Analysis

### Gap 1: No Penalty Calculation Service

**Missing:** `PenaltyCalculationService` or `PenaltyCalculator`

**Required Responsibilities:**
1. Calculate base penalty from `slaDefinition.penaltyAmount`
2. Evaluate custom formulas from `slaDefinition.penaltyCalculationFormula`
3. Apply breach severity multipliers
4. Round to currency precision (2 decimal places)
5. Handle currency conversion (future)

**Recommended Location:** `oci-monitor/src/main/java/com/sistemisolutions/oci/monitor/service/sla/PenaltyCalculationService.java`

### Gap 2: No Formula Parser

**Missing:** Formula expression evaluator

**Current Field:** `penalty_calculation_formula VARCHAR(2000)`

**Expected Formulas:**
```
Simple:
- "1000" → Flat $1000 penalty
- "100 * breach_hours" → $100 per hour breached
- "base_amount * (1 + (target_value - compliance_percent) / 10)" → Escalating penalty

Complex:
- "base_amount * breach_duration_minutes / 60" → Per-minute penalty (converted to hours)
- "base_amount * max(0, (target_value - compliance_percent) / target_value)" → Proportional to miss
- "CASE WHEN compliance_percent < 95 THEN base_amount * 2 ELSE base_amount END" → Tiered
```

**Recommendation:** Use **Spring Expression Language (SpEL)** or **Apache Commons JEXL**

### Gap 3: Integration with SlaComputationService

**File:** `SlaComputationService.java`

**Missing Code (lines 115-130):**
```java
// CURRENT CODE:
slaResult.setCompliancePercent(metrics.getCompliancePercent());
slaResult.setBreachDurationMinutes(metrics.getBreachDurationMinutes());
slaResult.setStatus(status);
slaResult.setMessage(message);

// ❌ MISSING:
// Calculate penalty if breached
if (status == SlaStatus.BREACHED && slaDefinition.getPenaltyAmount() != null) {
    PenaltyCalculationResult penaltyResult = penaltyCalculationService.calculatePenalty(
        slaDefinition, metrics, status
    );
    slaResult.setPenaltyAmount(penaltyResult.getAmount());
    slaResult.setPenaltyCurrency(penaltyResult.getCurrency());
}
```

### Gap 4: No Validation for Currency Codes

**Missing:** ISO 4217 currency code validation

**Required Validation:**
```java
private static final Set<String> VALID_CURRENCIES = Set.of(
    "USD", "EUR", "GBP", "RSD", "CHF", "JPY", "AUD", "CAD"
);

public void validatePenaltyCurrency(String currency) {
    if (currency != null && !VALID_CURRENCIES.contains(currency)) {
        throw new IllegalArgumentException("Invalid currency code: " + currency);
    }
}
```

---

## Recommended Implementation Approach

### Option 1: Simple Fixed Penalty (Quick Win - 1 Day)

**Scope:** Calculate flat penalty from `penalty_amount` field only

**Implementation:**
1. Create `PenaltyCalculationService` with single method: `calculateFixedPenalty()`
2. Integrate with `SlaComputationService` (5-line change)
3. Only calculate if `status == BREACHED`
4. Copy `penalty_currency` and `penalty_amount` from definition to result

**Pros:**
- ✅ Quick to implement (1 day)
- ✅ No external dependencies
- ✅ Covers 80% of use cases (flat penalty)
- ✅ Low risk

**Cons:**
- ❌ No formula support
- ❌ No tiered penalties
- ❌ Limited flexibility

**Example:**
```java
@Service
public class PenaltyCalculationService {
    public BigDecimal calculateFixedPenalty(SlaDefinition definition, SlaStatus status) {
        if (status != SlaStatus.BREACHED) {
            return null; // No penalty for non-breach
        }
        return definition.getPenaltyAmount(); // Use configured amount
    }
}
```

---

### Option 2: Formula-Based Penalty (Comprehensive - 3-5 Days)

**Scope:** Full formula evaluation with SpEL or JEXL

**Implementation:**
1. Create `PenaltyCalculationService` with formula evaluator
2. Support variables: `base_amount`, `breach_hours`, `compliance_percent`, `target_value`
3. Validate formulas on SLA definition save
4. Add formula syntax help in UI
5. Integrate with `SlaComputationService`

**Pros:**
- ✅ Maximum flexibility
- ✅ Supports complex business rules
- ✅ Future-proof
- ✅ Can model any penalty structure

**Cons:**
- ❌ More complex (3-5 days)
- ❌ Security risk (need expression sandboxing)
- ❌ Requires thorough testing
- ❌ UI complexity for formula editor

**Example with SpEL:**
```java
@Service
public class PenaltyCalculationService {
    private final SpelExpressionParser parser = new SpelExpressionParser();

    public BigDecimal calculatePenalty(SlaDefinition def, AvailabilityMetricsDTO metrics, SlaStatus status) {
        if (status != SlaStatus.BREACHED) {
            return null;
        }

        // Build evaluation context
        StandardEvaluationContext context = new StandardEvaluationContext();
        context.setVariable("base_amount", def.getPenaltyAmount());
        context.setVariable("compliance_percent", metrics.getCompliancePercent());
        context.setVariable("target_value", def.getTargetValue());
        context.setVariable("breach_hours", metrics.getBreachDurationMinutes() / 60.0);

        // Evaluate formula or use default
        String formula = def.getPenaltyCalculationFormula();
        if (formula == null || formula.isBlank()) {
            return def.getPenaltyAmount(); // Default to fixed amount
        }

        Expression exp = parser.parseExpression(formula);
        Object result = exp.getValue(context);
        return new BigDecimal(result.toString()).setScale(2, RoundingMode.HALF_UP);
    }
}
```

---

### Option 3: Tiered Penalty (Middle Ground - 2-3 Days)

**Scope:** Predefined penalty tiers based on compliance levels

**Implementation:**
1. Add `SlaBreachSeverity` multipliers (CRITICAL: 2x, HIGH: 1.5x, MEDIUM: 1x, LOW: 0.5x)
2. Calculate: `penalty = base_amount * severity_multiplier`
3. Store breach severity in `sla_breach` table
4. Link penalty to breach severity

**Pros:**
- ✅ Moderate complexity (2-3 days)
- ✅ Common business pattern
- ✅ Easy to understand for users
- ✅ No formula security concerns

**Cons:**
- ❌ Less flexible than formulas
- ❌ Still requires custom logic for edge cases

**Example:**
```java
@Service
public class PenaltyCalculationService {
    public BigDecimal calculateTieredPenalty(SlaDefinition def, BigDecimal compliancePercent) {
        BigDecimal baseAmount = def.getPenaltyAmount();
        if (baseAmount == null) {
            return null;
        }

        BigDecimal target = def.getTargetValue();
        BigDecimal multiplier;

        if (compliancePercent.compareTo(target.subtract(BigDecimal.valueOf(10))) < 0) {
            multiplier = BigDecimal.valueOf(2.0); // Critical: > 10% below target
        } else if (compliancePercent.compareTo(target.subtract(BigDecimal.valueOf(5))) < 0) {
            multiplier = BigDecimal.valueOf(1.5); // High: 5-10% below target
        } else {
            multiplier = BigDecimal.ONE; // Medium: < 5% below target
        }

        return baseAmount.multiply(multiplier).setScale(2, RoundingMode.HALF_UP);
    }
}
```

---

## Recommended Approach: **Hybrid Solution**

### Best of All Worlds

**Phase 2.1 (Week 1): Simple Fixed Penalty** → Option 1
- Implement basic penalty calculation
- Get 80% of value with 20% of effort
- **Deliverable:** Working penalty calculation in 1-2 days

**Phase 2.2 (Week 2): Add Formula Support** → Option 2
- Build on top of Phase 2.1
- Add SpEL-based formula evaluation
- Secure expression sandbox
- **Deliverable:** Full formula support in 3 days

**Phase 2.3 (Week 3): Enhanced UX** → UI Improvements
- Formula syntax help
- Formula validation on save
- Penalty preview calculator
- **Deliverable:** User-friendly formula editor

---

## Implementation Task Breakdown

### Task 1: Create PenaltyCalculationService (Simple Fixed)

**Estimate:** 4 hours

**Subtasks:**
1. Create `oci-monitor/service/sla/PenaltyCalculationService.java`
2. Implement `calculateFixedPenalty(SlaDefinition, SlaStatus)` method
3. Add unit tests
4. Add Lombok `@Service` and `@RequiredArgsConstructor`

**Acceptance Criteria:**
- Returns `penalty_amount` if `status == BREACHED`
- Returns `null` if status is FULFILLED, WARNING, or INSUFFICIENT_DATA
- Handles null `penalty_amount` gracefully

---

### Task 2: Integrate with SlaComputationService

**Estimate:** 2 hours

**Subtasks:**
1. Inject `PenaltyCalculationService` into `SlaComputationService`
2. Add penalty calculation call after line 124
3. Set `penaltyAmount` and `penaltyCurrency` on `slaResult`
4. Update integration tests

**Code Change (SlaComputationService.java:115-135):**
```java
// After line 124:
slaResult.setMessage(message);

// ADD:
if (status == SlaStatus.BREACHED && slaDefinition.getPenaltyAmount() != null) {
    BigDecimal penalty = penaltyCalculationService.calculateFixedPenalty(slaDefinition, status);
    slaResult.setPenaltyAmount(penalty);
    slaResult.setPenaltyCurrency(slaDefinition.getPenaltyCurrency());
}

slaResult.setIsManuallyAdjusted(false);
```

**Acceptance Criteria:**
- Penalty fields populated on BREACHED status
- Penalty fields remain NULL on FULFILLED/WARNING
- Currency copied from definition to result

---

### Task 3: Add Currency Validation

**Estimate:** 2 hours

**Subtasks:**
1. Create `CurrencyValidator` utility class
2. Add ISO 4217 currency code set
3. Validate in `SlaDefinitionManagementService.validateRequest()`
4. Add unit tests

**Acceptance Criteria:**
- Rejects invalid currency codes (e.g., "XXX", "INVALID")
- Accepts valid codes (USD, EUR, GBP, RSD, etc.)
- Validation runs on both create and update

---

### Task 4: Frontend - Display Penalty in Reports

**Estimate:** 3 hours

**Subtasks:**
1. Update `SlaReportDisplay.tsx` to show penalty amount
2. Format currency display (e.g., "$1,000.00 USD")
3. Show "No penalty" for non-breach results
4. Add penalty column to SLA results table

**Acceptance Criteria:**
- Penalty displayed with proper formatting
- Currency symbol shown based on currency code
- Handles null penalty gracefully

---

### Task 5: Add Formula Support (Phase 2.2)

**Estimate:** 8 hours

**Subtasks:**
1. Add SpEL dependency to `oci-monitor/pom.xml`
2. Implement `evaluateFormula()` method in `PenaltyCalculationService`
3. Add expression context with variables
4. Add formula validation
5. Add security sandbox (disable dangerous operations)
6. Update unit tests with formula examples
7. Document supported formula syntax

**Acceptance Criteria:**
- Supports basic formulas: `base_amount * 2`
- Supports variables: `breach_hours`, `compliance_percent`
- Rejects invalid formulas with clear error messages
- Securely sandboxed (no System.exit, no reflection)

---

### Task 6: Frontend - Formula Editor (Phase 2.3)

**Estimate:** 6 hours

**Subtasks:**
1. Add formula syntax help tooltip
2. Add formula validation on blur
3. Show example formulas
4. Add penalty preview calculator
5. Syntax highlighting (optional)

**Acceptance Criteria:**
- User can see formula syntax help
- Invalid formulas show error messages
- User can test formula before saving

---

## Testing Strategy

### Unit Tests

**PenaltyCalculationService:**
- Test fixed penalty calculation
- Test NULL handling
- Test formula evaluation
- Test invalid formulas
- Test edge cases (negative compliance, zero breach)

**SlaComputationService:**
- Test penalty integration
- Test currency propagation
- Test conditional penalty (only on BREACH)

### Integration Tests

**End-to-End SLA Computation:**
1. Create SLA definition with penalty configuration
2. Trigger manual SLA computation
3. Verify `sla_result.penalty_amount` is populated
4. Verify `sla_result.penalty_currency` matches definition

**Formula Evaluation:**
1. Create SLA with formula: `base_amount * breach_hours`
2. Trigger computation with 2-hour breach
3. Verify penalty = base_amount * 2

### Manual Testing

**Scenarios:**
1. **Simple Flat Penalty:**
   - SLA: 99% target, $1000 penalty
   - Result: 97% compliance → $1000 penalty

2. **Formula-Based Penalty:**
   - SLA: Formula `100 * breach_hours`
   - Result: 3-hour breach → $300 penalty

3. **No Penalty on Fulfilled:**
   - SLA: 99% target, $1000 penalty
   - Result: 99.5% compliance → No penalty

---

## Migration & Deployment Notes

### Database Migration

**NO MIGRATION NEEDED** - Schema already exists (V6__create_sla_tables.sql)

### Backward Compatibility

✅ **100% Backward Compatible**
- Existing SLA definitions without penalty config → No penalty calculated
- Existing SLA results with NULL penalty → Remain NULL
- New computations → Penalty calculated if configured

### Deployment Strategy

1. **Deploy Backend Changes:**
   - `oci-monitor` with `PenaltyCalculationService`
   - Restart `oci-monitor` service

2. **Verify Penalty Calculation:**
   - Trigger manual SLA computation
   - Check `sla_result` table for populated `penalty_amount`

3. **Deploy Frontend Changes:**
   - Update `SlaReportDisplay.tsx`
   - Clear browser cache

4. **Announce Feature:**
   - Notify users that penalty calculation is now live
   - Provide documentation on formula syntax

---

## Documentation Requirements

### User Documentation

1. **Penalty Configuration Guide:**
   - How to configure flat penalties
   - How to write formulas
   - Supported variables and functions
   - Example formulas

2. **Penalty Reports:**
   - How to view calculated penalties
   - How to export penalty data
   - How to generate billing reports

### Developer Documentation

1. **Architecture Documentation:**
   - Update `OCI-SLA-ARCHITECTURE.md` with penalty calculation flow
   - Add sequence diagram for penalty computation
   - Document formula evaluation engine

2. **API Documentation:**
   - Document penalty fields in DTOs
   - Add penalty calculation examples

---

## Risk Assessment

### Low Risk

✅ Simple fixed penalty implementation
✅ Database schema already exists
✅ Backward compatible (no breaking changes)
✅ Can be deployed incrementally

### Medium Risk

⚠️ Formula evaluation - security concerns
⚠️ Currency conversion (future) - exchange rate data needed
⚠️ Performance impact if formulas are complex

### Mitigation

1. **Security:** Use SpEL with restricted context (no dangerous operations)
2. **Performance:** Cache formula expressions, validate on save
3. **Testing:** Comprehensive unit + integration tests
4. **Rollback:** Feature flag to disable penalty calculation if needed

---

## Success Metrics

### Functional Metrics

- ✅ 100% of BREACHED SLA results have penalty calculated
- ✅ Penalty amounts match expected values in test cases
- ✅ No penalties calculated for FULFILLED/WARNING statuses

### Performance Metrics

- ✅ Penalty calculation adds < 50ms to SLA computation time
- ✅ Formula evaluation completes in < 10ms

### Business Metrics

- ✅ Users configure penalties on 50%+ of SLA definitions
- ✅ Finance team uses penalty reports for billing
- ✅ Reduction in manual penalty calculations

---

## Next Steps - Immediate Actions

### Step 1: Decision (15 min)

**Question:** Which approach do we want to start with?
- Option A: Simple Fixed Penalty (1-2 days, quick win)
- Option B: Formula-Based (3-5 days, comprehensive)
- Option C: Hybrid (Week 1: Simple, Week 2: Formulas)

**Recommendation:** **Option C - Hybrid** for maximum value

---

### Step 2: Task 1 Implementation (4 hours)

**Create PenaltyCalculationService**

Would you like me to proceed with implementing Task 1?

---

## Summary

### What We Have Today

✅ Database schema (penalty_amount, penalty_currency, penalty_calculation_formula)
✅ Entity fields (SlaDefinition, SlaResult)
✅ Frontend UI (penalty input fields)
✅ API endpoints (can save penalty config)

### What We're Missing

❌ **Penalty calculation business logic**
❌ Formula evaluation engine
❌ Integration with SlaComputationService
❌ Currency validation
❌ Penalty display in reports

### Recommended Path Forward

1. **Week 1:** Implement simple fixed penalty (Tasks 1-4)
2. **Week 2:** Add formula support (Task 5)
3. **Week 3:** Enhance UX (Task 6)

### Estimated Effort

- **Phase 2.1 (Simple):** 1-2 days
- **Phase 2.2 (Formulas):** 3 days
- **Phase 2.3 (UX):** 2 days
- **Total:** 6-7 days for complete feature

**Ready to start implementation?** Let me know which approach you prefer, and I'll begin with Task 1.
