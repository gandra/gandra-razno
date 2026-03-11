# Webhook Notifications Analysis - SLA Breach Webhooks

## 📋 Problem Statement

### Trenutna Situacija

SLA breach notifications currently only support **email**:

```java
// SlaNotificationService.java
public List<SlaNotificationResult> sendEmailNotification(SlaBreach breach, String recipients) {
    // Send emails via MailerService (SendGrid)
    ...
}

// TODO comment exists:
// TODO: Send webhook notification (configurable via application.properties)
// boolean webhookSent = notificationService.sendWebhookNotification(breach, webhookUrl);
```

### 🚨 Problemi

1. **No webhook support**: Nema integration sa external systems (Slack, PagerDuty, custom apps)
2. **Email only**: Limited notification channels
3. **No real-time alerts**: Email je slower od webhook-a
4. **No automation**: Ne može da triggeru automation workflows
5. **No integration with incident management**: Ne može da kreira tickets u Jira, ServiceNow, etc.

### 🎯 Use Cases za Webhooks

1. **Slack/Teams notifications**: Real-time alerts u team channels
2. **PagerDuty/OpsGenie**: Automatic incident creation
3. **Jira/ServiceNow**: Auto-create tickets za breaches
4. **Custom automation**: Trigger custom remediation scripts
5. **Monitoring systems**: Integration sa Prometheus, Grafana, Datadog
6. **Audit systems**: Log events u SIEM (Splunk, ElasticSearch)

---

## 🎯 Cilj

Implementirati webhook notification sistem koji omogućava:

1. **Multiple webhooks**: Support za više webhook URLs po SLA definition
2. **Configurable payloads**: Custom payload templates
3. **Retry mechanism**: Automatic retry na failure
4. **Security**: HMAC signature verification
5. **Webhook management**: CRUD API za webhook configuration
6. **Event types**: Different webhooks za different events (breach detected, resolved, etc.)
7. **Monitoring**: Track webhook delivery success/failure

---

## 🔧 Pristup 1: Simple Webhook Support (Quick Win ✅)

### Opis

Osnovni webhook support - POST request sa JSON payload.

### Implementacija

**1. Add webhook URL to SlaDefinition:**

```java
@Entity
@Table(name = "sla_definition")
public class SlaDefinition extends BaseEntity {

    // ... existing fields ...

    /**
     * Webhook URL for breach notifications.
     * If null, no webhook is sent.
     */
    @Column(name = "webhook_url", length = 2000)
    private String webhookUrl;

    /**
     * Webhook secret for HMAC signature verification.
     * Used by receiver to verify authenticity.
     */
    @Column(name = "webhook_secret", length = 255)
    private String webhookSecret;
}
```

**2. Migration:**

```sql
-- V12__add_webhook_support.sql
ALTER TABLE sla_definition
    ADD COLUMN webhook_url VARCHAR(2000),
    ADD COLUMN webhook_secret VARCHAR(255);
```

