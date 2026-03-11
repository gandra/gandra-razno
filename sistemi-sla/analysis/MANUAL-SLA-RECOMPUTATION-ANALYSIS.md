# Manual SLA Recomputation Analysis - Improvements & Features

## 📋 Problem Statement

### Trenutna Situacija

Postoji osnovni manual trigger endpoint u `oci-api`:

```java
// oci-api/src/main/java/com/sistemisolutions/oci/api/controller/sla/SlaController.java
@PostMapping("/trigger")
public ResponseEntity<?> triggerSlaComputation(
        @RequestBody SlaComputationRequestDTO request) {

    // Delegates to oci-monitor via MonitorApiService
    monitorApiService.triggerSlaComputation(request);

    return ResponseEntity.ok("SLA computation triggered");
}
```

I endpoint u `oci-monitor`:

```java
// oci-monitor/src/main/java/com/sistemisolutions/oci/monitor/controller/SlaSchedulerController.java
@PostMapping("/trigger")
public ResponseEntity<?> triggerComputation(
        @RequestBody SlaComputationRequestDTO request) {

    SlaResult result = slaComputationService.computeSla(
        request.getSlaDefinitionId(),
        request.getPeriodStart(),
        request.isForceRecompute(),
        request.getTriggeredBy()
    );

    return ResponseEntity.ok(result);
}
```

### 🚨 Problemi i Ograničenja

1. **Limited batch support**: Može se triggerovati samo jedan SLA definition po pozivu
2. **No progress tracking**: Nema način da se prati status batch recomputation-a
3. **No cancellation**: Jednom pokrenut, ne može da se canceluje
4. **Poor error handling**: Ne vraća detaljne error informacije
5. **No validation**: Ne validira da li period već ima result
6. **No dry-run**: Ne može da se vidi šta će se izračunati bez stvarnog izvršenja
7. **No bulk operations**: Ne može da se recompute-uje range perioda odjednom
8. **No historical recomputation**: Teško je recompute-ovati više meseci unazad

---

## 🎯 Cilj

Poboljšati manual recomputation sistem sa:

1. **Batch operations**: Recompute multiple SLA definitions ili periods odjednom
2. **Progress tracking**: Real-time status recomputation-a
3. **Dry-run mode**: Preview šta će biti recompute-ovano
4. **Better validation**: Upozorenja pre recomputation-a
5. **Bulk period recomputation**: Recompute date ranges (e.g., "last 3 months")
6. **Cancellation support**: Ability to cancel running batch operations
7. **Detailed results**: Report sa success/failure stats

---

## 🔧 Pristup 1: Enhanced Single SLA Trigger (Quick Win ✅)

### Opis

Poboljšanje postojećeg single-SLA trigger endpointa sa boljom validacijom i response-om.

### Implementacija

**1. Enhanced Request DTO:**

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SlaComputationRequestDTO {

    @NotNull(message = "slaDefinitionId is required")
    private UUID slaDefinitionId;

    @NotNull(message = "periodStart is required")
    private LocalDate periodStart;

    private Boolean forceRecompute = false;

    private Boolean dryRun = false; // ✅ NEW: Preview mode

    @Size(max = 255)
    private String triggeredBy;

    // ✅ NEW: Optional end date for range recomputation
    private LocalDate periodEnd;
}
```

**2. Enhanced Response DTO:**

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SlaComputationResponseDTO {

    private UUID slaDefinitionId;
    private String slaDefinitionName;

    // Computation results
    private List<SlaResultSummary> results;

    // Validation warnings
    private List<String> warnings;

    // Statistics
    private ComputationStatistics statistics;

    // Dry run info
    private Boolean wasDryRun;
    private String dryRunMessage;

    @Data
    @Builder
    public static class SlaResultSummary {
        private UUID resultId;
        private LocalDate periodStart;
        private LocalDate periodEnd;
        private SlaStatus status;
        private BigDecimal compliancePercent;
        private Boolean wasCreated; // true if new, false if updated
        private String message;
    }

    @Data
    @Builder
    public static class ComputationStatistics {
        private Integer totalPeriods;
        private Integer successCount;
        private Integer skippedCount; // Already exists and forceRecompute=false
        private Integer failureCount;
        private Long durationMs;
    }
}
```

