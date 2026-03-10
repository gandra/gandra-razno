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
6. [Pristup C: Dual-mode sa Facade/Gateway (⭐ Preporuka)](#6-pristup-c-dual-mode-sa-facadegateway--preporuka)
7. [Dependency analiza: oci-library i sc-notifications-client](#7-dependency-analiza-oci-library-i-sc-notifications-client)
8. [Strategije za dependency problem](#8-strategije-za-dependency-problem)
9. [Detaljan dizajn preporučenog pristupa](#9-detaljan-dizajn-preporučenog-pristupa)
10. [Strategija baze podataka](#10-strategija-baze-podataka)
11. [Docker konfiguracija](#11-docker-konfiguracija)
12. [Lokalno razvojno okruženje](#12-lokalno-razvojno-okruženje)
13. [Dev/Cloud okruženje](#13-devcloud-okruženje)
14. [Plan implementacije](#14-plan-implementacije)
15. [Obrazloženje preporuke](#15-obrazloženje-preporuke)
16. [Post-implementacija](#16-post-implementacija)

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

**oci-api (3 poziva):**

| Klasa | Email | Format |
|-------|-------|--------|
| `UserRegistrationService` | Potvrda registracije | Text |
| `UserRegistrationService` | Ponovo pošalji token | HTML/Text |
| `UsersService` | Reset lozinke | Text |

**oci-monitor (6 poziva):**

| Klasa | Email | Format |
|-------|-------|--------|
| `BudgetNotificationService` | Prekoračenje budžeta | HTML |
| `BudgetCompartmentService` | Prekoračenje po kompartmentima | HTML |
| `SubscriptionNotificationService` | Limiti pretplate | HTML/Text |
| `CommitmentNotificationService` | Limiti obaveza | Text |
| `CostReportsService` | Greška cost reporta | HTML |
| `MetricsNotificationEventListener` | Metrička notifikacija | Text |

### 1.3 Trenutna infrastruktura

```
docker-compose-local.yml:      MySQL (samo)
docker-compose-cloud-dev.yml:  web(nginx) + ui + api + monitor + db(MySQL)
```

### 1.4 Dijagram trenutnog stanja

```
┌─────────────────────────────────────────────────────────────────┐
│                        oci-backend                              │
│                                                                 │
│  ┌──────────────────────┐       ┌──────────────────────────┐   │
│  │      oci-api          │       │      oci-monitor          │   │
│  │                       │       │                           │   │
│  │  MailerService (I)    │       │  MailerService (I)        │   │
│  │   ├─SmtpMailerSvc     │       │   ├─SmtpMailerSvc         │   │
│  │   └─SendGridMailerSvc │       │   └─SendGridMailerSvc     │   │
│  │                       │       │                           │   │
│  │  Pozivi: 3            │       │  Pozivi: 6                │   │
│  └──────────┬────────────┘       └──────────┬────────────────┘   │
│             └───────────┬───────────────────┘                    │
│                         ▼                                        │
│              ┌─────────────────────┐                             │
│              │   SMTP / SendGrid   │                             │
│              │   (direktan poziv)  │                             │
│              └─────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Ciljevi refaktora

1. **Uvesti sc-notifications kao novi kanal** — dodati mogućnost slanja notifikacija putem sc-notifications REST API-ja, uz zadržavanje postojećeg email sistema
2. **Kontrola putem konfiguracije** — koji email sistem se koristi (legacy SMTP/SendGrid ili sc-notifications) određuje se isključivo konfiguracijom, **bez promene koda** između okruženja
3. **Podrazumevano ponašanje = legacy** — ako se ne promeni nijedna konfiguracija, sistem radi identično kao do sada
4. **Jedan codebase, više produkcija** — isti build artifact (JAR) se deployuje na sva okruženja. Razlika je samo u konfiguraciji.
5. **Dobiti failover/retry/DLQ** — na okruženjima koja koriste sc-notifications
6. **Proširivost** — novi kanali (SMS, webhook, websocket) dostupni na SC okruženjima bez izmena koda

> **Ključno:** Stari email kod (`MailerService`, `SmtpMailerService`, `SendGridMailerService`, `EmailConfig`) **ostaje u codebase-u**. Aplikacija je deplojovana na više produkcija. Samo na nekim okruženjima ćemo aktivirati nove notifikacije. Drugi klijenti koriste stari sistem — patching/bugfix treba biti moguć na istom codebase-u.

---

## 3. Ključno pravilo: Non-destructive deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ISTI BUILD ARTIFACT (JAR)  ───deploy───►  Okruženje X         │
│                              ───deploy───►  Okruženje Y         │
│                              ───deploy───►  Okruženje Z         │
│                                                                 │
│   X:  email.notification.mode ne postoji    → default "legacy"  │
│   Y:  email.notification.mode = legacy      → SMTP/SendGrid    │
│   Z:  email.notification.mode = sc-notifications → ✨ REST API │
│                                                                 │
│   X i Y rade identično kao pre refaktora.                       │
│   Z koristi nove notifikacije putem REST API-ja.                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Scenario | Očekivano ponašanje |
|----------|---------------------|
| Deploy bez promene env vars | ✅ Radi identično kao pre — SMTP/SendGrid |
| `email.notification.mode=legacy` | ✅ Eksplicitno legacy |
| `email.notification.mode=sc-notifications` | ✅ Koristi sc-notifications REST API |
| sc-notifications mod, ali servis nedostupan | ⚠️ Loguje error, ne pada aplikacija |
| Rollback na stari deploy | ✅ Bezbedan — stari kod ne zavisi od novih klasa |

---

## 4. Infrastrukturni preduslovi

### 4.1 Dockerfile za sc-notifications

sc-notifications **nema Dockerfile**. Kreirati ga za okruženja sa SC:

```dockerfile
FROM eclipse-temurin:25-jre-alpine
WORKDIR /app
COPY target/sc-notifications-*.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 4.2 Potrebni servisi (samo za SC okruženja)

| Servis | Image | Portovi (local) |
|--------|-------|-----------------|
| sc-notifications | custom build | 8091:8081 |
| PostgreSQL 17.6 | postgres:17.6-alpine | 5432:5432 |
| RabbitMQ 4.1.4 | rabbitmq:4.1.4-management-alpine | 5672, 15672 |
| Mailpit | ghcr.io/axllent/mailpit:latest | 13081:1025, 14081:8025 |

> Legacy okruženja ne trebaju ništa od navedenog.

---

## 5. Pristupi integraciji (sumarno)

| Pristup | Opis | Status |
|---------|------|--------|
| **A: SDK čist prelaz** | Potpun prelaz na sc-notifications, uklanja stari email kod | ❌ Krši non-destructive princip. Dugoročni cilj. |
| **B: Embedded mode** | sc-notifications kao in-process biblioteka u oci-backend JVM | ❌ **Blokirano:** Java 25 vs Java 17 nekompatibilnost |
| **C: Dual-mode Facade** | Oba sistema žive u codebase-u, konfig bira mod | ⭐ **Preporuka** — detalji u sekciji 6 |

Pristup **A** je **dugoročni cilj** — kada sve produkcije pređu na sc-notifications, Pristup C se transformiše u A brisanjem legacy koda.

Pristup **B** zahteva nadogradnju oci-backend na Java 25 — zaseban, visokorizičan projekat koji nije predmet ovog plana.

---

## 6. Pristup C: Dual-mode sa Facade/Gateway (⭐ Preporuka)

`NotificationFacade` u `oci-library` podržava oba moda — legacy i sc-notifications. Mod se bira **isključivo konfiguracijom**. Default: `legacy`.

```
┌────────────────────────────────────────────────────────────────────────┐
│                           oci-backend                                  │
│                                                                        │
│  ┌─────────────────────┐        ┌────────────────────────────┐        │
│  │      oci-api         │        │      oci-monitor            │        │
│  │  UserRegistration    │        │  BudgetNotificationSvc      │        │
│  │  UsersService        │        │  BudgetCompartmentSvc       │        │
│  │  ...                 │        │  CostReportsService  ...    │        │
│  └──────────┬───────────┘        └──────────────┬──────────────┘        │
│             └──────────────┬────────────────────┘                       │
│                            ▼                                            │
│           ┌───────────────────────────────────┐                        │
│           │     NotificationFacade            │  (oci-library)         │
│           │     email.notification.mode       │                        │
│           └───────────┬───────────────────────┘                        │
│                       │                                                 │
│          ┌────────────┴─────────────┐                                   │
│          │                          │                                   │
│  ┌───────┴───────┐       ┌─────────┴──────────┐                        │
│  │ mode=legacy   │       │ mode=sc-notif.     │                        │
│  │ (DEFAULT)     │       │                     │                        │
│  │               │       │ ScNotifications     │                        │
│  │ MailerService │       │ RestClient          │                        │
│  │ (postojeći)   │       │ (HTTP POST)         │                        │
│  └───────┬───────┘       └─────────┬───────────┘                        │
│          │                         │                                    │
│          ▼                         ▼                                    │
│  ┌──────────────┐       ┌──────────────────────┐                       │
│  │ SMTP/SendGrid│       │  sc-notifications    │                       │
│  │ (direktno)   │       │  REST API (:8091)    │                       │
│  └──────────────┘       └──────────────────────┘                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Dependency analiza: oci-library i sc-notifications-client

### 7.1 Karakter oci-library modula

Analiza `oci-library/pom.xml` i source koda:

```
oci-library/
├── pom.xml                    ← packaging: jar, spring-boot-maven-plugin: skip=true
├── src/main/java/
│   └── com/sistemisolutions/oci/lib/
│       ├── bean/              ← 1 POJO
│       ├── common/            ← BaseEntity, PageableFilter, enums
│       ├── dto/               ← 11 DTO klasa
│       ├── entity/            ← ~50 JPA @Entity klasa
│       ├── enums/             ← 13 enum tipova
│       ├── exception/         ← 2 custom exception klase
│       └── utils/             ← 11 utility klasa
└── (NEMA @Service, @Component, @Configuration, @Bean)
```

**Ključne karakteristike:**
- **Plain JAR** — `spring-boot-maven-plugin` sa `<skip>true</skip>`
- **Nula Spring beans** — čiste Java klase: entity-ji, DTO-ovi, enum-ovi, utility-ji
- **Nema auto-konfiguracije** — nema `META-INF/spring.factories` niti `AutoConfiguration.imports`
- **Minimalne zavisnosti** — samo `spring-boot-starter-test` (test scope) + `opencsv`
- Nasleđuje sve zavisnosti iz parent POM-a (`oci-backend/pom.xml`)

### 7.2 Karakter sc-notifications-client modula

```
sc-notifications-client/
├── pom.xml                    ← parent: sistemi-starter-parent:1.0.6-RELEASE
├── src/main/java/             ← 16 Java fajlova (client, config, DTOs, enums, handler)
└── src/main/resources/
    └── META-INF/spring/
        └── org.springframework.boot.autoconfigure.AutoConfiguration.imports
            ├── NotificationApiAutoConfiguration    ← @ConditionalOnProperty("notification.client.base-url")
            └── NotificationAckAutoConfiguration    ← @ConditionalOnProperty("notification.client.ack.enabled")
```

### 7.3 Identifikovani problemi

#### ❌ PROBLEM 1: Java Bytecode Nekompatibilnost (BLOKER)

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  sc-notifications-client.jar                                       │
│  ├── NotificationApiClient.class    → major version: 69 (Java 25) │
│  └── (sve klase)                    → major version: 69 (Java 25) │
│                                                                    │
│  sc-commons.jar (tranzitivna zavisnost)                            │
│  ├── AppException.class             → major version: 69 (Java 25) │
│  └── (sve klase)                    → major version: 69 (Java 25) │
│                                                                    │
│  oci-backend JVM                                                   │
│  └── Java 17                        → max major version: 61        │
│                                                                    │
│  REZULTAT: UnsupportedClassVersionError pri učitavanju bilo       │
│  koje klase iz sc-notifications-client ili sc-commons              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Verifikovano:**
```
$ javap -verbose NotificationApiClient.class | grep "major version"
  major version: 69

$ javap -verbose AppException.class | grep "major version"
  major version: 69
```

`sistemi-starter-parent:1.0.6-RELEASE` definiše:
```xml
<java.version>25</java.version>
<maven.compiler.source>25</maven.compiler.source>
<maven.compiler.target>25</maven.compiler.target>
```

**Java 17 JVM ne može učitati klase kompajlirane za Java 25.** Ovo je hardkodirana JVM limitacija — nema workaround-a na runtime nivou.

#### ⚠️ PROBLEM 2: Spring Boot Version Mismatch

| Aspekt | oci-backend | sc-notifications-client |
|--------|-------------|------------------------|
| Spring Boot | **3.2.1** | **3.5.11** (via sistemi-starter-parent) |
| Spring Framework | ~6.1.x | ~6.2.x |
| Hibernate | 6.4.4.Final | 6.6.29.Final |

Čak i ako se reši Problem 1, Spring Boot 3.5.11 klase (iz auto-konfiguracije) možda koriste API-je koji ne postoje u Spring Boot 3.2.1 runtime-u.

#### ⚠️ PROBLEM 3: Tranzitivne zavisnosti — verzijski konflikti

`sc-notifications-client` → `sc-commons` donosi:

| Zavisnost | oci-backend verzija | sc-commons verzija | Konflikt |
|-----------|--------------------|--------------------|:--------:|
| QueryDSL | 5.0.0 | 5.1.0 | ⚠️ |
| MapStruct | 1.5.5.Final | 1.6.3 | ⚠️ |
| Lombok | 1.18.30 | 1.18.42 | ⚠️ |
| Flyway | 10.0.1 | 11.3.3 | ⚠️ |
| Jackson | 2.16.0 | (Spring Boot 3.5.x managed) | ⚠️ |

Maven dependency resolution bi birao jednu verziju (nearest-wins), ali nepodudarnost može izazvati runtime greške.

### 7.4 Zaključak dependency analize

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  sc-notifications-client se NE MOŽE dodati kao              │
│  Maven zavisnost u oci-library/pom.xml                      │
│                                                              │
│  Razlog: Java 25 bytecode na Java 17 JVM                    │
│  = UnsupportedClassVersionError                             │
│                                                              │
│  Čak i sa cross-kompilacijom: Spring Boot version           │
│  mismatch (3.5.11 vs 3.2.1) donosi rizik.                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Strategije za dependency problem

### 8.1 Strategija D-A: Plain HTTP RestClient u oci-library (⭐ Preporuka)

**Opis:** Napisati lak REST klijent direktno u `oci-library` koristeći Spring-ov `RestClient` (već na classpath-u oci-backend-a). Nema zavisnosti na sc-notifications-client. Nema Java version problema.

```
┌────────────────────────────────────────────────────────────────┐
│                      oci-library                               │
│                                                                │
│  ScNotificationsClient.java  ← NAŠI klasa, plain HTTP        │
│  SendEmailRequest.java       ← NAŠI DTO (kopija strukture)   │
│  NotificationResponse.java   ← NAŠI DTO (kopija strukture)   │
│  NotificationFacade.java     ← Dual-mode facade              │
│                                                                │
│  Zavisnosti: NULA novih (RestClient je deo spring-boot-web)  │
│  Java version: 17 ✅                                          │
│  Spring Boot: 3.2.1 ✅                                        │
│  Tranzitivne zavisnosti: NULA novih ✅                        │
└────────────────────────────────────────────────────────────────┘
```

**Implementacija:**

```java
@Slf4j
@Component
@ConditionalOnProperty(name = "email.notification.mode", havingValue = "sc-notifications")
public class ScNotificationsClient {

   private final RestClient restClient;

   public ScNotificationsClient(
         @Value("${notification.sc.base-url}") String baseUrl,
         @Value("${notification.sc.connect-timeout-ms:5000}") int connectTimeout,
         @Value("${notification.sc.read-timeout-ms:10000}") int readTimeout) {
      this.restClient = RestClient.builder()
         .baseUrl(baseUrl)
         .build();
   }

   public ScNotificationResponse sendEmail(ScSendEmailRequest request) {
      return restClient.post()
         .uri("/api/v1/notifications/email")
         .contentType(MediaType.APPLICATION_JSON)
         .body(request)
         .retrieve()
         .body(ScNotificationResponse.class);
   }
}
```

DTO-ovi su jednostavni POJO-i — ne zahtevaju sc-notifications-client:

```java
@Data @Builder
public class ScSendEmailRequest {
   private List<String> to;
   private String subject;
   private String body;
   private boolean html;
   private String fromEmail;
   private String fromName;
   // opciono: cc, bcc, replyToEmail, providerKeys, meta
}

@Data
public class ScNotificationResponse {
   private String notificationUuid;
   private String correlationId;
   private String status;  // ACCEPTED, REJECTED, QUEUED
   private String channel;
}
```

**Prednosti:**

| # | Prednost |
|---|----------|
| 1 | **Nula novih zavisnosti** — RestClient je deo spring-boot-starter-web (već u classpath-u) |
| 2 | **Nula Java version rizika** — sve je Java 17 kod |
| 3 | **Nula Spring Boot version konflikta** — ne uvozimo tuđi BOM |
| 4 | **Potpuna kontrola** — naš kod, naši DTO-ovi, lako se menja |
| 5 | **@ConditionalOnProperty** — bean se kreira samo kad treba |
| 6 | sc-notifications REST API je stabilan i jednostavan (3 endpointa) |

**Mane:**

| # | Mana | Ozbiljnost |
|---|------|:----------:|
| 1 | DTO-ovi su kopija — treba ručno održavati ako se API menja | ⚠️ Nisko (API je stabilan) |
| 2 | Nema ACK listener-a iz kutije — treba ga implementirati ručno | ⚠️ Srednje (opcionalno) |
| 3 | Nema auto-retry na HTTP nivou | ⚠️ Nisko (sc-notifications ima interni retry) |

---

### 8.2 Strategija D-B: Cross-kompilacija sc-notifications-client za Java 17

**Opis:** Dodati build profil u sc-notifications-client koji kompajlira sa `-source 17 -target 17`. Objaviti poseban artifact (npr. classifier `java17`).

**Preduslov:** sc-notifications-client kod NE koristi Java 18+ jezičke feature-ove. Verifikovano — nema `sealed`, `record`, pattern matching, enhanced switch. Tehnički izvodljivo.

```xml
<!-- sc-notifications-client/pom.xml — novi profil -->
<profile>
    <id>java17</id>
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <maven.compiler.release>17</maven.compiler.release>
    </properties>
</profile>
```

**Problem:** sc-commons je takođe Java 25. Treba cross-kompajlirati i sc-commons za Java 17.

| Aspekt | Ocena |
|--------|-------|
| Java bytecode | ✅ Rešeno cross-kompilacijom |
| Spring Boot mismatch | ⚠️ Još uvek 3.5.11 auto-config sa 3.2.1 runtime |
| Tranzitivne zavisnosti | ⚠️ sc-commons donosi verzijski konflikt |
| Održavanje | ❌ Treba buildovati/objavljivati 2 artifacta (java17 + java25) |
| Rizik | ⚠️ Spring Boot 3.5 auto-config na 3.2 runtime-u — nepredvidivo |

---

### 8.3 Strategija D-C: Extrahovati sc-notifications-client-api modul

**Opis:** Kreirati ultra-tanak modul `sc-notifications-client-api` koji sadrži samo DTO-ove i interfejse. Kompajlirati za Java 17. Bez sc-commons zavisnosti, bez Spring auto-konfiguracije.

| Aspekt | Ocena |
|--------|-------|
| Java bytecode | ✅ Java 17 target |
| Tranzitivne zavisnosti | ✅ Nema (samo Lombok + Jackson) |
| Održavanje | ⚠️ Nov modul u sc-* ekosistemu |
| Reusability | ✅ Koristi ga i oci-backend i drugi Java 17 projekti |

---

### 8.4 Uporedna tabela dependency strategija

| Kriterijum | D-A: Plain HTTP (⭐) | D-B: Cross-compile | D-C: client-api modul |
|------------|:--------------------:|:-------------------:|:---------------------:|
| **Novih zavisnosti** | 0 | 2 (client + commons) | 1 (client-api) |
| **Java version rizik** | ✅ Nema | ⚠️ Cross-compile | ✅ Nema |
| **Spring Boot konflikt** | ✅ Nema | ⚠️ 3.5 vs 3.2 | ✅ Nema |
| **Tranzitivne zavisnosti** | ✅ Nema novih | ❌ sc-commons | ✅ Nema |
| **Održavanje DTO-ova** | ⚠️ Ručna kopija | ✅ Automatski | ✅ Automatski |
| **ACK support** | ⚠️ Ručno | ✅ Ugrađen | ⚠️ Ručno |
| **Složenost impl.** | ✅ Najniža | ⚠️ Srednja | ⚠️ Srednja |
| **Rizik** | ✅ Najniži | ❌ Najviši | ⚠️ Srednji |
| **Potrebna promena u sc-* | ❌ Ne | ✅ Da | ✅ Da |

---

## 9. Detaljan dizajn preporučenog pristupa

Kombinacija: **Pristup C (Dual-mode Facade)** + **Strategija D-A (Plain HTTP RestClient)**

### 9.1 Nove klase u oci-library

```
oci-library/src/main/java/com/sistemisolutions/oci/lib/
└── notification/
    ├── NotificationFacade.java         ← Centralni facade (dual-mode)
    ├── ScNotificationsClient.java      ← Plain HTTP klijent za sc-notifications
    ├── dto/
    │   ├── ScSendEmailRequest.java     ← Request DTO
    │   └── ScNotificationResponse.java ← Response DTO
    └── mapper/
        └── NotificationMapper.java     ← OCI SendEmailRequestDto → ScSendEmailRequest
```

### 9.2 NotificationFacade — centralna klasa

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationFacade {

   private final MailerService mailerService;
   private final Optional<ScNotificationsClient> scNotifClient;

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
      ScNotificationsClient client = scNotifClient.orElseThrow(() ->
         new IllegalStateException(
            "email.notification.mode=sc-notifications but " +
            "notification.sc.base-url is not configured"));

      ScSendEmailRequest scRequest = NotificationMapper.toScRequest(request, html);
      ScNotificationResponse response = client.sendEmail(scRequest);

      log.info("SC-Notification | uuid={} | status={} | to={}",
         response.getNotificationUuid(), response.getStatus(), request.getTo());

      return EmailSendResponseDto.builder()
         .emailSentTo(request.getTo())
         .emailProvider("sc-notifications")
         .error("REJECTED".equals(response.getStatus()))
         .build();
   }
}
```

### 9.3 ScNotificationsClient — plain HTTP

```java
@Slf4j
@Component
@ConditionalOnProperty(name = "notification.sc.base-url")
public class ScNotificationsClient {

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
         .uri("/api/v1/notifications/email")
         .body(request)
         .retrieve()
         .body(ScNotificationResponse.class);
   }
}
```

> **Napomena:** `ScNotificationsClient` bean se kreira **samo** kad `notification.sc.base-url` postoji u konfiguraciji. Na legacy okruženjima — bean ne postoji, nema greške.

### 9.4 Dijagram toka odlučivanja

```
                    ┌──────────────────────┐
                    │  Servis poziva       │
                    │  facade.sendEmail()  │
                    └──────────┬───────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │ email.notification     │
                  │ .mode = ?              │
                  └────────┬───────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
     ┌────────────────┐      ┌──────────────────┐
     │ "legacy"       │      │ "sc-notifications"│
     │ (default)      │      │                    │
     └───────┬────────┘      └────────┬───────────┘
             │                        │
             ▼                        ▼
  ┌────────────────────┐   ┌────────────────────────┐
  │ mailerService      │   │ ScNotificationsClient  │
  │ .sendTextEmail()   │   │ .sendEmail()           │
  │                    │   │                         │
  │ SmtpMailerSvc ili  │   │ HTTP POST ka            │
  │ SendGridMailerSvc  │   │ sc-notifications:8091   │
  │ (zavisi od         │   │                         │
  │ email.provider)    │   │ → Gateway → Dispatcher  │
  └────────┬───────────┘   │ → Channel → Provider    │
           │               │ → ACK                   │
           ▼               └────────────┬─────────────┘
     ┌───────────┐                     │
     │ SMTP ili  │                     ▼
     │ SendGrid  │           ┌──────────────────┐
     │ (direktno)│           │ Failover chain:  │
     └───────────┘           │ Loopia → SGrid   │
                             │ → Mailtrap → ... │
                             └──────────────────┘
```

### 9.5 Konfiguracija po profilima

#### application.properties (BEZ PROMENA)
```properties
email.provider=smtp
support.email=${NO_REPLY_EMAIL}
spring.sendgrid.api-key=${SENDGRID_API_KEY}
app.smtp.mail.host=${SMTP_HOST}
# ... ostali SMTP properties — bez promena
```

#### application-local.properties (DODATI)
```properties
# --- SC Notifications (novi) ---
email.notification.mode=sc-notifications
notification.sc.base-url=http://localhost:8091
```

#### application-dev.properties (za SC okruženja — DODATI)
```properties
email.notification.mode=sc-notifications
notification.sc.base-url=http://sc-notifications:8081
```

#### application-prod.properties (BEZ PROMENA)
```properties
# email.notification.mode NE POSTOJI → default "legacy"
# Sve radi identično kao pre refaktora
```

### 9.6 Refaktor poziva u servisima

**Pre:**
```java
private final MailerService mailerService;
mailerService.sendHtmlEmail(new SendEmailRequestDto(from, to, subject, body));
```

**Posle:**
```java
private final NotificationFacade notificationFacade;
notificationFacade.sendHtmlEmail(new SendEmailRequestDto(from, to, subject, body));
```

> Minimalna promena — samo zamena inject-a. Potpis metode ostaje isti.

---

## 10. Strategija baze podataka

oci-backend ostaje na MySQL. sc-notifications dobija zasebnu PostgreSQL instancu.

```
┌─────────────┐     ┌──────────────────┐
│  MySQL 8.0  │     │ PostgreSQL 17.6  │
│  (ociapp)   │     │ (sc_notifications)│
│             │     │                   │
│  oci-api    │     │  sc-notifications │
│  oci-monitor│     │                   │
└─────────────┘     └──────────────────┘
   postojeće             samo na SC
   bez promena           okruženjima
```

Nema rizika od cross-kontaminacije. Nezavisni lifecycle-ovi. Legacy okruženja ne trebaju PostgreSQL.

---

## 11. Docker konfiguracija

### 11.1 Izmene u `docker-compose-local.yml`

Dodati sc-notifications stack pored postojećeg MySQL-a:

```yaml
services:
  # --- Postojeći (BEZ PROMENA) ---
  db:
    image: "mysql/mysql-server:latest"
    # ... identično kao sada

  # --- Novi: sc-notifications stack ---
  sc-notifications:
    build:
      context: ../sc-notifications
      dockerfile: Dockerfile
    container_name: sc-notifications
    restart: always
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
      sc-notifications-db:
        condition: service_healthy
      sc-notifications-rabbitmq:
        condition: service_healthy

  sc-notifications-db:
    image: "postgres:17.6-alpine"
    container_name: sc-notifications-db
    restart: always
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
    restart: always
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
    restart: always
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

### 11.2 Izmene u `docker-compose-cloud-dev.yml` (samo SC okruženja)

Dodati `sc-notifications`, `sc-notifications-db`, `sc-notifications-rabbitmq` servise. Mailpit nije potreban — koriste se pravi SMTP provajderi.

Dodatni env vars za `api` i `monitor` (**samo na SC okruženjima**):

```yaml
api:
  environment:
    # ... sve postojeće OSTAJE ...
    - "EMAIL_NOTIFICATION_MODE=sc-notifications"
    - "NOTIFICATION_SC_BASE_URL=http://sc-notifications:8081"

monitor:
  environment:
    # ... sve postojeće OSTAJE ...
    - "EMAIL_NOTIFICATION_MODE=sc-notifications"
    - "NOTIFICATION_SC_BASE_URL=http://sc-notifications:8081"
```

> Na produkcijama klijenata — compose fajl **ne sadrži** sc-notifications servise, niti `EMAIL_NOTIFICATION_MODE` env var. Identično kao pre.

---

## 12. Lokalno razvojno okruženje

### 12.1 sc-notifications iz IntelliJ (⭐ Preporuka)

```
┌─ IntelliJ IDEA ────────────────────────────────────┐
│                                                     │
│  Run: oci-api (port 8080, profile: local)          │
│  Run: oci-monitor (port 8081, profile: local)      │
│  Run: sc-notifications (port 8091, profile: local) │
│                                                     │
└─────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─ Docker (docker-compose-local.yml) ────────────────┐
│                                                     │
│  MySQL (3306)        — oci-backend                 │
│  PostgreSQL (5432)   — sc-notifications            │
│  RabbitMQ (5672/15672) — sc-notifications           │
│  Mailpit (13081/14081) — email testing             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 12.2 Legacy mod (testiranje backward compat.)

Zakomentarisati `email.notification.mode` u `application-local.properties`:
```properties
# email.notification.mode=sc-notifications  ← zakomentarisano
```
→ Sistem automatski koristi legacy SMTP/SendGrid. Docker: samo `db` servis.

---

## 13. Dev/Cloud okruženje

### SC okruženje

```
┌─ Docker Host (dev) ───────────────────────────────────────────┐
│  nginx  │  ui  │  api  │  monitor  │  db(MySQL)  ← postojeće │
│                    │          │                                 │
│                    └────┬─────┘  email.notification.mode       │
│                         │        = sc-notifications             │
│                         ▼                                      │
│               sc-notifications (:8091) ← novo                  │
│                    │        │                                   │
│              PostgreSQL  RabbitMQ    ← novo                    │
└────────────────────────────────────────────────────────────────┘
```

### Legacy okruženje (produkcije klijenata)

```
┌─ Docker Host (prod) ──────────────────────────────────────────┐
│  nginx  │  ui  │  api  │  monitor  │  db(MySQL)               │
│                    │          │                                 │
│                    └────┬─────┘  email.notification.mode       │
│                         │        = legacy (default)            │
│                         ▼                                      │
│               SMTP / SendGrid (direktno)                       │
│                                                                │
│  NEMA SC-NOTIFICATIONS, NEMA PG, NEMA RABBITMQ               │
│  SVE RADI IDENTIČNO KAO PRE REFAKTORA                        │
└────────────────────────────────────────────────────────────────┘
```

---

## 14. Plan implementacije

### Faza 1: Infrastruktura (1-2 dana)

| # | Task | Lokacija |
|---|------|----------|
| 1 | Kreirati Dockerfile za sc-notifications | `sc-notifications/Dockerfile` |
| 2 | Dodati sc-notifications stack u `docker-compose-local.yml` | `oci-backend/docker-compose-local.yml` |

### Faza 2: Kod u oci-library (2-3 dana)

| # | Task | Lokacija |
|---|------|----------|
| 3 | Kreirati `ScSendEmailRequest` DTO | `oci-library/.../notification/dto/` |
| 4 | Kreirati `ScNotificationResponse` DTO | `oci-library/.../notification/dto/` |
| 5 | Kreirati `ScNotificationsClient` (plain HTTP) | `oci-library/.../notification/` |
| 6 | Kreirati `NotificationMapper` | `oci-library/.../notification/mapper/` |
| 7 | Kreirati `NotificationFacade` (dual-mode) | `oci-library/.../notification/` |

### Faza 3: Refaktor servisa (1-2 dana)

| # | Task | Lokacija |
|---|------|----------|
| 8 | `UserRegistrationService` → `NotificationFacade` | oci-api |
| 9 | `UsersService` → `NotificationFacade` | oci-api |
| 10 | `BudgetNotificationService` → `NotificationFacade` | oci-monitor |
| 11 | `BudgetCompartmentService` → `NotificationFacade` | oci-monitor |
| 12 | `SubscriptionNotificationService` → `NotificationFacade` | oci-monitor |
| 13 | `CommitmentNotificationService` → `NotificationFacade` | oci-monitor |
| 14 | `CostReportsService` → `NotificationFacade` | oci-monitor |
| 15 | `MetricsNotificationEventListener` → `NotificationFacade` | oci-monitor |

### Faza 4: Konfiguracija (0.5 dana)

| # | Task | Lokacija |
|---|------|----------|
| 16 | Dodati `email.notification.mode` + `notification.sc.base-url` | `application-local.properties` (oba) |

### Faza 5: Testiranje (1-2 dana)

| # | Task | Opis |
|---|------|------|
| 17 | Testirati SC mod lokalno | Mailpit UI: http://localhost:14081 |
| 18 | Testirati legacy mod lokalno | Zakomentarisati `email.notification.mode` |
| 19 | Proveriti da stari testovi prolaze | `mvn test` |

### Faza 6: Deploy (1 dan)

| # | Task | Opis |
|---|------|------|
| 20 | Deploy na dev sa SC konfiguracijom | Verifikovati email tokove |
| 21 | Deploy isti JAR na produkciju **bez promena** env vars | Verifikovati legacy mod |

> **Napomena:** `MailerService`, `SmtpMailerService`, `SendGridMailerService`, `EmailConfig` se **NE BRIŠU**.

---

## 15. Obrazloženje preporuke

**Preporuka: Pristup C (Dual-mode Facade) + Strategija D-A (Plain HTTP RestClient) ⭐**

### Zašto Dual-mode Facade?

1. **Non-destructive deployment** — deploy bez promene konfiguracije = identično ponašanje. Apsolutni prioritet jer je aplikacija na više produkcija.
2. **Jedan codebase** — isti JAR radi na svim okruženjima, razlika je samo u `email.notification.mode` property-ju.
3. **Stari kod ostaje** — patching legacy email toka ne zahteva poseban branch.
4. **Postepeni rollout** — jedno po jedno okruženje prelazi na SC, sa instant rollback opcijom.

### Zašto Plain HTTP RestClient (a ne sc-notifications-client)?

1. **Java 25 bytecode bloker** — sc-notifications-client je kompajliran za Java 25 (`major version: 69`). oci-backend JVM je Java 17 (`max version: 61`). **`UnsupportedClassVersionError`** bi pao pri prvom pokušaju učitavanja klase.
2. **Spring Boot version mismatch** — sc-notifications-client dolazi sa Spring Boot 3.5.11 auto-konfiguracijom, oci-backend koristi 3.2.1. Nepredvidivi runtime problemi.
3. **Tranzitivne zavisnosti** — sc-commons donosi Hibernate 6.6.x, QueryDSL 5.1, MapStruct 1.6 — sve u konfliktu sa oci-backend verzijama.
4. **Nula rizika sa plain HTTP** — `RestClient` je deo Spring Boot 3.2.1 koji oci-backend već koristi. Nema novih zavisnosti, nema version konflikta, nema bytecode problema.
5. **API je jednostavan** — sc-notifications ima 3 REST endpointa. Napisati HTTP klijent za 3 POST poziva je trivijalno.

### Evolucioni put

```
  Danas               Faza 1                  Dugoročno
  ──────              ──────                  ──────────

  MailerService  →  NotificationFacade   →  NotificationFacade
  (direktno)        ├─ legacy (default)      └─ sc-notifications (jedini)
                    └─ SC (plain HTTP)
                                              Brisanje:
                                              - MailerService, SmtpSvc, SendGridSvc
                                              - legacy grana u Facade
                                              - Opciono: zamena plain HTTP
                                                sa sc-notifications-client
                                                (kad oci-backend pređe na Java 25)
```

---

## 16. Post-implementacija

### Manual za operatere

Kreirati `docs/manuals/sc-notifications-integration.md`:

1. **Aktivacija SC moda** — koji env vars dodati
2. **Deaktivacija / Rollback** — ukloniti `EMAIL_NOTIFICATION_MODE` ili postaviti na `legacy`
3. **Konfiguracija provajdera** u sc-notifications
4. **Monitoring** — RabbitMQ Management UI, healthcheck endpoint-i
5. **Troubleshooting** — česti problemi
6. **Mailpit** — korišćenje za lokalno testiranje (UI: http://localhost:14081)

### Dijagram konačnog stanja (SC okruženje)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SC okruženje                                        │
│                                                                         │
│  ┌──────────┐  ┌──────────────┐                                        │
│  │  oci-api │  │  oci-monitor │   NotificationFacade                   │
│  │  :8080   │  │  :8081       │   mode = sc-notifications              │
│  └────┬─────┘  └──────┬───────┘                                        │
│       │   HTTP POST    │   HTTP POST   ScNotificationsClient           │
│       └───────┬────────┘              (plain RestClient, Java 17)      │
│               ▼                                                         │
│    ┌────────────────────────────┐                                       │
│    │     sc-notifications      │   Gateway → Dispatcher → Provider     │
│    │     :8091                 │   ├─ smtp_loopia (⭐1)                │
│    │                           │   ├─ api_sendgrid (⭐2)              │
│    │                           │   └─ api_mailtrap (⭐3)              │
│    └──────┬────────────────────┘                                       │
│    ┌──────┼──────────────┐                                              │
│    ▼      ▼              ▼                                              │
│  ┌────┐ ┌──────────┐ ┌───────────┐                                     │
│  │ PG │ │ RabbitMQ │ │  Mailpit  │                                     │
│  └────┘ └──────────┘ └───────────┘                                     │
│                                                                         │
│  ┌──────┐  oci-backend baza (bez promena)                              │
│  │MySQL │                                                               │
│  └──────┘                                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dijagram konačnog stanja (Legacy okruženje)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  Legacy okruženje                                        │
│                                                                         │
│  ┌──────────┐  ┌──────────────┐                                        │
│  │  oci-api │  │  oci-monitor │   NotificationFacade                   │
│  │  :8080   │  │  :8081       │   mode = legacy (default)              │
│  └────┬─────┘  └──────┬───────┘                                        │
│       └───────┬────────┘          MailerService (postojeći kod)        │
│               ▼                                                         │
│    ┌────────────────────────────┐                                       │
│    │   SMTP / SendGrid         │                                       │
│    │   (direktan poziv)        │                                       │
│    └────────────────────────────┘                                       │
│                                                                         │
│  ┌──────┐                                                               │
│  │MySQL │  NEMA SC-NOTIFICATIONS, NEMA PG, NEMA RABBITMQ              │
│  └──────┘  SVE RADI IDENTIČNO KAO PRE REFAKTORA                       │
└─────────────────────────────────────────────────────────────────────────┘
```