**3. Webhook Payload DTO:**

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SlaBreachWebhookPayload {

    private String eventType; // "sla.breach.detected", "sla.breach.resolved"
    private LocalDateTime timestamp;

    // Breach details
    private BreachInfo breach;

    // SLA definition details
    private SlaInfo sla;

    // Result details
    private ResultInfo result;

    @Data
    @Builder
    public static class BreachInfo {
        private UUID breachId;
        private String severity; // CRITICAL, HIGH, MEDIUM, LOW
        private LocalDateTime detectedAt;
        private Integer breachDurationMinutes;
        private BigDecimal actualValue;
        private BigDecimal thresholdValue;
        private BigDecimal deviationPercent;
        private String description;
    }

    @Data
    @Builder
    public static class SlaInfo {
        private UUID slaId;
        private String slaName;
        private String metricName;
        private String metricNamespace;
        private BigDecimal targetValue;
        private String targetType; // PERCENT, PENALTY
    }

    @Data
    @Builder
    public static class ResultInfo {
        private UUID resultId;
        private LocalDateTime periodStart;
        private LocalDateTime periodEnd;
        private SlaStatus status;
        private BigDecimal compliancePercent;
        private BigDecimal dataCoveragePercent;
    }
}
```

**4. Webhook Service:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class WebhookService {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    /**
     * Send webhook notification.
     *
     * @param webhookUrl Target webhook URL
     * @param payload Payload to send
     * @param secret HMAC secret for signature (optional)
     * @return true if successful, false otherwise
     */
    public boolean sendWebhook(String webhookUrl, Object payload, String secret) {
        try {
            // Serialize payload to JSON
            String jsonPayload = objectMapper.writeValueAsString(payload);

            // Create HTTP request
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("User-Agent", "OCI-SLA-Monitor/1.0");

            // Add HMAC signature if secret provided
            if (secret != null && !secret.isEmpty()) {
                String signature = generateHmacSignature(jsonPayload, secret);
                headers.set("X-Webhook-Signature", signature);
                headers.set("X-Webhook-Signature-Algorithm", "HmacSHA256");
            }

            HttpEntity<String> request = new HttpEntity<>(jsonPayload, headers);

            log.info("Sending webhook to: {}", webhookUrl);
            log.debug("Webhook payload: {}", jsonPayload);

            // Send POST request with 5 second timeout
            ResponseEntity<String> response = restTemplate.exchange(
                    webhookUrl,
                    HttpMethod.POST,
                    request,
                    String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("✅ Webhook sent successfully to: {} (status: {})",
                        webhookUrl, response.getStatusCode());
                return true;
            } else {
                log.warn("❌ Webhook failed with status: {} - Response: {}",
                        response.getStatusCode(), response.getBody());
                return false;
            }

        } catch (Exception e) {
            log.error("❌ Webhook send failed to {}: {}",
                    webhookUrl, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Generate HMAC SHA-256 signature.
     */
    private String generateHmacSignature(String payload, String secret) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKeySpec = new SecretKeySpec(
                    secret.getBytes(StandardCharsets.UTF_8),
                    "HmacSHA256"
            );
            mac.init(secretKeySpec);

            byte[] hash = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));

            // Return hex-encoded signature
            return bytesToHex(hash);

        } catch (Exception e) {
            log.error("Failed to generate HMAC signature", e);
            throw new RuntimeException("HMAC generation failed", e);
        }
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte b : bytes) {
            result.append(String.format("%02x", b));
        }
        return result.toString();
    }
}
```

**5. Configure RestTemplate with timeouts:**

```java
@Configuration
public class WebhookConfig {

    @Bean
    @Qualifier("webhookRestTemplate")
    public RestTemplate webhookRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000); // 5 seconds
        factory.setReadTimeout(5000);    // 5 seconds

        return new RestTemplate(factory);
    }
}
```

