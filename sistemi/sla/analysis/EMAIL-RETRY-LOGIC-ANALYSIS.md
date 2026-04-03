# Email Retry Logic Analysis - SLA Breach Notifications

## 📋 Problem Statement

### Trenutna Situacija

U trenutnoj implementaciji, notifikacije se šalju **bez retry mehanizma**:

```java
private void sendNotifications(SlaBreach breach) {
    String recipients = definition.getNotificationRecipientEmails();

    try {
        // ✅ Send email notification
        List<SlaNotificationResult> emailResults =
            notificationService.sendEmailNotification(breach, recipients);

        boolean emailSent = emailResults.stream().anyMatch(r -> r.isSuccess());

        if (emailSent) {
            breach.setNotificationSent(true);
            breach.setNotificationSentAt(LocalDateTime.now());
            slaBreachRepository.save(breach);
        }
    } catch (Exception e) {
        // ❌ PROBLEM: Just log and save failure reason - NO RETRY!
        log.error("Failed to send notifications: {}", e.getMessage(), e);

        breach.setNotificationSent(false);
        breach.setNotificationFailureReason(e.getMessage());
        slaBreachRepository.save(breach);
    }
}
```

### 🚨 Problemi

1. **Single attempt**: Samo jedan pokušaj slanja email-a
2. **Transient failures**: Privremeni network problemi ili SendGrid downtime rezultuju trajnim failure-om
3. **Lost notifications**: Ako email service nije dostupan u tom momentu, notifikacija se nikad ne pošalje
4. **No visibility**: Nema način da se ponovo pošalju failed notifikacije osim manual intervention

### 📊 Tipični Failure Scenariji

- **Network timeout** (5-10 sec downtime) → Notification lost forever
- **SendGrid rate limit** → Notification lost
- **Temporary SendGrid outage** → Notification lost
- **DNS resolution failure** → Notification lost
- **SSL handshake failure** → Notification lost

---

## 🎯 Cilj

Implementirati robustan retry mehanizam koji:
1. Automatski pokušava ponovno slanje failed notifikacija
2. Koristi exponential backoff da ne preopterećuje service
3. Ima konfigurabilan max retry count
4. Persistence stanja retry pokušaja
5. Omogućava manual retry kroz API

---

## 🔧 Pristup 1: Spring @Retryable (Simplest ✅)

### Opis

Spring Retry pruža deklarativnu anotaciju `@Retryable` koja automatski retry-uje metode na exception.

### Implementacija

**1. Dodati dependency:**

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.retry</groupId>
    <artifactId>spring-retry</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-aspects</artifactId>
</dependency>
```

**2. Enable Retry:**

```java
@Configuration
@EnableRetry
public class RetryConfig {
    // Auto-configures retry infrastructure
}
```

**3. Refaktorisati MailerService sa @Retryable:**

```java
@Service
@Slf4j
public class MailerService {

    private final JavaMailSender mailSender;

