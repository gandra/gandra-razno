# SLA Backlog

> **Poslednje ažuriranje**: 2026-03-12

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
| G-06 | Email retry (Hybrid — Phase 1 + Phase 2) | 2026-03-12 | **Phase 1**: Inline exponential backoff u sva 4 MailerService implementacije (oci-api + oci-monitor). **Phase 2**: Scheduled cleanup — `EmailSendLog` entity + `EmailSendStatus` enum (oci-library), `EmailSendLogRepository` + `EmailSendLogService` + `EmailRetryScheduler` (oci-monitor). @SchedulerLock + SchedulerToggleService. `SlaNotificationService` prebaèen na EmailSendLogService (prvi consumer). Scheduled backoff: 5min→15min→45min→2h15min→6h (5 retries, ~9.5h). Flyway: dev V12, prod V6. |

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
| — | Email delivery za zakazane izveštaje | 4-6h | SREDNJI | TODO |

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

---

## Backlog (budući sprintovi)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-12b | Manual recomputation Phase 2 (dry-run, async batch, cancellation) | 8-12h | NIZAK | BACKLOG |
| G-16 | Notifikacije za bitne evente (delete SLA, breach acknowledge/resolve, schedule activate/deactivate, etc.) | 4-6h | SREDNJI | BACKLOG |

---

## Dependency Notes

- **G-02** (PDF/CSV) mora pre email delivery za zakazane izveštaje
- **G-05** backend mora pre G-05 frontend (breach management)
- Sprint 1 stavke su međusobno nezavisne
- Sprint 4 stavke su međusobno nezavisne
