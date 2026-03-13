# SLA Backlog

> **Poslednje ažuriranje**: 2026-03-13

---

## Završeno

| # | Stavka | Datum | Napomena |
|---|--------|-------|----------|
| G-01 | Report Scheduler | 2026-03-11 | `SlaReportScheduler` + `SlaReportSchedulerService` + `SlaReportGenerationService` u oci-monitor. Cron 00:30, ShedLock, toggle via `sla.report.scheduled`. PDF/CSV gen. ostaje kao G-02. |
| G-03 | Authorization check u SlaReportService | 2026-03-11 | `validateTenantAccess()` implementiran sa superadmin/sysadmin bypass + organization ID poređenje. Prati TenantService pattern. |
| G-04 | Konfigurabilni monitoring interval | 2026-03-11 | `@Value("${sla.monitoring.interval-minutes:5}")` u `AvailabilityCalculatorService`. Uklonjen hardcoded `= 5` na 2 mesta. Property dodat u `application.properties`. |
| G-02 | PDF/CSV generisanje za stored reports | 2026-03-11 | `SlaReportMapper.toReportDtoFromStoredReport()` + `StoredSlaReportManagementService.getReportPdf/Csv()`. On-demand generisanje iz stored podataka, bez file storage. Reuse SlaExportService (Thymeleaf PDF + Commons CSV). |
| G-05 | Breach Management API (backend) | 2026-03-11 | Simple PATCH endpointi (Pristup A). `PATCH /breaches/{id}/acknowledge`, `PATCH /breaches/{id}/resolve`, `GET /breaches/unacknowledged`, `GET /breaches/unresolved`. Lifecycle polja u SlaBreachDto, MapStruct mappings, repository queries. Request DTOs u oci-library. Username iz SecurityContext. |
| G-08 | Deactivate SLA u UI | 2026-03-11 | Deactivate dugme u Actions koloni sa confirmation dialogom. Lista prebačena sa `getActiveDefinitions()` na `getAllDefinitions()` — prikazuje active + inactive. `slaDefinitionService.deactivate()` poziva PATCH endpoint. Optimistic UI update. |
| G-09 | SecurityContext za audit username | 2026-03-11 | Zamenjeno 6x hardkodirano `"system"` sa `AuthHelper.getPrincipalUsername("system")` u 3 kontrolera: SlaExcludedDowntimeController (create, update), SlaReportScheduleController (create, update, updateStatus), StoredSlaReportController (archive). |
| G-10 | Pagination na listama | 2026-03-11 | Reusable `Pagination` komponenta + `usePagination` hook (client-side). Integrisano u SlaListPage i SlaReportScheduleListPage. Default 10 items/page, page size selector (10/20/50), first/prev/next/last navigacija. |
| G-11 | Advanced filtering | 2026-03-11 | Client-side filtering sa `useMemo`. SlaListPage: search by name + status (All/Active/Inactive) + period type. SlaReportScheduleListPage: search by name + status + frequency. Clear filters dugme. Integrisano sa pagination (filtrirana lista → paginated). |
| G-12 | Manual recomputation improvements | 2026-03-11 | Poboljšan trigger dialog u SlaListPage: date range inputi (periodStart/periodEnd), force recompute checkbox, auto-default na početak tekućeg perioda po periodType, detaljni prikaz rezultata (status, compliance%, resultId, message). Frontend-only — koristi postojeća backend polja. |
| G-05 UI | Breach Management UI | 2026-03-11 | Nova `SlaBreachListPage` stranica (`/sla/breaches`). Tab toggle (Unacknowledged/Unresolved), tabela sa severity badge, compliance/target/deviation kolone, acknowledge/resolve dijalozi sa notes. `slaBreachService` (4 metode), `slaBreach.types.ts`, API rute u constants. Breaches tab u navigaciji. Pagination + filtering (search + severity). |
| G-13 | Cron expression builder | 2026-03-11 | Reusable `CronExpressionBuilder` komponenta. 6 preset-a (every hour, daily midnight, daily 6am, weekly Monday, monthly 1st, quarterly). Custom mode sa 5 field selektora (minute, hour, day, month, weekday). Human-readable opis, expression preview, manual input toggle. Integrisano u SlaReportScheduleFormPage umesto plain text inputa. |
| G-15 | Stored Report management UI | 2026-03-11 | Nova `StoredSlaReportListPage` stranica (`/sla/reports/stored`). Tabela: report name, SLA name, period, compliance% (color-coded vs target), breach count, status badge (DRAFT/PUBLISHED/ARCHIVED), generated at/by. Actions: Download PDF, Download CSV, Archive (optimistic update), Delete (confirmation dialog). `storedSlaReportService` (6 metoda sa blob download za PDF/CSV). Filtering: search + status + has breaches. Pagination. Nav tab "Stored Reports". |
| G-08b | Delete SLA Definition (backend + UI) | 2026-03-11 | Backend: `DELETE /api/sla/definitions/{id}` endpoint. `SlaDefinitionManagementService.deleteSlaDefinition()` — hard delete, samo inactive definicije. `SlaService.deleteSlaDefinition()` sa tenant access validacijom. Frontend: `slaDefinitionService.delete()`, Delete dugme u SlaListPage (samo za inactive SLA), confirmation dialog sa upozorenjem. API ruta `DeleteDefinition(id)` u constants. |
| G-14 | SLA Timeline chart | 2026-03-11 | `SlaTimelinePage` (`/sla/timeline`) sa Line chartom za compliance trend. `SlaTimelineChart` komponenta (Chart.js Line, target linija, status-colored tačke, gradient fill). `SlaResultDto` tip, `slaResultService` (koristi `GET /sla/results/definition/{id}`). Summary kartice (avg/min/max compliance, breach count, violation minutes). Tabela rezultata. Nav tab "Timeline". |
| G-06 | Email retry (Hybrid — Phase 1 + Phase 2) | 2026-03-12 | **Phase 1**: Inline exponential backoff u sva 4 MailerService implementacije (oci-api + oci-monitor). **Phase 2**: Scheduled cleanup — `EmailSendLog` entity + `EmailSendStatus` enum (oci-library), `EmailSendLogRepository` + `EmailSendLogService` + `EmailRetryScheduler` (oci-monitor). @SchedulerLock + SchedulerToggleService. `SlaNotificationService` prebačen na EmailSendLogService (prvi consumer). Scheduled backoff: 5min→15min→45min→2h15min→6h (5 retries, ~9.5h). Flyway: dev V12, prod V6. |
| G-17 | Email delivery za zakazane izveštaje sa PDF/CSV attachmentima | 2026-03-12 | **oci-library**: `EmailAttachmentDto` (filename, content, contentType), `SendEmailRequestDto.attachments` + `hasAttachments()`. **oci-monitor**: `SmtpMailerService` — multipart when attachments (MimeMessageHelper + addAttachment via ByteArrayDataSource). `SendGridMailerService` — Attachments API sa Base64 encoding. `pom.xml` — dodati Thymeleaf, Flying Saucer, Commons CSV dependencies. `SlaReportExportService` (NOVO) — PDF/CSV generisanje iz SlaReport entity (mirror oci-api SlaExportService). Kopirani `pdf_slareport.html` + `style.css` u oci-monitor resources. `SlaNotificationService.sendReportEmail()` — generiše PDF/CSV attachment-e po schedule config, šalje HTML email via EmailSendLogService. `SlaReportGenerationService.sendReportEmailIfConfigured()` — poziv posle logReportGeneratedEvent(), catch-and-log pattern. |
| G-16 | SLA Notifikacije — Backend + Frontend | 2026-03-12 | **Backend**: `sla_event_log` tabela, `SlaEventType` enum, `SlaEventLog` entity (oci-library). oci-api: `SlaEventLogService`, `SlaEventLogRepository`, `SlaNotificationController`, `SlaEventLogDto`, `SlaEventLogMapper`. oci-monitor: `SlaEventNotificationScheduler` (@Scheduled 5min, ShedLock), `SlaNotificationService.sendEventNotification()` via EmailSendLogService, `SlaEventLogRepository`. Integracioni pozivi u SlaService, SlaReportScheduleManagementService, SlaReportGenerationService. Flyway: dev V14, prod V8. **Frontend**: `NotificationBell` (badge + dropdown, polling 60s), `SlaNotificationListPage` (/sla/notifications, tabela, 3 filtera, pagination, dismiss), `slaNotificationService`, `slaNotification.types.ts`. **Navigacija**: Restrukturirano — 6 SLA sub-stranica u "SLA" dropdown, 3 top-level stavke (SLA, Notifications, Architecture Info). NavDropdown komponenta (hover+click, chevron, opisi). Olakšava UI team integraciju. |
| G-18 | Tenant-based data filtering (UI) | 2026-03-13 | Client-side filtriranje svih stranica/widgeta po selektovanom tenantu. **Direktno**: `d.tenant?.ocid === tenant.ocid` za SlaDefinitionsTable, SlaTimelinePage, SlaReportForm, SlaReportScheduleFormPage. **Indirektno**: novi `useTenantDefinitionIds` hook (`Set<string>` definition ID-jeva za tenant) za BreachTable, ScheduleTable, StoredReportTable, NotificationTable. React Query cache sharing (`slaKeys.all()`). Dvostepeni pattern: tenant scoping → user filters. Timeline auto-select first definition na tenant change. |
| G-19 | Tenant pre-selection na SLA create formi | 2026-03-13 | "Zakupac (Organizacija)" dropdown na `/sla/create` automatski pre-populated iz header TenantContext-a. `useEffect` u `SlaFormPage.tsx` mapira `tenant.organization.id` → `formData.tenantId`. Samo create mode (ne edit). Ne overrideuje ručnu promenu. "Form context pre-fill" pattern. |
| G-20 | Language picker (oci-ui aligned) | 2026-03-13 | `LanguagePicker` komponenta (Ćirilica/Latinica) po oci-ui patternu. Custom dropdown + inline SVG zastava. Placement: SlaNavigation + LoginPage. `i18n.changeLanguage()`, localStorage key `'language'`. Konstante u `constants/index.ts`, `i18n.ts` koristi konstante. UI tim zamenjuje sa Mantine Menu + country-flag-icons. Docs: §13. |