    /**
     * Send email with automatic retry on transient failures.
     *
     * Retry Configuration:
     * - Max attempts: 3 (initial + 2 retries)
     * - Backoff: Start 2 sec, multiply by 2 each retry (2s, 4s, 8s)
     * - Retry on: MailException, IOException, TimeoutException
     * - Max backoff: 10 seconds (prevent excessive waiting)
     *
     * Total max time: 2s + 4s + 8s = 14 seconds
     */
    @Retryable(
        value = {MailException.class, IOException.class, TimeoutException.class},
        maxAttempts = 3,
        backoff = @Backoff(
            delay = 2000,        // Initial delay: 2 seconds
            multiplier = 2.0,    // Exponential backoff multiplier
            maxDelay = 10000     // Max delay between retries: 10 seconds
        )
    )
    public EmailSendResponseDto sendTextEmail(SendEmailRequestDto request) {
        log.info("Attempting to send email to: {}", request.getTo());

        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setTo(request.getTo());
            helper.setSubject(request.getSubject());
            helper.setText(request.getBody(), false);

            // ✅ This will be retried automatically on failure
            mailSender.send(message);

            log.info("✅ Email sent successfully to: {}", request.getTo());

            return EmailSendResponseDto.builder()
                .success(true)
                .message("Email sent successfully")
                .build();

        } catch (MessagingException e) {
            log.error("❌ MessagingException sending email to {}: {}",
                request.getTo(), e.getMessage());

            // ❌ Non-retryable exception (bad email format, etc.)
            throw new IllegalArgumentException("Invalid email format: " + e.getMessage(), e);
        }
    }

    /**
     * Recovery method called when all retry attempts are exhausted.
     * Must have same signature as @Retryable method + Throwable parameter.
     */
    @Recover
    public EmailSendResponseDto recover(MailException e, SendEmailRequestDto request) {
        log.error("❌ All retry attempts exhausted for email to {}: {}",
            request.getTo(), e.getMessage());

        return EmailSendResponseDto.builder()
            .success(false)
            .error(true)
            .message("Email delivery failed after 3 attempts: " + e.getMessage())
            .build();
    }

    @Recover
    public EmailSendResponseDto recover(IOException e, SendEmailRequestDto request) {
        log.error("❌ All retry attempts exhausted (IOException) for email to {}: {}",
            request.getTo(), e.getMessage());

        return EmailSendResponseDto.builder()
            .success(false)
            .error(true)
            .message("Email delivery failed due to network error: " + e.getMessage())
            .build();
    }

    @Recover
    public EmailSendResponseDto recover(TimeoutException e, SendEmailRequestDto request) {
        log.error("❌ All retry attempts exhausted (Timeout) for email to {}: {}",
            request.getTo(), e.getMessage());

        return EmailSendResponseDto.builder()
            .success(false)
            .error(true)
            .message("Email delivery timed out: " + e.getMessage())
            .build();
    }
}
```

**4. Update application.properties (optional advanced config):**

```properties
# Spring Retry configuration (if using properties-based config)
spring.retry.max-attempts=3
spring.retry.backoff.delay=2000
spring.retry.backoff.max-delay=10000
spring.retry.backoff.multiplier=2.0
```

### Kako radi - Timeline

```
Attempt 1 (T=0s):
    └─ Send email → MailException (SendGrid timeout)
        └─ Wait 2 seconds

Attempt 2 (T=2s):
    └─ Send email → MailException (still failing)
        └─ Wait 4 seconds (2s * 2.0 multiplier)

Attempt 3 (T=6s):
    └─ Send email → MailException (still failing)
        └─ Wait 8 seconds (4s * 2.0 multiplier, but capped at maxDelay=10s)

All retries exhausted (T=14s):
    └─ Call @Recover method
        └─ Return EmailSendResponseDto with error=true
```

### Prednosti ✅

1. **Simplest implementation**: Samo anotacija, Spring radi sve
2. **Immediate retry**: Pokušava odmah u istom thread-u
3. **No external dependencies**: Samo Spring Retry library
4. **Declarative**: Config kroz anotacije
5. **Transparent**: Pozivalac ne mora da zna za retry logiku
6. **@Recover fallback**: Explicit handling kad svi pokušaji faile

### Mane ⚠️

1. **Blocking**: Blokira thread tokom retry-eva (2s + 4s + 8s = 14 sekundi)
2. **No persistence**: Ne čuva retry attempts u bazi
3. **Lost on restart**: Ako app se restartuje tokom retry-a, gubi se
4. **Synchronous only**: Radi samo sa synchronous methods
5. **Limited visibility**: Teško pratiti koliko retry-eva se desilo

### Kada koristiti

- **Quick wins**: Ako želite brzo rešenje koje pokriva 80% failure scenarios
- **Transient failures**: Kada su failures obično kratkog trajanja (< 15 sec)
- **Low volume**: Manji broj notifikacija (ne scale-uje za hiljadednevno)

---

## 🔧 Pristup 2: Async Retry sa Scheduled Cleanup Job (Balanced ✅)

### Opis

Kombinacija immediate retry-a + scheduled job koji pokušava ponovo poslati failed notifikacije.

### Implementacija

**1. Dodati retry tracking fields u SlaBreach:**

```java
@Entity
@Table(name = "sla_breach")
public class SlaBreach extends BaseEntity {

    // ... existing fields ...

    // ========== Retry Tracking ==========

    @Column(name = "notification_retry_count", nullable = false)
    private Integer notificationRetryCount = 0;

    @Column(name = "notification_last_retry_at")
    private LocalDateTime notificationLastRetryAt;

    @Column(name = "notification_next_retry_at")
    private LocalDateTime notificationNextRetryAt;

    @Column(name = "notification_max_retries_reached", nullable = false)
    private Boolean notificationMaxRetriesReached = false;

