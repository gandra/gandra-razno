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
│  │ 📊 Notifikacije metrike                           │  │
│  │    Praćenje i izveštavanje stanja metrika.         │  │
│  │    Uključuje metrički pražni probitak notifikacije │  │
│  │                                                    │  │
│  │ 🔔 SC Notifikacije                                │  │
│  │    Pregled i kreiranje SC Notifikacija             │  │
│  │                                                    │  │
│  │ 💰 Budžet notifikacije                             │  │
│  │    Pregled i kreiranje budžet notifikacija         │  │
│  │                                                    │  │
│  │ 🏢 Kompartment notifikacije                        │  │
│  │    Pregled i kreiranje notifikacija za             │  │
│  │    odabrane kompartmente                           │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Mapiranje UI → Backend

| UI labela | Backend tip | Entities | Controller (oci-api) | Scheduler (oci-monitor) | Event | Notification Service (oci-monitor) |
|---|---|---|---|---|---|---|
| **Notifikacije metrike** | Metric threshold alerts | MetricNotification, MetricNotificationReports, MetricNotificationVerification | MetricNotificationController | OciNotificationMetricsSchedulerService | MetricsNotificationEvent | MetricsNotificationEventListener (direktno šalje email) |
| **SC Notifikacije** | Subscription/Commitment alerts | SCNotification, SCNotificationReports, SCNotificationVerification | SCNotificationController | OciNotificationSCSchedulerService | CommitmentNotificationEvent, SubscriptionNotificationEvent | CommitmentNotificationService, SubscriptionNotificationService |
| **Budžet notifikacije** | Budget threshold alerts | BudgetNotification, BudgetNotificationReports, BudgetNotificationValue, BudgetNotificationVerification | BudgetNotificationController | OciNotificationBudgetSchedulerService | BudgetNotificationEvent | BudgetNotificationService |
| **Kompartment notifikacije** | Compartment budget alerts | BudgetCompartment, BudgetCompartmentReports, BudgetCompartmentValue, BudgetCompartmentEmail | *(nema dedikovanog kontrolera)* | OciNotificationBudgetCompartmentSchedulerService | BudgetCompartmentEvent | BudgetCompartmentService |

### 1.3 Zajednički pattern: Scheduler → Event → Listener → NotificationService → MailerService

Svi OCI notification tipovi prate isti arhitekturalni pattern. Korisnik kreira notifikacionu konfiguraciju (pravilo) kroz oci-api REST endpoint, a oci-monitor scheduler periodično proverava uslove i šalje obaveštenja.

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

**Ključne karakteristike postojećeg patterna:**
- **oci-api** — samo CRUD operacije nad notification konfiguracijama (create, list, delete)
- **oci-monitor** — sva logika za evaluaciju uslova i slanje emailova
- **ApplicationEvent** — decoupling između scheduler-a i notification servisa
- **ApplicationListener** — sinhroni (ne `@Async`, ne `@TransactionalEventListener`)
- **Mute mehanizam** — svaki notification tip ima Verification entitet sa `verificationCode` za mute-me/mute-all linkove u emailu
- **Dual email provider** — SMTP i SendGrid, istovremeno aktivan samo jedan (`email.provider` property)

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

**Važno**: Svi OCI eventi nose ceo entity objekat kao `source` u ApplicationEvent. Jedini izuzetak je `SlaResultComputedEvent` koji nosi samo UUID — to je namerni pattern jer se listener izvršava u drugoj transakciji (`AFTER_COMMIT`) pa entity mora biti ponovo učitan iz baze.

### 2.2 Listener pattern razlike

| Aspekt | OCI notifikacije (6 listener-a) | SLA notifikacije (1 listener) |
|---|---|---|
| **Interfejs** | `implements ApplicationListener<XxxEvent>` | `@TransactionalEventListener(AFTER_COMMIT)` |
| **Async** | Sinhroni (u istom thread-u) | `@Async` (thread pool: sla-async-*) |
| **Transakcija** | U transakciji publisher-a | Posle commit-a publisher-a |
| **Error handling** | Greška u listener-u može rollback-ovati publisher | Greška je izolirana (AFTER_COMMIT) |
| **Use case** | Notification reports sa statusom koji se ažurira | Breach detekcija gde rezultat mora biti persistiran |

### 2.3 MailerService — 4 implementacije (2 per modul)

```
oci-api/                                    oci-monitor/
├── service/email/                          ├── service/email/
│   ├── MailerService (interface)           │   ├── MailerService (interface)
│   ├── SmtpMailerService                   │   ├── SmtpMailerService
│   │   @ConditionalOnProperty(             │   │   @ConditionalOnProperty(
│   │     prefix="email",                   │   │     prefix="email",
│   │     name="provider",                  │   │     name="provider",
│   │     havingValue="smtp",               │   │     havingValue="smtp",
│   │     matchIfMissing=true)              │   │     matchIfMissing=true)
│   └── SendGridMailerService               │   └── SendGridMailerService
│       @ConditionalOnProperty(             │       @ConditionalOnProperty(
│         prefix="email",                   │         prefix="email",
│         name="provider",                  │         name="provider",
│         havingValue="sendgrid")           │         havingValue="sendgrid")
```

