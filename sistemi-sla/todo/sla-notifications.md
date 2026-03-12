# G-16: Notifikacije za bitne SLA evente — Analiza i pristup

> **Datum**: 2026-03-12
> **Status**: Analiza / Pre implementacije
> **Effort**: 4-6h (zavisno od pristupa)
> **Backlog ref**: G-16 u `sla-backlog.md`

---

## 1. Postojeća notifikaciona arhitektura u OCI sistemu

### 1.1 Pregled notifikacija u OCI UI

OCI UI ima 4 tipa notifikacija, dostupnih kroz "Notifikacije" dropdown u navigaciji:

```
┌─────────────────────────────────────────────────────────┐
│  Notifikacije ▼                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Notifikacije metrike                              │  │
│  │    Pracenje i izvestavanje stanja metrika.          │  │
│  │    Ukljucuje metricki prazni probitak notifikacije  │  │
│  │                                                    │  │
│  │  SC Notifikacije                                   │  │
│  │    Pregled i kreiranje SC Notifikacija              │  │
│  │                                                    │  │
│  │  Budzet notifikacije                               │  │
│  │    Pregled i kreiranje budzet notifikacija          │  │
│  │                                                    │  │
│  │  Kompartment notifikacije                          │  │
│  │    Pregled i kreiranje notifikacija za              │  │
│  │    odabrane kompartmente                           │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Mapiranje UI → Backend

| UI labela | Backend tip | Entities | Controller (oci-api) | Scheduler (oci-monitor) | Event | Notification Service (oci-monitor) |
|---|---|---|---|---|---|---|
| **Notifikacije metrike** | Metric threshold alerts | MetricNotification, MetricNotificationReports, MetricNotificationVerification | MetricNotificationController | OciNotificationMetricsSchedulerService | MetricsNotificationEvent | MetricsNotificationEventListener (direktno salje email) |
| **SC Notifikacije** | Subscription/Commitment alerts | SCNotification, SCNotificationReports, SCNotificationVerification | SCNotificationController | OciNotificationSCSchedulerService | CommitmentNotificationEvent, SubscriptionNotificationEvent | CommitmentNotificationService, SubscriptionNotificationService |
| **Budzet notifikacije** | Budget threshold alerts | BudgetNotification, BudgetNotificationReports, BudgetNotificationValue, BudgetNotificationVerification | BudgetNotificationController | OciNotificationBudgetSchedulerService | BudgetNotificationEvent | BudgetNotificationService |
| **Kompartment notifikacije** | Compartment budget alerts | BudgetCompartment, BudgetCompartmentReports, BudgetCompartmentValue, BudgetCompartmentEmail | *(nema dedikovanog kontrolera)* | OciNotificationBudgetCompartmentSchedulerService | BudgetCompartmentEvent | BudgetCompartmentService |

### 1.3 Zajednicki pattern: Scheduler → Event → Listener → NotificationService → MailerService

Svi OCI notification tipovi prate isti arhitekturalni pattern:

```
oci-api (Port 8080)                          oci-monitor (Port 8081)
────────────────────                         ──────────────────────────────

[Korisnik] ──POST──► Controller              Scheduler (@Scheduled cron)
                        │                         │
                        ▼                         ▼
                   *Service                  *SchedulerService
                   (CRUD, validacija)         (provera uslova)
                        │                         │
                        ▼                         ▼
                   Repository                ApplicationEventPublisher
                   (save config)              .publishEvent(XxxEvent)
                                                  │
                                                  ▼
                                             XxxEventListener
                                             implements ApplicationListener<XxxEvent>
                                                  │
                                                  ▼
                                             *NotificationService
                                             (build email, iterate recipients)
                                                  │
                                                  ▼
                                             MailerService
                                             .sendTextEmail() / .sendHtmlEmail()
