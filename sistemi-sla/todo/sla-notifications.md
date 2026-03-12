# G-16: SLA Notifikacije — UI prikaz + Email obaveštenja

> **Datum**: 2026-03-12
> **Status**: Kompletno (Backend + Frontend). Pristup A — Event Log + Scheduled Email.
> **Effort**: 7-9h
> **Backlog ref**: G-16 u `sla-backlog.md`

---

## 1. Zahtevi

### 1.1 Dva odvojena zahteva

| # | Zahtev | Opis |
|---|--------|------|
| **Z-1** | **UI prikaz SLA notifikacija** | `SlaNotificationController` u oci-api koji servira podatke za prikaz u header dropdown-u, po uzoru na MetricNotificationController / BudgetNotificationController / SCNotificationController. U oci-sla-management-poc-ui prikazati samo SLA notifikacije; UI team ce pri integraciji u oci-ui dodati SLA tab pored postojecih 4 tipa. |
| **Z-2** | **Email obaveštenja za SLA evente** | Slanje email notifikacija pri bitnim SLA dogadjajima (deactivate, delete, breach acknowledge/resolve, schedule status, report generated). Sve notifikacije treba da prolaze kroz `EmailSendLogService` za Phase 1+2 persistent retry. |

### 1.2 Ciljni UI

```
┌─────────────────────────────────────────────────────────────────┐
│  Monitoring    Billing    Kontrola   Notifikacije ▼    Admin    │
│                                      ┌──────────────────────────┤
│                                      │ Notifikacije metrike     │
│                                      │   Pracenje i izvestavanje│
│                                      │   stanja metrika resursa │
│                                      │                          │
│                                      │ SC Notifikacije          │
│                                      │   Pregled i kreiranje    │
│                                      │                          │
│                                      │ Budzet notifikacije      │
│                                      │   Pregled i kreiranje    │
│                                      │                          │
│                                      │ Kompartment notifikacije │
│                                      │   Pregled i kreiranje    │
│                                      │                          │
│                                      │ ─────────────────────────│
│                                      │ SLA Notifikacije    ← NOV│
│                                      │   Pregled SLA dogadjaja  │
│                                      │   i obaveštenja          │
│                                      └──────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

U oci-sla-management-poc-ui: samo SLA notifikacije u navigaciji (SLA tab jedini).

---

## 2. Ključni uvid: Tabela je neophodna

Za `SlaNotificationController` koji servira podatke UI-u **mora postojati tabela** u kojoj su SLA dogadjaji sačuvani.

Postojeći OCI notification kontroleri čitaju iz tabela:

| Controller | Čita iz tabele | Šta prikazuje |
|---|---|---|
| MetricNotificationController | `metric_notification` | Notification konfiguracije (rules) |
| BudgetNotificationController | `budget_notification` | Notification konfiguracije (rules) |
| SCNotificationController | `sc_notification` | Notification konfiguracije (rules) |
| **SlaNotificationController** | **`sla_event_log`** ← NOVO | **Triggered SLA dogadjaji (events)** |

**Razlika**: OCI kontroleri prikazuju **konfiguracije** (pravila za notifikacije). SLA kontroler prikazuje **dogadjaje** (šta se desilo). Ovo je razlika jer SLA nema zasebnu notification konfiguraciju — recipient email lista je deo `SlaDefinition.notificationRecipientEmails`.

**Posledica**: Svi pristupi koji ne ukljucuju tabelu (poput originalnog Pristupa A — Direct REST) **ne mogu da podrže Z-1 (UI prikaz)**.

---

## 3. Postojeća arhitektura (kontekst)

### 3.1 OCI Notification pattern

```
oci-api (8080)                                oci-monitor (8081)
─────────────────                             ──────────────────────
                                              Scheduler (@Scheduled)
