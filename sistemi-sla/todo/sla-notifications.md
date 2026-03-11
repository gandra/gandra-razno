# G-16: Notifikacije za bitne SLA evente — Analiza i pristup

> **Datum**: 2026-03-11
> **Status**: Analiza / Pre implementacije
> **Effort**: 4-6h (zavisno od pristupa)
> **Backlog ref**: G-16 u `sla-backlog.md`

---

## 1. Trenutno stanje

### 1.1 Postojeća event arhitektura

Sistem trenutno ima **jedan** ApplicationEvent i **jedan** listener:

```
SlaComputationService.computeSla()
    │
    └── eventPublisher.publishEvent(SlaResultComputedEvent)
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
                            ├── sendEmailNotification()     ← radi (SMTP/SendGrid)
                            └── sendWebhookNotification()   ← MOCK (TODO)
```

### 1.2 State-modifying operacije (kandidati za notifikacije)

Od ukupno 56 endpointa, **14 menja stanje** i potencijalno treba notifikaciju:

| Kategorija | Operacija | Endpoint | Prioritet notifikacije |
|---|---|---|---|
| **SLA Definition** | Kreiranje | POST `/definitions` | Nizak |
| | Izmena | PUT `/definitions/{id}` | Nizak |
| | Deaktivacija | PATCH `/definitions/{id}/deactivate` | **Visok** |
| | Brisanje | DELETE `/definitions/{id}` | **Visok** |
| **Breach** | Acknowledge | PATCH `/breaches/{id}/acknowledge` | **Srednji** |
| | Resolve | PATCH `/breaches/{id}/resolve` | **Srednji** |
| **Excluded Downtime** | Kreiranje | POST `/{slaId}/excluded-downtimes` | Nizak |
| | Izmena | PUT `/excluded-downtimes/{id}` | Nizak |
| | Brisanje | DELETE `/excluded-downtimes/{id}` | Nizak |
| **Report Schedule** | Kreiranje | POST `/report-schedules` | Nizak |
| | Activate/Deactivate | PATCH `/report-schedules/{id}/status` | **Srednji** |
| | Brisanje | DELETE `/report-schedules/{id}` | Nizak |
| **Execution** | Manual trigger | POST `/trigger` | Nizak |
| | Archive report | POST `/reports/{id}/archive` | Nizak |

### 1.3 Prioritetni eventi za Phase 1

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

### 1.4 Postojeća infrastruktura koja se može reuse-ovati

| Komponenta | Lokacija | Status |
|---|---|---|
| `ApplicationEventPublisher` | SlaComputationService | Radi — publishuje SlaResultComputedEvent |
| `SlaNotificationService` | oci-monitor | Radi — `sendEmailNotification()` |
| `MailerService` (SMTP/SendGrid) | oci-monitor | Radi — dva providera |
| `@Async` thread pool | oci-monitor | Konfigurisan |
| `@TransactionalEventListener` | SlaBreachDetectionService | Pattern postoji |
| `SlaDefinition.notificationRecipientEmails` | oci-library entity | Comma-separated email lista |
| `SlaBreach` notification fields | oci-library entity | notificationSent, sentAt, failureReason |

---

## 2. Koji eventi i kome?

### 2.1 Event → Recipient matrica

| Event | Recipient | Razlog |
|---|---|---|
| SLA deactivated | `definition.notificationRecipientEmails` | Stakeholder-i moraju znati da SLA više nije aktivan |
| SLA deleted | `definition.notificationRecipientEmails` | Stakeholder-i moraju znati da SLA ne postoji |
| Breach acknowledged | `definition.notificationRecipientEmails` | Tim zna da je neko preuzeo odgovornost |
| Breach resolved | `definition.notificationRecipientEmails` | Tim zna da je problem rešen |
| Schedule activated/deactivated | `definition.notificationRecipientEmails` | Informacija o promeni reporting režima |
| Report generated | `schedule.recipientEmails` | Izveštaj dostupan za pregled |

### 2.2 Event payload (zajedničko)

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