```

**Kljucne karakteristike postojeceg patterna:**
- **oci-api** — samo CRUD operacije nad notification konfiguracijama
- **oci-monitor** — sva logika za evaluaciju uslova i slanje emailova
- **ApplicationEvent** — decoupling izmedju scheduler-a i notification servisa
- **ApplicationListener** — sinhroni (ne `@Async`, ne `@TransactionalEventListener`)
- **Mute mehanizam** — svaki notification tip ima Verification entitet sa `verificationCode` za mute-me/mute-all linkove u emailu
- **Dual email provider** — SMTP i SendGrid, istovremeno aktivan samo jedan (`email.provider` property)
- **Inline retry (Phase 1)** — exponential backoff u MailerService (3 pokusaja, ~20s)

---

## 2. Detaljna backend arhitektura notifikacija

### 2.1 ApplicationEvent klase (7 + 1 u oci-api)

| Event klasa | Modul | Polja | Publisher | Listener |
|---|---|---|---|---|
| `OnRegistrationCompleteEvent` | oci-api | appUrl, user | User registration | RegistrationListener |
| `MetricsNotificationEvent` | oci-monitor | message, MetricNotificationReports (source) | OciNotificationMetricsSchedulerService | MetricsNotificationEventListener |
| `BudgetNotificationEvent` | oci-monitor | message, BudgetNotificationReports (source) | OciNotificationBudgetSchedulerService | BudgetNotificationEventListener |
| `BudgetCompartmentEvent` | oci-monitor | message, List\<ManageableResourceDto\>, BudgetCompartmentReports (source) | OciNotificationBudgetCompartmentSchedulerService | BudgetCompartmentEventListener |
| `CommitmentNotificationEvent` | oci-monitor | message, SCNotificationReports (source) | OciNotificationSCSchedulerService | CommitmentNotificationEventListener |
| `SubscriptionNotificationEvent` | oci-monitor | message, SCNotificationReports (source) | OciNotificationSCSchedulerService | SubscriptionNotificationEventListener |
| `CostReportsEvent` | oci-monitor | message, costReportsNotificationStatus, CostReports (source) | OciCostSchedulerService | CostReportsEventListener |
| **`SlaResultComputedEvent`** | oci-monitor | **slaResultId (UUID)** | SlaComputationService | SlaBreachDetectionService |

**Vazno**: Svi OCI eventi nose ceo entity objekat kao `source` u ApplicationEvent. Jedini izuzetak je `SlaResultComputedEvent` koji nosi samo UUID — namerni pattern jer se listener izvrsava u drugoj transakciji (`AFTER_COMMIT`) pa entity mora biti ponovo ucitan iz baze.

### 2.2 Listener pattern razlike

| Aspekt | OCI notifikacije (6 listener-a) | SLA notifikacije (1 listener) |
|---|---|---|
| **Interfejs** | `implements ApplicationListener<XxxEvent>` | `@TransactionalEventListener(AFTER_COMMIT)` |
| **Async** | Sinhroni (u istom thread-u) | `@Async` (thread pool: sla-async-*) |
| **Transakcija** | U transakciji publisher-a | Posle commit-a publisher-a |
| **Error handling** | Greska u listener-u moze rollback-ovati publisher | Greska je izolovana (AFTER_COMMIT) |
| **Use case** | Notification reports sa statusom koji se azurira | Breach detekcija gde rezultat mora biti persistiran |

### 2.3 MailerService — 4 implementacije (2 per modul)

```
oci-api/                                    oci-monitor/
├── service/email/                          ├── service/email/
│   ├── MailerService (interface)           │   ├── MailerService (interface)
│   ├── SmtpMailerService                   │   ├── SmtpMailerService
│   │   @ConditionalOnProperty(             │   │   @ConditionalOnProperty(
│   │     havingValue="smtp",               │   │     havingValue="smtp",
│   │     matchIfMissing=true)              │   │     matchIfMissing=true)
│   └── SendGridMailerService               │   └── SendGridMailerService
│       @ConditionalOnProperty(             │       @ConditionalOnProperty(
│         havingValue="sendgrid")           │         havingValue="sendgrid")
```

**Inline retry (Phase 1)** — obe implementacije koriste exponential backoff:
- `email.retry.max-attempts=3`
- `email.retry.base-delay-ms=5000`
- `email.retry.multiplier=3.0`
- `email.retry.max-delay-ms=45000`
- Timeline: pokusaj 1 → 5s pauza → pokusaj 2 → 15s pauza → pokusaj 3 (~20s ukupno)

### 2.4 SLA Notification Flow (trenutni — production)

SLA notifikacije koriste `EmailSendLogService` za persistent retry — jedini tip notifikacija u sistemu sa Phase 2 zastitom.

```
SlaComputationService.computeSla()
    │ @Transactional
    ├── AvailabilityCalculatorService.calculateAvailability()
    ├── Determine status (FULFILLED/WARNING/BREACHED/INSUFFICIENT_DATA)
    ├── PenaltyCalculationService.calculatePenalty()
    ├── Save SlaResult
    └── eventPublisher.publishEvent(new SlaResultComputedEvent(slaResultId))
            │
            ▼
SlaBreachDetectionService.onSlaResultComputed()
    │ @Async + @TransactionalEventListener(AFTER_COMMIT)
    │
    ├── Load SlaResult by ID (fresh from DB, new transaction)
    ├── status != BREACHED? → return (skip)
    ├── Already has breach? → return (duplicate prevention)
    │
    ├── detectAndCreateBreach(slaResult):
    │   ├── calculateSeverity()
    │   │   ├── deviation >= 5%  → CRITICAL
    │   │   ├── deviation >= 3%  → HIGH
    │   │   ├── deviation >= 1%  → MEDIUM
    │   │   └── deviation < 1%  → LOW
    │   ├── calculateDeviation() → (target - actual) / target * 100
    │   ├── generateBreachDescription()
    │   └── Save SlaBreach entity
    │
    └── sendNotifications(breach):
            │
            ├── SlaNotificationService.sendEmailNotification(breach, recipients)
            │   │
            │   └── Per recipient:
            │       └── EmailSendLogService.sendEmailWithPersistence(request, false, "SLA_BREACH", breachId)
            │           │
            │           ├── Phase 1: MailerService.sendTextEmail() — 3 inline pokusaja (~20s)
            │           │   ├── SUCCESS → return response
            │           │   └── ALL FAILED → logFailedSend() → save to email_send_log (FAILED)
            │           │
            │           └── Phase 2: EmailRetryScheduler (svaki 5 min)
            │               └── EmailSendLogService.processRetryableEmails()
            │                   ├── SUCCESS → markSent()
            │                   └── FAIL → backoff → MAX_RETRIES_REACHED → log.error alert
            │
            └── SlaNotificationService.sendWebhookNotification(breach, webhookUrl)
                └── MOCK — samo loguje (TODO: G-07)