[Korisnik]──POST──►NotificationController          │
                     │                              ▼
                     ▼                         *SchedulerService
                *NotificationService           (provera uslova)
                (CRUD, validacija)                  │
                     │                              ▼
                     ▼                         ApplicationEventPublisher
                Repository                     .publishEvent(XxxEvent)
                (save konfiguracija)                │
                                                    ▼
                                               XxxEventListener
                                               implements ApplicationListener
                                                    │
                                                    ▼
                                               *NotificationService
                                               (build email, iterate recipients)
                                                    │
                                                    ▼
                                               MailerService
                                               .sendTextEmail() / .sendHtmlEmail()
```

### 3.2 SLA Notification flow (trenutni — samo breach)

```
SlaComputationService.computeSla()  ──publish──►  SlaResultComputedEvent
                                                        │
                                     @Async + @TransactionalEventListener(AFTER_COMMIT)
                                                        │
                                                        ▼
                                                  SlaBreachDetectionService
                                                        │
                                              status == BREACHED ?
                                                        │
                                                        ▼
                                                  SlaNotificationService
                                                  .sendEmailNotification()
                                                        │
                                                        ▼
                                                  EmailSendLogService
                                                  .sendEmailWithPersistence()
                                                        │
                                              ┌─────────┴──────────┐
                                              │ Phase 1: inline    │
                                              │ retry (3x, ~20s)   │
                                              │                    │
                                              │ Phase 2: scheduled │
                                              │ retry (5x, ~9.5h)  │
                                              └────────────────────┘
```

### 3.3 Cross-module ogranicenje

| Komunikacija | Mehanizam | Primer |
|---|---|---|
| oci-api → oci-monitor | REST (MonitorApiService + RestTemplate) | `triggerSlaComputation()` |
| oci-monitor → oci-api | Ne postoji (jednosmerno) | — |
| Shared state | MySQL baza (entiteti u oci-library) | Oba modula citaju/pisu istu bazu |
| Spring events | Samo unutar jednog procesa | `ApplicationEvent` ne propagira cross-module |

### 3.4 Prioritetni SLA eventi za notifikacije

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

### 3.5 Event → Recipient matrica

| Event | Modul gde nastaje | Recipient | Razlog |
|---|---|---|---|
| SLA deactivated | oci-api | `definition.notificationRecipientEmails` | Stakeholder-i moraju znati da SLA vise nije aktivan |
| SLA deleted | oci-api | `definition.notificationRecipientEmails` | Stakeholder-i moraju znati da SLA ne postoji |
| Breach acknowledged | oci-api | `definition.notificationRecipientEmails` | Tim zna da je neko preuzeo odgovornost |
| Breach resolved | oci-api | `definition.notificationRecipientEmails` | Tim zna da je problem resen |
| Schedule activated/deactivated | oci-api | `definition.notificationRecipientEmails` | Informacija o promeni reporting rezima |
| Report generated | **oci-monitor** | `schedule.recipientEmails` | Izvestaj dostupan za pregled |

---

## 4. Pristupi

Svi pristupi osim Pristupa D ukljucuju `sla_event_log` tabelu jer je **neophodna za Z-1 (UI prikaz)**. Razlikuju se po nacinu slanja emaila (Z-2).

---

### 4.1 Pristup A: Event Log tabela + Scheduled Email (⭐ PREPORUKA)

Svaka state-modifying operacija loguje dogadjaj u `sla_event_log` tabelu. Scheduler u oci-monitor cita nenotificirane evente, salje email putem `EmailSendLogService` i markira ih. `SlaNotificationController` u oci-api cita istu tabelu za UI prikaz.

**Jedan mehanizam** — tabela je jedini interfejs izmedju modula. Nema REST poziva za notifikacije.

#### Dijagram

```
oci-api (8080)                          sla_event_log                    oci-monitor (8081)
────────────────                        (shared MySQL)                   ──────────────────

