# Scheduled SLA Reports Analysis - Automated Report Generation & Storage

## 📋 Problem Statement

### Trenutna Situacija

SLA sistem trenutno ima:

**✅ Šta POSTOJI:**
1. **SLA Computation** - Schedulers u `oci-monitor` računaju SLA metrike (daily/weekly/monthly)
2. **SLA Results Storage** - `sla_result` tabela čuva izračunate compliance metrike
3. **On-Demand Report Generation** - `SlaReportService` generiše reporte na zahtev iz postojećih rezultata
4. **Report Export** - Eksport u CSV i PDF formatima

**❌ Šta NEDOSTAJE:**
1. **Scheduled Report Generation** - Automatsko generisanje reportova (nedeljno/mesečno)
2. **Report Storage** - Čuvanje pre-generisanih reportova u bazi
3. **Report Schedule CRUD** - API za upravljanje scheduled reports
4. **Report History** - Pristup istorijskim reportovima bez re-generisanja
5. **Report Notifications** - Automatsko slanje reporta emailom
6. **Report Archiving** - Arhiviranje starih reportova

### 🎯 Biznis Zahtevi

1. **Automatizacija**: Reporti se automatski generišu nedeljno/mesečno
2. **Istorija**: Mogućnost pristupa istorijskim reportovima
3. **Notifikacije**: Stakeholderi dobijaju report emailom
4. **Performance**: Brz pristup reportovima (bez re-generisanja)
5. **Konfigurabilnost**: Fleksibilna konfiguracija report schedule-a
6. **Audit Trail**: Kompletna istorija generisanih reportova

### 📊 Use Cases

**UC1: Compliance Manager**
> "Želim da svakog ponedeljka ujutro automatski dobijem weekly compliance report za production SLA."

**UC2: Operations Team**
> "Treba mi pristup prošlomesečnom reportu da uporedim sa trenutnim mesecom."

**UC3: Executive Dashboard**
> "Dashbordu trebaju monthly SLA summaries za sve kritične servise bez kašnjenja."

**UC4: Audit Requirements**
> "Moram da arhiviram sve compliance reportove za regulatorne potrebe (GDPR, SOX)."

---

## 🔧 Pristup 1: Pre-Generated Reports sa Scheduler Storage ⭐⭐⭐⭐⭐

### Koncept

Scheduler u `oci-monitor` periodično generiše kompletne reportove i čuva ih u `sla_report` tabeli sa kompletnim summary i breach informacijama.

### Arhitektura

```
┌─────────────────────────────────────────────────────────┐
│  OCI-MONITOR (Schedulers)                               │
└─────────────────────────────────────────────────────────┘
    │
    │  SlaReportScheduler (weekly: MON 01:00, monthly: 1st 02:00)
    ├──> Load SlaReportSchedule configurations
    ├──> For each active schedule:
    │    ├──> Generate report (SlaReportGenerationService)
    │    ├──> Store in sla_report table
    │    ├──> Send email notifications (if configured)
    │    └──> Update schedule last_run timestamp
    │
    ▼
┌────────────────────────────────────────────────────────┐
│  DATABASE                                              │
│  - sla_report_schedule (CRUD via oci-api)             │
│  - sla_report (generated reports storage)             │
│  - sla_report_breach_summary (breach details)         │
└────────────────────────────────────────────────────────┘
    │
    │  User requests report
    ▼
┌─────────────────────────────────────────────────────────┐
│  OCI-API (REST Endpoints)                               │
│  - GET /api/sla/reports/scheduled/{reportId}            │
│  - GET /api/sla/reports/scheduled?slaId=...&period=...  │
│  - POST/PUT/DELETE /api/sla/report-schedules            │
└─────────────────────────────────────────────────────────┘
```

### Data Model

**1. SlaReportSchedule Entity:**

```java
@Entity
@Table(name = "sla_report_schedule", indexes = {
    @Index(name = "idx_schedule_sla_id", columnList = "sla_definition_id"),
    @Index(name = "idx_schedule_active", columnList = "is_active"),
    @Index(name = "idx_schedule_next_run", columnList = "next_run_at")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SlaReportSchedule {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @UuidGenerator
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "id", updatable = false, nullable = false, columnDefinition = "char(36)")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sla_definition_id", nullable = false)
    private SlaDefinition slaDefinition;

    @Column(name = "schedule_name", nullable = false, length = 255)
    private String scheduleName;

    @Column(name = "schedule_description", length = 1000)
    private String scheduleDescription;

    @Column(name = "period_type", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private SlaPeriodType periodType; // WEEKLY, MONTHLY, QUARTERLY

    @Column(name = "schedule_frequency", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private ScheduleFrequency frequency; // WEEKLY, MONTHLY, QUARTERLY

    /**
     * Cron expression for custom scheduling.
     * Examples:
     * - "0 0 1 * * MON" - Every Monday at 01:00
     * - "0 0 2 1 * *"   - First day of month at 02:00
     */
    @Column(name = "cron_expression", length = 100)
    private String cronExpression;

    @Column(name = "timezone", nullable = false, length = 50)
    private String timezone; // Inherit from SLA or override

    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;

    @Column(name = "email_recipients", length = 2000)
    private String emailRecipients; // Comma-separated emails

    @Column(name = "include_pdf_attachment", nullable = false)
    private Boolean includePdfAttachment = true;

    @Column(name = "include_csv_attachment", nullable = false)
    private Boolean includeCsvAttachment = false;

    @Column(name = "auto_archive_after_days")
    private Integer autoArchiveAfterDays; // NULL = never archive

    @Column(name = "last_run_at")
    private LocalDateTime lastRunAt;

    @Column(name = "next_run_at")
    private LocalDateTime nextRunAt;

    @Column(name = "last_report_id")
    @JdbcTypeCode(SqlTypes.CHAR)
    private UUID lastReportId;

    @Column(name = "total_reports_generated")
    private Long totalReportsGenerated = 0L;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "created_by", nullable = false, length = 255)
    private String createdBy;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "updated_by", length = 255)
    private String updatedBy;
}

public enum ScheduleFrequency {
    WEEKLY,    // Every Monday (or configurable day)
    MONTHLY,   // First day of month
    QUARTERLY, // First day of quarter
    CUSTOM     // Use cron expression
}
```

**2. SlaReport Entity (Stored Reports):**

```java
@Entity
@Table(name = "sla_report", indexes = {
    @Index(name = "idx_report_sla_id", columnList = "sla_definition_id"),
    @Index(name = "idx_report_schedule_id", columnList = "report_schedule_id"),
    @Index(name = "idx_report_period", columnList = "period_start_utc, period_end_utc"),
    @Index(name = "idx_report_generated", columnList = "generated_at"),
    @Index(name = "idx_report_status", columnList = "report_status")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SlaReport {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @UuidGenerator
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "id", updatable = false, nullable = false, columnDefinition = "char(36)")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sla_definition_id", nullable = false)
    private SlaDefinition slaDefinition;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "report_schedule_id")
    private SlaReportSchedule reportSchedule; // NULL if manually generated

    @Column(name = "report_name", nullable = false, length = 255)
    private String reportName; // "Production API - Weekly Report - 2025-W45"

    @Column(name = "period_type", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private SlaPeriodType periodType;

    @Column(name = "period_start_utc", nullable = false)
    private LocalDateTime periodStartUtc;

    @Column(name = "period_end_utc", nullable = false)
    private LocalDateTime periodEndUtc;

    @Column(name = "period_start_local", nullable = false)
    private LocalDateTime periodStartLocal; // In SLA timezone

    @Column(name = "period_end_local", nullable = false)
    private LocalDateTime periodEndLocal; // In SLA timezone

    // ===== COMPLIANCE SUMMARY =====

    @Column(name = "compliance_percent", precision = 5, scale = 2)
    private BigDecimal compliancePercent; // 99.95

    @Column(name = "compliance_status", length = 20)
    @Enumerated(EnumType.STRING)
    private SlaStatus complianceStatus; // FULFILLED, BREACHED, WARNING

    @Column(name = "target_percent", precision = 5, scale = 2)
    private BigDecimal targetPercent; // 99.50

    @Column(name = "deviation_percent", precision = 5, scale = 2)
    private BigDecimal deviationPercent; // +0.45 or -2.30

    @Column(name = "total_minutes_in_period")
    private Long totalMinutesInPeriod; // 10080 for weekly

    @Column(name = "uptime_minutes")
    private Long uptimeMinutes; // 10072

    @Column(name = "downtime_minutes")
    private Long downtimeMinutes; // 8

    @Column(name = "excluded_downtime_minutes")
    private Long excludedDowntimeMinutes; // Planned maintenance

    // ===== BREACH SUMMARY =====

    @Column(name = "total_breaches")
    private Integer totalBreaches; // 3

    @Column(name = "critical_breaches")
    private Integer criticalBreaches; // 1

    @Column(name = "high_breaches")
    private Integer highBreaches; // 1

    @Column(name = "medium_breaches")
    private Integer mediumBreaches; // 1

    @Column(name = "low_breaches")
    private Integer lowBreaches; // 0

    @Column(name = "total_breach_duration_minutes")
    private Long totalBreachDurationMinutes; // Sum of all breach durations

    @Column(name = "longest_breach_duration_minutes")
    private Long longestBreachDurationMinutes; // Longest single breach

    @Column(name = "mttr_minutes") // Mean Time To Resolution
    private Long mttrMinutes;

    @Column(name = "has_breaches", nullable = false)
    private Boolean hasBreaches; // Quick filter flag

    // ===== AVAILABILITY METRICS =====

    @Column(name = "availability_percent", precision = 5, scale = 2)
    private BigDecimal availabilityPercent; // 99.92

    @Column(name = "data_coverage_percent", precision = 5, scale = 2)
    private BigDecimal dataCoveragePercent; // 98.50 (how much data available)

    @Column(name = "total_data_points")
    private Long totalDataPoints;

    @Column(name = "missing_data_points")
    private Long missingDataPoints;

    // ===== METADATA =====

    @Column(name = "report_status", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private ReportStatus reportStatus; // DRAFT, PUBLISHED, ARCHIVED

    @Column(name = "report_format", length = 20)
    @Enumerated(EnumType.STRING)
    private ReportFormat reportFormat; // JSON, PDF, CSV

    @Column(name = "report_size_bytes")
    private Long reportSizeBytes; // For stored files

    @Column(name = "report_file_path", length = 500)
    private String reportFilePath; // Optional: S3/filesystem path for PDF/CSV

    @Column(name = "generation_duration_ms")
    private Long generationDurationMs; // Performance tracking

    @Column(name = "generated_at", nullable = false)
    private LocalDateTime generatedAt;

    @Column(name = "generated_by", nullable = false, length = 255)
    private String generatedBy; // "scheduler" or user email

    @Column(name = "notification_sent", nullable = false)
    private Boolean notificationSent = false;

    @Column(name = "notification_sent_at")
    private LocalDateTime notificationSentAt;

    @Column(name = "notification_recipients", length = 2000)
    private String notificationRecipients; // Who received notification

    @Column(name = "archived_at")
    private LocalDateTime archivedAt;

    @Column(name = "archived_by", length = 255)
    private String archivedBy;

    // ===== RELATIONSHIPS =====

    @OneToMany(mappedBy = "slaReport", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<SlaReportBreachSummary> breachSummaries = new ArrayList<>();

    // Business logic methods
    public boolean isArchived() {
        return reportStatus == ReportStatus.ARCHIVED;
    }

    public boolean shouldArchive(Integer archiveAfterDays) {
        if (archiveAfterDays == null || isArchived()) {
            return false;
        }
        LocalDateTime archiveThreshold = LocalDateTime.now().minusDays(archiveAfterDays);
        return generatedAt.isBefore(archiveThreshold);
    }
}

public enum ReportStatus {
    DRAFT,      // Being generated
    PUBLISHED,  // Available for viewing
    ARCHIVED    // Moved to archive (read-only)
}

public enum ReportFormat {
    JSON,   // Stored as JSON in database
    PDF,    // PDF file in storage
    CSV,    // CSV file in storage
    HYBRID  // JSON + PDF/CSV files
}
```

