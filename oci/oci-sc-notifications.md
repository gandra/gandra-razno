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
5. [Pristupi integraciji](#5-pristupi-integraciji)
   - 5.1 [Pristup A: SDK mode — čist prelaz (uklanja stari kod)](#51-pristup-a-sdk-mode--čist-prelaz-uklanja-stari-kod)
   - 5.2 [Pristup B: Embedded mode — In-process biblioteka](#52-pristup-b-embedded-mode--in-process-biblioteka)
   - 5.3 [Pristup C: Dual-mode sa Facade/Gateway (⭐ Preporuka)](#53-pristup-c-dual-mode-sa-facadegateway--preporuka)
6. [Uporedna tabela pristupa](#6-uporedna-tabela-pristupa)
7. [Detaljan dizajn preporučenog pristupa (C)](#7-detaljan-dizajn-preporučenog-pristupa-c)
8. [Strategija baze podataka](#8-strategija-baze-podataka)
9. [Docker konfiguracija](#9-docker-konfiguracija)
10. [Lokalno razvojno okruženje](#10-lokalno-razvojno-okruženje)
11. [Dev/Cloud okruženje](#11-devcloud-okruženje)
12. [Plan implementacije](#12-plan-implementacije)
13. [Obrazloženje preporuke](#13-obrazloženje-preporuke)
14. [Post-implementacija](#14-post-implementacija)

---

## 1. Trenutno stanje

### 1.1 Duplirani email kod

`MailerService` interfejs je identičan u oba modula:

```
oci-api/src/main/java/.../service/email/MailerService.java
oci-monitor/src/main/java/.../service/email/MailerService.java
```

```java
public interface MailerService {
   EmailSendResponseDto sendTextEmail(@Valid SendEmailRequestDto request);
   EmailSendResponseDto sendHtmlEmail(@Valid SendEmailRequestDto request);
}
```

Implementacije su takođe duplirane:

| Klasa | oci-api | oci-monitor | Aktivacija |
|-------|---------|-------------|------------|
| `SmtpMailerService` | ✅ | ✅ | `email.provider=smtp` (default, `matchIfMissing=true`) |
| `SendGridMailerService` | ✅ | ✅ | `email.provider=sendgrid` (`matchIfMissing=false`) |
| `EmailConfig` | ✅ | ✅ | `JavaMailSender` bean konfiguracija |

### 1.2 Korisnici email servisa

**oci-api (3 poziva):**

| Klasa | Email | Format | Primaoci |
|-------|-------|--------|----------|
| `UserRegistrationService` | Potvrda registracije | Text | Korisnik |
| `UserRegistrationService` | Ponovo pošalji token | HTML/Text | Korisnik |
| `UsersService` | Reset lozinke | Text | Korisnik |

**oci-monitor (6 poziva):**

| Klasa | Email | Format | Primaoci |
|-------|-------|--------|----------|
| `BudgetNotificationService` | Prekoračenje budžeta | HTML | Višestruki pretplatnici |
| `BudgetCompartmentService` | Prekoračenje po kompartmentima | HTML | Višestruki primaoci |
| `SubscriptionNotificationService` | Limiti pretplate | HTML/Text | SC pretplatnici |
| `CommitmentNotificationService` | Limiti obaveza | Text | SC pretplatnici |
| `CostReportsService` | Greška cost reporta | HTML | Support email |
| `MetricsNotificationEventListener` | Metrička notifikacija | Text | Organizacioni email |

### 1.3 Trenutna infrastruktura

```
docker-compose-local.yml:      MySQL (samo)
docker-compose-cloud-dev.yml:  web(nginx) + ui + api + monitor + db(MySQL)
```

Nema RabbitMQ, nema sc-notifications, nema PostgreSQL.

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
│  │  EmailConfig (bean)   │       │  EmailConfig (bean)       │   │
│  │                       │       │                           │   │
│  │  Pozivi: 3            │       │  Pozivi: 6                │   │
│  └──────────┬────────────┘       └──────────┬────────────────┘   │
│             │                               │                    │
│             └───────────┬───────────────────┘                    │
│                         ▼                                        │
│              ┌─────────────────────┐                             │
│              │   SMTP / SendGrid   │                             │
│              │   (direktan poziv)  │                             │
│              └─────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

**Poznati problemi:**
- Dupliran kod (2x interfejs, 2x SMTP impl, 2x SendGrid impl, 2x config)
- Nema fallback/failover — ako SMTP padne, email se gubi
- Nema retry mehanizma
- Nema delivery tracking
- Nema DLQ za neuspele pošiljke
- Vezanost za 2 provajdera (SMTP + SendGrid), dodavanje novog zahteva kod u oba modula

---

## 2. Ciljevi refaktora

1. **Uvesti sc-notifications kao novi kanal** — dodati mogućnost slanja notifikacija putem sc-notifications REST API-ja, uz zadržavanje postojećeg email sistema
2. **Kontrola putem konfiguracije** — koji email sistem se koristi (legacy SMTP/SendGrid ili sc-notifications) određuje se isključivo konfiguracijom (`application.properties` / environment varijable), **bez ikakve promene koda** između okruženja
3. **Podrazumevano ponašanje = legacy** — ako se ne promeni nijedna konfiguracija, sistem radi identično kao i do sada (SMTP/SendGrid)
4. **Jedan codebase, više produkcija** — isti build artifact (JAR) se deployuje na sva okruženja. Razlika je samo u konfiguraciji.
5. **Dobiti failover/retry/DLQ** — na okruženjima koja koriste sc-notifications, automatski se dobijaju ove mogućnosti
6. **Delivery tracking** — ACK mehanizam za potvrdu isporuke (opcionalno, samo na sc-notifications okruženjima)
7. **Proširivost** — novi kanali (SMS, webhook, websocket) dostupni na okruženjima sa sc-notifications, bez izmena koda

> **Ključno:** Stari email kod (`MailerService`, `SmtpMailerService`, `SendGridMailerService`, `EmailConfig`) **ostaje u codebase-u**. Razlog: aplikacija je deplojovana na više produkcija. Samo na nekim okruženjima ćemo aktivirati nove notifikacije. Drugi klijenti i dalje koriste stari sistem, i eventualni patching/bugfix treba da bude moguć na istom codebase-u.

---

## 3. Ključno pravilo: Non-destructive deployment

### Princip

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ISTI BUILD ARTIFACT (JAR)  ───deploy───►  Okruženje X         │
│                              ───deploy───►  Okruženje Y         │
│                              ───deploy───►  Okruženje Z         │
│                                                                 │
│   Okruženje X:  email.notification.mode = legacy    ← default   │
│   Okruženje Y:  email.notification.mode = legacy    ← default   │
│   Okruženje Z:  email.notification.mode = sc-notifications ← ✨ │
│                                                                 │
│   X i Y rade identično kao pre refaktora.                       │
│   Z koristi nove notifikacije putem REST API-ja.                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Garancija kompatibilnosti

| Scenario | Očekivano ponašanje |
|----------|---------------------|
| Deploy bez promene env vars | ✅ Radi identično kao pre refaktora — SMTP/SendGrid |
| Deploy sa `email.notification.mode=legacy` | ✅ Eksplicitno legacy — isto kao bez promene |
| Deploy sa `email.notification.mode=sc-notifications` | ✅ Koristi sc-notifications REST API |
| Deploy sa `email.notification.mode=sc-notifications`, ali sc-notifications je nedostupan | ⚠️ Greška pri slanju — loguje error, ne pada aplikacija |
| Rollback na stari deploy (pre refaktora) | ✅ Bezbedan — stari kod ne zavisi od novih klasa |

### Mehanizam

```java
// Podrazumevana vrednost je UVEK "legacy"
@Value("${email.notification.mode:legacy}")
private String notificationMode;
```

- Ako property `email.notification.mode` **ne postoji** u konfiguraciji → koristi se `legacy`
- Ako property **postoji** sa vrednošću `legacy` → koristi se legacy
- Ako property **postoji** sa vrednošću `sc-notifications` → koristi se sc-notifications REST API
- Stare SMTP/SendGrid konfiguracije (`email.provider`, `SMTP_*`, `SENDGRID_*`) **ostaju netaknute** i funkcionalne

### Conditional Bean Loading

```java
// Stari beans — učitavaju se UVEK (matchIfMissing=true obezbeđuje backward compat.)
@ConditionalOnProperty(prefix = "email", name = "provider", havingValue = "smtp", matchIfMissing = true)
public class SmtpMailerService implements MailerService { ... }

// Novi beans — učitavaju se SAMO kad postoji notification.client.base-url
@ConditionalOnProperty("notification.client.base-url")
public class NotificationApiClient { ... }  // iz sc-notifications-client auto-config
```

Na okruženjima bez `notification.client.base-url` property-ja, `NotificationApiClient` bean **uopšte ne postoji** u Spring kontekstu — nema mogućnosti greške.

---

## 4. Infrastrukturni preduslovi

### 4.1 Dockerfile za sc-notifications

sc-notifications **nema Dockerfile**. Potrebno ga je kreirati za okruženja koja će koristiti nove notifikacije:

```dockerfile
FROM eclipse-temurin:25-jre-alpine
WORKDIR /app
COPY target/sc-notifications-*.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
```

> **Napomena:** sc-notifications koristi Java 25. Docker image mora koristiti JRE 25+.

### 4.2 Potrebni servisi (samo za okruženja sa sc-notifications)

| Servis | Image | Portovi (local) | Napomena |
|--------|-------|-----------------|----------|
| sc-notifications | custom build | 8091:8081 | REST API za slanje |
| PostgreSQL 17.6 | postgres:17.6-alpine | 5432:5432 | sc-notifications baza |
| RabbitMQ 4.1.4 | rabbitmq:4.1.4-management-alpine | 5672, 15672 | Message broker |
| Mailpit | ghcr.io/axllent/mailpit:latest | 13081:1025, 14081:8025 | Lokalno testiranje email-a |

> **Napomena:** Okruženja koja koriste `email.notification.mode=legacy` **ne trebaju** ništa od navedenog. Infrastruktura ostaje nepromenjena.

---

## 5. Pristupi integraciji

### 5.1 Pristup A: SDK mode — čist prelaz (uklanja stari kod)

**Opis:** Potpuni prelaz na sc-notifications. Stari email kod (`MailerService`, `SmtpMailerService`, `SendGridMailerService`) se **uklanja** iz codebase-a. Svi pozivi idu isključivo kroz `NotificationApiClient`.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          oci-backend                                │
│                                                                     │
│  ┌──────────────────────┐      ┌──────────────────────────┐        │
│  │      oci-api          │      │      oci-monitor          │        │
│  │                       │      │                           │        │
│  │  NotificationApiClient│      │  NotificationApiClient    │        │
│  │  (iz sc-notif-client) │      │  (iz sc-notif-client)     │        │
│  └──────────┬────────────┘      └──────────┬────────────────┘        │
│             │  REST (HTTP)                 │  REST (HTTP)            │
│             └──────────┬───────────────────┘                        │
│                        ▼                                            │
│          ┌──────────────────────────┐                               │
│          │   sc-notifications      │                               │
│          │   Gateway → Dispatcher  │                               │
│          │   → Channel → Provider  │                               │
│          │   → ACK (RabbitMQ)      │                               │
│          └──────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

**Prednosti:**

| # | Prednost |
|---|----------|
| 1 | Čist codebase — nema dualnog koda |
| 2 | Failover, retry, DLQ ugrađeni |
| 3 | Referentna impl. postoji (`sc-notifications-test-api`) |
| 4 | Podržava sve kanale (email, SMS, webhook, websocket) |

**Mane:**

| # | Mana | Ozbiljnost |
|---|------|:----------:|
| 1 | **Uklanja stari email kod** — ne može se koristiti na okruženjima bez sc-notifications | ❌ Kritično |
| 2 | Sva okruženja moraju imati sc-notifications infrastrukturu | ❌ Kritično |
| 3 | Big-bang migracija — sve ili ništa | ❌ Kritično |
| 4 | Ne može se patchovati stari email tok na istom codebase-u | ❌ Kritično |
| 5 | Dodatna infrastruktura (sc-notifications + PostgreSQL + RabbitMQ) | ⚠️ Srednje |

**Ograničenja:**
- **Krši non-destructive deployment princip** — deploy bez promene konfiguracije bi pukao na okruženjima bez sc-notifications
- Nije primenljiv dok se SVI klijenti/produkcije ne migriraju na sc-notifications

> **Zaključak:** Ovaj pristup je cilj **dugoročno**, ali **ne sada**. Može se primeniti tek kada sve produkcije pređu na sc-notifications i kad se validira stabilnost sistema.

---

### 5.2 Pristup B: Embedded mode — In-process biblioteka

**Opis:** sc-notifications se koristi kao embedded biblioteka direktno u oci-backend JVM procesu.

```
┌────────────────────────────────────────────────────────────────┐
│                      oci-backend JVM                           │
│                                                                │
│  ┌──────────────────────┐     ┌──────────────────────────┐    │
│  │      oci-api          │     │      oci-monitor          │    │
│  │                       │     │                           │    │
│  │  NotificationGateway  │     │  NotificationGateway      │    │
│  │  (iz sc-notifications)│     │  (iz sc-notifications)    │    │
│  └──────────┬────────────┘     └──────────┬────────────────┘    │
│             │                             │                     │
│             └──────────┬──────────────────┘                     │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  sc-notifications (embedded)                             │   │
│  │  Gateway → Dispatcher → Channel → Provider              │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

**Prednosti:**

| # | Prednost |
|---|----------|
| 1 | Nema mrežne latencije — sve u istom procesu |
| 2 | Jednostavnija infrastruktura — bez dodatnog kontejnera za sc-notifications |
| 3 | Nema single point of failure za mrežni poziv |

**Mane:**

| # | Mana | Ozbiljnost |
|---|------|:----------:|
| 1 | **Java 25 nekompatibilnost** — sc-notifications zahteva Java 25, oci-backend koristi Java 17 | ❌ Blokirano |
| 2 | Veći memory footprint po JVM instanci | ⚠️ Srednje |
| 3 | Teže nezavisno ažuriranje sc-notifications | ⚠️ Srednje |
| 4 | Duplirani provider beans u oba modula | ⚠️ Srednje |
| 5 | Zahteva PostgreSQL za sc-notifications entity-je | ⚠️ Srednje |
| 6 | Gubi se mogućnost nezavisnog skaliranja | ⚠️ Srednje |

**Ograničenja:**
- **BLOKIRANO:** Java 17 → Java 25 nadogradnja je preduslov. Ovo je zaseban, visokorizičan projekat.
- Potrebna reorganizacija sc-notifications da bi funkcionisao kao biblioteka (`standalone=false`)
- Potencijalni konflikti beans-a između oci-backend i sc-notifications konfiguracija

> **Zaključak:** Tehnički nemoguć dok se oci-backend ne nadogradi na Java 25. Ne razmatrati.

---

### 5.3 Pristup C: Dual-mode sa Facade/Gateway (⭐ Preporuka)

**Opis:** `NotificationFacade` u `oci-library` podržava oba moda — legacy (direktni SMTP/SendGrid) i novi (sc-notifications SDK). Mod se bira **isključivo putem konfiguracije**. Podrazumevano: legacy.

**Referentna implementacija:** `sc-notifications-test-api` (za SDK deo).

```
┌────────────────────────────────────────────────────────────────────────┐
│                           oci-backend                                  │
│                                                                        │
│  ┌─────────────────────┐        ┌────────────────────────────┐        │
│  │      oci-api         │        │      oci-monitor            │        │
│  │                      │        │                             │        │
│  │  UserRegistration    │        │  BudgetNotificationSvc      │        │
│  │  Service             │        │  BudgetCompartmentSvc       │        │
│  │  UsersService        │        │  SubscriptionNotifSvc       │        │
│  │  TesterController    │        │  CommitmentNotifSvc         │        │
│  │                      │        │  CostReportsService         │        │
│  │                      │        │  MetricsNotifEventListener  │        │
│  └──────────┬───────────┘        └──────────────┬──────────────┘        │
│             │                                   │                       │
│             └──────────────┬────────────────────┘                       │
│                            ▼                                            │
│           ┌───────────────────────────────────┐                        │
│           │     NotificationFacade            │  (oci-library)         │
│           │     @Value("${email.notification  │                        │
│           │      .mode:legacy}")              │                        │
│           └───────────┬───────────────────────┘                        │
│                       │                                                 │
│          ┌────────────┴─────────────┐                                   │
│          │ email.notification.mode  │                                   │
│          │                          │                                   │
│  ┌───────┴───────┐       ┌─────────┴──────────┐                        │
│  │ mode=legacy   │       │ mode=sc-notif.     │                        │
│  │ (DEFAULT)     │       │                     │                        │
│  │               │       │ NotificationApi     │                        │
│  │ MailerService │       │ Client (SDK)        │                        │
│  │ ├─SmtpSvc     │       │ (auto-configured    │                        │
│  │ └─SendGridSvc │       │  by base-url prop.) │                        │
│  └───────┬───────┘       └─────────┬───────────┘                        │
│          │                         │                                    │
│          ▼                         ▼                                    │
│  ┌──────────────┐       ┌──────────────────────┐                       │
│  │ SMTP/SendGrid│       │  sc-notifications    │                       │
│  │ (direktno)   │       │  REST API (:8091)    │                       │
│  │              │       │  Gateway→Dispatcher  │                       │
│  │  ✉ email     │       │  →Channel→Provider   │                       │
│  │              │       │  →ACK (RabbitMQ)     │                       │
│  └──────────────┘       └──────────────────────┘                       │
└────────────────────────────────────────────────────────────────────────┘
```

### Kako radi konfiguracija po okruženjima

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                  ISTI CODEBASE → ISTI JAR ARTIFACT                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Produkcija klijenta A (bez promena u env vars):                            │
│  ┌────────────────────────────────────────────┐                             │
│  │ email.provider=smtp          ← postojeće   │                             │
│  │ SMTP_HOST=mail.klijent-a.com ← postojeće   │                             │
│  │ (email.notification.mode     ← ne postoji) │ → default "legacy" → SMTP  │
│  └────────────────────────────────────────────┘                             │
│                                                                              │
│  Produkcija klijenta B (bez promena u env vars):                            │
│  ┌────────────────────────────────────────────┐                             │
│  │ email.provider=sendgrid      ← postojeće   │                             │
│  │ SENDGRID_API_KEY=sg-xxx      ← postojeće   │                             │
│  │ (email.notification.mode     ← ne postoji) │ → default "legacy" → SGrid │
│  └────────────────────────────────────────────┘                             │
│                                                                              │
│  Dev/Test okruženje (nove env vars):                                        │
│  ┌────────────────────────────────────────────────────────────┐             │
│  │ email.notification.mode=sc-notifications    ← NOVO         │             │
│  │ notification.client.base-url=http://sc-notifications:8081  │             │
│  │ notification.client.ack.enabled=true        ← opcionalno   │             │
│  │ spring.rabbitmq.host=sc-notifications-rabbitmq             │             │
│  │                                                             │             │
│  │ email.provider=smtp              ← ostaje (ignorisano)     │             │
│  │ SMTP_HOST=...                    ← ostaje (ignorisano)     │             │
│  └────────────────────────────────────────────────────────────┘             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Koraci implementacije

| # | Task | Lokacija |
|---|------|----------|
| 1 | Dodati `sc-notifications-client` zavisnost (optional) | `oci-library/pom.xml` |
| 2 | Dodati `spring-boot-starter-amqp` zavisnost (optional) | `oci-library/pom.xml` |
| 3 | Kreirati `NotificationFacade` | `oci-library/.../service/notification/` |
| 4 | Kreirati DTO adapter (mapiranje) | `oci-library/.../mapper/` |
| 5 | Refaktorisati svih 9 poziva da koriste `NotificationFacade` umesto `MailerService` | oci-api (3), oci-monitor (6) |
| 6 | Konfigurisati properties za local profil | `application-local.properties` |
| 7 | Opciono: implementirati `NotificationDeliveryReceiptHandler` | oci-library ili oci-api/monitor |

> **Važno:** Korak 5 ne uklanja `MailerService` i implementacije — oni ostaju jer ih `NotificationFacade` koristi u legacy modu.

**Prednosti:**

| # | Prednost |
|---|----------|
| 1 | **Non-destructive deployment** — ako se ne promeni nijedna konfiguracija, ponašanje je identično |
| 2 | **Jedan codebase, više strategija** — isti JAR radi na svim okruženjima |
| 3 | **Postepeni rollout** — po jedno okruženje prelazi na sc-notifications, validira se, pa sledeće |
| 4 | **Stari kod ostaje za patching** — bugfix na legacy email toku ne zahteva poseban branch |
| 5 | **Bezbedan rollback** — promena jednog property-ja vraća na legacy mod |
| 6 | Failover, retry, DLQ — dostupni na sc-notifications okruženjima |
| 7 | Referentna impl. postoji (`sc-notifications-test-api`) za SDK deo |

**Mane:**

| # | Mana | Ozbiljnost |
|---|------|:----------:|
| 1 | Oba email koda žive u codebase-u | ⚠️ Prihvatljivo — svesna odluka |
| 2 | `NotificationFacade` je dodatni sloj apstrakcije | ⚠️ Nisko — jednostavan if/else |
| 3 | Dual konfiguracija (stari SMTP + novi notification.client) | ⚠️ Nisko — različiti property-ji, nema konflikta |
| 4 | Testiranje oba puta | ⚠️ Srednje — ali samo jednom po okruženju |

**Ograničenja:**
- `sc-notifications-client` zahteva Spring Boot 3.2+ (oci-backend koristi 3.2.1 — kompatibilno)
- Na okruženjima sa sc-notifications, RabbitMQ mora biti dostupan za ACK (ali ACK je opcionalan)
- Mapiranje DTO objekata zahteva adapter sloj u `oci-library`

---

## 6. Uporedna tabela pristupa

| Kriterijum | A: SDK čist | B: Embedded | C: Dual-mode (⭐) |
|------------|:-----------:|:-----------:|:------------------:|
| **Non-destructive deploy** | ❌ Puca bez SC infra | ❌ Puca bez Java 25 | ✅ Default = legacy |
| **Jedan codebase, više prod.** | ❌ Svi moraju na SC | ❌ Svi moraju na J25 | ✅ Config per env |
| **Java kompatibilnost** | ✅ Java 17 OK | ❌ Zahteva Java 25 | ✅ Java 17 OK |
| **Stari kod za patching** | ❌ Uklonjen | ❌ Blokirano | ✅ Ostaje funkcionalan |
| **Failover/Retry/DLQ** | ✅ Ugrađen | ✅ Ugrađen | ✅ U SC modu |
| **Delivery tracking (ACK)** | ✅ RabbitMQ ACK | ⚠️ In-process event | ✅ U SC modu |
| **Loose coupling** | ✅ Razdvojeno | ❌ Isti classpath | ✅ Razdvojeno |
| **Nezavisno skaliranje** | ✅ | ❌ | ✅ U SC modu |
| **Rizik migracije** | ❌ Visok (big-bang) | ❌ Visok (Java 25) | ✅ Nizak (postepen) |
| **Složenost implementacije** | ⚠️ Srednja | ❌ Visoka | ⚠️ Srednja |
| **Dugoročno održavanje** | ✅ Minimalno | ⚠️ Srednje | ⚠️ Dva puta, ali stabilan |
| **Referentna impl.** | ✅ sc-notif-test-api | ❌ Ne postoji | ✅ sc-notif-test-api |
| **Multi-channel support** | ✅ Svi kanali | ✅ Svi kanali | ✅ U SC modu |
| **Rollback mogućnost** | ❌ Zahteva redeploy | ❌ Zahteva redeploy | ✅ Promena 1 property-ja |

---

## 7. Detaljan dizajn preporučenog pristupa (C)

### 7.1 NotificationFacade — centralna klasa

Smešta se u `oci-library` da bude dostupna i u `oci-api` i u `oci-monitor`:

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationFacade {

   private final MailerService mailerService;                     // uvek postoji
   private final Optional<NotificationApiClient> scNotifClient;  // postoji samo kad je base-url set

   @Value("${email.notification.mode:legacy}")
   private String notificationMode;

   /**
    * Šalje text email.
    * U "legacy" modu: koristi MailerService (SMTP/SendGrid).
    * U "sc-notifications" modu: koristi sc-notifications REST API.
    */
   public EmailSendResponseDto sendTextEmail(SendEmailRequestDto request) {
      if (isScNotificationsMode()) {
         return sendViaScNotifications(request, false);
      }
      return mailerService.sendTextEmail(request);
   }

   /**
    * Šalje HTML email.
    */
   public EmailSendResponseDto sendHtmlEmail(SendEmailRequestDto request) {
      if (isScNotificationsMode()) {
         return sendViaScNotifications(request, true);
      }
      return mailerService.sendHtmlEmail(request);
   }

   private boolean isScNotificationsMode() {
      return "sc-notifications".equals(notificationMode);
   }

   private EmailSendResponseDto sendViaScNotifications(SendEmailRequestDto request, boolean html) {
      NotificationApiClient client = scNotifClient.orElseThrow(() ->
         new IllegalStateException("notification.client.base-url is not configured " +
            "but email.notification.mode=sc-notifications"));

      SendEmailRequest scRequest = SendEmailRequest.builder()
         .to(List.of(request.getTo()))
         .subject(request.getSubject())
         .body(request.getBody())
         .html(html)
         .fromEmail(request.getFrom())
         .build();

      NotificationResponse response = client.sendEmail(scRequest);
      log.info("SC-Notification sent | uuid={} | status={}",
         response.getNotificationUuid(), response.getStatus());

      return EmailSendResponseDto.builder()
         .emailSentTo(request.getTo())
         .emailProvider("sc-notifications")
         .error(response.getStatus() == NotificationResponseStatus.REJECTED)
         .build();
   }
}
```

### 7.2 Dijagram toka odlučivanja

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
     │ (ili ne postoji│      │                    │
     │  — default)    │      │                    │
     └───────┬────────┘      └────────┬───────────┘
             │                        │
             ▼                        ▼
  ┌────────────────────┐   ┌────────────────────────┐
  │ mailerService      │   │ NotificationApiClient  │
  │ .sendTextEmail()   │   │ .sendEmail()           │
  │                    │   │                         │
  │ (SmtpMailerSvc ili │   │ REST POST ka            │
  │  SendGridMailerSvc │   │ sc-notifications:8091   │
  │  — zavisi od       │   │                         │
  │  email.provider)   │   │ → Gateway → Dispatcher  │
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

### 7.3 Konfiguracija po profilima

#### application.properties (zajedničko — BEZ PROMENA)
```properties
# Postojeće — ostaje kako jeste
email.provider=smtp
support.email=${NO_REPLY_EMAIL}
spring.sendgrid.api-key=${SENDGRID_API_KEY}
app.smtp.mail.host=${SMTP_HOST}
app.smtp.mail.port=${SMTP_PORT}
# ... ostali SMTP properties
```

#### application-local.properties (NOVO — dodajemo)
```properties
# --- SC Notifications integration ---
email.notification.mode=sc-notifications
notification.client.base-url=http://localhost:8091
notification.client.connect-timeout-ms=5000
notification.client.read-timeout-ms=10000

# ACK (opcionalno)
notification.client.ack.enabled=true
notification.client.ack.queue=oci-api.notification-ack
notification.client.ack.exchange=notifications.ack.fanout
spring.rabbitmq.host=localhost
spring.rabbitmq.port=5672
spring.rabbitmq.username=notifier
spring.rabbitmq.password=topsecret
```

#### application-dev.properties (za dev okruženje sa SC)
```properties
# --- SC Notifications integration ---
email.notification.mode=sc-notifications
notification.client.base-url=http://sc-notifications:8081
notification.client.ack.enabled=true
notification.client.ack.queue=oci-api.notification-ack
spring.rabbitmq.host=sc-notifications-rabbitmq
spring.rabbitmq.port=5672
spring.rabbitmq.username=notifier
spring.rabbitmq.password=topsecret
```

#### application-prod.properties (postojeće produkcije — BEZ PROMENA)
```properties
# email.notification.mode NE POSTOJI → default "legacy"
# Sve radi identično kao pre refaktora
```

### 7.4 Dependency konfiguracija

```xml
<!-- oci-library/pom.xml — DODATI -->
<dependency>
    <groupId>com.sistemisolutions.core</groupId>
    <artifactId>sc-notifications-client</artifactId>
    <optional>true</optional>
</dependency>

<!-- Samo ako treba ACK -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-amqp</artifactId>
    <optional>true</optional>
</dependency>
```

> **`<optional>true</optional>`** — oci-api i oci-monitor nasleđuju zavisnost, ali je ona opciona. Na runtime-u, ako `notification.client.base-url` ne postoji, `NotificationApiClient` bean se ne kreira i nikakav error ne nastaje.

### 7.5 Refaktor poziva u servisima

**Pre (trenutno stanje):**
```java
@RequiredArgsConstructor
public class BudgetNotificationService {
    private final MailerService mailerService;

    public void notify(...) {
        mailerService.sendHtmlEmail(
            new SendEmailRequestDto(from, to, subject, htmlBody));
    }
}
```

**Posle (refaktorisano):**
```java
@RequiredArgsConstructor
public class BudgetNotificationService {
    private final NotificationFacade notificationFacade;  // zamena

    public void notify(...) {
        notificationFacade.sendHtmlEmail(                 // isti potpis
            new SendEmailRequestDto(from, to, subject, htmlBody));
    }
}
```

> Promena je minimalna — samo zamena `mailerService` → `notificationFacade`. Potpis metode ostaje isti. Nema strukturne promene u servisnom kodu.

---

## 8. Strategija baze podataka

sc-notifications koristi PostgreSQL 17.6, oci-backend koristi MySQL 8.0.

### 8.1 Opcija DB-A: Zasebna PostgreSQL instanca (⭐ Preporuka)

```
┌─────────────┐     ┌──────────────────┐
│  MySQL 8.0  │     │ PostgreSQL 17.6  │
│  (ociapp)   │     │ (sc_notifications)│
│             │     │                   │
│  oci-api    │     │  sc-notifications │
│  oci-monitor│     │                   │
└─────────────┘     └──────────────────┘
   postojeće             novo (samo na
   bez promena           SC okruženjima)
```

| Aspekt | Ocena |
|--------|-------|
| Izolacija | ✅ Potpuna — pad jedne baze ne utiče na drugu |
| Backup/Restore | ✅ Nezavisni — različiti RPO/RTO |
| Performance | ✅ Nema contention između servisa |
| Složenost | ⚠️ Dodatni kontejner, dodatan monitoring |
| Resursi | ⚠️ ~256MB RAM ekstra za PostgreSQL |
| Non-destructive | ✅ Legacy okruženja ne trebaju PostgreSQL |

### 8.2 Opcija DB-B: Deljeni PostgreSQL, zasebna baza

```
┌────────────────────────────┐
│      PostgreSQL 17.6       │
│                            │
│  ┌──────┐  ┌────────────┐ │
│  │ociapp│  │sc_notificat│ │
│  │ (DB) │  │ions (DB)   │ │
│  └──────┘  └────────────┘ │
└────────────────────────────┘
```

| Aspekt | Ocena |
|--------|-------|
| Izolacija | ⚠️ Logička (zasebne baze), fizički deljeni resursi |
| Resursi | ✅ Jedna instanca |
| Složenost | ❌ Zahteva MySQL→PG migraciju oci-backend-a |
| Rizik | ❌ Visok — MySQL→PG migracija je invazivna |
| Non-destructive | ❌ Menja bazu za sve okruženja |

### 8.3 Opcija DB-C: Deljena baza, zasebne šeme

| Aspekt | Ocena |
|--------|-------|
| Izolacija | ❌ Minimalna |
| Rizik | ❌ Najviši |
| Preporuka | ❌ Ne preporučuje se |

### Preporuka za bazu

**DB-A: Zasebna PostgreSQL instanca.** oci-backend ostaje na MySQL (bez ikakvih promena), sc-notifications dobija svoj PostgreSQL. Postoji samo na okruženjima koja koriste sc-notifications mod.

---

## 9. Docker konfiguracija

### 9.1 Izmene u `docker-compose-local.yml`

Dodati sc-notifications stack pored postojećeg MySQL-a:

```yaml
services:
  # --- Postojeći (BEZ PROMENA) ---
  db:
    image: "mysql/mysql-server:latest"
    command: --default-authentication-plugin=caching_sha2_password
    container_name: db
    restart: always
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=myrootsecret
      - MYSQL_DATABASE=ociapp
      - MYSQL_USER=ocidbuser
      - MYSQL_PASSWORD=mysecret
    volumes:
      - oci_db_volume:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  # --- Novi: sc-notifications stack ---
  # Opciono — može se komentarisati ako se ne koristi
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
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider",
             "http://localhost:8081/actuator/health"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 30s

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

### 9.2 Izmene u `docker-compose-cloud-dev.yml`

Dodati sc-notifications servise **samo za dev okruženja koja koriste sc-notifications**:

```yaml
  # --- sc-notifications (dodati samo na SC okruženjima) ---
  sc-notifications:
    image: "${SC_NOTIFICATIONS_IMAGE}"
    container_name: sc-notifications
    entrypoint: ["java", "-Dspring.profiles.active=dev", "-jar", "sc-notifications.jar"]
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://sc-notifications-db:5432/sc_notifications
      - SPRING_DATASOURCE_USERNAME=${SC_NOTIF_DB_USERNAME}
      - SPRING_DATASOURCE_PASSWORD=${SC_NOTIF_DB_PASSWORD}
      - SPRING_RABBITMQ_HOST=sc-notifications-rabbitmq
      - SPRING_RABBITMQ_PORT=5672
      - SPRING_RABBITMQ_USERNAME=${SC_NOTIF_RABBITMQ_USER}
      - SPRING_RABBITMQ_PASSWORD=${SC_NOTIF_RABBITMQ_PASS}
    ports:
      - "8091:8081"
    depends_on:
      sc-notifications-db:
        condition: service_healthy
      sc-notifications-rabbitmq:
        condition: service_healthy
    restart: unless-stopped

  sc-notifications-db:
    image: "postgres:17.6-alpine"
    container_name: sc-notifications-db
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=${SC_NOTIF_DB_USERNAME}
      - POSTGRES_PASSWORD=${SC_NOTIF_DB_PASSWORD}
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
    restart: unless-stopped
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=${SC_NOTIF_RABBITMQ_USER}
      - RABBITMQ_DEFAULT_PASS=${SC_NOTIF_RABBITMQ_PASS}
    volumes:
      - sc_notifications_rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Dodatni environment variables za `api` i `monitor` kontejnere (**samo na SC okruženjima**):

```yaml
api:
  environment:
    # ... sve postojeće env vars OSTAJU ...
    # Dodati samo na okruženjima sa sc-notifications:
    - "EMAIL_NOTIFICATION_MODE=sc-notifications"
    - "NOTIFICATION_CLIENT_BASE_URL=http://sc-notifications:8081"
    - "NOTIFICATION_CLIENT_ACK_ENABLED=true"
    - "NOTIFICATION_CLIENT_ACK_QUEUE=oci-api.notification-ack"
    - "SPRING_RABBITMQ_HOST=sc-notifications-rabbitmq"
    - "SPRING_RABBITMQ_PORT=5672"
    - "SPRING_RABBITMQ_USERNAME=${SC_NOTIF_RABBITMQ_USER}"
    - "SPRING_RABBITMQ_PASSWORD=${SC_NOTIF_RABBITMQ_PASS}"
  depends_on:
    - db
    - sc-notifications  # dodati samo na SC okruženjima

monitor:
  environment:
    # ... sve postojeće env vars OSTAJU ...
    - "EMAIL_NOTIFICATION_MODE=sc-notifications"
    - "NOTIFICATION_CLIENT_BASE_URL=http://sc-notifications:8081"
    - "NOTIFICATION_CLIENT_ACK_ENABLED=true"
    - "NOTIFICATION_CLIENT_ACK_QUEUE=oci-monitor.notification-ack"
    - "SPRING_RABBITMQ_HOST=sc-notifications-rabbitmq"
    - "SPRING_RABBITMQ_PORT=5672"
    - "SPRING_RABBITMQ_USERNAME=${SC_NOTIF_RABBITMQ_USER}"
    - "SPRING_RABBITMQ_PASSWORD=${SC_NOTIF_RABBITMQ_PASS}"
  depends_on:
    - db
    - api
    - sc-notifications  # dodati samo na SC okruženjima
```

> **Napomena:** Na produkcijama klijenata A i B — `docker-compose-cloud-dev.yml` (ili njihov prod compose) **ne sadrži** sc-notifications servise, niti `EMAIL_NOTIFICATION_MODE` env var. Deploy JAR-a radi identično kao pre.

---

## 10. Lokalno razvojno okruženje

### 10.1 Opcija Local-A: sc-notifications iz IntelliJ (⭐ Preporuka za razvoj)

Za svakodnevni razvoj, pokrenuti sc-notifications direktno iz IntelliJ IDEA:

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

**IntelliJ konfiguracija za sc-notifications:**
- Profile: `local`
- Port: `8091` (podesi u `application-local.properties` ili via `-Dserver.port=8091`)
- Before launch: `mvn clean install` na `sc-commons` projektu

### 10.2 Opcija Local-B: Sve iz Docker-a

Za testiranje production-like okruženja:

```bash
# 1. Build sc-notifications image
cd sc-notifications
mvn clean install -Plocal -DskipTests
docker build -t sc-notifications:local .

# 2. Start oci-backend stack + sc-notifications
cd ../oci-backend
docker compose -f docker-compose-local.yml up -d
```

### 10.3 Opcija Local-C: Bez sc-notifications (legacy mod)

Za testiranje da legacy mod i dalje radi:

```bash
# Samo MySQL
cd oci-backend
docker compose -f docker-compose-local.yml up -d db
```

Ukloniti ili komentarisati `email.notification.mode` iz `application-local.properties`:
```properties
# email.notification.mode=sc-notifications  ← zakomentarisano
```

→ Sistem automatski koristi legacy SMTP/SendGrid.

---

## 11. Dev/Cloud okruženje

### Okruženje sa sc-notifications

```
┌─ Docker Host (dev server) ─────────────────────────────────────────┐
│                                                                     │
│  ┌────────┐  ┌─────┐  ┌──────┐  ┌──────────┐  ┌──────┐           │
│  │  nginx  │  │  ui │  │  api │  │  monitor  │  │  db  │ (postoj.)│
│  │  :80    │  │:3000│  │:8080 │  │  :8081   │  │:3306 │           │
│  └────────┘  └─────┘  └──┬───┘  └────┬─────┘  └──────┘           │
│                           │           │                             │
│                           │   email.notification.mode               │
│                           │   = sc-notifications                    │
│                           ▼           ▼                             │
│                    ┌──────────────────────────┐                     │
│                    │    sc-notifications      │  (novi)             │
│                    │    :8091                 │                     │
│                    └──────────┬───────────────┘                     │
│                               │                                     │
│              ┌────────────────┼────────────────┐                    │
│              ▼                ▼                 ▼                    │
│        ┌──────────┐  ┌──────────────┐  ┌────────────┐              │
│        │PostgreSQL│  │  RabbitMQ    │  │  Loopia..   │  (novi)     │
│        │  :5432   │  │ :5672/:15672 │  │  (SMTP)     │             │
│        └──────────┘  └──────────────┘  └────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### Okruženje BEZ sc-notifications (legacy — produkcije klijenata)

```
┌─ Docker Host (produkcija klijenta) ────────────────────────────────┐
│                                                                     │
│  ┌────────┐  ┌─────┐  ┌──────┐  ┌──────────┐  ┌──────┐           │
│  │  nginx  │  │  ui │  │  api │  │  monitor  │  │  db  │           │
│  │  :80    │  │:3000│  │:8080 │  │  :8081   │  │:3306 │           │
│  └────────┘  └─────┘  └──┬───┘  └────┬─────┘  └──────┘           │
│                           │           │                             │
│                           │   email.notification.mode               │
│                           │   = legacy (default)                    │
│                           ▼           ▼                             │
│                    ┌──────────────────────────┐                     │
│                    │    SMTP / SendGrid       │                     │
│                    │    (direktan poziv)      │                     │
│                    └──────────────────────────┘                     │
│                                                                     │
│               NEMA SC-NOTIFICATIONS, NEMA PG, NEMA RABBITMQ       │
│               SVE RADI IDENTIČNO KAO PRE REFAKTORA                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 12. Plan implementacije

### Faza 1: Infrastruktura (1-2 dana)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 1 | Kreirati Dockerfile za sc-notifications | `sc-notifications/Dockerfile` |
| 2 | Dodati sc-notifications stack u `docker-compose-local.yml` | `oci-backend/docker-compose-local.yml` |
| 3 | Validirati: `docker compose up -d` i proveriti health svih servisa | — |

### Faza 2: Dependency i konfiguracija (1 dan)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 4 | Dodati `sc-notifications-client` (optional) u `oci-library/pom.xml` | `oci-library/pom.xml` |
| 5 | Dodati `spring-boot-starter-amqp` (optional) u `oci-library/pom.xml` | `oci-library/pom.xml` |
| 6 | Konfigurisati `email.notification.mode` + `notification.client.*` | `oci-api/.../application-local.properties` |
| 7 | Konfigurisati isto za monitor | `oci-monitor/.../application-local.properties` |

### Faza 3: Kod — NotificationFacade (2-3 dana)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 8 | Kreirati `NotificationFacade` | `oci-library/.../service/notification/` |
| 9 | Kreirati DTO adapter (mapiranje OCI ↔ sc-notifications-client) | `oci-library/.../mapper/` |
| 10 | Refaktorisati `UserRegistrationService` → koristi `NotificationFacade` | `oci-api` |
| 11 | Refaktorisati `UsersService` → koristi `NotificationFacade` | `oci-api` |
| 12 | Refaktorisati `BudgetNotificationService` → koristi `NotificationFacade` | `oci-monitor` |
| 13 | Refaktorisati `BudgetCompartmentService` → koristi `NotificationFacade` | `oci-monitor` |
| 14 | Refaktorisati `SubscriptionNotificationService` → koristi `NotificationFacade` | `oci-monitor` |
| 15 | Refaktorisati `CommitmentNotificationService` → koristi `NotificationFacade` | `oci-monitor` |
| 16 | Refaktorisati `CostReportsService` → koristi `NotificationFacade` | `oci-monitor` |
| 17 | Refaktorisati `MetricsNotificationEventListener` → koristi `NotificationFacade` | `oci-monitor` |

> **Napomena:** `MailerService`, `SmtpMailerService`, `SendGridMailerService`, `EmailConfig` se **NE BRIŠU**.
> `NotificationFacade` ih koristi kada je mod `legacy`.

### Faza 4: Opciono — ACK handler (0.5 dana)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 18 | Implementirati `NotificationDeliveryReceiptHandler` | `oci-library/.../handler/` |

### Faza 5: Testiranje (1-2 dana)

| # | Task | Opis |
|---|------|------|
| 19 | Testirati **sc-notifications mod** lokalno | `email.notification.mode=sc-notifications`, Mailpit UI |
| 20 | Testirati **legacy mod** lokalno | `email.notification.mode=legacy` ili zakomentarisano |
| 21 | Proveriti failover u SC modu | Ugasiti primarni provajder, verifikovati fallback |
| 22 | Proveriti ACK (ako implementiran) | Logovi potvrde isporuke |
| 23 | Proveriti da **stari tests** prolaze bez promena | `mvn test` |

### Faza 6: Deploy na dev (1 dan)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 24 | Ažurirati `docker-compose-cloud-dev.yml` | `oci-backend/docker-compose-cloud-dev.yml` |
| 25 | Ažurirati `.env` na dev serveru | dev server — dodati SC env vars |
| 26 | Deploy isti JAR na dev sa SC konfiguracijom | — |
| 27 | Verifikovati da dev radi sa sc-notifications | — |

### Faza 7: Verifikacija produkcija (0.5 dana)

| # | Task | Opis |
|---|------|------|
| 28 | Deploy isti JAR na produkciju klijenta A | **BEZ PROMENA** u env vars |
| 29 | Verifikovati da produkcija radi identično | Legacy SMTP/SendGrid |

---

## 13. Obrazloženje preporuke

**Preporučeni pristup: C (Dual-mode sa Facade/Gateway) ⭐**

### Zašto Dual-mode?

1. **Non-destructive deployment** — Ovo je **apsolutni prioritet**. Aplikacija je deplojovana na više produkcija kod različitih klijenata. Deploy novog JAR-a bez promene env vars mora rezultovati identičnim ponašanjem kao pre refaktora. Samo Pristup C to garantuje jer je default mod `legacy`.

2. **Jedan codebase, više strategija** — Isti Git repository, isti `mvn clean install`, isti JAR artifact — ali svako okruženje bira svoj email mod putem konfiguracije. Nema potrebe za različitim branchevima ili build profilima.

3. **Stari kod ostaje za patching** — Ako se pojavi bug u legacy SMTP slanju na produkciji klijenta koji koristi stari sistem, fix se radi na istom codebase-u. Ne treba poseban branch, fork, ili cherry-pick.

4. **Postepeni rollout bez rizika** — Prelaz se radi po jednom okruženju:
   - Prvo `local` → testiramo oba moda
   - Zatim `dev` → validiramo sa pravim email provajderima
   - Na kraju selektivno na produkcijama koje želimo migrirati
   - Rollback = promena jednog property-ja

5. **Minimalna invazivnost** — Refaktor se svodi na:
   - 1 nova klasa (`NotificationFacade`)
   - 1 nova zavisnost (`sc-notifications-client`, optional)
   - 9 izmena u servisima (zamena `mailerService` → `notificationFacade`)
   - 0 uklonjenih klasa

### Zašto ne Pristup A (čist SDK)?

Pristup A uklanja stari email kod — to znači da **sva** okruženja moraju imati sc-notifications infrastrukturu. To je neprihvatljivo za produkcije klijenata koje koriste stari sistem i ne planiraju migraciju u bliskoj budućnosti.

> **Pristup A ostaje dugoročni cilj.** Kada sve produkcije pređu na sc-notifications, Pristup C se prirodno transformiše u Pristup A brisanjem legacy koda i `NotificationFacade` if/else grananja.

### Zašto ne Pristup B (Embedded)?

Java 17 → Java 25 nekompatibilnost. Nemoguć bez nadogradnje čitavog oci-backend stack-a.

### Zašto zasebna PostgreSQL instanca (DB-A)?

oci-backend koristi MySQL. Dva zasebna DB engine-a su potpuno prihvatljiv pattern (polyglot persistence). Nema rizika od cross-kontaminacije, nezavisni lifecycle-ovi. Legacy okruženja ne trebaju PostgreSQL uopšte.

---

## 14. Post-implementacija

### Manual za operatere

Kreirati `docs/manuals/sc-notifications-integration.md` sa sledećim sadržajem:

1. **Preduslovi** — potrebni Docker image-i, volume-i, mrežni zahtevi (samo za SC okruženja)
2. **Aktivacija SC moda** — koji env vars dodati, koji compose fajl ažurirati
3. **Deaktivacija / Rollback** — ukloniti `EMAIL_NOTIFICATION_MODE` ili postaviti na `legacy`
4. **Konfiguracija provajdera** — kako dodati/promeniti email provajder u sc-notifications
5. **Monitoring** — RabbitMQ Management UI (port 15672), healthcheck endpoint-i
6. **Troubleshooting** — česti problemi (sc-notifications ne startuje, email se ne šalje, ACK ne stiže)
7. **Mailpit** — korišćenje za lokalno testiranje (UI: http://localhost:14081)
8. **DLQ upravljanje** — pregled i replay neuspelih poruka
9. **Dijagram env var matrice** — koje env vars za koje okruženje

### Dijagram konačnog stanja (SC okruženje)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Konačno stanje (SC okruženje)                           │
│                                                                             │
│  ┌──────────┐  ┌──────────────┐                                            │
│  │  oci-api │  │  oci-monitor │                                            │
│  │  :8080   │  │  :8081       │                                            │
│  │          │  │              │                                            │
│  │  Notif   │  │  Notif       │  NotificationFacade (oci-library)          │
│  │  Facade  │  │  Facade      │  mode = sc-notifications                   │
│  └────┬─────┘  └──────┬───────┘                                            │
│       │   REST         │   REST     sc-notifications-client (SDK)          │
│       └───────┬────────┘                                                    │
│               ▼                                                             │
│    ┌────────────────────────────┐                                           │
│    │     sc-notifications      │                                           │
│    │     :8091                 │                                           │
│    │                           │                                           │
│    │  Gateway → Dispatcher     │                                           │
│    │  → EmailChannel           │                                           │
│    │    ├─ smtp_loopia  (⭐1)  │                                           │
│    │    ├─ smtp_mailpit (dev)  │                                           │
│    │    ├─ api_sendgrid (⭐2)  │                                           │
│    │    └─ api_mailtrap (⭐3)  │                                           │
│    │  → ACK Publisher          │                                           │
│    └──────┬────────────────────┘                                           │
│           │                                                                 │
│    ┌──────┼──────────────┐                                                  │
│    ▼      ▼              ▼                                                  │
│  ┌────┐ ┌──────────┐ ┌───────────┐                                         │
│  │ PG │ │ RabbitMQ │ │  Mailpit  │                                         │
│  │5432│ │5672/15672│ │13081/14081│                                         │
│  └────┘ └──────────┘ └───────────┘                                         │
│                                                                             │
│  ┌──────┐                                                                   │
│  │MySQL │  oci-backend baza (bez promena)                                  │
│  │ 3306 │                                                                   │
│  └──────┘                                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dijagram konačnog stanja (Legacy okruženje)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  Konačno stanje (Legacy okruženje)                          │
│                                                                             │
│  ┌──────────┐  ┌──────────────┐                                            │
│  │  oci-api │  │  oci-monitor │                                            │
│  │  :8080   │  │  :8081       │                                            │
│  │          │  │              │                                            │
│  │  Notif   │  │  Notif       │  NotificationFacade (oci-library)          │
│  │  Facade  │  │  Facade      │  mode = legacy (default)                   │
│  └────┬─────┘  └──────┬───────┘                                            │
│       │                │                                                    │
│       └───────┬────────┘                                                    │
│               ▼                                                             │
│    ┌────────────────────────────┐                                           │
│    │   SMTP / SendGrid         │   MailerService (postojeći kod)           │
│    │   (direktan poziv)        │   SmtpMailerSvc / SendGridMailerSvc       │
│    └────────────────────────────┘                                           │
│                                                                             │
│  ┌──────┐                                                                   │
│  │MySQL │  oci-backend baza (bez promena)                                  │
│  │ 3306 │                                                                   │
│  └──────┘                                                                   │
│                                                                             │
│  NEMA SC-NOTIFICATIONS, NEMA POSTGRESQL, NEMA RABBITMQ                     │
│  SVE RADI IDENTIČNO KAO PRE REFAKTORA                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Evolucioni put

```
  Danas                  Faza 1                    Dugoročno
  ──────                 ──────                    ──────────

  Legacy only     →   Dual-mode (C)         →   SDK only (A)
                      (preporuka)               (kad svi pređu)

  MailerService   →   NotificationFacade    →   NotificationFacade
  (direktno)          ├─ legacy (default)       └─ sc-notifications (jedini)
                      └─ sc-notifications
                                                 Brisanje:
                                                 - MailerService
                                                 - SmtpMailerService
                                                 - SendGridMailerService
                                                 - EmailConfig
                                                 - legacy if/else grana
```