[Korisnik]                                    │
    │                                         │
    ├── PATCH /deactivate ──►SlaService       │
    │                          │              │
    │                   deactivateDefinition() │
    │                          │              │
    │                   slaEventLogService     │
    │                    .logEvent(            │
    │                      SLA_DEACTIVATED,   │
    │                      definition,        │
    │                      actor, details)    │
    │                          │              │
    │                          └── INSERT ───►│               SlaEventNotificationScheduler
    │                         (emailNotified   │               @Scheduled(fixedDelay=1min)
    │                          = false)        │               @SchedulerLock
    │                                         │                      │
    │                                         │◄── SELECT WHERE ─────┤
    │                                         │    emailNotified      │
    │                                         │    = false            │
    │                                         │                      │
    │                                         │                      ├── Per event:
    │                                         │                      │   SlaNotificationService
    │                                         │                      │    .sendEventNotification()
    │                                         │                      │        │
    │                                         │                      │        ▼
    │                                         │                      │   EmailSendLogService
    │                                         │                      │    .sendEmailWithPersistence()
    │                                         │                      │        │
    │                                         │                      │   Phase 1: inline (3x, ~20s)
    │                                         │                      │   Phase 2: scheduled (5x, ~9.5h)
    │                                         │                      │
    │                                         │◄── UPDATE SET ───────┤
    │                                         │    emailNotified      │
    │                                         │    = true             │
    │                                         │                      │
    │                                         │
    │   SlaNotificationController             │
    │   GET /api/sla/notifications            │
    │          │                              │
    │          └── SELECT ───────────────────►│
    │              WHERE organization = X      │
    │              ORDER BY created_at DESC    │
    │◄──────── List<SlaEventLogDto> ──────────┤
    │                                         │
    ▼                                         │
[UI prikazuje notifikacije]                   │


  oci-monitor (interni eventi — report generated):
  ──────────────────────────────────────────────
  SlaReportGenerationService.generateReport()
      │
      └── slaEventLogRepository.save(
              SlaEventLog.builder()
                  .eventType(REPORT_GENERATED)
                  .slaDefinitionName(name)
                  .recipients(schedule.getRecipientEmails())
                  .actor("scheduler")
                  .build()
          )
          │
          └── INSERT ──► sla_event_log
                         (emailNotified = false)
                              │
                              ▼
                    Scheduler ce pokupiti na sledecem ciklusu
```

#### Tabela: `sla_event_log`

```sql
CREATE TABLE sla_event_log (
    id                    BIGINT AUTO_INCREMENT PRIMARY KEY,
    uuid                  CHAR(36) NOT NULL,
    event_type            VARCHAR(50) NOT NULL,

    -- SLA definition reference
    sla_definition_uuid   CHAR(36),
    sla_definition_name   VARCHAR(255) NOT NULL,

    -- Multi-tenancy
    organization_id       BIGINT,

    -- Who and when
    actor                 VARCHAR(100) NOT NULL,

    -- Event details
    details               TEXT,                   -- JSON string za event-specific data
    message               VARCHAR(500),           -- Human-readable summary

    -- Email notification tracking
    recipients            TEXT,                   -- Comma-separated email lista
    email_notified        BOOLEAN NOT NULL DEFAULT FALSE,
    email_notified_at     DATETIME NULL,

    -- UI dismiss tracking (po uzoru na isMuted u OCI *NotificationReports)
    is_dismissed          BOOLEAN NOT NULL DEFAULT FALSE,
    dismissed_at          DATETIME NULL,
    dismissed_by          VARCHAR(100) NULL,

    -- Timestamps
    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE KEY uk_event_uuid (uuid),

    -- Indexes
    INDEX idx_event_pending_email (email_notified, created_at),
    INDEX idx_event_org_created (organization_id, created_at DESC),
    INDEX idx_event_org_undismissed (organization_id, is_dismissed, created_at DESC)
);
```

#### Klase

**`SlaEventType` enum (oci-library):**

```java
public enum SlaEventType {
    SLA_DEACTIVATED("SLA Deactivated"),
    SLA_DELETED("SLA Deleted"),
    BREACH_ACKNOWLEDGED("Breach Acknowledged"),
    BREACH_RESOLVED("Breach Resolved"),
    SCHEDULE_ACTIVATED("Schedule Activated"),
    SCHEDULE_DEACTIVATED("Schedule Deactivated"),
    REPORT_GENERATED("Report Generated");
}
```

**`SlaEventLog` entity (oci-library):**

```java
@Entity @Table(name = "sla_event_log")
public class SlaEventLog {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, columnDefinition = "char(36)")
    private UUID uuid;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 50)
    private SlaEventType eventType;

    private UUID slaDefinitionUuid;
    private String slaDefinitionName;
    private Long organizationId;
    private String actor;
    private String details;         // JSON
    private String message;
    private String recipients;      // comma-separated

    private boolean emailNotified;
    private LocalDateTime emailNotifiedAt;
    private boolean isDismissed;
    private LocalDateTime dismissedAt;
    private String dismissedBy;

    private LocalDateTime createdAt;
}
```

**`SlaEventLogService` (oci-api) — log-only, write-side:**

```java
@Service @RequiredArgsConstructor
public class SlaEventLogService {
    private final SlaEventLogRepository slaEventLogRepository;

