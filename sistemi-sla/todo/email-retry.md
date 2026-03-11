# G-06: Email Retry — Analiza i pristup

> **Datum**: 2026-03-11 (analiza), 2026-03-12 (implementacija)
> **Status**: Phase 1 IMPLEMENTIRANO (inline retry), Phase 2 PRIPREMLJENO (email_send_log tabela)
> **Effort**: 2-6h (zavisno od pristupa)
> **Referenca**: `analysis/EMAIL-RETRY-LOGIC-ANALYSIS.md`

---

## IMPLEMENTACIJA — Pristup D: Hybrid (Phase 1 inline retry + Phase 2 scheduled cleanup)

### Implementirano (Phase 1 — Inline Exponential Backoff)

**Pristup**: Generički email retry na nivou `MailerService` — pokriva SVE pozivaoce emaila u celoj aplikaciji (SLA breach, budget, subscription, commitment, cost reports, user registration, password reset, metrics notifications, tester).

**Izmenjeni fajlovi:**

| Fajl | Modul | Izmena |
|------|-------|--------|
| `SmtpMailerService.java` | oci-api | Inline retry sa exponential backoff |
| `SmtpMailerService.java` | oci-monitor | Inline retry sa exponential backoff |
| `SendGridMailerService.java` | oci-api | Inline retry sa exponential backoff + SendGrid status code handling |
| `SendGridMailerService.java` | oci-monitor | Inline retry sa exponential backoff + SendGrid status code handling |
| `application.properties` | oci-api | Retry konfiguracija (4 propertyja) |
| `application.properties` | oci-monitor | Retry konfiguracija (4 propertyja) |

**Retry konfiguracija (oba modula):**
```properties
email.retry.max-attempts=3
email.retry.base-delay-ms=5000
email.retry.multiplier=3.0
email.retry.max-delay-ms=45000
```

**Backoff raspored:**
```
Attempt 1:  T+0s     (odmah)
Attempt 2:  T+5s     (sleep 5s)
Attempt 3:  T+20s    (sleep 15s = 5s × 3^1)
Ukupno:     ~20s worst case
```

### Pripremljeno (Phase 2 — email_send_log tabela)

**Flyway migracioni fajlovi:**

| Profil | Putanja | Verzija |
|--------|---------|---------|
| **dev** | `oci-api/src/main/resources/db/migration/dev/V12__create_email_send_log_table.sql` | V12 |
| **prod** | `oci-api/src/main/resources/db/migration/prod/V6__create_email_send_log_table.sql` | V6 |

Tabela `email_send_log` je kreirana za Phase 2 (scheduled cleanup job). Phase 1 ne koristi ovu tabelu.

### Phase 2 TODO (scheduled cleanup)
- Entity klasa `EmailSendLog`
- Repository `EmailSendLogRepository`
- `EmailSendLogService` — logovanje failed emailova posle inline retry iscrpljivanja
- `EmailRetryScheduler` — `@Scheduled` job koji periodično retry-uje PENDING/FAILED zapise
- Alerting kad `MAX_RETRIES_REACHED`

---

## 1. Trenutno stanje

### 1.1 Flow slanja notifikacije

```
SlaResultComputedEvent
    │
    ▼
SlaBreachDetectionService              (oci-monitor)
    @Async
    @TransactionalEventListener(AFTER_COMMIT)
    │
    ├── detectBreach()
    │       └── saveBreach() → sla_breach tabela
    │
    └── sendNotifications(breach)
            │
            ▼
        SlaNotificationService.sendEmailNotification(breach, recipients)
            │
            ▼
        MailerService.sendTextEmail(request)
            │
            ├── SmtpMailerService   (default, JavaMailSender)
            └── SendGridMailerService (email.provider=sendgrid)
```

### 1.2 Problem — jedan pokušaj, nema retry