**Interface:**
```java
public interface MailerService {
    EmailSendResponseDto sendTextEmail(SendEmailRequestDto request);
    EmailSendResponseDto sendHtmlEmail(SendEmailRequestDto request);
}
```

**Inline retry (Phase 1)** — oba implementacija koriste exponential backoff:
- `email.retry.max-attempts=3` (default)
- `email.retry.base-delay-ms=5000` (5 sekundi)
- `email.retry.multiplier=3.0`
- `email.retry.max-delay-ms=45000` (45 sekundi)
- Timeline: pokušaj 1 → 5s pauza → pokušaj 2 → 15s pauza → pokušaj 3 (~20s ukupno)

### 2.4 SLA Notification Flow (trenutni)

SLA notifikacije imaju jedinstven flow u sistemu — jedini tip koji koristi `EmailSendLogService` za persistent retry.

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
    │   │   ├── deviation ≥ 5%  → CRITICAL
    │   │   ├── deviation ≥ 3%  → HIGH
    │   │   ├── deviation ≥ 1%  → MEDIUM
    │   │   └── deviation < 1%  → LOW
    │   ├── calculateDeviation() → (target - actual) / target × 100
    │   ├── generateBreachDescription()
    │   └── Save SlaBreach entity
    │
    └── sendNotifications(breach):
            │
            ├── SlaNotificationService.sendEmailNotification(breach, recipients)
            │   │
            │   ├── Build subject: "[CRITICAL] SLA Breach - Production API"
            │   ├── Build body: SLA name, period, status, severity,
            │   │   target/actual compliance, deviation, duration, description
            │   │
            │   └── Per recipient:
            │       └── EmailSendLogService.sendEmailWithPersistence(request, false, "SLA_BREACH", breachId)
            │           │
            │           ├── Phase 1: MailerService.sendTextEmail() — 3 inline pokušaja
            │           │   ├── SUCCESS → return response
            │           │   └── ALL FAILED → logFailedSend() → save to email_send_log (FAILED)
            │           │
            │           └── Phase 2: EmailRetryScheduler (svaki 5 min)
            │               └── EmailSendLogService.processRetryableEmails()
            │                   ├── SUCCESS → markSent()
            │                   └── FAIL → recordFailedAttempt() → backoff
            │                       └── retry_count ≥ max_retries → MAX_RETRIES_REACHED + log.error
            │
            └── SlaNotificationService.sendWebhookNotification(breach, webhookUrl)
                └── MOCK — samo loguje (TODO: G-07)
```

### 2.5 Scheduled Email Retry (Phase 2) — detalji

**Implementirano u G-06** (2026-03-12). Ova infrastruktura je dostupna za G-16.

| Komponenta | Lokacija | Uloga |
|---|---|---|
| `EmailSendLog` entity | oci-library | BIGINT PK, standalone (ne BaseEntity). Polja: recipient, subject, body, isHtml, status, retryCount, maxRetries, nextRetryAt, errorMessage, source, sourceEntityId |
| `EmailSendStatus` enum | oci-library | PENDING, SENT, FAILED, MAX_RETRIES_REACHED. Helper metode: `isRetryable()`, `isTerminal()` |
| `EmailSendLogRepository` | oci-monitor | `findRetryableEmails(now)` — PENDING/FAILED + nextRetryAt ≤ now + retryCount < maxRetries |
| `EmailSendLogService` | oci-monitor | `sendEmailWithPersistence()` — wrapper oko MailerService. `processRetryableEmails()` — batch retry |
| `EmailRetryScheduler` | oci-monitor | `@Scheduled(fixedDelay=5min)` + `@SchedulerLock` + `SchedulerToggleService("email.retry.scheduled")` |
| `email_send_log` tabela | Flyway dev V12, prod V6 | MySQL tabela sa indeksima za retry queries |

**Scheduled retry backoff** (exponential, konfigurabilno):
```
Retry 1:  T+5min      (5 × 3^0)
Retry 2:  T+20min     (5 × 3^1 = 15min later)
Retry 3:  T+1h5min    (5 × 3^2 = 45min later)
Retry 4:  T+3h20min   (5 × 3^3 = 135min later)
Retry 5:  T+9h20min   (5 × 3^4 = 360min = 6h cap)
```

**Trenutni consumeri**: samo `SlaNotificationService` (source=`"SLA_BREACH"`).

### 2.6 OCI Notification Flow primeri

#### Budget Notification Flow
```
OciNotificationBudgetSchedulerService (@Scheduled)
    │ Provera: budget threshold prekoračen?
    ▼
applicationEventPublisher.publishEvent(new BudgetNotificationEvent(...))
    │
    ▼
BudgetNotificationEventListener.onApplicationEvent()
    │
    ▼
BudgetNotificationService.notifyBudgetNotificationReports()
    │ Provera: already muted?
    │ Iteracija: BudgetNotificationVerification records
    │ Build HTML email sa mute-me/mute-all linkovima
    ▼
MailerService.sendHtmlEmail()      ← direktno, bez EmailSendLogService
```

#### SC (Commitment + Subscription) Notification Flow
```
OciNotificationSCSchedulerService (@Scheduled)
    │ Provera: commitment/subscription threshold?
    ├── publishEvent(CommitmentNotificationEvent)
    └── publishEvent(SubscriptionNotificationEvent)
            │
            ▼