    public void logEvent(SlaEventType eventType, SlaDefinition definition,
                         String actor, Map<String, String> details) {
        slaEventLogRepository.save(SlaEventLog.builder()
            .uuid(UUID.randomUUID())
            .eventType(eventType)
            .slaDefinitionUuid(definition.getUuid())
            .slaDefinitionName(definition.getName())
            .organizationId(definition.getOrganization().getId())
            .recipients(definition.getNotificationRecipientEmails())
            .actor(actor)
            .details(details != null ? objectMapper.writeValueAsString(details) : null)
            .message(buildMessage(eventType, definition.getName(), actor))
            .createdAt(LocalDateTime.now())
            .build());
    }
}
```

**`SlaNotificationController` (oci-api) — read-side za UI:**

```java
@RestController @RequestMapping("/api/sla/notifications")
public class SlaNotificationController {
    private final SlaEventLogRepository slaEventLogRepository;
    private final SlaEventLogMapper mapper;

    @GetMapping
    public List<SlaEventLogDto> getNotifications(
            @RequestParam Long organizationId,
            @RequestParam(defaultValue = "50") int limit) {
        return slaEventLogRepository
            .findByOrganizationIdOrderByCreatedAtDesc(organizationId, PageRequest.of(0, limit))
            .stream().map(mapper::toDto).toList();
    }

    @GetMapping("/undismissed")
    public List<SlaEventLogDto> getUndismissed(@RequestParam Long organizationId) {
        return slaEventLogRepository
            .findByOrganizationIdAndIsDismissedFalseOrderByCreatedAtDesc(organizationId)
            .stream().map(mapper::toDto).toList();
    }

    @GetMapping("/undismissed/count")
    public long getUndismissedCount(@RequestParam Long organizationId) {
        return slaEventLogRepository
            .countByOrganizationIdAndIsDismissedFalse(organizationId);
    }

    @PatchMapping("/{uuid}/dismiss")
    public ResponseEntity<Void> dismiss(@PathVariable UUID uuid) {
        SlaEventLog event = slaEventLogRepository.findByUuid(uuid)
            .orElseThrow(() -> new ResourceNotFoundException("SlaEventLog", uuid));
        event.setDismissed(true);
        event.setDismissedAt(LocalDateTime.now());
        event.setDismissedBy(AuthHelper.getPrincipalUsername("system"));
        slaEventLogRepository.save(event);
        return ResponseEntity.ok().build();
    }
}
```

**`SlaEventNotificationScheduler` (oci-monitor):**

```java
@Scheduled(fixedDelayString = "${sla.event.notification.interval-ms:60000}")
@SchedulerLock(name = "sla-event-notification-scheduler",
               lockAtMostFor = "PT5M", lockAtLeastFor = "PT30S")