```java
// SlaBreachDetectionService.sendNotifications() — TRENUTNI KOD
private void sendNotifications(SlaBreach breach) {
    try {
        List<SlaNotificationResult> results =
            notificationService.sendEmailNotification(breach, recipients);

        boolean emailSent = results.stream().anyMatch(r -> r.isSuccess());
        if (emailSent) {
            breach.setNotificationSent(true);       // ← jedini happy path
            breach.setNotificationSentAt(now());
        }
    } catch (Exception e) {
        log.error("Failed to send: {}", e.getMessage());
        breach.setNotificationSent(false);           // ← trajna izgubljena notifikacija
        breach.setNotificationFailureReason(e.getMessage());
    }
    slaBreachRepository.save(breach);
}
```

### 1.3 Postojeća infrastruktura u SlaBreach entitetu

| Polje | Tip | Opis |
|-------|-----|------|
| `notification_sent` | Boolean | Da li je notifikacija uspešno poslata |
| `notification_sent_at` | LocalDateTime | Kada je poslata |
| `notification_recipient_emails` | String(1000) | Kome je poslata (comma-separated) |
| `notification_failure_reason` | String(500) | Razlog neuspeha |

Takođe postoji gotov repository query:
```java
@Query("SELECT sb FROM SlaBreach sb WHERE sb.notificationSent = false ORDER BY sb.detectedAt ASC")
List<SlaBreach> findPendingNotifications();
```

### 1.4 Failure scenariji

| Scenario | Trajanje | Učestalost | Posledica danas |
|----------|----------|------------|-----------------|
| Network timeout | 5-30s | Čest | Notifikacija izgubljena zauvek |
| SendGrid rate limit | Sekunde | Retko | Notifikacija izgubljena zauvek |
| SendGrid outage | Minuti-sati | Retko | Notifikacija izgubljena zauvek |
| DNS resolution failure | Sekunde | Retko | Notifikacija izgubljena zauvek |
| SMTP server nedostupan | Minuti-sati | Srednje | Notifikacija izgubljena zauvek |
| Invalid recipient email | Permanentno | Retko | Notifikacija zauvek neuspešna (OK) |

---

## 2. Pristupi

---

### 2.1 Pristup A: Inline Exponential Backoff (PREPORUKA)

Retry logika direktno u `sendNotifications()` metodu — isti thread, isti poziv. Najjednostavniji pristup koji pokriva ~80% failure scenarija (kratki transient failures).

#### Dijagram toka

```
sendNotifications(breach)
    │
    for attempt = 1..MAX_RETRIES (3):
    │
    ├── attempt 1 ─── sendEmail() ─── SUCCESS? ─── DA ──→ markNotificationSent() ──→ KRAJ
    │                                    │
    │                                   NE
    │                                    │
    │                              sleep(5s)  ← backoff
    │
    ├── attempt 2 ─── sendEmail() ─── SUCCESS? ─── DA ──→ markNotificationSent() ──→ KRAJ
    │                                    │
    │                                   NE
    │                                    │
    │                              sleep(15s) ← 5s × 3^1
    │
    └── attempt 3 ─── sendEmail() ─── SUCCESS? ─── DA ──→ markNotificationSent() ──→ KRAJ
                                         │
                                        NE
                                         │
                                    markNotificationFailed() ──→ KRAJ
```

#### Backoff raspored

```
Attempt 1:  T+0s     ← odmah
Attempt 2:  T+5s     ← sleep 5s
Attempt 3:  T+20s    ← sleep 15s (5 × 3^1)

Ukupno blokirano vreme:  ~20 sekundi (worst case)
Formula:  delay = BASE × MULTIPLIER^(attempt-1)
          BASE = 5s, MULTIPLIER = 3, MAX_DELAY = 45s
```

#### Pseudo-kod