    // Business logic methods
    public boolean shouldRetryNotification() {
        if (notificationMaxRetriesReached) {
            return false;
        }
        if (notificationSent) {
            return false;
        }
        if (notificationNextRetryAt == null) {
            return true; // First retry
        }
        return LocalDateTime.now().isAfter(notificationNextRetryAt);
    }

    public void recordRetryAttempt(boolean success) {
        notificationLastRetryAt = LocalDateTime.now();
        notificationRetryCount++;

        if (success) {
            notificationSent = true;
            notificationSentAt = LocalDateTime.now();
            notificationNextRetryAt = null;
        } else {
            // Exponential backoff: 5min, 15min, 45min, 2h, 6h
            long backoffMinutes = (long) (5 * Math.pow(3, notificationRetryCount - 1));
            backoffMinutes = Math.min(backoffMinutes, 360); // Cap at 6 hours

            notificationNextRetryAt = LocalDateTime.now().plusMinutes(backoffMinutes);

            // Max 5 retries
            if (notificationRetryCount >= 5) {
                notificationMaxRetriesReached = true;
            }
        }
    }
}
```

**2. Migration script:**

```sql
-- V10__add_notification_retry_fields.sql
ALTER TABLE sla_breach
    ADD COLUMN notification_retry_count INT NOT NULL DEFAULT 0,
    ADD COLUMN notification_last_retry_at DATETIME,
    ADD COLUMN notification_next_retry_at DATETIME,
    ADD COLUMN notification_max_retries_reached BOOLEAN NOT NULL DEFAULT FALSE,
    ADD INDEX idx_breach_retry (notification_sent, notification_next_retry_at, notification_max_retries_reached);
```

**3. Refaktorisati sendNotifications sa retry tracking:**

```java
private void sendNotifications(SlaBreach breach) {
    SlaDefinition definition = breach.getSlaResult().getSlaDefinition();
    String recipients = definition.getNotificationRecipientEmails();

    if (recipients == null || recipients.trim().isEmpty()) {
        log.warn("No recipients configured, skipping");
        return;
    }

    try {
        // ✅ Attempt to send
        List<SlaNotificationResult> emailResults =
            notificationService.sendEmailNotification(breach, recipients);

        boolean success = emailResults.stream().anyMatch(r -> r.isSuccess());

        // ✅ Record retry attempt with result
        breach.recordRetryAttempt(success);

        if (success) {
            String recipientsSuccess = emailResults.stream()
                .filter(r -> r.isSuccess())
                .map(SlaNotificationResult::getRecipient)
                .collect(Collectors.joining(", "));

            breach.setNotificationRecipientEmails(recipientsSuccess);
            log.info("✅ Notifications sent successfully (attempt {})", breach.getNotificationRetryCount());
        } else {
            String failureReason = emailResults.stream()
                .filter(r -> !r.isSuccess())
                .map(SlaNotificationResult::getMessage)
                .collect(Collectors.joining("; "));

            breach.setNotificationFailureReason(failureReason);
            log.warn("❌ Notification failed (attempt {}), will retry at {}",
                breach.getNotificationRetryCount(),
                breach.getNotificationNextRetryAt());
        }

        slaBreachRepository.save(breach);

    } catch (Exception e) {
        log.error("❌ Exception sending notifications (attempt {}): {}",
            breach.getNotificationRetryCount() + 1, e.getMessage(), e);

        breach.recordRetryAttempt(false);
        breach.setNotificationFailureReason(e.getMessage());
        slaBreachRepository.save(breach);
    }
}
```

**4. Scheduled Retry Job:**

```java
@Component
@Slf4j
@RequiredArgsConstructor
public class BreachNotificationRetryScheduler {

    private final SlaBreachRepository breachRepository;
    private final SlaNotificationService notificationService;