public void processEventNotifications() {
    if (!schedulerToggleService.isTaskEnabled("sla.event.notification.scheduled")) return;

    List<SlaEventLog> pending = slaEventLogRepository
        .findByEmailNotifiedFalseOrderByCreatedAtAsc();

    for (SlaEventLog event : pending) {
        slaNotificationService.sendEventNotification(event);
        event.setEmailNotified(true);
        event.setEmailNotifiedAt(LocalDateTime.now());
        slaEventLogRepository.save(event);
    }
}
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Sloznost | Srednja |
| Effort | **7-9h** |
| Flyway | **Da** — nova tabela + seed data za scheduler toggle |
| Email retry | **Phase 1+2 (sve)** — sve kroz EmailSendLogService u oci-monitor |
| UI prikaz | **Da** — SlaNotificationController cita iz sla_event_log |
| Audit trail | **Da** — svi eventi trajno u bazi |
| Novi scheduler | **Da** — 16. scheduler u sistemu |

#### Prednosti

- **Jedan mehanizam** — tabela je jedini interfejs. oci-api pise (INSERT), oci-monitor cita (SELECT). Nema REST poziva za notifikacije, nema event propagacije.
- **Full Phase 1+2 retry** — sve notifikacije prolaze kroz EmailSendLogService. Konzistentno za sve evente.
- **Cross-module natural** — shared DB je vec primarni mehanizam komunikacije. INSERT je atomican sa business operacijom (ista transakcija).
- **Audit trail** — svaki dogadjaj trajno u bazi. Queryable za analizu, debugging, compliance.
- **UI prikaz** — `SlaNotificationController` cita direktno iz tabele. Undismissed count za badge. Dismiss akcija.
- **Decoupled** — INSERT je <1ms, ne utice na response time. Email se salje async u scheduler ciklusu.
- **Persistent** — prezivljava restart oba modula. Ako oci-monitor nije bio dostupan 10 min, pri pokretanju ce obraditi sve pending evente.
- **Existing pattern** — `sla_event_log` + scheduler je isti pattern kao `email_send_log` + `EmailRetryScheduler`. Dokazan u produkciji.

#### Mane / Ogranicenja

- **Delay** — notifikacija kasni do 1 minut (scheduler interval). Prihvatljivo za event notification, ali ne za real-time.
- **Nova tabela** — Flyway migracija, novi entity, repository.
- **Novi scheduler** — 16. scheduler u sistemu + ShedLock + SchedulerToggleService seed data.
- **DB rast** — tabela raste. Potreban cleanup job za stare evente (>90 dana). Moze se dodati naknadno.
- **isDismissed je globalan** — dismiss je per-event, ne per-user. Ako jedan korisnik dismiss-uje, svi vide dismissed. Isto kao OCI `isMuted` pattern — prihvatljivo za team-level notifikacije.

---

### 4.2 Pristup B: Event Log tabela + Direct REST Email (odbačen)

Isti kao A za UI (tabela + controller), ali email odmah putem REST ka oci-monitor. **Dva mehanizma** (tabela za UI, REST za email). Odbačen jer: dva mesta za maintain, REST dependency za email (izgubljen ako oci-monitor nedostupan), nejasna `emailNotified` semantika, error handling kompleksnost (INSERT uspe ali REST ne).

### 4.3 Pristup C: Event Log tabela + Inline Email (odbačen)

Tabela za UI + email lokalno u svakom modulu (oci-api: MailerService Phase 1 only, oci-monitor: EmailSendLogService Phase 1+2). Odbačen jer: **nekonzistentan retry** — 5/6 evenata u oci-api ima samo Phase 1 (3 pokušaja, ~20s), duplirana email logika u dva modula, anti-pattern (83% evenata zaobilazi EmailSendLogService).

### 4.4 Pristup D: Direct REST Email bez tabele (odbačen)