```

### 2.5 Email Retry infrastruktura (Phase 1 + Phase 2)

| Komponenta | Lokacija | Uloga |
|---|---|---|
| `EmailSendLog` entity | oci-library | BIGINT PK, standalone. Polja: recipient, subject, body, isHtml, status, retryCount, maxRetries, nextRetryAt, errorMessage, source, sourceEntityId |
| `EmailSendStatus` enum | oci-library | PENDING, SENT, FAILED, MAX_RETRIES_REACHED |
| `EmailSendLogRepository` | oci-monitor | `findRetryableEmails(now)` — PENDING/FAILED + nextRetryAt <= now + retryCount < maxRetries |
| `EmailSendLogService` | oci-monitor | `sendEmailWithPersistence()` + `processRetryableEmails()` |
| `EmailRetryScheduler` | oci-monitor | `@Scheduled(fixedDelay=5min)` + `@SchedulerLock` + `SchedulerToggleService` |
| `email_send_log` tabela | Flyway dev V12, prod V6 | MySQL tabela |

**Scheduled retry backoff:**
```
Retry 1:  T+5min      (5 * 3^0)
Retry 2:  T+20min     (5 * 3^1 = 15min later)
Retry 3:  T+1h5min    (5 * 3^2 = 45min later)
Retry 4:  T+3h20min   (5 * 3^3 = 135min later)
Retry 5:  T+9h20min   (5 * 3^4 = 360min = 6h cap)
```

**Trenutni consumeri**: samo `SlaNotificationService` (source=`"SLA_BREACH"`).

### 2.6 Cross-module komunikacija

oci-api i oci-monitor su **zasebni procesi** sa zasebnim Spring context-ima. Komunikacija:

1. **Shared DB** — oba modula citaju/pisu istu MySQL bazu (entiteti u oci-library)
2. **REST poziv** — oci-api poziva oci-monitor putem `MonitorApiService` (RestTemplate)
3. **Spring events** — rade samo unutar jednog procesa, ne propagiraju se cross-module

Za G-16 ovo je kljucno pitanje jer:
- **User akcije** (deactivate, delete, acknowledge, resolve, schedule status) se izvrsavaju u **oci-api**
- **SlaNotificationService** i **EmailSendLogService** zive u **oci-monitor**
- Report generated event se izvrsava u **oci-monitor** (lokalno)

### 2.7 Kompletna scheduler infrastruktura (15 schedulera)

```
VREME/INTERVAL    SCHEDULER                                           TOGGLE KEY
──────────────────────────────────────────────────────────────────────────────────
svaki 5min        OciDataScheduler                                     oci.data.scheduled
svaki 5min        OciNotificationMetricsSchedulerService                metric.notification.scheduled
svaki 10min       OciNotificationBudgetSchedulerService                 budget.notification.scheduled
svaki 10min       OciNotificationBudgetCompartmentSchedulerService      compartment.notification.scheduled
svaki 10min       OciNotificationSCSchedulerService                     sc.notification.scheduled
svaki 30min       OciCostSchedulerService                               cost.scheduled
svaki sat         OciAggregateTenantUsageSchedulerService                aggregate.tenant.usage.scheduled
svaki sat         OciAggregateBillingReportSchedulerService              aggregate.billing.report.scheduled
svaki sat         OciAggregateCompartmentConsumptionSchedulerService     aggregate.compartment.scheduled
svaki sat         OciAggregateTenantConsumptionSchedulerService          aggregate.tenant.consumption.scheduled
00:05             SlaScheduler.scheduleDailySlas()                       sla.scheduled.daily
00:10 (MON)       SlaScheduler.scheduleWeeklySlas()                     sla.scheduled.weekly
00:15 (1st)       SlaScheduler.scheduleMonthlySlas()                    sla.scheduled.monthly
00:30             SlaReportScheduler.processScheduledReports()          sla.report.scheduled
svaki 5min        EmailRetryScheduler.processFailedEmails()             email.retry.scheduled
```

---

## 3. Trenutno stanje SLA notifikacija

### 3.1 Postojeca SLA event arhitektura

Sistem ima **1 SLA ApplicationEvent** i **1 listener** (+ EmailRetryScheduler):

```
SlaComputationService.computeSla()
    │
    └── eventPublisher.publishEvent(SlaResultComputedEvent(slaResultId))
            │
            ▼
SlaBreachDetectionService                  @Async + @TransactionalEventListener(AFTER_COMMIT)
    │
    ├── status != BREACHED? → skip
    │
    └── status == BREACHED
            ├── detectAndCreateBreach()
            └── sendNotifications()
                    │
                    └── SlaNotificationService
                            ├── sendEmailNotification()     ← radi (via EmailSendLogService)
                            └── sendWebhookNotification()   ← MOCK (TODO: G-07)