---

## Sprint 1: Kritični quick-fix (~2 dana)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-03 | ~~Authorization check u SlaReportService~~ | ~~2h~~ | ~~KRITIČAN~~ | ✅ DONE |
| G-04 | ~~Konfigurabilni monitoring interval~~ | ~~1h~~ | ~~KRITIČAN~~ | ✅ DONE |
| G-09 | ~~SecurityContext za audit username~~ | ~~1h~~ | ~~NIZAK~~ | ✅ DONE |
| G-06 | ~~Email retry (inline exponential backoff)~~ | ~~2-3h~~ | ~~VISOK~~ | ✅ DONE |
| G-08 | ~~Delete/Deactivate SLA u UI~~ | ~~2-3h~~ | ~~SREDNJI~~ | ✅ DONE (deactivate + delete) |

---

## Sprint 2: Report Pipeline (~1-2 nedelje)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-02 | ~~PDF/CSV generisanje (StoredSlaReportManagementService)~~ | ~~8-12h~~ | ~~KRITIČAN~~ | ✅ DONE |
| G-15 | ~~Stored Report management UI~~ | ~~4-6h~~ | ~~SREDNJI~~ | ✅ DONE |
| G-17 | ~~Email delivery za zakazane izveštaje~~ | ~~4-6h~~ | ~~SREDNJI~~ | ✅ DONE |