Email putem REST ka oci-monitor, bez tabele. Odbačen jer: **ne podržava Z-1 (UI prikaz)** — nema tabele, nema podataka za SlaNotificationController. Nema audit trail. Pokriva samo email.

---

## 5. Zašto Pristup A?

1. **Jedan mehanizam za obe potrebe** — tabela je source of truth za UI i email. Nema duplikacije.
2. **Konzistentan Phase 1+2 retry** — sve kroz EmailSendLogService u oci-monitor. B i C imaju probleme (REST dep. / nekonzistentan retry).
3. **Self-healing** — scheduler pokuplja pending evente posle restarta. Nema izgubljenih notifikacija.
4. **Proven pattern** — `email_send_log` + `EmailRetryScheduler` analog. Dokazan u produkciji.
5. **SOLID: Single Responsibility** — SlaService zna samo za INSERT, scheduler zna za email, controller zna za UI.
6. **Delay ~1min prihvatljiv** — SLA notifikacije su informativne, ne zahtevaju real-time.

---

## 6. Implementacioni plan (Pristup A)

### Korak 1+2: Flyway + SlaEventType enum + SlaEventLog entity — ✅ DONE

- Dev: `V14__create_sla_event_log_table.sql` — CREATE TABLE + scheduler seed
- Prod: `V8__create_sla_event_log_table.sql` — isto za prod
- `com.sistemisolutions.oci.lib.entity.sla.SlaEventType` — enum sa 7 vrednosti
- `com.sistemisolutions.oci.lib.entity.sla.SlaEventLog` — standalone entity (BIGINT PK, kao EmailSendLog)

### Korak 3: `SlaEventLogRepository` (oci-api + oci-monitor) — ✅ DONE

- oci-api: `findByOrganizationIdOrderByCreatedAtDesc`, `findByUuid`, `findByOrganizationIdAndIsDismissedFalseOrderByCreatedAtDesc`, `countByOrganizationIdAndIsDismissedFalse`
- oci-monitor: `findPendingEmailNotifications()` — JPQL query za `emailNotified = false AND recipients IS NOT NULL`

### Korak 4: `SlaEventLogService` (oci-api) — write-side — ✅ DONE

- `logEvent(eventType, definition, actor, details)` — INSERT u tabelu
- `logEvent(eventType, uuid, name, orgId, recipients, actor, details)` — overload za slucajeve gde definition vec ne postoji (delete)
- try/catch wrapper — event logging nikad ne prekida primarnu operaciju

### Korak 5: `SlaNotificationController` + `SlaEventLogDto` + `SlaEventLogMapper` (oci-api) — ✅ DONE

- `GET /api/sla/notifications` — lista svih SLA notifikacija za organizaciju (paginated)
- `GET /api/sla/notifications/undismissed` — samo nedismisovane
- `GET /api/sla/notifications/undismissed/count` — za badge
- `PATCH /api/sla/notifications/{uuid}/dismiss` — dismiss
- Authorization: `AuthHelper.getCurrentUserPrincipal().getUser().getOrganization().getId()`
- MapStruct mapper: `SlaEventLogMapper` sa UUID-to-String mappings

### Korak 6: `SlaEventNotificationScheduler` (oci-monitor) — ✅ DONE

- `@Scheduled(fixedDelayString = "${sla.event.notification.scheduler.interval-ms:300000}")` — svaki 5 min
- `@SchedulerLock(name = "sla-event-notification-scheduler", lockAtMostFor = "PT10M", lockAtLeastFor = "PT1M")`
- `schedulerToggleService.isTaskEnabled("sla.event.notification.scheduled")`
- Cita pending evente, poziva `SlaNotificationService.sendEventNotification()`, markira `emailNotified = true`
- Per-event error handling — neuspeh jednog eventa ne zaustavlja batch

### Korak 7: `sendEventNotification(SlaEventLog)` u `SlaNotificationService` (oci-monitor) — ✅ DONE