    /**
     * Retry failed notifications.
     * Runs every 5 minutes.
     */
    @Scheduled(fixedDelay = 300000) // 5 minutes
    public void retryFailedNotifications() {
        log.debug("Starting notification retry job...");

        LocalDateTime now = LocalDateTime.now();

        // Find breaches that need retry
        List<SlaBreach> breachesToRetry = breachRepository.findAll().stream()
            .filter(SlaBreach::shouldRetryNotification)
            .collect(Collectors.toList());

        if (breachesToRetry.isEmpty()) {
            log.debug("No breaches need notification retry");
            return;
        }

        log.info("Found {} breaches needing notification retry", breachesToRetry.size());

        int successCount = 0;
        int failedCount = 0;

        for (SlaBreach breach : breachesToRetry) {
            try {
                log.info("Retrying notification for breach {} (attempt {})",
                    breach.getId(), breach.getNotificationRetryCount() + 1);

                SlaDefinition definition = breach.getSlaResult().getSlaDefinition();
                String recipients = definition.getNotificationRecipientEmails();

                List<SlaNotificationResult> results =
                    notificationService.sendEmailNotification(breach, recipients);

                boolean success = results.stream().anyMatch(r -> r.isSuccess());
                breach.recordRetryAttempt(success);

                if (success) {
                    String recipientsSuccess = results.stream()
                        .filter(r -> r.isSuccess())
                        .map(SlaNotificationResult::getRecipient)
                        .collect(Collectors.joining(", "));

                    breach.setNotificationRecipientEmails(recipientsSuccess);
                    breach.setNotificationFailureReason(null);
                    successCount++;

                    log.info("✅ Retry successful for breach {} after {} attempts",
                        breach.getId(), breach.getNotificationRetryCount());
                } else {
                    failedCount++;
                    log.warn("❌ Retry failed for breach {}, will try again at {}",
                        breach.getId(), breach.getNotificationNextRetryAt());
                }

                breachRepository.save(breach);

            } catch (Exception e) {
                failedCount++;
                log.error("❌ Exception during retry for breach {}: {}",
                    breach.getId(), e.getMessage(), e);

                breach.recordRetryAttempt(false);
                breach.setNotificationFailureReason(e.getMessage());
                breachRepository.save(breach);
            }

            // Small delay between retries to avoid overwhelming email service
            try {
                Thread.sleep(1000); // 1 second between emails
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }

        log.info("Notification retry job completed: {} successful, {} failed", successCount, failedCount);
    }

    /**
     * Alert on max retries reached.
     * Runs every hour.
     */
    @Scheduled(cron = "0 0 * * * *") // Every hour
    public void alertOnMaxRetriesReached() {
        List<SlaBreach> maxRetriedBreaches = breachRepository
            .findByNotificationMaxRetriesReachedTrueAndNotificationSentFalse();

        if (!maxRetriedBreaches.isEmpty()) {
            log.error("⚠️ {} breaches have reached max retry attempts and still not sent!",
                maxRetriedBreaches.size());

            // TODO: Send alert to ops team
            // alertService.sendOperationalAlert("SLA notifications failing", ...);
        }
    }
}
```

**5. Repository query methods:**

```java
@Repository
public interface SlaBreachRepository extends JpaRepository<SlaBreach, UUID> {

    // ... existing methods ...

    /**
     * Find breaches with max retries reached but notification not sent.
     * Used for alerting.
     */
    @Query("SELECT sb FROM SlaBreach sb " +
           "WHERE sb.notificationMaxRetriesReached = true " +
           "AND sb.notificationSent = false")
    List<SlaBreach> findByNotificationMaxRetriesReachedTrueAndNotificationSentFalse();

