# SLA Backlog

> **Poslednje ažuriranje**: 2026-03-11

---

## Završeno

| # | Stavka | Datum | Napomena |
|---|--------|-------|----------|
| G-01 | Report Scheduler | 2026-03-11 | `SlaReportScheduler` + `SlaReportSchedulerService` + `SlaReportGenerationService` u oci-monitor. Cron 00:30, ShedLock, toggle via `sla.report.scheduled`. PDF/CSV gen. ostaje kao G-02. |

---

## Sprint 1: Kritični quick-fix (~2 dana)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-03 | Authorization check u SlaReportService | 2h | KRITIČAN | TODO |
| G-04 | Konfigurabilni monitoring interval | 1h | KRITIČAN | TODO |
| G-09 | SecurityContext za audit username | 1h | NIZAK | TODO |
| G-06 | Email retry (inline exponential backoff) | 2-3h | VISOK | TODO |
| G-08 | Delete/Deactivate SLA u UI | 2-3h | SREDNJI | TODO |

---

## Sprint 2: Report Pipeline (~1-2 nedelje)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-02 | PDF/CSV generisanje (StoredSlaReportManagementService) | 8-12h | KRITIČAN | TODO |
| G-15 | Stored Report management UI | 4-6h | SREDNJI | TODO |
| — | Email delivery za zakazane izveštaje | 4-6h | SREDNJI | TODO |

---

## Sprint 3: Breach Management & Notifications (~1 nedelja)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-05 | Breach Management API (simple PATCH endpoints) | 4-6h | VISOK | TODO |
| G-05 | Breach Management UI | 4-6h | VISOK | TODO |
| G-07 | Webhook notifikacije (simple POST + HMAC) | 2-3h | SREDNJI | TODO |

---

## Sprint 4: UX Polish (~1 nedelja)

| # | Stavka | Effort | Prioritet | Status |
|---|--------|--------|-----------|--------|
| G-14 | SLA Timeline chart | 6-8h | SREDNJI | TODO |
| G-10 | Pagination na listama | 4h | NIZAK | TODO |
| G-11 | Advanced filtering | 4-6h | NIZAK | TODO |
| G-12 | Manual recomputation improvements | 3-4h | NIZAK | TODO |
| G-13 | Cron expression builder | 4h | NIZAK | TODO |

---

## Dependency Notes

- **G-02** (PDF/CSV) mora pre email delivery za zakazane izveštaje
- **G-05** backend mora pre G-05 frontend (breach management)
- Sprint 1 stavke su međusobno nezavisne
- Sprint 4 stavke su međusobno nezavisne
