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
5. [Zasto ne mozemo koristiti sc-notifications-client direktno](#5-zasto-ne-mozemo-koristiti-sc-notifications-client-direktno)
6. [Resenje: sc-notifications-rest-client (Bridge Service)](#6-resenje-sc-notifications-rest-client-bridge-service)
7. [sc-notifications-rest-client — detaljan dizajn](#7-sc-notifications-rest-client--detaljan-dizajn)
8. [Integracija u oci-backend](#8-integracija-u-oci-backend)
9. [Docker konfiguracija](#9-docker-konfiguracija)
10. [Lokalno i Dev/Cloud okruzenje](#10-lokalno-i-devcloud-okruzenje)
11. [Plan implementacije](#11-plan-implementacije)
12. [Post-implementacija](#12-post-implementacija)

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
6. **Prosirivost** — SMS, webhook, websocket dostupni na SC okruzenjima bez izmena koda

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
| sc-notifications-rest-client | custom build (Java 25) | 8094:8094 |
| PostgreSQL 17.6 | postgres:17.6-alpine | 5432:5432 |
| RabbitMQ 4.1.4 | rabbitmq:4.1.4-management-alpine | 5672, 15672 |
| Mailpit | ghcr.io/axllent/mailpit:latest | 13081:1025, 14081:8025 |

> Legacy okruzenja ne trebaju nista od navedenog.

---

## 5. Zasto ne mozemo koristiti sc-notifications-client direktno

**Tri blokera onemogucavaju dodavanje `sc-notifications-client` kao Maven zavisnost u projekte koji nisu na Java 25:**

| # | Problem | Detalj |
|---|---------|--------|
| 1 | **Java bytecode** | sc-notifications-client kompajliran za Java 25 (major version: 69). oci-backend JVM = Java 17 (max: 61). → `UnsupportedClassVersionError` |
| 2 | **Spring Boot verzija** | sc-notifications-client → sistemi-starter-parent → Spring Boot **3.5.11**. oci-backend → Spring Boot **3.2.1**. Auto-konfiguracija pisana za 3.5 mozda koristi API-je koji ne postoje u 3.2. |
| 3 | **Tranzitivne zavisnosti** | sc-notifications-client → sc-commons donosi Hibernate 6.6.x, QueryDSL 5.1, MapStruct 1.6, Flyway 11.3 — sve u konfliktu sa starijim verzijama. |

**Kljucni uvid:** Sva tri blokera postoje samo kad klase treba ucitati u **isti JVM**. REST komunikacija je cist HTTP — potpuno agnostican na Java verziju, Spring Boot verziju i zavisnosti na drugoj strani.

---

## 6. Resenje: sc-notifications-rest-client (Bridge Service)

### 6.1 Koncept

Kreiramo **novi projekat u sc-\* ekosistemu** — `sc-notifications-rest-client` — zaseban Java 25 Spring Boot servis koji:

- **Pripada sc-\* ekosistemu** — univerzalan, nije vezan za jedan projekat
- **Java 25 + sistemi-starter-parent** — nema bytecode nekompatibilnosti, nema konflikata zavisnosti
- **Koristi sc-notifications-client** kao pravu Maven zavisnost — nema repliciranja koda
- **Pokrece se kao Docker kontejner** — pozivajuci projekti (oci, ili bilo koji drugi) ga zovu preko REST-a
- **Kod je svuda isti** — konfiguracija se menja od projekta do projekta (port, ACK queue, sc-notifications URL)
- **Baziran na sc-notifications-test-api** — vec dokazan SDK mode pattern

### 6.2 Zasto sc-notifications-rest-client a ne oci-notifications-client-api?

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  oci-notifications-client-api           sc-notifications-rest-client   │
│  ═══════════════════════════            ═══════════════════════════    │
│                                                                        │
│  ❌ Ime vezano za OCI                  ✅ Deo sc-* ekosistema          │
│  ❌ Nelogicnost u naming-u             ✅ Konzistentan naming          │
│  ❌ Percepcija: samo za OCI            ✅ Reusable za sve projekte     │
│  ❌ Package: com...oci.notifications   ✅ Package: com...notifications │
│                                            .restclient                 │
│                                                                        │
│  Kod je ISTI. Samo naziv i package se razlikuju.                      │
│  Konfiguracija odredjuje ponasanje po projektu.                       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Pozicija u sc-* ekosistemu

```
sc-* ekosistem
│
├── sc-commons                          ← bazna biblioteka
├── sc-notifications                    ← notifikacioni engine (servis)
├── sc-notifications-client             ← Spring Boot starter (biblioteka, Java 25)
├── sc-notifications-test              ← referentni projekat: embedded mode
├── sc-notifications-test-api          ← referentni projekat: SDK mode
│
└── sc-notifications-rest-client       ← NOV: bridge servis za projekte
                                          koji ne mogu koristiti
                                          sc-notifications-client direktno
                                          (Java < 25, SB < 3.5, itd.)
```

### 6.4 Princip: isti kod, razlicita konfiguracija

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  sc-notifications-rest-client  (jedan Docker image)                   │
│                                                                        │
│  Deploy za OCI:                                                       │
│    API_PORT=8094                                                      │
│    NOTIFICATION_SERVICE_BASE_URL=http://sc-notifications:8081         │
│    NOTIFICATION_ACK_QUEUE=oci.notification-ack                        │
│    RABBITMQ_AMQP_HOST=sc-notifications-rabbitmq                      │
│                                                                        │
│  Deploy za Projekat X:                                                │
│    API_PORT=8095                                                      │
│    NOTIFICATION_SERVICE_BASE_URL=http://sc-notifications-x:8081      │
│    NOTIFICATION_ACK_QUEUE=project-x.notification-ack                 │
│    RABBITMQ_AMQP_HOST=project-x-rabbitmq                             │
│                                                                        │
│  Deploy za Projekat Y:                                                │
│    API_PORT=8096                                                      │
│    NOTIFICATION_SERVICE_BASE_URL=http://sc-notifications-y:8081      │
│    NOTIFICATION_ACK_QUEUE=project-y.notification-ack                 │
│    RABBITMQ_AMQP_HOST=project-y-rabbitmq                             │
│                                                                        │
│  KOD JE ISTI. Build jednom, deploy svuda.                             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 6.5 Arhitektura — dijagram zavisnosti (build time)

```
┌─ Build time (Maven) ──────────────────────────────────────────────────────────────┐
│                                                                                    │
│  sistemi-starter-parent (Java 25, SB 3.5.11)                                    │
│       │                                                                            │
│       ├── sc-commons                                                              │
│       │       │                                                                    │
│       ├── sc-notifications-client ───────────────────────┐                        │
│       │       │ (depends on sc-commons)                    │                        │
│       │       │                                            │                        │
│       ├── sc-notifications (engine, Docker image)         │                        │
│       │                                                    │                        │
│       └── sc-notifications-rest-client (NOV) ◄────────────┘                        │
│               │ koristi sc-notifications-client kao Maven dep                      │
│               │ Java 25, SB 3.5.11 — NEMA konflikata (isti parent POM)            │
│               └── Dockerfile → Docker image                                       │
│                                                                                    │
│  spring-boot-starter-parent (Java 17, SB 3.2.1)                                  │
│       │                                                                            │
│       └── oci-backend (ili bilo koji drugi projekat)                               │
│            ├── oci-library ←── lak HTTP klijent (RestClient, Java 17)             │
│            ├── oci-api                                                             │
│            └── oci-monitor                                                         │
│                                                                                    │
│  NEMA Maven zavisnosti izmedju oci-backend i sc-* projekata                      │
│  Komunikacija ISKLJUCIVO preko HTTP (REST)                                        │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.6 Arhitektura — komunikacioni tok (runtime, OCI primer)

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
│                │  ┌───────────────────────────────────────────┐                    │
│                │  │  sc-notifications-rest-client             │  Java 25, SB 3.5  │
│                │  │  :8094                                    │                    │
│                │  │                                           │                    │
│                │  │  POST /api/v1/notifications/email         │                    │
│                │  │       │                                   │                    │
│                │  │  NotificationProxyService                 │                    │
│                │  │       │                                   │                    │
│                │  │  NotificationApiClient                    │  ← oficijalni      │
│                │  │  (iz sc-notifications-client)             │     sc-notif-client│
│                │  │       │                                   │                    │
│                │  │  DeliveryReceiptHandler                   │  ← ACK listener   │
│                │  │  (RabbitMQ consumer)                      │     od pocetka     │
│                │  └───────┼───────────────────────────────────┘                    │
│                │          │                                                         │
│                │          │ REST (2)                                                │
│                │          ▼                                                         │
│                │  ┌───────────────────────────────────────────┐                    │
│                │  │     sc-notifications                      │  Java 25, SB 3.5  │
│                │  │     :8091                                 │                    │
│                │  │                                           │                    │
│                │  │  POST /api/v1/notifications/email         │                    │
│                │  │                                           │                    │
│                │  │  Gateway → Dispatcher → Provider          │                    │
│                │  │  ├─ smtp_loopia  (failover 1)             │                    │
│                │  │  ├─ api_sendgrid (failover 2)             │                    │
│                │  │  └─ api_mailtrap (failover 3)             │                    │
│                │  │  → ACK Publisher                           │                    │
│                │  └──────────┬────────────────────────────────┘                    │
│                │             │                                                      │
│                │     ┌───────┼──────────────┐                                       │
│                │     ▼       ▼              ▼                                       │
│                │   ┌────┐ ┌──────────┐ ┌───────────┐                               │
│                │   │ PG │ │ RabbitMQ │ │  Mailpit  │                               │
│                │   │5432│ │5672/15672│ │13081/14081│                               │
│                │   └────┘ └──────────┘ └───────────┘                               │
│                │                │                                                    │
│                │                │ ACK (fanout)                                       │
│                │                └──────────► sc-notifications-rest-client            │
│                │                             (DeliveryReceiptHandler)                │
│                │                                                                    │
│  ┌──────┐     │                                                                     │
│  │MySQL │     │  oci-backend baza (bez promena)                                     │
│  │ 3306 │     │                                                                     │
│  └──────┘     │                                                                     │
│               │                                                                     │
└───────────────┘─────────────────────────────────────────────────────────────────────┘
```

### 6.7 HTTP pozivi — detaljan tok

```
Pozivajuci projekat (npr. oci-api, Java 17)
        │
        │  HTTP POST (1)
        │  URL: http://sc-notifications-rest-client:8094/api/v1/notifications/email
        │  Content-Type: application/json
        │  Body: {
        │    "to": ["user@example.com"],
        │    "subject": "Budget Alert",
        │    "body": "<h1>Prekoracenje</h1>...",
        │    "html": true,
        │    "fromEmail": "noreply@company.com",
        │    "meta": { "correlationId": "uuid-123" }
        │  }
        │
        ▼
sc-notifications-rest-client (Java 25)
        │
        │  NotificationProxyService:
        │  1. Prima SendEmailRequest (sc-notifications-client DTO)
        │  2. Poziva notificationApiClient.sendEmail(request)
        │     (koristi oficijalni NotificationApiClient)
        │
        │  HTTP POST (2)
        │  URL: http://sc-notifications:8091/api/v1/notifications/email
        │  (isti JSON body — transparentan proxy)
        │
        ▼
sc-notifications (Java 25)
        │
        │  Response: HTTP 202 Accepted
        │  { "notificationUuid": "...", "correlationId": "uuid-123",
        │    "status": "ACCEPTED", "channel": "EMAIL" }
        │
        ├──► Gateway → Dispatcher → Provider(smtp_loopia) → EMAIL SENT
        │
        └──► DeliveryReceiptPublisher → RabbitMQ (notifications.ack.fanout)
                                              │
                                              ▼
                                    sc-notifications-rest-client
                                    DeliveryReceiptHandler.onReceipt()
                                    → log delivery status
```

> **Transparentan proxy:** REST API koji izlaze sc-notifications-rest-client je **isti** kao sc-notifications API (`/api/v1/notifications/email`, `/webhook`, `/webhook/mattermost`). Pozivajuci projekat koristi iste DTO-ove (ili kompatibilan JSON). Razlika je samo URL.

---

## 7. sc-notifications-rest-client — detaljan dizajn

### 7.1 Baza: sc-notifications-test-api

`sc-notifications-test-api` je referentni SDK mode projekat koji vec demonstrira sve sto nama treba:

| Komponenta | sc-notifications-test-api | sc-notifications-rest-client |
|------------|---------------------------|------------------------------|
| Parent POM | sistemi-starter-parent:1.0.6-RELEASE | isti |
| Maven deps | sc-notifications-client, web, amqp, validation, lombok | isti |
| REST klijent | NotificationApiClient (auto-config) | isti |
| ACK handler | TestReceiptHandler | DeliveryReceiptHandler (genericki) |
| Endpointi | /api/test/send-email (test-specificni) | /api/v1/notifications/* (isti kao sc-notifications) |
| Dockerfile | nema | DA |
| Profili | local | local, dev, prod |

### 7.2 Struktura projekta

```
sc-notifications-rest-client/
├── pom.xml                                         ← parent: sistemi-starter-parent:1.0.6-RELEASE
│                                                      deps: sc-notifications-client, web, amqp,
│                                                            validation, lombok
│                                                      (identicne deps kao sc-notifications-test-api)
│
├── Dockerfile                                      ← FROM eclipse-temurin:25-jre-alpine
│
├── src/main/java/com/sistemisolutions/core/notifications/restclient/
│   ├── ScNotificationsRestClientApplication.java   ← @SpringBootApplication
│   │
│   ├── controller/
│   │   └── NotificationProxyController.java        ← proxy endpointi, isti contract kao sc-notifications
│   │       POST /api/v1/notifications/email
│   │       POST /api/v1/notifications/webhook
│   │       POST /api/v1/notifications/webhook/mattermost
│   │
│   ├── service/
│   │   └── NotificationProxyService.java           ← delegira ka NotificationApiClient
│   │
│   ├── handler/
│   │   └── DeliveryReceiptHandler.java             ← implements NotificationDeliveryReceiptHandler
│   │                                                  default: loguje receipts
│   │
│   ├── config/
│   │   ├── OpenApiConfig.java                      ← Swagger/OpenAPI
│   │   └── TimeZoneConfig.java                     ← Europe/Belgrade
│   │
│   └── info/
│       ├── RestClientInfo.java                     ← module info
│       └── RestClientGitProperties.java            ← git properties
│
├── src/main/resources/
│   ├── application.properties                      ← springdoc, logging
│   ├── application-local.properties                ← konfigurisano iz local.env
│   ├── application-dev.properties
│   ├── application-prod.properties
│   ├── local.env                                   ← portovi, RabbitMQ, sc-notifications URL
│   └── logback-spring.xml
│
└── src/test/java/
    └── ScNotificationsRestClientApplicationTests.java
```

### 7.3 Kljucni kod

**NotificationProxyController** — izlaze iste endpoint-e kao sc-notifications:

```java
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/notifications")
@Tag(name = "Notification Proxy", description = "Proxy endpoints to sc-notifications service")
public class NotificationProxyController {

    private final NotificationProxyService proxyService;

    @Operation(summary = "Send email notification")
    @PostMapping("/email")
    public NotificationResponse sendEmail(@RequestBody SendEmailRequest request) {
        return proxyService.sendEmail(request);
    }

    @Operation(summary = "Send webhook notification")
    @PostMapping("/webhook")
    public NotificationResponse sendWebhook(@RequestBody SendWebhookRequest request) {
        return proxyService.sendWebhook(request);
    }

    @Operation(summary = "Send Mattermost webhook notification")
    @PostMapping("/webhook/mattermost")
    public NotificationResponse sendMattermost(@RequestBody SendMattermostWebhookRequest request) {
        return proxyService.sendMattermost(request);
    }
}
```

> Koriste se **originalni DTO-ovi** iz sc-notifications-client: `SendEmailRequest`, `SendWebhookRequest`, `SendMattermostWebhookRequest`, `NotificationResponse`. Nema repliciranja.

**NotificationProxyService** — delegira ka sc-notifications:

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationProxyService {

    private final NotificationApiClient notificationApiClient;

    public NotificationResponse sendEmail(SendEmailRequest request) {
        log.info("Proxying email | to={} | subject={}", request.getTo(), request.getSubject());
        NotificationResponse response = notificationApiClient.sendEmail(request);
        log.info("Email proxied | uuid={} | status={}", response.getNotificationUuid(), response.getStatus());
        return response;
    }

    public NotificationResponse sendWebhook(SendWebhookRequest request) {
        log.info("Proxying webhook | url={}", request.getUrl());
        return notificationApiClient.sendWebhook(request);
    }

    public NotificationResponse sendMattermost(SendMattermostWebhookRequest request) {
        log.info("Proxying mattermost | text={}", request.getText());
        return notificationApiClient.sendMattermostWebhook(request);
    }
}
```

**DeliveryReceiptHandler** — genericko ACK logovanje:

```java
@Slf4j
@Component
public class DeliveryReceiptHandler implements NotificationDeliveryReceiptHandler {

    @Override
    public void onReceipt(NotificationDeliveryReceipt receipt) {
        switch (receipt.getStatus()) {
            case SUCCESS ->
                log.info("DELIVERED | channel={} | provider={} | correlationId={}",
                    receipt.getChannelType(), receipt.getProviderKey(), receipt.getCorrelationId());
            case PERM_FAILURE ->
                log.error("FAILED | channel={} | error={} | correlationId={}",
                    receipt.getChannelType(), receipt.getDetail(), receipt.getCorrelationId());
            case TEMP_FAILURE ->
                log.warn("TEMP_FAILURE | channel={} | error={} | correlationId={}",
                    receipt.getChannelType(), receipt.getDetail(), receipt.getCorrelationId());
            default ->
                log.info("Receipt | status={} | channel={} | correlationId={}",
                    receipt.getStatus(), receipt.getChannelType(), receipt.getCorrelationId());
        }
    }
}
```

### 7.4 Konfiguracija — local.env (OCI primer)

```properties
API_PORT=8094

RABBITMQ_AMQP_HOST=localhost
RABBITMQ_AMQP_PORT=11081
RABBITMQ_UI_PORT=12081
RABBITMQ_DEFAULT_USER=notifier
RABBITMQ_DEFAULT_PASS=topsecret

NOTIFICATION_SERVICE_BASE_URL=http://localhost:8081
NOTIFICATION_ACK_QUEUE=oci.notification-ack
```

### 7.5 Konfiguracija — application-local.properties

```properties
spring.output.ansi.enabled=ALWAYS
spring.config.import=classpath:local.env[.properties]

server.port=${API_PORT}

# RabbitMQ (deli instancu sa sc-notifications)
spring.rabbitmq.host=${RABBITMQ_AMQP_HOST}
spring.rabbitmq.port=${RABBITMQ_AMQP_PORT}
spring.rabbitmq.username=${RABBITMQ_DEFAULT_USER}
spring.rabbitmq.password=${RABBITMQ_DEFAULT_PASS}

# Notification API Client → sc-notifications
notification.client.base-url=${NOTIFICATION_SERVICE_BASE_URL}
notification.client.connect-timeout-ms=5000
notification.client.read-timeout-ms=10000

# Delivery Receipt ACK
notification.client.ack.enabled=true
notification.client.ack.queue=${NOTIFICATION_ACK_QUEUE}
notification.client.ack.exchange=notifications.ack.fanout

# OpenAPI
springdoc.api-docs.enabled=true
springdoc.swagger-ui.enabled=true
```

### 7.6 pom.xml

```xml
<parent>
    <groupId>com.sistemisolutions.core</groupId>
    <artifactId>sistemi-starter-parent</artifactId>
    <version>1.0.6-RELEASE</version>
</parent>

<artifactId>sc-notifications-rest-client</artifactId>
<version>0.0.1-SNAPSHOT</version>
<name>sc-notifications-rest-client</name>
<description>Sistemi Core — REST bridge to sc-notifications for non-Java-25 projects</description>

<dependencies>
    <dependency>
        <groupId>com.sistemisolutions.core</groupId>
        <artifactId>sc-notifications-client</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-amqp</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
</dependencies>
```

> Identicne zavisnosti kao sc-notifications-test-api. 5 direktnih zavisnosti. Nema PG, Redis, JPA.

### 7.7 Port konvencija

| Servis | Port |
|--------|------|
| sc-notifications | 8081 (interno), 8091 (mapirano lokalno) |
| sc-notifications-test-api (referentni) | 8093 |
| **sc-notifications-rest-client** | **8094** |
| oci-api | 8080 |
| oci-monitor | 8081 |

---

## 8. Integracija u oci-backend

### 8.1 Nove klase u oci-library

```
oci-library/src/main/java/com/sistemisolutions/oci/lib/
└── notification/
    ├── NotificationFacade.java           ← Dual-mode facade
    ├── ScNotificationsClient.java        ← Plain HTTP klijent (RestClient)
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

> Bean se kreira **samo** kad `notification.sc.base-url` postoji. Legacy okruzenja: bean ne postoji, nema greske.
>
> URL pokazuje na **sc-notifications-rest-client** (bridge): `http://sc-notifications-rest-client:8094`

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

> JSON format identican sa sc-notifications-client DTO-ovima. Kompatibilnost zagarantovana.

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

### 8.5 Konfiguracija — oci-backend

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
notification.sc.base-url=http://localhost:8094
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

> Minimalna promena — zamena inject-a. Potpis metode isti. Stari `MailerService` se NE BRISE.

### 8.7 Strategija baze podataka

oci-backend ostaje na MySQL. sc-notifications dobija zasebnu PostgreSQL instancu. sc-notifications-rest-client **nema svoju bazu** (stateless servis).

```
┌─────────────┐     ┌──────────────────┐
│  MySQL 8.0  │     │ PostgreSQL 17.6  │
│  (ociapp)   │     │ (sc_notifications)│
│  oci-api    │     │  sc-notifications │
│  oci-monitor│     │                   │
└─────────────┘     └──────────────────┘
   bez promena       samo na SC okruzenjima

   sc-notifications-rest-client → NEMA BAZU (stateless)
```

---

## 9. Docker konfiguracija

### 9.1 docker-compose-local.yml — dodati SC stack

```yaml
services:
  # Postojeci (BEZ PROMENA)
  db:
    image: "mysql/mysql-server:latest"
    # ... identicno kao sada

  # Novi: sc-notifications-rest-client (bridge)
  sc-notifications-rest-client:
    build:
      context: ../sc-notifications-rest-client
      dockerfile: Dockerfile
    container_name: sc-notifications-rest-client
    ports:
      - "8094:8094"
    environment:
      - SPRING_PROFILES_ACTIVE=local
      - API_PORT=8094
      - NOTIFICATION_SERVICE_BASE_URL=http://sc-notifications:8081
      - NOTIFICATION_ACK_QUEUE=oci.notification-ack
      - SPRING_RABBITMQ_HOST=sc-notifications-rabbitmq
      - SPRING_RABBITMQ_PORT=5672
      - SPRING_RABBITMQ_USERNAME=notifier
      - SPRING_RABBITMQ_PASSWORD=topsecret
    depends_on:
      sc-notifications: { condition: service_healthy }

  # Novi: sc-notifications (engine)
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

### 9.2 docker-compose-cloud-dev.yml (samo SC okruzenja)

Dodati `sc-notifications-rest-client`, `sc-notifications`, `sc-notifications-db`, `sc-notifications-rabbitmq`. Dodatni env vars za `api` i `monitor`:

```yaml
- "EMAIL_NOTIFICATION_MODE=sc-notifications"
- "NOTIFICATION_SC_BASE_URL=http://sc-notifications-rest-client:8094"
```

> Produkcije klijenata: compose fajl **ne sadrzi** SC servise, niti nove env vars. Identicno kao pre.

---

## 10. Lokalno i Dev/Cloud okruzenje

### Lokalno — IntelliJ

```
┌─ IntelliJ IDEA ──────────────────────────────────────────────────────────┐
│  Run: oci-api (8080)                                                      │
│  Run: oci-monitor (8081)                                                  │
│  Run: sc-notifications (8091)  ← IntelliJ ili Docker                     │
│  Run: sc-notifications-rest-client (8094)  ← IntelliJ ili Docker         │
└──────────────────────────────────────────────────────────────────────────┘
         │              │              │              │
┌─ Docker ────────────────────────────────────────────────────────────────┐
│  MySQL(3306) PostgreSQL(5432) RabbitMQ(5672/15672) Mailpit(13081/14081)  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dev/Cloud — SC okruzenje

```
┌─ Docker Host ──────────────────────────────────────────────────────────────┐
│  nginx │ ui │ api │ monitor │ db(MySQL)            ← postojece             │
│                │       │                                                    │
│                └───┬───┘ mode=sc-notifications                              │
│                    │                                                        │
│                    ▼  REST (1)                                              │
│     sc-notifications-rest-client(:8094)             ← NOVO                 │
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
│  NEMA SC STACK-a                                                           │
│  IDENTICNO KAO PRE REFAKTORA                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Plan implementacije

### Faza 1: sc-notifications-rest-client projekat (2-3 dana)

| # | Task | Lokacija |
|---|------|----------|
| 1 | Kreirati projekat (pom.xml, Application class) | `sc-notifications-rest-client/` |
| 2 | `NotificationProxyController` (email, webhook, mattermost) | `.../restclient/controller/` |
| 3 | `NotificationProxyService` (delegira ka NotificationApiClient) | `.../restclient/service/` |
| 4 | `DeliveryReceiptHandler` (ACK handler) | `.../restclient/handler/` |
| 5 | Konfiguracija (properties, local.env, logback) | `src/main/resources/` |
| 6 | OpenApiConfig, TimeZoneConfig, Info klase | `.../restclient/config/`, `.../restclient/info/` |
| 7 | Dockerfile | `sc-notifications-rest-client/Dockerfile` |

### Faza 2: Infrastruktura (1-2 dana)

| # | Task | Lokacija |
|---|------|----------|
| 8 | Kreirati Dockerfile za sc-notifications | `sc-notifications/Dockerfile` |
| 9 | Dodati SC stack u `docker-compose-local.yml` | `oci-backend/docker-compose-local.yml` |
| 10 | Testirati: sc-notifications + sc-notifications-rest-client rade u Docker-u | manualno |

### Faza 3: Kod u oci-library (1-2 dana)

| # | Task | Lokacija |
|---|------|----------|
| 11 | `ScSendEmailRequest` DTO | `oci-library/.../notification/dto/` |
| 12 | `ScNotificationResponse` DTO | `oci-library/.../notification/dto/` |
| 13 | `ScNotificationsClient` (plain HTTP ka bridge) | `oci-library/.../notification/` |
| 14 | `NotificationMapper` | `oci-library/.../notification/mapper/` |
| 15 | `NotificationFacade` (dual-mode) | `oci-library/.../notification/` |

### Faza 4: Refaktor servisa (1-2 dana)

| # | Task | Modul |
|---|------|-------|
| 16 | `UserRegistrationService` → `NotificationFacade` | oci-api |
| 17 | `UsersService` → `NotificationFacade` | oci-api |
| 18 | `BudgetNotificationService` → `NotificationFacade` | oci-monitor |
| 19 | `BudgetCompartmentService` → `NotificationFacade` | oci-monitor |
| 20 | `SubscriptionNotificationService` → `NotificationFacade` | oci-monitor |
| 21 | `CommitmentNotificationService` → `NotificationFacade` | oci-monitor |
| 22 | `CostReportsService` → `NotificationFacade` | oci-monitor |
| 23 | `MetricsNotificationEventListener` → `NotificationFacade` | oci-monitor |

### Faza 5: Konfiguracija + Test (1-2 dana)

| # | Task |
|---|------|
| 24 | Dodati `email.notification.mode` + `notification.sc.base-url` u `application-local.properties` |
| 25 | Testirati SC mod: oci-api → rest-client → sc-notifications → Mailpit |
| 26 | Testirati legacy mod — zakomentarisati `email.notification.mode` |
| 27 | `mvn test` — verifikovati stare testove |

### Faza 6: Deploy (1 dan)

| # | Task |
|---|------|
| 28 | Deploy na dev sa SC konfiguracijom |
| 29 | Deploy isti JAR na produkciju **bez promena** env vars — verifikovati legacy |

---

## 12. Post-implementacija

### Evolucioni put

```
  Danas               Sada                    Kad OCI predje na Java 25
  ──────              ──────                   ─────────────────────────

  MailerService  →  NotificationFacade    →  NotificationFacade
  (direktno)        ├─ legacy (default)       └─ sc-notifications (jedini)
                    └─ SC (via rest-client)
                                               Opciono:
                                               - Zamena rest-client-a sa
                                                 sc-notifications-client
                                                 direktno u oci-backend
                                               - Brisanje legacy grane
                                               - Gasenje rest-client servisa
```

### Manual za operatere

Kreirati `docs/manuals/sc-notifications-integration.md`:

1. **Aktivacija SC moda** — koji env vars dodati
2. **Deaktivacija / Rollback** — ukloniti `EMAIL_NOTIFICATION_MODE`
3. **Konfiguracija provajdera** u sc-notifications
4. **Monitoring** — RabbitMQ UI, healthcheck
5. **Troubleshooting** — cesti problemi
6. **Mailpit** — lokalno testiranje (http://localhost:14081)

### Dijagram konacnog stanja — SC okruzenje

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
│    ┌──────────────────────────────────┐                                        │
│    │ sc-notifications-rest-client     │  Java 25, Docker                       │
│    │ :8094                            │  koristi sc-notifications-client        │
│    │ NotificationProxyService         │  ACK via RabbitMQ                      │
│    └───────────┬──────────────────────┘                                        │
│                ▼                                                                │
│    ┌──────────────────────────────────┐                                        │
│    │   sc-notifications               │  Gateway → Dispatcher → Provider       │
│    │   :8091 (Java 25)                │  ├─ smtp_loopia (1)                   │
│    │                                  │  ├─ api_sendgrid (2)                  │
│    │                                  │  └─ api_mailtrap (3)                  │
│    └──────┬───────────────────────────┘                                        │
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