    /**
     * Find breaches needing retry (for repository-based filtering if needed).
     */
    @Query("SELECT sb FROM SlaBreach sb " +
           "WHERE sb.notificationSent = false " +
           "AND sb.notificationMaxRetriesReached = false " +
           "AND (sb.notificationNextRetryAt IS NULL OR sb.notificationNextRetryAt <= :now)")
    List<SlaBreach> findBreachesNeedingRetry(@Param("now") LocalDateTime now);
}
```

### Exponential Backoff Schedule

```
Attempt 1: Immediate (within breach detection)
           └─ Fail → Next retry in 5 minutes

Attempt 2: T + 5 min
           └─ Fail → Next retry in 15 minutes (5 * 3^1)

Attempt 3: T + 20 min (5 + 15)
           └─ Fail → Next retry in 45 minutes (5 * 3^2)

Attempt 4: T + 65 min (5 + 15 + 45)
           └─ Fail → Next retry in 135 minutes = 2h 15min (5 * 3^3)

Attempt 5: T + 200 min (3h 20min)
           └─ Fail → Next retry in 360 minutes = 6 hours (5 * 3^4, capped)

Attempt 6: T + 560 min (9h 20min)
           └─ Fail → Max retries reached, alert ops team
```

### Prednosti ✅

1. **Persistent retry state**: Sve se čuva u bazi
2. **Survives restarts**: App restart ne utiče na retry schedule
3. **Exponential backoff**: Progresivno duži intervali između retry-a
4. **Bounded retries**: Max 5 pokušaja, ne pokušava beskonačno
5. **Visibility**: Jasno vidljivo u bazi koliko retry-eva se desilo
6. **Non-blocking**: Ne blokira scheduler thread
7. **Alerting**: Automatic alert kad max retries dostignut
8. **Manual retry**: Može se ručno retry-ovati (reset next_retry_at)

### Mane ⚠️

1. **Delayed retry**: Minimalno 5 minuta do prvog retry-a
2. **More complex**: Zahteva dodatne DB fields i scheduled job
3. **Database growth**: Dodatni fields povećavaju row size
4. **Scheduler dependency**: Zavisi od scheduled job da radi

### Kada koristiti

- **Production-grade solution**: Robust rešenje za production
- **Medium-high volume**: Skalira sa većim brojem notifikacija
- **Audit requirements**: Potreba za tracking retry attempts
- **Operational visibility**: Ops tim treba da vidi retry status

---

## 🔧 Pristup 3: Message Queue (Kafka/RabbitMQ) - Enterprise ✅

### Opis

Koristi message queue za guaranteed delivery sa built-in retry mehanizmom.

### Implementacija

**1. Dodati RabbitMQ dependency:**

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-amqp</artifactId>
</dependency>
```

**2. RabbitMQ Configuration:**

```java
@Configuration
public class RabbitMQConfig {

    public static final String BREACH_NOTIFICATION_QUEUE = "sla.breach.notification";
    public static final String BREACH_NOTIFICATION_EXCHANGE = "sla.breach.exchange";
    public static final String BREACH_NOTIFICATION_DLQ = "sla.breach.notification.dlq";

    @Bean
    public Queue breachNotificationQueue() {
        return QueueBuilder.durable(BREACH_NOTIFICATION_QUEUE)
            .withArgument("x-dead-letter-exchange", "")
            .withArgument("x-dead-letter-routing-key", BREACH_NOTIFICATION_DLQ)
            .build();
    }

    @Bean
    public Queue deadLetterQueue() {
        return new Queue(BREACH_NOTIFICATION_DLQ, true);
    }

    @Bean
    public DirectExchange breachExchange() {
        return new DirectExchange(BREACH_NOTIFICATION_EXCHANGE);
    }

    @Bean
    public Binding binding(Queue breachNotificationQueue, DirectExchange breachExchange) {
        return BindingBuilder.bind(breachNotificationQueue)
            .to(breachExchange)
            .with("breach.notification");
    }

    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);
        template.setMessageConverter(new Jackson2JsonMessageConverter());

        // Configure retry
        template.setRetryTemplate(retryTemplate());

        return template;
    }

    private RetryTemplate retryTemplate() {
        RetryTemplate retryTemplate = new RetryTemplate();

        // Exponential backoff: 1s, 2s, 4s, 8s, 16s
        ExponentialBackOffPolicy backOffPolicy = new ExponentialBackOffPolicy();
        backOffPolicy.setInitialInterval(1000);
        backOffPolicy.setMultiplier(2.0);
        backOffPolicy.setMaxInterval(16000);

        retryTemplate.setBackOffPolicy(backOffPolicy);

        // Max 5 attempts
        SimpleRetryPolicy retryPolicy = new SimpleRetryPolicy();
        retryPolicy.setMaxAttempts(5);
        retryTemplate.setRetryPolicy(retryPolicy);

        return retryTemplate;
    }
}
```

**3. Breach Notification Message:**

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BreachNotificationMessage {
    private UUID breachId;
    private String recipients;
    private Integer attemptCount;
    private LocalDateTime scheduledAt;
}
```

**4. Refaktorisati SlaBreachDetectionService:**

```java
@Service
@RequiredArgsConstructor
public class SlaBreachDetectionService {

    private final RabbitTemplate rabbitTemplate;