```

### 3.2 State-modifying operacije (kandidati za notifikacije)

Od ukupno 56 endpointa, **14 menja stanje** i potencijalno treba notifikaciju:

| Kategorija | Operacija | Endpoint | Modul | Prioritet |
|---|---|---|---|---|
| **SLA Definition** | Kreiranje | POST `/definitions` | oci-api | Nizak |
| | Izmena | PUT `/definitions/{id}` | oci-api | Nizak |
| | Deaktivacija | PATCH `/definitions/{id}/deactivate` | oci-api | **Visok** |
| | Brisanje | DELETE `/definitions/{id}` | oci-api | **Visok** |
| **Breach** | Acknowledge | PATCH `/breaches/{id}/acknowledge` | oci-api | **Srednji** |
| | Resolve | PATCH `/breaches/{id}/resolve` | oci-api | **Srednji** |
| **Excluded Downtime** | Kreiranje | POST `/{slaId}/excluded-downtimes` | oci-api | Nizak |
| | Izmena | PUT `/excluded-downtimes/{id}` | oci-api | Nizak |
| | Brisanje | DELETE `/excluded-downtimes/{id}` | oci-api | Nizak |
| **Report Schedule** | Kreiranje | POST `/report-schedules` | oci-api | Nizak |
| | Activate/Deactivate | PATCH `/report-schedules/{id}/status` | oci-api | **Srednji** |
| | Brisanje | DELETE `/report-schedules/{id}` | oci-api | Nizak |
| **Execution** | Manual trigger | POST `/trigger` | oci-api→oci-monitor | Nizak |
| | Archive report | POST `/reports/{id}/archive` | oci-api | Nizak |

### 3.3 Prioritetni eventi za Phase 1

Na osnovu poslovnog uticaja, **6 evenata** je najvaznije:

```
 VISOK PRIORITET                         SREDNJI PRIORITET
 ┌─────────────────────────┐             ┌──────────────────────────────┐
 │ 1. SLA Definition       │             │ 3. Breach acknowledged       │
 │    deactivated           │             │ 4. Breach resolved           │
 │ 2. SLA Definition       │             │ 5. Report schedule           │
 │    deleted               │             │    activated/deactivated     │
 └─────────────────────────┘             │ 6. Report generation         │
                                          │    completed                 │
                                          └──────────────────────────────┘
```

### 3.4 Postojeca infrastruktura za reuse

| Komponenta | Lokacija | Status |
|---|---|---|
| `ApplicationEventPublisher` | SlaComputationService | Radi — publishuje SlaResultComputedEvent |
| `SlaNotificationService` | oci-monitor | Radi — `sendEmailNotification()` via EmailSendLogService |
| `EmailSendLogService` | oci-monitor | Radi — Phase 1 + Phase 2 persistent retry |
| `MailerService` (SMTP/SendGrid) | oci-monitor + oci-api | Radi — Phase 1 inline retry u oba modula |
| `MonitorApiService` | oci-api | Radi — REST pozivi ka oci-monitor (RestTemplate) |
| `@Async` thread pool | oci-monitor | Konfigurisan — 4-8 thread-ova, sla-async-* prefix |
| `@TransactionalEventListener` | SlaBreachDetectionService | Production pattern |
| `SlaDefinition.notificationRecipientEmails` | oci-library entity | Comma-separated email lista |
| `SlaBreach` notification fields | oci-library entity | notificationSent, sentAt, failureReason |

---

## 4. Koji eventi i kome?

### 4.1 Event → Recipient matrica

| Event | Recipient | Razlog |
|---|---|---|
| SLA deactivated | `definition.notificationRecipientEmails` | Stakeholder-i moraju znati da SLA vise nije aktivan |
| SLA deleted | `definition.notificationRecipientEmails` | Stakeholder-i moraju znati da SLA ne postoji |
| Breach acknowledged | `definition.notificationRecipientEmails` | Tim zna da je neko preuzeo odgovornost |
| Breach resolved | `definition.notificationRecipientEmails` | Tim zna da je problem resen |
| Schedule activated/deactivated | `definition.notificationRecipientEmails` | Informacija o promeni reporting rezima |
| Report generated | `schedule.recipientEmails` | Izvestaj dostupan za pregled |

### 4.2 Event payload (zajednicko)

```
Subject:  [EVENT_TYPE] SLA event — {slaDefinitionName}
Body:
  - Event type (human-readable)
  - SLA Definition name
  - Timestamp
  - Actor (ko je izvrsio akciju)
  - Event-specific detalji
  - Link ka UI (opciono)
```

---

## 5. Pristupi

### 5.1 Pristup A: Direct Notification via REST ka oci-monitor (PREPORUKA)

Dodati REST endpoint na oci-monitor za slanje SLA event notifikacija. oci-api poziva taj endpoint putem `MonitorApiService` — isti pattern kao `triggerSlaComputation()`. Sve notifikacije prolaze kroz `EmailSendLogService` i dobijaju Phase 1 + Phase 2 persistent retry.

#### Dijagram

```
oci-api                                              oci-monitor
────────                                             ───────────

SlaController                                        SlaEventNotificationController
    │                                                    │
    ├── deactivate(id)                                   │
    │       │                                            │
    │       ▼                                            │
    │   SlaService                                       │
    │       ├── deactivateDefinition()                   │
    │       └── monitorApiService                        │
    │              .sendSlaEventNotification(             │
    │                 type, name, recipients,             │
    │                 actor, details)                     │
    │                     │                              │
    │                     │  POST /monitoring/sla/        │
    │                     │       event-notification      │
    │                     │──────────────────────────────►│
    │                     │                              ▼
    │                     │                    SlaNotificationService
    │                     │                      .sendEventNotification()
    │                     │                              │
    │                     │                              ▼
    │                     │                    EmailSendLogService
    │                     │                      .sendEmailWithPersistence()
    │                     │                              │
    │                     │                    ┌─────────┴──────────┐
    │                     │                    │ Phase 1: inline    │
    │                     │                    │ Phase 2: scheduled │
    │                     │                    └────────────────────┘
    │                     │◄── 200 OK ─────────────────────
    │◄── 200 OK ──────────┤