**3. SlaReportBreachSummary Entity (Breach Details in Report):**

```java
@Entity
@Table(name = "sla_report_breach_summary", indexes = {
    @Index(name = "idx_breach_summary_report", columnList = "sla_report_id"),
    @Index(name = "idx_breach_summary_breach", columnList = "sla_breach_id")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SlaReportBreachSummary {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @UuidGenerator
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "id", updatable = false, nullable = false, columnDefinition = "char(36)")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sla_report_id", nullable = false)
    private SlaReport slaReport;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sla_breach_id", nullable = false)
    private SlaBreach slaBreach; // Reference to original breach

    @Column(name = "breach_detected_at", nullable = false)
    private LocalDateTime breachDetectedAt;

    @Column(name = "breach_severity", nullable = false, length = 20)
    private String breachSeverity; // CRITICAL, HIGH, MEDIUM, LOW

    @Column(name = "breach_duration_minutes")
    private Long breachDurationMinutes;

    @Column(name = "actual_value", precision = 5, scale = 2)
    private BigDecimal actualValue; // 88.50%

    @Column(name = "threshold_value", precision = 5, scale = 2)
    private BigDecimal thresholdValue; // 95.00%

    @Column(name = "deviation_percent", precision = 5, scale = 2)
    private BigDecimal deviationPercent; // 6.50%

    @Column(name = "breach_description", length = 2000)
    private String breachDescription;

    @Column(name = "is_resolved", nullable = false)
    private Boolean isResolved;

    @Column(name = "resolved_at")
    private LocalDateTime resolvedAt;
}
```

### Implementation - Scheduler

**SlaReportScheduler (oci-monitor):**

```java
@Slf4j
@Component
@RequiredArgsConstructor
public class SlaReportScheduler {

    private final SlaReportScheduleRepository scheduleRepository;
    private final SlaReportGenerationService reportGenerationService;
    private final SchedulerToggleService schedulerToggleService;

    /**
     * Process weekly SLA report schedules.
     * Runs every Monday at 01:00 AM.
     */
    @Scheduled(cron = "0 0 1 * * MON")
    @SchedulerLock(
        name = "weekly-sla-report-scheduler",
        lockAtMostFor = "PT30M",
        lockAtLeastFor = "PT2M"
    )
    public void generateWeeklyReports() {
        if (!schedulerToggleService.isTaskEnabled("sla.report.scheduled.weekly")) {
            log.info("SlaReportScheduler:: Weekly report scheduler is disabled. Skipping.");
            return;
        }

        log.info("=== WEEKLY SLA Report Scheduler Started ===");

        LocalDateTime now = LocalDateTime.now();
        processSchedules(ScheduleFrequency.WEEKLY, now);

        log.info("=== WEEKLY SLA Report Scheduler Completed ===");
    }

    /**
     * Process monthly SLA report schedules.
     * Runs on the 1st day of every month at 02:00 AM.
     */
    @Scheduled(cron = "0 0 2 1 * *")
    @SchedulerLock(
        name = "monthly-sla-report-scheduler",
        lockAtMostFor = "PT60M",
        lockAtLeastFor = "PT5M"
    )
    public void generateMonthlyReports() {
        if (!schedulerToggleService.isTaskEnabled("sla.report.scheduled.monthly")) {
            log.info("SlaReportScheduler:: Monthly report scheduler is disabled. Skipping.");
            return;
        }

        log.info("=== MONTHLY SLA Report Scheduler Started ===");

        LocalDateTime now = LocalDateTime.now();
        processSchedules(ScheduleFrequency.MONTHLY, now);

        log.info("=== MONTHLY SLA Report Scheduler Completed ===");
    }

    /**
     * Process report schedules for given frequency.
     */
    private void processSchedules(ScheduleFrequency frequency, LocalDateTime now) {
        // Find all active schedules for this frequency that are due
        List<SlaReportSchedule> schedules = scheduleRepository
                .findActiveSchedulesDueForExecution(frequency, now);

        if (schedules.isEmpty()) {
            log.info("No active {} report schedules found", frequency);
            return;
        }

        log.info("Found {} active {} report schedules to process", schedules.size(), frequency);

        int successCount = 0;
        int failureCount = 0;

        for (SlaReportSchedule schedule : schedules) {
            try {
                log.info("Processing schedule: {} ({})",
                         schedule.getScheduleName(), schedule.getId());

                // Generate and store report
                SlaReport generatedReport = reportGenerationService.generateScheduledReport(schedule);

                // Update schedule
                schedule.setLastRunAt(now);
                schedule.setNextRunAt(calculateNextRun(schedule, now));
                schedule.setLastReportId(generatedReport.getId());
                schedule.setTotalReportsGenerated(schedule.getTotalReportsGenerated() + 1);
                scheduleRepository.save(schedule);

                successCount++;
                log.info("✅ Report generated successfully: {}", generatedReport.getId());

            } catch (Exception e) {
                failureCount++;
                log.error("❌ Failed to generate report for schedule {}: {}",
                          schedule.getId(), e.getMessage(), e);
            }
        }

        log.info("Report generation summary: {} success, {} failed", successCount, failureCount);
    }

    /**
     * Calculate next run time based on frequency.
     */
    private LocalDateTime calculateNextRun(SlaReportSchedule schedule, LocalDateTime current) {
        return switch (schedule.getFrequency()) {
            case WEEKLY -> current.plusWeeks(1);
            case MONTHLY -> current.plusMonths(1);
            case QUARTERLY -> current.plusMonths(3);
            case CUSTOM -> {
                // Parse cron and calculate next execution
                // Implementation depends on cron library
                yield current.plusWeeks(1); // Fallback
            }
        };
    }
}
```