**3. Enhanced Service:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class SlaComputationService {

    /**
     * Enhanced computation method with validation, dry-run, and detailed response.
     */
    @Transactional
    public SlaComputationResponseDTO computeSlaEnhanced(SlaComputationRequestDTO request) {
        long startTime = System.currentTimeMillis();

        // 1. Load and validate SLA definition
        SlaDefinition slaDefinition = slaDefinitionRepository.findById(request.getSlaDefinitionId())
                .orElseThrow(() -> new ResourceNotFoundException(
                    "SLA Definition not found: " + request.getSlaDefinitionId()
                ));

        if (!slaDefinition.getIsActive()) {
            throw new IllegalArgumentException("SLA Definition is inactive: " + slaDefinition.getName());
        }

        // 2. Calculate periods to compute
        List<LocalDate> periodsToCompute = calculatePeriods(
                request.getPeriodStart(),
                request.getPeriodEnd(),
                slaDefinition.getPeriodType()
        );

        log.info("Computing {} periods for SLA: {}", periodsToCompute.size(), slaDefinition.getName());

        // 3. Pre-check existing results
        List<String> warnings = new ArrayList<>();
        for (LocalDate periodDate : periodsToCompute) {
            LocalDateTime periodStart = calculatePeriodStart(slaDefinition.getPeriodType(), periodDate);
            LocalDateTime periodEnd = calculatePeriodEnd(slaDefinition.getPeriodType(), periodStart);

            Optional<SlaResult> existing = slaResultRepository.findByDefinitionAndPeriod(
                    request.getSlaDefinitionId(), periodStart, periodEnd
            );

            if (existing.isPresent() && !request.getForceRecompute()) {
                warnings.add(String.format(
                    "Result already exists for period %s to %s (will be skipped)",
                    periodStart, periodEnd
                ));
            }
        }

        // 4. DRY RUN - Return preview without actual computation
        if (Boolean.TRUE.equals(request.getDryRun())) {
            return SlaComputationResponseDTO.builder()
                    .slaDefinitionId(slaDefinition.getId())
                    .slaDefinitionName(slaDefinition.getName())
                    .warnings(warnings)
                    .statistics(SlaComputationResponseDTO.ComputationStatistics.builder()
                            .totalPeriods(periodsToCompute.size())
                            .build())
                    .wasDryRun(true)
                    .dryRunMessage(String.format(
                        "Dry run: Would compute %d periods for SLA '%s'",
                        periodsToCompute.size(),
                        slaDefinition.getName()
                    ))
                    .build();
        }

        // 5. ACTUAL COMPUTATION
        List<SlaComputationResponseDTO.SlaResultSummary> results = new ArrayList<>();
        int successCount = 0;
        int skippedCount = 0;
        int failureCount = 0;

        for (LocalDate periodDate : periodsToCompute) {
            try {
                SlaResult result = computeSla(
                        request.getSlaDefinitionId(),
                        periodDate,
                        request.getForceRecompute(),
                        request.getTriggeredBy()
                );

                boolean wasCreated = result.getCreatedBy().equals(request.getTriggeredBy());

                results.add(SlaComputationResponseDTO.SlaResultSummary.builder()
                        .resultId(result.getId())
                        .periodStart(periodDate)
                        .periodEnd(periodDate.plusDays(1)) // Simplified
                        .status(result.getStatus())
                        .compliancePercent(result.getCompliancePercent())
                        .wasCreated(wasCreated)
                        .message(result.getMessage())
                        .build());

                if (wasCreated) {
                    successCount++;
                } else {
                    skippedCount++;
                }

            } catch (Exception e) {
                log.error("Failed to compute SLA for period {}: {}", periodDate, e.getMessage());

                results.add(SlaComputationResponseDTO.SlaResultSummary.builder()
                        .periodStart(periodDate)
                        .wasCreated(false)
                        .message("ERROR: " + e.getMessage())
                        .build());

                failureCount++;
            }
        }

        long duration = System.currentTimeMillis() - startTime;

        // 6. Build response
        return SlaComputationResponseDTO.builder()
                .slaDefinitionId(slaDefinition.getId())
                .slaDefinitionName(slaDefinition.getName())
                .results(results)
                .warnings(warnings)
                .statistics(SlaComputationResponseDTO.ComputationStatistics.builder()
                        .totalPeriods(periodsToCompute.size())
                        .successCount(successCount)
                        .skippedCount(skippedCount)
                        .failureCount(failureCount)
                        .durationMs(duration)
                        .build())
                .wasDryRun(false)
                .build();
    }

    /**
     * Calculate list of periods to compute based on start/end dates.
     */
    private List<LocalDate> calculatePeriods(LocalDate start, LocalDate end, SlaPeriodType periodType) {
        if (end == null) {
            return List.of(start); // Single period
        }

        List<LocalDate> periods = new ArrayList<>();
        LocalDate current = start;

        while (!current.isAfter(end)) {
            periods.add(current);

            // Increment based on period type
            current = switch (periodType) {
                case DAILY -> current.plusDays(1);
                case WEEKLY -> current.plusWeeks(1);
                case MONTHLY -> current.plusMonths(1);
                case QUARTERLY -> current.plusMonths(3);
                case YEARLY -> current.plusYears(1);
                default -> current.plusDays(1);
            };
        }

        return periods;
    }
}
```

**4. Enhanced Controller:**

```java
@PostMapping("/trigger")
public ResponseEntity<SlaComputationResponseDTO> triggerSlaComputation(
        @RequestBody @Valid SlaComputationRequestDTO request) {

    log.info("Manual SLA computation triggered by: {}", request.getTriggeredBy());

    SlaComputationResponseDTO response = slaComputationService.computeSlaEnhanced(request);

    return ResponseEntity.ok(response);
}
```

### Example Usage

**Dry Run:**
```bash
POST /api/sla/trigger
{
  "slaDefinitionId": "abc-123",
  "periodStart": "2025-10-01",
  "periodEnd": "2025-10-31",
  "dryRun": true,
  "triggeredBy": "john.doe"
}

