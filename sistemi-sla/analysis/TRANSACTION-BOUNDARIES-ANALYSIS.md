# Transaction Boundaries Analysis - SLA Breach Detection

## 📋 Problem Statement

### Trenutna Situacija

U trenutnoj implementaciji, `SlaComputationService` kreira `SlaResult` i objavljuje event **unutar iste transakcije**:

```java
@Transactional
public SlaResult computeSla(...) {
    // ... computation logic ...

    // STEP 8: Save result to database
    SlaResult savedResult = slaResultRepository.save(slaResult);

    // STEP 9: Publish event (still within same transaction!)
    eventPublisher.publishEvent(new SlaResultComputedEvent(this, savedResult.getId()));

    return savedResult;
}
```

Event listener je asinhroni i pokreće se u novom thread-u:

```java
@Async  // ← Runs in separate thread
@EventListener
@Transactional  // ← New transaction
public void onSlaResultComputed(SlaResultComputedEvent event) {
    // Load SlaResult from database
    SlaResult slaResult = slaResultRepository.findById(event.getSlaResultId())...;

    // Process breach detection...
}
```

### 🚨 Potencijalni Problem

**Race Condition**: Async thread može da se pokrene **PRE** nego što parent transakcija commituje podatke u bazu.

**Scenario:**
```
T0: Thread-1 (computeSla)      | Thread-2 (@Async listener)
    - Create SlaResult          |
    - Save to DB (not committed)|
    - Publish event ----------->|
    - Continue execution...     | - Start listening
                                | - findById(resultId)
                                | - ⚠️ NOT FOUND or OLD DATA!
    - Commit transaction ------>|
                                | - Process outdated data
```

**Rezultat:**
- `findById()` u async listener-u može vratiti NULL ili stare podatke
- Breach detection može da faila ili radi sa nevalidnim state-om

---

## 🎯 Cilj

Osigurati da event listener **UVEK** vidi commitovane podatke iz baze.

---

## 🔧 Pristup 1: @TransactionalEventListener (PREPORUČENO ✅)

### Opis

Spring pruža `@TransactionalEventListener` koji omogućava da se listener izvrši u specifičnoj fazi transakcije.

**Faze:**
- `BEFORE_COMMIT` - Pre commit-a parent transakcije
- `AFTER_COMMIT` - Posle commit-a parent transakcije ✅
- `AFTER_ROLLBACK` - Posle rollback-a
- `AFTER_COMPLETION` - Posle završetka (commit ili rollback)

### Implementacija

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class SlaBreachDetectionService {

    private final SlaBreachRepository slaBreachRepository;
    private final SlaResultRepository slaResultRepository;
    private final SlaNotificationService notificationService;

    /**
     * Event listener for SLA result computation.
     *
     * ✅ IMPORTANT: Uses @TransactionalEventListener(phase = AFTER_COMMIT)
     * to ensure async processing starts AFTER parent transaction commits.
     *
     * This prevents race conditions where async thread could read
     * uncommitted/stale data from database.
     */
    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)  // ← Key change!
    @Transactional
    public void onSlaResultComputed(SlaResultComputedEvent event) {
        UUID slaResultId = event.getSlaResultId();

        log.debug("Processing SlaResultComputedEvent for result {} (AFTER COMMIT)", slaResultId);

        // Now safe to load - parent transaction is committed
        SlaResult slaResult = slaResultRepository.findById(slaResultId)
            .orElseThrow(() -> new IllegalArgumentException("SLA Result not found: " + slaResultId));

        // ... rest of breach detection logic ...
    }
}
```

### Kako radi

```
T0: Thread-1 (computeSla)      | Thread-2 (@Async listener)
    - Create SlaResult          |
    - Save to DB (not committed)|
    - Publish event             |
    - Continue execution...     |
    - Commit transaction ✅     |
                                | - ✅ NOW start listening
                                | - findById(resultId)
                                | - ✅ GUARANTEED to find committed data
                                | - Process breach detection