**6. Update SlaNotificationService:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class SlaNotificationService {

    private final MailerService mailerService;
    private final WebhookService webhookService;

    public void sendNotifications(SlaBreach breach) {
        SlaDefinition definition = breach.getSlaResult().getSlaDefinition();

        // Send email notifications
        String emailRecipients = definition.getNotificationRecipientEmails();
        if (emailRecipients != null && !emailRecipients.isEmpty()) {
            sendEmailNotification(breach, emailRecipients);
        }

        // ✅ Send webhook notification
        String webhookUrl = definition.getWebhookUrl();
        if (webhookUrl != null && !webhookUrl.isEmpty()) {
            sendWebhookNotification(breach, webhookUrl, definition.getWebhookSecret());
        }
    }

    /**
     * Send webhook notification for breach.
     */
    public boolean sendWebhookNotification(SlaBreach breach, String webhookUrl, String secret) {
        log.info("Sending webhook notification for breach: {}", breach.getId());

        // Build payload
        SlaBreachWebhookPayload payload = buildWebhookPayload(breach, "sla.breach.detected");

        // Send webhook
        boolean success = webhookService.sendWebhook(webhookUrl, payload, secret);

        if (success) {
            // Update breach record
            breach.setWebhookSent(true); // Add this field to SlaBreach
            breach.setWebhookSentAt(LocalDateTime.now());
        }

        return success;
    }

    /**
     * Build webhook payload from breach entity.
     */
    private SlaBreachWebhookPayload buildWebhookPayload(SlaBreach breach, String eventType) {
        SlaResult result = breach.getSlaResult();
        SlaDefinition definition = result.getSlaDefinition();

        return SlaBreachWebhookPayload.builder()
                .eventType(eventType)
                .timestamp(LocalDateTime.now())
                .breach(SlaBreachWebhookPayload.BreachInfo.builder()
                        .breachId(breach.getId())
                        .severity(breach.getSeverity())
                        .detectedAt(breach.getDetectedAt())
                        .breachDurationMinutes(breach.getBreachDurationMinutes())
                        .actualValue(breach.getActualValue())
                        .thresholdValue(breach.getThresholdValue())
                        .deviationPercent(breach.getDeviationPercent())
                        .description(breach.getDescription())
                        .build())
                .sla(SlaBreachWebhookPayload.SlaInfo.builder()
                        .slaId(definition.getId())
                        .slaName(definition.getName())
                        .metricName(definition.getMetricName())
                        .metricNamespace(definition.getMetricNamespace())
                        .targetValue(definition.getTargetValue())
                        .targetType(definition.getTargetType().name())
                        .build())
                .result(SlaBreachWebhookPayload.ResultInfo.builder()
                        .resultId(result.getId())
                        .periodStart(result.getPeriodStart())
                        .periodEnd(result.getPeriodEnd())
                        .status(result.getStatus())
                        .compliancePercent(result.getCompliancePercent())
                        .dataCoveragePercent(result.getDataCoveragePercent())
                        .build())
                .build();
    }
}
```

**7. Add webhook fields to SlaBreach:**

```java
@Entity
@Table(name = "sla_breach")
public class SlaBreach extends BaseEntity {

    // ... existing fields ...

    @Column(name = "webhook_sent", nullable = false)
    private Boolean webhookSent = false;

    @Column(name = "webhook_sent_at")
    private LocalDateTime webhookSentAt;

    @Column(name = "webhook_failure_reason", length = 500)
    private String webhookFailureReason;
}
```

### Example Webhook Payload

```json
{
  "eventType": "sla.breach.detected",
  "timestamp": "2025-11-13T10:30:15",
  "breach": {
    "breachId": "breach-abc-123",
    "severity": "CRITICAL",
    "detectedAt": "2025-11-13T10:30:00",
    "breachDurationMinutes": 120,
    "actualValue": 88.50,
    "thresholdValue": 95.00,
    "deviationPercent": 6.50,
    "description": "CRITICAL severity SLA breach detected. Compliance dropped to 88.50% (target: 95.00%)"
  },
  "sla": {
    "slaId": "sla-def-456",
    "slaName": "Production API Availability",
    "metricName": "CpuUtilization",
    "metricNamespace": "oci_computeagent",
    "targetValue": 95.00,
    "targetType": "PERCENT"
  },
  "result": {
    "resultId": "result-789",
    "periodStart": "2025-11-12T00:00:00",
    "periodEnd": "2025-11-13T00:00:00",
    "status": "BREACHED",
    "compliancePercent": 88.50,
    "dataCoveragePercent": 99.86
  }
}
```

### HMAC Signature Verification (Receiver Side)

```python
# Example webhook receiver in Python (Flask)
import hmac
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

WEBHOOK_SECRET = "your-webhook-secret"