Response:
{
  "slaDefinitionId": "abc-123",
  "slaDefinitionName": "Production API Availability",
  "warnings": [
    "Result already exists for period 2025-10-01 to 2025-10-02 (will be skipped)",
    "Result already exists for period 2025-10-02 to 2025-10-03 (will be skipped)"
  ],
  "statistics": {
    "totalPeriods": 31
  },
  "wasDryRun": true,
  "dryRunMessage": "Dry run: Would compute 31 periods for SLA 'Production API Availability'"
}
```

**Actual Recomputation:**
```bash
POST /api/sla/trigger
{
  "slaDefinitionId": "abc-123",
  "periodStart": "2025-10-01",
  "periodEnd": "2025-10-31",
  "forceRecompute": false,
  "triggeredBy": "john.doe"
}

Response:
{
  "slaDefinitionId": "abc-123",
  "slaDefinitionName": "Production API Availability",
  "results": [
    {
      "resultId": "res-001",
      "periodStart": "2025-10-01",
      "status": "FULFILLED",
      "compliancePercent": 99.5,
      "wasCreated": true,
      "message": "SLA target met: 99.5% compliance"
    },
    ...
  ],
  "statistics": {
    "totalPeriods": 31,
    "successCount": 29,
    "skippedCount": 2,
    "failureCount": 0,
    "durationMs": 4523
  },
  "wasDryRun": false
}
```

### Prednosti ✅

1. **Dry-run preview**: Vidi šta će biti recompute-ovano
2. **Range support**: Recompute date range odjednom
3. **Detailed response**: Kompletan summary sa stats
4. **Validation warnings**: Upozorenja pre execution-a
5. **Fast implementation**: ~3-4 sata rada

### Mane ⚠️

1. **Synchronous**: Blokira HTTP request dok se ne završi
2. **No progress tracking**: Ne može da se prati progress long-running jobs
3. **Timeout risk**: Može da timeout-uje za velike range-ove
4. **No cancellation**: Ne može da se canceluje

### Kada koristiti

- **Quick win**: Brze improvemente nad postojećim sistemom
- **Small ranges**: Recomputation do ~30 perioda
- **Interactive use**: Admin manually triggeruje small batches

---

## 🔧 Pristup 2: Async Batch Job sa Progress Tracking (Production ✅)

### Opis

Kreiranje background batch job-a koji radi asinkrono sa progress tracking-om.

### Implementacija

**1. Batch Job Entity:**

```java
@Entity
@Table(name = "sla_batch_job", indexes = {
    @Index(name = "idx_batch_status", columnList = "status"),
    @Index(name = "idx_batch_created", columnList = "created_at")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SlaBatchJob {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @UuidGenerator
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "id", updatable = false, nullable = false, columnDefinition = "char(36)")
    private UUID id;

    @Column(name = "job_type", nullable = false, length = 50)
    @Enumerated(EnumType.STRING)
    private BatchJobType jobType; // SLA_RECOMPUTATION, BULK_NOTIFICATION, etc.

    @Column(name = "status", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private BatchJobStatus status; // PENDING, RUNNING, COMPLETED, FAILED, CANCELLED

    @Column(name = "sla_definition_id")
    @JdbcTypeCode(SqlTypes.CHAR)
    private UUID slaDefinitionId;

    @Column(name = "period_start")
    private LocalDate periodStart;

    @Column(name = "period_end")
    private LocalDate periodEnd;

    @Column(name = "force_recompute", nullable = false)
    private Boolean forceRecompute = false;

    @Column(name = "total_items")
    private Integer totalItems;

    @Column(name = "processed_items")
    private Integer processedItems = 0;

    @Column(name = "success_count")
    private Integer successCount = 0;

    @Column(name = "failure_count")
    private Integer failureCount = 0;

    @Column(name = "skipped_count")
    private Integer skippedCount = 0;

    @Column(name = "progress_percent", precision = 5, scale = 2)
    private BigDecimal progressPercent = BigDecimal.ZERO;

    @Column(name = "error_message", length = 2000)
    private String errorMessage;

    @Column(name = "created_by", nullable = false, length = 255)
    private String createdBy;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "started_at")
    private LocalDateTime startedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Column(name = "cancelled_at")
    private LocalDateTime cancelledAt;

    @Column(name = "cancelled_by", length = 255)
    private String cancelledBy;

    // Business logic methods
    public void start() {
        this.status = BatchJobStatus.RUNNING;
        this.startedAt = LocalDateTime.now();
    }

    public void incrementProgress(boolean success) {
        this.processedItems++;

        if (success) {
            this.successCount++;
        } else {
            this.failureCount++;
        }

        updateProgressPercent();
    }

    public void skip() {
        this.processedItems++;
        this.skippedCount++;
        updateProgressPercent();
    }

    private void updateProgressPercent() {
        if (totalItems != null && totalItems > 0) {
            this.progressPercent = BigDecimal.valueOf(processedItems)
                    .divide(BigDecimal.valueOf(totalItems), 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100))
                    .setScale(2, RoundingMode.HALF_UP);
        }
    }

    public void complete() {
        this.status = BatchJobStatus.COMPLETED;
        this.completedAt = LocalDateTime.now();
        this.progressPercent = BigDecimal.valueOf(100);
    }

    public void fail(String errorMessage) {
        this.status = BatchJobStatus.FAILED;
        this.completedAt = LocalDateTime.now();
        this.errorMessage = errorMessage;
    }

    public void cancel(String cancelledBy) {
        this.status = BatchJobStatus.CANCELLED;
        this.cancelledAt = LocalDateTime.now();
        this.cancelledBy = cancelledBy;
    }

    public boolean isCancellable() {
        return status == BatchJobStatus.PENDING || status == BatchJobStatus.RUNNING;
    }
}