```

### Prednosti ✅

1. **Garantovana konzistentnost**: Listener se pokreće samo posle uspešnog commit-a
2. **Minimal code change**: Samo zamena anotacije
3. **Spring-native solution**: Koristi built-in mehanizam, ne zavisi od external libraries
4. **Automatic rollback handling**: Ako parent transakcija failuje, listener se NE pokreće
5. **Clean separation**: Parent transaction završava pre nego što async processing počinje

### Mane ⚠️

1. **Slight delay**: Minimalno kašnjenje (par milisekundi) dok se čeka commit
2. **Lost events on app crash**: Ako app padne posle commit-a, ali pre pokretanja listener-a, event se gubi (ali ovo je generalni problem async processing-a)

### Rizici i Mitigacije

**Rizik 1:** Event se gubi ako app padne između commit-a i pokretanja listener-a
- **Mitigation:** Dodati scheduled job koji proverava `sla_result` zapise sa `status=BREACHED` ali bez odgovarajućeg `sla_breach` zapisa (cleanup/recovery job)

**Rizik 2:** Listener failuje posle commit-a
- **Mitigation:** Exception handling u listener-u + logging + monitoring (Sentry)

---

## 🔧 Pristup 2: Explicit Flush + Wait

### Opis

Ručno flush-ujemo EntityManager i čekamo da se transakcija commituje pre objavljivanja event-a.

### Implementacija

```java
@Transactional
public SlaResult computeSla(...) {
    // ... computation logic ...

    // STEP 8: Save result to database
    SlaResult savedResult = slaResultRepository.save(slaResult);

    // ✅ FORCE immediate flush to database
    entityManager.flush();

    // At this point, data is written to DB but transaction not yet committed
    // Event will still be published within transaction, but data is flushed

    // STEP 9: Publish event
    eventPublisher.publishEvent(new SlaResultComputedEvent(this, savedResult.getId()));

    return savedResult;
}
```

### Prednosti ✅

1. **Data is written to DB immediately**: Smanjuje rizik od race condition
2. **No additional annotations**: Koristi postojeći `@EventListener`

### Mane ⚠️

1. **❌ DOES NOT SOLVE THE PROBLEM!**: Flush piše u bazu ali **transakcija još nije commitovana**
2. **Transaction isolation**: Async thread može i dalje da vidi stare podatke zbog isolation level-a
3. **Not guaranteed**: Zavisi od database isolation level-a i lock-ova
4. **Rollback risk**: Ako parent transakcija failuje posle flush-a, async thread može da vidi podatke koji će biti rollback-ovani

### Verdict: ❌ NE PREPORUČUJEM

Ovo rešenje **NE REŠAVA** problem jer flush ne garantuje visibility u drugim transakcijama.

---

## 🔧 Pristup 3: Synchronous Processing + Manual Async

### Opis

Obrađujemo breach detection **sinhrono** unutar iste transakcije, a zatim asinkrono šaljemo notifikacije.

### Implementacija

**Refaktorisanje SlaComputationService:**

```java
@Transactional
public SlaResult computeSla(...) {
    // ... computation logic ...

    // STEP 8: Save result to database
    SlaResult savedResult = slaResultRepository.save(slaResult);

    // STEP 9: ✅ Synchronous breach detection (within same transaction)
    if (savedResult.getStatus() == SlaStatus.BREACHED) {
        SlaBreach breach = breachDetectionService.detectAndCreateBreachSync(savedResult);

        // STEP 10: ✅ Async notification (fire-and-forget)
        notificationService.sendNotificationsAsync(breach.getId());
    }

    return savedResult;
}
```

**Novi SlaBreachDetectionService metod:**

```java
@Service
@RequiredArgsConstructor
public class SlaBreachDetectionService {

    /**
     * ✅ SYNCHRONOUS breach creation (no event listener needed).
     * Called directly from SlaComputationService within same transaction.
     */
    public SlaBreach detectAndCreateBreachSync(SlaResult slaResult) {
        // Check if breach already exists
        boolean breachExists = slaBreachRepository.existsBySlaResult(slaResult);
        if (breachExists) {
            log.info("Breach already exists for SLA result {}, skipping", slaResult.getId());
            return slaBreachRepository.findBySlaResult(slaResult).orElseThrow();
        }

        log.info("SLA breach detected for result {} - creating breach record", slaResult.getId());

        // Create breach entity
        SlaBreach breach = detectAndCreateBreach(slaResult);

        return breach;
    }

    /**
     * Existing async event listener can be REMOVED or kept for backward compatibility.
     */
}
```

**Novi SlaNotificationService metod:**

```java
@Service
@RequiredArgsConstructor
public class SlaNotificationService {