```java
private void sendNotifications(SlaBreach breach) {
    String recipients = definition.getNotificationRecipientEmails();
    if (recipients == null || recipients.isBlank()) return;

    int maxRetries = 3;
    long baseDelayMs = 5_000;   // 5 sekundi
    double multiplier = 3.0;
    long maxDelayMs = 45_000;   // 45 sekundi cap

    for (int attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            List<SlaNotificationResult> results =
                notificationService.sendEmailNotification(breach, recipients);

            boolean success = results.stream().anyMatch(SlaNotificationResult::isSuccess);

            if (success) {
                breach.markNotificationSent(recipientsSuccess);
                slaBreachRepository.save(breach);
                log.info("Email sent (attempt {})", attempt);
                return;  // ← USPEH, izlazi iz loop-a
            }

            // Svi recipijenti fail-ovali ali bez exception-a
            if (attempt < maxRetries) {
                long delay = Math.min((long)(baseDelayMs * Math.pow(multiplier, attempt - 1)), maxDelayMs);
                log.warn("Attempt {} failed, retrying in {}ms", attempt, delay);
                Thread.sleep(delay);
            }

        } catch (Exception e) {
            if (attempt < maxRetries) {
                long delay = Math.min((long)(baseDelayMs * Math.pow(multiplier, attempt - 1)), maxDelayMs);
                log.warn("Attempt {} exception: {}, retrying in {}ms", attempt, e.getMessage(), delay);
                try { Thread.sleep(delay); } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            } else {
                log.error("All {} attempts exhausted: {}", maxRetries, e.getMessage());
                breach.markNotificationFailed(e.getMessage());
                slaBreachRepository.save(breach);
            }
        }
    }

    // Svi pokušaji neuspešni
    if (!breach.getNotificationSent()) {
        breach.markNotificationFailed("Failed after " + maxRetries + " attempts");
        slaBreachRepository.save(breach);
    }
}
```

#### Konfigurisanje

```properties
# application.properties
sla.notification.retry.max-attempts=3
sla.notification.retry.base-delay-ms=5000
sla.notification.retry.multiplier=3.0
sla.notification.retry.max-delay-ms=45000
```

```java
@Value("${sla.notification.retry.max-attempts:3}")
private int maxRetries;
@Value("${sla.notification.retry.base-delay-ms:5000}")
private long baseDelayMs;
@Value("${sla.notification.retry.multiplier:3.0}")
private double multiplier;
@Value("${sla.notification.retry.max-delay-ms:45000}")
private long maxDelayMs;
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska — izmena jednog metoda |
| Effort | **2-3h** |
| Rizik | Nizak — ne menja šemu, ne dodaje zavisnosti |
| Pokriva | Kratke transient failures (timeout, rate limit, kratki outage) |
| Ne pokriva | Duži outage (>1 min), app restart |

#### Prednosti

- Najjednostavnija implementacija — samo jedan metod
- Nema novih zavisnosti, nema migracije, nema novih tabela
- Koristi postojeća `markNotificationSent()` / `markNotificationFailed()` polja
- Konfigurabilni parametri preko `application.properties`
- Pokriva najčešće failure scenarije (kratki network problemi)

#### Mane / Ograničenja

- **Blokira `@Async` thread** tokom retry-a (~20s worst case) — ali pošto je `@Async` sa sopstvenim thread pool-om, ovo blokira samo taj task, ne main thread
- **Ne preživljava restart** — ako se app restartuje tokom retry-a, notifikacija je izgubljena
- **Ne pokriva duže outage** — ako je email servis nedostupan >1 min, sve retry-eve iscrpi
- **Nema persistent tracking** — u bazi ne vidimo koliko retry-eva je bilo
- Notifikacija sa `findPendingNotifications()` ostaje vidljiva ali nema mehanizma da je ponovo pokuša

---

### 2.2 Pristup B: Scheduled Retry Job sa DB Tracking

Dodaje retry tracking polja u `SlaBreach` entitet + scheduled job koji periodično proverava i ponovo pokušava failed notifikacije.

#### Dijagram toka

```
┌─────────────────────────────────────────────────────────────────┐
│  IMMEDIATE PATH (SlaBreachDetectionService)                     │
│                                                                 │
│  onSlaResultComputed()                                          │
│      └── sendNotifications(breach)                              │
│              ├── SUCCESS → markSent(), retry_count=1             │
│              └── FAIL → retry_count=1, next_retry=now()+5min    │
└─────────────────────────────────────────────────────────────────┘
                            │
                     (fail path)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  RETRY PATH (BreachNotificationRetryScheduler)                  │