CommitmentNotificationEventListener / SubscriptionNotificationEventListener
    │
    ▼
CommitmentNotificationService / SubscriptionNotificationService
    │ Build text/html email, mute linkovi, affected resources
    ▼
MailerService.sendTextEmail() / sendHtmlEmail()     ← direktno
```

#### Cost Reports Flow (error notification)
```
OciCostSchedulerService (@Scheduled)
    │ Error prilikom download/parse cost fajla
    ▼
applicationEventPublisher.publishEvent(new CostReportsEvent(status=DOWNLOAD/PARSE))
    │
    ▼
CostReportsEventListener → CostReportsService.notifyCostReports()
    │ Error email sa retry count + environment info
    ▼
MailerService.sendHtmlEmail()     ← to support email
```

### 2.7 Razlike između OCI i SLA notifikacija

| Aspekt | OCI notifikacije | SLA notifikacije |
|---|---|---|
| **Konfiguracija** | Korisnik kreira pravilo (threshold, recipients) | Recipient emails u SlaDefinition |
| **Trigger** | Scheduler periodično evaluira uslove | Event-driven (SlaResultComputedEvent → breach detection) |
| **Mute** | Da — verification code sa mute-me/mute-all linkovima | Ne — nema mute mehanizma |
| **Retry** | Phase 1 samo (inline u MailerService) | Phase 1 + Phase 2 (EmailSendLogService, persistent) |
| **Email format** | HTML sa linkovima na frontend + mute linkovi | Plain text sa SLA metrikama |
| **Listener tip** | `ApplicationListener<T>` (sinhroni) | `@TransactionalEventListener(AFTER_COMMIT)` + `@Async` |
| **Notification Reports** | Da — *NotificationReports entity prati status | Ne — samo SlaBreach.notificationSent flag |
| **Duplikat slanje** | Da — muted flag sprečava | Da — breach already exists check |

### 2.8 Kompletna scheduler infrastruktura (14 schedulera)

Za kontekst — svi scheduleri u oci-monitor sa ShedLock distributed locking:

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

### 2.9 MonitorApiService — inter-modul komunikacija

`oci-api` komunicira sa `oci-monitor` putem REST poziva (RestTemplate). Relevantno za SLA:

```java
// MonitorApiService u oci-api — poziva oci-monitor endpoint
triggerSlaComputation(SlaComputationRequestDTO request)
    → POST /monitoring/sla/trigger
```

Ovo je jedini cross-module poziv za SLA. Za G-16 notifikacije, pitanje je: da li notifikacije treba slati iz oci-api (gde se izvršava user akcija) ili iz oci-monitor (gde živi SlaNotificationService)?

---

## 3. Trenutno stanje SLA notifikacija

### 3.1 Postojeća SLA event arhitektura

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

| Kategorija | Operacija | Endpoint | Modul | Prioritet notifikacije |
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

**Napomena**: Sve user-initiated operacije se izvršavaju u oci-api, dok se SLA computation i breach detection izvršavaju u oci-monitor.

### 3.3 Prioritetni eventi za Phase 1

Na osnovu poslovnog uticaja, **6 evenata** je najvažnije:

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

### 3.4 Postojeća infrastruktura za reuse

| Komponenta | Lokacija | Status | Napomena |
|---|---|---|---|
| `ApplicationEventPublisher` | SlaComputationService | Radi | Publishuje SlaResultComputedEvent |
| `SlaNotificationService` | oci-monitor | Radi | `sendEmailNotification()` — koristi EmailSendLogService |
| `EmailSendLogService` | oci-monitor | **NOVO** (2026-03-12) | Persistent retry za email — koristi se za `sendEventNotification()` |
| `MailerService` (SMTP/SendGrid) | oci-monitor + oci-api | Radi | Phase 1 inline retry u oba modula |
| `@Async` thread pool | oci-monitor | Konfigurisan | 4-8 thread-ova, sla-async-* prefix |
| `@TransactionalEventListener` | SlaBreachDetectionService | Pattern postoji | AFTER_COMMIT + @Async |
| `SlaDefinition.notificationRecipientEmails` | oci-library entity | Radi | Comma-separated email lista |
| `SlaBreach` notification fields | oci-library entity | Radi | notificationSent, sentAt, failureReason |

---

## 4. Koji eventi i kome?

### 4.1 Event → Recipient matrica

| Event | Recipient | Razlog |
|---|---|---|
| SLA deactivated | `definition.notificationRecipientEmails` | Stakeholder-i moraju znati da SLA više nije aktivan |
| SLA deleted | `definition.notificationRecipientEmails` | Stakeholder-i moraju znati da SLA ne postoji |
| Breach acknowledged | `definition.notificationRecipientEmails` | Tim zna da je neko preuzeo odgovornost |
| Breach resolved | `definition.notificationRecipientEmails` | Tim zna da je problem rešen |
| Schedule activated/deactivated | `definition.notificationRecipientEmails` | Informacija o promeni reporting režima |
| Report generated | `schedule.recipientEmails` | Izveštaj dostupan za pregled |

### 4.2 Event payload (zajedničko)

Svaki event notification treba sadržati:

```
Subject:  [EVENT_TYPE] SLA event — {slaDefinitionName}
Body:
  - Event type (human-readable)
  - SLA Definition name
  - Timestamp
  - Actor (ko je izvršio akciju)
  - Event-specific detalji
  - Link ka UI (opciono)