    private void sendNotifications(SlaBreach breach) {
        SlaDefinition definition = breach.getSlaResult().getSlaDefinition();
        String recipients = definition.getNotificationRecipientEmails();

        // ✅ Publish to message queue instead of direct send
        BreachNotificationMessage message = BreachNotificationMessage.builder()
            .breachId(breach.getId())
            .recipients(recipients)
            .attemptCount(0)
            .scheduledAt(LocalDateTime.now())
            .build();

        rabbitTemplate.convertAndSend(
            RabbitMQConfig.BREACH_NOTIFICATION_EXCHANGE,
            "breach.notification",
            message
        );

        log.info("✅ Breach notification queued for breach {}", breach.getId());
    }
}
```

**5. Message Consumer:**

```java
@Component
@Slf4j
@RequiredArgsConstructor
public class BreachNotificationConsumer {

    private final SlaBreachRepository breachRepository;
    private final SlaNotificationService notificationService;

    /**
     * Consume breach notification messages.
     * RabbitMQ will automatically retry on exception.
     */
    @RabbitListener(queues = RabbitMQConfig.BREACH_NOTIFICATION_QUEUE)
    @Transactional
    public void processBreachNotification(BreachNotificationMessage message) {
        log.info("Processing breach notification for breach {} (attempt {})",
            message.getBreachId(), message.getAttemptCount() + 1);

        SlaBreach breach = breachRepository.findById(message.getBreachId())
            .orElseThrow(() -> new IllegalArgumentException("Breach not found: " + message.getBreachId()));

        if (breach.getNotificationSent()) {
            log.info("Notification already sent for breach {}, skipping", breach.getId());
            return; // Idempotency check
        }

        try {
            // ✅ Attempt to send
            List<SlaNotificationResult> results =
                notificationService.sendEmailNotification(breach, message.getRecipients());

            boolean success = results.stream().anyMatch(r -> r.isSuccess());

            if (success) {
                String recipientsSuccess = results.stream()
                    .filter(r -> r.isSuccess())
                    .map(SlaNotificationResult::getRecipient)
                    .collect(Collectors.joining(", "));

                breach.setNotificationSent(true);
                breach.setNotificationSentAt(LocalDateTime.now());
                breach.setNotificationRecipientEmails(recipientsSuccess);
                breachRepository.save(breach);

                log.info("✅ Notification sent successfully for breach {}", breach.getId());
            } else {
                // ❌ All recipients failed - throw to trigger retry
                throw new MailSendException("All recipients failed");
            }

        } catch (Exception e) {
            log.error("❌ Failed to send notification for breach {}: {}",
                breach.getId(), e.getMessage());

            // Update failure reason
            breach.setNotificationFailureReason(e.getMessage());
            breachRepository.save(breach);

            // ❌ Re-throw to trigger RabbitMQ retry
            throw new AmqpRejectAndDontRequeueException("Failed to send notification", e);
        }
    }