│  @Scheduled(fixedDelay = 5min)                                  │
│  @SchedulerLock("breach-notification-retry")                    │
│                                                                 │
│  1. findBreachesNeedingRetry(now)                               │
│  2. For each:                                                   │
│     ├── sendEmail()                                             │
│     ├── SUCCESS → markSent()                                    │
│     └── FAIL → retry_count++, next_retry = backoff(count)      │
│                                                                 │
│  Backoff:  5min → 15min → 45min → 2h15min → 6h (cap)          │
│  Max:      5 pokušaja → max_retries_reached = true              │
└─────────────────────────────────────────────────────────────────┘
                            │
                     (max retries)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  ALERT PATH                                                     │
│  @Scheduled(cron = "0 0 * * * *")  ← svaki sat                 │
│                                                                 │
│  findByMaxRetriesReachedAndNotSent()                            │
│  → log.error("N breaches exhausted all retries!")               │
└─────────────────────────────────────────────────────────────────┘
```

#### Backoff raspored

```
Pokušaj 1:  T+0          Odmah (u breach detection)
Pokušaj 2:  T+5min       5 × 3^0 = 5min
Pokušaj 3:  T+20min      5 × 3^1 = 15min
Pokušaj 4:  T+1h5min     5 × 3^2 = 45min
Pokušaj 5:  T+3h20min    5 × 3^3 = 135min = 2h15min
(max)       T+9h20min    5 × 3^4 = 405min → cap 360min = 6h

Ukupno pokušaja:  5 (+ inicijalni)
Ukupan period:    ~9.5 sati od prvog pokušaja
```

#### Potrebne izmene

**1. Flyway migracija** — nova polja u `sla_breach`:

```sql
ALTER TABLE sla_breach
    ADD COLUMN notification_retry_count INT NOT NULL DEFAULT 0,
    ADD COLUMN notification_last_retry_at DATETIME NULL,
    ADD COLUMN notification_next_retry_at DATETIME NULL,
    ADD COLUMN notification_max_retries_reached BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX idx_breach_notification_retry
    ON sla_breach (notification_sent, notification_max_retries_reached, notification_next_retry_at);
```

**2. Polja u SlaBreach entitetu:**

```java
@Column(name = "notification_retry_count", nullable = false)
private Integer notificationRetryCount = 0;

@Column(name = "notification_last_retry_at")
private LocalDateTime notificationLastRetryAt;

@Column(name = "notification_next_retry_at")
private LocalDateTime notificationNextRetryAt;

@Column(name = "notification_max_retries_reached", nullable = false)
private Boolean notificationMaxRetriesReached = false;
```

**3. Business metode u SlaBreach:**

```java
public void recordRetryAttempt(boolean success) { ... }
public boolean shouldRetryNotification() { ... }
```

**4. Nova komponenta:** `BreachNotificationRetryScheduler`

**5. Novi repository query:** `findBreachesNeedingRetry(LocalDateTime now)`

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Srednja — migracija + entitet + scheduler + repository |
| Effort | **4-6h** |
| Rizik | Nizak — dodaje nove komponente, ne menja postojeće suštinski |
| Pokriva | Kratki i duži outage (do ~9.5h), preživljava restart |
| Ne pokriva | Outage >9.5h (ali tada je verovatno sistemski problem) |

#### Prednosti

- **Persistent** — retry state u bazi, preživljava restart
- **Exponential backoff** — ne bombarduje email servis
- **Bounded** — max 5 pokušaja, ne retry-uje beskonačno
- **Vidljivost** — u bazi vidljiv retry_count, next_retry, max_reached
- **Alerting** — scheduled job loguje error kad max retries dostignut
- **ShedLock** — safe za multi-instance deployment
- **Manual retry** — moguć reset `next_retry_at` iz baze ili budućeg API-ja

#### Mane / Ograničenja

- **Migracija** — zahteva Flyway skript, entitet izmenu
- **Složenost** — nova komponenta (scheduler), novi query-ji
- **Delay** — prvi retry tek posle 5min (ne pokriva instant transient)
- **Scheduler zavisnost** — ako scheduler ne radi, retry ne radi
- **DB load** — periodični query svakih 5 min (zanemarljiv za mali broj breach-eva)

---

### 2.3 Pristup C: Spring @Retryable (deklarativni)

Spring Retry biblioteka — `@Retryable` anotacija na `MailerService.sendTextEmail()` / `sendHtmlEmail()`.

#### Dijagram toka

```
SlaNotificationService.sendEmailNotification()
    │
    ▼