    /**
     * ✅ ASYNC notification sending (fire-and-forget).
     * Loads breach from DB and sends notifications in background thread.
     */
    @Async
    @Transactional
    public void sendNotificationsAsync(UUID breachId) {
        SlaBreach breach = breachRepository.findById(breachId)
            .orElseThrow(() -> new IllegalArgumentException("Breach not found: " + breachId));

        sendNotifications(breach);  // Existing method
    }
}
```

### Kako radi

```
T0: Thread-1 (computeSla) - Single Transaction
    ├─ Create SlaResult
    ├─ Save SlaResult
    ├─ ✅ detectAndCreateBreachSync(slaResult)
    │   ├─ Create SlaBreach
    │   └─ Save SlaBreach
    ├─ ✅ sendNotificationsAsync(breachId) → starts Thread-2
    └─ Commit transaction ✅

                                | Thread-2 (async notifications)
                                | - Load breach (guaranteed committed)
                                | - Send emails
```

### Prednosti ✅

1. **Atomicity**: Oba `SlaResult` i `SlaBreach` se kreiraju u istoj transakciji
2. **No race conditions**: Breach detection vidi fresh data (ista transakcija)
3. **Fast rollback**: Ako bilo šta faila, sve se rollback-uje zajedno
4. **Clear control flow**: Nema event listener magic
5. **Testability**: Lakše za unit testove (direktan poziv, bez events)

### Mane ⚠️

1. **Longer transaction**: Transakcija traje duže (includes breach creation)
2. **Blocking**: Scheduler mora da čeka breach creation (ali je to brza operacija)
3. **Less decoupled**: Breach detection nije više potpuno odvojen concern
4. **Lost notifications on crash**: Ako app padne posle commit-a, notifikacije se gube (ali ovo se može recovery-ati)

### Mitigacija za izgubljene notifikacije

Dodati scheduled cleanup job:

```java
@Scheduled(fixedDelay = 300000) // Every 5 minutes
public void retryFailedNotifications() {
    // Find breaches where notification_sent = false AND created_at > 5 minutes ago
    List<SlaBreach> failedNotifications = breachRepository
        .findByNotificationSentFalseAndCreatedAtBefore(LocalDateTime.now().minusMinutes(5));

    for (SlaBreach breach : failedNotifications) {
        try {
            notificationService.sendNotificationsAsync(breach.getId());
        } catch (Exception e) {
            log.error("Retry notification failed for breach {}", breach.getId(), e);
        }
    }
}
```

---

## 🔧 Pristup 4: Database Polling (Anti-Pattern ❌)

### Opis

Umesto event-driven architecture, koristimo scheduled job koji poll-uje bazu za nove `SlaResult` zapise sa `status=BREACHED`.

### Implementacija

```java
@Scheduled(fixedDelay = 60000) // Every 1 minute
public void pollForBreaches() {
    LocalDateTime cutoff = LocalDateTime.now().minusMinutes(5);

    // Find breached results without corresponding breach records
    List<SlaResult> unprocessedBreaches = slaResultRepository
        .findByStatusAndCreatedAtAfterAndNoBreachExists(
            SlaStatus.BREACHED,
            cutoff
        );

    for (SlaResult result : unprocessedBreaches) {
        breachDetectionService.detectAndCreateBreachSync(result);
    }
}
```

### Prednosti ✅

1. **No race conditions**: Polling uvek vidi committed data
2. **Automatic retry**: Ponovno pokušava neprocessed breaches
3. **Simple**: Nema event complexity

### Mane ⚠️

1. **❌ Latency**: Kašnjenje do 1 minute pre nego što se breach procesira
2. **❌ Resource waste**: Konstantno query-uje bazu čak i kad nema posla
3. **❌ Anti-pattern**: Database kao message queue je bad practice
4. **❌ Scalability**: Ne skalira dobro sa velikim brojem SLA definitions

### Verdict: ❌ NE PREPORUČUJEM

Ovo je anti-pattern koji se koristi samo kao fallback/recovery mehanizam, ne kao primarno rešenje.

---

## 🔧 Pristup 5: Outbox Pattern (Enterprise Solution)

### Opis

Implementiramo **Transactional Outbox Pattern**: event se snima u bazu unutar iste transakcije, a zatim se asinkrono procesira.

### Implementacija

**Kreiranje Outbox tabele:**

```sql
CREATE TABLE event_outbox (
    id CHAR(36) PRIMARY KEY,
    aggregate_type VARCHAR(255) NOT NULL,  -- 'SlaResult'
    aggregate_id CHAR(36) NOT NULL,        -- SlaResult ID
    event_type VARCHAR(255) NOT NULL,       -- 'SlaResultComputedEvent'
    payload JSON NOT NULL,                  -- Event data
    created_at DATETIME NOT NULL,
    processed_at DATETIME,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING, PROCESSING, COMPLETED, FAILED
    retry_count INT DEFAULT 0,
    error_message VARCHAR(2000),

    INDEX idx_outbox_status_created (status, created_at)
);
```

**Service refaktoring:**

```java
@Transactional
public SlaResult computeSla(...) {
    // ... computation logic ...

    // STEP 8: Save result to database
    SlaResult savedResult = slaResultRepository.save(slaResult);

    // STEP 9: ✅ Save event to outbox table (same transaction!)
    EventOutbox outboxEvent = EventOutbox.builder()
        .aggregateType("SlaResult")
        .aggregateId(savedResult.getId())
        .eventType("SlaResultComputedEvent")
        .payload(toJson(savedResult))
        .createdAt(LocalDateTime.now())
        .status(OutboxStatus.PENDING)
        .build();

    eventOutboxRepository.save(outboxEvent);

    return savedResult;
}
```

**Outbox Processor (scheduled):**

```java
@Scheduled(fixedDelay = 5000) // Every 5 seconds
@Transactional
public void processOutbox() {
    List<EventOutbox> pendingEvents = eventOutboxRepository
        .findTop100ByStatusOrderByCreatedAtAsc(OutboxStatus.PENDING);

    for (EventOutbox event : pendingEvents) {
        try {
            // Mark as processing
            event.setStatus(OutboxStatus.PROCESSING);
            eventOutboxRepository.save(event);

            // Process event asynchronously
            breachDetectionService.processBreachFromOutbox(event);

            // Mark as completed
            event.setStatus(OutboxStatus.COMPLETED);
            event.setProcessedAt(LocalDateTime.now());
            eventOutboxRepository.save(event);

        } catch (Exception e) {
            event.setStatus(OutboxStatus.FAILED);
            event.setRetryCount(event.getRetryCount() + 1);
            event.setErrorMessage(e.getMessage());
            eventOutboxRepository.save(event);
        }
    }
}
```

### Prednosti ✅

1. **✅ Guaranteed delivery**: Event je garantovan jer je u bazi
2. **✅ No race conditions**: Event se procesira posle commit-a
3. **✅ Retry mechanism**: Automatski retry na failure
4. **✅ Audit trail**: Kompletan history svih events
5. **✅ Idempotency**: Lako implementirati idempotent processing

### Mane ⚠️

1. **Complexity**: Zahteva dodatnu tabelu i scheduled processor
2. **Latency**: Malo kašnjenje (do 5 sekundi) pre procesiranja
3. **Database growth**: Outbox tabela raste (potreban cleanup job)
4. **Overkill**: Možda previše kompleksno za ovaj use case

### Kada koristiti

- Microservices architecture sa distributed transactions
- Potreba za guaranteed event delivery
- Potreba za event replay/audit
- Više event consumers

---

## 📊 Poređenje Pristupa

| Pristup | Complexity | Latency | Consistency | Retry | Scalability | Preporuka |
|---------|------------|---------|-------------|-------|-------------|-----------|
| **@TransactionalEventListener** | ⭐ Low | ⭐⭐⭐ Very Low | ⭐⭐⭐ High | ⭐⭐ Medium | ⭐⭐⭐ High | ✅ **BEST** |
| **Explicit Flush** | ⭐ Low | ⭐⭐⭐ Very Low | ❌ Low | ⭐ Low | ⭐⭐ Medium | ❌ No |
| **Synchronous + Async Notify** | ⭐⭐ Medium | ⭐⭐⭐ Very Low | ⭐⭐⭐ High | ⭐⭐ Medium | ⭐⭐ Medium | ✅ **GOOD** |
| **Database Polling** | ⭐⭐ Medium | ❌ High (1min) | ⭐⭐⭐ High | ⭐⭐⭐ High | ❌ Poor | ❌ No |
| **Outbox Pattern** | ⭐⭐⭐ High | ⭐⭐ Low (5sec) | ⭐⭐⭐ High | ⭐⭐⭐ High | ⭐⭐⭐ High | ⚠️ Overkill |

---

## 🎯 Finalna Preporuka

### Primarna Preporuka: **Pristup 1 - @TransactionalEventListener** ✅

**Razlog:**
- **Simplest solution** koji rešava problem
- **Spring-native** - koristi built-in mehanizam
- **Minimal code change** - samo zamena anotacije
- **Production-proven** - široko korišćen pattern
- **No overhead** - nema dodatnih tabela ili scheduled jobs

**Implementacija:**

```java
@Async
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
@Transactional
public void onSlaResultComputed(SlaResultComputedEvent event) {
    // ... existing logic ...
}
```

### Sekundarna Preporuka: **Pristup 3 - Synchronous + Async Notify** ✅

**Razlog:**
- **Bolji ako želite atomicity** breach detection-a sa result creation-om
- **Clearer control flow** - nema event listener "magic"
- **Easier testing** - direktan poziv umesto event-driven

**Kada koristiti:**
- Ako želite da `SlaResult` i `SlaBreach` budu apsolutno sinhronizovani
- Ako vam je atomic rollback kritičan requirement
- Ako vam kontrola toka važnija od decoupling-a

### Dodatak: Recovery Job (za oba pristupa)

Implementirati cleanup job koji proverava consistency:

```java
@Scheduled(cron = "0 */15 * * * *") // Every 15 minutes
public void recoverMissedBreaches() {
    LocalDateTime cutoff = LocalDateTime.now().minusHours(1);

    // Find breached results without breach records
    List<SlaResult> orphanedBreaches = slaResultRepository
        .findBreachedWithoutBreachRecord(SlaStatus.BREACHED, cutoff);

    if (!orphanedBreaches.isEmpty()) {
        log.warn("Found {} orphaned breach results, recovering...", orphanedBreaches.size());

        for (SlaResult result : orphanedBreaches) {
            try {
                breachDetectionService.detectAndCreateBreachSync(result);
                notificationService.sendNotificationsAsync(result.getId());
            } catch (Exception e) {
                log.error("Failed to recover breach for result {}", result.getId(), e);
            }
        }
    }
}
```

---

## 📝 Implementation Checklist

Ako odlučite za **Pristup 1 (@TransactionalEventListener)**:

- [ ] Zameniti `@EventListener` sa `@TransactionalEventListener(phase = AFTER_COMMIT)`
- [ ] Testirati race condition scenario (load testing)
- [ ] Dodati recovery job za missed breaches
- [ ] Dodati monitoring/alerting za failed breach detections
- [ ] Update dokumentaciju

Ako odlučite za **Pristup 3 (Synchronous + Async Notify)**:

- [ ] Refaktorisati `SlaComputationService.computeSla()` da direktno zove breach detection
- [ ] Kreirati `detectAndCreateBreachSync()` metod
- [ ] Refaktorisati notification service za async sending
- [ ] Ukloniti ili deprecate-ovati event listener
- [ ] Dodati recovery job za failed notifications
- [ ] Testirati rollback behavior
- [ ] Update dokumentaciju

---

## 🧪 Testing Strategy

### Unit Tests

```java
@Test
void testBreachDetectionAfterCommit() {
    // Given
    SlaDefinition definition = createSlaDefinition();
    LocalDate periodDate = LocalDate.now().minusDays(1);

    // When
    SlaResult result = slaComputationService.computeSla(
        definition.getId(),
        periodDate,
        false,
        "test"
    );

    // Then - breach should be created after transaction commits
    await().atMost(5, SECONDS).until(() ->
        breachRepository.existsBySlaResult(result)
    );

    SlaBreach breach = breachRepository.findBySlaResult(result).orElseThrow();
    assertThat(breach.getSeverity()).isNotNull();
    assertThat(breach.getNotificationSent()).isTrue();
}
```

### Integration Tests

```java
@Test
@Transactional
void testNoRaceConditionBetweenSaveAndEvent() {
    // Test that async listener always sees committed data
    // Use CountDownLatch to synchronize threads
}
```

### Load Tests

```java
@Test
void testConcurrentSlaComputations() {
    // Simulate scheduler processing 100 SLA definitions concurrently
    // Verify no race conditions or missing breaches
}
```

---

## 📚 References

- [Spring @TransactionalEventListener](https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html)
- [Transaction Propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html)
- [Async Processing Best Practices](https://spring.io/guides/gs/async-method/)
- [Transactional Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)