public enum BatchJobType {
    SLA_RECOMPUTATION,
    BULK_NOTIFICATION,
    DATA_CLEANUP
}

public enum BatchJobStatus {
    PENDING,
    RUNNING,
    COMPLETED,
    FAILED,
    CANCELLED
}
```

**2. Batch Job Service:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class SlaBatchJobService {

    private final SlaBatchJobRepository batchJobRepository;
    private final SlaComputationService slaComputationService;
    private final ApplicationEventPublisher eventPublisher;

    /**
     * Create and queue batch recomputation job.
     * Returns immediately with job ID.
     */
    @Transactional
    public SlaBatchJob createRecomputationJob(SlaComputationRequestDTO request) {
        // Calculate total periods
        SlaDefinition slaDefinition = slaDefinitionRepository.findById(request.getSlaDefinitionId())
                .orElseThrow(() -> new ResourceNotFoundException("SLA not found"));

        List<LocalDate> periods = calculatePeriods(
                request.getPeriodStart(),
                request.getPeriodEnd(),
                slaDefinition.getPeriodType()
        );

        // Create job
        SlaBatchJob job = SlaBatchJob.builder()
                .jobType(BatchJobType.SLA_RECOMPUTATION)
                .status(BatchJobStatus.PENDING)
                .slaDefinitionId(request.getSlaDefinitionId())
                .periodStart(request.getPeriodStart())
                .periodEnd(request.getPeriodEnd())
                .forceRecompute(request.getForceRecompute())
                .totalItems(periods.size())
                .createdBy(request.getTriggeredBy())
                .createdAt(LocalDateTime.now())
                .build();

        SlaBatchJob saved = batchJobRepository.save(job);

        log.info("✅ Created batch job {} for {} periods", saved.getId(), periods.size());

        // Trigger async execution
        eventPublisher.publishEvent(new BatchJobCreatedEvent(this, saved.getId()));

        return saved;
    }

    /**
     * Execute batch job asynchronously.
     */
    @Async
    @EventListener
    @Transactional
    public void executeBatchJob(BatchJobCreatedEvent event) {
        UUID jobId = event.getJobId();

        SlaBatchJob job = batchJobRepository.findById(jobId)
                .orElseThrow(() -> new IllegalArgumentException("Job not found: " + jobId));

        try {
            job.start();
            batchJobRepository.save(job);

            log.info("▶️ Starting batch job {}", jobId);

            // Calculate periods
            SlaDefinition slaDefinition = slaDefinitionRepository.findById(job.getSlaDefinitionId())
                    .orElseThrow(() -> new ResourceNotFoundException("SLA not found"));

            List<LocalDate> periods = calculatePeriods(
                    job.getPeriodStart(),
                    job.getPeriodEnd(),
                    slaDefinition.getPeriodType()
            );

            // Process each period
            for (LocalDate periodDate : periods) {
                // Check if cancelled
                SlaBatchJob currentJob = batchJobRepository.findById(jobId).orElseThrow();
                if (currentJob.getStatus() == BatchJobStatus.CANCELLED) {
                    log.info("⏹️ Batch job {} cancelled", jobId);
                    return;
                }

                try {
                    SlaResult result = slaComputationService.computeSla(
                            job.getSlaDefinitionId(),
                            periodDate,
                            job.getForceRecompute(),
                            job.getCreatedBy()
                    );

                    boolean wasCreated = result.getCreatedBy().equals(job.getCreatedBy());
                    if (wasCreated) {
                        job.incrementProgress(true);
                    } else {
                        job.skip();
                    }

                } catch (Exception e) {
                    log.error("Failed to compute period {}: {}", periodDate, e.getMessage());
                    job.incrementProgress(false);
                }

                // Save progress every 10 items
                if (job.getProcessedItems() % 10 == 0) {
                    batchJobRepository.save(job);
                    log.info("Progress: {}/{} ({}%)",
                            job.getProcessedItems(),
                            job.getTotalItems(),
                            job.getProgressPercent());
                }
            }

            // Complete
            job.complete();
            batchJobRepository.save(job);

            log.info("✅ Batch job {} completed: {} success, {} failed, {} skipped",
                    jobId, job.getSuccessCount(), job.getFailureCount(), job.getSkippedCount());

        } catch (Exception e) {
            log.error("❌ Batch job {} failed: {}", jobId, e.getMessage(), e);

            job.fail(e.getMessage());
            batchJobRepository.save(job);
        }
    }

    /**
     * Get job status.
     */
    @Transactional(readOnly = true)
    public SlaBatchJob getJobStatus(UUID jobId) {
        return batchJobRepository.findById(jobId)
                .orElseThrow(() -> new ResourceNotFoundException("Job not found: " + jobId));
    }

    /**
     * Cancel running job.
     */
    @Transactional
    public void cancelJob(UUID jobId, String cancelledBy) {
        SlaBatchJob job = batchJobRepository.findById(jobId)
                .orElseThrow(() -> new ResourceNotFoundException("Job not found: " + jobId));

        if (!job.isCancellable()) {
            throw new IllegalStateException(
                    "Job cannot be cancelled in status: " + job.getStatus()
            );
        }

        job.cancel(cancelledBy);
        batchJobRepository.save(job);

        log.info("🛑 Batch job {} cancelled by {}", jobId, cancelledBy);
    }
}
```