MailerService.sendTextEmail(request)     ← @Retryable
    │
    ├── Attempt 1 (T+0s) ──── OK? ──→ return SUCCESS
    │                           │
    │                          FAIL (MailException)
    │                           │
    │                      sleep(2s)
    │
    ├── Attempt 2 (T+2s) ──── OK? ──→ return SUCCESS
    │                           │
    │                          FAIL
    │                           │
    │                      sleep(4s) ← 2s × 2.0
    │
    └── Attempt 3 (T+6s) ──── OK? ──→ return SUCCESS
                                │
                               FAIL
                                │
                           @Recover → return ERROR response
```

#### Potrebne izmene

**1. Maven dependency:**

```xml
<dependency>
    <groupId>org.springframework.retry</groupId>
    <artifactId>spring-retry</artifactId>
</dependency>
```

**2. `@EnableRetry` konfiguracija**

**3. `@Retryable` na MailerService metodama:**

```java
@Retryable(
    retryFor = {MailException.class, IOException.class},
    maxAttempts = 3,
    backoff = @Backoff(delay = 2000, multiplier = 2.0, maxDelay = 10000)
)
public EmailSendResponseDto sendTextEmail(SendEmailRequestDto request) { ... }

@Recover
public EmailSendResponseDto recover(Exception e, SendEmailRequestDto request) { ... }
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska — dependency + anotacija |
| Effort | **2h** |
| Rizik | Nizak |
| Pokriva | Kratke transient failures (do ~14s) |
| Ne pokriva | Duži outage, restart, persistent tracking |

#### Prednosti

- Najčistija implementacija — deklarativna, Spring-native
- Framework radi retry logiku — nema manual loop
- `@Recover` fallback metod za exhausted retries
- Automatski podržava razne exception tipove
- Transparentno za pozivaoce

#### Mane / Ograničenja

- **Nova zavisnost** — `spring-retry` + `spring-aspects`
- **Blokira thread** — 2s + 4s + 8s = ~14s
- **Ne preživljava restart** — in-memory retry
- **Nema persistent tracking** — ne znamo koliko retry-eva je bilo
- **Slab retry window** — svega ~14s, ne pokriva outage >15s
- **Radi na nivou MailerService** — retry-uje `sendEmail()`, ali ne `sendNotifications()`. Ako je problem u kodu pre/posle poziva MailerService, nema retry.

---

### 2.4 Pristup D: Hybrid — Inline retry + Scheduled cleanup

Kombinuje Pristup A (inline retry za instant recovery) + Pristup B (scheduled job za duže outage).

#### Dijagram toka

