# SLA Schedulers — Pregled

> **Datum**: 2026-03-11
> **Modul**: oci-monitor (oci-backend)
> **Paket**: `com.sistemisolutions.oci.monitor.scheduler`

---

## Infrastruktura

### Distributed Locking (ShedLock)

Svi scheduleri koriste **ShedLock** za multi-instance safety. Konfiguracija:

| Komponenta | Lokacija |
|-----------|---------|
| `SchedulerConfig.java` | `oci-monitor/config/` — `@EnableScheduling`, `@EnableSchedulerLock(defaultLockAtMostFor = "PT10M")` |
| `shedlock` tabela | Flyway migracija `V9__create_shedlock_table.sql` — `name PK`, `lock_until`, `locked_at`, `locked_by` |
| `LockProvider` bean | `JdbcTemplateLockProvider` sa `usingDbTime()` (zaštita od clock drift-a) |

### Scheduler Toggle (On/Off)

Svaki scheduler može biti nezavisno uključen/isključen putem `scheduler_settings` tabele:

```sql
SELECT * FROM scheduler_settings WHERE scheduler_task_name LIKE 'sla.%';
```

Servis: `SchedulerToggleService.isTaskEnabled(taskName)` — vraća `false` ako task nije pronađen.

---

## SLA Scheduleri

### Timeline izvršavanja

```
VREME     SCHEDULER                              ŠTA RADI
─────────────────────────────────────────────────────────────────────
00:05     SlaScheduler.scheduleDailySlas()        Dnevna SLA computation
00:10     SlaScheduler.scheduleWeeklySlas()       Nedeljna SLA computation (samo ponedeljkom)
00:15     SlaScheduler.scheduleMonthlySlas()      Mesečna SLA computation (samo 1. u mesecu)
00:30     SlaReportScheduler.processScheduledReports()  Generisanje izveštaja (svaki dan)
```

**Redosled je bitan**: SlaReportScheduler mora da se izvršava POSLE SlaScheduler-a jer koristi prethodno izračunate SlaResult zapise za generisanje izveštaja.

---

### 1. SlaScheduler — SLA Computation

**Fajl**: `oci-monitor/scheduler/SlaScheduler.java`

Izvršava periodične batch SLA kalkulacije. Za svaku aktivnu SLA definiciju:
1. Učitava SlaDefinition
2. Računa availability metriku iz cached metric podataka
3. Određuje status (FULFILLED / WARNING / BREACHED / INSUFFICIENT_DATA)
4. Računa penalty ako je BREACHED
5. Čuva SlaResult u bazu
6. Emituje `SlaResultComputedEvent` → breach detection → notifikacije

| Metoda | Cron | Izvršava se | ShedLock | Toggle |
|--------|------|------------|----------|--------|
| `scheduleDailySlas()` | `0 5 0 * * *` | Svaki dan u 00:05 | lockAtMost=10min, lockAtLeast=1min | `sla.scheduled.daily` |
| `scheduleWeeklySlas()` | `0 10 0 * * MON` | Ponedeljkom u 00:10 | lockAtMost=10min, lockAtLeast=1min | `sla.scheduled.weekly` |
| `scheduleMonthlySlas()` | `0 15 0 1 * *` | 1. u mesecu u 00:15 | lockAtMost=30min, lockAtLeast=2min | `sla.scheduled.monthly` |

**Delegacija**: `SlaScheduler` → `SlaSchedulerService.processPeriodType()` → `SlaComputationService.computeSla()` (per SLA)

**Greške**: Catch-and-log per SLA definition. Neuspeh jedne SLA ne zaustavlja batch.

**Period koji se obrađuje**:
- Daily: juče (`LocalDate.now().minusDays(1)`)
- Weekly: prošla nedelja (`LocalDate.now().minusWeeks(1)`)
- Monthly: prošli mesec (`LocalDate.now().minusMonths(1)`)

---

### 2. SlaReportScheduler — Report Generation

**Fajl**: `oci-monitor/scheduler/SlaReportScheduler.java`

Generiše SLA izveštaje na osnovu konfiguracije iz `SlaReportSchedule` entiteta. Svaki report schedule definiše:
- Koju SLA definition prati
- Period type izveštaja (DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY)
- Frekvenciju generisanja (WEEKLY, MONTHLY, QUARTERLY, CUSTOM cron)
- Email primaoce i PDF/CSV attachment opcije

| Metoda | Cron | Konfigurabilno | ShedLock | Toggle |
|--------|------|---------------|----------|--------|
| `processScheduledReports()` | `${sla.report.scheduler.cron:0 30 0 * * *}` | Da, via props | lockAtMost=30min, lockAtLeast=2min | `sla.report.scheduled` |