**3. API Controller:**

```java
@RestController
@RequestMapping("/api/sla/batch")
@RequiredArgsConstructor
@Slf4j
public class SlaBatchJobController {

    private final SlaBatchJobService batchJobService;

    /**
     * Create batch recomputation job.
     * Returns immediately with job ID.
     *
     * POST /api/sla/batch/recompute
     */
    @PostMapping("/recompute")
    public ResponseEntity<SlaBatchJobDto> createRecomputationJob(
            @RequestBody @Valid SlaComputationRequestDTO request) {

        log.info("Creating batch recomputation job for SLA: {}", request.getSlaDefinitionId());

        SlaBatchJob job = batchJobService.createRecomputationJob(request);

        SlaBatchJobDto dto = batchJobMapper.toDto(job);

        return ResponseEntity.status(HttpStatus.ACCEPTED).body(dto);
    }

    /**
     * Get job status.
     * Poll this endpoint to track progress.
     *
     * GET /api/sla/batch/{jobId}
     */
    @GetMapping("/{jobId}")
    public ResponseEntity<SlaBatchJobDto> getJobStatus(@PathVariable UUID jobId) {
        SlaBatchJob job = batchJobService.getJobStatus(jobId);

        SlaBatchJobDto dto = batchJobMapper.toDto(job);

        return ResponseEntity.ok(dto);
    }

    /**
     * Cancel running job.
     *
     * POST /api/sla/batch/{jobId}/cancel
     */
    @PostMapping("/{jobId}/cancel")
    public ResponseEntity<Void> cancelJob(
            @PathVariable UUID jobId,
            @RequestParam String cancelledBy) {

        batchJobService.cancelJob(jobId, cancelledBy);

        return ResponseEntity.noContent().build();
    }

    /**
     * List all batch jobs with filters.
     *
     * GET /api/sla/batch?status=RUNNING&slaDefinitionId=...
     */
    @GetMapping
    public ResponseEntity<List<SlaBatchJobDto>> listJobs(
            @RequestParam(required = false) BatchJobStatus status,
            @RequestParam(required = false) UUID slaDefinitionId) {

        List<SlaBatchJob> jobs = batchJobService.listJobs(status, slaDefinitionId);

        List<SlaBatchJobDto> dtos = jobs.stream()
                .map(batchJobMapper::toDto)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }
}
```