```

#### Implementacija

**1. `SlaEventType` enum (oci-library):**

```java
@Getter
@AllArgsConstructor
@Schema(description = "SLA event types for notifications")
public enum SlaEventType {
    SLA_DEACTIVATED("SLA Deactivated", "SLA definition has been deactivated"),
    SLA_DELETED("SLA Deleted", "SLA definition has been permanently deleted"),
    BREACH_ACKNOWLEDGED("Breach Acknowledged", "SLA breach has been acknowledged"),
    BREACH_RESOLVED("Breach Resolved", "SLA breach has been resolved"),
    SCHEDULE_ACTIVATED("Schedule Activated", "Report schedule has been activated"),
    SCHEDULE_DEACTIVATED("Schedule Deactivated", "Report schedule has been deactivated"),
    REPORT_GENERATED("Report Generated", "SLA report has been generated");

    private final String displayName;
    private final String description;
}
```

**2. `SlaEventNotificationRequestDTO` (oci-library):**

```java
@Data @Builder
@Schema(description = "Request DTO for SLA event notification")
public class SlaEventNotificationRequestDTO {
    @Schema(description = "Event type") private SlaEventType eventType;
    @Schema(description = "SLA definition name") private String slaDefinitionName;
    @Schema(description = "Comma-separated recipients") private String recipients;
    @Schema(description = "Username who triggered the action") private String actor;
    @Schema(description = "Event-specific details") private Map<String, String> details;
}
```

**3. Endpoint u oci-monitor:**

```java
@Slf4j @RequiredArgsConstructor @RestController
@RequestMapping("/monitoring/sla")
public class SlaEventNotificationController {
    private final SlaNotificationService slaNotificationService;

    @PostMapping("/event-notification")
    public ResponseEntity<Void> sendEventNotification(
            @Valid @RequestBody SlaEventNotificationRequestDTO request) {
        slaNotificationService.sendEventNotification(
            request.getEventType(),
            request.getSlaDefinitionName(),
            request.getRecipients(),
            request.getActor(),
            request.getDetails()
        );
        return ResponseEntity.ok().build();
    }
}
```

**4. `sendEventNotification()` u `SlaNotificationService` (oci-monitor):**

```java
public void sendEventNotification(SlaEventType eventType, String slaDefinitionName,
        String recipients, String actor, Map<String, String> details) {
    if (StringUtils.isBlank(recipients)) {
        log.info("No recipients for {} event on SLA: {}", eventType, slaDefinitionName);
        return;
    }

    String subject = buildEventSubject(eventType, slaDefinitionName);
    String body = buildEventBody(eventType, slaDefinitionName, actor, details);
    String source = "SLA_EVENT_" + eventType.name();
    String sourceEntityId = details != null ? details.getOrDefault("entityId", null) : null;

    for (String recipient : recipients.split(",")) {
        String trimmedRecipient = recipient.trim();
        try {
            emailSendLogService.sendEmailWithPersistence(
                SendEmailRequestDto.builder()
                    .to(trimmedRecipient)
                    .subject(subject)
                    .body(body)
                    .build(),
                false, source, sourceEntityId);
        } catch (Exception e) {
            log.warn("Failed to send {} notification to {}: {}",
                eventType, trimmedRecipient, e.getMessage());
        }
    }
}
```

**5. Poziv iz `MonitorApiService` (oci-api):**

```java
public void sendSlaEventNotification(SlaEventNotificationRequestDTO request) {
    restTemplate.postForEntity(
        monitorBaseUrl + "/monitoring/sla/event-notification",
        request, Void.class);
}
```

**6. Pozivi u servisima (oci-api):**

```java
// SlaService.deactivateDefinition()
slaDefinitionManagementService.deactivateDefinition(id);
monitorApiService.sendSlaEventNotification(SlaEventNotificationRequestDTO.builder()
    .eventType(SlaEventType.SLA_DEACTIVATED)
    .slaDefinitionName(definition.getName())
    .recipients(definition.getNotificationRecipientEmails())
    .actor(AuthHelper.getPrincipalUsername("system"))
    .details(Map.of("definitionUuid", definition.getUuid().toString()))
    .build());

// SlaService.deleteSlaDefinition()
// VAZNO: recipients preuzeti PRE brisanja
String recipients = existing.getNotificationRecipientEmails();
String name = existing.getName();
slaDefinitionManagementService.deleteSlaDefinition(id, deletedBy);
monitorApiService.sendSlaEventNotification(SlaEventNotificationRequestDTO.builder()
    .eventType(SlaEventType.SLA_DELETED)
    .slaDefinitionName(name)
    .recipients(recipients)
    .actor(deletedBy)
    .build());
