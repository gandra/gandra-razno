# Refaktor oci-backend: Integracija sc-notifications

> **Datum:** 2026-03-10
> **Status:** PLAN / TODO
> **Autor:** Dragan Mijatović

---

## Sadržaj

1. [Trenutno stanje](#1-trenutno-stanje)
2. [Ciljevi refaktora](#2-ciljevi-refaktora)
3. [Ključno pravilo: Non-destructive deployment](#3-ključno-pravilo-non-destructive-deployment)
4. [Infrastrukturni preduslovi](#4-infrastrukturni-preduslovi)
5. [Pristupi integraciji (sumarno)](#5-pristupi-integraciji-sumarno)
6. [Preporučeni pristup: Dual-mode Facade + Plain HTTP](#6-preporučeni-pristup-dual-mode-facade--plain-http)
7. [Odnos sa sc-notifications-client](#7-odnos-sa-sc-notifications-client)
8. [Detaljan dizajn](#8-detaljan-dizajn)
9. [Strategija baze podataka](#9-strategija-baze-podataka)
10. [Docker konfiguracija](#10-docker-konfiguracija)
11. [Lokalno i Dev/Cloud okruženje](#11-lokalno-i-devcloud-okruženje)
12. [Plan implementacije](#12-plan-implementacije)
13. [Obrazloženje preporuke](#13-obrazloženje-preporuke)
14. [Post-implementacija](#14-post-implementacija)

---

## 1. Trenutno stanje

### 1.1 Duplirani email kod

`MailerService` interfejs je identičan u oba modula:

```java
public interface MailerService {
   EmailSendResponseDto sendTextEmail(@Valid SendEmailRequestDto request);
   EmailSendResponseDto sendHtmlEmail(@Valid SendEmailRequestDto request);
}
```

| Klasa | oci-api | oci-monitor | Aktivacija |
|-------|---------|-------------|------------|
| `SmtpMailerService` | ✅ | ✅ | `email.provider=smtp` (default, `matchIfMissing=true`) |
| `SendGridMailerService` | ✅ | ✅ | `email.provider=sendgrid` (`matchIfMissing=false`) |
| `EmailConfig` | ✅ | ✅ | `JavaMailSender` bean konfiguracija |

### 1.2 Korisnici email servisa

**oci-api (3 poziva):** `UserRegistrationService` (registracija, resend token), `UsersService` (reset lozinke)

**oci-monitor (6 poziva):** `BudgetNotificationService`, `BudgetCompartmentService`, `SubscriptionNotificationService`, `CommitmentNotificationService`, `CostReportsService`, `MetricsNotificationEventListener`

### 1.3 Dijagram zavisnosti — trenutno stanje

```
┌─ oci-backend (Java 17, Spring Boot 3.2.1) ──────────────────────────────┐
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                     oci-library (plain JAR)                      │    │
│  │                                                                  │    │
│  │  entity/  dto/  enums/  utils/  exception/                      │    │
│  │  (čiste Java klase — nema @Service, @Component, @Configuration) │    │
│  │  Zavisnosti: opencsv, spring-boot-starter-test (test scope)     │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│        ▲ Maven dependency               ▲ Maven dependency              │
│        │                                 │                               │
│  ┌─────┴──────────────┐          ┌───────┴──────────────────┐           │
│  │     oci-api         │          │     oci-monitor           │           │
│  │     port: 8080      │          │     port: 8081            │           │
│  │                     │          │                           │           │
│  │  MailerService ────────────────── MailerService            │           │
│  │   ├─SmtpMailerSvc   │          │   ├─SmtpMailerSvc         │           │
│  │   └─SendGridSvc     │          │   └─SendGridSvc           │           │
│  │                     │          │                           │           │
│  │  Pozivi: 3          │          │  Pozivi: 6                │           │
│  └─────────┬───────────┘          └───────────┬──────────────┘           │
│            │                                  │                          │
│            └──────────┬───────────────────────┘                          │
│                       ▼                                                  │
│            ┌─────────────────────┐                                       │
│            │  SMTP / SendGrid    │  (direktan poziv, nema failover)      │
│            └─────────────────────┘                                       │
│                                                                          │
│  ┌──────┐                                                                │
│  │MySQL │  oci-backend baza                                              │
│  │ 3306 │                                                                │
│  └──────┘                                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ciljevi refaktora

1. **Uvesti sc-notifications kao novi kanal** — dodati mogućnost slanja notifikacija putem sc-notifications REST API-ja, uz zadržavanje postojećeg email sistema
2. **Kontrola putem konfiguracije** — koji email sistem se koristi određuje se isključivo konfiguracijom, **bez promene koda** između okruženja
3. **Podrazumevano ponašanje = legacy** — ako se ne promeni nijedna konfiguracija, sistem radi identično kao do sada
4. **Jedan codebase, više produkcija** — isti build artifact (JAR) na sva okruženja
5. **Failover/retry/DLQ** — na okruženjima sa sc-notifications, automatski
6. **Proširivost** — SMS, webhook, websocket dostupni na SC okruženjima bez izmena koda

> **Ključno:** Stari email kod **ostaje u codebase-u**. Aplikacija je na više produkcija. Samo na nekim okruženjima aktiviramo sc-notifications. Patching/bugfix na starom email toku mora biti moguć na istom codebase-u.

---

## 3. Ključno pravilo: Non-destructive deployment

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  ISTI JAR ARTIFACT  ──deploy──►  Okruženje X (klijent A)      │
│                     ──deploy──►  Okruženje Y (klijent B)      │
│                     ──deploy──►  Okruženje Z (dev/test)       │
│                                                                │
│  X:  email.notification.mode ne postoji  → default "legacy"   │
│  Y:  email.notification.mode = legacy    → SMTP/SendGrid     │
│  Z:  email.notification.mode = sc-notifications → REST API   │
│                                                                │
│  X i Y rade identično kao pre refaktora.                      │
│  Z koristi sc-notifications.                                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

| Scenario | Ponašanje |
|----------|-----------|
| Deploy bez promene env vars | ✅ Identično kao pre — SMTP/SendGrid |
| `email.notification.mode=sc-notifications` | ✅ Koristi sc-notifications REST API |
| SC mod, ali servis nedostupan | ⚠️ Loguje error, ne pada aplikacija |
| Rollback | ✅ Promena jednog property-ja |

---

## 4. Infrastrukturni preduslovi

sc-notifications **nema Dockerfile** — kreirati ga. Potrebni servisi (samo za SC okruženja):

| Servis | Image | Portovi (local) |
|--------|-------|-----------------|
| sc-notifications | custom build (Java 25) | 8091:8081 |
| PostgreSQL 17.6 | postgres:17.6-alpine | 5432:5432 |
| RabbitMQ 4.1.4 | rabbitmq:4.1.4-management-alpine | 5672, 15672 |
| Mailpit | ghcr.io/axllent/mailpit:latest | 13081:1025, 14081:8025 |

> Legacy okruženja ne trebaju ništa od navedenog.

---

## 5. Pristupi integraciji (sumarno)

| Pristup | Status | Razlog |
|---------|--------|--------|
| **A: SDK čist prelaz** — uklanja stari kod, svi koriste SC | ❌ | Krši non-destructive princip. Dugoročni cilj. |
| **B: Embedded** — sc-notifications kao in-process biblioteka | ❌ | Blokirano: Java 25 vs Java 17 nekompatibilnost. |
| **C: Dual-mode Facade + Plain HTTP** | ⭐ | Oba sistema žive u codebase-u. Konfig bira. Default = legacy. |

---

## 6. Preporučeni pristup: Dual-mode Facade + Plain HTTP

### 6.1 Zašto ne koristimo sc-notifications-client kao Maven zavisnost?

**Tri blokera onemogućavaju direktno dodavanje `sc-notifications-client` u `oci-library/pom.xml`:**

| # | Problem | Detalj |
|---|---------|--------|
| 1 | **Java bytecode** | sc-notifications-client kompajliran za Java 25 (major version: 69). oci-backend JVM = Java 17 (max: 61). → `UnsupportedClassVersionError` |
| 2 | **Spring Boot verzija** | sc-notifications-client → sistemi-starter-parent → Spring Boot **3.5.11**. oci-backend → Spring Boot **3.2.1**. Auto-konfiguracija pisana za 3.5 možda koristi API-je koji ne postoje u 3.2. |
| 3 | **Tranzitivne zavisnosti** | sc-notifications-client → sc-commons donosi Hibernate 6.6.x, QueryDSL 5.1, MapStruct 1.6, Flyway 11.3 — sve u konfliktu sa oci-backend verzijama. |

### 6.2 Šta radimo umesto toga?

Pišemo **lak REST klijent** (`ScNotificationsClient`) direktno u `oci-library` koristeći Spring-ov `RestClient` koji je već na classpath-u. **Nula novih zavisnosti.** Pratimo isti REST API kontract koji koristi sc-notifications-client, ali sa našim kodom kompajliranim za Java 17.

---

## 7. Odnos sa sc-notifications-client

### 7.1 Šta postoji u sc-notifications-client

sc-notifications-client (`com.sistemisolutions.core.notifications.client`) sadrži 16 Java fajlova:

```
sc-notifications-client/src/main/java/.../client/
├── NotificationApiClient.java              ← REST klijent (RestClient)
├── config/
│   ├── NotificationApiAutoConfiguration    ← @ConditionalOnProperty("base-url")
│   ├── NotificationAckAutoConfiguration    ← @ConditionalOnProperty("ack.enabled")
│   └── properties/
│       └── NotificationClientProperties    ← @ConfigurationProperties("notification.client")
├── enums/
│   ├── DeliveryStatusType                  ← SUCCESS, TEMP_FAILURE, PERM_FAILURE, UNKNOWN
│   ├── NotificationChannelType             ← EMAIL, SMS, PUSH, SLACK, WEBHOOK, WEBSOCKET
│   └── NotificationResponseStatus          ← ACCEPTED, REJECTED, QUEUED
├── handler/
│   └── NotificationDeliveryReceiptHandler  ← @FunctionalInterface (ACK callback)
├── listener/
│   └── NotificationAckListener             ← @RabbitListener za ACK poruke
├── model/
│   ├── ack/
│   │   └── NotificationDeliveryReceipt     ← ACK DTO (uuid, status, provider, timestamp)
│   ├── request/
│   │   ├── SendEmailRequest                ← to, subject, body, html, from, cc, bcc, providerKeys, meta
│   │   ├── SendWebhookRequest              ← url, httpMethod, body, headers, retryAttempts
│   │   └── SendMattermostWebhookRequest    ← text, username, iconUrl, webhookUrl
│   └── response/
│       └── NotificationResponse            ← notificationUuid, correlationId, status, channel
└── info/
    ├── NotificationsClientInfo             ← Git info bean
    └── NotificationsClientGitProperties    ← Git properties
```

**Funkcionalnosti:**

| Grupa | Klase | Opis |
|-------|-------|------|
| **REST klijent** | `NotificationApiClient` | POST ka `/api/v1/notifications/email`, `/webhook`, `/webhook/mattermost` |
| **Auto-konfiguracija** | `NotificationApiAutoConfiguration` | Kreira `RestClient` + `NotificationApiClient` bean kad postoji `base-url` |
| **ACK listener** | `NotificationAckAutoConfiguration`, `NotificationAckListener` | RabbitMQ consumer za delivery receipts (fanout exchange) |
| **DTO-ovi** | `SendEmailRequest`, `NotificationResponse`, `NotificationDeliveryReceipt` | Request/response/ACK modeli |
| **Enumi** | 3 enum klase | Status tipovi |
| **Info** | 2 klase | Git commit info (irelevantno za nas) |

### 7.2 Šta MI radimo (Strategija D-A: Plain HTTP)

**NE koristimo** sc-notifications-client JAR kao Maven zavisnost.

**REPLICIAMO** samo ono što nam treba — REST poziv i DTO-ove — kao naš Java 17 kod u `oci-library`:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  sc-notifications-client (Java 25)          oci-library (Java 17)           │
│  ════════════════════════════                ═══════════════════════          │
│                                                                              │
│  NotificationApiClient ──── replicirano ──→ ScNotificationsClient           │
│   └─ sendEmail()                             └─ sendEmail()                  │
│   └─ sendWebhook()                           (webhook/mattermost later)     │
│   └─ sendMattermostWebhook()                                                │
│                                                                              │
│  SendEmailRequest ─────── replicirano ──→ ScSendEmailRequest                │
│   └─ to, subject, body,                   └─ to, subject, body,             │
│      html, fromEmail,                        html, fromEmail,               │
│      cc, bcc, providerKeys,                  cc, bcc, providerKeys,         │
│      deliveryMode, meta                      deliveryMode, meta             │
│                                                                              │
│  NotificationResponse ─── replicirano ──→ ScNotificationResponse            │
│   └─ notificationUuid,                    └─ notificationUuid,              │
│      correlationId,                          correlationId,                  │
│      status, channel                         status, channel                │
│                                                                              │
│  NotificationApiAutoConfig ─ NE treba ──→ @ConditionalOnProperty            │
│  NotificationClientProperties              na ScNotificationsClient          │
│   (Spring Boot 3.5 auto-config)            (jednostavan @Value inject)       │
│                                                                              │
│  NotificationAckAutoConfig ── LATER ──→ Opciono u budućnosti                │
│  NotificationAckListener                (kad bude potreban ACK)             │
│  NotificationDeliveryReceipt                                                │
│  NotificationDeliveryReceiptHandler                                         │
│                                                                              │
│  Enumi (3) ───────────────── NE treba ──→ Koristimo String za status       │
│  Info klase (2) ─────────── NE treba ──→ Irelevantno                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Dijagram zavisnosti i komunikacije — ciljno stanje

```
┌─ Build time (Maven) ──────────────────────────────────────────────────────────┐
│                                                                               │
│  sistemi-starter-parent (Java 25, SB 3.5.11)                                │
│       │                                                                       │
│       ├── sc-commons ──────────┐                                             │
│       │                        ▼                                              │
│       ├── sc-notifications-client ←── NE KORISTIMO u oci-backend             │
│       │                                                                       │
│       └── sc-notifications (servis, Java 25)                                 │
│               │                                                               │
│               └── Dockerfile → Docker image                                  │
│                                                                               │
│  spring-boot-starter-parent (Java 17, SB 3.2.1)                             │
│       │                                                                       │
│       └── oci-backend                                                        │
│            ├── oci-library ←── ScNotificationsClient (naš kod, Java 17)      │
│            ├── oci-api ────── zavisi od oci-library                           │
│            └── oci-monitor ── zavisi od oci-library                           │
│                                                                               │
│  NEMA Maven zavisnosti između oci-backend i sc-* projekata                   │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘


┌─ Runtime (komunikacija) ─────────────────────────────────────────────────────┐
│                                                                               │
│                                                                               │
│  ┌──────────────┐  ┌────────────────┐                                        │
│  │   oci-api    │  │  oci-monitor   │   Java 17, Spring Boot 3.2.1           │
│  │   :8080      │  │  :8081         │                                        │
│  │              │  │                │                                        │
│  │  Notif.      │  │  Notif.        │                                        │
│  │  Facade      │  │  Facade        │                                        │
│  └──────┬───────┘  └───────┬────────┘                                        │
│         │                  │                                                  │
│         │ email.notification.mode = ?                                        │
│         │                  │                                                  │
│    ┌────┴────┐       ┌────┴────┐                                             │
│    │ legacy  │       │ sc-notif│                                              │
│    │ (dflt)  │       │         │                                              │
│    ▼         │       ▼         │                                              │
│ ┌────────┐   │   ┌────────┐   │                                              │
│ │ SMTP / │   │   │ HTTP   │   │                                              │
│ │ SGrid  │   │   │ POST   │   │                                              │
│ │(direkt)│   │   │        │   │                                              │
│ └────────┘   │   └───┬────┘   │                                              │
│              │       │        │                                               │
│              │       │ REST   │                                               │
│              │       ▼        │                                               │
│              │  ┌──────────────────────────────────┐                         │
│              │  │     sc-notifications             │  Java 25, SB 3.5       │
│              │  │     :8091                        │                         │
│              │  │                                  │                         │
│              │  │  POST /api/v1/notifications/email │                         │
│              │  │                                  │                         │
│              │  │  Gateway → Dispatcher            │                         │
│              │  │  → EmailChannel                  │                         │
│              │  │    ├─ smtp_loopia  (failover 1)  │                         │
│              │  │    ├─ api_sendgrid (failover 2)  │                         │
│              │  │    └─ api_mailtrap (failover 3)  │                         │
│              │  │  → ACK Publisher                  │                         │
│              │  └──────────┬───────────────────────┘                         │
│              │             │                                                  │
│              │     ┌───────┼──────────────┐                                   │
│              │     ▼       ▼              ▼                                   │
│              │   ┌────┐ ┌──────────┐ ┌───────────┐                           │
│              │   │ PG │ │ RabbitMQ │ │  Mailpit  │                           │
│              │   │5432│ │5672/15672│ │13081/14081│                           │
│              │   └────┘ └──────────┘ └───────────┘                           │
│              │                                                                │
│  ┌──────┐    │                                                                │
│  │MySQL │    │  oci-backend baza (bez promena)                                │
│  │ 3306 │    │                                                                │
│  └──────┘    │                                                                │
│              │                                                                │
└──────────────┘────────────────────────────────────────────────────────────────┘
```

### 7.4 Komunikacioni protokol — šta naš klijent radi

Naš `ScNotificationsClient` radi **identičan HTTP poziv** kao `NotificationApiClient` iz sc-notifications-client:

```
ScNotificationsClient (naš kod, Java 17)
        │
        │  HTTP POST
        │  URL: http://sc-notifications:8091/api/v1/notifications/email
        │  Content-Type: application/json
        │  Body: {
        │    "to": ["user@example.com"],
        │    "subject": "Budget Alert",
        │    "body": "<h1>Prekoračenje</h1>...",
        │    "html": true,
        │    "fromEmail": "noreply@company.com",
        │    "meta": { "correlationId": "uuid-123" }
        │  }
        │
        ▼
sc-notifications server (Java 25)
        │
        │  Response HTTP 202 Accepted
        │  Body: {
        │    "notificationUuid": "...",
        │    "correlationId": "uuid-123",
        │    "status": "ACCEPTED",
        │    "channel": "EMAIL"
        │  }
        │
        ▼
NotificationApiController → NotificationApiService
→ NotificationGateway → Dispatcher → EmailChannel
→ Provider (smtp_loopia → failover → api_sendgrid → ...)
→ DeliveryReceiptPublisher → RabbitMQ (ACK)
```

> JSON format je isti. Endpoint je isti. Jedina razlika: mi pišemo `RestClient.post()` u Javi 17 umesto da koristimo sc-notifications-client `NotificationApiClient` klasu kompajliranu za Java 25.

### 7.5 Šta je odloženo za kasnije (ACK)

ACK (delivery receipts) zahteva RabbitMQ listener. sc-notifications-client ovo rešava putem `NotificationAckAutoConfiguration` + `NotificationAckListener`. Mi to za sada **preskačemo** — implementiraćemo kad bude potrebno, koristeći `spring-boot-starter-amqp` (koji je kompatibilan sa Spring Boot 3.2.1).

---

## 8. Detaljan dizajn

### 8.1 Nove klase u oci-library

```
oci-library/src/main/java/com/sistemisolutions/oci/lib/
└── notification/
    ├── NotificationFacade.java           ← Dual-mode facade
    ├── ScNotificationsClient.java        ← Plain HTTP klijent
    ├── dto/
    │   ├── ScSendEmailRequest.java       ← Request DTO
    │   └── ScNotificationResponse.java   ← Response DTO
    └── mapper/
        └── NotificationMapper.java       ← OCI DTO → SC DTO
```

### 8.2 ScNotificationsClient

```java
@Slf4j
@Component
@ConditionalOnProperty(name = "notification.sc.base-url")
public class ScNotificationsClient {

   private static final String EMAIL_PATH = "/api/v1/notifications/email";
   private final RestClient restClient;

   public ScNotificationsClient(
         @Value("${notification.sc.base-url}") String baseUrl) {
      this.restClient = RestClient.builder()
         .baseUrl(baseUrl)
         .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
         .build();
   }

   public ScNotificationResponse sendEmail(ScSendEmailRequest request) {
      return restClient.post()
         .uri(EMAIL_PATH)
         .body(request)
         .retrieve()
         .body(ScNotificationResponse.class);
   }
}
```

> Bean se kreira **samo** kad `notification.sc.base-url` postoji. Legacy okruženja: bean ne postoji, nema greške.

### 8.3 DTO-ovi

```java
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class ScSendEmailRequest {
   private List<String> to;
   private String subject;
   private String body;
   private boolean html;
   private String fromEmail;
   private String fromName;
   private List<String> cc;
   private List<String> bcc;
   private String replyToEmail;
   private String replyToName;
   private List<String> providerKeys;
   private String deliveryMode;
   private Map<String, Object> meta;
}

@Data @NoArgsConstructor @AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class ScNotificationResponse {
   private UUID notificationUuid;
   private String correlationId;
   private String status;   // ACCEPTED, REJECTED, QUEUED
   private String channel;  // EMAIL, WEBHOOK, ...
}
```

### 8.4 NotificationFacade

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationFacade {

   private final MailerService mailerService;
   private final Optional<ScNotificationsClient> scClient;

   @Value("${email.notification.mode:legacy}")
   private String notificationMode;

   public EmailSendResponseDto sendTextEmail(SendEmailRequestDto request) {
      if (isScNotificationsMode()) {
         return sendViaScNotifications(request, false);
      }
      return mailerService.sendTextEmail(request);
   }

   public EmailSendResponseDto sendHtmlEmail(SendEmailRequestDto request) {
      if (isScNotificationsMode()) {
         return sendViaScNotifications(request, true);
      }
      return mailerService.sendHtmlEmail(request);
   }

   private boolean isScNotificationsMode() {
      return "sc-notifications".equals(notificationMode);
   }

   private EmailSendResponseDto sendViaScNotifications(
         SendEmailRequestDto request, boolean html) {
      ScNotificationsClient client = scClient.orElseThrow(() ->
         new IllegalStateException(
            "email.notification.mode=sc-notifications ali " +
            "notification.sc.base-url nije konfigurisano"));

      ScSendEmailRequest scReq = NotificationMapper.toScRequest(request, html);
      ScNotificationResponse resp = client.sendEmail(scReq);

      log.info("SC-Notification | uuid={} | status={} | to={}",
         resp.getNotificationUuid(), resp.getStatus(), request.getTo());

      return EmailSendResponseDto.builder()
         .emailSentTo(request.getTo())
         .emailProvider("sc-notifications")
         .error("REJECTED".equals(resp.getStatus()))
         .build();
   }
}
```

### 8.5 Konfiguracija po profilima

**application.properties — BEZ PROMENA:**
```properties
email.provider=smtp
support.email=${NO_REPLY_EMAIL}
spring.sendgrid.api-key=${SENDGRID_API_KEY}
app.smtp.mail.host=${SMTP_HOST}
# ... ostalo bez promena
```

**application-local.properties — DODATI:**
```properties
email.notification.mode=sc-notifications
notification.sc.base-url=http://localhost:8091
```

**application-prod.properties — BEZ PROMENA:**
```properties
# email.notification.mode ne postoji → default "legacy"
```

### 8.6 Refaktor poziva u servisima

```java
// Pre:
private final MailerService mailerService;
mailerService.sendHtmlEmail(new SendEmailRequestDto(from, to, subject, body));

// Posle:
private final NotificationFacade notificationFacade;
notificationFacade.sendHtmlEmail(new SendEmailRequestDto(from, to, subject, body));
```

> Minimalna promena — zamena inject-a. Potpis metode isti. Stari `MailerService` se NE BRIŠE.

---

## 9. Strategija baze podataka

oci-backend ostaje na MySQL. sc-notifications dobija **zasebnu** PostgreSQL instancu.

```
┌─────────────┐     ┌──────────────────┐
│  MySQL 8.0  │     │ PostgreSQL 17.6  │
│  (ociapp)   │     │ (sc_notifications)│
│  oci-api    │     │  sc-notifications │
│  oci-monitor│     │                   │
└─────────────┘     └──────────────────┘
   bez promena       samo na SC okruženjima
```

---

## 10. Docker konfiguracija

### 10.1 docker-compose-local.yml — dodati SC stack

```yaml
services:
  # Postojeći (BEZ PROMENA)
  db:
    image: "mysql/mysql-server:latest"
    # ... identično kao sada

  # Novi: sc-notifications stack
  sc-notifications:
    build:
      context: ../sc-notifications
      dockerfile: Dockerfile
    container_name: sc-notifications
    ports:
      - "8091:8081"
    environment:
      - SPRING_PROFILES_ACTIVE=local
      - SPRING_DATASOURCE_URL=jdbc:postgresql://sc-notifications-db:5432/sc_notifications
      - SPRING_DATASOURCE_USERNAME=postgres
      - SPRING_DATASOURCE_PASSWORD=topsecret
      - SPRING_RABBITMQ_HOST=sc-notifications-rabbitmq
      - SPRING_RABBITMQ_PORT=5672
      - SPRING_RABBITMQ_USERNAME=notifier
      - SPRING_RABBITMQ_PASSWORD=topsecret
      - MAILPIT_SMTP_PORT=1025
    depends_on:
      sc-notifications-db: { condition: service_healthy }
      sc-notifications-rabbitmq: { condition: service_healthy }

  sc-notifications-db:
    image: "postgres:17.6-alpine"
    container_name: sc-notifications-db
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=topsecret
      - POSTGRES_DB=sc_notifications
    volumes:
      - sc_notifications_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d sc_notifications"]
      interval: 10s
      timeout: 5s
      retries: 5

  sc-notifications-rabbitmq:
    image: rabbitmq:4.1.4-management-alpine
    container_name: sc-notifications-rabbitmq
    hostname: sc-notifications-rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=notifier
      - RABBITMQ_DEFAULT_PASS=topsecret
    volumes:
      - sc_notifications_rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  sc-notifications-mailpit:
    image: ghcr.io/axllent/mailpit:latest
    container_name: sc-notifications-mailpit
    ports:
      - "13081:1025"
      - "14081:8025"
    environment:
      MP_MAX_MESSAGES: "5000"
      MP_SMTP_AUTH_ACCEPT_ANY: "true"
      MP_SMTP_AUTH_ALLOW_INSECURE: "true"

volumes:
  oci_db_volume:
    external: true
  sc_notifications_db_data:
    external: true
  sc_notifications_rabbitmq_data:
```

### 10.2 docker-compose-cloud-dev.yml (samo SC okruženja)

Dodati `sc-notifications`, `sc-notifications-db`, `sc-notifications-rabbitmq`. Dodatni env vars za `api` i `monitor`:

```yaml
- "EMAIL_NOTIFICATION_MODE=sc-notifications"
- "NOTIFICATION_SC_BASE_URL=http://sc-notifications:8081"
```

> Produkcije klijenata: compose fajl **ne sadrži** SC servise, niti nove env vars. Identično kao pre.

---

## 11. Lokalno i Dev/Cloud okruženje

### Lokalno — IntelliJ (⭐ Preporuka)

```
┌─ IntelliJ IDEA ────────────────────────────────────┐
│  Run: oci-api (8080)  oci-monitor (8081)           │
│  Run: sc-notifications (8091)                      │
└─────────────────────────────────────────────────────┘
         │              │              │
┌─ Docker ───────────────────────────────────────────┐
│  MySQL(3306) PostgreSQL(5432) RabbitMQ(5672)       │
│  Mailpit(13081 SMTP / 14081 UI)                    │
└────────────────────────────────────────────────────┘
```

### Dev/Cloud — SC okruženje

```
┌─ Docker Host ──────────────────────────────────────────────┐
│  nginx │ ui │ api │ monitor │ db(MySQL)   ← postojeće     │
│                │       │                                    │
│                └───┬───┘ mode=sc-notifications              │
│                    ▼                                        │
│          sc-notifications(:8091)          ← novo           │
│             │       │                                       │
│       PostgreSQL  RabbitMQ                ← novo           │
└─────────────────────────────────────────────────────────────┘
```

### Dev/Cloud — Legacy okruženje (produkcije klijenata)

```
┌─ Docker Host ──────────────────────────────────────────────┐
│  nginx │ ui │ api │ monitor │ db(MySQL)                    │
│                │       │                                    │
│                └───┬───┘ mode=legacy (default)             │
│                    ▼                                        │
│              SMTP / SendGrid (direktno)                    │
│                                                             │
│  NEMA SC-NOTIFICATIONS, NEMA PG, NEMA RABBITMQ            │
│  IDENTIČNO KAO PRE REFAKTORA                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Plan implementacije

### Faza 1: Infrastruktura (1-2 dana)

| # | Task | Lokacija |
|---|------|----------|
| 1 | Kreirati Dockerfile za sc-notifications | `sc-notifications/Dockerfile` |
| 2 | Dodati SC stack u `docker-compose-local.yml` | `oci-backend/docker-compose-local.yml` |

### Faza 2: Kod u oci-library (2-3 dana)

| # | Task | Lokacija |
|---|------|----------|
| 3 | `ScSendEmailRequest` DTO | `oci-library/.../notification/dto/` |
| 4 | `ScNotificationResponse` DTO | `oci-library/.../notification/dto/` |
| 5 | `ScNotificationsClient` (plain HTTP) | `oci-library/.../notification/` |
| 6 | `NotificationMapper` | `oci-library/.../notification/mapper/` |
| 7 | `NotificationFacade` (dual-mode) | `oci-library/.../notification/` |

### Faza 3: Refaktor servisa (1-2 dana)

| # | Task | Modul |
|---|------|-------|
| 8 | `UserRegistrationService` → `NotificationFacade` | oci-api |
| 9 | `UsersService` → `NotificationFacade` | oci-api |
| 10 | `BudgetNotificationService` → `NotificationFacade` | oci-monitor |
| 11 | `BudgetCompartmentService` → `NotificationFacade` | oci-monitor |
| 12 | `SubscriptionNotificationService` → `NotificationFacade` | oci-monitor |
| 13 | `CommitmentNotificationService` → `NotificationFacade` | oci-monitor |
| 14 | `CostReportsService` → `NotificationFacade` | oci-monitor |
| 15 | `MetricsNotificationEventListener` → `NotificationFacade` | oci-monitor |

### Faza 4: Konfiguracija + Test (1-2 dana)

| # | Task |
|---|------|
| 16 | Dodati `email.notification.mode` + `notification.sc.base-url` u `application-local.properties` |
| 17 | Testirati SC mod — Mailpit UI http://localhost:14081 |
| 18 | Testirati legacy mod — zakomentarisati `email.notification.mode` |
| 19 | `mvn test` — verifikovati stare testove |

### Faza 5: Deploy (1 dan)

| # | Task |
|---|------|
| 20 | Deploy na dev sa SC konfiguracijom |
| 21 | Deploy isti JAR na produkciju **bez promena** env vars — verifikovati legacy |

---

## 13. Obrazloženje preporuke

### Zašto Dual-mode Facade?

1. **Non-destructive** — deploy bez promene config = identično ponašanje
2. **Jedan codebase** — isti JAR na svim okruženjima
3. **Stari kod ostaje** — patching legacy toka ne zahteva poseban branch
4. **Postepeni rollout** — po jedno okruženje prelazi na SC, instant rollback

### Zašto Plain HTTP (a ne sc-notifications-client)?

1. **Java 25 bloker** — bytecode version 69 na Java 17 JVM = `UnsupportedClassVersionError`
2. **Spring Boot mismatch** — auto-config pisana za 3.5.11 na runtime-u 3.2.1
3. **Tranzitivne zavisnosti** — sc-commons donosi nekompatibilne verzije
4. **Nula rizika sa plain HTTP** — `RestClient` je deo Spring Boot 3.2.1, isti JSON format, isti endpoint
5. **API je jednostavan** — 1 POST endpoint za email, trivijalan za implementaciju

### Evolucioni put

```
  Danas               Sada                   Kad OCI pređe na Java 25
  ──────              ──────                  ─────────────────────────

  MailerService  →  NotificationFacade   →  NotificationFacade
  (direktno)        ├─ legacy (default)      └─ sc-notifications (jedini)
                    └─ SC (plain HTTP)
                                              Opciono:
                                              - Zamena plain HTTP sa
                                                sc-notifications-client
                                              - Brisanje legacy grane
```

---

## 14. Post-implementacija

### Manual za operatere

Kreirati `docs/manuals/sc-notifications-integration.md`:

1. **Aktivacija SC moda** — koji env vars dodati
2. **Deaktivacija / Rollback** — ukloniti `EMAIL_NOTIFICATION_MODE`
3. **Konfiguracija provajdera** u sc-notifications
4. **Monitoring** — RabbitMQ UI, healthcheck
5. **Troubleshooting** — česti problemi
6. **Mailpit** — lokalno testiranje (http://localhost:14081)

### Dijagram konačnog stanja (SC okruženje)

```
┌───────────────────────────────────────────────────────────────────────┐
│                        SC okruženje                                   │
│                                                                       │
│  ┌──────────┐  ┌──────────────┐   NotificationFacade (oci-library)   │
│  │  oci-api │  │  oci-monitor │   mode = sc-notifications            │
│  │  :8080   │  │  :8081       │                                      │
│  └────┬─────┘  └──────┬───────┘   ScNotificationsClient              │
│       │  HTTP POST     │          (naš kod, Java 17, plain RestClient)│
│       └───────┬────────┘                                              │
│               ▼                                                       │
│    ┌────────────────────────┐                                         │
│    │   sc-notifications    │   Gateway → Dispatcher → Provider       │
│    │   :8091 (Java 25)     │   ├─ smtp_loopia (⭐1)                  │
│    │                       │   ├─ api_sendgrid (⭐2)                 │
│    │                       │   └─ api_mailtrap (⭐3)                 │
│    └──────┬────────────────┘                                         │
│    ┌──────┼──────────────┐                                            │
│    ▼      ▼              ▼                                            │
│  ┌────┐ ┌──────────┐ ┌───────────┐                                   │
│  │ PG │ │ RabbitMQ │ │  Mailpit  │                                   │
│  └────┘ └──────────┘ └───────────┘                                   │
│  ┌──────┐                                                             │
│  │MySQL │  oci-backend baza (bez promena)                            │
│  └──────┘                                                             │
└───────────────────────────────────────────────────────────────────────┘
```

### Dijagram konačnog stanja (Legacy okruženje)

```
┌───────────────────────────────────────────────────────────────────────┐
│                     Legacy okruženje                                   │
│                                                                       │
│  ┌──────────┐  ┌──────────────┐   NotificationFacade (oci-library)   │
│  │  oci-api │  │  oci-monitor │   mode = legacy (default)            │
│  │  :8080   │  │  :8081       │                                      │
│  └────┬─────┘  └──────┬───────┘   MailerService (postojeći kod)      │
│       └───────┬────────┘                                              │
│               ▼                                                       │
│    ┌────────────────────────┐                                         │
│    │   SMTP / SendGrid     │                                         │
│    │   (direktan poziv)    │                                         │
│    └────────────────────────┘                                         │
│  ┌──────┐                                                             │
│  │MySQL │  NEMA SC-NOTIFICATIONS, PG, RABBITMQ                      │
│  └──────┘  IDENTIČNO KAO PRE REFAKTORA                              │
└───────────────────────────────────────────────────────────────────────┘
```