```

---

## 5. Pristupi

### 5.1 Pristup A: Direct Notification u servisnom sloju (PREPORUKA)

Poziv `SlaNotificationService` direktno iz servisnih metoda koje menjaju stanje. Najjednostavniji pristup — bez novih ApplicationEvent klasa, bez novih listener-a.

#### Dijagram

```
SlaController (oci-api)          SlaService (oci-api)              SlaNotificationService (oci-monitor)
    │                               │                                   │
    ├── deactivate(id) ────────────►├── deactivateDefinition()          │
    │                               │       │                           │
    │                               │       ├── save(definition)        │
    │                               │       │                           │
    │                               │       └── notifyEvent(            │
    │                               │              "SLA_DEACTIVATED",   │
    │                               │              definition,          │
    │                               │              actor)  ────────────►├── sendEventEmail()
    │                               │                                   │   via EmailSendLogService
    │                               │                                   │   (persistent retry)
    │◄──────────────── 200 OK ──────┤                                   │
```

**Cross-module pitanje**: `SlaNotificationService` živi u oci-monitor, a user akcije se izvršavaju u oci-api.

**Rešenje**: 3 opcije:
1. **REST poziv** — oci-api poziva oci-monitor endpoint za slanje notifikacije (kao MonitorApiService pattern)
2. **Lokalni MailerService** — oci-api već ima MailerService, može slati direktno (ali gubi EmailSendLogService persistent retry)
3. **Shared servis** — premestiti notification logiku u oci-library (ali library nema servise)

**Preporuka za POC**: Opcija 2 — slanje direktno iz oci-api korišćenjem lokalnog MailerService. Za POC, Phase 1 inline retry (3 pokušaja, ~20s) je dovoljan. Ako se zahteva persistent retry, može se dodati endpoint na oci-monitor.

#### Implementacija

**1. Kreirati `SlaEventType` enum (oci-library):**

```java
@Getter
@AllArgsConstructor
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

**Lokacija**: `oci-library` — jer se koristi i u oci-api (servis) i u oci-monitor (notification service).

**2. Dodati `sendEventNotification()` u `SlaNotificationService` (oci-monitor):**

```java
public void sendEventNotification(
        SlaEventType eventType,
        String slaDefinitionName,
        String recipients,
        String actor,
        Map<String, String> details
) {
    if (StringUtils.isBlank(recipients)) {
        log.info("No recipients for {} event on SLA: {}", eventType, slaDefinitionName);
        return;
    }

    String subject = buildEventSubject(eventType, slaDefinitionName);
    String body = buildEventBody(eventType, slaDefinitionName, actor, details);

    String sourceEntityId = details.getOrDefault("entityId", null);

    for (String recipient : recipients.split(",")) {
        String trimmedRecipient = recipient.trim();
        SendEmailRequestDto emailRequest = SendEmailRequestDto.builder()
            .to(trimmedRecipient)
            .subject(subject)
            .body(body)
            .build();
        try {
            emailSendLogService.sendEmailWithPersistence(
                emailRequest, false, "SLA_EVENT_" + eventType.name(), sourceEntityId);
        } catch (Exception e) {
            log.warn("Failed to send {} notification to {}: {}",
                eventType, trimmedRecipient, e.getMessage());
        }
    }
}
```

**Koristi `EmailSendLogService`** (ne direktno MailerService) — dobija Phase 1 + Phase 2 retry besplatno.

**3. Alternativa za oci-api — direktno slanje bez persistent retry:**

Ako se ne želi REST poziv ka oci-monitor, kreirati lightweight `SlaEventNotificationHelper` u oci-api koji koristi lokalni MailerService:

```java
@Service @Slf4j @RequiredArgsConstructor
public class SlaEventNotificationHelper {

    private final MailerService mailerService;

    public void sendEventNotification(SlaEventType eventType, String slaName,
            String recipients, String actor, Map<String, String> details) {
        if (StringUtils.isBlank(recipients)) return;

        String subject = String.format("[%s] %s", eventType.getDisplayName(), slaName);
        String body = buildBody(eventType, slaName, actor, details);

        for (String recipient : recipients.split(",")) {
            try {
                mailerService.sendTextEmail(SendEmailRequestDto.builder()
                    .to(recipient.trim()).subject(subject).body(body).build());
            } catch (Exception e) {
                log.warn("Failed to send {} notification to {}: {}",
                    eventType, recipient.trim(), e.getMessage());
            }
        }
    }
}
```

**Trade-off**: Nema persistent retry (Phase 2), ali je jednostavnije — ne zahteva cross-module REST poziv.

**4. Pozivi u servisima (oci-api):**