```

**7. Report generated — lokalno u oci-monitor (bez REST poziva):**

```java
// SlaReportGenerationService.generateReport()
// ... generisanje ...
slaNotificationService.sendEventNotification(
    SlaEventType.REPORT_GENERATED,
    schedule.getSlaDefinition().getName(),
    schedule.getRecipientEmails(),
    "scheduler",
    Map.of("reportName", report.getReportName()));
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Sloznost | Niska-Srednja |
| Effort | **4-5h** |
| Rizik | Nizak — koristi postojece MonitorApiService pattern |
| Fajlovi | Enum + RequestDTO (oci-library), Controller + SlaNotificationService izmena (oci-monitor), MonitorApiService + 3 servisa (oci-api) |
| Flyway | Ne |
| Email retry | **Phase 1 + Phase 2** — sve notifikacije prolaze kroz EmailSendLogService |

#### Prednosti

- **Full Phase 1 + Phase 2 retry** — sve notifikacije imaju persistent retry via EmailSendLogService
- **Centralizovano** — sva notification logika u SlaNotificationService (oci-monitor), jedno mesto za maintain
- **Existing pattern** — MonitorApiService vec koristi REST za `triggerSlaComputation()`
- **Eksplicitan** — jasno se vidi u kodu gde se salje notifikacija
- **Testabilan** — mock MonitorApiService u oci-api testovima, mock SlaNotificationService u oci-monitor testovima
- **Vidljivost** — svi emailovi u `email_send_log` tabeli sa `source = SLA_EVENT_*`
- **Multi-instance safe** — EmailRetryScheduler koristi ShedLock

#### Mane / Ogranicenja

- **REST dependency** — ako oci-monitor nije dostupan, notifikacija ne prolazi (ali MonitorApiService vec ima error handling)
- **Tight coupling** — servisni sloj direktno poziva MonitorApiService
- **Sinhrono za caller** — REST poziv blokira response dok oci-monitor ne odgovori (ali email se salje async iz oci-monitor perspektive — odmah se vraca nakon INSERT u email_send_log ili uspesnog slanja)
- **Nema centralizovane event log** — dogadjaji se ne cuvaju nigde (samo email_send_log za email deliverability)

---

### 5.2 Pristup B: ApplicationEvent per operacija

Dedicirane `ApplicationEvent` klase za svaki tip operacije. Listener-i reaguju na evente i salju notifikacije.

**Cross-module ogranicenje**: Spring event bus je per-process. Potrebna su **dva listener-a** — jedan u oci-api (za user-initiated evente) i jedan u oci-monitor (za report generated). Listener u oci-api koristi lokalni MailerService (samo Phase 1), listener u oci-monitor koristi EmailSendLogService (Phase 1 + 2).

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Sloznost | Srednja |
| Effort | **4-6h** |
| Email retry | **Mesovito** — oci-api eventi samo Phase 1, oci-monitor eventi Phase 1+2 |
| Fajlovi | 6 event klasa + 1 bazna (oci-library) + 2 listener-a (oci-api + oci-monitor) + enum + 3 servisa |
| Flyway | Ne |

#### Prednosti / Mane

- (+) Loose coupling — servisi ne znaju za notifikacije, publishuju event
- (+) Extensible — lako dodati nove listener-e
- (+) Async — `@Async` + `AFTER_COMMIT` ne blokira request
- (-) **Nekonzistentan retry** — oci-api eventi nemaju Phase 2 persistent retry
- (-) 6-7 novih event klasa (boilerplate)
- (-) AFTER_COMMIT za DELETE — entity vise ne postoji
- (-) Dva listener-a u dva modula za maintain

---

### 5.3 Pristup C: Genericki SlaEvent + Event Type enum

Jedna genericka `SlaEvent` klasa sa `eventType` poljem. Kompromis izmedju A i B.

**Cross-module**: Isti problem kao Pristup B — dva listener-a, nekonzistentan retry.

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Sloznost | Niska-Srednja |
| Effort | **3-4h** |
| Email retry | **Mesovito** — isti problem kao B |
| Fajlovi | 1 event klasa + 1 listener per modul + enum |
| Flyway | Ne |

#### Prednosti / Mane

- (+) Jedna event klasa — nema boilerplate-a
- (+) Loose coupling, extensible
- (-) **Nekonzistentan retry** — oci-api eventi samo Phase 1
- (-) Type-unsafe details (`Map<String, String>`)
- (-) Dva listener-a za maintain

---

### 5.4 Pristup D: Event Log tabela + Scheduled Notification

Svaka state-modifying operacija loguje event u `sla_event_log` tabelu. Scheduled job u oci-monitor cita nove evente, salje notifikacije via EmailSendLogService i markira kao notified.

**Cross-module resenje**: Prirodno — oci-api pise u shared tabelu (INSERT), oci-monitor cita iz nje (SELECT). Nema REST poziva niti event propagacije.

#### Dijagram

```
oci-api                            sla_event_log              oci-monitor
────────                           (shared MySQL)             ───────────

SlaService                              │              SlaEventNotificationScheduler
    │                                   │              @Scheduled(fixedDelay=1min)
    ├── deactivate()                    │              @SchedulerLock
    │   ├── save(definition)            │                      │
    │   └── slaEventLogService          │                      │
    │       .logEvent(type, id,         │                      │
    │        name, recipients,          │                      │
    │        actor, details)            │                      │
    │           │                       │                      │
    │           └── INSERT ────────────►│                      │
    │              (notified=false)      │                      │
    │                                   │◄── SELECT WHERE ─────┤
    │                                   │    notified=false     │
    │                                   │                      │
    │                                   │                      ├── EmailSendLogService
    │                                   │                      │   .sendEmailWithPersistence()
    │                                   │                      │
    │                                   │◄── UPDATE SET ───────┤
    │                                   │    notified=true      │
```