**Konfigurabilni cron** — property `sla.report.scheduler.cron` u `application.properties`:
```properties
# Default: svaki dan u 00:30 (posle SLA computation schedulera 00:05-00:15)
sla.report.scheduler.cron=0 30 0 * * *
```

**VAŽNO**: Ako se menja cron expression, mora biti POSLE 00:15 da bi svež computation data bio dostupan.

**Delegacija**: `SlaReportScheduler` → `SlaReportSchedulerService.processDueSchedules()` → `SlaReportGenerationService.generateReport()` (per schedule)

**Logika obrade**:
1. Pronalazi sve aktivne schedule-ove gde `nextRunAt IS NULL OR nextRunAt <= now`
2. Za svaki schedule: generiše SlaReport iz SlaResult i SlaBreach podataka
3. Ažurira schedule: `lastRunAt`, `nextRunAt`, `lastReportId`, `totalReportsGenerated`
4. Skip ako report za period već postoji ili nema podataka

**nextRunAt kalkulacija**:
- WEEKLY → +7 dana
- MONTHLY → +1 mesec
- QUARTERLY → +3 meseca
- CUSTOM → +1 dan (cron kontroliše stvarno vreme)

**Greške**: Catch-and-log per schedule. Neuspeh jednog schedule-a ne zaustavlja batch.

---

## Data Flow

### SLA Computation Flow

```
SlaScheduler (@Scheduled cron)
    │
    ▼
SlaSchedulerService.processPeriodType(periodType, periodDate, now)
    │ findCurrentlyActiveByPeriodType()
    │
    ▼ for each SlaDefinition:
SlaComputationService.computeSla(id, date, forceRecompute, triggeredBy)
    │
    ├─ AvailabilityCalculatorService.calculateAvailability()
    │   ├─ Fetch MetricResult from DB
    │   ├─ Filter by schedule (SlaScheduleUtils)
    │   ├─ Filter by excluded downtimes
    │   └─ Return AvailabilityMetricsDTO
    │
    ├─ Determine SLA status
    ├─ PenaltyCalculationService.calculatePenalty()
    ├─ Save SlaResult
    └─ Publish SlaResultComputedEvent
         │
         ▼
    SlaBreachDetectionService (@TransactionalEventListener AFTER_COMMIT)
         │
         ├─ Calculate severity
         ├─ Create SlaBreach
         └─ SlaNotificationService (email)
```

### Report Generation Flow

```
SlaReportScheduler (@Scheduled cron at 00:30)
    │
    ▼
SlaReportSchedulerService.processDueSchedules(now)
    │ findAllActiveSchedulesDueForExecution(now)
    │
    ▼ for each SlaReportSchedule:
SlaReportGenerationService.generateReport(schedule)
    │
    ├─ calculateReportPeriod() — previous completed period, timezone-aware
    ├─ Check if report already exists → skip
    ├─ Fetch SlaResult records for period
    ├─ Fetch SlaBreach records for period
    ├─ Calculate compliance metrics (aggregation)
    ├─ Calculate breach metrics (severity breakdown, MTTR)
    ├─ Build SlaReport entity
    ├─ Build SlaReportBreachSummary per breach
    ├─ Save → Publish
    └─ Update schedule (recordSuccessfulExecution)
```

---

## Konfiguracija

### application.properties (oci-monitor)

```properties
# Scheduling (global toggle)
scheduling.enabled=true

# SLA Report Scheduler cron
# Default: daily at 00:30 — MUST be after SLA computation (00:05-00:15)
sla.report.scheduler.cron=0 30 0 * * *
```

### scheduler_settings tabela

```sql
-- SLA Computation toggles
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('sla.scheduled.daily', true);
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('sla.scheduled.weekly', true);
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('sla.scheduled.monthly', true);

-- SLA Report toggle
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('sla.report.scheduled', true);
```

---

## Monitoring

### Log prefixes

```
SlaScheduler::         — SLA computation scheduler lifecycle
SlaReportScheduler::   — Report scheduler lifecycle
=== DAILY SLA ===      — Daily computation batch
=== WEEKLY SLA ===     — Weekly computation batch
=== MONTHLY SLA ===    — Monthly computation batch
=== Report Scheduler === — Report generation batch
```

### Batch summary log format

Svaki batch na kraju loguje summary:
```
Total found: N
Successfully processed: N
Skipped: N
Failed: N
Duration: N ms
```

### ShedLock monitoring

```sql
-- Proveri aktivne lock-ove
SELECT * FROM shedlock WHERE lock_until > NOW();

-- Proveri kad je poslednji put lock bio zauzet
SELECT name, locked_at, locked_by FROM shedlock WHERE name LIKE 'sla%';
```