```java
// SlaService.deactivateDefinition()
slaDefinitionManagementService.deactivateDefinition(id);
slaEventNotificationHelper.sendEventNotification(
    SlaEventType.SLA_DEACTIVATED,
    definition.getName(),
    definition.getNotificationRecipientEmails(),
    AuthHelper.getPrincipalUsername("system"),
    Map.of("definitionId", definition.getUuid().toString())
);

// SlaService.deleteSlaDefinition()
// VAŽNO: recipients treba preuzeti PRE brisanja jer će entity biti obrisan
String recipients = existing.getNotificationRecipientEmails();
String name = existing.getName();
slaDefinitionManagementService.deleteSlaDefinition(id, deletedBy);
slaEventNotificationHelper.sendEventNotification(
    SlaEventType.SLA_DELETED, name, recipients, deletedBy, Map.of());

// SlaService.acknowledgeBreach()
// ... acknowledge logic ...
slaEventNotificationHelper.sendEventNotification(
    SlaEventType.BREACH_ACKNOWLEDGED,
    definition.getName(),
    definition.getNotificationRecipientEmails(),
    actor,
    Map.of("severity", breach.getSeverity().name(),
           "notes", notes != null ? notes : "")
);

// SlaService.resolveBreach()
// ... resolve logic ...
slaEventNotificationHelper.sendEventNotification(
    SlaEventType.BREACH_RESOLVED,
    definition.getName(),
    definition.getNotificationRecipientEmails(),
    actor,
    Map.of("notes", notes != null ? notes : "")
);
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska |
| Effort | **3-4h** |
| Rizik | Nizak — dodaje pozive, ne menja flow |
| Fajlovi | SlaEventType enum (oci-library) + SlaEventNotificationHelper (oci-api) + pozivi u 3 servisa |
| Zavisnosti | Nema novih |
| Flyway | Ne |

#### Prednosti

- **Najjednostavniji pristup** — nema novih klasa, event objekata, listener-a
- **Eksplicitan** — jasno se vidi u kodu gde se šalje notifikacija
- **Kontrola** — lako se dodaje/uklanja notifikacija po operaciji
- **Reuse** — koristi postojeći `MailerService` sa inline retry
- **Brz** — sinhroni poziv, nema event queue delay-a
- **Testabilan** — mock `SlaEventNotificationHelper` u unit testovima
- **EmailSendLogService opcija** — ako treba persistent retry, može se dodati REST endpoint na oci-monitor

#### Mane / Ograničenja

- **Tight coupling** — servisni sloj direktno poziva notification helper
- **Sinhrono** — ako email slanje kasni, kasni i response (ali inline retry je max ~20s)
- **Duplikacija** — svaki servis mora da pozove notifikaciju ručno
- **Nema centralizovane event log** — događaji se ne čuvaju nigde (samo email)
- **Nema persistent retry** — ako se koristi oci-api MailerService direktno (Phase 1 only)

---

### 5.2 Pristup B: ApplicationEvent per operacija

Kreirati dedicirane `ApplicationEvent` klase za svaki tip operacije. Listener-i reaguju na evente i šalju notifikacije. Prati postojeći OCI notification pattern.

#### Dijagram

```
SlaService (oci-api)              Spring Event Bus                SlaEventNotificationListener
    │                                   │                                   │
    ├── deactivate()                    │                                   │
    │   ├── save(definition)            │                                   │
    │   └── publishEvent(               │                                   │
    │        SlaDefinitionDeactivated)──►│                                   │
    │                                   │──►@TransactionalEventListener     │
    │                                   │   @Async                          │
    │                                   │   onSlaDefinitionDeactivated() ──►│
    │                                   │                                   ├── sendEmail()
    │                                   │                                   │
    │                                   │                                   │
    ├── delete()                        │                                   │
    │   └── publishEvent(               │                                   │
    │        SlaDefinitionDeleted) ────►│                                   │
    │                                   │──►onSlaDefinitionDeleted() ──────►│
    │                                   │                                   ├── sendEmail()
```

**Cross-module problem**: Ovaj pristup radi samo unutar jednog Spring context-a. Pošto su oci-api i oci-monitor zasebni procesi, event se ne može automatski propagirati.

**Rešenje za cross-module**:
- Event bus radi unutar modula — listener mora biti u istom modulu kao publisher
- Za oci-api evente → listener u oci-api (koristi lokalni MailerService, bez persistent retry)
- Za oci-monitor evente (report generated) → listener u oci-monitor (koristi EmailSendLogService)

#### Implementacija

**1. Event klase (6 komada u oci-library):**

```java
@Getter
public abstract class SlaEvent extends ApplicationEvent {
    private final UUID entityId;
    private final String slaDefinitionName;
    private final String recipients;
    private final String actor;
    // ... constructor
}

public class SlaDefinitionDeactivatedEvent extends SlaEvent { }
public class SlaDefinitionDeletedEvent extends SlaEvent { }
public class SlaBreachAcknowledgedEvent extends SlaEvent {
    private final String severity;
    private final String notes;
}
public class SlaBreachResolvedEvent extends SlaEvent {
    private final String notes;
}
public class SlaScheduleStatusChangedEvent extends SlaEvent {
    private final boolean activated;
}
public class SlaReportGeneratedEvent extends SlaEvent {
    private final String reportName;
}
```

**2. Listener u oci-api:**

```java
@Component @Slf4j @RequiredArgsConstructor
public class SlaEventNotificationListener {

    private final MailerService mailerService;

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onDefinitionDeactivated(SlaDefinitionDeactivatedEvent event) {
        sendNotification(SlaEventType.SLA_DEACTIVATED, event);
    }