#### Potrebne izmene

**1. Flyway migracija:**

```sql
CREATE TABLE sla_event_log (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_type  VARCHAR(50) NOT NULL,
    entity_id   VARCHAR(36) NOT NULL,
    entity_name VARCHAR(255),
    recipients  TEXT,
    actor       VARCHAR(100),
    details     TEXT,           -- JSON
    notified    BOOLEAN NOT NULL DEFAULT FALSE,
    notified_at DATETIME NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_pending (notified, created_at)
);
```

**2. Entity (oci-library), Repository (oci-monitor + oci-api), LogService (oci-api), Scheduler (oci-monitor)**

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Sloznost | Srednja-Visoka |
| Effort | **6-8h** |
| Email retry | **Phase 1 + Phase 2** — sve kroz EmailSendLogService u oci-monitor |
| Fajlovi | Flyway + Entity (oci-library) + Repository + Scheduler (oci-monitor) + LogService (oci-api) |
| Flyway | **Da** — nova tabela |

#### Prednosti / Mane

- (+) **Audit trail** — svaki event trajno u bazi, queryable
- (+) **Cross-module natural** — shared DB, nema REST dependency
- (+) **Persistent** — prezivljava restart oba modula
- (+) **Full Phase 1+2 retry** — sve kroz EmailSendLogService
- (+) **Decoupled** — INSERT je brz (<1ms), slanje je async
- (-) **Nova tabela** — Flyway migracija, novi entity, novi repository
- (-) **Delay** — notifikacija kasni do 1 minut
- (-) **DB rast** — tabela raste (potreban cleanup job)
- (-) **Novi scheduler** — 16. scheduler u sistemu, operativni overhead

---

## 6. Uporedna tabela

| Kriterijum | A: Direct + REST | B: Event per tip | C: Generic Event | D: Event Log |
|---|---|---|---|---|
| **Sloznost** | Niska-Srednja | Srednja | Niska-Srednja | Srednja-Visoka |
| **Effort** | 4-5h | 4-6h | 3-4h | 6-8h |
| **Nove klase** | enum + DTO + controller | 7 events + 2 listeners | event + enum + 2 listeners | entity + repo + scheduler + service |
| **Flyway** | Ne | Ne | Ne | Da |
| **Email retry** | **Phase 1+2 (sve)** | Mesovito (api=P1, monitor=P1+2) | Mesovito | **Phase 1+2 (sve)** |
| **Cross-module** | REST (MonitorApiService) | 2 listener-a | 2 listener-a | Shared DB (natural) |
| **Async** | Da (EmailSendLogService) | Da (@Async) | Da (@Async) | Da (scheduled) |
| **Audit trail** | Ne (samo email_send_log) | Ne | Ne | **Da** |
| **Extensible** | Srednje | Visoko | Visoko | Visoko |
| **Existing pattern** | Da (MonitorApiService) | Da (ApplicationEvent) | Da (ApplicationEvent) | Nov pattern |
| **Testabilnost** | Visoka | Visoka | Visoka | Srednja |

---

## 7. Preporuka: Pristup A — Direct Notification via REST

### Zasto Pristup A?

**Kljucni argumenti:**

1. **Konzistentan Phase 1+2 retry za SVE notifikacije** — svaki email prolazi kroz EmailSendLogService u oci-monitor. Pristup B i C imaju problem da oci-api eventi dobijaju samo Phase 1 retry jer EmailSendLogService ne postoji u oci-api.

2. **Existing pattern** — MonitorApiService vec koristi REST pozive za `triggerSlaComputation()`. Dodavanje `sendSlaEventNotification()` je prirodno prosirenje. Nema novog infrastrukturnog patterna.

3. **Centralizovana notification logika** — `SlaNotificationService` u oci-monitor je jedino mesto gde se gradi email subject/body, poziva EmailSendLogService, i loguje rezultate. Nema duplirane logike u oci-api.

4. **Bez migracije** — ne zahteva novu tabelu niti promenu DB seme. Pristup D zahteva Flyway + entity + repository.

5. **Eksplicitnost** — jasno se vidi u kodu gde i zasto se salje notifikacija. Nema indirekcije (publish → event bus → listener → notification). Za debugging i code review — jasan tok.

6. **SOLID: Single Responsibility** — SlaService je odgovoran za business logiku, delegira notification ka MonitorApiService. SlaNotificationService je odgovoran za slanje emailova. Svako radi svoj posao.

**Pristup A vs D:**

Pristup D (Event Log) je robusniji jer ne zavisi od REST komunikacije i ima audit trail. Medjutim:
- REST dependency izmedju oci-api i oci-monitor vec postoji i funkcionise u produkciji
- Audit trail evenata nije trenutni zahtev (moze se dodati naknadno)
- Pristup D uvodi novu tabelu, novi scheduler (16.), i delay do 1 min
- Ako se u buducnosti pokaze da je audit trail neophodan, migracija sa A na D je jednostavna — pozivi u servisima se zamene sa INSERT u tabelu

**Kada upgrade-ovati:**
- Na **Pristup D** — ako se zahteva audit trail evenata ili ako REST dependency postane problem
- Na **Pristup B/C** — ako se uvede webhook kanal (G-07) i treba centralizovani event bus za vise kanala

