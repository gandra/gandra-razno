# SLA Backlog

> **Poslednje ažuriranje**: 2026-03-11

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

---

## Sprint 1: Kritični quick-fix (~2 dana)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-03 | ~~Authorization check u SlaReportService~~ | ~~2h~~ | ~~KRITIČAN~~ | ✅ DONE |
| G-04 | ~~Konfigurabilni monitoring interval~~ | ~~1h~~ | ~~KRITIČAN~~ | ✅ DONE |
| G-09 | ~~SecurityContext za audit username~~ | ~~1h~~ | ~~NIZAK~~ | ✅ DONE |
| G-06 | Email retry (inline exponential backoff) | 2-3h | VISOK | TODO |
| G-08 | ~~Delete/Deactivate SLA u UI~~ | ~~2-3h~~ | ~~SREDNJI~~ | ✅ DONE |

---

## Sprint 2: Report Pipeline (~1-2 nedelje)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-02 | ~~PDF/CSV generisanje (StoredSlaReportManagementService)~~ | ~~8-12h~~ | ~~KRITIČAN~~ | ✅ DONE |
| G-15 | Stored Report management UI | 4-6h | SREDNJI | TODO |
| — | Email delivery za zakazane izveštaje | 4-6h | SREDNJI | TODO |

---

## Sprint 3: Breach Management & Notifications (~1 nedelja)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-05 | ~~Breach Management API (simple PATCH endpoints)~~ | ~~4-6h~~ | ~~VISOK~~ | ✅ DONE |
| G-05 | Breach Management UI | 4-6h | VISOK | TODO |
| G-07 | Webhook notifikacije (simple POST + HMAC) | 2-3h | SREDNJI | TODO |

---

## Sprint 4: UX Polish (~1 nedelja)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-14 | SLA Timeline chart | 6-8h | SREDNJI | TODO |
| G-10 | ~~Pagination na listama~~ | ~~4h~~ | ~~NIZAK~~ | ✅ DONE |
| G-11 | Advanced filtering | 4-6h | NIZAK | TODO |
| G-12 | Manual recomputation improvements | 3-4h | NIZAK | TODO |
| G-13 | Cron expression builder | 4h | NIZAK | TODO |

---

## Dependency Notes

- **G-02** (PDF/CSV) mora pre email delivery za zakazane izveštaje
- **G-05** backend mora pre G-05 frontend (breach management)
- Sprint 1 stavke su međusobno nezavisne
- Sprint 4 stavke su međusobno nezavisne