### Example Usage

**Create Job:**
```bash
POST /api/sla/batch/recompute
{
  "slaDefinitionId": "abc-123",
  "periodStart": "2025-01-01",
  "periodEnd": "2025-06-30",
  "forceRecompute": true,
  "triggeredBy": "john.doe"
}

Response (202 Accepted):
{
  "jobId": "job-456",
  "status": "PENDING",
  "totalItems": 181,
  "createdAt": "2025-11-13T10:00:00",
  "message": "Job queued for execution"
}
```

**Poll Status:**
```bash
GET /api/sla/batch/job-456

Response:
{
  "jobId": "job-456",
  "status": "RUNNING",
  "totalItems": 181,
  "processedItems": 87,
  "successCount": 85,
  "failureCount": 0,
  "skippedCount": 2,
  "progressPercent": 48.07,
  "startedAt": "2025-11-13T10:00:05",
  "estimatedTimeRemaining": "00:03:24"
}
```

**Cancel Job:**
```bash
POST /api/sla/batch/job-456/cancel?cancelledBy=admin

Response: 204 No Content
```

### Prednosti ✅

1. **Async execution**: Ne blokira HTTP request
2. **Progress tracking**: Real-time progress updates
3. **Cancellation support**: Može da se prekine execution
4. **Large ranges**: Može da handleuje hundreds of periods
5. **Audit trail**: Kompletan history batch jobs
6. **Recovery**: Restart failed jobs