    // ... analogno za ostalih 4 evenata u oci-api
}
```

**3. Listener u oci-monitor** (za report generated):

```java
@Component @Slf4j @RequiredArgsConstructor
public class SlaReportEventNotificationListener {

    private final EmailSendLogService emailSendLogService;

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onReportGenerated(SlaReportGeneratedEvent event) {
        // Koristi EmailSendLogService za persistent retry
    }
}
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Srednja |
| Effort | **4-6h** |
| Rizik | Nizak |
| Fajlovi | 6 event klasa + 1 bazna (oci-library) + 2 listener-a (oci-api + oci-monitor) + enum + 3 servisa |
| Zavisnosti | Nema novih |
| Flyway | Ne |

#### Prednosti

- **Loose coupling** — servisi ne znaju za notifikacije, samo publishuju event
- **Extensible** — lako dodati nove listener-e (audit log, webhook, Slack)
- **Async** — `@Async` + `AFTER_COMMIT` ne blokira request
- **Consistent pattern** — prati postojeći OCI notification pattern
- **Centralized** — sva notification logika u listener-ima
- **Testable** — event publishing lako se testira

#### Mane / Ograničenja

- **Više klasa** — 6-7 novih event klasa (boilerplate)
- **Indirection** — teže se prati flow (publish → listener → notification)
- **AFTER_COMMIT ograničenje** — za DELETE operacije, entitet više ne postoji kad listener primi event (mora se proslediti sav payload u eventu)
- **Event explosion** — sa vremenom raste broj event klasa
- **Cross-module** — dva listener-a u dva modula, jer Spring event bus je per-process

---

### 5.3 Pristup C: Generički SlaEvent + Event Type enum

Jedna generička `SlaEvent` klasa sa `eventType` poljem umesto zasebnih klasa po operaciji. Kompromis između A i B.

#### Dijagram

```
SlaService (oci-api)              Spring Event Bus              SlaEventNotificationListener
    │                                   │                                │
    ├── deactivate()                    │                                │
    │   └── publishEvent(SlaEvent(      │                                │
    │        type=DEACTIVATED,          │                                │
    │        name, recipients,          │                                │
    │        actor, details)) ─────────►│                                │
    │                                   │──►@Async                       │
    │                                   │   @TransactionalEventListener  │
    │                                   │   onSlaEvent(event) ──────────►│
    │                                   │                                ├── switch(eventType)
    │                                   │                                ├── buildSubject()
    │                                   │                                ├── buildBody()
    │                                   │                                └── sendEmail()
```

#### Implementacija

**1. Jedna event klasa (oci-library):**

```java
@Getter
public class SlaEvent extends ApplicationEvent {
    private final SlaEventType eventType;
    private final UUID entityId;
    private final String slaDefinitionName;
    private final String recipients;
    private final String actor;
    private final Map<String, String> details;
    // ... constructor
}
```

**2. Jedan listener sa switch:**

```java
@Async
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void onSlaEvent(SlaEvent event) {
    log.info("Processing SLA event: {} for {}", event.getEventType(), event.getSlaDefinitionName());
    // build subject + body based on eventType, send email
}
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska-Srednja |
| Effort | **3-4h** |
| Rizik | Nizak |
| Fajlovi | 1 event klasa + 1 listener + enum (oci-library) + 3 servisa |
| Zavisnosti | Nema novih |
| Flyway | Ne |

#### Prednosti

- **Jedna event klasa** — nema boilerplate-a, nema event explosion
- **Loose coupling** — servisi publishuju event, ne znaju za notifikacije
- **Extensible** — novi event tipovi = samo novi enum value
- **Async + AFTER_COMMIT** — konzistentan sa postojećim SLA pattern-om
- **Centralized** — jedan listener, jedna metoda
- **Details map** — fleksibilan payload bez novih klasa

#### Mane / Ograničenja

- **Type-unsafe details** — `Map<String, String>` umesto typed polja
- **Listener prima sve evente** — ne može se selektivno slušati po tipu (ali switch rešava)
- **AFTER_COMMIT** — isti problem kao B za DELETE operacije
- **Cross-module** — isti problem kao Pristup B

---

### 5.4 Pristup D: Audit Event Log tabela + Scheduled Notification

Svaka state-modifying operacija se loguje u `sla_event_log` tabelu. Scheduled job periodično čita nove evente i šalje notifikacije.

#### Dijagram

```
SlaService (oci-api)            sla_event_log                  SlaEventNotificationScheduler
    │                              tabela                      @Scheduled(fixedDelay=1min)
    │                                │                         (u oci-monitor)
    │                                │                                │
    ├── deactivate()                 │                                │
    │   ├── save(definition)         │                                │
    │   └── INSERT INTO              │                                │
    │       sla_event_log ──────────►│                                │
    │       (type, entity_id,        │                                │
    │        actor, details,         │                                │
    │        notified=false)         │                                │
    │                                │                                │
    │                                │◄───── SELECT * WHERE           │
    │                                │       notified = false ────────┤
    │                                │                                │
    │                                │                                ├── sendEmail() per event
    │                                │                                │   via EmailSendLogService
    │                                │                                │
    │                                │◄───── UPDATE SET               │
    │                                │       notified = true ─────────┤