## 3. Pristupi

---

### 3.1 Pristup A: Direct Notification u servisnom sloju (PREPORUKA)

Poziv `SlaNotificationService` direktno iz servisnih metoda koje menjaju stanje. Najjednostavniji pristup — bez novih ApplicationEvent klasa, bez novih listener-a.

#### Dijagram

```
SlaController                   SlaService                      SlaNotificationService
    │                               │                                   │
    ├── deactivate(id) ────────────►├── deactivateDefinition()          │
    │                               │       │                           │
    │                               │       ├── save(definition)        │
    │                               │       │                           │
    │                               │       └── notifyEvent(            │
    │                               │              "SLA_DEACTIVATED",   │
    │                               │              definition,          │
    │                               │              actor)  ────────────►├── sendEventEmail()
    │                               │                                   │
    │◄──────────────── 200 OK ──────┤                                   │
```

#### Implementacija

**1. Dodati generički `sendEventNotification()` u `SlaNotificationService`:**

```java
public void sendEventNotification(
        SlaEventType eventType,
        String slaDefinitionName,
        String recipients,
        String actor,
        Map<String, String> details
) {
    if (recipients == null || recipients.isBlank()) return;

    String subject = buildSubject(eventType, slaDefinitionName);
    String body = buildBody(eventType, slaDefinitionName, actor, details);

    for (String recipient : recipients.split(",")) {
        try {
            mailerService.sendTextEmail(SendEmailRequestDto.builder()
                .to(recipient.trim())
                .subject(subject)
                .body(body)
                .build());
        } catch (Exception e) {
            log.warn("Failed to send {} notification to {}: {}",
                eventType, recipient, e.getMessage());
        }
    }
}
```

**2. Enum za event tipove:**

```java
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

**3. Pozivi u servisima:**

```java
// SlaService.deactivateDefinition()
slaDefinitionManagementService.deactivateDefinition(id);
notificationService.sendEventNotification(
    SlaEventType.SLA_DEACTIVATED,
    definition.getName(),
    definition.getNotificationRecipientEmails(),
    AuthHelper.getPrincipalUsername("system"),
    Map.of("definitionId", definition.getId().toString())
);

// SlaService.deleteSlaDefinition()
// Nota: recipients treba preuzeti PRE brisanja
String recipients = existing.getNotificationRecipientEmails();
String name = existing.getName();
slaDefinitionManagementService.deleteSlaDefinition(id, deletedBy);
notificationService.sendEventNotification(
    SlaEventType.SLA_DELETED, name, recipients, deletedBy, Map.of());
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska |
| Effort | **3-4h** |
| Rizik | Nizak — dodaje pozive, ne menja flow |
| Fajlovi | SlaNotificationService + SlaEventType enum + 3 servisa (6 poziva) |
| Zavisnosti | Nema novih |
| Flyway | Ne |

#### Prednosti

- **Najjednostavniji pristup** — nema novih klasa, interfejsa, event objekata
- **Eksplicitan** — jasno se vidi u kodu gde se šalje notifikacija
- **Kontrola** — lako se dodaje/uklanja notifikacija po operaciji
- **Reuse** — koristi postojeći `SlaNotificationService` i `MailerService`
- **Brz** — sinhroni poziv, nema event queue delay-a
- **Testabilan** — mock `SlaNotificationService` u unit testovima

#### Mane / Ograničenja

- **Tight coupling** — servisni sloj direktno poziva notification servis
- **Sinhrono** — ako email slanje kasni, kasni i response (ali email je brz, <1s)
- **Duplikacija** — svaki servis mora da pozove notifikaciju ručno
- **Nema centralizovane event log** — događaji se ne čuvaju nigde (samo email)
- **Nema subscriber pattern** — ne može se lako dodati novi kanal (SMS, Slack) bez izmene koda

---

### 3.2 Pristup B: ApplicationEvent per operacija

Kreirati dedicirane `ApplicationEvent` klase za svaki tip operacije. Listener-i reaguju na evente i šalju notifikacije. Prati postojeći pattern (`SlaResultComputedEvent`).