@app.route('/webhook/sla-breach', methods=['POST'])
def handle_sla_breach():
    # Get signature from header
    signature = request.headers.get('X-Webhook-Signature')
    if not signature:
        return jsonify({"error": "Missing signature"}), 401

    # Calculate expected signature
    payload = request.get_data()
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Verify signature
    if not hmac.compare_digest(signature, expected_signature):
        return jsonify({"error": "Invalid signature"}), 401

    # Process webhook
    data = request.get_json()
    print(f"Breach detected: {data['breach']['severity']}")
    print(f"SLA: {data['sla']['slaName']}")

    # Trigger automation (e.g., create Jira ticket, send Slack message)
    # ...

    return jsonify({"status": "received"}), 200
```

### Prednosti ✅

1. **Quick implementation**: 2-3 sata rada
2. **Simple**: Samo POST request sa JSON
3. **Secure**: HMAC signature verification
4. **Standard**: Industry-standard webhook pattern
5. **No additional infrastructure**: Koristi existing HTTP client

### Mane ⚠️

1. **Single webhook per SLA**: Samo jedan webhook URL
2. **No retry**: Ako faila, gubi se (može se dodati)
3. **No webhook management UI**: Mora da se konfiguriše kroz database ili API
4. **Fixed payload**: Ne može da se customizuje payload template

### Kada koristiti

- **Quick win**: Brza implementacija webhook support-a
- **Simple use case**: Jedan webhook URL po SLA
- **Standard integrations**: Slack, PagerDuty, generic webhooks

---

## 🔧 Pristup 2: Advanced Webhook System (Production ✅)

### Opis

Kompletan webhook management sistem sa multiple webhooks, templates, i retry logic.

### Implementacija

**1. Webhook Configuration Entity:**

```java
@Entity
@Table(name = "webhook_config", indexes = {
    @Index(name = "idx_webhook_sla", columnList = "sla_definition_id"),
    @Index(name = "idx_webhook_active", columnList = "is_active")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WebhookConfig {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @UuidGenerator
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "id", updatable = false, nullable = false, columnDefinition = "char(36)")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sla_definition_id", nullable = false)
    private SlaDefinition slaDefinition;

    @Column(name = "name", nullable = false, length = 255)
    private String name; // "Slack Critical Alerts", "PagerDuty Integration"

    @Column(name = "webhook_url", nullable = false, length = 2000)
    private String webhookUrl;

    @Column(name = "webhook_secret", length = 255)
    private String webhookSecret;

    @Column(name = "event_types", length = 500)
    private String eventTypes; // Comma-separated: "breach.detected,breach.resolved"

    @Column(name = "severity_filter", length = 100)
    private String severityFilter; // Comma-separated: "CRITICAL,HIGH"

    @Column(name = "payload_template", columnDefinition = "TEXT")
    private String payloadTemplate; // Custom JSON template (FreeMarker/Velocity)

    @Column(name = "http_method", length = 10)
    private String httpMethod = "POST"; // POST, PUT

    @Column(name = "custom_headers", columnDefinition = "TEXT")
    private String customHeaders; // JSON: {"Authorization": "Bearer token"}

    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;

    @Column(name = "timeout_ms", nullable = false)
    private Integer timeoutMs = 5000;

    @Column(name = "retry_enabled", nullable = false)
    private Boolean retryEnabled = true;

    @Column(name = "max_retries")
    private Integer maxRetries = 3;

    @Column(name = "created_by", nullable = false, length = 255)
    private String createdBy;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    // Statistics
    @Column(name = "last_sent_at")
    private LocalDateTime lastSentAt;

    @Column(name = "success_count")
    private Integer successCount = 0;

    @Column(name = "failure_count")
    private Integer failureCount = 0;

    // Business logic
    public boolean shouldTriggerFor(String eventType, String severity) {
        if (!isActive) {
            return false;
        }

        // Check event type filter
        if (eventTypes != null && !eventTypes.isEmpty()) {
            List<String> allowedEvents = Arrays.asList(eventTypes.split(","));
            if (!allowedEvents.contains(eventType)) {
                return false;
            }
        }

        // Check severity filter
        if (severityFilter != null && !severityFilter.isEmpty()) {
            List<String> allowedSeverities = Arrays.asList(severityFilter.split(","));
            if (!allowedSeverities.contains(severity)) {
                return false;
            }
        }

        return true;
    }

    public void recordSuccess() {
        this.successCount++;
        this.lastSentAt = LocalDateTime.now();
    }

    public void recordFailure() {
        this.failureCount++;
    }
}
```

**2. Webhook Delivery Log:**

```java
@Entity
@Table(name = "webhook_delivery_log", indexes = {
    @Index(name = "idx_delivery_webhook", columnList = "webhook_config_id"),
    @Index(name = "idx_delivery_status", columnList = "status"),
    @Index(name = "idx_delivery_created", columnList = "created_at")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WebhookDeliveryLog {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @UuidGenerator
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "id", updatable = false, nullable = false, columnDefinition = "char(36)")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "webhook_config_id", nullable = false)
    private WebhookConfig webhookConfig;

    @Column(name = "breach_id")
    @JdbcTypeCode(SqlTypes.CHAR)
    private UUID breachId;

    @Column(name = "event_type", nullable = false, length = 100)
    private String eventType;

    @Column(name = "payload", columnDefinition = "TEXT")
    private String payload;

    @Column(name = "status", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private WebhookDeliveryStatus status;

    @Column(name = "http_status_code")
    private Integer httpStatusCode;

    @Column(name = "response_body", columnDefinition = "TEXT")
    private String responseBody;

    @Column(name = "error_message", length = 2000)
    private String errorMessage;

    @Column(name = "retry_count")
    private Integer retryCount = 0;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "delivered_at")
    private LocalDateTime deliveredAt;
}

public enum WebhookDeliveryStatus {
    PENDING,
    DELIVERED,
    FAILED,
    RETRYING
}
```

**3. Enhanced Webhook Service:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class WebhookManagementService {

    private final WebhookConfigRepository webhookConfigRepository;
    private final WebhookDeliveryLogRepository deliveryLogRepository;
    private final WebhookService webhookService;

    /**
     * Send webhooks for breach event.
     * Finds all matching webhook configs and sends to each.
     */
    @Async
    @Transactional
    public void sendWebhooksForBreach(SlaBreach breach, String eventType) {
        SlaDefinition slaDefinition = breach.getSlaResult().getSlaDefinition();

        // Find all active webhooks for this SLA
        List<WebhookConfig> webhooks = webhookConfigRepository
                .findBySlaDefinitionIdAndIsActiveTrue(slaDefinition.getId());

        if (webhooks.isEmpty()) {
            log.debug("No active webhooks configured for SLA: {}", slaDefinition.getName());
            return;
        }

        String severity = breach.getSeverity();

        for (WebhookConfig webhook : webhooks) {
            // Check if webhook should trigger for this event/severity
            if (!webhook.shouldTriggerFor(eventType, severity)) {
                log.debug("Webhook {} filtered out by event/severity", webhook.getName());
                continue;
            }

            // Send webhook
            sendWebhook(webhook, breach, eventType);
        }
    }

    /**
     * Send individual webhook with retry and logging.
     */
    private void sendWebhook(WebhookConfig webhook, SlaBreach breach, String eventType) {
        log.info("Sending webhook {} for breach {}", webhook.getName(), breach.getId());

        // Build payload
        SlaBreachWebhookPayload payload = buildWebhookPayload(breach, eventType);
        String jsonPayload;

        try {
            // Apply custom template if configured
            if (webhook.getPayloadTemplate() != null) {
                jsonPayload = applyTemplate(webhook.getPayloadTemplate(), payload);
            } else {
                jsonPayload = objectMapper.writeValueAsString(payload);
            }
        } catch (Exception e) {
            log.error("Failed to build webhook payload for {}: {}", webhook.getName(), e.getMessage());
            return;
        }

        // Create delivery log
        WebhookDeliveryLog deliveryLog = WebhookDeliveryLog.builder()
                .webhookConfig(webhook)
                .breachId(breach.getId())
                .eventType(eventType)
                .payload(jsonPayload)
                .status(WebhookDeliveryStatus.PENDING)
                .createdAt(LocalDateTime.now())
                .build();

        deliveryLog = deliveryLogRepository.save(deliveryLog);

        // Send with retry
        boolean success = sendWithRetry(webhook, jsonPayload, deliveryLog);

        if (success) {
            webhook.recordSuccess();
            deliveryLog.setStatus(WebhookDeliveryStatus.DELIVERED);
            deliveryLog.setDeliveredAt(LocalDateTime.now());
        } else {
            webhook.recordFailure();
            deliveryLog.setStatus(WebhookDeliveryStatus.FAILED);
        }

        webhookConfigRepository.save(webhook);
        deliveryLogRepository.save(deliveryLog);
    }

    /**
     * Send webhook with retry logic.
     */
    private boolean sendWithRetry(WebhookConfig webhook, String payload, WebhookDeliveryLog log) {
        int maxRetries = webhook.getRetryEnabled() ? webhook.getMaxRetries() : 1;

        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                log.setRetryCount(attempt - 1);

                if (attempt > 1) {
                    log.setStatus(WebhookDeliveryStatus.RETRYING);
                    deliveryLogRepository.save(log);

                    // Exponential backoff: 2s, 4s, 8s
                    long backoffMs = (long) (2000 * Math.pow(2, attempt - 2));
                    Thread.sleep(backoffMs);

                    log.info("Retry attempt {} for webhook {}", attempt, webhook.getName());
                }

                // Send webhook
                boolean success = webhookService.sendWebhook(
                        webhook.getWebhookUrl(),
                        payload,
                        webhook.getWebhookSecret()
                );

                if (success) {
                    log.info("✅ Webhook {} delivered successfully (attempt {})",
                            webhook.getName(), attempt);
                    return true;
                }

            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            } catch (Exception e) {
                log.error("❌ Webhook {} failed (attempt {}): {}",
                        webhook.getName(), attempt, e.getMessage());
                log.setErrorMessage(e.getMessage());
            }
        }

        log.error("❌ Webhook {} failed after {} attempts", webhook.getName(), maxRetries);
        return false;
    }

    /**
     * Apply custom payload template (simple string replacement for now).
     * Future: Use FreeMarker or Velocity for complex templates.
     */
    private String applyTemplate(String template, SlaBreachWebhookPayload payload) {
        // Simple placeholder replacement
        String result = template;
        result = result.replace("${breach.id}", payload.getBreach().getBreachId().toString());
        result = result.replace("${breach.severity}", payload.getBreach().getSeverity());
        result = result.replace("${sla.name}", payload.getSla().getSlaName());
        // ... more placeholders ...
        return result;
    }
}
```

**4. Webhook Management API:**

```java
@RestController
@RequestMapping("/api/sla/webhooks")
@RequiredArgsConstructor
@Slf4j
public class WebhookManagementController {

    private final WebhookManagementService webhookService;

    /**
     * Create webhook configuration.
     * POST /api/sla/webhooks
     */
    @PostMapping
    public ResponseEntity<WebhookConfigDto> createWebhook(
            @RequestBody @Valid CreateWebhookRequest request) {

        WebhookConfig webhook = webhookService.createWebhook(request);
        WebhookConfigDto dto = webhookMapper.toDto(webhook);

        return ResponseEntity.status(HttpStatus.CREATED).body(dto);
    }

    /**
     * List webhooks for SLA definition.
     * GET /api/sla/webhooks?slaDefinitionId=...
     */
    @GetMapping
    public ResponseEntity<List<WebhookConfigDto>> listWebhooks(
            @RequestParam UUID slaDefinitionId) {

        List<WebhookConfig> webhooks = webhookService.listWebhooks(slaDefinitionId);

        List<WebhookConfigDto> dtos = webhooks.stream()
                .map(webhookMapper::toDto)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * Test webhook (send test payload).
     * POST /api/sla/webhooks/{webhookId}/test
     */
    @PostMapping("/{webhookId}/test")
    public ResponseEntity<WebhookTestResult> testWebhook(@PathVariable UUID webhookId) {
        WebhookTestResult result = webhookService.testWebhook(webhookId);
        return ResponseEntity.ok(result);
    }

    /**
     * Get webhook delivery logs.
     * GET /api/sla/webhooks/{webhookId}/deliveries
     */
    @GetMapping("/{webhookId}/deliveries")
    public ResponseEntity<List<WebhookDeliveryLogDto>> getDeliveryLogs(
            @PathVariable UUID webhookId,
            @RequestParam(defaultValue = "50") int limit) {

        List<WebhookDeliveryLog> logs = webhookService.getDeliveryLogs(webhookId, limit);

        List<WebhookDeliveryLogDto> dtos = logs.stream()
                .map(deliveryMapper::toDto)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * Delete webhook.
     * DELETE /api/sla/webhooks/{webhookId}
     */
    @DeleteMapping("/{webhookId}")
    public ResponseEntity<Void> deleteWebhook(@PathVariable UUID webhookId) {
        webhookService.deleteWebhook(webhookId);
        return ResponseEntity.noContent().build();
    }
}
```

### Prednosti ✅

1. **Multiple webhooks per SLA**: Neograničen broj webhooks
2. **Event filtering**: Različiti webhooks za različite events/severities
3. **Custom templates**: Customizable payload templates
4. **Retry logic**: Automatic retry sa exponential backoff
5. **Delivery tracking**: Kompletan log svih webhook deliveries
6. **Statistics**: Success/failure metrics po webhook-u
7. **Test endpoint**: Može da se testuje webhook pre aktivacije

### Mane ⚠️

1. **High complexity**: Dosta dodatnog code-a i tabela
2. **Resource usage**: Više database writes za logging
3. **Maintenance**: Više moving parts

### Kada koristiti

- **Production system**: Enterprise-grade webhook support
- **Multiple integrations**: Više različitih webhook consumers
- **Complex filtering**: Potrebna selective notification routing
- **Audit requirements**: Potreban kompletan delivery log

---

## 📊 Poređenje Pristupa

| Feature | Pristup 1 (Simple) | Pristup 2 (Advanced) |
|---------|-------------------|----------------------|
| **Implementation Time** | 2-3h | 12-16h |
| **Complexity** | ⭐ Low | ⭐⭐⭐ High |
| **Multiple Webhooks** | ❌ No (1 per SLA) | ✅ Yes (unlimited) |
| **Event Filtering** | ❌ No | ✅ Yes |
| **Severity Filtering** | ❌ No | ✅ Yes |
| **Custom Templates** | ❌ No | ✅ Yes |
| **Retry Logic** | ❌ No | ✅ Yes |
| **Delivery Logging** | ⭐ Basic | ⭐⭐⭐ Complete |
| **Test Endpoint** | ❌ No | ✅ Yes |
| **Management UI** | ❌ No | ✅ Full CRUD API |
| **Statistics** | ❌ No | ✅ Yes |

---

## 🎯 Finalna Preporuka

### Phased Approach: **Start Simple, Grow to Advanced** ✅

**Faza 1 (Week 1)**: Simple Webhook (Pristup 1)
- [ ] Dodati `webhook_url` i `webhook_secret` fields u `SlaDefinition`
- [ ] Implementirati `WebhookService` sa basic send logic
- [ ] Dodati HMAC signature generation
- [ ] Update `SlaNotificationService` da šalje webhooks
- [ ] Testing sa test webhook receiver

**Faza 2 (Week 2-3)**: Advanced Features (Pristup 2)
- [ ] Kreirati `WebhookConfig` entity (multiple webhooks)
- [ ] Kreirati `WebhookDeliveryLog` entity
- [ ] Implementirati `WebhookManagementService`
- [ ] Dodati retry logic sa exponential backoff
- [ ] Event/severity filtering
- [ ] Webhook management API

**Faza 3 (Week 4)**: Nice-to-Have
- [ ] Custom payload templates (FreeMarker)
- [ ] Test webhook endpoint
- [ ] Webhook statistics dashboard
- [ ] Retry failed webhooks UI

---

## 🧪 Testing Strategy

### Unit Tests

```java
@Test
void testHmacSignatureGeneration() {
    String payload = "{\"test\":\"data\"}";
    String secret = "my-secret";

    String signature = webhookService.generateHmacSignature(payload, secret);

    assertThat(signature).isNotEmpty();
    assertThat(signature).hasSize(64); // SHA-256 hex = 64 chars
}

@Test
void testWebhookFiltering() {
    WebhookConfig webhook = WebhookConfig.builder()
        .eventTypes("breach.detected")
        .severityFilter("CRITICAL,HIGH")
        .build();

    assertThat(webhook.shouldTriggerFor("breach.detected", "CRITICAL")).isTrue();
    assertThat(webhook.shouldTriggerFor("breach.detected", "LOW")).isFalse();
    assertThat(webhook.shouldTriggerFor("breach.resolved", "CRITICAL")).isFalse();
}
```

### Integration Tests

```java
@SpringBootTest
@Transactional
class WebhookIntegrationTest {

    @Test
    void testWebhookDeliveryWithRetry() {
        // Mock webhook endpoint that fails first 2 times, succeeds on 3rd
        mockServer.when(request().withPath("/webhook"))
            .respond(response().withStatusCode(500)); // First attempt

        mockServer.when(request().withPath("/webhook"))
            .respond(response().withStatusCode(500)); // Second attempt

        mockServer.when(request().withPath("/webhook"))
            .respond(response().withStatusCode(200)); // Third attempt success

        // Send webhook
        webhookService.sendWebhooksForBreach(breach, "breach.detected");

        // Verify delivery log
        List<WebhookDeliveryLog> logs = deliveryLogRepository.findByBreachId(breach.getId());
        assertThat(logs).hasSize(1);
        assertThat(logs.get(0).getStatus()).isEqualTo(WebhookDeliveryStatus.DELIVERED);
        assertThat(logs.get(0).getRetryCount()).isEqualTo(2);
    }
}
```

---

## 📚 Integration Examples

### Slack Integration

```bash
# Create Slack webhook
POST /api/sla/webhooks
{
  "slaDefinitionId": "abc-123",
  "name": "Slack Critical Alerts",
  "webhookUrl": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX",
  "eventTypes": "breach.detected",
  "severityFilter": "CRITICAL,HIGH",
  "payloadTemplate": "{\"text\":\"🚨 SLA Breach: ${sla.name}\",\"attachments\":[{\"color\":\"danger\",\"fields\":[{\"title\":\"Severity\",\"value\":\"${breach.severity}\"},{\"title\":\"Compliance\",\"value\":\"${breach.actualValue}%\"}]}]}"
}
```

### PagerDuty Integration

```bash
POST /api/sla/webhooks
{
  "slaDefinitionId": "abc-123",
  "name": "PagerDuty Incidents",
  "webhookUrl": "https://events.pagerduty.com/v2/enqueue",
  "eventTypes": "breach.detected",
  "severityFilter": "CRITICAL",
  "customHeaders": "{\"Authorization\":\"Token token=YOUR_INTEGRATION_KEY\"}",
  "payloadTemplate": "{\"routing_key\":\"YOUR_INTEGRATION_KEY\",\"event_action\":\"trigger\",\"payload\":{\"summary\":\"SLA Breach: ${sla.name}\",\"severity\":\"critical\",\"source\":\"OCI SLA Monitor\"}}"
}
```

---

## 📚 References

- [Webhook Security Best Practices](https://webhooks.fyi/)
- [HMAC Authentication](https://www.oauth.com/oauth2-servers/signing-and-verifying-requests/hmac/)
- [Slack Webhook Guide](https://api.slack.com/messaging/webhooks)
- [PagerDuty Events API](https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview)