```

**Prednost za cross-module**: Rešava problem oci-api → oci-monitor komunikacije prirodno — oci-api piše u shared tabelu, oci-monitor čita iz nje.

#### Potrebne izmene

**1. Flyway migracija — nova tabela:**

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

**2. Entity (oci-library) + Repository (oci-monitor)**

**3. SlaEventLogService (oci-api)** — za INSERT:
```java
public void logEvent(SlaEventType eventType, UUID entityId, String entityName,
        String recipients, String actor, Map<String, String> details) {
    SlaEventLog log = SlaEventLog.builder()
        .eventType(eventType.name())
        .entityId(entityId.toString())
        .entityName(entityName)
        .recipients(recipients)
        .actor(actor)
        .details(objectMapper.writeValueAsString(details))
        .notified(false)
        .build();
    repository.save(log);
}
```

**4. Scheduled job (oci-monitor):**

```java
@Scheduled(fixedDelay = 60_000)  // 1 minut
@SchedulerLock(name = "sla-event-notification", lockAtMostFor = "PT5M", lockAtLeastFor = "PT30S")
public void processEvents() {
    if (!schedulerToggleService.isTaskEnabled("sla.event.notification")) return;

    List<SlaEventLog> pending = eventLogRepository.findByNotifiedFalse();
    for (SlaEventLog event : pending) {
        emailSendLogService.sendEmailWithPersistence(...);  // Full Phase 1 + Phase 2 retry
        event.setNotified(true);
        event.setNotifiedAt(LocalDateTime.now());
        eventLogRepository.save(event);
    }
}
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Srednja-Visoka |
| Effort | **6-8h** |
| Rizik | Nizak-Srednji |
| Fajlovi | Flyway + Entity (oci-library) + Repository + Scheduler (oci-monitor) + Log Service (oci-api) |
| Zavisnosti | Nema novih |
| Flyway | **Da** — nova tabela |

#### Prednosti

- **Audit trail** — svaki event trajno zabeležen u bazi
- **Cross-module natural** — piše oci-api, čita oci-monitor (shared DB)
- **Persistent** — preživljava restart, event se ne gubi
- **Full retry** — koristi EmailSendLogService za Phase 1 + Phase 2
- **Queryable** — "Koji eventi su se desili za ovaj SLA u poslednjem mesecu?"
- **Decoupled** — INSERT je brz (<1ms), slanje je async

#### Mane / Ograničenja

- **Nova tabela** — Flyway migracija, novi entity, novi repository
- **Delay** — notifikacija kasni do 1 minut (scheduled interval)
- **DB rast** — tabela raste sa svakim eventom (potreban cleanup job)
- **Overkill** — za 6 event tipova i ~10-50 evenata/dan
- **Operativni overhead** — maintain scheduled job, monitor table growth

---

## 6. Uporedna tabela

| Kriterijum | A: Direct | B: Event per tip | C: Generic Event | D: Event Log tabela |
|---|---|---|---|---|
| **Složenost** | Niska | Srednja | Niska-Srednja | Srednja-Visoka |
| **Effort** | 3-4h | 4-6h | 3-4h | 6-8h |
| **Nove klase** | 1 (enum) + 1 (helper) | 7 (6 events + base) + 2 listeners | 2 (event + enum) + 1 listener | 4+ (entity, repo, scheduler, service) |
| **Flyway** | Ne | Ne | Ne | Da |
| **Async** | Ne (sinhrono) | Da (@Async) | Da (@Async) | Da (scheduled) |
| **Loose coupling** | Ne | Da | Da | Da |
| **Audit trail** | Ne | Ne | Ne | Da |
| **Persistent retry** | Phase 1 only (oci-api) | Phase 1 only (oci-api) | Phase 1 only (oci-api) | **Phase 1 + 2** (via EmailSendLogService) |
| **Cross-module** | Trivijalno (lokalni poziv) | 2 listener-a u 2 modula | 2 listener-a u 2 modula | Natural (shared DB) |
| **Extensible** | Srednje | Visoko | Visoko | Visoko |
| **Consistent pattern** | Novi (direct) | Prati OCI pattern | Prati SLA pattern | Nov pattern |
| **AFTER_COMMIT safe** | N/A (sinhrono) | Da | Da | N/A (sinhrono write) |
| **Testabilnost** | Visoka | Visoka | Visoka | Srednja |

---

## 7. Preporuka: Pristup A — Direct Notification

### Zašto Pristup A?

**Kontekst:**
- Ovo je **POC UI** — ne enterprise production sistem
- Volume je nizak: ~10-50 event notifikacija dnevno u najgorem slučaju
- `EmailSendLogService` sa Phase 2 persistent retry postoji za breach notifikacije, ali G-16 eventi su manje kritični od breach alertova
- Phase 1 inline retry (3 pokušaja, ~20s) je dovoljan za event notifikacije
- KISS princip — najjednostavniji pristup koji ispunjava zahtev

**Pristup A optimalno balansira:**

```
                     EXTENSIBILNOST
                          ▲
                          │
      B (Events)  ●      │        ● D (Event Log)
                          │
      C (Generic) ●      │
                          │
                          │   ● A (Direct)  ← SWEET SPOT za POC
                          │
  ────────────────────────┼────────────────────► JEDNOSTAVNOST
                          │
```