```
sendNotifications(breach)
    │
    ▼
 INLINE RETRY (3 pokušaja, ~20s)
    │
    ├── SUCCESS ──→ markSent() ──→ KRAJ
    │
    └── ALL FAILED ──→ markFailed()
                       retry_count = 1
                       next_retry = now() + 15min
                            │
                            ▼
              ┌─────────────────────────────┐
              │  BreachNotificationRetry     │
              │  @Scheduled(fixedDelay=15min)│
              │                             │
              │  Pokušaj 2: T+15min         │
              │  Pokušaj 3: T+1h            │
              │  Pokušaj 4: T+4h            │
              │  Max → alert                │
              └─────────────────────────────┘
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Srednja — inline loop + DB tracking + scheduler |
| Effort | **4-6h** |
| Rizik | Nizak |
| Pokriva | Instant transient (inline) + duži outage (scheduled) |
| Ne pokriva | Outage duži od max retry perioda |

#### Prednosti

- **Best of both worlds** — instant retry za kratke failures + persistent retry za duže
- **Pokriva 95%+ scenarija** — od 5s network timeout do višesatnog outage
- **Persistent** — scheduled deo preživljava restart

#### Mane / Ograničenja

- **Dva mehanizma** — inline loop + scheduled job, dva mesta za maintain
- **Ista složenost kao B** — i dalje treba migracija, entitet izmene, scheduler
- **Marginalna prednost** — razlika vs Pristup B je samo prvih ~20s instant retry

---

### 2.5 Pristup E: Message Queue (RabbitMQ)

Publish-subscribe pattern sa RabbitMQ za guaranteed delivery i built-in retry.

#### Dijagram toka

```
SlaBreachDetectionService
    │
    └── rabbitTemplate.convertAndSend("sla.breach.notification", message)
            │
            ▼
    ┌────────────────────────────────────┐
    │     RabbitMQ                        │
    │  ┌──────────────────────────────┐  │
    │  │ sla.breach.notification      │  │
    │  │ (durable queue)              │  │
    │  └──────────┬───────────────────┘  │
    │             │                      │
    │    fail ──► │ ◄── retry policy     │
    │             │     (3x, exp backoff)│
    │             │                      │
    │  ┌──────────▼───────────────────┐  │
    │  │ Dead Letter Queue (DLQ)      │  │
    │  └──────────────────────────────┘  │
    └────────────────────────────────────┘
            │                    │
            ▼                    ▼
    BreachNotification      DLQ Consumer
    Consumer                (alert ops)
```

#### Procena

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Visoka — nova infrastruktura (RabbitMQ), konfiguracija, consumer |
| Effort | **8-12h** |
| Rizik | Srednji — nova zavisnost, docker-compose izmena |
| Pokriva | Sve scenarije, guaranteed delivery |
| Ne pokriva | N/A — RabbitMQ je production-grade message broker |

#### Prednosti

- Guaranteed delivery — poruka se ne gubi
- Built-in retry + DLQ — RabbitMQ nativno
- Decoupling — breach detection nezavisan od notifikacije
- Skalabilnost — horizontalno skaliranje sa više consumer-a
- Monitoring — RabbitMQ management UI

#### Mane / Ograničenja

- **Infrastruktura** — zahteva RabbitMQ server (docker/cloud)
- **Operativni overhead** — još jedan servis za održavanje
- **Overkill za ovaj use case** — SLA breach notifikacije su low-volume (~10-100/dan)
- **Cena** — hosting, monitoring, alerting za RabbitMQ
- **Latency** — dodatan network hop
- OCI projekat trenutno **ne koristi** message queue

---

## 3. Uporedna tabela

| Kriterijum | A: Inline Backoff | B: Scheduled + DB | C: @Retryable | D: Hybrid | E: RabbitMQ |
|---|---|---|---|---|---|
| **Složenost** | Niska | Srednja | Niska | Srednja | Visoka |
| **Effort** | 2-3h | 4-6h | 2h | 4-6h | 8-12h |
| **Nova zavisnost** | Ne | Ne | spring-retry | spring-retry | RabbitMQ |
| **Flyway migracija** | Ne | Da | Ne | Da | Ne |
| **Instant retry** | Da (~20s) | Ne (min 5min) | Da (~14s) | Da (~20s) | Da (queue delay) |
| **Persistent tracking** | Ne | Da | Ne | Da | Da (queue) |
| **Preživljava restart** | Ne | Da | Ne | Da | Da |
| **Max retry window** | ~20s | ~9.5h | ~14s | ~4h+ | Neograničen |
| **Multi-instance safe** | Da (@Async) | Da (ShedLock) | Da (@Async) | Da (ShedLock) | Da (consumer) |
| **Vidljivost/audit** | Samo final status | Retry count + timestamps | Samo final status | Retry count + timestamps | Queue depth + DLQ |
| **Alerting** | Ne | Da (scheduled) | Ne | Da (scheduled) | Da (DLQ) |
| **Konfigurabilnost** | @Value properties | @Value + DB | @Retryable params | Oba | RabbitMQ config |
| **Pokriva kratki outage** | Da | Ne (delay) | Da | Da | Da |
| **Pokriva duži outage** | Ne | Da | Ne | Da | Da |

---

## 4. Preporuka: Pristup A — Inline Exponential Backoff

### Zašto Pristup A?

**Kontekst ovog sistema:**
- SLA breach notifikacije su **low-volume** (~10-100 breach-eva dnevno u najgorem slučaju)
- Već postoji `@Async` thread pool — blokiranje jednog thread-a 20s je prihvatljivo
- Postojeća `SlaBreach` polja (`notificationSent`, `notificationFailureReason`) su dovoljni za status tracking
- Već postoji `findPendingNotifications()` query — budući admin može ručno retry-ovati
- Sistem još uvek nema RabbitMQ ni spring-retry dependency

**Pristup A optimalno balansira:**

```
                        ROBUSNOST
                           ▲
                           │
        E (RabbitMQ) ●     │
                           │     D (Hybrid) ●
        B (Scheduled) ●   │
                           │
                           │         ● A (Inline Backoff)  ← SWEET SPOT
        C (@Retryable) ●  │
                           │
   ────────────────────────┼──────────────────────► JEDNOSTAVNOST
                           │
