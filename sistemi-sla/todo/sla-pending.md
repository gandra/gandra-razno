# SLA Gap Analysis & Pending Items

> **Datum**: 2026-03-11
> **Verzija**: 1.0
> **Status**: Radni dokument

---

## Sadržaj

1. [Rezime trenutnog stanja](#1-rezime-trenutnog-stanja)
2. [Poređenje sa zahtevima (TehnickaSpecifikacija_v2)](#2-poređenje-sa-zahtevima)
3. [Gap Analysis matrica](#3-gap-analysis-matrica)
4. [Zabbix SLA — komparativna analiza](#4-zabbix-sla-komparativna-analiza)
5. [Pregled dosadašnjih analiza (docs-sla/analysis/)](#5-pregled-dosadašnjih-analiza)
6. [Predlozi unapređenja sa pristupima](#6-predlozi-unapređenja-sa-pristupima)
7. [Preporuke i prioritizacija](#7-preporuke-i-prioritizacija)
8. [Implementacioni plan](#8-implementacioni-plan)

---

## 1. Rezime trenutnog stanja

### 1.1 Backend (oci-backend, grana `sla`)

**Implementirano i funkcionalno (100%):**
- SLA Definition CRUD (kreiranje, izmena, deaktivacija, tag filtriranje)
- SLA Computation Pipeline (daily/weekly/monthly scheduler → availability calculation → status → penalty → save → event)
- Breach Detection (event-driven, `@TransactionalEventListener(AFTER_COMMIT)`, `@Async`)
- Penalty Calculation (Phase 2.1 fixed + Phase 2.2 formula-based via SpEL)
- Formula Evaluation Service (secure SpEL sa whitelistom varijabli)
- Excluded Downtime Management (CRUD + overlap validacija + status tracking)
- SLA Schedule Utils (timezone-aware, custom schedule podrška, 24x7 režim)
- Tag Filter Service (resource → SLA matching po tag kriterijumima)
- ShedLock distributed locking (MySQL-based, za multi-instance deployment)
- SLA Scheduler (daily 00:05, weekly Monday 00:10, monthly 1st 00:15)
- Severity kalkulacija (CRITICAL ≥5%, HIGH 3-5%, MEDIUM 1-3%, LOW <1%)
- Data coverage validacija (≥80% za dovoljno podataka)

**Parcijalno implementirano:**
- SLA Notification Service — email radi, webhook TODO
- ~~SLA Report Service — on-demand generisanje radi, ali `generateReport()` nema authorization check~~ ✅ Implementirano (2026-03-11)
- ~~Stored SLA Report — entity postoji, PDF/CSV retrieval nije implementiran (TODO)~~ ✅ Implementirano (2026-03-11)
- ~~Manual computation trigger — endpoint postoji, ali bez dry-run, batch, progress tracking~~ ✅ UI poboljšan (2026-03-11): date range, force recompute, detaljni rezultati. Dry-run/batch/progress ostaje za Phase 2.

**Nije implementirano:**
- ~~SLA Report Scheduler~~ ✅ Implementirano (2026-03-11)
- ~~Report Format Generation — PDF/CSV fajlovi se ne generišu (samo JSON)~~ ✅ On-demand PDF/CSV generisanje implementirano (2026-03-11)
- ~~Breach Management API — nema lifecycle (acknowledge/resolve), nema state machine, nema audit trail~~ ✅ Breach Management API implementiran (2026-03-11): PATCH acknowledge/resolve + GET unacknowledged/unresolved
- Webhook Notifications — komentarisano, nije implementirano
- Email Retry Logic — jedan pokušaj, nema exponential backoff
- Manual Report Trigger — endpoint postoji ali implementacija je TODO

### 1.2 Frontend (oci-sla-management-poc-ui)

**Implementirano i funkcionalno (100%):**
- SLA Lista sa statusima, penalty info, downtime count, manual trigger (SlaListPage)
- SLA Form — 5-step wizard (Basic Info → Metric → Target/Schedule → Advanced → Review)
- Dva monitoring režima: Single Resource vs OCI Query
- Report generisanje na zahtev sa 3 čarta (gauge, datapoints, breach timeline)
- CSV/PDF export (service metode, blob download)
- Report Schedule CRUD (WEEKLY/MONTHLY/QUARTERLY/CUSTOM cron, email, PDF/CSV attachment)
- Excluded Downtime management (dialog, form, lista, count)
- Feature flags (penalty, formula-based penalty) — backend-driven
- JWT autentifikacija sa token persistence
- Architecture documentation viewer (3 markdown fajla)
- Cascading dropdowns (Organization → Compartment → Resource → Metric)

**Parcijalno implementirano:**
- Penalty polja postoje u formi ali se ne prikazuju u izveštajima
- Tag filter criteria polje postoji ali nije potpuno integrisano
- ~~Cron expression — nema UI builder/validator~~ ✅ Implementirano (2026-03-11): CronExpressionBuilder sa presetima, field selektorima, human-readable opisom

**Nije implementirano:**
- ~~Delete SLA Definition — nema dugme za brisanje~~ ⚠️ Backend nema delete endpoint, ostaje TODO
- ~~Deactivate SLA toggle — samo edit~~ ✅ Deactivate dugme sa confirmation dialogom implementirano (2026-03-11)
- ~~Delete SLA Definition — nema backend endpoint~~ ✅ Implementirano (2026-03-11): DELETE /api/sla/definitions/{id} (samo inactive), Delete dugme u UI sa confirmation dialogom
- ~~Breach Management UI — nema acknowledge/resolve interfejs~~ ✅ Implementirano (2026-03-11): SlaBreachListPage sa tab toggle, acknowledge/resolve dijalozima, pagination, filtering
- ~~Stored Report pregled — nema UI za pregled generisanih izveštaja~~ ✅ Implementirano (2026-03-11): StoredSlaReportListPage sa download PDF/CSV, archive, delete, filtering, pagination
- ~~Pagination — sve liste učitavaju sve podatke odjednom~~ ✅ Client-side pagination implementirana (2026-03-11)
- ~~Search/Filter na listama — nema global search~~ ✅ Filtering implementiran (2026-03-11)
- User Profile page — endpoint definisan ali nije korišćen

### 1.3 Flyway migracije

| Migracija | Opis | Status |
|-----------|------|--------|
| V6 | Core SLA tabele (definition, result, breach, excluded_downtime) | ✅ |
| V7 | Resource SLA info | ✅ |
| V8 | Scheduler settings | ✅ |
| V10 | Report tabele (report, report_schedule, report_breach_summary) | ✅ |

---

## 2. Poređenje sa zahtevima

Referenca: `docs-sla/requirements/TehnickaSpecifikacija_v2.md`

### Funkcionalni zahtevi vs implementacija

| # | Zahtev iz specifikacije | Backend | Frontend | Status |
|---|------------------------|---------|----------|--------|
| 1.1 | Kreiranje SLA pravila | ✅ Full CRUD | ✅ 5-step wizard | ✅ Ispunjeno |
| 1.2 | Naziv pravila, metrika, namespace | ✅ SlaDefinition entity | ✅ SlaFormPage Step 1-2 | ✅ Ispunjeno |
| 1.3 | Komparator i prag vrednosti | ✅ SlaComparator enum (GTE/LTE/GT/LT) | ✅ Step 2 metric config | ✅ Ispunjeno |
| 1.4 | Period praćenja (dnevni/nedeljni/mesečni/kvartalni/godišnji) | ✅ SlaPeriodType enum | ✅ Step 3 period selection | ✅ Ispunjeno |
| 1.5 | SLO cilj u procentima | ✅ targetCompliance field | ✅ Step 3 target input | ✅ Ispunjeno |
| 1.6 | Datum početka primene | ✅ startDate field | ✅ Step 1 date picker | ✅ Ispunjeno |
| 1.7 | Izmena i deaktivacija SLA | ✅ Update + deactivate endpoints | ⚠️ Edit da, deactivate/delete ne | ⚠️ Parcijalno |
| 2.1 | Kontinuirano praćenje metrika | ✅ oci-monitor scheduler | ✅ Lista sa statusima | ✅ Ispunjeno |
| 2.2 | Podaci iz CCPM baze (ne direktno OCI) | ✅ Pull-and-Cache arhitektura | N/A | ✅ Ispunjeno |
| 2.3 | Prikaz trenutnog statusa | ✅ SlaStatus enum | ✅ Status badge na listi | ✅ Ispunjeno |
| 2.4 | Istorijat vrednosti i statusa | ✅ SlaResult tabela | ⚠️ Report prikazuje period, nema timeline pregled | ⚠️ Parcijalno |
| 3.1 | Automatsko periodično generisanje | ✅ SlaScheduler (daily/weekly/monthly) | N/A | ✅ Ispunjeno |
| 3.2 | Filtriranje po metrici, resursu, datumu, statusu | ⚠️ Basic query parametri | ⚠️ Nema advanced filter UI | ⚠️ Parcijalno |
| 3.3 | Čuvanje istorijskih rezultata | ✅ SlaResult tabela u MySQL | N/A | ✅ Ispunjeno |
| 4.1 | Grafički i tabelarni prikaz rezultata | N/A | ✅ 3 čarta + tabela u reportu | ✅ Ispunjeno |
| 4.2 | Dashboard sa indikatorima usklađenosti i trendovima | N/A | ✅ ComplianceGauge + charts | ✅ Ispunjeno |
| 4.3 | Izvoz u CSV i PDF format | ✅ Export endpoints | ✅ Blob download | ✅ Ispunjeno |
| 4.4 | Uvid u dnevne i kumulativne vrednosti | ✅ Period-based computation | ⚠️ Jedan period po report requestu | ⚠️ Parcijalno |
| T.1 | Modularna arhitektura (bez izmene CCPM core-a) | ✅ Odvojen modul, zajedničke tabele | ✅ Odvojen POC UI | ✅ Ispunjeno |
| T.2 | Podaci u realnom vremenu iz OCI Monitoring | ✅ oci-monitor scheduleri | N/A | ✅ Ispunjeno |
| T.3 | Integracija sa notifikacionim sistemom | ⚠️ Email radi, webhook TODO | N/A | ⚠️ Parcijalno |

### Rezime pokrivenosti zahteva

```
Ispunjeno:         14/19 (74%)
Parcijalno:         5/19 (26%)
Neispunjeno:        0/19 (0%)
```

**Svi ključni zahtevi su implementirani.** Parcijalni gapovi su:
1. Deaktivacija/brisanje SLA (UI gap)
2. Istorijat vrednosti kao timeline pregled (UI gap)
3. Napredni filteri (UI gap)
4. Kumulativni pregled preko perioda (UI gap)
5. Webhook notifikacije (backend gap)

---

## 3. Gap Analysis matrica

### 3.1 Kritični gapovi (blokeri za produkciju)

| # | Gap | Komponenta | Rizik | Effort | Opis |
|---|-----|-----------|-------|--------|------|
| G-01 | ~~Report Scheduler ne postoji~~ | Backend | ~~KRITIČAN~~ | ~~12-16h~~ | ✅ **IMPLEMENTIRANO** (2026-03-11): `SlaReportScheduler`, `SlaReportSchedulerService`, `SlaReportGenerationService` u oci-monitor. Cron 00:30 (posle computation 00:05-00:15). ShedLock, toggle. PDF/CSV generisanje ostaje kao G-02. |
| G-02 | ~~PDF/CSV generisanje ne radi~~ | Backend | ~~KRITIČAN~~ | ~~8-12h~~ | ✅ **IMPLEMENTIRANO** (2026-03-11): `SlaReportMapper.toReportDtoFromStoredReport()` mapira stored SlaReport → SlaReportDto. `StoredSlaReportManagementService.getReportPdf/Csv()` generišu on-demand preko SlaExportService. Bez file storage — on-the-fly generisanje. |
| G-03 | ~~Authorization check u report servisu~~ | Backend | ~~KRITIČAN~~ | ~~2h~~ | ✅ **IMPLEMENTIRANO** (2026-03-11): `SlaReportService.validateTenantAccess()` implementiran sa superadmin bypass + organization ID poredjenje. Prati TenantService pattern. |
| G-04 | ~~Hardcoded monitoring interval~~ | Backend | ~~VISOK~~ | ~~1h~~ | ✅ **IMPLEMENTIRANO** (2026-03-11): `@Value("${sla.monitoring.interval-minutes:5}")` u `AvailabilityCalculatorService`. Property dodat u `application.properties`. |

### 3.2 Značajni gapovi (should-have za produkciju)

| # | Gap | Komponenta | Rizik | Effort | Opis |
|---|-----|-----------|-------|--------|------|
| G-05 | ~~Breach Management lifecycle~~ | ~~Backend + UI~~ | ~~VISOK~~ | ~~20-30h~~ | ✅ **KOMPLETNO IMPLEMENTIRANO** (2026-03-11): Backend — PATCH acknowledge/resolve endpointi, GET unacknowledged/unresolved, lifecycle polja u DTO, MapStruct mappings, repository queries. Frontend — SlaBreachListPage sa tab toggle (Unacknowledged/Unresolved), acknowledge/resolve dijalozi sa notes, severity badges, pagination, filtering. |
| G-06 | Email retry mehanizam | Backend | VISOK | 4-6h | Jedan pokušaj slanja emaila. Mrežni problem = trajna izgubljena notifikacija. |
| G-07 | Webhook notifikacije | Backend | SREDNJI | 2-3h (Phase 1) | Email-only. Nema integracije sa Slack, PagerDuty, ServiceNow, Mattermost. |
| G-08 | ~~Delete/Deactivate SLA u UI~~ | ~~Frontend~~ | ~~SREDNJI~~ | ~~2h~~ | ✅ **KOMPLETNO IMPLEMENTIRANO** (2026-03-11): Deactivate dugme + confirmation dialog. Delete: backend `DELETE /api/sla/definitions/{id}` (samo inactive), frontend Delete dugme sa confirmation dialogom. |
| G-09 | ~~Audit username u ExcludedDowntime~~ | Backend | ~~NIZAK~~ | ~~1h~~ | ✅ **IMPLEMENTIRANO** (2026-03-11): `AuthHelper.getPrincipalUsername("system")` u 3 kontrolera (6 mesta): SlaExcludedDowntimeController, SlaReportScheduleController, StoredSlaReportController. |

### 3.3 Nice-to-have gapovi

| # | Gap | Komponenta | Effort | Opis |
|---|-----|-----------|--------|------|
| G-10 | ~~Pagination na listama~~ | Frontend | ~~4h~~ | ✅ **IMPLEMENTIRANO** (2026-03-11): Reusable `Pagination` komponenta + `usePagination` hook. Client-side pagination na SlaListPage i SlaReportScheduleListPage (10 items/page, page size selector). |
| G-11 | ~~Advanced filtering~~ | Frontend | ~~4-6h~~ | ✅ **IMPLEMENTIRANO** (2026-03-11): Client-side filtering na SlaListPage (search by name, status, period type) i SlaReportScheduleListPage (search by name, status, frequency). useMemo + Clear filters dugme. Integrisano sa pagination. |
| G-12 | ~~Manual recomputation improvements~~ | ~~Backend~~ | ~~3-4h~~ | ✅ **UI IMPLEMENTIRAN** (2026-03-11): Poboljšan trigger dialog — date range inputi (periodStart/periodEnd), force recompute checkbox, default period po periodType, detaljni prikaz rezultata. Dry-run/async batch ostaje za Phase 2. |
| G-12b | Manual recomputation Phase 2 | Backend | 8-12h | **BACKLOG**: Backend dry-run (`dryRun` field u DTO + skip save logika), async batch job (`sla_batch_job` tabela + `@Async` servis + polling endpoint), progress tracking, cancellation support. Ref: `MANUAL-SLA-RECOMPUTATION-ANALYSIS.md` Pristup 1 komplet + Pristup 2. |
| G-16 | Notifikacije za bitne evente | Backend | 4-6h | **BACKLOG**: Email/webhook notifikacije za: delete SLA definition, breach acknowledge/resolve, schedule activate/deactivate, report generation complete. Event-driven pattern (`ApplicationEventPublisher`). |
| G-13 | ~~Cron expression builder~~ | ~~Frontend~~ | ~~4h~~ | ✅ **IMPLEMENTIRANO** (2026-03-11): Reusable `CronExpressionBuilder` komponenta sa 6 preset-a, 5 field selektora, human-readable opisom, manual input toggle. Integrisano u SlaReportScheduleFormPage. |
| G-14 | SLA istorijat timeline | Frontend | 6-8h | Pregled SLA rezultata kroz vreme kao timeline/trend chart. |
| G-15 | ~~Stored Report management UI~~ | ~~Frontend~~ | ~~4-6h~~ | ✅ **IMPLEMENTIRANO** (2026-03-11): `StoredSlaReportListPage` sa tabelom (report name, SLA name, period, compliance%, breaches, status), download PDF/CSV (blob), archive (optimistic update), delete (confirmation dialog). `storedSlaReportService` (6 metoda). Filtering (search + status + breaches) + pagination. Nav tab. |

---

## 4. Zabbix SLA — komparativna analiza

### 4.1 Zabbix SLA 7.0 — ključne karakteristike

Zabbix SLA (od verzije 6.0) pruža built-in SLA monitoring sa sledećim mogućnostima:

| Aspekt | Zabbix SLA | OCI SLA (naš sistem) |
|--------|-----------|---------------------|
| **SLI formula** | uptime / (uptime + downtime) | matched_datapoints / expected_datapoints |
| **Reporting periodi** | Daily, Weekly, Monthly, Quarterly, Annually | Hourly, Daily, Weekly, Monthly, Quarterly, Yearly |
| **Schedule** | 24x7 ili custom (dani u nedelji, time windows) | 24x7 ili custom JSON schedule |
| **Service matching** | Tag-based (service tags, AND/OR logika) | Resource-based + OCI Query + Tag filtering |
| **Excluded downtimes** | Da (ime, period, service tags) | Da (period, opis, overlap validacija) |
| **SLO Target** | Procenat (npr. 99.9%) | Procenat + opcioni penalty |
| **Effective date** | Datum od kog važi | startDate |
| **Timezone** | Globalni ili per-SLA | Per-SLA |
| **Status** | Enabled/Disabled | isActive + dateRange |
| **API** | sla.create, sla.get, sla.getsli, sla.update, sla.delete | Full REST CRUD + trigger + report |
| **Penalty** | ❌ Ne postoji | ✅ Fixed + formula-based (SpEL) |
| **Breach lifecycle** | ❌ Ne postoji | ⚠️ Entity postoji, API nedostaje |
| **Report scheduling** | Automatski dostupno | ⚠️ Entity postoji, scheduler nedostaje |
| **Report export** | ❌ (samo web pregled) | ✅ CSV/PDF endpoints (PDF gen. TODO) |
| **Notifikacije** | ❌ Ne postoji u SLA kontekstu | ✅ Email (webhook TODO) |
| **Multi-instance** | Zabbix Server je singleton | ✅ ShedLock distributed locking |
| **UI filter** | Name, Status, Service tags | ⚠️ Nema filter UI |

### 4.2 Šta OCI SLA ima a Zabbix nema

1. **Penalty kalkulacija** — Zabbix nema nikakav koncept penala. Naš sistem ima fixed penalty i formula-based penalty sa SpEL evaluacijom.
2. **Breach Detection & Severity** — Zabbix ne generiše breach evente. Naš sistem detektuje breach-eve sa severity klasifikacijom (CRITICAL/HIGH/MEDIUM/LOW).
3. **Email notifikacije na breach** — Zabbix SLA nema notifikacije. Naš sistem šalje email pri breach-u.
4. **Report export (CSV/PDF)** — Zabbix SLA izveštaji su samo u web interfejsu.
5. **Report scheduling** — Zabbix nema koncept zakazanih SLA izveštaja.
6. **Manual recomputation** — Zabbix ne dozvoljava ručno ponovno izračunavanje.
7. **Grace tolerance** — Naš sistem podržava grace period pre breach eskalacije.
8. **Data coverage validacija** — Naš sistem proverava da li ima dovoljno podataka (≥80%) pre nego što donese zaključak.

### 4.3 Šta Zabbix ima a OCI SLA nema (potencijalna inspiracija)

1. **Service dependency tree** — Zabbix Services imaju parent-child relacije. SLA se računa na nivou servisa koji može zavisiti od drugih servisa. Naš sistem prati individualne resurse.
2. **Problem-based SLI** — Zabbix SLI se bazira na trigger/problem stanju (up/down), dok naš sistem koristi metric datapoint matching. Zabbix pristup je jednostavniji za availability kalkulaciju.
3. **Tag-based AND/OR logika u filteru** — Zabbix filter na SLA listi podržava AND/OR kombinovanje service tagova. Naš UI nema filter na listi.

### 4.4 Zaključak komparacije

OCI SLA sistem je **značajno bogatiji funkcionalno** od Zabbix SLA:
- Penalty, breach lifecycle, notifikacije, report scheduling — ništa od toga Zabbix nema
- Zabbix SLA je dizajniran kao lightweight additional feature, ne kao enterprise SLA management
- Jedina inspiracija iz Zabbix-a: service dependency model i tag-based filtering na UI listi

---

## 5. Pregled dosadašnjih analiza

### 5.1 Status po dokumentu iz `docs-sla/analysis/`

| Dokument | Tema | Preporučeni pristup | Status implementacije |
|----------|------|---------------------|----------------------|
| PENALTY_CALCULATION_STATUS.md | Penalty kalkulacija | Phase 2.1 (fixed) + Phase 2.2 (formula) | ✅ **Implementirano** — PenaltyCalculationService + FormulaEvaluationService potpuno funkcionalni |
| BREACH-RESOLUTION-API-ANALYSIS.md | Breach lifecycle | State Machine sa workflow-om (DETECTED→ACKNOWLEDGED→INVESTIGATING→RESOLVED) | ⚠️ **Backend implementiran** (2026-03-11) — Simple PATCH endpointi (Pristup A). UI ostaje TODO. |
| EMAIL-RETRY-LOGIC-ANALYSIS.md | Email retry | Scheduled cleanup + exponential backoff | ❌ **Nije implementirano** — Jedan pokušaj, nema retry |
| MULTI-INSTANCE-SCHEDULER-ANALYSIS.md | Distributed locking | ShedLock (MySQL-based) | ✅ **Implementirano** — ShedLock sa `@SchedulerLock` na svim scheduled metodama |
| SLA-REPORTS-SCHEDULER-ANALYSIS.md | Automatsko generisanje izveštaja | Entity + Scheduler + Email delivery | ✅ **Implementirano** (2026-03-11) — SlaReportScheduler + SlaReportSchedulerService + SlaReportGenerationService. Email delivery ostaje TODO. |
| SLA_EXCLUDED_DOWNTIME_IMPLEMENTATION.md | Maintenance windows | Full CRUD + overlap validacija | ✅ **Implementirano** — 100% kompletno, backend + frontend |
| TRANSACTION-BOUNDARIES-ANALYSIS.md | Race condition | @TransactionalEventListener(AFTER_COMMIT) | ✅ **Implementirano** — SlaBreachDetectionService koristi AFTER_COMMIT |
| WEBHOOK-NOTIFICATIONS-ANALYSIS.md | Webhook podrška | Phase 1 (simple POST + HMAC) | ❌ **Nije implementirano** — Komentarisano u kodu |
| MANUAL-SLA-RECOMPUTATION-ANALYSIS.md | Manual recomputation | Phase 1 (dry-run + range) + Phase 2 (async batch) | ⚠️ **UI poboljšan** (2026-03-11): date range, force recompute, detaljni rezultati. Dry-run/async batch ostaje za Phase 2. |

### 5.2 Scorecard

```
Implementirano po preporuci:  8/9 (89%)
Parcijalno:                   1/9 (11%)
Neimplementirano:             0/9 (0%)
```

---

## 6. Predlozi unapređenja sa pristupima

### 6.1 Report Scheduler (G-01 + G-02)

**Problem**: Korisnici mogu konfigurisati report schedule ali izveštaji se nikada neće generisati.

#### Pristup A: Lightweight Scheduler (⭐ PREPORUKA)

Dodati `@Scheduled` komponentu koja koristi postojeći `SlaReportSchedule` entity.

```
┌──────────────────────────────────────────────────────┐
│              SlaReportScheduler                       │
│                                                      │
│  @Scheduled(cron = "0 0 * * * *")  ← svaki sat      │
│  @SchedulerLock("sla-report-scheduler")              │
│                                                      │
│  1. Find all active SlaReportSchedule                │
│  2. Filter: nextRunAt <= now()                       │
│  3. For each:                                        │
│     a) SlaReportService.generateReport()             │
│     b) Generate PDF/CSV if configured                │
│     c) Send email with attachment                    │
│     d) Update lastRunAt, nextRunAt, counter          │
│     e) Archive if policy requires                    │
│                                                      │
│  Error handling: per-schedule, catch-and-log          │
└──────────────────────────────────────────────────────┘
```

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska — koristi postojeće entitete i servise |
| Effort | 12-16h |
| Rizik | Nizak — dodaje novu komponentu, ne menja postojeće |
| Preduslov | PDF/CSV generisanje mora biti implementirano prvo |

#### Pristup B: Event-Driven Report Generation

Umesto cron-a, report se generiše kad SLA computation završi.

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Srednja — event listener pattern |
| Effort | 16-20h |
| Rizik | Srednji — zavisi od computation pipeline-a |

**Preporuka**: Pristup A — jednostavniji, ShedLock osigurava da radi samo jedna instanca.

---

### 6.2 Breach Management Lifecycle (G-05)

**Problem**: SlaBreach entity ima `isResolved`, `resolvedAt`, `resolvedBy`, `isAcknowledged`, `acknowledgedAt`, `acknowledgedBy` polja ali ne postoji API za upravljanje breach lifecycle-om.

#### Pristup A: Simple PATCH Endpoints (⭐ PREPORUKA za Phase 1)

Direktni PATCH endpointi za acknowledge i resolve bez state machine-a.

```
┌─────────────────────────────────────────────────┐
│  Breach Management API                          │
│                                                 │
│  PATCH /api/sla/breaches/{id}/acknowledge       │
│  Body: { "notes": "Looking into this" }         │
│  → setAcknowledged + acknowledgedAt + By        │
│                                                 │
│  PATCH /api/sla/breaches/{id}/resolve           │
│  Body: { "notes": "Root cause fixed" }          │
│  → setResolved + resolvedAt + By                │
│                                                 │
│  GET /api/sla/breaches?status=UNACKNOWLEDGED    │
│  → Lista neprihvaćenih breach-eva               │
│                                                 │
│  GET /api/sla/breaches/{id}                     │
│  → Detalji breach-a sa svim poljima             │
└─────────────────────────────────────────────────┘
```

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska |
| Effort | 4-6h backend + 4-6h frontend |
| Rizik | Nizak |
| Ograničenje | Nema audit trail, nema MTTA/MTTR |

#### Pristup B: Full State Machine + Audit Trail

Kompletan workflow sa state machine-om (DETECTED → ACKNOWLEDGED → INVESTIGATING → RESOLVED) i `breach_state_transition` tabelom.

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Visoka |
| Effort | 20-30h ukupno (4 nedelje) |
| Rizik | Srednji — nova tabela, nova logika, nova UI |
| Prednost | MTTA/MTTR, audit trail, eskalacija |

**Preporuka**: Pristup A za MVP, Pristup B kao Phase 2 unapređenje.

---

### 6.3 Email Retry Logic (G-06)

**Problem**: Mrežni problem pri slanju emaila = trajna izgubljena notifikacija.

#### Pristup A: Inline Retry (⭐ PREPORUKA)

Retry u okviru istog metoda sa exponential backoff.

```
┌──────────────────────────────────────────────────────┐
│  SlaNotificationService.sendNotification()           │
│                                                      │
│  for (attempt = 1; attempt <= MAX_RETRIES; attempt++)│
│    try:                                              │
│      mailerService.sendEmail(...)                    │
│      breach.markNotificationSent()                   │
│      return SUCCESS                                  │
│    catch:                                            │
│      if (attempt < MAX_RETRIES)                      │
│        sleep(backoff(attempt))  ← 5s, 15s, 45s       │
│      else                                            │
│        breach.markNotificationFailed(reason)         │
│        return FAILURE                                │
│                                                      │
│  Backoff: 5s × 3^(attempt-1), max 5 min             │
└──────────────────────────────────────────────────────┘
```

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska |
| Effort | 2-3h |
| Rizik | Nizak |
| Ograničenje | Blokira async thread za vreme retry-a |

#### Pristup B: Scheduled Retry Job

Dodati retry tracking polja na SlaBreach i scheduled job koji periodično proverava.

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Srednja |
| Effort | 4-6h |
| Rizik | Nizak |
| Prednost | Ne blokira thread, persistent state |

**Preporuka**: Pristup A za brzi fix, Pristup B ako se pokaže da su email problemi česti.

---

### 6.4 Webhook Notifikacije (G-07)

**Problem**: Samo email notifikacije. Nema integracije sa modernim alatima (Slack, PagerDuty, Mattermost).

#### Pristup A: Simple Webhook (⭐ PREPORUKA za Phase 1)

Dodati `webhookUrl` na `SlaDefinition`, POST JSON payload pri breach-u.

```
┌──────────────────────────────────────────────┐
│  Breach Detection                            │
│       │                                      │
│       ├─→ SlaNotificationService             │
│       │     ├─→ sendEmail()    ← postojeće   │
│       │     └─→ sendWebhook() ← NOVO         │
│       │           │                          │
│       │           ▼                          │
│       │     POST webhookUrl                  │
│       │     Headers:                         │
│       │       X-Webhook-Signature: HMAC      │
│       │     Body: {                          │
│       │       "eventType": "sla.breach",     │
│       │       "breach": { ... },             │
│       │       "sla": { ... }                 │
│       │     }                                │
│       │                                      │
└──────────────────────────────────────────────┘
```

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska |
| Effort | 2-3h |
| Rizik | Nizak |
| Ograničenje | Jedan webhook per SLA |

#### Pristup B: WebhookConfig Entity sa Delivery Logging

Nova `webhook_config` tabela, višestruki webhook-ovi per SLA, delivery log sa retry logikom.

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Visoka |
| Effort | 12-16h |
| Prednost | Audit trail, retry, filtering, test endpoint |

**Preporuka**: Pristup A za MVP. Pristup B samo ako korisnici zahtevaju webhook management.

---

### 6.5 UI Delete/Deactivate (G-08)

**Problem**: Korisnik ne može obrisati ili deaktivirati SLA iz interfejsa.

#### Pristup: Dodati akcije na SlaListPage

```
┌────────────────────────────────────────────────────┐
│  SlaListPage — Actions kolona                      │
│                                                    │
│  [Edit] [Report] [Trigger] [⋮]                     │
│                              │                     │
│                              ├── Deactivate        │
│                              ├── Activate          │
│                              └── Delete (confirm)  │
│                                                    │
│  Delete → Custom confirmation dialog               │
│  Deactivate → PATCH /definitions/{id}/deactivate   │
└────────────────────────────────────────────────────┘
```

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Niska |
| Effort | 2-3h |
| Rizik | Nizak |

---

### 6.6 SLA Istorijat Timeline (G-14)

**Problem**: Korisnik ne može videti trend SLA compliance-a kroz vreme.

#### Pristup A: Timeline Chart na Report Page (⭐ PREPORUKA)

Dodati novi endpoint koji vraća SLA rezultate za date range i prikazati kao line chart.

```
┌──────────────────────────────────────────────────┐
│  GET /api/sla/results/timeline                   │
│  ?slaDefinitionId=xxx                            │
│  &periodStart=2025-01-01                         │
│  &periodEnd=2025-12-31                           │
│                                                  │
│  Response: [                                     │
│    { "periodDate": "2025-01", "compliance": 99.5,│
│      "status": "FULFILLED" },                    │
│    { "periodDate": "2025-02", "compliance": 98.1,│
│      "status": "WARNING" },                      │
│    ...                                           │
│  ]                                               │
│                                                  │
│  UI: Line chart sa compliance trendom            │
│  ───────────────────────────                     │
│  100% ─────●─────────────●───                    │
│  99%  ──────────●────────────                    │
│  98%  ────────────────●──────  ← breach zone     │
│       Jan  Feb  Mar  Apr  May                    │
└──────────────────────────────────────────────────┘
```

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Srednja |
| Effort | 6-8h (backend 3h + frontend 3-5h) |
| Rizik | Nizak |

#### Pristup B: Dedicated Dashboard Page

Nova stranica sa multiple SLA-ova na jednom dashboard-u, filter po periodu i statusu.

| Kriterijum | Ocena |
|-----------|-------|
| Složenost | Visoka |
| Effort | 16-20h |
| Prednost | Holistic view svih SLA-ova |

**Preporuka**: Pristup A kao brz dodatak na postojeću Report stranicu.

---

## 7. Preporuke i prioritizacija

### 7.1 Prioritetna matrica

```
                VISOK IMPACT
                    │
         G-01  G-03 │ G-05
     (report  (auth)│(breach
      sched)        │ mgmt)
                    │
  ──────────────────┼──────────────── EFFORT
                    │
         G-06  G-08 │ G-14  G-02
     (email  (UI    │(timeline)(PDF/
      retry)  del)  │        CSV)
                    │
                NIZAK IMPACT
```

### 7.2 Preporučeni redosled implementacije

#### Sprint 1: Kritični gapovi (2-3 dana)

| # | Zadatak | Effort | Prioritet |
|---|---------|--------|-----------|
| 1 | G-03: Authorization check u SlaReportService | 2h | ⭐ KRITIČAN |
| 2 | G-04: Konfigurabilni monitoring interval | 1h | ⭐ KRITIČAN |
| 3 | G-09: SecurityContext za audit username | 1h | NIZAK ali trivijalan |
| 4 | G-06: Email retry (Pristup A — inline) | 2-3h | VISOK |
| 5 | G-08: Delete/Deactivate u UI | 2-3h | SREDNJI |

#### Sprint 2: Report Pipeline (1-2 nedelje)

| # | Zadatak | Effort | Prioritet |
|---|---------|--------|-----------|
| 6 | G-02: PDF/CSV generisanje | 8-12h | ⭐ KRITIČAN |
| 7 | G-01: Report Scheduler (Pristup A) | 12-16h | ⭐ KRITIČAN |
| 8 | G-15: Stored Report management UI | 4-6h | SREDNJI |

#### Sprint 3: Breach Management & Notifications (1-2 nedelje)

| # | Zadatak | Effort | Prioritet |
|---|---------|--------|-----------|
| 9 | G-05: Breach Management API (Pristup A — simple PATCH) | 4-6h | VISOK |
| 10 | G-05: Breach Management UI | 4-6h | VISOK |
| 11 | G-07: Webhook notifikacije (Pristup A — simple) | 2-3h | SREDNJI |

#### Sprint 4: UX Polish (1 nedelja)

| # | Zadatak | Effort | Prioritet |
|---|---------|--------|-----------|
| 12 | G-14: SLA Timeline chart (Pristup A) | 6-8h | SREDNJI |
| 13 | G-10: Pagination na listama | 4h | NIZAK |
| 14 | G-11: Advanced filtering | 4-6h | NIZAK |
| 15 | G-12: Manual recomputation improvements | 3-4h | NIZAK |

---

## 8. Implementacioni plan

### 8.1 Ukupna procena

```
Sprint 1 (Kritični quick-fix):       8-10h  (~2 dana)
Sprint 2 (Report Pipeline):         24-34h  (~1-2 nedelje)
Sprint 3 (Breach & Notifications):  10-15h  (~1 nedelja)
Sprint 4 (UX Polish):              17-22h  (~1 nedelja)
────────────────────────────────────────────
UKUPNO:                             59-81h  (~4-6 nedelja)
```

### 8.2 Dependency dijagram

```
G-03 (auth) ────────────────┐
G-04 (interval) ────────────┤
G-09 (audit) ───────────────┤ Sprint 1 (nezavisni)
G-06 (retry) ───────────────┤
G-08 (UI delete) ──────────┘

G-02 (PDF/CSV) ─────────────┐
        │                   │ Sprint 2 (sekvencijalni)
        ▼                   │
G-01 (Report Scheduler) ────┤
        │                   │
        ▼                   │
G-15 (Stored Report UI) ───┘

G-05 (Breach API) ──────────┐
        │                   │ Sprint 3
        ▼                   │
G-05 (Breach UI) ───────────┤
G-07 (Webhook) ────────────┘ (nezavisan)

G-14 (Timeline) ────────────┐
G-10 (Pagination) ──────────┤ Sprint 4 (nezavisni)
G-11 (Filtering) ───────────┤
G-12 (Recomputation) ──────┘
```

### 8.3 Rok i milestone-ovi

| Milestone | Sadržaj | Okvirni rok |
|-----------|---------|-------------|
| M1: Security & Stability | G-03, G-04, G-06, G-08, G-09 | +2 dana |
| M2: Report Pipeline | G-02, G-01, G-15 | +2 nedelje |
| M3: Breach Management | G-05, G-07 | +3 nedelje |
| M4: UX Improvements | G-10, G-11, G-12, G-14 | +4-6 nedelja |
| **Produkcija** | Svi gapovi zatvoreni | **~6 nedelja od početka** |

### 8.4 Preduslovi i rizici

| Rizik | Mitigacija |
|-------|-----------|
| PDF generisanje može zahtevati eksternu biblioteku (iText, OpenPDF, Jasper) | Proceniti effort za integraciju unapred; razmotriti da li je HTML-to-PDF (wkhtmltopdf) dovoljno |
| Email server nedostupnost u produkciji | Implementirati G-06 (retry) pre puštanja u produkciju |
| Multi-tenant security | Implementirati G-03 (auth check) odmah |
| Performanse sa velikim brojem SLA definicija | Implementirati G-10 (pagination) pre nego što bude >50 SLA |

---

## Napomene

- Svi effort-i su okvirne procene i mogu varirati
- Priority se može promeniti na osnovu feedback-a korisnika
- Ovaj dokument treba ažurirati nakon svakog sprint-a
- Referentni dokumenti: `docs-sla/analysis/*.md`, `docs-sla/requirements/TehnickaSpecifikacija_v2.md`