- Prima SlaEventLog, gradi subject/body per eventType, iterira recipients
- Poziva `EmailSendLogService.sendEmailWithPersistence()` per recipient
- Source: `"SLA_EVENT_" + eventType.name()`
- Helper metode: `buildEventEmailSubject()`, `buildEventEmailBody()`

### Korak 8: Pozivi u servisni sloj (oci-api + oci-monitor) — ✅ DONE

| Servis | Modul | Metod | Poziv |
|--------|-------|-------|-------|
| `SlaService` | oci-api | `deactivateDefinition()` | `slaEventLogService.logEvent(SLA_DEACTIVATED, definition, actor, ...)` |
| `SlaService` | oci-api | `deleteSlaDefinition()` | `slaEventLogService.logEvent(SLA_DELETED, name, orgId, recipients, actor, ...)` ★ |
| `SlaService` | oci-api | `acknowledgeBreach()` | `slaEventLogService.logEvent(BREACH_ACKNOWLEDGED, definition, actor, ...)` |
| `SlaService` | oci-api | `resolveBreach()` | `slaEventLogService.logEvent(BREACH_RESOLVED, definition, actor, ...)` |
| `SlaReportScheduleService` | oci-api | `updateScheduleStatus()` | `slaEventLogService.logEvent(SCHEDULE_ACTIVATED/DEACTIVATED, definition, actor, ...)` |
| `SlaReportGenerationService` | oci-monitor | `generateReport()` | `slaEventLogRepository.save(...)` (direktno, lokalni modul) |

★ Za delete: preuzeti name, orgId, recipients PRE brisanja definicije.

### Fajlovi koji se menjaju:

| Fajl | Modul | Izmena |
|------|-------|--------|
| `V14__create_sla_event_log_table.sql` (dev) | oci-api | **NOVO** — Flyway |
| `V8__create_sla_event_log_table.sql` (prod) | oci-api | **NOVO** — Flyway |
| `SlaEventType.java` | **oci-library** | **NOVO** — enum |
| `SlaEventLog.java` | **oci-library** | **NOVO** — entity |
| `SlaEventLogDto.java` | **oci-library** | **NOVO** — response DTO |
| `SlaEventLogMapper.java` | oci-api ili oci-library | **NOVO** — MapStruct mapper |
| `SlaEventLogRepository.java` | oci-api | **NOVO** — JPA repository |
| `SlaEventLogRepository.java` | oci-monitor | **NOVO** — JPA repository (query za pending) |
| `SlaEventLogService.java` | oci-api | **NOVO** — logEvent() write-side |
| `SlaNotificationController.java` | oci-api | **NOVO** — REST za UI |
| `SlaEventNotificationScheduler.java` | oci-monitor | **NOVO** — scheduler |
| `SlaNotificationService.java` | oci-monitor | **IZMENA** — dodati `sendEventNotification(SlaEventLog)` |
| `SlaService.java` | oci-api | **IZMENA** — 4 poziva za logEvent |
| `SlaReportScheduleService.java` | oci-api | **IZMENA** — 1 poziv za logEvent |
| `SlaReportGenerationService.java` | oci-monitor | **IZMENA** — 1 poziv (direktan save) |

---

## 7. Frontend plan — ✅ DONE

### 8.1 oci-sla-management-poc-ui — ✅ DONE

**Samo SLA notifikacije** — header dropdown sa jednim tipom.

```
┌──────────────────────────────────────────────────────────────────┐
│  SLA Definitions  │  Breaches  │  Schedules  │  🔔 (3)  │  ...  │
│                                                ┌─────────────────┤
│                                                │ SLA Notifikacije│
│                                                │                 │
│                                                │ ⬤ SLA "Prod    │
│                                                │   API" deaktiv. │
│                                                │   admin@ 5m ago │
│                                                │                 │
│                                                │ ⬤ Breach       │
│                                                │   acknowledged  │
│                                                │   user@ 1h ago  │
│                                                │                 │
│                                                │ ○ Report        │
│                                                │   generated     │
│                                                │   scheduler 2d  │
│                                                │                 │
│                                                │ [Prikaži sve]   │
│                                                └─────────────────┘
└──────────────────────────────────────────────────────────────────┘
```

