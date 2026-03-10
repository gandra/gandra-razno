# Refaktor oci-backend: Integracija sc-notifications

> **Datum:** 2026-03-10
> **Status:** PLAN / TODO
> **Autor:** Dragan Mijatovic

---

## Sadrzaj

1. [Trenutno stanje](#1-trenutno-stanje)
2. [Ciljevi refaktora](#2-ciljevi-refaktora)
3. [Kljucno pravilo: Non-destructive deployment](#3-kljucno-pravilo-non-destructive-deployment)
4. [Infrastrukturni preduslovi](#4-infrastrukturni-preduslovi)
5. [Pristupi integraciji (sumarno)](#5-pristupi-integraciji-sumarno)
6. [Pristup C: Dual-mode Facade + Plain HTTP](#6-pristup-c-dual-mode-facade--plain-http)
7. [Odnos sa sc-notifications-client](#7-odnos-sa-sc-notifications-client)
8. [Pristup D: oci-notifications-client-api (Bridge Service)](#8-pristup-d-oci-notifications-client-api-bridge-service)
9. [Detaljan dizajn (zajednicki elementi)](#9-detaljan-dizajn-zajednicki-elementi)
10. [Strategija baze podataka](#10-strategija-baze-podataka)
11. [Docker konfiguracija](#11-docker-konfiguracija)
12. [Lokalno i Dev/Cloud okruzenje](#12-lokalno-i-devcloud-okruzenje)
13. [Plan implementacije](#13-plan-implementacije)
14. [Obrazlozenje preporuke](#14-obrazlozenje-preporuke)
15. [Post-implementacija](#15-post-implementacija)

---

## 1. Trenutno stanje

### 1.1 Duplirani email kod

`MailerService` interfejs je identican u oba modula:

```java
public interface MailerService {
   EmailSendResponseDto sendTextEmail(@Valid SendEmailRequestDto request);
   EmailSendResponseDto sendHtmlEmail(@Valid SendEmailRequestDto request);
}
```

| Klasa | oci-api | oci-monitor | Aktivacija |
|-------|---------|-------------|------------|
| `SmtpMailerService` | da | da | `email.provider=smtp` (default, `matchIfMissing=true`) |
| `SendGridMailerService` | da | da | `email.provider=sendgrid` (`matchIfMissing=false`) |
| `EmailConfig` | da | da | `JavaMailSender` bean konfiguracija |

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
│  │  (ciste Java klase — nema @Service, @Component, @Configuration) │    │
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

1. **Uvesti sc-notifications kao novi kanal** — dodati mogucnost slanja notifikacija putem sc-notifications REST API-ja, uz zadrzavanje postojeceg email sistema
2. **Kontrola putem konfiguracije** — koji email sistem se koristi odredjuje se iskljucivo konfiguracijom, **bez promene koda** izmedju okruzenja
3. **Podrazumevano ponasanje = legacy** — ako se ne promeni nijedna konfiguracija, sistem radi identicno kao do sada
4. **Jedan codebase, vise produkcija** — isti build artifact (JAR) na sva okruzenja
5. **Failover/retry/DLQ** — na okruzenjima sa sc-notifications, automatski
6. **Prosrivost** — SMS, webhook, websocket dostupni na SC okruzenjima bez izmena koda

> **Kljucno:** Stari email kod **ostaje u codebase-u**. Aplikacija je na vise produkcija. Samo na nekim okruzenjima aktiviramo sc-notifications. Patching/bugfix na starom email toku mora biti moguc na istom codebase-u.

---

## 3. Kljucno pravilo: Non-destructive deployment

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  ISTI JAR ARTIFACT  ──deploy──►  Okruzenje X (klijent A)      │
│                     ──deploy──►  Okruzenje Y (klijent B)      │
│                     ──deploy──►  Okruzenje Z (dev/test)       │
│                                                                │
│  X:  email.notification.mode ne postoji  → default "legacy"   │
│  Y:  email.notification.mode = legacy    → SMTP/SendGrid     │
│  Z:  email.notification.mode = sc-notifications → REST API   │
│                                                                │
│  X i Y rade identicno kao pre refaktora.                      │
│  Z koristi sc-notifications.                                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

| Scenario | Ponasanje |
|----------|-----------|
| Deploy bez promene env vars | Identicno kao pre — SMTP/SendGrid |
| `email.notification.mode=sc-notifications` | Koristi sc-notifications REST API |
| SC mod, ali servis nedostupan | Loguje error, ne pada aplikacija |
| Rollback | Promena jednog property-ja |

---

## 4. Infrastrukturni preduslovi

sc-notifications **nema Dockerfile** — kreirati ga. Potrebni servisi (samo za SC okruzenja):

| Servis | Image | Portovi (local) |
|--------|-------|-----------------|
| sc-notifications | custom build (Java 25) | 8091:8081 |
| PostgreSQL 17.6 | postgres:17.6-alpine | 5432:5432 |
| RabbitMQ 4.1.4 | rabbitmq:4.1.4-management-alpine | 5672, 15672 |
| Mailpit | ghcr.io/axllent/mailpit:latest | 13081:1025, 14081:8025 |

> Legacy okruzenja ne trebaju nista od navedenog.

---

## 5. Pristupi integraciji (sumarno)

| Pristup | Status | Razlog |
|---------|--------|--------|
| **A: SDK cist prelaz** — uklanja stari kod, svi koriste SC | ❌ | Krsi non-destructive princip. Dugorocni cilj. |
| **B: Embedded** — sc-notifications kao in-process biblioteka | ❌ | Blokirano: Java 25 vs Java 17 nekompatibilnost. |
| **C: Dual-mode Facade + Plain HTTP** | ⭐ | Oba sistema zive u codebase-u. Konfig bira. Default = legacy. Naš kod u oci-library. |
| **D: oci-notifications-client-api (Bridge Service)** | ⭐⭐ | Zaseban Java 25 servis baziran na sc-notifications-test-api. Koristi oficijalni sc-notifications-client. OCI ga zove preko REST-a. |

---

## 6. Pristup C: Dual-mode Facade + Plain HTTP

### 6.1 Zasto ne koristimo sc-notifications-client kao Maven zavisnost?

**Tri blokera onemogucavaju direktno dodavanje `sc-notifications-client` u `oci-library/pom.xml`:**

| # | Problem | Detalj |
|---|---------|--------|
| 1 | **Java bytecode** | sc-notifications-client kompajliran za Java 25 (major version: 69). oci-backend JVM = Java 17 (max: 61). → `UnsupportedClassVersionError` |
| 2 | **Spring Boot verzija** | sc-notifications-client → sistemi-starter-parent → Spring Boot **3.5.11**. oci-backend → Spring Boot **3.2.1**. Auto-konfiguracija pisana za 3.5 mozda koristi API-je koji ne postoje u 3.2. |
| 3 | **Tranzitivne zavisnosti** | sc-notifications-client → sc-commons donosi Hibernate 6.6.x, QueryDSL 5.1, MapStruct 1.6, Flyway 11.3 — sve u konfliktu sa oci-backend verzijama. |

### 6.2 Sta radimo umesto toga?

Pisemo **lak REST klijent** (`ScNotificationsClient`) direktno u `oci-library` koristeci Spring-ov `RestClient` koji je vec na classpath-u. **Nula novih zavisnosti.** Pratimo isti REST API contract koji koristi sc-notifications-client, ali sa nasim kodom kompajliranim za Java 17.

---

## 7. Odnos sa sc-notifications-client

### 7.1 Sta postoji u sc-notifications-client

sc-notifications-client (`com.sistemisolutions.core.notifications.client`) sadrzi 16 Java fajlova:

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

### 7.2 Sta MI radimo u Pristupu C (Plain HTTP)

**NE koristimo** sc-notifications-client JAR kao Maven zavisnost.

**REPLICIAMO** samo ono sto nam treba — REST poziv i DTO-ove — kao nas Java 17 kod u `oci-library`:

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
│  NotificationAckAutoConfig ── LATER ──→ Opciono u buducnosti                │
│  NotificationAckListener                (kad bude potreban ACK)             │
│  NotificationDeliveryReceipt                                                │
│  NotificationDeliveryReceiptHandler                                         │
│                                                                              │
│  Enumi (3) ───────────────── NE treba ──→ Koristimo String za status       │
│  Info klase (2) ─────────── NE treba ──→ Irelevantno                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Pristup D: oci-notifications-client-api (Bridge Service)

### 8.1 Koncept

Umesto da repliciamo sc-notifications-client kod u oci-library (Pristup C), kreiramo **zaseban Java 25 projekat** — `oci-notifications-client-api` — baziran na referentnom projektu `sc-notifications-test-api`.

Ovaj projekat:
- **Java 25** — nema bytecode nekompatibilnosti
- **Koristi sc-notifications-client** kao pravu Maven zavisnost — nema repliciranja koda
- **sistemi-starter-parent** — iste verzije Spring Boot-a i zavisnosti kao sc-notifications
- **Docker kontejner** — pokrece se kao zaseban servis
- **oci-api i oci-monitor ga zovu preko REST-a** — HTTP protokol ne mari za Java verziju

### 8.2 Zasto ovo radi — eliminacija sva tri blokera

```
┌─────────────────────────────────────────────────────────────────────┐
│  BLOKER                     │  Pristup C          │  Pristup D     │
│─────────────────────────────│──────────────────────│────────────────│
│                             │                      │                │
│  Java 25 bytecode (v.69)   │  Zaobilazimo:        │  NEMA blokera: │
│  na Java 17 JVM (max 61)   │  pisemo nas kod      │  oci-notif-    │
│                             │  u Java 17           │  client-api je │
│                             │                      │  Java 25 JVM   │
│                             │                      │                │
│  Spring Boot 3.5 vs 3.2    │  Zaobilazimo:        │  NEMA blokera: │
│  auto-config API razlike    │  ne koristimo        │  parent je     │
│                             │  auto-config         │  sistemi-      │
│                             │                      │  starter-parent│
│                             │                      │  (SB 3.5.11)  │
│                             │                      │                │
│  Tranzitivne zavisnosti     │  Zaobilazimo:        │  NEMA blokera: │
│  sc-commons konflikti       │  nula novih deps     │  sc-commons    │
│                             │                      │  kompatibilan  │
│                             │                      │  sa parent POM │
│                             │                      │                │
│  MEHANIZAM:                 │  Replicirani Java 17 │  Oficijalni    │
│                             │  kod u oci-library   │  sc-notif-     │
│                             │                      │  client u      │
│                             │                      │  zasebnom JVM  │
└─────────────────────────────────────────────────────────────────────┘
```

**Kljucni uvid:** Sva tri blokera postoje samo kad klase treba ucitati u **isti JVM**. REST komunikacija je cist HTTP — potpuno agnostican na Java verziju, Spring Boot verziju i zavisnosti na drugoj strani.

### 8.3 Baza: sc-notifications-test-api — sta vec postoji

`sc-notifications-test-api` je **referentni SDK mode projekat** za sc-notifications-client. Sadrzi:

```
sc-notifications-test-api/
├── pom.xml                                 ← parent: sistemi-starter-parent:1.0.6-RELEASE
│                                              deps: sc-notifications-client, spring-boot-starter-web,
│                                                    spring-boot-starter-amqp, validation, lombok
├── src/main/java/.../testapi/
│   ├── ScNotificationsTestApiApplication   ← @SpringBootApplication (cist, bez @ComponentScan)
│   ├── controller/
│   │   ├── TestController                  ← POST /api/test/send-email, /send-webhook, /send-mattermost
│   │   └── InfoController                  ← GET /api/v1/info
│   ├── service/
│   │   └── TestNotificationService         ← koristi NotificationApiClient za slanje
│   ├── handler/
│   │   └── TestReceiptHandler              ← implements NotificationDeliveryReceiptHandler (ACK)
│   ├── config/
│   │   ├── OpenApiConfig                   ← Swagger/OpenAPI setup
│   │   └── TimeZoneConfig                  ← Europe/Belgrade
│   └── info/
│       ├── NotificationsTestApiInfo        ← module info
│       └── NotificationsTestApiGitProperties
├── src/main/resources/
│   ├── application.properties              ← springdoc, logging
│   ├── application-local.properties        ← server.port, rabbitmq, notification.client.*
│   ├── local.env                           ← API_PORT=8093, RABBITMQ_AMQP_PORT=11081
│   └── logback-spring.xml                  ← rolling file appender
└── (nema Dockerfile, nema docker-compose)
```

**Kljucni fajlovi:**

`TestNotificationService` — koristi `NotificationApiClient` direktno:
```java
@Service
@RequiredArgsConstructor
public class TestNotificationService {
    private final NotificationApiClient notificationApiClient;

    public NotificationResponse sendEmail(Map<String, String> params) {
        SendEmailRequest request = SendEmailRequest.builder()
                .to(List.of(params.getOrDefault("to", "test@example.com")))
                .subject(params.getOrDefault("subject", "Test Email"))
                .body(params.getOrDefault("body", "<h1>Hello!</h1>"))
                .html(Boolean.parseBoolean(params.getOrDefault("html", "true")))
                .deliveryMode(params.getOrDefault("deliveryMode", "DISPATCHER"))
                .build();
        return notificationApiClient.sendEmail(request);
    }
}
```

`TestReceiptHandler` — prima ACK sa RabbitMQ:
```java
@Component
public class TestReceiptHandler implements NotificationDeliveryReceiptHandler {
    @Override
    public void onReceipt(NotificationDeliveryReceipt receipt) {
        // log SUCCESS, TEMP_FAILURE, PERM_FAILURE
    }
}
```

`application-local.properties` — aktivira obe auto-konfiguracije:
```properties
notification.client.base-url=${NOTIFICATION_SERVICE_BASE_URL}  # → NotificationApiAutoConfiguration
notification.client.ack.enabled=true                           # → NotificationAckAutoConfiguration
notification.client.ack.queue=sc-test-api.notification-ack
notification.client.ack.exchange=notifications.ack.fanout
```

### 8.4 Sta MI pravimo — oci-notifications-client-api

Novi projekat baziran na sc-notifications-test-api, prilagodjen za OCI:

```
oci-notifications-client-api/                     (NOV PROJEKAT)
├── pom.xml                                       ← parent: sistemi-starter-parent:1.0.6-RELEASE
│                                                    deps: sc-notifications-client, web, amqp, validation, lombok
│                                                    (identicne zavisnosti kao sc-notifications-test-api)
│
├── Dockerfile                                    ← Java 25, FROM eclipse-temurin:25-jre-alpine
│
├── src/main/java/com/sistemisolutions/oci/notifications/
│   ├── OciNotificationsClientApiApplication.java ← @SpringBootApplication
│   │
│   ├── controller/
│   │   └── NotificationController.java           ← OCI-specificni REST endpointi
│   │       POST /api/v1/email                       (oci-api i oci-monitor zovu ovo)
│   │
│   ├── service/
│   │   └── OciNotificationService.java           ← mapira OCI request → SendEmailRequest
│   │       koristi NotificationApiClient              → prosledjuje ka sc-notifications
│   │
│   ├── handler/
│   │   └── OciReceiptHandler.java                ← implements NotificationDeliveryReceiptHandler
│   │       prima ACK sa RabbitMQ, loguje/skladisti
│   │
│   ├── dto/
│   │   ├── OciSendEmailRequest.java              ← DTO prilagodjen OCI backend-u
│   │   └── OciNotificationResponse.java          ← Response DTO za OCI
│   │
│   └── config/
│       └── OpenApiConfig.java                    ← Swagger
│
├── src/main/resources/
│   ├── application.properties
│   ├── application-local.properties
│   ├── application-dev.properties
│   └── local.env
│
└── docker/
    └── docker-compose-local.yml                  ← (opciono, za standalone razvoj)
```

### 8.5 Arhitektura — dijagram zavisnosti (build time)

```
┌─ Build time (Maven) ──────────────────────────────────────────────────────────────┐
│                                                                                    │
│  sistemi-starter-parent (Java 25, SB 3.5.11)                                    │
│       │                                                                            │
│       ├── sc-commons                                                              │
│       │       │                                                                    │
│       ├── sc-notifications-client ──────────────────────────┐                     │
│       │       │ (depends on sc-commons)                      │                     │
│       │       │                                              │                     │
│       ├── sc-notifications (servis, Docker image)           │                     │
│       │                                                      │                     │
│       └── oci-notifications-client-api (NOV)  ◄─────────────┘                     │
│               │ koristi sc-notifications-client kao Maven dep                      │
│               │ Java 25, SB 3.5.11                                                │
│               │ NEMA nikakvih konflikata — isti parent POM                        │
│               └── Dockerfile → Docker image                                       │
│                                                                                    │
│  spring-boot-starter-parent (Java 17, SB 3.2.1)                                  │
│       │                                                                            │
│       └── oci-backend                                                             │
│            ├── oci-library ←── lak HTTP klijent (RestClient, Java 17)             │
│            ├── oci-api ────── zavisi od oci-library                                │
│            └── oci-monitor ── zavisi od oci-library                                │
│                                                                                    │
│  NEMA Maven zavisnosti izmedju oci-backend i sc-* / oci-notif-client-api         │
│  Komunikacija ISKLJUCIVO preko HTTP (REST)                                        │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 8.6 Arhitektura — komunikacioni tok (runtime)

```
┌─ Runtime ──────────────────────────────────────────────────────────────────────────┐
│                                                                                    │
│  ┌──────────────────┐  ┌────────────────────┐                                     │
│  │     oci-api      │  │    oci-monitor     │     Java 17, Spring Boot 3.2.1      │
│  │     :8080        │  │    :8081           │                                     │
│  │                  │  │                    │                                     │
│  │  Notification    │  │  Notification      │                                     │
│  │  Facade          │  │  Facade            │                                     │
│  └────────┬─────────┘  └─────────┬──────────┘                                     │
│           │                      │                                                 │
│           │  email.notification.mode = ?                                           │
│           │                      │                                                 │
│      ┌────┴─────┐          ┌─────┴────┐                                            │
│      │ legacy   │          │ sc-notif │                                             │
│      │ (default)│          │          │                                             │
│      ▼          │          ▼          │                                             │
│   ┌────────┐   │   ┌───────────┐     │                                             │
│   │ SMTP / │   │   │  HTTP     │     │                                             │
│   │ SGrid  │   │   │  POST     │     │                                             │
│   │(direkt)│   │   │           │     │                                             │
│   └────────┘   │   └─────┬─────┘     │                                             │
│                │         │           │                                              │
│                │         │ REST (1)  │                                              │
│                │         ▼           │                                              │
│                │  ┌──────────────────────────────────────┐                         │
│                │  │  oci-notifications-client-api (NOV)  │  Java 25, SB 3.5       │
│                │  │  :8094                               │                         │
│                │  │                                      │                         │
│                │  │  POST /api/v1/email                  │                         │
│                │  │       │                              │                         │
│                │  │  OciNotificationService              │                         │
│                │  │       │  mapira OCI DTO →            │                         │
│                │  │       │  SendEmailRequest             │                         │
│                │  │       │                              │                         │
│                │  │  NotificationApiClient               │  ← oficijalni           │
│                │  │  (iz sc-notifications-client)        │     sc-notif-client     │
│                │  │       │                              │                         │
│                │  │  OciReceiptHandler                   │  ← ACK listener         │
│                │  │  (RabbitMQ consumer)                 │     ugradjeno           │
│                │  └───────┼──────────────────────────────┘                         │
│                │          │                                                         │
│                │          │ REST (2)                                                │
│                │          ▼                                                         │
│                │  ┌──────────────────────────────────────┐                         │
│                │  │     sc-notifications                  │  Java 25, SB 3.5       │
│                │  │     :8091                             │                         │
│                │  │                                      │                         │
│                │  │  POST /api/v1/notifications/email    │                         │
│                │  │                                      │                         │
│                │  │  Gateway → Dispatcher → Provider     │                         │
│                │  │  ├─ smtp_loopia  (failover 1)        │                         │
│                │  │  ├─ api_sendgrid (failover 2)        │                         │
│                │  │  └─ api_mailtrap (failover 3)        │                         │
│                │  │  → ACK Publisher                      │                         │
│                │  └──────────┬───────────────────────────┘                         │
│                │             │                                                      │
│                │     ┌───────┼──────────────┐                                       │
│                │     ▼       ▼              ▼                                       │
│                │   ┌────┐ ┌──────────┐ ┌───────────┐                               │
│                │   │ PG │ │ RabbitMQ │ │  Mailpit  │                               │
│                │   │5432│ │5672/15672│ │13081/14081│                               │
│                │   └────┘ └──────────┘ └───────────┘                               │
│                │                │                                                    │
│                │                │ ACK (fanout)                                       │
│                │                └──────────► oci-notifications-client-api            │
│                │                             (OciReceiptHandler prima receipts)      │
│                │                                                                    │
│  ┌──────┐     │                                                                     │
│  │MySQL │     │  oci-backend baza (bez promena)                                     │
│  │ 3306 │     │                                                                     │
│  └──────┘     │                                                                     │
│               │                                                                     │
└───────────────┘─────────────────────────────────────────────────────────────────────┘
```

### 8.7 HTTP pozivi — detaljan tok

```
oci-api / oci-monitor (Java 17)
        │
        │  HTTP POST (1)
        │  URL: http://oci-notifications-client-api:8094/api/v1/email
        │  Content-Type: application/json
        │  Body: {
        │    "to": ["user@example.com"],
        │    "subject": "Budget Alert",
        │    "body": "<h1>Prekoracenje</h1>...",
        │    "html": true,
        │    "fromEmail": "noreply@company.com"
        │  }
        │
        ▼
oci-notifications-client-api (Java 25)
        │
        │  OciNotificationService:
        │  1. Prima OciSendEmailRequest
        │  2. Mapira → SendEmailRequest (sc-notifications-client DTO)
        │  3. Poziva notificationApiClient.sendEmail(request)
        │
        │  HTTP POST (2)
        │  URL: http://sc-notifications:8091/api/v1/notifications/email
        │  Content-Type: application/json
        │  Body: {
        │    "to": ["user@example.com"],
        │    "subject": "Budget Alert",
        │    "body": "<h1>Prekoracenje</h1>...",
        │    "html": true,
        │    "fromEmail": "noreply@company.com",
        │    "deliveryMode": "DISPATCHER"
        │  }
        │
        ▼
sc-notifications (Java 25)
        │
        │  Response: HTTP 202 Accepted
        │  { "notificationUuid": "...", "status": "ACCEPTED", "channel": "EMAIL" }
        │
        ├──► Gateway → Dispatcher → Provider(smtp_loopia) → EMAIL SENT
        │
        └──► DeliveryReceiptPublisher → RabbitMQ (notifications.ack.fanout)
                                              │
                                              ▼
                                    oci-notifications-client-api
                                    OciReceiptHandler.onReceipt()
                                    → log / sacuvaj status
```

### 8.8 Prednosti Pristupa D u odnosu na Pristup C

| Aspekt | Pristup C (Plain HTTP) | Pristup D (Bridge Service) |
|--------|------------------------|----------------------------|
| **sc-notifications-client** | NE koristimo (repliciramo kod) | DA — oficijalni, kao Maven dep |
| **ACK (delivery receipts)** | Odlozeno za kasnije | Ugradjen od pocetka (RabbitMQ listener) |
| **Kod za repliciranje** | 3 klase u oci-library | 0 — koristimo originalne DTO-ove |
| **Novi kanali (webhook, SMS)** | Svaki zahteva novu metodu u nasem kodu | Dodamo endpoint, koristimo vec postojeci `NotificationApiClient` |
| **Azuriranje sc-notif-client** | Rucno azuriramo replicirani kod | `mvn versions:update` — automatski |
| **HTTP hopovi** | 1 (oci → sc-notifications) | 2 (oci → bridge → sc-notifications) |
| **Infrastruktura** | Nista dodatno | Jedan Docker kontejner vise |
| **Java kod u oci-library** | ScNotificationsClient + 2 DTO-a + mapper | Samo lak HTTP klijent (moze biti jednostavniji) |
| **Kompleksnost** | Manja (sve u jednom projektu) | Veca (jos jedan projekat za maintain) |

### 8.9 Uticaj na oci-backend

Sa Pristupom D, oci-backend i dalje treba:

1. **NotificationFacade** — dual-mode facade u oci-library (isti pattern kao Pristup C)
2. **Lak HTTP klijent** — ali sada zove `oci-notifications-client-api` umesto `sc-notifications` direktno
3. **Konfiguracija** — `email.notification.mode`, `notification.oci-api.base-url`

Razlika: klijent kod u oci-library je **jos jednostavniji** jer oci-notifications-client-api moze da izlozi API prilagodjen OCI-ju (OCI-specificni DTO-ovi, defaulti, error handling).

```
┌────────────────────────────────────────────────────────────────┐
│  Pristup C:  oci-library sadrzi                                │
│              ScNotificationsClient + ScSendEmailRequest +      │
│              ScNotificationResponse + NotificationMapper +     │
│              NotificationFacade                                │
│              (sve replicirano iz sc-notifications-client)       │
│                                                                │
│  Pristup D:  oci-library sadrzi                                │
│              OciNotificationClient + OciSendEmailRequest +     │
│              OciNotificationResponse + NotificationMapper +    │
│              NotificationFacade                                │
│              (slicna kolicina koda, ali DTO-ovi mogu biti      │
│               jednostavniji jer bridge adaptira)               │
│                                                                │
│  ZAJEDNICKO: NotificationFacade (dual-mode) je isti pattern.   │
│              Stari MailerService kod se NE BRISE.              │
│              Default = legacy.                                 │
└────────────────────────────────────────────────────────────────┘
```

### 8.10 Varijanta: Direktna zamena bez proxy-ja

Postoji varijanta gde oci-notifications-client-api **ne zove sc-notifications** vec sam sadrzi notifikacioni engine (embedded mode):

```
Varijanta D1 (Proxy/Bridge — preporucena):
  oci → oci-notifications-client-api → sc-notifications
  Light: 5 deps, deli RabbitMQ sa sc-notifications

Varijanta D2 (Standalone/Embedded):
  oci → oci-notifications-client-api (sa ugradjenim sc-notifications)
  Heavy: PG + Redis + RabbitMQ + sc-notifications + sc-core + sc-auth
  Ali: ne treba zaseban sc-notifications servis
```

D1 je preporucena jer je laka i prati SDK mode pattern. D2 ima smisla samo ako ne zelimo zaseban sc-notifications servis.

### 8.11 Port konvencija

| Servis | Port |
|--------|------|
| oci-api | 8080 |
| oci-monitor | 8081 |
| sc-notifications | 8091 (mapiran sa 8081 interno) |
| sc-notifications-test-api (referentni) | 8093 |
| **oci-notifications-client-api** | **8094** |

---

## 9. Detaljan dizajn (zajednicki elementi)

Nezavisno od toga da li se koristi Pristup C ili D, u oci-library su potrebni sledeci elementi:

### 9.1 Nove klase u oci-library

```
oci-library/src/main/java/com/sistemisolutions/oci/lib/
└── notification/
    ├── NotificationFacade.java           ← Dual-mode facade
    ├── ScNotificationsClient.java        ← Plain HTTP klijent (za Pristup C: zove sc-notifications,
    │                                        za Pristup D: zove oci-notifications-client-api)
    ├── dto/
    │   ├── ScSendEmailRequest.java       ← Request DTO
    │   └── ScNotificationResponse.java   ← Response DTO
    └── mapper/
        └── NotificationMapper.java       ← OCI DTO → SC DTO
```

### 9.2 ScNotificationsClient

```java
@Slf4j
@Component
@ConditionalOnProperty(name = "notification.sc.base-url")
public class ScNotificationsClient {

   private static final String EMAIL_PATH = "/api/v1/notifications/email";
   // Za Pristup D: EMAIL_PATH = "/api/v1/email"
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

> Bean se kreira **samo** kad `notification.sc.base-url` postoji. Legacy okruzenja: bean ne postoji, nema greske.
>
> Za Pristup C: `base-url = http://sc-notifications:8091`
> Za Pristup D: `base-url = http://oci-notifications-client-api:8094`

### 9.3 DTO-ovi

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

### 9.4 NotificationFacade

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

### 9.5 Konfiguracija po profilima

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

# Za Pristup C (direktan poziv ka sc-notifications):
# notification.sc.base-url=http://localhost:8091

# Za Pristup D (poziv ka bridge servisu):
notification.sc.base-url=http://localhost:8094
```

**application-prod.properties — BEZ PROMENA:**
```properties
# email.notification.mode ne postoji → default "legacy"
```

### 9.6 Refaktor poziva u servisima

```java
// Pre:
private final MailerService mailerService;
mailerService.sendHtmlEmail(new SendEmailRequestDto(from, to, subject, body));

// Posle:
private final NotificationFacade notificationFacade;
notificationFacade.sendHtmlEmail(new SendEmailRequestDto(from, to, subject, body));
```

> Minimalna promena — zamena inject-a. Potpis metode isti. Stari `MailerService` se NE BRISE.

---

## 10. Strategija baze podataka

oci-backend ostaje na MySQL. sc-notifications dobija **zasebnu** PostgreSQL instancu. oci-notifications-client-api **nema svoju bazu** (stateless servis).

```
┌─────────────┐     ┌──────────────────┐
│  MySQL 8.0  │     │ PostgreSQL 17.6  │
│  (ociapp)   │     │ (sc_notifications)│
│  oci-api    │     │  sc-notifications │
│  oci-monitor│     │                   │
└─────────────┘     └──────────────────┘
   bez promena       samo na SC okruzenjima

   oci-notifications-client-api → NEMA BAZU (stateless)
```

---

## 11. Docker konfiguracija

### 11.1 docker-compose-local.yml — dodati SC stack

```yaml
services:
  # Postojeci (BEZ PROMENA)
  db:
    image: "mysql/mysql-server:latest"
    # ... identicno kao sada

  # Novi: oci-notifications-client-api (Pristup D)
  oci-notifications-client-api:
    build:
      context: ../oci-notifications-client-api
      dockerfile: Dockerfile
    container_name: oci-notifications-client-api
    ports:
      - "8094:8094"
    environment:
      - SPRING_PROFILES_ACTIVE=local
      - NOTIFICATION_SERVICE_BASE_URL=http://sc-notifications:8081
      - SPRING_RABBITMQ_HOST=sc-notifications-rabbitmq
      - SPRING_RABBITMQ_PORT=5672
      - SPRING_RABBITMQ_USERNAME=notifier
      - SPRING_RABBITMQ_PASSWORD=topsecret
    depends_on:
      sc-notifications: { condition: service_healthy }

  # Novi: sc-notifications
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

### 11.2 docker-compose-cloud-dev.yml (samo SC okruzenja)

Dodati `oci-notifications-client-api`, `sc-notifications`, `sc-notifications-db`, `sc-notifications-rabbitmq`. Dodatni env vars za `api` i `monitor`:

```yaml
- "EMAIL_NOTIFICATION_MODE=sc-notifications"
- "NOTIFICATION_SC_BASE_URL=http://oci-notifications-client-api:8094"
```

> Produkcije klijenata: compose fajl **ne sadrzi** SC servise, niti nove env vars. Identicno kao pre.

---

## 12. Lokalno i Dev/Cloud okruzenje

### Lokalno — IntelliJ (Pristup D)

```
┌─ IntelliJ IDEA ──────────────────────────────────────────────────────────┐
│  Run: oci-api (8080)                                                      │
│  Run: oci-monitor (8081)                                                  │
│  Run: sc-notifications (8091)  ← IntelliJ ili Docker                     │
│  Run: oci-notifications-client-api (8094)  ← IntelliJ ili Docker         │
└──────────────────────────────────────────────────────────────────────────┘
         │              │              │              │
┌─ Docker ────────────────────────────────────────────────────────────────┐
│  MySQL(3306) PostgreSQL(5432) RabbitMQ(5672/15672) Mailpit(13081/14081)  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dev/Cloud — SC okruzenje (Pristup D)

```
┌─ Docker Host ──────────────────────────────────────────────────────────────┐
│  nginx │ ui │ api │ monitor │ db(MySQL)            ← postojece             │
│                │       │                                                    │
│                └───┬───┘ mode=sc-notifications                              │
│                    │                                                        │
│                    ▼  REST (1)                                              │
│     oci-notifications-client-api(:8094)             ← NOVO                 │
│                    │                                                        │
│                    ▼  REST (2)                                              │
│           sc-notifications(:8091)                   ← NOVO                 │
│              │       │                                                      │
│        PostgreSQL  RabbitMQ  Mailpit                ← NOVO                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dev/Cloud — Legacy okruzenje (produkcije klijenata)

```
┌─ Docker Host ──────────────────────────────────────────────────────────────┐
│  nginx │ ui │ api │ monitor │ db(MySQL)                                    │
│                │       │                                                    │
│                └───┬───┘ mode=legacy (default)                              │
│                    ▼                                                        │
│              SMTP / SendGrid (direktno)                                    │
│                                                                             │
│  NEMA OCI-NOTIFICATIONS-CLIENT-API                                         │
│  NEMA SC-NOTIFICATIONS, PG, RABBITMQ                                       │
│  IDENTICNO KAO PRE REFAKTORA                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Plan implementacije

### Faza 1: Infrastruktura (1-2 dana)

| # | Task | Lokacija |
|---|------|----------|
| 1 | Kreirati Dockerfile za sc-notifications | `sc-notifications/Dockerfile` |
| 2 | Kreirati oci-notifications-client-api projekat (Pristup D) | `oci-notifications-client-api/` |
| 3 | Kreirati Dockerfile za oci-notifications-client-api | `oci-notifications-client-api/Dockerfile` |
| 4 | Dodati SC stack u `docker-compose-local.yml` | `oci-backend/docker-compose-local.yml` |

### Faza 2: oci-notifications-client-api (2-3 dana, Pristup D)

| # | Task | Lokacija |
|---|------|----------|
| 5 | pom.xml (parent: sistemi-starter-parent, deps: sc-notifications-client) | `oci-notifications-client-api/pom.xml` |
| 6 | `OciNotificationsClientApiApplication` | `...notifications/` |
| 7 | `OciSendEmailRequest` / `OciNotificationResponse` DTO | `...notifications/dto/` |
| 8 | `OciNotificationService` (mapira → NotificationApiClient) | `...notifications/service/` |
| 9 | `NotificationController` (POST /api/v1/email) | `...notifications/controller/` |
| 10 | `OciReceiptHandler` (ACK listener) | `...notifications/handler/` |
| 11 | Properties (local, dev) | `src/main/resources/` |

### Faza 3: Kod u oci-library (1-2 dana)

| # | Task | Lokacija |
|---|------|----------|
| 12 | `ScSendEmailRequest` DTO | `oci-library/.../notification/dto/` |
| 13 | `ScNotificationResponse` DTO | `oci-library/.../notification/dto/` |
| 14 | `ScNotificationsClient` (plain HTTP ka bridge) | `oci-library/.../notification/` |
| 15 | `NotificationMapper` | `oci-library/.../notification/mapper/` |
| 16 | `NotificationFacade` (dual-mode) | `oci-library/.../notification/` |

### Faza 4: Refaktor servisa (1-2 dana)

| # | Task | Modul |
|---|------|-------|
| 17 | `UserRegistrationService` → `NotificationFacade` | oci-api |
| 18 | `UsersService` → `NotificationFacade` | oci-api |
| 19 | `BudgetNotificationService` → `NotificationFacade` | oci-monitor |
| 20 | `BudgetCompartmentService` → `NotificationFacade` | oci-monitor |
| 21 | `SubscriptionNotificationService` → `NotificationFacade` | oci-monitor |
| 22 | `CommitmentNotificationService` → `NotificationFacade` | oci-monitor |
| 23 | `CostReportsService` → `NotificationFacade` | oci-monitor |
| 24 | `MetricsNotificationEventListener` → `NotificationFacade` | oci-monitor |

### Faza 5: Konfiguracija + Test (1-2 dana)

| # | Task |
|---|------|
| 25 | Dodati `email.notification.mode` + `notification.sc.base-url` u `application-local.properties` |
| 26 | Testirati SC mod: oci-api → oci-notifications-client-api → sc-notifications → Mailpit |
| 27 | Testirati legacy mod — zakomentarisati `email.notification.mode` |
| 28 | `mvn test` — verifikovati stare testove |

### Faza 6: Deploy (1 dan)

| # | Task |
|---|------|
| 29 | Deploy na dev sa SC konfiguracijom |
| 30 | Deploy isti JAR na produkciju **bez promena** env vars — verifikovati legacy |

---

## 14. Obrazlozenje preporuke

### Zasto Dual-mode Facade?

1. **Non-destructive** — deploy bez promene config = identicno ponasanje
2. **Jedan codebase** — isti JAR na svim okruzenjima
3. **Stari kod ostaje** — patching legacy toka ne zahteva poseban branch
4. **Postepeni rollout** — po jedno okruzenje prelazi na SC, instant rollback

### Pristup C vs Pristup D — uporedni pregled

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  Pristup C: Plain HTTP u oci-library                               │
│  ═══════════════════════════════════                                │
│  + Jednostavniji (manje servisa)                                   │
│  + Jedan HTTP hop (oci → sc-notifications)                         │
│  + Nema novog projekta za odrzavanje                               │
│  - Replicira sc-notifications-client kod                           │
│  - Nema ACK-a na pocetku                                           │
│  - Svaki novi kanal = novi kod u oci-library                       │
│                                                                     │
│  Pristup D: oci-notifications-client-api (Bridge)                  │
│  ════════════════════════════════════════════════                   │
│  + Koristi oficijalni sc-notifications-client                      │
│  + ACK ugrajen od pocetka                                          │
│  + Novi kanali trivijalni (webhook, mattermost, SMS)               │
│  + Nema repliciranja — azuriranja automatska                       │
│  - Dva HTTP hopa (oci → bridge → sc-notifications)                 │
│  - Jedan Docker kontejner vise                                     │
│  - Nov projekat za odrzavanje                                      │
│                                                                     │
│  PREPORUKA: Pristup D ako planiramo vise kanala i ACK.             │
│             Pristup C ako nam treba samo email i brzi start.       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Zasto Plain HTTP klijent u oci-library (oba pristupa)?

1. **Java 25 bloker** — bytecode version 69 na Java 17 JVM = `UnsupportedClassVersionError`
2. **Nula rizika sa plain HTTP** — `RestClient` je deo Spring Boot 3.2.1
3. **API je jednostavan** — 1 POST endpoint za email, trivijalan za implementaciju

### Evolucioni put

```
  Danas               Sada                    Kad OCI predje na Java 25
  ──────              ──────                   ─────────────────────────

  MailerService  →  NotificationFacade    →  NotificationFacade
  (direktno)        ├─ legacy (default)       └─ sc-notifications (jedini)
                    └─ SC (via bridge/
                       plain HTTP)             Opciono:
                                               - Zamena bridge servisa sa
                                                 sc-notifications-client
                                                 direktno u oci-backend
                                               - Brisanje legacy grane
                                               - Gasenje bridge servisa
```

---

## 15. Post-implementacija

### Manual za operatere

Kreirati `docs/manuals/sc-notifications-integration.md`:

1. **Aktivacija SC moda** — koji env vars dodati
2. **Deaktivacija / Rollback** — ukloniti `EMAIL_NOTIFICATION_MODE`
3. **Konfiguracija provajdera** u sc-notifications
4. **Monitoring** — RabbitMQ UI, healthcheck
5. **Troubleshooting** — cesti problemi
6. **Mailpit** — lokalno testiranje (http://localhost:14081)

### Dijagram konacnog stanja — SC okruzenje (Pristup D)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                            SC okruzenje                                        │
│                                                                                │
│  ┌──────────┐  ┌──────────────┐   NotificationFacade (oci-library)            │
│  │  oci-api │  │  oci-monitor │   mode = sc-notifications                     │
│  │  :8080   │  │  :8081       │                                               │
│  └────┬─────┘  └──────┬───────┘   ScNotificationsClient (Java 17, RestClient) │
│       │  HTTP POST     │                                                       │
│       └───────┬────────┘                                                       │
│               ▼                                                                │
│    ┌─────────────────────────────────┐                                         │
│    │ oci-notifications-client-api    │  Java 25, Docker                        │
│    │ :8094                           │  koristi sc-notifications-client         │
│    │ OciNotificationService          │  ACK via RabbitMQ                       │
│    └───────────┬─────────────────────┘                                         │
│                ▼                                                                │
│    ┌─────────────────────────────────┐                                         │
│    │   sc-notifications              │  Gateway → Dispatcher → Provider        │
│    │   :8091 (Java 25)               │  ├─ smtp_loopia (1)                    │
│    │                                 │  ├─ api_sendgrid (2)                   │
│    │                                 │  └─ api_mailtrap (3)                   │
│    └──────┬──────────────────────────┘                                         │
│    ┌──────┼──────────────┐                                                     │
│    ▼      ▼              ▼                                                     │
│  ┌────┐ ┌──────────┐ ┌───────────┐                                            │
│  │ PG │ │ RabbitMQ │ │  Mailpit  │                                            │
│  └────┘ └──────────┘ └───────────┘                                            │
│  ┌──────┐                                                                      │
│  │MySQL │  oci-backend baza (bez promena)                                     │
│  └──────┘                                                                      │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Dijagram konacnog stanja — Legacy okruzenje

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                     Legacy okruzenje                                            │
│                                                                                │
│  ┌──────────┐  ┌──────────────┐   NotificationFacade (oci-library)            │
│  │  oci-api │  │  oci-monitor │   mode = legacy (default)                     │
│  │  :8080   │  │  :8081       │                                               │
│  └────┬─────┘  └──────┬───────┘   MailerService (postojeci kod)               │
│       └───────┬────────┘                                                       │
│               ▼                                                                │
│    ┌────────────────────────┐                                                  │
│    │   SMTP / SendGrid      │                                                  │
│    │   (direktan poziv)     │                                                  │
│    └────────────────────────┘                                                  │
│  ┌──────┐                                                                      │
│  │MySQL │  NEMA SC STACK-a. IDENTICNO KAO PRE REFAKTORA.                     │
│  └──────┘                                                                      │
└────────────────────────────────────────────────────────────────────────────────┘
```