**SlaReportGenerationService (oci-monitor):**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class SlaReportGenerationService {

    private final SlaReportRepository slaReportRepository;
    private final SlaDefinitionRepository slaDefinitionRepository;
    private final SlaResultRepository slaResultRepository;
    private final SlaBreachRepository slaBreachRepository;
    private final SlaNotificationService notificationService;
    private final PeriodCalculator periodCalculator;

    /**
     * Generate scheduled report and store in database.
     */
    @Transactional
    public SlaReport generateScheduledReport(SlaReportSchedule schedule) {
        long startTime = System.currentTimeMillis();

        SlaDefinition slaDefinition = schedule.getSlaDefinition();

        log.info("Generating {} report for SLA: {}",
                 schedule.getPeriodType(), slaDefinition.getName());

        // 1. Calculate period range
        LocalDate periodStart = calculatePeriodStart(schedule);
        PeriodRange periodRange = periodCalculator.calculateRange(
                slaDefinition,
                schedule.getPeriodType(),
                periodStart
        );

        // 2. Check if report already exists
        Optional<SlaReport> existingReport = slaReportRepository
                .findByDefinitionAndPeriod(
                        slaDefinition.getId(),
                        periodRange.getPeriodStartUtc(),
                        periodRange.getPeriodEndUtc()
                );

        if (existingReport.isPresent()) {
            log.warn("Report already exists for this period, skipping: {}",
                     existingReport.get().getId());
            return existingReport.get();
        }

        // 3. Fetch SLA results for period
        List<SlaResult> results = slaResultRepository.findAllByDefinitionAndPeriodRange(
                slaDefinition.getId(),
                periodRange.getPeriodStartUtc(),
                periodRange.getPeriodEndUtc()
        );

        // 4. Fetch breaches for period
        List<SlaBreach> breaches = slaBreachRepository.findAllByDefinitionAndPeriodRange(
                slaDefinition.getId(),
                periodRange.getPeriodStartUtc(),
                periodRange.getPeriodEndUtc()
        );

        // 5. Calculate aggregated metrics
        ReportMetrics metrics = calculateReportMetrics(results, breaches, periodRange);

        // 6. Build report entity
        String reportName = generateReportName(slaDefinition, schedule, periodStart);

        SlaReport report = SlaReport.builder()
                .slaDefinition(slaDefinition)
                .reportSchedule(schedule)
                .reportName(reportName)
                .periodType(schedule.getPeriodType())
                .periodStartUtc(periodRange.getPeriodStartUtc())
                .periodEndUtc(periodRange.getPeriodEndUtc())
                .periodStartLocal(periodRange.getPeriodStartLocal())
                .periodEndLocal(periodRange.getPeriodEndLocal())
                // Compliance metrics
                .compliancePercent(metrics.compliancePercent())
                .complianceStatus(metrics.complianceStatus())
                .targetPercent(slaDefinition.getTargetValue())
                .deviationPercent(metrics.deviationPercent())
                .totalMinutesInPeriod(metrics.totalMinutes())
                .uptimeMinutes(metrics.uptimeMinutes())
                .downtimeMinutes(metrics.downtimeMinutes())
                .excludedDowntimeMinutes(metrics.excludedDowntimeMinutes())
                // Breach metrics
                .totalBreaches(breaches.size())
                .criticalBreaches(metrics.criticalBreaches())
                .highBreaches(metrics.highBreaches())
                .mediumBreaches(metrics.mediumBreaches())
                .lowBreaches(metrics.lowBreaches())
                .totalBreachDurationMinutes(metrics.totalBreachDuration())
                .longestBreachDurationMinutes(metrics.longestBreachDuration())
                .mttrMinutes(metrics.mttrMinutes())
                .hasBreaches(!breaches.isEmpty())
                // Availability metrics
                .availabilityPercent(metrics.availabilityPercent())
                .dataCoveragePercent(metrics.dataCoveragePercent())
                .totalDataPoints(metrics.totalDataPoints())
                .missingDataPoints(metrics.missingDataPoints())
                // Metadata
                .reportStatus(ReportStatus.PUBLISHED)
                .reportFormat(ReportFormat.JSON)
                .generationDurationMs(System.currentTimeMillis() - startTime)
                .generatedAt(LocalDateTime.now())
                .generatedBy("scheduler")
                .notificationSent(false)
                .build();

        // 7. Add breach summaries
        for (SlaBreach breach : breaches) {
            SlaReportBreachSummary breachSummary = SlaReportBreachSummary.builder()
                    .slaReport(report)
                    .slaBreach(breach)
                    .breachDetectedAt(breach.getDetectedAt())
                    .breachSeverity(breach.getSeverity())
                    .breachDurationMinutes(breach.getBreachDurationMinutes())
                    .actualValue(breach.getActualValue())
                    .thresholdValue(breach.getThresholdValue())
                    .deviationPercent(breach.getDeviationPercent())
                    .breachDescription(breach.getDescription())
                    .isResolved(breach.getIsResolved())
                    .resolvedAt(breach.getResolvedAt())
                    .build();
            report.getBreachSummaries().add(breachSummary);
        }

        // 8. Save report
        SlaReport savedReport = slaReportRepository.save(report);

        log.info("✅ Report saved: {} - Compliance: {}% - Breaches: {}",
                 savedReport.getId(),
                 savedReport.getCompliancePercent(),
                 savedReport.getTotalBreaches());

        // 9. Send notifications (async)
        if (schedule.getEmailRecipients() != null && !schedule.getEmailRecipients().isEmpty()) {
            sendReportNotifications(savedReport, schedule);
        }

        return savedReport;
    }

    /**
     * Calculate aggregated report metrics.
     */
    private ReportMetrics calculateReportMetrics(
            List<SlaResult> results,
            List<SlaBreach> breaches,
            PeriodRange periodRange) {

        // Calculate average compliance
        BigDecimal avgCompliance = results.stream()
                .map(SlaResult::getCompliancePercent)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .divide(BigDecimal.valueOf(results.size()), 2, RoundingMode.HALF_UP);

        // Calculate breach severity distribution
        long critical = breaches.stream().filter(b -> "CRITICAL".equals(b.getSeverity())).count();
        long high = breaches.stream().filter(b -> "HIGH".equals(b.getSeverity())).count();
        long medium = breaches.stream().filter(b -> "MEDIUM".equals(b.getSeverity())).count();
        long low = breaches.stream().filter(b -> "LOW".equals(b.getSeverity())).count();

        // Calculate breach durations
        long totalBreachDuration = breaches.stream()
                .mapToLong(b -> b.getBreachDurationMinutes() != null ? b.getBreachDurationMinutes() : 0)
                .sum();

        long longestBreach = breaches.stream()
                .mapToLong(b -> b.getBreachDurationMinutes() != null ? b.getBreachDurationMinutes() : 0)
                .max()
                .orElse(0);

        // Calculate MTTR (Mean Time To Resolution)
        long resolvedBreaches = breaches.stream().filter(SlaBreach::getIsResolved).count();
        long mttr = resolvedBreaches > 0 ? totalBreachDuration / resolvedBreaches : 0;

        // More calculations...

        return new ReportMetrics(
                avgCompliance,
                determineSlaStatus(avgCompliance),
                BigDecimal.ZERO, // deviation
                10080L, // total minutes
                10000L, // uptime
                80L,    // downtime
                0L,     // excluded
                (int) critical,
                (int) high,
                (int) medium,
                (int) low,
                totalBreachDuration,
                longestBreach,
                mttr,
                avgCompliance, // availability
                BigDecimal.valueOf(98.5), // data coverage
                1000L, // total data points
                15L    // missing data points
        );
    }

    /**
     * Generate human-readable report name.
     */
    private String generateReportName(
            SlaDefinition definition,
            SlaReportSchedule schedule,
            LocalDate periodStart) {

        String periodLabel = switch (schedule.getPeriodType()) {
            case WEEKLY -> String.format("Week %d", periodStart.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR));
            case MONTHLY -> periodStart.format(DateTimeFormatter.ofPattern("MMMM yyyy"));
            case QUARTERLY -> String.format("Q%d %d",
                    (periodStart.getMonthValue() - 1) / 3 + 1,
                    periodStart.getYear());
            default -> periodStart.toString();
        };

        return String.format("%s - %s Report - %s",
                definition.getName(),
                schedule.getPeriodType(),
                periodLabel);
    }

    /**
     * Send report notifications via email.
     */
    private void sendReportNotifications(SlaReport report, SlaReportSchedule schedule) {
        try {
            log.info("Sending report notifications to: {}", schedule.getEmailRecipients());

            boolean sent = notificationService.sendReportNotification(
                    report,
                    schedule.getEmailRecipients(),
                    schedule.getIncludePdfAttachment(),
                    schedule.getIncludeCsvAttachment()
            );

            if (sent) {
                report.setNotificationSent(true);
                report.setNotificationSentAt(LocalDateTime.now());
                report.setNotificationRecipients(schedule.getEmailRecipients());
                slaReportRepository.save(report);
            }

        } catch (Exception e) {
            log.error("Failed to send report notifications: {}", e.getMessage(), e);
        }
    }

    /**
     * Calculate period start based on schedule frequency.
     */
    private LocalDate calculatePeriodStart(SlaReportSchedule schedule) {
        LocalDate now = LocalDate.now();

        return switch (schedule.getFrequency()) {
            case WEEKLY -> now.minusWeeks(1).with(DayOfWeek.MONDAY);
            case MONTHLY -> now.minusMonths(1).withDayOfMonth(1);
            case QUARTERLY -> {
                int currentQuarter = (now.getMonthValue() - 1) / 3;
                int prevQuarter = currentQuarter - 1;
                if (prevQuarter < 0) {
                    prevQuarter = 3;
                }
                Month startMonth = Month.of(prevQuarter * 3 + 1);
                yield LocalDate.of(now.getYear(), startMonth, 1);
            }
            case CUSTOM -> now.minusWeeks(1); // Fallback
        };
    }

    private SlaStatus determineSlaStatus(BigDecimal compliance) {
        if (compliance.compareTo(BigDecimal.valueOf(95)) >= 0) {
            return SlaStatus.FULFILLED;
        } else if (compliance.compareTo(BigDecimal.valueOf(90)) >= 0) {
            return SlaStatus.WARNING;
        } else {
            return SlaStatus.BREACHED;
        }
    }

    /**
     * Internal record for report metrics.
     */
    private record ReportMetrics(
            BigDecimal compliancePercent,
            SlaStatus complianceStatus,
            BigDecimal deviationPercent,
            Long totalMinutes,
            Long uptimeMinutes,
            Long downtimeMinutes,
            Long excludedDowntimeMinutes,
            Integer criticalBreaches,
            Integer highBreaches,
            Integer mediumBreaches,
            Integer lowBreaches,
            Long totalBreachDuration,
            Long longestBreachDuration,
            Long mttrMinutes,
            BigDecimal availabilityPercent,
            BigDecimal dataCoveragePercent,
            Long totalDataPoints,
            Long missingDataPoints
    ) {}
}
```

### Implementation - CRUD API (oci-api)

**SlaReportScheduleController:**

```java
@RestController
@RequestMapping("/api/sla/report-schedules")
@RequiredArgsConstructor
@Slf4j
public class SlaReportScheduleController {

    private final SlaReportScheduleService scheduleService;
    private final SlaReportScheduleMapper scheduleMapper;