#### Dijagram

```
SlaService                        Spring Event Bus                  SlaEventNotificationListener
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

#### Implementacija

**1. Event klase (6 komada):**

```java
// Zajednička bazna klasa
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

**2. Centralni listener:**

```java
@Component @Slf4j @RequiredArgsConstructor
public class SlaEventNotificationListener {

    private final SlaNotificationService notificationService;

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onDefinitionDeactivated(SlaDefinitionDeactivatedEvent event) {
        notificationService.sendEventNotification(
            SlaEventType.SLA_DEACTIVATED,
            event.getSlaDefinitionName(),
            event.getRecipients(),
            event.getActor(),
            Map.of()
        );
    }

    // ... analogno za ostalih 5 evenata
}
```

**3. Publish u servisima:**

```java
// SlaService.deactivateDefinition()
slaDefinitionManagementService.deactivateDefinition(id);
eventPublisher.publishEvent(new SlaDefinitionDeactivatedEvent(
    this, definition.getId(), definition.getName(),
    definition.getNotificationRecipientEmails(),
    AuthHelper.getPrincipalUsername("system")
));
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Srednja |
| Effort | **4-6h** |
| Rizik | Nizak |
| Fajlovi | 6 event klasa + 1 bazna + 1 listener + enum + SlaNotificationService izmena + 3 servisa |
| Zavisnosti | Nema novih |
| Flyway | Ne |

#### Prednosti

- **Loose coupling** — servisi ne znaju za notifikacije, samo publishuju event
- **Extensible** — lako dodati nove listener-e (audit log, webhook, Slack)
- **Async** — `@Async` + `AFTER_COMMIT` ne blokira request
- **Consistent pattern** — prati postojeći `SlaResultComputedEvent` pattern
- **Centralized** — sva notification logika u jednom listener-u
- **Testable** — event publishing lako se testira

#### Mane / Ograničenja

- **Više klasa** — 6-7 novih event klasa (boilerplate)
- **Indirection** — teže se prati flow (publish → listener → notification)
- **AFTER_COMMIT ograničenje** — za DELETE operacije, entitet više ne postoji kad listener primi event (mora se proslediti sav payload u eventu)
- **Event explosion** — sa vremenom raste broj event klasa

---

### 3.3 Pristup C: Generički SlaEvent + Event Type enum

Jedna generička `SlaEvent` klasa sa `eventType` poljem umesto zasebnih klasa po operaciji. Kompromis između A i B.

#### Dijagram

```
SlaService                        Spring Event Bus              SlaEventNotificationListener
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

**1. Jedna event klasa:**

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
    notificationService.sendEventNotification(
        event.getEventType(),
        event.getSlaDefinitionName(),
        event.getRecipients(),
        event.getActor(),
        event.getDetails()
    );
}
```

**3. Publish — isti za sve operacije:**

```java
eventPublisher.publishEvent(new SlaEvent(
    this,
    SlaEventType.SLA_DEACTIVATED,
    definition.getId(),
    definition.getName(),
    definition.getNotificationRecipientEmails(),
    actor,
    Map.of("reason", "Manually deactivated")
));
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska-Srednja |
| Effort | **3-4h** |
| Rizik | Nizak |
| Fajlovi | 1 event klasa + 1 listener + enum + SlaNotificationService izmena + 3 servisa |
| Zavisnosti | Nema novih |
| Flyway | Ne |

#### Prednosti

- **Jedna event klasa** — nema boilerplate-a, nema event explosion
- **Loose coupling** — servisi publishuju event, ne znaju za notifikacije
- **Extensible** — novi event tipovi = samo novi enum value
- **Async + AFTER_COMMIT** — konzistentan sa postojećim pattern-om
- **Centralized** — jedan listener, jedna `sendEventNotification()` metoda
- **Details map** — fleksibilan payload bez novih klasa

#### Mane / Ograničenja