### Napomena o REST dependency

`MonitorApiService` poziv ka oci-monitor moze da ne prodje ako je oci-monitor nedostupan. U tom slucaju:
- Notifikacija se **nece poslati** (email se ne loguje u email_send_log)
- User akcija (deactivate, delete, itd.) **ce se uspesno zavrsiti** — notifikacija se salje u try/catch bloku, ne utice na primarnu operaciju
- Log warning se emituje

Ovo je prihvatljiv trade-off jer:
- oci-api i oci-monitor u produkciji rade paralelno i medjusobno zavise (monitoring, triggering)
- Ako oci-monitor nije dostupan, onda ni breach notifikacije ne rade — problem je siri od G-16
- U multi-instance deploymentu sa load balancerom, nedostupnost je vrlo retka

---

## 8. Implementacioni plan (Pristup A)

### Korak 1: Kreirati `SlaEventType` enum i `SlaEventNotificationRequestDTO` u oci-library

`oci-library/dto/sla/SlaEventNotificationRequestDTO.java` + `oci-library/entity/sla/SlaEventType.java`

### Korak 2: Dodati `sendEventNotification()` u `SlaNotificationService` (oci-monitor)

Genericka metoda — prima eventType, slaDefinitionName, recipients, actor, details. Gradi subject i body po event tipu, salje kroz EmailSendLogService per recipient.

### Korak 3: Dodati REST endpoint u oci-monitor

`POST /monitoring/sla/event-notification` — prima `SlaEventNotificationRequestDTO`, delegira na `SlaNotificationService.sendEventNotification()`.

### Korak 4: Dodati `sendSlaEventNotification()` u `MonitorApiService` (oci-api)

REST poziv ka oci-monitor endpoint-u.

### Korak 5: Dodati pozive u servisni sloj (oci-api + oci-monitor)

| Servis | Modul | Metod | Event |
|--------|-------|-------|-------|
| `SlaService` | oci-api | `deactivateDefinition()` | `SLA_DEACTIVATED` |
| `SlaService` | oci-api | `deleteSlaDefinition()` | `SLA_DELETED` |
| `SlaService` | oci-api | `acknowledgeBreach()` | `BREACH_ACKNOWLEDGED` |
| `SlaService` | oci-api | `resolveBreach()` | `BREACH_RESOLVED` |
| `SlaReportScheduleService` | oci-api | `updateScheduleStatus()` | `SCHEDULE_ACTIVATED` / `SCHEDULE_DEACTIVATED` |
| `SlaReportGenerationService` | oci-monitor | `generateReport()` | `REPORT_GENERATED` (lokalno, bez REST) |

### Fajlovi koji se menjaju:

| Fajl | Modul | Izmena |
|------|-------|--------|
| `SlaEventType.java` | **oci-library** | **NOVO** — enum sa 7 vrednosti |
| `SlaEventNotificationRequestDTO.java` | **oci-library** | **NOVO** — request DTO |
| `SlaEventNotificationController.java` | **oci-monitor** | **NOVO** — REST endpoint |
| `SlaNotificationService.java` | oci-monitor | Dodati `sendEventNotification()` + `buildEventSubject()` + `buildEventBody()` |
| `MonitorApiService.java` | oci-api | Dodati `sendSlaEventNotification()` |
| `SlaService.java` | oci-api | 4 poziva (deactivate, delete, acknowledge, resolve) |
| `SlaReportScheduleService.java` | oci-api | 1 poziv (status change) |
| `SlaReportGenerationService.java` | oci-monitor | 1 poziv (report generated — lokalno) |

### Email format primeri

**Subject**: `[SLA Deactivated] Production API Availability`

**Body**:
```
SLA Event Notification
━━━━━━━━━━━━━━━━━━━━━

Event:       SLA Definition Deactivated
SLA Name:    Production API Availability
Performed by: admin@sistemi.rs
Time:        2026-03-12 14:30:00 UTC

This SLA definition has been deactivated and will no longer
be monitored. No further computations will be performed.

---
This is an automated notification from OCI SLA Management.
```

---

## 9. Frontend

Frontend za G-16 je minimalan — nema novih stranica ni komponenti. Notifikacije su email-only.

**Opciono za buducnost** (van scope-a G-16):
- Toast/snackbar u UI kad se breach acknowledge/resolve
- Notification center u navigaciji (po uzoru na OCI UI dropdown)
- WebSocket push za real-time obavestenja

---

## 10. Buduca unapredjenja (van scope-a G-16)

| Stavka | Pristup | Trigger |
|--------|---------|---------|
| Webhook kanal | Dodati webhook poziv u SlaNotificationService.sendEventNotification() | G-07 implementacija |
| Audit event log | Migracija na Pristup D | Compliance/audit zahtev |
| Notification preferences | Per-SLA + per-event config tabela | Korisnici zele kontrolu |
| Mute mehanizam | Verification entity + mute linkovi u emailu | Po uzoru na OCI notification pattern |
| Slack/Teams integration | Novi kanal u SlaNotificationService | Enterprise zahtev |
| Email template (HTML) | Thymeleaf template umesto plain text | UX zahtev |
| Digest/summary email | Scheduled batch umesto per-event | Volume >100 event/dan |
