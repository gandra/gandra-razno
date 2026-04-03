# SLA Schedulers — Pregled

> **Datum**: 2026-03-12
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
~5min     EmailRetryScheduler.processFailedEmails()    Retry failed emailova (svaki 5 min)
~5min     SlaEventNotificationScheduler.processEventNotifications()  Email za SLA evente (svaki 5 min)
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
- Email primaoce i PDF/CSV attachment opcije (email delivery implementiran — `SlaNotificationService.sendReportEmail()` sa `SlaReportExportService` za PDF/CSV generisanje)

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

### 3. EmailRetryScheduler — Scheduled Email Retry (Phase 2)

**Fajl**: `oci-monitor/scheduler/EmailRetryScheduler.java`

Retry-uje emailove koji su propali posle inline retry-a (Phase 1). Čita iz `email_send_log` tabele i ponovo pokušava slanje putem MailerService.

| Metoda | Interval | Konfigurabilno | ShedLock | Toggle |
|--------|----------|---------------|----------|--------|
| `processFailedEmails()` | `${email.retry.scheduler.interval-ms:300000}` (5 min) | Da, via props | lockAtMost=10min, lockAtLeast=1min | `email.retry.scheduled` |

**Delegacija**: `EmailRetryScheduler` → `EmailSendLogService.processRetryableEmails()` → `MailerService.sendTextEmail/sendHtmlEmail()` (per email)

**Logika obrade**:
1. Pronalazi sve zapise iz `email_send_log` gde `status IN (PENDING, FAILED)` i `next_retry_at <= now` i `retry_count < max_retries`
2. Za svaki: poziva MailerService (koji radi inline retry — 3 pokušaja)
3. SUCCESS → `status = SENT`
4. FAIL → `retry_count++`, `next_retry_at = backoff(count)` (exponential)
5. Kad `retry_count >= max_retries` → `status = MAX_RETRIES_REACHED` + `log.error` alert

**Scheduled retry backoff** (exponential, konfigurabilno):
```
Retry 1:  T+5min      (5 × 3^0)
Retry 2:  T+20min     (5 × 3^1 = 15min later)
Retry 3:  T+1h5min    (5 × 3^2 = 45min later)
Retry 4:  T+3h20min   (5 × 3^3 = 135min later)
Retry 5:  T+9h20min   (5 × 3^4 = 360min = 6h cap)
```

**Alerting**: Na kraju svakog batch-a, proverava `MAX_RETRIES_REACHED` zapise u poslednjih 24h i loguje `log.error` alert.

**Greške**: Catch-and-log per email. Neuspeh jednog email-a ne zaustavlja batch.

**Tabela**: `email_send_log` (Flyway dev V12, prod V6)
**Entity**: `EmailSendLog` (oci-library, standalone, BIGINT PK)
**Servis**: `EmailSendLogService` — `sendEmailWithPersistence()` + `processRetryableEmails()`

**Prvi consumer**: `SlaNotificationService` koristi `EmailSendLogService.sendEmailWithPersistence()` umesto direktnog `MailerService` poziva.

---

### 4. SlaEventNotificationScheduler — SLA Event Email Notifications

**Fajl**: `oci-monitor/scheduler/SlaEventNotificationScheduler.java`

Šalje email notifikacije za SLA lifecycle evente (deactivate, delete, breach acknowledge/resolve, schedule status, report generated). Čita iz `sla_event_log` tabele zapise gde `email_notified = false` i šalje email putem `SlaNotificationService.sendEventNotification()` → `EmailSendLogService.sendEmailWithPersistence()`.

| Metoda | Interval | Konfigurabilno | ShedLock | Toggle |
|--------|----------|---------------|----------|--------|
| `processEventNotifications()` | `${sla.event.notification.scheduler.interval-ms:300000}` (5 min) | Da, via props | lockAtMost=10min, lockAtLeast=1min | `sla.event.notification.scheduled` |

**Delegacija**: `SlaEventNotificationScheduler` → `SlaNotificationService.sendEventNotification(SlaEventLog)` → `EmailSendLogService.sendEmailWithPersistence()` (per recipient)

**Logika obrade**:
1. Pronalazi sve zapise iz `sla_event_log` gde `email_notified = false AND recipients IS NOT NULL AND recipients <> ''` (oldest first)
2. Za svaki event: poziva `SlaNotificationService.sendEventNotification(event)` koji iterira recipients
3. Markira `emailNotified = true`, `emailNotifiedAt = now()` posle uspešnog slanja
4. Per-event error handling — neuspeh jednog eventa ne zaustavlja batch

**Izvori evenata**:
- oci-api: `SlaEventLogService.logEvent()` — za SLA_DEACTIVATED, SLA_DELETED, BREACH_ACKNOWLEDGED, BREACH_RESOLVED, SCHEDULE_ACTIVATED, SCHEDULE_DEACTIVATED
- oci-monitor: `SlaReportGenerationService.logReportGeneratedEvent()` — za REPORT_GENERATED

