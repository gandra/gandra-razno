# Refaktor oci-backend: Integracija sc-notifications

> **Datum:** 2026-03-10
> **Status:** PLAN / TODO
> **Autor:** Dragan Mijatović

---

## Sadržaj

1. [Trenutno stanje](#1-trenutno-stanje)
2. [Ciljevi refaktora](#2-ciljevi-refaktora)
3. [Infrastrukturni preduslovi](#3-infrastrukturni-preduslovi)
4. [Pristupi integraciji](#4-pristupi-integraciji)
   - 4.1 [Pristup A: SDK mode — REST API (⭐ Preporuka)](#41-pristup-a-sdk-mode--rest-api--preporuka)
   - 4.2 [Pristup B: Embedded mode — In-process biblioteka](#42-pristup-b-embedded-mode--in-process-biblioteka)
   - 4.3 [Pristup C: Dual-mode sa Facade/Gateway](#43-pristup-c-dual-mode-sa-facadegateway)
5. [Uporedna tabela pristupa](#5-uporedna-tabela-pristupa)
6. [Strategija baze podataka](#6-strategija-baze-podataka)
7. [Docker konfiguracija](#7-docker-konfiguracija)
8. [Lokalno razvojno okruženje](#8-lokalno-razvojno-okruženje)
9. [Dev/Cloud okruženje](#9-devcloud-okruženje)
10. [Plan implementacije](#10-plan-implementacije)
11. [Obrazloženje preporuke](#11-obrazloženje-preporuke)
12. [Post-implementacija](#12-post-implementacija)

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
| `SmtpMailerService` | ✅ | ✅ | `email.provider=smtp` (default, matchIfMissing=true) |
| `SendGridMailerService` | ✅ | ✅ | `email.provider=sendgrid` (matchIfMissing=false) |
| `EmailConfig` | ✅ | ✅ | JavaMailSender bean konfiguracija |

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

**Problemi:**
- Dupliran kod (2x interfejs, 2x SMTP impl, 2x SendGrid impl, 2x config)
- Nema fallback/failover — ako SMTP padne, email se gubi
- Nema retry mehanizma
- Nema delivery tracking
- Nema DLQ za neuspele pošiljke
- Vezanost za 2 provajdera (SMTP + SendGrid), dodavanje novog zahteva kod u oba modula

---

## 2. Ciljevi refaktora

1. **Eliminisati duplikaciju** — ukloniti lokalni email kod iz oba modula
2. **Centralizovati slanje** — sve notifikacije prolaze kroz sc-notifications
3. **Dobiti failover** — automatski prelaz na sledeći provajder pri grešci
4. **Dobiti retry + DLQ** — RabbitMQ obezbeđuje pouzdanu isporuku
5. **Delivery tracking** — ACK mehanizam za potvrdu isporuke
6. **Proširivost** — novi kanali (SMS, webhook, websocket) bez izmena u oci-backend
7. **Minimalan uticaj** — refaktor ne sme pokvariti postojeću funkcionalnost

---

## 3. Infrastrukturni preduslovi

### 3.1 Dockerfile za sc-notifications

sc-notifications **nema Dockerfile**. Potrebno ga je kreirati:

```dockerfile
FROM eclipse-temurin:25-jre-alpine
WORKDIR /app
COPY target/sc-notifications-*.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
```

> **Napomena:** sc-notifications koristi Java 25. Docker image mora koristiti JRE 25+.

### 3.2 Potrebni servisi za oci-backend integraciju

| Servis | Image | Portovi (local) | Napomena |
|--------|-------|-----------------|----------|
| sc-notifications | custom build | 8091:8081 | REST API za slanje |
| PostgreSQL 17.6 | postgres:17.6-alpine | 5432:5432 | sc-notifications baza |
| RabbitMQ 4.1.4 | rabbitmq:4.1.4-management-alpine | 5672, 15672 | Message broker |
| Mailpit | ghcr.io/axllent/mailpit:latest | 13081:1025, 14081:8025 | Lokalno testiranje email-a |

---

## 4. Pristupi integraciji

### 4.1 Pristup A: SDK mode — REST API (⭐ Preporuka)

**Opis:** oci-backend koristi `sc-notifications-client` biblioteku za slanje notifikacija putem REST API-ja ka sc-notifications servisu.

**Referentna implementacija:** `sc-notifications-test-api` projekat.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          oci-backend                                    │
│                                                                         │
│  ┌──────────────────────┐        ┌──────────────────────────┐          │
│  │      oci-api          │        │      oci-monitor          │          │
│  │                       │        │                           │          │
│  │  NotificationApiClient│        │  NotificationApiClient    │          │
│  │  (iz sc-notif-client) │        │  (iz sc-notif-client)     │          │
│  └──────────┬────────────┘        └──────────┬────────────────┘          │
│             │  REST (HTTP)                   │  REST (HTTP)              │
│             └───────────┬────────────────────┘                          │
│                         ▼                                               │
│           ┌────────────────────────┐                                    │
│           │   sc-notifications     │ (Docker kontejner ili IntelliJ)    │
│           │   port: 8091 (local)   │                                    │
│           │                        │                                    │
│           │  Gateway → Dispatcher  │                                    │
│           │  → Channel → Provider  │                                    │
│           │  → ACK (RabbitMQ)      │                                    │
│           └────────┬───────────────┘                                    │
│                    │                                                    │
│         ┌──────────┼──────────────────┐                                 │
│         ▼          ▼                  ▼                                  │
│    ┌────────┐ ┌──────────┐  ┌──────────────┐                           │
│    │ Mailpit│ │  Loopia  │  │   SendGrid   │  ...                      │
│    │ (local)│ │  SMTP    │  │    API       │                           │
│    └────────┘ └──────────┘  └──────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
                    │
              ┌─────┴─────┐
              │  RabbitMQ  │ ──── ACK ──→ oci-backend (opcionalno)
              └───────────┘
```

**Koraci implementacije:**

1. Dodati `sc-notifications-client` zavisnost u `oci-api/pom.xml` i `oci-monitor/pom.xml`
2. Konfigurisati property-je:
   ```properties
   # application-local.properties
   notification.client.base-url=http://localhost:8091
   notification.client.connect-timeout-ms=5000
   notification.client.read-timeout-ms=10000

   # Opciono: ACK listener
   notification.client.ack.enabled=true
   notification.client.ack.queue=oci-api.notification-ack
   notification.client.ack.exchange=notifications.ack.fanout
   ```
3. Kreirati `NotificationFacadeService` koji zamenjuje `MailerService`:
   ```java
   @Service
   @RequiredArgsConstructor
   public class NotificationFacadeService {
       private final NotificationApiClient notificationClient;

       public NotificationResponse sendTextEmail(SendEmailRequest request) {
           return notificationClient.sendEmail(request);
       }

       public NotificationResponse sendHtmlEmail(SendEmailRequest request) {
           return notificationClient.sendEmail(
               request.toBuilder().html(true).build()
           );
       }
   }
   ```
4. Zameniti sve pozive `mailerService.sendTextEmail(...)` / `sendHtmlEmail(...)` sa `notificationFacadeService.sendTextEmail(...)`
5. Mapirati `SendEmailRequestDto` (OCI) → `SendEmailRequest` (sc-notifications-client)
6. Ukloniti stari email kod (`MailerService`, `SmtpMailerService`, `SendGridMailerService`, `EmailConfig`)
7. Opciono: implementirati `NotificationDeliveryReceiptHandler` za ACK

**Prednosti:**
- Čisto razdvajanje servisa (loose coupling)
- sc-notifications se može nezavisno skalirati, restartovati, ažurirati
- Automatski failover između provajdera (SMTP → SendGrid → Mailtrap → ...)
- Retry + DLQ ugrađeni
- Delivery tracking putem ACK
- Referentna implementacija postoji (`sc-notifications-test-api`)
- Podržava sve kanale (email, SMS, webhook, websocket) bez izmena

**Mane:**
- Dodatna infrastruktura (sc-notifications + PostgreSQL + RabbitMQ kontejneri)
- Mrežna latencija (HTTP poziv umesto direktnog slanja)
- Single point of failure — ako sc-notifications padne, email se ne šalje
- Java 25 zahtev za sc-notifications (oci-backend je Java 17)

**Ograničenja:**
- `sc-notifications-client` zahteva Spring Boot 3.2+ (oci-backend koristi 3.2.1 — kompatibilno)
- RabbitMQ mora biti dostupan za ACK, ali ACK je opcionalan
- Mapiranje DTO objekata zahteva adapter sloj

---

### 4.2 Pristup B: Embedded mode — In-process biblioteka

**Opis:** sc-notifications se koristi kao embedded biblioteka direktno u oci-backend JVM procesu (bez zasebnog servisa).

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
│  └──────────┬──────────────────────────────────────────────┘   │
│             │                                                   │
│    ┌────────┼──────────┐                                        │
│    ▼        ▼          ▼                                        │
│ Mailpit  Loopia    SendGrid  ...                                │
└────────────────────────────────────────────────────────────────┘
```

**Prednosti:**
- Nema mrežne latencije — sve u istom procesu
- Jednostavnija infrastruktura — bez dodatnog kontejnera za sc-notifications
- Nema single point of failure za mrežni poziv

**Mane:**
- **Java 25 nekompatibilnost** — sc-notifications zahteva Java 25, oci-backend koristi Java 17. Nije moguće bez nadogradnje oci-backend-a na Java 25
- Veći memory footprint po JVM instanci
- sc-notifications code u oci-backend classpath-u — teže nezavisno ažuriranje
- Duplirani provider beans — oba modula (oci-api i oci-monitor) bi instancirali sopstvene provajdere
- Zahteva PostgreSQL za sc-notifications entity-je (ntf_db_config tabele)
- Gubi se mogućnost nezavisnog skaliranja

**Ograničenja:**
- **BLOKIRANO:** Java 17 → Java 25 nadogradnja je preduslov
- Potrebna reorganizacija sc-notifications da bi funkcionisao kao biblioteka (standalone=false mode)
- Potencijalni konflikti beans-a između oci-backend i sc-notifications konfiguracija

---

### 4.3 Pristup C: Dual-mode sa Facade/Gateway

**Opis:** Intermedijarni pristup gde `NotificationFacade` podržava oba moda — stari (direktni SMTP/SendGrid) i novi (sc-notifications SDK). Mod se bira putem konfiguracije.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          oci-backend                                │
│                                                                     │
│  ┌──────────────────────┐      ┌──────────────────────────┐        │
│  │      oci-api          │      │      oci-monitor          │        │
│  │                       │      │                           │        │
│  │  poziv servisa ───────┼──────┼──→  NotificationFacade    │        │
│  └───────────────────────┘      └──────────┬────────────────┘        │
│                                            │                         │
│                              ┌─────────────┴─────────────┐           │
│                              │   email.notification.mode  │           │
│                              │                            │           │
│                    ┌─────────┴──────┐         ┌──────────┴────────┐  │
│                    │  mode=legacy   │         │  mode=sc-notif    │  │
│                    │                │         │                    │  │
│                    │ SmtpMailerSvc  │         │ NotificationApi   │  │
│                    │ SendGridSvc    │         │ Client (SDK)      │  │
│                    └────────┬───────┘         └────────┬──────────┘  │
│                             │                          │             │
│                             ▼                          ▼             │
│                    ┌─────────────┐          ┌──────────────────┐     │
│                    │ SMTP/SGrid  │          │ sc-notifications │     │
│                    │ (direktno)  │          │ (REST API)       │     │
│                    └─────────────┘          └──────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

**Implementacija facade-a:**

```java
@Service
@RequiredArgsConstructor
public class NotificationFacade {
    private final Optional<MailerService> legacyMailer;
    private final Optional<NotificationApiClient> notificationClient;

    @Value("${email.notification.mode:legacy}")
    private String mode;

    public void sendTextEmail(String to, String subject, String body) {
        if ("sc-notifications".equals(mode)) {
            notificationClient.orElseThrow().sendEmail(
                SendEmailRequest.builder()
                    .to(to).subject(subject).body(body).html(false)
                    .build()
            );
        } else {
            legacyMailer.orElseThrow().sendTextEmail(
                new SendEmailRequestDto(null, to, subject, body)
            );
        }
    }
}
```

**Prednosti:**
- Bezbedan postepeni prelaz — fallback na stari sistem
- Može se testirati po okruženju: `local` → sc-notifications, `prod` → legacy dok se ne validira
- Nema big-bang migracije

**Mane:**
- Održavate oba koda dugoročno (ili do potpune migracije)
- Kompleksniji kod — grananje po modu
- Dual konfiguracija (stari SMTP properties + novi notification.client properties)
- Facade sloj je privremeni kod koji se na kraju briše
- Testiranje oba puta zahteva više effort-a

**Ograničenja:**
- Smisleno samo kao prelazni korak ka punom SDK mode-u (Pristup A)
- Ne rešava fundamentalno dupliranje — samo ga skriva iza facade-a

---

## 5. Uporedna tabela pristupa

| Kriterijum | A: SDK (⭐) | B: Embedded | C: Dual-mode |
|------------|:-----------:|:-----------:|:------------:|
| **Java kompatibilnost** | ✅ Java 17 OK | ❌ Zahteva Java 25 | ✅ Java 17 OK |
| **Infrastrukturna složenost** | ⚠️ +3 kontejnera | ✅ Samo PostgreSQL | ⚠️ +3 kontejnera |
| **Mrežna latencija** | ⚠️ HTTP poziv (~5ms) | ✅ In-process | ⚠️ HTTP poziv |
| **Loose coupling** | ✅ Potpuno razdvojeno | ❌ Isti classpath | ✅ Razdvojeno |
| **Failover/Retry** | ✅ Ugrađen | ✅ Ugrađen | ⚠️ Samo u SC modu |
| **Delivery tracking (ACK)** | ✅ RabbitMQ ACK | ⚠️ In-process event | ⚠️ Samo u SC modu |
| **Nezavisno skaliranje** | ✅ | ❌ | ✅ |
| **Složenost implementacije** | ⚠️ Srednja | ❌ Visoka (Java 25+) | ⚠️ Srednja-visoka |
| **Rizik migracije** | ⚠️ Srednji | ❌ Visok | ✅ Nizak (postepen) |
| **Dugoročno održavanje** | ✅ Minimalno | ⚠️ Srednje | ❌ Dupli kod privremeno |
| **Referentna impl.** | ✅ sc-notif-test-api | ❌ Ne postoji | ❌ Ne postoji |
| **Multi-channel support** | ✅ Email+SMS+WH+WS | ✅ Email+SMS+WH+WS | ⚠️ Samo u SC modu |

---

## 6. Strategija baze podataka

sc-notifications koristi PostgreSQL 17.6, oci-backend koristi MySQL 8.0.

### 6.1 Opcija DB-A: Zasebna PostgreSQL instanca (⭐ Preporuka)

```
┌─────────────┐     ┌──────────────────┐
│  MySQL 8.0  │     │ PostgreSQL 17.6  │
│  (ociapp)   │     │ (sc_notifications)│
│             │     │                   │
│  oci-api    │     │  sc-notifications │
│  oci-monitor│     │                   │
└─────────────┘     └──────────────────┘
```

| Aspekt | Ocena |
|--------|-------|
| Izolacija | ✅ Potpuna — pad jedne baze ne utiče na drugu |
| Backup/Restore | ✅ Nezavisni — različiti RPO/RTO |
| Performance | ✅ Nema contentions između servisa |
| Složenost | ⚠️ Dodatni kontejner, dodatan monitoring |
| Resursi | ⚠️ ~256MB RAM ekstra za PostgreSQL |

### 6.2 Opcija DB-B: Deljeni PostgreSQL, zasebna baza

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

> **Napomena:** Ovo zahteva migraciju oci-backend sa MySQL na PostgreSQL, što je zaseban, značajan projekat.

| Aspekt | Ocena |
|--------|-------|
| Izolacija | ⚠️ Logička (zasebne baze), fizički deljeni resursi |
| Resursi | ✅ Jedna instanca |
| Složenost | ❌ Zahteva MySQL→PG migraciju oci-backend-a |
| Rizik | ❌ Visok — MySQL→PG migracija je invazivna |

### 6.3 Opcija DB-C: Deljena baza, zasebne šeme

> **Napomena:** Ista ograničenja kao DB-B plus potencijalni name collision-i.

| Aspekt | Ocena |
|--------|-------|
| Izolacija | ❌ Minimalna |
| Rizik | ❌ Najviši |
| Preporuka | ❌ Ne preporučuje se |

### Preporuka za bazu

**DB-A: Zasebna PostgreSQL instanca.** oci-backend ostaje na MySQL, sc-notifications dobija svoj PostgreSQL. Nema rizika od cross-kontaminacije, nezavisni lifecycle-ovi, minimalan dodatni trošak resursa.

---

## 7. Docker konfiguracija

### 7.1 Izmene u `docker-compose-local.yml`

Dodati sc-notifications stack pored postojećeg MySQL-a:

```yaml
services:
  # --- Postojeći ---
  db:
    image: "mysql/mysql-server:latest"
    # ... (bez izmena)

  # --- Novi: sc-notifications stack ---
  sc-notifications:
    build:
      context: ../sc-notifications  # ili image iz registry-ja
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
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8081/actuator/health"]
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

### 7.2 Izmene u `docker-compose-cloud-dev.yml`

Dodati iste servise (sc-notifications, PostgreSQL, RabbitMQ) sa dev konfiguracijama. Mailpit nije potreban u dev okruženju — koristi se pravi SMTP provajder.

Dodatni environment variables za `api` i `monitor` kontejnere:

```yaml
api:
  environment:
    # ... postojeći ...
    - "NOTIFICATION_SERVICE_BASE_URL=http://sc-notifications:8081"
    - "NOTIFICATION_ACK_ENABLED=true"
    - "NOTIFICATION_ACK_QUEUE=oci-api.notification-ack"
    - "SPRING_RABBITMQ_HOST=sc-notifications-rabbitmq"
    - "SPRING_RABBITMQ_PORT=5672"
    - "SPRING_RABBITMQ_USERNAME=notifier"
    - "SPRING_RABBITMQ_PASSWORD=topsecret"
  depends_on:
    - db
    - sc-notifications

monitor:
  environment:
    # ... postojeći ...
    - "NOTIFICATION_SERVICE_BASE_URL=http://sc-notifications:8081"
    - "NOTIFICATION_ACK_ENABLED=true"
    - "NOTIFICATION_ACK_QUEUE=oci-monitor.notification-ack"
    - "SPRING_RABBITMQ_HOST=sc-notifications-rabbitmq"
    - "SPRING_RABBITMQ_PORT=5672"
    - "SPRING_RABBITMQ_USERNAME=notifier"
    - "SPRING_RABBITMQ_PASSWORD=topsecret"
  depends_on:
    - db
    - api
    - sc-notifications
```

---

## 8. Lokalno razvojno okruženje

### 8.1 Opcija Local-A: sc-notifications iz IntelliJ (⭐ Preporuka za razvoj)

Za svakodnevni razvoj, pokrenuti sc-notifications direktno iz IntelliJ IDEA (ne Docker):

```
┌─ IntelliJ IDEA ────────────────────────────────────┐
│                                                     │
│  Run: oci-api (port 8080)                          │
│  Run: oci-monitor (port 8081)                      │
│  Run: sc-notifications (port 8091)  ← dodati       │
│                                                     │
└─────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─ Docker (docker-compose) ──────────────────────────┐
│                                                     │
│  MySQL (3306) — oci-backend                        │
│  PostgreSQL (5432) — sc-notifications              │
│  RabbitMQ (5672 / 15672) — sc-notifications        │
│  Mailpit (13081 SMTP / 14081 UI) — email testing   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**IntelliJ konfiguracija za sc-notifications:**
- Profile: `local`
- Port: `8091` (podesi u `application-local.properties` ili via `-Dserver.port=8091`)
- Before launch: `mvn clean install` na `sc-commons` projektu

**oci-backend properties (local profil):**
```properties
# application-local.properties (oci-api i oci-monitor)
notification.client.base-url=http://localhost:8091
notification.client.ack.enabled=true
notification.client.ack.queue=oci-api.notification-ack
notification.client.ack.exchange=notifications.ack.fanout
spring.rabbitmq.host=localhost
spring.rabbitmq.port=5672
spring.rabbitmq.username=notifier
spring.rabbitmq.password=topsecret
```

### 8.2 Opcija Local-B: Sve iz Docker-a

Za testiranje production-like okruženja, pokrenuti sve iz Docker-a:

```bash
# 1. Build sc-notifications image
cd sc-notifications
mvn clean install -Plocal -DskipTests
docker build -t sc-notifications:local .

# 2. Start oci-backend stack + sc-notifications
cd ../oci-backend
docker compose -f docker-compose-local.yml up -d
```

---

## 9. Dev/Cloud okruženje

U dev/cloud okruženju sve je dockerizovano:

```
┌─ Docker Host (dev server) ─────────────────────────────────────────┐
│                                                                     │
│  ┌────────┐  ┌─────┐  ┌──────┐  ┌──────────┐  ┌──────┐           │
│  │  nginx  │  │  ui │  │  api │  │  monitor  │  │  db  │  (exist) │
│  │  :80    │  │:3000│  │:8080 │  │  :8081   │  │:3306 │           │
│  └────────┘  └─────┘  └──┬───┘  └────┬─────┘  └──────┘           │
│                           │           │                             │
│                    REST   │           │   REST                      │
│                           ▼           ▼                             │
│                    ┌──────────────────────────┐                     │
│                    │    sc-notifications      │  (novi)             │
│                    │    :8091                 │                     │
│                    └──────────┬───────────────┘                     │
│                               │                                     │
│              ┌────────────────┼────────────────┐                    │
│              ▼                ▼                 ▼                    │
│        ┌──────────┐  ┌──────────────┐  ┌────────────┐              │
│        │PostgreSQL│  │  RabbitMQ    │  │  (provajd.) │  (novi)     │
│        │  :5432   │  │ :5672/:15672 │  │  Loopia..   │             │
│        └──────────┘  └──────────────┘  └────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

**Napomena:** U dev okruženju Mailpit nije potreban — koriste se pravi SMTP provajderi (Loopia, SendGrid, itd.).

---

## 10. Plan implementacije

### Faza 1: Infrastruktura (1-2 dana)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 1 | Kreirati Dockerfile za sc-notifications | `sc-notifications/Dockerfile` |
| 2 | Dodati sc-notifications stack u `docker-compose-local.yml` | `oci-backend/docker-compose-local.yml` |
| 3 | Kreirati `local.env` za oci-backend sa SC portovima | `oci-backend/local.env` |
| 4 | Validirati: `docker compose up -d` i proveriti health svih servisa | — |

### Faza 2: Dependency i konfiguracija (1 dan)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 5 | Dodati `sc-notifications-client` u `oci-library/pom.xml` | `oci-library/pom.xml` |
| 6 | Dodati `spring-boot-starter-amqp` u `oci-library/pom.xml` | `oci-library/pom.xml` |
| 7 | Konfigurisati notification.client.* properties | `oci-api/src/main/resources/application-local.properties` |
| 8 | Konfigurisati notification.client.* properties | `oci-monitor/src/main/resources/application-local.properties` |
| 9 | Konfigurisati RabbitMQ properties | oba application-local.properties |

### Faza 3: Kod — Facade sloj (2-3 dana)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 10 | Kreirati `NotificationFacadeService` u oci-library | `oci-library/src/main/java/.../service/notification/` |
| 11 | Kreirati DTO adapter: OCI → sc-notifications-client | `oci-library/src/main/java/.../mapper/` |
| 12 | Refaktorisati `UserRegistrationService` — zaменити MailerService | `oci-api` |
| 13 | Refaktorisati `UsersService` — zaменити MailerService | `oci-api` |
| 14 | Refaktorisati `BudgetNotificationService` | `oci-monitor` |
| 15 | Refaktorisati `BudgetCompartmentService` | `oci-monitor` |
| 16 | Refaktorisati `SubscriptionNotificationService` | `oci-monitor` |
| 17 | Refaktorisati `CommitmentNotificationService` | `oci-monitor` |
| 18 | Refaktorisati `CostReportsService` | `oci-monitor` |
| 19 | Refaktorisati `MetricsNotificationEventListener` | `oci-monitor` |

### Faza 4: Čišćenje (1 dan)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 20 | Ukloniti `MailerService` interfejs iz oba modula | oci-api, oci-monitor |
| 21 | Ukloniti `SmtpMailerService` iz oba modula | oci-api, oci-monitor |
| 22 | Ukloniti `SendGridMailerService` iz oba modula | oci-api, oci-monitor |
| 23 | Ukloniti `EmailConfig` iz oba modula | oci-api, oci-monitor |
| 24 | Ukloniti stare email properties (SMTP_*, SENDGRID_*) | oba application.properties |
| 25 | Ukloniti SendGrid zavisnost iz pom.xml | oci-api/pom.xml, oci-monitor/pom.xml |
| 26 | Ukloniti spring-boot-starter-mail zavisnost | oci-api/pom.xml, oci-monitor/pom.xml |

### Faza 5: Testiranje i validacija (1-2 dana)

| # | Task | Opis |
|---|------|------|
| 27 | Lokalno testiranje svakog email toka | Mailpit UI: http://localhost:14081 |
| 28 | Proveriti failover | Ugasiti primarni provajder, verifikovati fallback |
| 29 | Proveriti ACK | Logovi potvrde isporuke u oci-backend konzoli |
| 30 | Dev deployment | Docker compose up na dev serveru |

### Faza 6: Dev/Prod konfiguracija (1 dan)

| # | Task | Fajl/Lokacija |
|---|------|---------------|
| 31 | Ažurirati `docker-compose-cloud-dev.yml` | `oci-backend/docker-compose-cloud-dev.yml` |
| 32 | Konfigurisati dev properties | `application-dev.properties` (oba modula) |
| 33 | Konfigurisati prod properties | `application-prod.properties` (oba modula) |
| 34 | Ažurirati `.env` fajl za dev server | dev server |

---

## 11. Obrazloženje preporuke

**Preporučeni pristup: A (SDK mode — REST API) ⭐**

### Zašto SDK mode?

1. **Java kompatibilnost** — Ovo je jedini pristup koji radi sa trenutnim Java 17 stack-om oci-backend-a. Embedded mode (B) zahteva nadogradnju na Java 25, što je zaseban, visoko-rizičan projekat.

2. **Referentna implementacija postoji** — `sc-notifications-test-api` je funkcionalan primer SDK integracije. Ovo drastično smanjuje rizik i vreme implementacije jer imamo proveren obrazac za copy.

3. **Čista arhitektura** — Potpuno razdvajanje oci-backend-a i sc-notifications na nivou servisa. Svaki servis ima svoj lifecycle, može se nezavisno deployovati, skalirati i ažurirati.

4. **Failover iz kutije** — sc-notifications već ima ugrađen FAILOVER mod sa automatskim prelazom između provajdera (Loopia → Mailtrap → SendGrid → Brevo → ...). Ovo je funkcionalnost koju oci-backend trenutno nema.

5. **Buduća proširivost** — Jednom kada je integracija uspostavljena, dodavanje novih kanala (SMS, webhook, websocket) ne zahteva nikakve izmene u oci-backend kodu. Dovoljno je konfigurisati sc-notifications.

6. **Infrastrukturna cena je prihvatljiva** — Dodajemo 3-4 kontejnera (sc-notifications, PostgreSQL, RabbitMQ, Mailpit), ali dobijamo pouzdaniji i fleksibilniji notification stack. PostgreSQL za sc-notifications troši minimalne resurse (~256MB RAM).

### Zašto ne Dual-mode (C)?

Dual-mode ima smisla samo ako postoji rizik da sc-notifications neće biti stabilan u produkciji. S obzirom na to da se sc-notifications već koristi u drugim projektima i ima razvijenu test infrastrukturu, taj rizik je nizak. Dual-mode uvodi nepotrebnu složenost i odlaže puno uklanjanje starog koda.

**Preporuka:** Koristiti Pristup C samo privremeno ako je potreban postepeni rollout po okruženjima (local → dev → prod), ali sa jasnim planom i datumom za potpuni prelaz na Pristup A.

### Zašto zasebna PostgreSQL instanca (DB-A)?

oci-backend koristi MySQL, sc-notifications koristi PostgreSQL. Migracija oci-backend-a na PostgreSQL bi bila zaseban projekat visokog rizika sa minimalnim benefitom za ovaj refaktor. Dva zasebna DB engine-a su potpuno prihvatljiv pattern u mikroservisnoj arhitekturi (polyglot persistence).

---

## 12. Post-implementacija

### Manual za operatere

Kreirati `docs/manuals/sc-notifications-integration.md` sa sledećim sadržajem:

1. **Preduslovi** — potrebni Docker image-i, volume-i, mrežni zahtevi
2. **Pokretanje** — docker compose komande za svako okruženje
3. **Konfiguracija provajdera** — kako dodati/promeniti email provajder u sc-notifications
4. **Monitoring** — RabbitMQ Management UI (port 15672), healthcheck endpoint-i
5. **Troubleshooting** — česti problemi (sc-notifications ne startuje, email se ne šalje, ACK ne stiže)
6. **Mailpit** — korišćenje za lokalno testiranje (UI: http://localhost:14081)
7. **DLQ upravljanje** — pregled i replay neuspelih poruka

### Dijagram konačnog stanja

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Konačno stanje                                     │
│                                                                             │
│  ┌──────────┐  ┌──────────────┐                                            │
│  │  oci-api │  │  oci-monitor │                                            │
│  │  :8080   │  │  :8081       │                                            │
│  │          │  │              │                                            │
│  │  Notif   │  │  Notif       │   sc-notifications-client                  │
│  │  Facade  │  │  Facade      │   (Maven dependency)                       │
│  └────┬─────┘  └──────┬───────┘                                            │
│       │   REST         │   REST                                             │
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