Komponente (✅ implementirano):
- `NotificationBell` — ikona sa badge-om (undismissed count), dropdown sa poslednjih 10, dismiss, "View all" link. Polling svakih 60s za count. Click-outside-to-close.
- `SlaNotificationListPage` — `/sla/notifications` — full page sa tabelom, pagination (`usePagination`), 3 filtera (search, event type, dismissed status), dismiss akcija, event type badges sa bojama, "Refresh" dugme.
- `slaNotificationService` — 4 API metode: `getNotifications(limit)`, `getUndismissed()`, `getUndismissedCount()`, `dismiss(uuid)`
- `slaNotification.types.ts` — `SlaNotificationDto` interface + `SlaEventType` union type
- API rute u `constants.ts`: `SlaNotification.List/Undismissed/UndismissedCount/Dismiss`
- Ruta `/sla/notifications` u `App.tsx`
- `NotificationBell` dodat u `SlaNavigation.tsx` (desna strana, pre Logout dugmeta)
- **Navigacija restruktuirana**: 6 SLA sub-stranica (Definitions, Report, Timeline, Breaches, Schedules, Stored Reports) u "SLA" dropdown. 3 top-level stavke: SLA, Notifications, Architecture Info. `NavDropdown` komponenta (hover+click, 300ms delay, chevron, per-item opisi). Olakšava UI team integraciju — dodaju samo "SLA" dropdown item u NavMenu i "SLA Notifications" u postojeći Notifications dropdown.

API pozivi:
- `GET /api/sla/notifications/undismissed/count` — za badge (polling svaki 60s)
- `GET /api/sla/notifications/undismissed` — za dropdown (lazy load on open)
- `GET /api/sla/notifications?limit=200` — za full page
- `PATCH /api/sla/notifications/{uuid}/dismiss` — za dismiss

### 8.2 Integracija u oci-ui (UI team)

Kad UI team preuzme, dodaju:
- "SLA Notifikacije" kao 5. stavku u Notification dropdown-u (NavMenu.tsx)
- Link ka SLA notification management stranici
- Isti pattern kao MetricNotificationListPage, BudgetNotificationsPage, itd.
- Badge za undismissed count

---

## 8. Email format

**Subject**: `[SLA Deactivated] Production API Availability`

**Body**:
```
SLA Event Notification
━━━━━━━━━━━━━━━━━━━━━

Event:       SLA Definition Deactivated
SLA Name:    Production API Availability
Performed by: admin@sistemi.rs
Time:        2026-03-12 14:30:00

This SLA definition has been deactivated and will no longer
be monitored. No further computations will be performed.

---
This is an automated notification from OCI SLA Management.
```

---

## 9. Buduca unapredjenja (van scope-a G-16)

| Stavka | Opis | Trigger |
|--------|------|---------|
| ~~Report email sa PDF/CSV~~ | ~~SlaNotificationService.sendReportEmail() sa PDF/CSV attachmentima iz SlaReportExportService~~ | ✅ **IMPLEMENTIRANO** (2026-03-12) — G-17 |
| Webhook kanal | SlaNotificationService salje i webhook pored emaila | G-07 implementacija |
| Per-user read tracking | Zasebna `sla_event_log_read` tabela sa user_id + event_id | Vise korisnika po organizaciji |
| Cleanup job | Brisanje evenata starijih od 90 dana | Tabela raste >10K redova |
| Notification preferences | Per-SLA + per-event-type config | Korisnici zele kontrolu koje evente primaju |
| HTML email template | Thymeleaf template umesto plain text | UX zahtev |
| Digest/summary email | Scheduled batch umesto per-event | Volume >100 event/dan |
| Real-time push | WebSocket za instant UI update | UX zahtev za real-time |