---

## Sprint 3: Breach Management & Notifications (~1 nedelja)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-05 | ~~Breach Management API (simple PATCH endpoints)~~ | ~~4-6h~~ | ~~VISOK~~ | ✅ DONE |
| G-05 | ~~Breach Management UI~~ | ~~4-6h~~ | ~~VISOK~~ | ✅ DONE |
| G-07 | Webhook notifikacije (simple POST + HMAC) | 2-3h | SREDNJI | TODO |

---

## Sprint 4: UX Polish (~1 nedelja)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-14 | ~~SLA Timeline chart~~ | ~~6-8h~~ | ~~SREDNJI~~ | ✅ DONE |
| G-10 | ~~Pagination na listama~~ | ~~4h~~ | ~~NIZAK~~ | ✅ DONE |
| G-11 | ~~Advanced filtering~~ | ~~4-6h~~ | ~~NIZAK~~ | ✅ DONE |
| G-12 | ~~Manual recomputation improvements~~ | ~~3-4h~~ | ~~NIZAK~~ | ✅ DONE |
| G-13 | ~~Cron expression builder~~ | ~~4h~~ | ~~NIZAK~~ | ✅ DONE |
| G-18 | ~~Tenant-based data filtering~~ | ~~3-4h~~ | ~~SREDNJI~~ | ✅ DONE |