    /**
     * List all report schedules with filters.
     * GET /api/sla/report-schedules?slaDefinitionId=...&isActive=true
     */
    @GetMapping
    public ResponseEntity<List<SlaReportScheduleDto>> listSchedules(
            @RequestParam(required = false) UUID slaDefinitionId,
            @RequestParam(required = false) Boolean isActive,
            @RequestParam(required = false) ScheduleFrequency frequency) {

        List<SlaReportSchedule> schedules = scheduleService.listSchedules(
                slaDefinitionId, isActive, frequency);

        List<SlaReportScheduleDto> dtos = schedules.stream()
                .map(scheduleMapper::toDto)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * Get report schedule by ID.
     * GET /api/sla/report-schedules/{scheduleId}
     */
    @GetMapping("/{scheduleId}")
    public ResponseEntity<SlaReportScheduleDto> getSchedule(@PathVariable UUID scheduleId) {
        SlaReportSchedule schedule = scheduleService.getScheduleById(scheduleId);
        return ResponseEntity.ok(scheduleMapper.toDto(schedule));
    }

    /**
     * Create new report schedule.
     * POST /api/sla/report-schedules
     */
    @PostMapping
    public ResponseEntity<SlaReportScheduleDto> createSchedule(
            @RequestBody @Valid CreateSlaReportScheduleRequest request) {

        log.info("Creating report schedule for SLA: {}", request.getSlaDefinitionId());

        SlaReportSchedule created = scheduleService.createSchedule(request);

        return ResponseEntity.status(HttpStatus.CREATED)
                .body(scheduleMapper.toDto(created));
    }

    /**
     * Update existing report schedule.
     * PUT /api/sla/report-schedules/{scheduleId}
     */
    @PutMapping("/{scheduleId}")
    public ResponseEntity<SlaReportScheduleDto> updateSchedule(
            @PathVariable UUID scheduleId,
            @RequestBody @Valid UpdateSlaReportScheduleRequest request) {

        log.info("Updating report schedule: {}", scheduleId);

        SlaReportSchedule updated = scheduleService.updateSchedule(scheduleId, request);

        return ResponseEntity.ok(scheduleMapper.toDto(updated));
    }

    /**
     * Delete report schedule.
     * DELETE /api/sla/report-schedules/{scheduleId}
     */
    @DeleteMapping("/{scheduleId}")
    public ResponseEntity<Void> deleteSchedule(@PathVariable UUID scheduleId) {
        log.info("Deleting report schedule: {}", scheduleId);

        scheduleService.deleteSchedule(scheduleId);

        return ResponseEntity.noContent().build();
    }

    /**
     * Activate/deactivate schedule.
     * PATCH /api/sla/report-schedules/{scheduleId}/status
     */
    @PatchMapping("/{scheduleId}/status")
    public ResponseEntity<Void> updateScheduleStatus(
            @PathVariable UUID scheduleId,
            @RequestParam Boolean isActive) {

        scheduleService.updateScheduleStatus(scheduleId, isActive);

        return ResponseEntity.noContent().build();
    }

    /**
     * Manually trigger report generation for schedule.
     * POST /api/sla/report-schedules/{scheduleId}/trigger
     */
    @PostMapping("/{scheduleId}/trigger")
    public ResponseEntity<SlaReportDto> triggerReportGeneration(
            @PathVariable UUID scheduleId,
            @RequestParam(required = false) LocalDate periodStart) {

        log.info("Manually triggering report generation for schedule: {}", scheduleId);

        SlaReportDto report = scheduleService.triggerManualGeneration(scheduleId, periodStart);

        return ResponseEntity.accepted().body(report);
    }
}
```

**ScheduledSlaReportController (Access to stored reports):**

```java
@RestController
@RequestMapping("/api/sla/reports/scheduled")
@RequiredArgsConstructor
@Slf4j
public class ScheduledSlaReportController {

    private final ScheduledSlaReportService reportService;
    private final SlaReportMapper reportMapper;

    /**
     * List all generated reports with filters.
     * GET /api/sla/reports/scheduled?slaDefinitionId=...&periodType=MONTHLY&status=PUBLISHED
     */
    @GetMapping
    public ResponseEntity<Page<SlaReportDto>> listReports(
            @RequestParam(required = false) UUID slaDefinitionId,
            @RequestParam(required = false) SlaPeriodType periodType,
            @RequestParam(required = false) ReportStatus status,
            @RequestParam(required = false) LocalDateTime startDate,
            @RequestParam(required = false) LocalDateTime endDate,
            Pageable pageable) {

        Page<SlaReport> reports = reportService.listReports(
                slaDefinitionId, periodType, status, startDate, endDate, pageable);

        Page<SlaReportDto> dtos = reports.map(reportMapper::toDto);

        return ResponseEntity.ok(dtos);
    }

    /**
     * Get specific report by ID.
     * GET /api/sla/reports/scheduled/{reportId}
     */
    @GetMapping("/{reportId}")
    public ResponseEntity<SlaReportDto> getReport(@PathVariable UUID reportId) {
        SlaReport report = reportService.getReportById(reportId);
        return ResponseEntity.ok(reportMapper.toDto(report));
    }

    /**
     * Get latest report for SLA definition.
     * GET /api/sla/reports/scheduled/latest?slaDefinitionId=...&periodType=WEEKLY
     */
    @GetMapping("/latest")
    public ResponseEntity<SlaReportDto> getLatestReport(
            @RequestParam UUID slaDefinitionId,
            @RequestParam SlaPeriodType periodType) {

        SlaReport report = reportService.getLatestReport(slaDefinitionId, periodType);
        return ResponseEntity.ok(reportMapper.toDto(report));
    }

    /**
     * Download report as PDF.
     * GET /api/sla/reports/scheduled/{reportId}/pdf
     */
    @GetMapping("/{reportId}/pdf")
    public ResponseEntity<byte[]> downloadReportPdf(@PathVariable UUID reportId) {
        byte[] pdf = reportService.generateReportPdf(reportId);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_PDF);
        headers.setContentDispositionFormData("attachment", "sla-report-" + reportId + ".pdf");

        return ResponseEntity.ok().headers(headers).body(pdf);
    }

    /**
     * Download report as CSV.
     * GET /api/sla/reports/scheduled/{reportId}/csv
     */
    @GetMapping("/{reportId}/csv")
    public ResponseEntity<byte[]> downloadReportCsv(@PathVariable UUID reportId) {
        byte[] csv = reportService.generateReportCsv(reportId);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(new MediaType("text", "csv"));
        headers.setContentDispositionFormData("attachment", "sla-report-" + reportId + ".csv");

        return ResponseEntity.ok().headers(headers).body(csv);
    }

    /**
     * Archive old report.
     * POST /api/sla/reports/scheduled/{reportId}/archive
     */
    @PostMapping("/{reportId}/archive")
    public ResponseEntity<Void> archiveReport(@PathVariable UUID reportId) {
        reportService.archiveReport(reportId);
        return ResponseEntity.noContent().build();
    }

    /**
     * Delete archived report.
     * DELETE /api/sla/reports/scheduled/{reportId}
     */
    @DeleteMapping("/{reportId}")
    public ResponseEntity<Void> deleteReport(@PathVariable UUID reportId) {
        reportService.deleteReport(reportId);
        return ResponseEntity.noContent().build();
    }
}
```

### Migration Script

```sql
-- V10__create_sla_report_tables.sql