### Mane ⚠️

1. **More complex**: Zahteva dodatnu tabelu i async logic
2. **Polling required**: Frontend mora da poll-uje status
3. **Resource usage**: Long-running jobs koriste thread pool

### Kada koristiti

- **Production system**: Pravi production-ready solution
- **Large ranges**: Recomputation 100+ perioda
- **Background processing**: Long-running operacije
- **Multiple users**: Concurrent batch jobs

---

## 📊 Poređenje Pristupa

| Feature | Pristup 1 (Enhanced Sync) | Pristup 2 (Async Batch) |
|---------|--------------------------|-------------------------|
| **Implementation Time** | 3-4h | 8-12h |
| **Complexity** | ⭐ Low | ⭐⭐⭐ High |
| **Execution Mode** | ❌ Synchronous | ✅ Asynchronous |
| **Progress Tracking** | ❌ No | ✅ Yes |
| **Cancellation** | ❌ No | ✅ Yes |
| **Dry-run** | ✅ Yes | ⭐ Can add |
| **Large Ranges** | ⚠️ Limited (<50) | ✅ Unlimited |
| **Timeout Risk** | ⚠️ High | ✅ None |
| **User Experience** | ⭐ Blocking | ⭐⭐⭐ Non-blocking |
| **Audit Trail** | ⭐ Basic | ⭐⭐⭐ Complete |

---

## 🎯 Finalna Preporuka

### Kombinovani Pristup: **Oba Pristupa** ✅

**Razlog:**
- **Pristup 1** za quick/small recomputations (< 30 perioda)
- **Pristup 2** za large batch operations (> 30 perioda)

**Implementation Strategy:**

**Faza 1**: Enhanced Sync (Quick Win)
- [ ] Implementirati dry-run mode
- [ ] Dodati range support
- [ ] Enhanced validation i warnings
- [ ] Detailed response DTO

**Faza 2**: Async Batch (Long-term)
- [ ] Kreirati `SlaBatchJob` entity
- [ ] Implementirati batch job service
- [ ] Async execution sa progress tracking
- [ ] Cancellation support
- [ ] API endpoints

**Decision Logic u Controller:**
```java
@PostMapping("/trigger")
public ResponseEntity<?> triggerRecomputation(@RequestBody SlaComputationRequestDTO request) {
    int periodCount = calculatePeriodCount(request);

    if (periodCount <= 30) {
        // Use synchronous for small batches
        SlaComputationResponseDTO response = slaComputationService.computeSlaEnhanced(request);
        return ResponseEntity.ok(response);
    } else {
        // Use async batch for large batches
        SlaBatchJob job = batchJobService.createRecomputationJob(request);
        return ResponseEntity.accepted().body(batchJobMapper.toDto(job));
    }
}
```

---

## 🧪 Testing Strategy

### Unit Tests

```java
@Test
void testDryRunMode() {
    SlaComputationRequestDTO request = SlaComputationRequestDTO.builder()
        .slaDefinitionId(slaId)
        .periodStart(LocalDate.of(2025, 10, 1))
        .periodEnd(LocalDate.of(2025, 10, 31))
        .dryRun(true)
        .build();

    SlaComputationResponseDTO response = service.computeSlaEnhanced(request);

    assertThat(response.getWasDryRun()).isTrue();
    assertThat(response.getStatistics().getTotalPeriods()).isEqualTo(31);
    verify(slaResultRepository, never()).save(any());
}

@Test
void testBatchJobProgressTracking() {
    SlaBatchJob job = createTestJob();

    job.incrementProgress(true);
    assertThat(job.getProcessedItems()).isEqualTo(1);
    assertThat(job.getSuccessCount()).isEqualTo(1);
    assertThat(job.getProgressPercent()).isGreaterThan(BigDecimal.ZERO);
}
```

---

## 📚 References

- [Async Processing with Spring](https://spring.io/guides/gs/async-method/)
- [Long-Running Operations Best Practices](https://restfulapi.net/rest-api-long-running-operations/)
- [Progress Tracking Patterns](https://martinfowler.com/articles/patterns-of-distributed-systems/request-pipeline.html)