---

## Backlog (budući sprintovi)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-06a | ~~Seed data `email.retry.scheduled` u `scheduler_settings` tabeli~~ | ~~15min~~ | ~~VISOK~~ | ✅ DONE |
| G-06b | Inkrementalna migracija ostalih oci-monitor pozivalaca na `EmailSendLogService` — BudgetNotificationService, SubscriptionNotificationService, CommitmentNotificationService, CostReportsService, MetricsNotificationEventListener. Zamena `mailerService` → `emailSendLogService.sendEmailWithPersistence()`. | 2-3h | SREDNJI | BACKLOG |
| G-12b | Manual recomputation Phase 2 (dry-run, async batch, cancellation) | 8-12h | NIZAK | BACKLOG |
| G-16 | ~~Notifikacije za bitne evente~~ | ~~7-9h~~ | ~~SREDNJI~~ | ✅ DONE (backend + frontend). |
| G-16-FE | ~~SLA Notifikacije — Frontend~~ | ~~4-6h~~ | ~~SREDNJI~~ | ✅ DONE. NotificationBell (badge + dropdown), SlaNotificationListPage (tabela, filteri, pagination, dismiss), slaNotificationService, tipovi. |
| G-17 | ~~Email delivery za zakazane izveštaje~~ | ~~4-6h~~ | ~~SREDNJI~~ | ✅ DONE (2026-03-12). Detalji u "Završeno" sekciji. |

---

## UI Alignment (oci-ui pattern usklađivanje) — ✅ DONE (2026-03-13)

Usklađivanje `oci-sla-management-poc-ui` sa `oci-ui` code patterns-om. Detaljan plan: `todo/sla-poc-ui-alignment.md`. Dokumentovani paterni: `oci-sla-management-poc-ui/docs/oci-ui-code-patterns.md`.

| # | Stavka | Status | Napomena |
|---|--------|--------|----------|
| A-01 | Folder layout (`components/`, `hooks/`, `pages/`, `services/`, `types/`, `widgets/`) | ✅ DONE | Struktura usklađena sa oci-ui |
| A-02 | Alias `@/` u tsconfig + vite.config | ✅ DONE | Path aliasi po oci-ui patternu |
| A-03 | Reusable hooks (`usePagination`) | ✅ DONE | Client-side pagination hook |
| A-05 | Sonner toast umesto `console.error`/`window.alert` | ✅ DONE | Toaster + toast integrisan |
| A-06 | Constants/enums fajl | ✅ DONE | `constants.ts` sa API rutama |
| A-07 | PageInfoButton komponenta | ✅ DONE | Po oci-ui patternu |
| A-08 | Widget pattern (page = thin wrapper, widget = self-contained) | ✅ DONE | 5 widgeta: SlaDefinitionsTable, BreachTable, ScheduleTable, StoredReportTable, NotificationTable |
| A-09 | NavDropdown komponenta | ✅ DONE | Dropdown sa hover+click, chevron, per-item opisi |
| A-10 | i18n (i18next + HttpBackend) | ✅ DONE | 2 jezika (cyril/latin), 3 namespace-a (common/sla/navbar), **100% stringova prevedeno** — sve stranice, widgeti, komponente, forme, dijalozi, chartovi. 30 TSX fajlova koristi useTranslation. |
| A-11b | TenantSelect usklađen sa oci-ui | ✅ DONE | Custom GroupedSelect dropdown vizuelno odgovara Mantine Select-u. Iste širine, grouping, check ikona, subscriptionID value. Isti API endpointi. |
| A-04 | Api object conversion | SKIP | Service pattern je OK, konverzija nije potrebna |

---

## Dependency Notes

- ~~**G-02** (PDF/CSV) mora pre email delivery za zakazane izveštaje~~ ✅ Oba implementirana
- **G-05** backend mora pre G-05 frontend (breach management)
- Sprint 1 stavke su međusobno nezavisne
- Sprint 4 stavke su međusobno nezavisne