    /**
     * Handle messages from Dead Letter Queue.
     * These are messages that failed after all retry attempts.
     */
    @RabbitListener(queues = RabbitMQConfig.BREACH_NOTIFICATION_DLQ)
    public void handleDeadLetter(BreachNotificationMessage message) {
        log.error("⚠️ Breach notification exhausted all retries: {}", message.getBreachId());

        // TODO: Send alert to ops team
        // alertService.sendOperationalAlert("SLA notification permanently failed", ...);

        // Optionally update breach record
        breachRepository.findById(message.getBreachId()).ifPresent(breach -> {
            breach.setNotificationMaxRetriesReached(true);
            breach.setNotificationFailureReason("Exhausted all retry attempts");
            breachRepository.save(breach);
        });
    }
}
```

### Prednosti ✅

1. **Guaranteed delivery**: Message queue garantuje delivery
2. **Built-in retry**: RabbitMQ ima built-in retry mehanizam
3. **Decoupling**: Kompletno odvajanje breach detection od notification sending
4. **Scalability**: Može se horizontalno skalirati sa više consumer-a
5. **Durability**: Messages survive app restarts
6. **Dead Letter Queue**: Automatic handling failed messages
7. **Monitoring**: RabbitMQ UI za monitoring queue depth, throughput, etc.
8. **Priority queues**: Može se dodati prioritization (CRITICAL breaches first)

### Mane ⚠️

1. **Infrastructure complexity**: Zahteva RabbitMQ server
2. **Operational overhead**: Još jedan service za maintain
3. **Network dependency**: Dodatni network hop
4. **Overkill**: Možda previše kompleksno za ovaj use case
5. **Cost**: RabbitMQ hosting (ako cloud-hosted)

### Kada koristiti

- **Microservices architecture**: Već koristite message queue u arhitekturi
- **High volume**: Hiljade notifikacija dnevno
- **Multiple consumers**: Potreba za parallel processing
- **Complex workflows**: Više koraka u notification pipeline-u
- **Enterprise requirements**: Strict SLA za notification delivery

---

## 🔧 Pristup 4: Hybrid - Spring @Retryable + Scheduled Cleanup

### Opis

Kombinacija immediate retry-a (@Retryable) + scheduled cleanup job za permanentne failure-e.

### Implementacija

**1. Immediate retry sa @Retryable (kao Pristup 1)**

```java
@Retryable(
    value = {MailException.class, IOException.class},
    maxAttempts = 3,
    backoff = @Backoff(delay = 2000, multiplier = 2.0)
)
public EmailSendResponseDto sendTextEmail(SendEmailRequestDto request) {
    // ... send logic ...
}
```

**2. Dodati retry fields u SlaBreach (kao Pristup 2)**

```java
private Integer notificationRetryCount = 0;
private LocalDateTime notificationNextRetryAt;
private Boolean notificationMaxRetriesReached = false;
```

**3. Update sendNotifications sa tracking:**

```java
private void sendNotifications(SlaBreach breach) {
    try {
        // ✅ Immediate retry handled by @Retryable (3 attempts over ~14 sec)
        List<SlaNotificationResult> results =
            notificationService.sendEmailNotification(breach, recipients);

        boolean success = results.stream().anyMatch(r -> r.isSuccess());
        breach.recordRetryAttempt(success);
        slaBreachRepository.save(breach);

    } catch (Exception e) {
        // ❌ All immediate retries failed, schedule for later retry
        breach.recordRetryAttempt(false);
        breach.setNotificationNextRetryAt(LocalDateTime.now().plusMinutes(15));
        slaBreachRepository.save(breach);
    }
}
```

**4. Scheduled cleanup job (svakih 15 minuta):**

```java
@Scheduled(fixedDelay = 900000) // 15 minutes
public void retryFailedNotifications() {
    List<SlaBreach> breachesToRetry = breachRepository.findAll().stream()
        .filter(SlaBreach::shouldRetryNotification)
        .collect(Collectors.toList());

    for (SlaBreach breach : breachesToRetry) {
        // Will use @Retryable again
        notificationService.sendNotificationsAsync(breach.getId());
    }
}
```

### Prednosti ✅

1. **Best of both worlds**: Immediate + delayed retry
2. **Quick transient recovery**: @Retryable pokriva kratke outage-e (< 15 sec)
3. **Long-term recovery**: Scheduled job pokriva duže outage-e
4. **Simple**: Kombinuje dva jednostavna pristupa
5. **Visibility**: Tracking u bazi + @Retryable transparentnost

### Mane ⚠️

1. **Duplication**: Dva različita retry mehanizma
2. **Complexity**: Treba maintain oba
3. **Potential overlap**: Scheduled job može retry-ovati dok je @Retryable još aktivan (mali rizik)

### Kada koristiti

- **Pragmatic solution**: Balans između simplicity i robustness
- **Most common use case**: Pokriva 95% scenarija

---

## 📊 Poređenje Pristupa

| Pristup | Complexity | Immediate Retry | Persistent | Survives Restart | Alerting | Scalability | Preporuka |
|---------|------------|-----------------|------------|------------------|----------|-------------|-----------|
| **@Retryable** | ⭐ Low | ✅ Yes (14s) | ❌ No | ❌ No | ❌ No | ⭐⭐ Medium | ✅ **Quick Win** |
| **Scheduled + Tracking** | ⭐⭐ Medium | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ⭐⭐⭐ High | ✅ **BEST** |
| **RabbitMQ** | ⭐⭐⭐ High | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⭐⭐⭐ Very High | ⚠️ Overkill |
| **Hybrid** | ⭐⭐ Medium | ✅ Yes (14s) | ✅ Yes | ✅ Yes | ✅ Yes | ⭐⭐⭐ High | ✅ **GOOD** |

---

## 🎯 Finalna Preporuka

### Primarna Preporuka: **Pristup 2 - Scheduled Retry sa Tracking** ✅

**Razlog:**
- **Production-ready**: Robust solution za production environment
- **Persistent**: Sve retry attempts tracked u bazi
- **Survives restarts**: Ne gubi se state na app restart
- **Exponential backoff**: Pametno raspoređivanje retry-a
- **Bounded retries**: Ne pokušava beskonačno
- **Visibility**: Jasno vidljivo u bazi i monitoring-u
- **Alerting**: Automatic alert na max retries

**Implementation effort:** ~4-6 sati (migration + code + testing)

### Alternativa: **Pristup 4 - Hybrid (@Retryable + Scheduled)** ✅

**Razlog:**
- **Quick transient recovery**: @Retryable pokriva 80% failure-a
- **Long-term recovery**: Scheduled job za remaining 20%
- **Pragmatic**: Balans complexity vs robustness

**Implementation effort:** ~3-4 sata

### Za buduća scaling: **Pristup 3 - RabbitMQ**

**Kada implementirati:**
- Kada dosegnete > 1000 notifikacija/dan
- Kada dodajete više consumer-a
- Kada trebate complex notification workflows
- Kada već imate message queue infrastructure

---

## 📝 Implementation Checklist

Za **Pristup 2 (Scheduled Retry)**:

- [ ] Dodati retry tracking fields u `SlaBreach` entitet
- [ ] Kreirati migration `V10__add_notification_retry_fields.sql`
- [ ] Implementirati `SlaBreach.recordRetryAttempt()` metod
- [ ] Implementirati `SlaBreach.shouldRetryNotification()` metod
- [ ] Refaktorisati `sendNotifications()` sa retry tracking
- [ ] Kreirati `BreachNotificationRetryScheduler` component
- [ ] Dodati repository queries za retry lookup
- [ ] Implementirati `alertOnMaxRetriesReached()` scheduled job
- [ ] Dodati monitoring/alerting za max retries
- [ ] Dodati unit tests za retry logic
- [ ] Dodati integration tests za scheduled job
- [ ] Update dokumentaciju

---

## 🧪 Testing Strategy

### Unit Tests

```java
@Test
void testRecordRetryAttemptSuccess() {
    SlaBreach breach = new SlaBreach();

    breach.recordRetryAttempt(true);

    assertThat(breach.getNotificationSent()).isTrue();
    assertThat(breach.getNotificationRetryCount()).isEqualTo(1);
    assertThat(breach.getNotificationNextRetryAt()).isNull();
}

@Test
void testRecordRetryAttemptFailure_ExponentialBackoff() {
    SlaBreach breach = new SlaBreach();

    breach.recordRetryAttempt(false);
    LocalDateTime firstRetry = breach.getNotificationNextRetryAt();
    // Should be ~5 minutes from now
    assertThat(firstRetry).isAfter(LocalDateTime.now().plusMinutes(4));

    breach.recordRetryAttempt(false);
    LocalDateTime secondRetry = breach.getNotificationNextRetryAt();
    // Should be ~15 minutes from now (5 * 3^1)
    assertThat(secondRetry).isAfter(LocalDateTime.now().plusMinutes(14));
}

@Test
void testMaxRetriesReached() {
    SlaBreach breach = new SlaBreach();

    for (int i = 0; i < 5; i++) {
        breach.recordRetryAttempt(false);
    }

    assertThat(breach.getNotificationMaxRetriesReached()).isTrue();
    assertThat(breach.shouldRetryNotification()).isFalse();
}
```

### Integration Tests

```java
@SpringBootTest
@Transactional
class BreachNotificationRetrySchedulerTest {

    @Test
    void testScheduledRetryJob() throws InterruptedException {
        // Create breach with failed notification
        SlaBreach breach = createBreachWithFailedNotification();
        breach.setNotificationNextRetryAt(LocalDateTime.now());
        breachRepository.save(breach);

        // Trigger scheduled job
        retryScheduler.retryFailedNotifications();

        // Verify retry attempt
        SlaBreach updated = breachRepository.findById(breach.getId()).orElseThrow();
        assertThat(updated.getNotificationRetryCount()).isGreaterThan(0);
    }
}
```

---

## 📚 References

- [Spring Retry Documentation](https://docs.spring.io/spring-retry/docs/current/reference/html/)
- [Exponential Backoff Best Practices](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [RabbitMQ Reliability Guide](https://www.rabbitmq.com/reliability.html)
- [Email Delivery Best Practices](https://sendgrid.com/blog/email-delivery-best-practices/)