```

**Ključni argumenti:**

1. **80/20 pravilo** — inline retry pokriva ~80% failure scenarija (network timeout, rate limit, kratki outage) sa ~20% effort-a
2. **Nema migracije** — ne dodaje kolone, ne menja šemu baze
3. **Nema novih zavisnosti** — ne uvodi spring-retry ni RabbitMQ
4. **2-3h effort** — najbrža implementacija
5. **Backward compatible** — ne menja interfejs ni ponašanje postojećih komponenti
6. **Konfigurabilno** — parametri preko `@Value`, lako se podešavaju bez recompile
7. **Upgrade path** — ako se pokaže nedovoljnim, lako se nadogradi na Pristup B ili D

**Kada upgrade-ovati na Pristup B:**
- Ako se u produkciji pokaže da email servis ima outage >1 min redovno
- Ako se uvede potreba za audit trail-om retry pokušaja
- Ako ops tim zahteva alerting na failed notifikacije

---

## 5. Implementacioni plan (Pristup A)

### Korak 1: Dodati konfigurabilne retry parametre

`application.properties` → 4 nova property-ja

### Korak 2: Refaktorisati `sendNotifications()` u `SlaBreachDetectionService`

- Inline for-loop sa exponential backoff
- Koristi postojeće `markNotificationSent()` / `markNotificationFailed()`
- `Thread.sleep()` za backoff (prihvatljivo jer je `@Async`)

### Korak 3: Test

Korisnik testira ručno — pokrenuti scenario sa nedostupnim email serverom i proveriti logove.

### Fajlovi koji se menjaju:

| Fajl | Izmena |
|------|--------|
| `oci-monitor/.../SlaBreachDetectionService.java` | Refaktor `sendNotifications()` + `@Value` injekcija |
| `oci-monitor/src/main/resources/application.properties` | 4 nova property-ja |

---

## 6. Buduća unapređenja (van scope-a G-06)

| Stavka | Pristup | Trigger za implementaciju |
|--------|---------|--------------------------|
| Persistent retry tracking | Pristup B | Ops tim zahteva audit trail |
| Scheduled retry job | Pristup B | Email outage >1min postane čest |
| Manual retry API | Pristup B | Admin UI zahtev |
| RabbitMQ integration | Pristup E | Sistem preraste >1000 notifikacija/dan |
| Notification preferences | N/A | Korisnici žele per-SLA notification config |