**Tabela**: `sla_event_log` (Flyway dev V14, prod V8)
**Entity**: `SlaEventLog` (oci-library, standalone, BIGINT PK)
**Servis**: `SlaNotificationService.sendEventNotification(SlaEventLog)` — gradi subject/body per eventType

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
    ├─ logReportGeneratedEvent() — INSERT sla_event_log
    ├─ sendReportEmailIfConfigured() — Email delivery sa PDF/CSV attachmentima
    │   ├─ Check schedule.hasEmailRecipients() && hasEmailAttachments()
    │   ├─ SlaNotificationService.sendReportEmail(schedule, report)
    │   │   ├─ SlaReportExportService.exportToPdf() → byte[] attachment
    │   │   ├─ SlaReportExportService.exportToCsv() → String → byte[] attachment
    │   │   └─ EmailSendLogService.sendEmailWithPersistence() per recipient
    │   └─ Catch-and-log — email failure ne prekida report generation
    └─ Update schedule (recordSuccessfulExecution)
```

---

### SLA Event Notification Flow

```
oci-api (user actions)                    sla_event_log               oci-monitor (scheduler)
──────────────────────                    ─────────────               ───────────────────────

SlaService.deactivate/delete/                  │
  acknowledge/resolve()                        │
    │                                          │
    └── SlaEventLogService.logEvent()          │
        │                                      │
        └── INSERT ──────────────────────────► │
            (emailNotified = false)            │
                                               │         SlaEventNotificationScheduler
SlaReportScheduleManagementService             │         @Scheduled(fixedDelay=5min)
  .updateScheduleStatus()                      │                │
    │                                          │                ▼
    └── SlaEventLogService.logEvent()          │         findPendingEmailNotifications()
        │                                      │                │
        └── INSERT ──────────────────────────► │◄── SELECT ─────┤
                                               │                │
SlaReportGenerationService (oci-monitor)       │                ▼ per event:
  .generateReport()                            │         SlaNotificationService
    │                                          │          .sendEventNotification()
    └── slaEventLogRepository.save()           │                │
        │                                      │                ▼
        └── INSERT ──────────────────────────► │         EmailSendLogService
                                               │          .sendEmailWithPersistence()
                                               │                │
                                               │◄── UPDATE ─────┤
                                               │    emailNotified│
                                               │    = true       │
```

### Email Retry Flow (Phase 1 + Phase 2)

```
[Pozivalac] (npr. SlaNotificationService)
    │
    ▼
EmailSendLogService.sendEmailWithPersistence(request, isHtml, source, sourceEntityId)
    │
    ├── MailerService.send() ──── Phase 1: 3 inline pokušaja (5s, 15s backoff)
    │   │
    │   ├── SUCCESS → return response
    │   │
    │   └── ALL FAILED → logFailedSend() → save email_send_log (FAILED, next_retry_at)
    │                                        return error response
    │
    ▼ (5 min later)
EmailRetryScheduler (@Scheduled fixedDelay=5min)
    │
    ▼
EmailSendLogService.processRetryableEmails()
    │ findRetryableEmails(now)
    │
    ▼ for each EmailSendLog:
MailerService.send() ── Phase 1: 3 inline pokušaja
    │
    ├── SUCCESS → markSent()
    │
    └── FAIL → recordFailedAttempt() → next_retry_at = backoff
                 │
                 └── retry_count >= max_retries? → MAX_RETRIES_REACHED + log.error alert
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

# Email inline retry (Phase 1) — applies to both SMTP and SendGrid
email.retry.max-attempts=3
email.retry.base-delay-ms=5000
email.retry.multiplier=3.0
email.retry.max-delay-ms=45000

# Email scheduled retry (Phase 2) — background job via email_send_log
email.retry.scheduled.max-retries=5
email.retry.scheduled.base-delay-minutes=5
email.retry.scheduled.multiplier=3.0
email.retry.scheduled.max-delay-minutes=360
email.retry.scheduler.interval-ms=300000

# SLA Event Notification Scheduler — email for SLA lifecycle events
sla.event.notification.scheduler.interval-ms=300000
```

### scheduler_settings tabela

```sql
-- SLA Computation toggles
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('sla.scheduled.daily', true);
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('sla.scheduled.weekly', true);
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('sla.scheduled.monthly', true);

-- SLA Report toggle
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('sla.report.scheduled', true);

-- Email Retry toggle
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('email.retry.scheduled', true);

-- SLA Event Notification toggle
INSERT INTO scheduler_settings (scheduler_task_name, is_enabled) VALUES ('sla.event.notification.scheduled', true);
```

---

## Monitoring

### Log prefixes

```
SlaScheduler::                  — SLA computation scheduler lifecycle
SlaReportScheduler::            — Report scheduler lifecycle
=== DAILY SLA ===               — Daily computation batch
=== WEEKLY SLA ===              — Weekly computation batch
=== MONTHLY SLA ===             — Monthly computation batch
=== Report Scheduler ===        — Report generation batch
=== Email Retry Scheduler ===   — Email retry batch
EMAIL RETRY EXHAUSTED:          — ALERT: email propao posle svih retry-eva
ALERT: N email(s) have exhausted — Batch alert za MAX_RETRIES_REACHED
=== SLA Event Notification === — SLA event notification batch
SLA event notification sent     — Uspešno poslata notifikacija
SLA event notification has no   — Event nema recipients, skip email
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