- **Type-unsafe details** — `Map<String, String>` umesto typed polja
- **Listener prima sve evente** — ne može se selektivno slušati po tipu (ali switch rešava)
- **AFTER_COMMIT** — isti problem kao B za DELETE operacije

---

### 3.4 Pristup D: Audit Event Log tabela + Scheduled Notification

Svaka state-modifying operacija se loguje u `sla_event_log` tabelu. Scheduled job periodično čita nove evente i šalje notifikacije.

#### Dijagram

```
SlaService                     sla_event_log                  SlaEventNotificationScheduler
    │                              tabela                     @Scheduled(fixedDelay=1min)
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
    │                                │                                │
    │                                │◄───── UPDATE SET               │
    │                                │       notified = true ─────────┤
```

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

**2. Entity + Repository**

**3. Scheduled job:**

```java
@Scheduled(fixedDelay = 60_000)  // 1 minut
@SchedulerLock(name = "sla-event-notification", lockAtLeastFor = "30s")
public void processEvents() {
    List<SlaEventLog> pending = eventLogRepository.findByNotifiedFalse();
    for (SlaEventLog event : pending) {
        notificationService.sendEventNotification(...);
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
| Fajlovi | Flyway + Entity + Repository + Scheduler + Service izmene |
| Zavisnosti | Nema novih |
| Flyway | **Da** — nova tabela |

#### Prednosti

- **Audit trail** — svaki event trajno zabeležen u bazi
- **Persistent** — preživljava restart, event se ne gubi
- **Retry** — ako slanje propadne, event ostaje `notified=false`
- **Queryable** — "Koji eventi su se desili za ovaj SLA u poslednjem mesecu?"
- **Decoupled** — zapis u tabelu je brz, slanje je async

#### Mane / Ograničenja

- **Nova tabela** — Flyway migracija, novi entity, novi repository
- **Delay** — notifikacija kasni do 1 minut (scheduled interval)
- **DB rast** — tabela raste sa svakim eventom (potreban cleanup job)
- **Overkill** — za 6 event tipova i ~10-50 evenata/dan
- **Operativni overhead** — maintain scheduled job, monitor table growth

---

## 4. Uporedna tabela

| Kriterijum | A: Direct | B: Event per tip | C: Generic Event | D: Event Log tabela |
|---|---|---|---|---|
| **Složenost** | Niska | Srednja | Niska-Srednja | Srednja-Visoka |
| **Effort** | 3-4h | 4-6h | 3-4h | 6-8h |
| **Nove klase** | 1 (enum) | 7 (6 events + base) | 2 (event + enum) | 4+ (entity, repo, scheduler) |
| **Flyway** | Ne | Ne | Ne | Da |
| **Async** | Ne (sinhrono) | Da (@Async) | Da (@Async) | Da (scheduled) |
| **Loose coupling** | Ne | Da | Da | Da |
| **Audit trail** | Ne | Ne | Ne | Da |
| **Persistent** | Ne | Ne | Ne | Da |
| **Retry** | Ne | Ne | Ne | Da (inherent) |
| **Extensible** | Srednje | Visoko | Visoko | Visoko |
| **Consistent pattern** | Ne | Da (prati existing) | Da (prati existing) | Nov pattern |
| **AFTER_COMMIT safe** | N/A (sinhrono) | Da | Da | N/A (sinhrono write) |
| **Testabilnost** | Visoka | Visoka | Visoka | Srednja |

---

## 5. Preporuka: Pristup A — Direct Notification

### Zašto Pristup A?

**Kontekst:**
- Ovo je **POC UI** — ne enterprise production sistem
- Volume je nizak: ~10-50 event notifikacija dnevno u najgorem slučaju
- Trenutni pattern u kodu je direct poziv (SlaBreachDetectionService → SlaNotificationService)
- Već postoji `SlaNotificationService.sendEmailNotification()` koji se može reuse-ovati
- Nema potrebe za audit trail-om evenata (to je budući zahtev)
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

1. **Najmanji effort** — 3-4h, samo `SlaEventType` enum + `sendEventNotification()` + 6 poziva u servisima
2. **Nema novih klasa** — jedan enum, jedna metoda, nema event klasa, nema listener-a
3. **Nema migracije** — ne menja DB šemu
4. **Eksplicitan** — jasno se u kodu vidi gde se šalje notifikacija
5. **Testabilan** — mock `SlaNotificationService`, verify poziv
6. **Upgrade path** — ako zatreba async/event-driven, lako se refaktoriše na Pristup C

**Kada upgrade-ovati na Pristup C:**
- Ako se uvede webhook kanal (G-07) — tada ima smisla centralizovati kroz event bus
- Ako se uvede Slack/Teams integracija
- Ako se zahteva audit trail — tada Pristup D

### Napomena o sinhronosti

Pristup A je sinhroni — `sendEventNotification()` se poziva u istom thread-u. Ali:
- Email slanje je brzo (<1s za SMTP, <2s za SendGrid)
- Ako email server ne odgovori, catch loguje error i nastavlja — response nije blokiran zauvek
- Za POC, ovo je prihvatljivo. Za production, može se wrap-ovati u `@Async` metod

---

## 6. Implementacioni plan (Pristup A)

### Korak 1: Kreirati `SlaEventType` enum

`oci-monitor/.../sla/SlaEventType.java` — 7 vrednosti sa displayName i description.

### Korak 2: Dodati `sendEventNotification()` u `SlaNotificationService`

Generička metoda koja prima `SlaEventType`, ime definicije, recipijente, aktora i details mapu. Gradi subject i body, šalje email svakom recipijentu.

### Korak 3: Dodati pozive u servisni sloj

| Servis | Metod | Event |
|--------|-------|-------|
| `SlaService` | `deactivateDefinition()` | `SLA_DEACTIVATED` |
| `SlaService` | `deleteSlaDefinition()` | `SLA_DELETED` |
| `SlaService` | `acknowledgeBreach()` | `BREACH_ACKNOWLEDGED` |
| `SlaService` | `resolveBreach()` | `BREACH_RESOLVED` |
| `SlaReportScheduleService` | `updateScheduleStatus()` | `SCHEDULE_ACTIVATED` / `SCHEDULE_DEACTIVATED` |
| `SlaReportGenerationService` | `generateReport()` | `REPORT_GENERATED` |

### Fajlovi koji se menjaju:

| Fajl | Izmena |
|------|--------|
| `oci-monitor/.../SlaEventType.java` | **NOVO** — enum sa 7 vrednosti |
| `oci-monitor/.../SlaNotificationService.java` | Dodati `sendEventNotification()` + `buildSubject()` + `buildBody()` |
| `oci-api/.../SlaService.java` | 4 poziva (deactivate, delete, acknowledge, resolve) |
| `oci-api/.../SlaReportScheduleService.java` | 1 poziv (status change) |
| `oci-monitor/.../SlaReportGenerationService.java` | 1 poziv (report generated) |

### Email format primeri

**Subject**: `[SLA Deactivated] Production API Availability`

**Body**:
```
SLA Event Notification
━━━━━━━━━━━━━━━━━━━━━

Event:       SLA Definition Deactivated
SLA Name:    Production API Availability
Performed by: admin@sistemi.rs
Time:        2026-03-11 14:30:00 UTC

This SLA definition has been deactivated and will no longer
be monitored. No further computations will be performed.

---
This is an automated notification from OCI SLA Management.
```

---

## 7. Buduća unapređenja (van scope-a G-16)

| Stavka | Pristup | Trigger |
|--------|---------|---------|
| Webhook kanal | Refaktor na Pristup C + webhook sender | G-07 implementacija |
| Audit event log | Pristup D overlay | Compliance/audit zahtev |
| Notification preferences | Per-SLA + per-event config | Korisnici žele granularniju kontrolu |
| Slack/Teams integration | Novi kanal u SlaNotificationService | Enterprise zahtev |
| Email template (HTML) | Thymeleaf template umesto plain text | UX zahtev |
| Digest/summary email | Scheduled batch umesto per-event | Volume >100 event/dan |