**Ključni argumenti:**

1. **Najmanji effort** — 3-4h, samo `SlaEventType` enum + `SlaEventNotificationHelper` + 6 poziva
2. **Nema cross-module komplikacije** — sve u oci-api (osim report generated koji je u oci-monitor)
3. **Nema migracije** — ne menja DB šemu
4. **Eksplicitan** — jasno se u kodu vidi gde se šalje notifikacija
5. **Testabilan** — mock `SlaEventNotificationHelper`, verify poziv
6. **Upgrade path** — ako zatreba persistent retry, lako se dodaje REST endpoint ka oci-monitor ili se prelazi na Pristup D

**Kada upgrade-ovati:**
- Na **Pristup C** — ako se uvede webhook kanal (G-07), centralizovati kroz event bus
- Na **Pristup D** — ako se zahteva audit trail ili persistent retry za sve event notifikacije

### Napomena o sinhronosti i retry-ju

Pristup A je sinhroni — `sendEventNotification()` se poziva u istom thread-u. Ali:
- MailerService ima inline retry sa exponential backoff (3 pokušaja, max ~20s)
- Ako sva 3 pokušaja propadnu, catch loguje error i response se vraća — korisnik ne čeka duže od ~20s u najgorem slučaju
- Za POC, ovo je prihvatljivo
- Za production: wrap u `@Async` ili prelaz na Pristup D za full persistent retry

---

## 8. Implementacioni plan (Pristup A)

### Korak 1: Kreirati `SlaEventType` enum u oci-library

`oci-library/.../sla/SlaEventType.java` — 7 vrednosti sa displayName i description.

### Korak 2: Kreirati `SlaEventNotificationHelper` u oci-api

`oci-api/.../sla/SlaEventNotificationHelper.java` — `@Service` koji koristi lokalni MailerService. Metode: `sendEventNotification()`, `buildSubject()`, `buildBody()`.

### Korak 3: Dodati `sendEventNotification()` u `SlaNotificationService` (oci-monitor)

Za report generated event koji se izvršava u oci-monitor. Koristi EmailSendLogService za persistent retry.

### Korak 4: Dodati pozive u servisni sloj

| Servis | Modul | Metod | Event |
|--------|-------|-------|-------|
| `SlaService` | oci-api | `deactivateDefinition()` | `SLA_DEACTIVATED` |
| `SlaService` | oci-api | `deleteSlaDefinition()` | `SLA_DELETED` |
| `SlaService` | oci-api | `acknowledgeBreach()` | `BREACH_ACKNOWLEDGED` |
| `SlaService` | oci-api | `resolveBreach()` | `BREACH_RESOLVED` |
| `SlaReportScheduleService` | oci-api | `updateScheduleStatus()` | `SCHEDULE_ACTIVATED` / `SCHEDULE_DEACTIVATED` |
| `SlaReportGenerationService` | oci-monitor | `generateReport()` | `REPORT_GENERATED` |

### Fajlovi koji se menjaju:

| Fajl | Modul | Izmena |
|------|-------|--------|
| `SlaEventType.java` | **oci-library** | **NOVO** — enum sa 7 vrednosti |
| `SlaEventNotificationHelper.java` | **oci-api** | **NOVO** — service sa sendEventNotification() + buildSubject() + buildBody() |
| `SlaService.java` | oci-api | 4 poziva (deactivate, delete, acknowledge, resolve) |
| `SlaReportScheduleService.java` | oci-api | 1 poziv (status change) |
| `SlaNotificationService.java` | oci-monitor | Dodati `sendEventNotification()` za report generated |
| `SlaReportGenerationService.java` | oci-monitor | 1 poziv (report generated) |

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

## 9. Frontend — kratki pregled

Frontend za G-16 je minimalan — nema novih stranica ni komponenti. Notifikacije su email-only.

**Opciono za budućnost** (van scope-a G-16):
- Toast/snackbar notifikacija u UI kad se breach acknowledge/resolve (već postoji optimistic update u `SlaBreachListPage`)
- Notification center/inbox u navigaciji (po uzoru na OCI UI "Notifikacije" dropdown)
- WebSocket push za real-time obaveštenja

---

## 10. Buduća unapređenja (van scope-a G-16)

| Stavka | Pristup | Trigger |
|--------|---------|---------|
| Webhook kanal | Refaktor na Pristup C + webhook sender | G-07 implementacija |
| Audit event log | Pristup D overlay | Compliance/audit zahtev |
| Notification preferences | Per-SLA + per-event config | Korisnici žele granularniju kontrolu |
| Mute mehanizam | Verification entity + mute linkovi (po OCI notification patternu) | Korisnici žele unsubscribe |
| Slack/Teams integration | Novi kanal u notification helper | Enterprise zahtev |
| Email template (HTML) | Thymeleaf template umesto plain text | UX zahtev |
| Digest/summary email | Scheduled batch umesto per-event | Volume >100 event/dan |
| Persistent retry za event notifikacije | Migriraj na EmailSendLogService (REST ka oci-monitor ili Pristup D) | Mission-critical event notifikacije |