-- Table: sla_report_schedule
CREATE TABLE IF NOT EXISTS sla_report_schedule (
    id CHAR(36) NOT NULL PRIMARY KEY
        COMMENT 'Unique schedule identifier (UUID)',
    sla_definition_id CHAR(36) NOT NULL
        COMMENT 'Reference to sla_definition',
    schedule_name VARCHAR(255) NOT NULL
        COMMENT 'User-friendly schedule name',
    schedule_description VARCHAR(1000)
        COMMENT 'Description of what this schedule does',
    period_type VARCHAR(20) NOT NULL
        COMMENT 'Period type for reports: WEEKLY, MONTHLY, QUARTERLY',
    schedule_frequency VARCHAR(20) NOT NULL
        COMMENT 'How often to generate: WEEKLY, MONTHLY, QUARTERLY, CUSTOM',
    cron_expression VARCHAR(100)
        COMMENT 'Custom cron expression for CUSTOM frequency',
    timezone VARCHAR(50) NOT NULL
        COMMENT 'Timezone for schedule execution',
    is_active BOOLEAN NOT NULL DEFAULT TRUE
        COMMENT 'Whether schedule is active',
    email_recipients VARCHAR(2000)
        COMMENT 'Comma-separated list of email recipients',
    include_pdf_attachment BOOLEAN NOT NULL DEFAULT TRUE
        COMMENT 'Include PDF attachment in email',
    include_csv_attachment BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'Include CSV attachment in email',
    auto_archive_after_days INT
        COMMENT 'Auto-archive reports after N days (NULL = never)',
    last_run_at TIMESTAMP
        COMMENT 'When schedule last executed',
    next_run_at TIMESTAMP
        COMMENT 'When schedule will next execute',
    last_report_id CHAR(36)
        COMMENT 'Last generated report ID',
    total_reports_generated BIGINT NOT NULL DEFAULT 0
        COMMENT 'Total number of reports generated',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        COMMENT 'When schedule was created',
    created_by VARCHAR(255) NOT NULL
        COMMENT 'Who created the schedule',
    updated_at TIMESTAMP
        COMMENT 'Last update timestamp',
    updated_by VARCHAR(255)
        COMMENT 'Who last updated the schedule',

    INDEX idx_schedule_sla_id (sla_definition_id),
    INDEX idx_schedule_active (is_active),
    INDEX idx_schedule_next_run (next_run_at),
    INDEX idx_schedule_frequency (schedule_frequency),

    CONSTRAINT fk_schedule_sla_definition
        FOREIGN KEY (sla_definition_id)
        REFERENCES sla_definition(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- Table: sla_report
CREATE TABLE IF NOT EXISTS sla_report (
    id CHAR(36) NOT NULL PRIMARY KEY
        COMMENT 'Unique report identifier (UUID)',
    sla_definition_id CHAR(36) NOT NULL
        COMMENT 'Reference to sla_definition',
    report_schedule_id CHAR(36)
        COMMENT 'Reference to sla_report_schedule (NULL if manual)',
    report_name VARCHAR(255) NOT NULL
        COMMENT 'Human-readable report name',
    period_type VARCHAR(20) NOT NULL
        COMMENT 'Period type: DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY',
    period_start_utc TIMESTAMP NOT NULL
        COMMENT 'Period start in UTC',
    period_end_utc TIMESTAMP NOT NULL
        COMMENT 'Period end in UTC',
    period_start_local TIMESTAMP NOT NULL
        COMMENT 'Period start in SLA timezone',
    period_end_local TIMESTAMP NOT NULL
        COMMENT 'Period end in SLA timezone',

    -- Compliance Summary
    compliance_percent DECIMAL(5, 2)
        COMMENT 'Overall compliance percentage (0-100)',
    compliance_status VARCHAR(20)
        COMMENT 'FULFILLED, BREACHED, WARNING, INSUFFICIENT_DATA',
    target_percent DECIMAL(5, 2)
        COMMENT 'Target compliance percentage',
    deviation_percent DECIMAL(5, 2)
        COMMENT 'Deviation from target (positive or negative)',
    total_minutes_in_period BIGINT
        COMMENT 'Total minutes in reporting period',
    uptime_minutes BIGINT
        COMMENT 'Minutes of uptime',
    downtime_minutes BIGINT
        COMMENT 'Minutes of downtime',
    excluded_downtime_minutes BIGINT
        COMMENT 'Minutes of excluded downtime (maintenance)',

    -- Breach Summary
    total_breaches INT
        COMMENT 'Total number of breaches',
    critical_breaches INT
        COMMENT 'Number of CRITICAL breaches',
    high_breaches INT
        COMMENT 'Number of HIGH breaches',
    medium_breaches INT
        COMMENT 'Number of MEDIUM breaches',
    low_breaches INT
        COMMENT 'Number of LOW breaches',
    total_breach_duration_minutes BIGINT
        COMMENT 'Sum of all breach durations',
    longest_breach_duration_minutes BIGINT
        COMMENT 'Longest single breach duration',
    mttr_minutes BIGINT
        COMMENT 'Mean Time To Resolution',
    has_breaches BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'Quick filter flag for breaches',

    -- Availability Metrics
    availability_percent DECIMAL(5, 2)
        COMMENT 'Availability percentage',
    data_coverage_percent DECIMAL(5, 2)
        COMMENT 'Data coverage percentage',
    total_data_points BIGINT
        COMMENT 'Total number of data points',
    missing_data_points BIGINT
        COMMENT 'Number of missing data points',

    -- Metadata
    report_status VARCHAR(20) NOT NULL
        COMMENT 'DRAFT, PUBLISHED, ARCHIVED',
    report_format VARCHAR(20)
        COMMENT 'JSON, PDF, CSV, HYBRID',
    report_size_bytes BIGINT
        COMMENT 'Size of stored report files',
    report_file_path VARCHAR(500)
        COMMENT 'Path to PDF/CSV files (S3 or filesystem)',
    generation_duration_ms BIGINT
        COMMENT 'Time taken to generate report',
    generated_at TIMESTAMP NOT NULL
        COMMENT 'When report was generated',
    generated_by VARCHAR(255) NOT NULL
        COMMENT 'Who/what generated the report',
    notification_sent BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'Whether notification was sent',
    notification_sent_at TIMESTAMP
        COMMENT 'When notification was sent',
    notification_recipients VARCHAR(2000)
        COMMENT 'Who received notifications',
    archived_at TIMESTAMP
        COMMENT 'When report was archived',
    archived_by VARCHAR(255)
        COMMENT 'Who archived the report',

    INDEX idx_report_sla_id (sla_definition_id),
    INDEX idx_report_schedule_id (report_schedule_id),
    INDEX idx_report_period (period_start_utc, period_end_utc),
    INDEX idx_report_generated (generated_at),
    INDEX idx_report_status (report_status),
    INDEX idx_report_has_breaches (has_breaches),

    CONSTRAINT fk_report_sla_definition
        FOREIGN KEY (sla_definition_id)
        REFERENCES sla_definition(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_report_schedule
        FOREIGN KEY (report_schedule_id)
        REFERENCES sla_report_schedule(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- Table: sla_report_breach_summary
CREATE TABLE IF NOT EXISTS sla_report_breach_summary (
    id CHAR(36) NOT NULL PRIMARY KEY
        COMMENT 'Unique summary identifier (UUID)',
    sla_report_id CHAR(36) NOT NULL
        COMMENT 'Reference to sla_report',
    sla_breach_id CHAR(36) NOT NULL
        COMMENT 'Reference to sla_breach',
    breach_detected_at TIMESTAMP NOT NULL
        COMMENT 'When breach was detected',
    breach_severity VARCHAR(20) NOT NULL
        COMMENT 'CRITICAL, HIGH, MEDIUM, LOW',
    breach_duration_minutes BIGINT
        COMMENT 'Duration of breach in minutes',
    actual_value DECIMAL(5, 2)
        COMMENT 'Actual compliance value',
    threshold_value DECIMAL(5, 2)
        COMMENT 'Threshold that was breached',
    deviation_percent DECIMAL(5, 2)
        COMMENT 'Deviation from threshold',
    breach_description VARCHAR(2000)
        COMMENT 'Human-readable breach description',
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'Whether breach was resolved',
    resolved_at TIMESTAMP
        COMMENT 'When breach was resolved',

    INDEX idx_breach_summary_report (sla_report_id),
    INDEX idx_breach_summary_breach (sla_breach_id),
    INDEX idx_breach_summary_severity (breach_severity),

    CONSTRAINT fk_breach_summary_report
        FOREIGN KEY (sla_report_id)
        REFERENCES sla_report(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_breach_summary_breach
        FOREIGN KEY (sla_breach_id)
        REFERENCES sla_breach(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;
```

### Prednosti ✅

1. **✅ Automatizacija**: Reporti se automatski generišu prema rasporedu
2. **✅ Pre-computed Data**: Brz pristup reportovima (već izračunati)
3. **✅ Historical Access**: Pristup starim reportovima bez re-generisanja
4. **✅ Rich Metadata**: Detaljan summary sa breach info, compliance metrics
5. **✅ Email Notifications**: Automatsko slanje stakeholderima
6. **✅ Flexible Scheduling**: Weekly/Monthly/Quarterly + custom cron
7. **✅ Audit Trail**: Kompletna istorija svih generisanih reportova
8. **✅ Archive Support**: Arhiviranje starih reportova
9. **✅ Performance**: O(1) pristup reportovima (already in database)
10. **✅ CRUD API**: Kompletna administracija schedule-a preko API-ja

### Mane ⚠️

1. **❌ Storage Overhead**: Dodatno storage za sve reportove (može biti značajno)
2. **❌ Data Duplication**: Podaci već postoje u `sla_result` i `sla_breach`
3. **❌ Stale Data Risk**: Report može biti outdated ako se naknadno recompute-uje SLA
4. **❌ Complexity**: Dodatne tabele, schedulers, servisi
5. **❌ Migration Effort**: Potrebna migracija postojećih reporta (ako je potrebna istorija)

### Kada koristiti

- ✅ **Production system** sa čestim pristupom reportovima
- ✅ **Compliance requirements** (audit trail, regulatory)
- ✅ **Dashboard integrations** (brz pristup pre-computed data)
- ✅ **Email notifications** (automatsko slanje stakeholderima)
- ✅ **Historical analysis** (uporedni reporti kroz vreme)

---

## 🔧 Pristup 2: Lazy Report Generation sa Caching (Hybrid Approach) ⭐⭐⭐⭐

### Koncept

Čuva se samo **schedule configuration** i **report metadata** (summary). Detaljan report se generiše on-demand iz `sla_result` podataka i kesira.

### Arhitektura

```
┌─────────────────────────────────────────────────────────┐
│  OCI-MONITOR (Schedulers)                               │
└─────────────────────────────────────────────────────────┘
    │
    │  SlaReportScheduler (weekly: MON 01:00, monthly: 1st 02:00)
    ├──> Load SlaReportSchedule configurations
    ├──> For each active schedule:
    │    ├──> Calculate summary metrics ONLY
    │    ├──> Store report METADATA in sla_report_metadata
    │    ├──> Send email notifications with summary
    │    └──> Update schedule last_run timestamp
    │
    ▼
┌────────────────────────────────────────────────────────┐
│  DATABASE                                              │
│  - sla_report_schedule (schedule config)              │
│  - sla_report_metadata (summary only, lightweight)    │
│  - sla_result (source data - already exists)          │
│  - sla_breach (source data - already exists)          │
└────────────────────────────────────────────────────────┘
    │
    │  User requests report
    ▼
┌─────────────────────────────────────────────────────────┐
│  OCI-API (REST Endpoints)                               │
│  - GET /api/sla/reports/scheduled/{reportId}            │
│    └─> Check if full report cached                      │
│    └─> If not, generate from sla_result + cache         │
│  - GET /api/sla/reports/scheduled/summary (fast)        │
└─────────────────────────────────────────────────────────┘
```

### Data Model (Lightweight)

**SlaReportMetadata Entity:**

```java
@Entity
@Table(name = "sla_report_metadata")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SlaReportMetadata {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @UuidGenerator
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "id", updatable = false, nullable = false, columnDefinition = "char(36)")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sla_definition_id", nullable = false)
    private SlaDefinition slaDefinition;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "report_schedule_id")
    private SlaReportSchedule reportSchedule;

    @Column(name = "report_name", nullable = false, length = 255)
    private String reportName;

    @Column(name = "period_type", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private SlaPeriodType periodType;

    @Column(name = "period_start_utc", nullable = false)
    private LocalDateTime periodStartUtc;

    @Column(name = "period_end_utc", nullable = false)
    private LocalDateTime periodEndUtc;

    // SUMMARY ONLY (lightweight)
    @Column(name = "compliance_percent", precision = 5, scale = 2)
    private BigDecimal compliancePercent;

    @Column(name = "compliance_status", length = 20)
    @Enumerated(EnumType.STRING)
    private SlaStatus complianceStatus;

    @Column(name = "total_breaches")
    private Integer totalBreaches;

    @Column(name = "has_breaches", nullable = false)
    private Boolean hasBreaches;

    // Caching metadata
    @Column(name = "full_report_cached", nullable = false)
    private Boolean fullReportCached = false; // Flag: is full report in cache?

    @Column(name = "cache_key", length = 255)
    private String cacheKey; // Redis key for cached report

    @Column(name = "cache_expires_at")
    private LocalDateTime cacheExpiresAt; // When cache expires

    @Column(name = "generated_at", nullable = false)
    private LocalDateTime generatedAt;

    @Column(name = "generated_by", nullable = false, length = 255)
    private String generatedBy;

    // Notification metadata
    @Column(name = "notification_sent", nullable = false)
    private Boolean notificationSent = false;

    @Column(name = "notification_sent_at")
    private LocalDateTime notificationSentAt;
}
```

**Scheduler (generates metadata only):**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class SlaReportMetadataService {

    private final SlaReportMetadataRepository metadataRepository;
    private final SlaResultRepository slaResultRepository;
    private final SlaBreachRepository slaBreachRepository;

    /**
     * Generate report metadata (summary only).
     * Full report generated on-demand.
     */
    @Transactional
    public SlaReportMetadata generateReportMetadata(SlaReportSchedule schedule) {
        SlaDefinition slaDefinition = schedule.getSlaDefinition();

        // Calculate period
        LocalDate periodStart = calculatePeriodStart(schedule);
        PeriodRange periodRange = periodCalculator.calculateRange(
                slaDefinition, schedule.getPeriodType(), periodStart);

        // Calculate SUMMARY metrics only (fast)
        Object[] metrics = slaResultRepository.calculateAggregatedMetrics(
                slaDefinition.getId(),
                periodRange.getPeriodStartUtc(),
                periodRange.getPeriodEndUtc()
        );

        BigDecimal avgCompliance = (BigDecimal) metrics[0];
        Integer totalBreaches = (Integer) metrics[1];

        // Store metadata only
        SlaReportMetadata metadata = SlaReportMetadata.builder()
                .slaDefinition(slaDefinition)
                .reportSchedule(schedule)
                .reportName(generateReportName(slaDefinition, schedule, periodStart))
                .periodType(schedule.getPeriodType())
                .periodStartUtc(periodRange.getPeriodStartUtc())
                .periodEndUtc(periodRange.getPeriodEndUtc())
                .compliancePercent(avgCompliance)
                .complianceStatus(determineSlaStatus(avgCompliance))
                .totalBreaches(totalBreaches)
                .hasBreaches(totalBreaches > 0)
                .fullReportCached(false) // Not cached yet
                .generatedAt(LocalDateTime.now())
                .generatedBy("scheduler")
                .build();

        return metadataRepository.save(metadata);
    }
}
```

**On-Demand Report Generation with Caching:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class LazyReportGenerationService {

    private final SlaReportMetadataRepository metadataRepository;
    private final SlaReportService reportService; // Existing on-demand service
    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper;

    /**
     * Get full report - generate if not cached.
     */
    @Transactional(readOnly = true)
    public SlaReportDto getFullReport(UUID metadataId) {
        SlaReportMetadata metadata = metadataRepository.findById(metadataId)
                .orElseThrow(() -> new ResourceNotFoundException("Report not found"));

        // Check cache
        if (metadata.getFullReportCached() && metadata.getCacheKey() != null) {
            String cachedJson = redisTemplate.opsForValue().get(metadata.getCacheKey());

            if (cachedJson != null) {
                log.info("✅ Report served from cache: {}", metadataId);
                return objectMapper.readValue(cachedJson, SlaReportDto.class);
            }
        }

        // Generate report on-demand (using existing service)
        log.info("Generating report on-demand: {}", metadataId);
        SlaReportDto report = reportService.generateReport(
                metadata.getSlaDefinition().getId(),
                metadata.getPeriodType(),
                metadata.getPeriodStartUtc().toLocalDate()
        );

        // Cache for 7 days
        String cacheKey = "sla:report:" + metadataId;
        String reportJson = objectMapper.writeValueAsString(report);
        redisTemplate.opsForValue().set(cacheKey, reportJson, Duration.ofDays(7));

        // Update metadata
        metadata.setFullReportCached(true);
        metadata.setCacheKey(cacheKey);
        metadata.setCacheExpiresAt(LocalDateTime.now().plusDays(7));
        metadataRepository.save(metadata);

        log.info("✅ Report generated and cached: {}", metadataId);
        return report;
    }

    /**
     * Invalidate cache when SLA results change.
     */
    @EventListener
    public void onSlaResultUpdated(SlaResultUpdatedEvent event) {
        // Find all report metadata for this SLA + period
        List<SlaReportMetadata> affectedReports = metadataRepository
                .findBySlaDefinitionAndPeriod(
                        event.getSlaDefinitionId(),
                        event.getPeriodStart(),
                        event.getPeriodEnd()
                );

        for (SlaReportMetadata metadata : affectedReports) {
            if (metadata.getCacheKey() != null) {
                redisTemplate.delete(metadata.getCacheKey());
                metadata.setFullReportCached(false);
                metadata.setCacheKey(null);
                metadataRepository.save(metadata);

                log.info("Cache invalidated for report: {}", metadata.getId());
            }
        }
    }
}
```

### Prednosti ✅

1. **✅ Minimal Storage**: Čuva se samo summary metadata
2. **✅ Always Fresh Data**: Report se generiše iz latest data
3. **✅ Automatic Updates**: Cache se invalidiše kada se SLA recompute-uje
4. **✅ Fast Listings**: Brzo listanje reportova (samo metadata)
5. **✅ Flexible**: Full report on-demand, summary always available
6. **✅ Cost Effective**: Manje storage cost-a
7. **✅ Cache Performance**: Redis cache za često pristupane reportove
8. **✅ Lower Complexity**: Jednostavniji data model

### Mane ⚠️

1. **❌ First Access Latency**: Prvi pristup reportu je spor (generate + cache)
2. **❌ Cache Dependency**: Zahteva Redis za optimalan performance
3. **❌ Cache Invalidation Complexity**: Mora se pravilno invalidirati cache
4. **❌ No True Historical Reports**: Report može biti različit od originalnog (ako se data promeni)
5. **❌ Email Limitations**: Emailovi sadrže samo summary (ne full report)

### Kada koristiti

- ✅ **Storage-constrained environments**
- ✅ **Frequently changing data** (recomputations are common)
- ✅ **Infrequent report access** (većina reportova se retko gleda)
- ✅ **Real-time accuracy required** (report uvek reflektuje latest data)

---

## 🔧 Pristup 3: Event-Driven Report Generation (Auto-Generate on SLA Computation) ⭐⭐⭐

### Koncept

Reporti se automatski generišu kada se završi SLA computation. Nema posebnih schedulera za reportove - koristi se već postojeći `SlaScheduler`.

### Arhitektura

```
┌─────────────────────────────────────────────────────────┐
│  OCI-MONITOR (Existing SLA Schedulers)                  │
└─────────────────────────────────────────────────────────┘
    │
    │  SlaScheduler (already exists)
    ├──> Compute DAILY SLA results
    ├──> Compute WEEKLY SLA results
    ├──> Compute MONTHLY SLA results
    │
    │  Event: SlaComputationCompletedEvent(periodType, periodDate)
    ▼
┌─────────────────────────────────────────────────────────┐
│  SlaReportAutoGenerationService (@EventListener)        │
│  - Listens to SlaComputationCompletedEvent              │
│  - Checks if report should be generated for period      │
│  - Generates report if schedule configured              │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────────────────────┐
│  DATABASE                                              │
│  - sla_report_schedule (minimal config)               │
│  - sla_report (generated reports)                     │
└────────────────────────────────────────────────────────┘
```

### Implementation

**Event Listener:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class SlaReportAutoGenerationService {

    private final SlaReportScheduleRepository scheduleRepository;
    private final SlaReportGenerationService reportGenerationService;

    /**
     * Automatically generate report when SLA computation completes.
     */
    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onSlaComputationCompleted(SlaComputationCompletedEvent event) {
        UUID slaDefinitionId = event.getSlaDefinitionId();
        SlaPeriodType periodType = event.getPeriodType();
        LocalDate periodDate = event.getPeriodDate();

        log.info("SLA computation completed, checking for report schedules: {} - {} - {}",
                 slaDefinitionId, periodType, periodDate);

        // Find active schedule for this SLA + period type
        Optional<SlaReportSchedule> schedule = scheduleRepository
                .findActiveBySlaDefinitionAndPeriodType(slaDefinitionId, periodType);

        if (schedule.isEmpty()) {
            log.debug("No active report schedule found for: {} - {}", slaDefinitionId, periodType);
            return;
        }

        SlaReportSchedule activeSchedule = schedule.get();

        // Check if this is a "report period" (e.g., end of week for WEEKLY reports)
        if (!isReportPeriod(activeSchedule, periodDate)) {
            log.debug("Not a report period for schedule: {}", activeSchedule.getId());
            return;
        }

        try {
            log.info("Auto-generating report for schedule: {}", activeSchedule.getScheduleName());

            SlaReport report = reportGenerationService.generateScheduledReport(activeSchedule);

            log.info("✅ Report auto-generated: {}", report.getId());

        } catch (Exception e) {
            log.error("❌ Failed to auto-generate report for schedule {}: {}",
                     activeSchedule.getId(), e.getMessage(), e);
        }
    }

    /**
     * Check if this date triggers report generation.
     * For WEEKLY: Monday (end of previous week)
     * For MONTHLY: 1st of month (end of previous month)
     */
    private boolean isReportPeriod(SlaReportSchedule schedule, LocalDate date) {
        return switch (schedule.getPeriodType()) {
            case WEEKLY -> date.getDayOfWeek() == DayOfWeek.MONDAY;
            case MONTHLY -> date.getDayOfMonth() == 1;
            case QUARTERLY -> date.getDayOfMonth() == 1 && (date.getMonthValue() % 3 == 1);
            default -> false;
        };
    }
}
```

**Event Definition:**

```java
@Getter
public class SlaComputationCompletedEvent extends ApplicationEvent {

    private final UUID slaDefinitionId;
    private final SlaPeriodType periodType;
    private final LocalDate periodDate;
    private final UUID slaResultId;

    public SlaComputationCompletedEvent(
            Object source,
            UUID slaDefinitionId,
            SlaPeriodType periodType,
            LocalDate periodDate,
            UUID slaResultId) {
        super(source);
        this.slaDefinitionId = slaDefinitionId;
        this.periodType = periodType;
        this.periodDate = periodDate;
        this.slaResultId = slaResultId;
    }
}
```

**Publish Event from SlaSchedulerService:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class SlaSchedulerService {

    private final ApplicationEventPublisher eventPublisher;

    public void processPeriodType(SlaPeriodType periodType, LocalDate periodDate, LocalDateTime now) {
        // ... existing logic ...

        for (SlaDefinition slaDefinition : slaDefinitions) {
            SlaResult result = slaComputationService.computeSla(...);

            // ✅ NEW: Publish event after computation
            eventPublisher.publishEvent(new SlaComputationCompletedEvent(
                    this,
                    slaDefinition.getId(),
                    periodType,
                    periodDate,
                    result.getId()
            ));
        }
    }
}
```

### Prednosti ✅

1. **✅ No Separate Scheduler**: Koristi postojeće SLA schedulers
2. **✅ Perfect Timing**: Report se generiše odmah nakon SLA computationa
3. **✅ Simpler Architecture**: Manje moving parts
4. **✅ Guaranteed Consistency**: Report uvek odgovara latest SLA results
5. **✅ Lower Latency**: Report dostupan odmah nakon computationa
6. **✅ Event-Driven**: Moderna arhitektura, loosely coupled

### Mane ⚠️

1. **❌ Limited Flexibility**: Vezano za SLA computation schedule
2. **❌ Cannot Skip Periods**: Report se generiše za svaki computed period
3. **❌ No Custom Timing**: Ne može se generisati report u drugom vremenu
4. **❌ Tight Coupling**: Report generation vezan za SLA computation events
5. **❌ Harder to Debug**: Event-driven flows su kompleksniji za debug

### Kada koristiti

- ✅ **Simple requirements** (report uvek prati SLA computation)
- ✅ **Real-time reporting** (report odmah nakon computationa)
- ✅ **Minimal infrastructure** (ne želiš dodatne schedulers)
- ✅ **Event-driven architecture** (vec koristiš events)

---

## 📊 Detaljno Poređenje Pristupa

| Feature | Pristup 1: Pre-Generated | Pristup 2: Lazy + Cache | Pristup 3: Event-Driven |
|---------|-------------------------|------------------------|------------------------|
| **Storage** | ❌ High (full reports) | ✅ Low (metadata only) | ⚠️ Medium (full reports) |
| **Performance (List)** | ✅ Fast (pre-computed) | ✅ Fast (metadata) | ✅ Fast (pre-computed) |
| **Performance (Detail)** | ✅ Instant | ⚠️ First access slow | ✅ Instant |
| **Historical Accuracy** | ✅ Perfect snapshot | ❌ Changes with data | ✅ Perfect snapshot |
| **Flexibility** | ✅ Full control | ✅ Full control | ⚠️ Limited |
| **Complexity** | ⚠️ High | ⚠️ Medium | ✅ Low |
| **Scheduler Count** | ⚠️ +2 (weekly/monthly) | ⚠️ +2 (weekly/monthly) | ✅ 0 (reuse existing) |
| **Cache Dependency** | ✅ None | ❌ Redis required | ✅ None |
| **Cache Invalidation** | ✅ N/A | ❌ Complex logic | ✅ N/A |
| **Email Notifications** | ✅ Full report | ⚠️ Summary only | ✅ Full report |
| **Data Freshness** | ⚠️ Snapshot | ✅ Always fresh | ✅ Latest |
| **Archive Support** | ✅ Built-in | ⚠️ Manual | ✅ Built-in |
| **Audit Trail** | ✅ Complete | ⚠️ Metadata only | ✅ Complete |
| **Implementation Time** | ⚠️ 16-20h | ✅ 10-14h | ✅ 8-12h |
| **Maintenance Cost** | ⚠️ High | ⚠️ Medium | ✅ Low |

---

## 🎯 Finalna Preporuka

### **Preporučujem Pristup 1: Pre-Generated Reports sa Scheduler Storage** ⭐⭐⭐⭐⭐

### Obrazloženje

**1. Biznis Zahtevi Najbolje Pokriveni:**
- ✅ **Compliance & Audit**: Potreban je immutable snapshot reporta za regulatory compliance
- ✅ **Historical Analysis**: Stakeholderi trebaju pristup prošlim reportovima u originalnom obliku
- ✅ **Email Notifications**: Treba slati full report emailom, ne samo summary
- ✅ **Dashboard Performance**: Executive dashboards zahtevaju brz pristup pre-computed data

**2. Prednosti Pretežu Mane:**
- Storage cost je zanemarljiv u odnosu na vrednost complete audit trail-a
- Performance benefit (instant access) je kritičan za user experience
- Immutable reports su esencijalni za compliance (SOX, GDPR, internal audits)
- Flexibility u scheduling-u (custom cron, different frequencies) je važna

**3. Realne Potrebe:**
```
Use Case: Monthly Compliance Meeting
- Manager treba uporediti Q1, Q2, Q3 reportove
- Reporti moraju biti identical kao kada su originalno generisani
- Ne može se osloniti na cache (može expirovati)
- Treba instant access (ne može čekati generation)

✅ Pristup 1: Instant access, immutable data
❌ Pristup 2: Možda expirovan cache, data može biti changed
⚠️ Pristup 3: OK, ali limited flexibility
```

**4. Storage je Pristupačan:**
```
Procena storage-a:
- Report size: ~50KB (JSON with metadata + breach summaries)
- Frequency: 100 SLAs × 52 weeks = 5,200 reports/year
- Total: 5,200 × 50KB = 260 MB/year
- Cost: <$1/year na većini cloud providera

→ Storage cost is negligible, value is immense
```

**5. Alternativni Pristup za Edge Cases:**

Ako storage postane problem (highly unlikely), može se kombinovati:
- **Pristup 1** za kritične SLAs (production, customer-facing)
- **Pristup 2** za non-critical SLAs (internal, development)

---

## 📦 Implementation Roadmap

### Faza 1: Core Entities & Migrations (Week 1) - 12h

**Tasks:**
1. Create `SlaReportSchedule` entity (2h)
2. Create `SlaReport` entity (3h)
3. Create `SlaReportBreachSummary` entity (1h)
4. Create migration script V10 (2h)
5. Create repositories (1h)
6. Create mappers (2h)
7. Unit tests for entities (1h)

**Deliverables:**
- ✅ Database schema created
- ✅ Entities with relationships
- ✅ Repositories with queries
- ✅ MapStruct mappers

### Faza 2: Report Generation Service (Week 2) - 16h

**Tasks:**
1. Implement `SlaReportGenerationService` (6h)
   - Period calculation
   - Metrics aggregation
   - Report building
   - Breach summary creation
2. Implement `PeriodCalculator` helper (2h)
3. Implement `ReportMetricsCalculator` helper (3h)
4. Email notification integration (2h)
5. Unit tests (2h)
6. Integration tests (1h)

**Deliverables:**
- ✅ Report generation logic
- ✅ Email notifications
- ✅ Comprehensive tests

### Faza 3: Scheduler (Week 3) - 10h

**Tasks:**
1. Implement `SlaReportScheduler` (4h)
   - Weekly scheduler (@Scheduled)
   - Monthly scheduler (@Scheduled)
   - ShedLock integration
2. Implement schedule processing logic (3h)
3. Next run calculation (1h)
4. Scheduler tests (2h)

**Deliverables:**
- ✅ Automated report generation
- ✅ ShedLock coordination
- ✅ Scheduler tests

### Faza 4: CRUD API (Week 4) - 14h

**Tasks:**
1. Implement `SlaReportScheduleService` (4h)
2. Implement `SlaReportScheduleController` (3h)
3. Implement `ScheduledSlaReportService` (3h)
4. Implement `ScheduledSlaReportController` (2h)
5. Request/Response DTOs (1h)
6. API tests (1h)

**Deliverables:**
- ✅ Schedule CRUD endpoints
- ✅ Report access endpoints
- ✅ API documentation

### Faza 5: Archive & Cleanup (Week 5) - 8h

**Tasks:**
1. Implement auto-archive scheduler (3h)
2. Implement archive service (2h)
3. Implement cleanup/delete logic (2h)
4. Tests (1h)

**Deliverables:**
- ✅ Auto-archive old reports
- ✅ Manual archive API
- ✅ Delete archived reports

### Faza 6: Polish & Documentation (Week 6) - 8h

**Tasks:**
1. Performance optimization (2h)
2. Error handling improvements (1h)
3. Logging enhancements (1h)
4. API documentation (Postman collection) (2h)
5. User guide (1h)
6. Code review & refactoring (1h)

**Deliverables:**
- ✅ Production-ready code
- ✅ Complete documentation
- ✅ Postman collection

**Total Estimated Time: 68 hours (8-9 weeks)**

---

## 🧪 Testing Strategy

### Unit Tests

```java
@Test
void testWeeklyReportGeneration() {
    // Given
    SlaReportSchedule schedule = createWeeklySchedule();

    // When
    SlaReport report = reportGenerationService.generateScheduledReport(schedule);

    // Then
    assertThat(report).isNotNull();
    assertThat(report.getPeriodType()).isEqualTo(SlaPeriodType.WEEKLY);
    assertThat(report.getCompliancePercent()).isGreaterThan(BigDecimal.ZERO);
    assertThat(report.getBreachSummaries()).isNotEmpty();
}

@Test
void testReportMetricsCalculation() {
    // Given
    List<SlaResult> results = createTestResults();
    List<SlaBreach> breaches = createTestBreaches();

    // When
    ReportMetrics metrics = reportMetricsCalculator.calculate(results, breaches);

    // Then
    assertThat(metrics.compliancePercent()).isEqualTo(new BigDecimal("95.50"));
    assertThat(metrics.totalBreaches()).isEqualTo(3);
    assertThat(metrics.criticalBreaches()).isEqualTo(1);
}
```

### Integration Tests

```java
@Test
@Transactional
void testScheduledReportCreation() {
    // Given
    CreateSlaReportScheduleRequest request = new CreateSlaReportScheduleRequest();
    request.setSlaDefinitionId(slaId);
    request.setPeriodType(SlaPeriodType.WEEKLY);
    request.setFrequency(ScheduleFrequency.WEEKLY);

    // When
    ResponseEntity<SlaReportScheduleDto> response =
            controller.createSchedule(request);

    // Then
    assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
    assertThat(response.getBody().getId()).isNotNull();

    // Verify database
    SlaReportSchedule saved = scheduleRepository.findById(response.getBody().getId()).orElseThrow();
    assertThat(saved.getIsActive()).isTrue();
}
```

### Scheduler Tests

```java
@Test
@EnableScheduling
void testWeeklySchedulerExecution() {
    // Given
    SlaReportSchedule schedule = createActiveWeeklySchedule();
    scheduleRepository.save(schedule);

    // When
    scheduler.generateWeeklyReports();

    // Then
    SlaReport generatedReport = reportRepository
            .findLatestBySchedule(schedule.getId()).orElseThrow();

    assertThat(generatedReport).isNotNull();
    assertThat(generatedReport.getGeneratedBy()).isEqualTo("scheduler");
}
```

---

## 📚 API Examples

### Create Report Schedule

```bash
POST /api/sla/report-schedules
Content-Type: application/json

{
  "slaDefinitionId": "abc-123",
  "scheduleName": "Production API Weekly Reports",
  "scheduleDescription": "Weekly compliance reports for production API SLA",
  "periodType": "WEEKLY",
  "frequency": "WEEKLY",
  "timezone": "America/New_York",
  "isActive": true,
  "emailRecipients": "compliance@company.com,ops-lead@company.com",
  "includePdfAttachment": true,
  "includeCsvAttachment": false,
  "autoArchiveAfterDays": 90
}

Response (201 Created):
{
  "id": "schedule-456",
  "scheduleName": "Production API Weekly Reports",
  "isActive": true,
  "nextRunAt": "2025-11-18T01:00:00",
  "totalReportsGenerated": 0
}
```

### List Generated Reports

```bash
GET /api/sla/reports/scheduled?slaDefinitionId=abc-123&periodType=WEEKLY&page=0&size=10

Response (200 OK):
{
  "content": [
    {
      "id": "report-789",
      "reportName": "Production API - Weekly Report - Week 45",
      "periodType": "WEEKLY",
      "periodStartLocal": "2025-11-04T00:00:00",
      "periodEndLocal": "2025-11-11T00:00:00",
      "compliancePercent": 99.85,
      "complianceStatus": "FULFILLED",
      "totalBreaches": 2,
      "criticalBreaches": 0,
      "highBreaches": 1,
      "mediumBreaches": 1,
      "hasBreaches": true,
      "generatedAt": "2025-11-11T01:05:23",
      "reportStatus": "PUBLISHED"
    },
    ...
  ],
  "totalElements": 52,
  "totalPages": 6
}
```

### Get Report Details

```bash
GET /api/sla/reports/scheduled/report-789

Response (200 OK):
{
  "id": "report-789",
  "slaDefinitionName": "Production API Availability",
  "reportName": "Production API - Weekly Report - Week 45",
  "periodType": "WEEKLY",
  "periodStartUtc": "2025-11-04T05:00:00Z",
  "periodEndUtc": "2025-11-11T05:00:00Z",
  "periodStartLocal": "2025-11-04T00:00:00",
  "periodEndLocal": "2025-11-11T00:00:00",

  "complianceSummary": {
    "compliancePercent": 99.85,
    "complianceStatus": "FULFILLED",
    "targetPercent": 99.50,
    "deviationPercent": 0.35,
    "totalMinutesInPeriod": 10080,
    "uptimeMinutes": 10065,
    "downtimeMinutes": 15,
    "excludedDowntimeMinutes": 0
  },

  "breachSummary": {
    "totalBreaches": 2,
    "criticalBreaches": 0,
    "highBreaches": 1,
    "mediumBreaches": 1,
    "lowBreaches": 0,
    "totalBreachDurationMinutes": 15,
    "longestBreachDurationMinutes": 10,
    "mttrMinutes": 7
  },

  "breachEvents": [
    {
      "breachDetectedAt": "2025-11-05T14:30:00",
      "breachSeverity": "HIGH",
      "breachDurationMinutes": 10,
      "actualValue": 92.50,
      "thresholdValue": 95.00,
      "deviationPercent": 2.50,
      "breachDescription": "High severity SLA breach detected...",
      "isResolved": true,
      "resolvedAt": "2025-11-05T14:40:00"
    },
    {
      "breachDetectedAt": "2025-11-08T09:15:00",
      "breachSeverity": "MEDIUM",
      "breachDurationMinutes": 5,
      "actualValue": 94.20,
      "thresholdValue": 95.00,
      "deviationPercent": 0.80,
      "breachDescription": "Medium severity SLA breach detected...",
      "isResolved": true,
      "resolvedAt": "2025-11-08T09:20:00"
    }
  ],

  "metadata": {
    "generatedAt": "2025-11-11T01:05:23",
    "generatedBy": "scheduler",
    "generationDurationMs": 2341,
    "reportStatus": "PUBLISHED",
    "notificationSent": true,
    "notificationSentAt": "2025-11-11T01:06:45",
    "notificationRecipients": "compliance@company.com,ops-lead@company.com"
  }
}
```

### Download Report PDF

```bash
GET /api/sla/reports/scheduled/report-789/pdf

Response (200 OK):
Content-Type: application/pdf
Content-Disposition: attachment; filename="sla-report-Production_API-weekly-2025-11-04.pdf"

[Binary PDF content]
```

---

## 🔒 Security & Access Control

### Authorization Rules

```java
@PreAuthorize("hasAuthority('SLA_REPORT_READ')")
public ResponseEntity<SlaReportDto> getReport(@PathVariable UUID reportId) {
    // Only users with SLA_REPORT_READ can access
}

@PreAuthorize("hasAuthority('SLA_REPORT_MANAGE')")
public ResponseEntity<SlaReportScheduleDto> createSchedule(...) {
    // Only admins can create/modify schedules
}
```

### Tenant Isolation

```java
private void validateTenantAccess(SlaReport report) {
    String currentTenant = SecurityContextHolder.getContext()
            .getAuthentication().getPrincipal().getTenantId();

    if (!report.getSlaDefinition().getTenant().getId().equals(currentTenant)) {
        throw new AccessDeniedException("No access to this tenant's reports");
    }
}
```

---

## 🚀 Deployment Considerations

### Database Indexes

```sql
-- Critical indexes for performance
CREATE INDEX idx_report_period_lookup
    ON sla_report(sla_definition_id, period_start_utc, period_end_utc);

CREATE INDEX idx_report_latest
    ON sla_report(sla_definition_id, period_type, generated_at DESC);

CREATE INDEX idx_schedule_next_run
    ON sla_report_schedule(is_active, frequency, next_run_at);
```

### Scheduler Configuration

```properties
# application.properties (oci-monitor)

# Enable/disable report schedulers
sla.report.scheduled.weekly.enabled=true
sla.report.scheduled.monthly.enabled=true

# Scheduler timing (override defaults)
# sla.report.scheduled.weekly.cron=0 0 1 * * MON
# sla.report.scheduled.monthly.cron=0 0 2 1 * *

# Report generation settings
sla.report.generation.timeout.minutes=30
sla.report.generation.batch.size=10

# Archive settings
sla.report.archive.enabled=true
sla.report.archive.default.days=90
sla.report.archive.cleanup.cron=0 0 3 * * *
```

### Monitoring & Alerts

```java
// Metrics to track
@Timed("sla.report.generation.duration")
@Counted("sla.report.generation.count")
public SlaReport generateScheduledReport(SlaReportSchedule schedule) {
    // ... generation logic
}

// Alerts to configure
- Alert: Report generation takes > 5 minutes
- Alert: Report generation failure rate > 5%
- Alert: No reports generated in last 48 hours (for active schedules)
- Alert: Email notification failure rate > 10%
```

---

## 📊 Success Metrics

### KPIs to Track

1. **Report Generation Performance:**
   - Average generation time (target: <3 seconds)
   - 95th percentile generation time (target: <10 seconds)
   - Generation success rate (target: >99%)

2. **User Engagement:**
   - Reports accessed per week
   - Average time to access report after generation
   - PDF/CSV download rate

3. **System Health:**
   - Storage usage growth rate
   - Scheduler execution success rate (target: 100%)
   - Email delivery success rate (target: >98%)

4. **Business Value:**
   - Time saved on manual report generation
   - Compliance audit readiness
   - Stakeholder satisfaction scores

---

## 🎯 Next Steps

1. **Review & Approval** (1 day)
   - Review this analysis with team
   - Discuss any concerns/questions
   - Get approval to proceed

2. **Planning** (1 day)
   - Create Jira tickets for all tasks
   - Assign to sprint(s)
   - Set up development environment

3. **Implementation** (6-8 weeks)
   - Follow roadmap phases
   - Weekly demos to stakeholders
   - Continuous testing & feedback

4. **Deployment** (1 week)
   - Dev environment testing
   - Staging deployment
   - Production rollout (with feature flag)

5. **Monitoring** (Ongoing)
   - Track KPIs
   - Gather user feedback
   - Iterate based on learnings

---

**Prepared by:** Claude Code Analysis
**Date:** 2025-11-13
**Version:** 1.0
**Status:** Ready for Review
