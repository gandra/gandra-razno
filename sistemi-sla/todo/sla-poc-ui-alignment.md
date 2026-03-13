# Uskladjivanje oci-sla-management-poc-ui sa oci-ui

> **Datum**: 2026-03-13
> **Status**: Elaboracija — ceka odobrenje pre implementacije
> **Cilj**: Prilagoditi strukturu koda u POC UI projektu da bude sto slicniji oci-ui patternu, kako bi UI tim lakse preneo SLA features u produkcioni oci-ui
>
> **Princip**: Gde god je moguce, **kopirati kod i komponente direktno iz oci-ui** i prilagoditi za shadcn/ui/Tailwind stack. Cilj je da struktura fajlova, naming, import paterni i logika budu 1:1 sa oci-ui — razlikuje se samo UI framework (shadcn umesto Mantine).

---

## Sadrzaj

1. [Komparativna analiza](#1-komparativna-analiza)
2. [Detaljna matrica razlika](#2-detaljna-matrica-razlika)
3. [Predlozi uskladjivanja po kategorijama](#3-predlozi-uskladjivanja)
4. [Prioritetna matrica](#4-prioritetna-matrica)
5. [Implementacioni plan](#5-implementacioni-plan)

---

## 1. Komparativna analiza

### 1.1 Tehnicki stack

| Aspekt | oci-ui | oci-sla-poc-ui | Razlika |
|--------|--------|----------------|---------|
| **React** | 18.3.1 | 19.1.1 | POC noviji — OK |
| **TypeScript** | 5.5.4 | 5.9.3 | POC noviji — OK |
| **Vite** | 5.3.5 | 7.1.7 | POC noviji — OK |
| **Package manager** | pnpm 9.7.0 | npm | Razliciti |
| **UI framework** | Mantine 7.x | shadcn/ui (Radix + Tailwind) | **KRITICNA RAZLIKA** |
| **Tabele** | Mantine React Table 2.0 | Rucno gradjen HTML + Tailwind | **VELIKA RAZLIKA** |
| **Forme** | @mantine/form + Zod (mantine-form-zod-resolver) | react-hook-form + Zod (@hookform/resolvers) | Razlicite biblioteke |
| **State (auth)** | Zustand 4.5 + zustand-x 3.0 | Zustand 5.0 | Slicno |
| **State (server)** | TanStack React Query 5.51 | TanStack React Query 5.90 | Slicno — OK |
| **HTTP** | Axios 1.7 | Axios 1.13 | Slicno — OK |
| **Routing** | react-router-dom 6.25 | react-router-dom 7.9 | POC noviji |
| **i18n** | i18next + HttpBackend (full) | **Nema** — hardcoded stringovi | **VELIKA RAZLIKA** |
| **Ikone** | — (Mantine built-in) | Lucide React | Razliciti |
| **Chartovi** | Chart.js + react-chartjs-2 | Chart.js + react-chartjs-2 | Isto |
| **Date** | date-fns 2.30 | date-fns 4.1 | POC noviji — OK |
| **CSS** | Mantine + Tailwind (hybrid) | Tailwind + shadcn/ui | Razliciti |
| **Toast** | Sonner + custom use-toast | **Nema** — window.alert / console | **RAZLIKA** |
| **Linting** | ESLint + Prettier + Husky | ESLint (basic) | POC slabiji |
| **Error tracking** | Sentry | Nema | POC nema |
| **Path alias** | `@` → `./src` | Nema | POC nema |

### 1.2 Struktura direktorijuma

```
oci-ui/src/                              oci-sla-poc-ui/src/
─────────────                            ──────────────────
├── assets/                              ├── assets/
├── components/                          ├── components/
│   ├── PermissionControl.tsx            │   ├── charts/
│   └── ui/                              │   ├── sla/
│       ├── use-toast.ts                 │   ├── ui/         (shadcn/ui)
│       ├── sonner.tsx                   │   ├── CronExpressionBuilder.tsx
│       ├── card.tsx                     │   ├── NotificationBell.tsx
│       └── enum-select.tsx              │   ├── PageInfoButton.tsx
│                                        │   ├── ProtectedRoute.tsx
├── config/                              │   ├── SearchableSelect.tsx
│                                        │   ├── SlaNavigation.tsx
├── constants/                           │   └── SlaReportDisplay.tsx
│   ├── index.ts                         │
│   ├── routes.ts    ← ODVOJENO         ├── data/
│   ├── currencies.ts                    │   └── endpointInfo.ts
│   └── entity-sidebar-links.ts         │
│                                        ├── hooks/           ← FLAT
├── context/                             │   ├── useAuth.ts
│   ├── TenantContext.tsx                │   ├── useCompartments.ts
│   ├── OrganizationContext.tsx          │   ├── useLoginMutation.ts
│   └── SubscriptionContext.tsx          │   ├── useMetricNames.ts
│                                        │   └── useSlaFeatures.tsx
├── hooks/                               │
│   ├── useAuth.ts                       ├── lib/
│   ├── useTForm.ts                      │   ├── axiosInstance.ts
│   ├── useMRT.ts                        │   └── utils.ts
│   └── api/          ← PODDIR          │
│       ├── queryKeys.ts                 ├── pages/           ← FLAT
│       ├── useFetch*Query.ts            │   ├── SlaListPage.tsx
│       └── useCreate*Mutation.ts        │   └── ...
│                                        │
├── lib/                                 ├── services/        ← NE POSTOJI u oci-ui
│   ├── api/          ← PODDIR          │   ├── slaDefinitionService.ts
│   │   ├── axiosInstance.ts             │   └── ...
│   │   ├── api.ts    ← CENTRALIZOVANO  │
│   │   └── dto.ts    ← SVI DTO-ovi     ├── types/           ← SLICNO
│   ├── queryClient/                     │   ├── sla.types.ts
│   │   ├── queryClient.ts              │   └── ...
│   │   └── idb-persister.ts            │
│   ├── utils.ts                         ├── constants.ts     ← JEDAN FAJL
│   ├── forms.ts                         ├── App.tsx          ← ROUTING OVDE
│   └── dateUtils.ts                     ├── main.tsx
│                                        └── index.css
├── pages/
│   ├── DashboardPage.tsx
│   └── ...
│
├── types/
│   ├── util.ts
│   ├── i18next.d.ts
│   └── tanstack-table.d.ts
│
├── widgets/          ← NE POSTOJI u POC
│   ├── Navbar/
│   ├── Footer/
│   ├── OrganizationsTable/
│   │   ├── OrganizationsTable.tsx
│   │   └── columns.tsx
│   └── OrganizationDetails/
│
├── App.tsx            ← PROVIDERS
├── Pages.tsx          ← ROUTING ODVOJENO
├── Layout.tsx         ← LAYOUT ODVOJEN
├── i18n.ts            ← i18n CONFIG
└── main.tsx
```

### 1.3 Kljucne arhitekturne razlike

| Pattern | oci-ui | oci-sla-poc-ui |
|---------|--------|----------------|
| **API pozivi** | Centralni `Api` objekat (`lib/api/api.ts`) sa namespaces | Individualni service fajlovi (`services/*.ts`) |
| **Query keys** | Factory pattern (`hooks/api/queryKeys.ts`) | Inline nizovi u hookovima |
| **Query hooks** | Genericki sa `props` spreading, u `hooks/api/` | Pojedinacni hookovi u `hooks/` flat |
| **Mutation hooks** | Odvojeni fajlovi sa `queryClient.invalidateQueries` | Inline u komponentama |
| **Routing** | Odvojen `Pages.tsx` sa `Layout.tsx` wrapper | Sve u `App.tsx` |
| **Layout** | `Layout.tsx` sa `<Outlet />`, uslovni Navbar/Footer | `SlaNavigation` ubacen u svaku stranicu |
| **Toast/feedback** | Sonner + custom toast hook sa i18n | `window.alert` / `console.error` |
| **i18n** | Potpun — 10 namespace-a, 2 jezika, HttpBackend | Nema — hardcoded srpski |
| **Tabele** | Mantine React Table sa `useMRT` wrapper | Rucni HTML `<div>` grid sa Tailwind |
| **Forme** | `useTForm` (Mantine form + Zod + i18n errors) | `useForm` (react-hook-form + Zod) |
| **Error handling** | Globalni toast, typed error responses | Per-component, nekonzistentno |
| **Permissions** | `PermissionControl` wrapper + `Claim` enum | `ProtectedRoute` (samo auth check) |
| **Widgets** | Odvojeni `widgets/` dir (Table + Columns + Details) | Sve u `pages/` (monolitne stranice) |

---

## 2. Detaljna matrica razlika

### 2.1 Razlike koje TREBA uskladiti (olaksavaju tranziciju)

| # | Razlika | Impact na tranziciju | Effort | Rizik |
|---|---------|---------------------|--------|-------|
| **A-01** | Nema `@` path alias | Svi importi moraju biti relatvni → kod ruznji, teze premestanje | 15min | Nula |
| **A-02** | Routing u `App.tsx` umesto `Pages.tsx` + `Layout.tsx` | UI tim mora da prepravi routing | 1-2h | Nizak |
| **A-03** | Nema query keys factory | Duplirani stringovi, tesko invalidation management | 1-2h | Nizak |
| **A-04** | Service pattern umesto centralizovanog `Api` objekta | UI tim mora da prepravi sve API pozive | 2-3h | Srednji |
| **A-05** | Nema toast sistema | UI tim mora da zameni svaki alert/console.error | 1-2h | Nizak |
| **A-06** | `constants.ts` jedan fajl umesto `constants/` direktorijuma | Organizacija, razdvajanje routes od drugih konstanti | 30min | Nula |
| **A-07** | Hooks flat umesto `hooks/api/` poddirektorijuma | UI tim mora da reorganizuje hook fajlove | 30min | Nula |
| **A-08** | Nema widgets pattern (Table + Columns odvojeni) | Stranice monolitne, teze za ponovnu upotrebu | 4-6h | Srednji |
| **A-09** | Mutation inline umesto odvojenih mutation hookova | Nekonzistentno sa oci-ui patternom | 2-3h | Nizak |
| **A-10** | Nema i18n infrastructure | **Najveci gap** — UI tim mora sve stringove prebaciti | 3-4h (setup) | Nizak |
| **A-11** | Nema Tenant selector u header-u | UI tim mora da doda ceo context/provider/selector pattern | 3-4h | Srednji |

### 2.2 Razlike koje NE TREBA dirati (razliciti stackovi, resi se pri tranziciji)

| # | Razlika | Razlog zasto ne dirati |
|---|---------|----------------------|
| **B-01** | Mantine vs shadcn/ui | Kompletna UI zamena — nema smisla u POC-u. UI tim ce direktno prepisivati u Mantine. |
| **B-02** | Mantine React Table vs rucne tabele | Zavisi od B-01. Tabele se prepisuju kad se prebace na Mantine. |
| **B-03** | @mantine/form vs react-hook-form | Zavisi od B-01. Forme se prepisuju sa UI framework-om. |
| **B-04** | useTForm / useMRT wrapperi | Specificni za Mantine — ne mogu se portovati. |
| **B-05** | Zustand 4 + zustand-x vs Zustand 5 | Minorna razlika, trivijalno za migraciju. |
| **B-06** | pnpm vs npm | Trivijalno, UI tim vec koristi pnpm. |
| **B-07** | PermissionControl (claims) | SLA POC nema role management — dodaje se pri integraciji. |
| **B-08** | Sentry integracija | Dodaje se pri integraciji u oci-ui. |
| **B-09** | Husky / lint-staged | Dev tooling — ne utice na kod. |
| **B-10** | React 18 vs 19 | Tranzicija ide u oci-ui React 18 — nema potrebe za downgrade. |

---

## 3. Predlozi uskladjivanja

### A-01: Path alias `@` → `./src`

**Trenutno** (POC):
```typescript
import { slaDefinitionService } from '../services/slaDefinitionService'
import { SlaDefinitionDto } from '../types/sla.types'
```

**Ciljno** (oci-ui pattern):
```typescript
import { slaDefinitionService } from '@/services/slaDefinitionService'
import { SlaDefinitionDto } from '@/types/sla.types'
```

**Izmene**:
1. `vite.config.ts` — dodati `resolve.alias`
2. `tsconfig.app.json` — dodati `paths`
3. Bulk replace svih importa (regex)

**Effort**: 15 min
**Rizik**: Nula — potpuno automatizovano

---

### A-02: Routing — Pages.tsx + Layout.tsx

**Trenutno** (POC): Sve u `App.tsx` — routing, providers, layout.

**Ciljno** (oci-ui pattern):

```
App.tsx          → Samo providers (QueryClient, SlaFeaturesProvider, BrowserRouter)
Pages.tsx        → Sva route definicija (Routes, Route, Navigate)
Layout.tsx       → Layout wrapper sa SlaNavigation i Outlet
```

**Prednosti**:
- Razdvajanje odgovornosti
- UI tim prepoznaje pattern iz oci-ui
- Layout se menja na jednom mestu

**Effort**: 1-2h
**Rizik**: Nizak

---

### A-03: Query keys factory

**Trenutno** (POC) — inline u hookovima:
```typescript
queryKey: ['compartments', tenantId, organizationUuid],
queryKey: ['organizations'],
queryKey: ['sla-definitions'],
```

**Ciljno** (oci-ui pattern) — centralni factory:
```typescript
// hooks/api/queryKeys.ts
export const slaKeys = {
  all: () => ['sla-definitions'] as const,
  detail: (id: string) => ['sla-definitions', id] as const,
  active: () => ['sla-definitions', 'active'] as const,
}

export const slaReportKeys = {
  generate: (id: string) => ['sla-report', id] as const,
}

export const slaBreachKeys = {
  unacknowledged: () => ['sla-breaches', 'unacknowledged'] as const,
  unresolved: () => ['sla-breaches', 'unresolved'] as const,
}

// ... po domain-u
```

**Prednosti**:
- Jedno mesto za sve cache kljuceve
- Siguran `queryClient.invalidateQueries({ queryKey: slaKeys.all() })`
- UI tim odmah prepoznaje pattern

**Effort**: 1-2h
**Rizik**: Nizak

---

### A-04: Centralizovani Api objekat (opciono — diskusija)

**Trenutno** (POC) — service pattern:
```typescript
// services/slaDefinitionService.ts
export const slaDefinitionService = {
  async getAll(): Promise<SlaDefinitionDto[]> {
    const response = await api.get<SlaDefinitionDto[]>(ApiRoutes.Sla.Definitions())
    return response.data
  },
}
```

**oci-ui pattern** — centralni Api:
```typescript
// lib/api/api.ts
export const Api = {
  sla: {
    definitions: () => api.get<SlaDefinitionDto[]>(ApiRoutes.Sla.Definitions()),
    definition: (id: string) => api.get<SlaDefinitionDto>(ApiRoutes.Sla.DefinitionById(id)),
    create: (data: CreateSlaRequest) => api.post(ApiRoutes.Sla.CreateDefinition(), data),
  },
  slaReport: { ... },
  slaBreach: { ... },
}
```

**Analiza**:

| Kriterijum | Service pattern (POC) | Centralni Api (oci-ui) |
|-----------|----------------------|----------------------|
| Organizacija | Jasna — 1 fajl po domenu | Jasna — 1 objekat sa namespace-ovima |
| Tipovi | Ekplicitni return type | Response type na axios poziv |
| Reusability | Direktan import servisa | Direktan import Api objekta |
| Tranzicija | UI tim prepisuje u Api | UI tim kopira direktno |
| Effort za konverziju | 2-3h | — |
| Dodajna vrednost | Umerena | — |

**PREPORUKA**: Ovo je **diskutabilno**. Oba pristupa su validna. Service pattern je cak i citkiji. UI tim ce svakako prepisivati API pozive (drugi base URL, drugi auth pattern). **Predlazem da ostavimo service pattern ali dodamo komentar u svakom servisu koji mapira na buduce Api namespace**.

**Alternativa**: Dodati `lib/api/api.ts` kao tanak proxy koji re-exportuje service metode u oci-ui formatu. Time UI tim vidi poznati interfejs ali ne prepisujemo servise.

**Effort**: 0h (ostavi kako jeste) ili 2-3h (konvertuj)
**Preporuka**: Ostavi + dodaj komentare

---

### A-05: Toast sistem

**Trenutno** (POC): `window.alert()`, `console.error()`, inline error rendering

**Ciljno** (oci-ui pattern): Sonner toast + helper funkcije

**Implementacija**:
1. Dodati `sonner` dependency (vec je lightweight — 4KB)
2. Kreirati `components/ui/sonner.tsx` (Toaster wrapper)
3. Kreirati toast helper:
   ```typescript
   import { toast } from 'sonner'
   export const successToast = (message: string) => toast.success(message)
   export const errorToast = (message: string) => toast.error(message)
   ```
4. Dodati `<Toaster />` u App.tsx
5. Zameniti sve `window.alert` i `console.error` sa toast pozivima

**Effort**: 1-2h
**Rizik**: Nizak — dodaje biblioteku ali ne menja logiku

---

### A-06: Constants reorganizacija

**Trenutno** (POC): Sve u jednom `constants.ts` (ApiRoutes + LocalStorageKeys)

**Ciljno** (oci-ui pattern):
```
constants/
├── index.ts          → LocalStorageKeys, staleTime, itd.
└── routes.ts         → ApiRoutes (odvojeno od ostalih konstanti)
```

**Effort**: 30 min
**Rizik**: Nula

---

### A-07: Hooks reorganizacija

**Trenutno** (POC): Svi hookovi u `hooks/` flat

**Ciljno** (oci-ui pattern):
```
hooks/
├── useAuth.ts              → Auth hook (ostaje)
├── useSlaFeatures.tsx      → Feature flags (ostaje)
├── api/                    → NOVO poddirektorijum
│   ├── queryKeys.ts        → Factory (novo, A-03)
│   ├── useCompartments.ts  → Premesten
│   ├── useOrganizations.ts → Premesten
│   ├── useLoginMutation.ts → Premesten
│   └── ...
```

**Effort**: 30 min (samo premestanje + import update)
**Rizik**: Nula

---

### A-08: Widget pattern za tabele (opciono — diskusija)

**Trenutno** (POC): Monolitne stranice od 300-700 linija. Tabela, filteri, modali, CRUD — sve u jednom fajlu.

**oci-ui pattern**: Razdvojeno u widget direktorijum:
```
widgets/
├── SlaDefinitionsTable/
│   ├── SlaDefinitionsTable.tsx   → Tabela + akcije + modali
│   └── columns.tsx               → Definicija kolona
├── SlaBreachTable/
│   ├── SlaBreachTable.tsx
│   └── columns.tsx
```

**Analiza**:

| Za | Protiv |
|----|--------|
| Stranice postaju kratke i citke | 4-6h za refaktoring svih tabela |
| columns.tsx se lako prenosi | POC ima rucne HTML tabele, oci-ui koristi MRT — format kolona potpuno drugaciji |
| UI tim prepoznaje pattern | Kolone u MRT formatu se svakako prepisuju |

**PREPORUKA**: **Delimicno** — Izvuci tabelu i filtere u zasebne komponente (npr. `SlaDefinitionTable.tsx`), ali **NE** praviti `columns.tsx` u MRT formatu jer ce se ionako prepisivati. Cilj je da stranice budu krace i da tabele budu reusable, ne da kopiramo MRT API.

**Effort**: 4-6h (ako se radi) / 0h (ako se preskoci)
**Preporuka**: Srednji prioritet — radi ako ima vremena

---

### A-09: Mutation hook pattern

**Trenutno** (POC): Mutacije inline u komponentama:
```typescript
// U SlaListPage.tsx
const handleDeactivate = async () => {
  try {
    await slaDefinitionService.deactivate(sla.uuid)
    // refresh
  } catch (err) {
    console.error(err)
  }
}
```

**Ciljno** (oci-ui pattern): Odvojeni mutation hookovi:
```typescript
// hooks/api/useDeactivateSlaMutation.ts
export const useDeactivateSlaMutation = (options) => {
  const queryClient = useQueryClient()
  return useMutation({
    ...options,
    mutationFn: (uuid: string) => slaDefinitionService.deactivate(uuid),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: slaKeys.all() })
    },
  })
}
```

**Prednosti**:
- Cache invalidation na jednom mestu
- Konzistentno sa oci-ui
- Reusable iz vise komponenti

**Effort**: 2-3h (10+ mutacija u projektu)
**Rizik**: Nizak

---

### A-10: i18n infrastructure (setup only)

**Trenutno** (POC): Hardcoded srpski stringovi u JSX

**oci-ui**: Full i18next sa 10 namespace-a, HttpBackend, 2 jezika

**PREPORUKA**: **Ne prevoditi sve stringove**, ali postaviti infrastrukturu:

1. Dodati `i18next`, `react-i18next` dependencies
2. Kreirati `i18n.ts` sa minimalnom konfiguracijom (samo srpski)
3. Kreirati `public/locales/sr/` sa jednim namespace-om (`sla.json`)
4. Prebaciti **kljucne stringove** (naslove stranica, dugmad, kolone tabela) — ne sve
5. Hardcoded stringovi koji ostanu su OK za POC — UI tim ih prebacuje

**Zasto**:
- UI tim vidi da je i18n framework spreman
- Struktura prevoda je na mestu
- Prenosive su i18n key konvencije iz oci-ui

**Effort**: 3-4h (setup + ~30% stringova)
**Rizik**: Nizak
**Alternativa**: Preskoci potpuno — UI tim dodaje i18n pri integraciji. Ovo je biggest bang-for-buck ako se radi, ali i potpuno prihvatljivo ako se ne radi.

---

### A-11: Tenant selector u header-u (kao oci-ui)

**Screenshot reference**: `temp/oci-ui-header-tenants.png`

**oci-ui implementacija**:
- Header (Navbar) sadrzi `AccountMenu` → `TenantSelect` komponenta na desnoj strani
- `TenantSelect` prikazuje 2 Mantine `<Select>` u `flex gap-2`:
  - Tenant dropdown (grupiran po organizaciji, value = OCID, label = name)
  - Subscription dropdown (filtriran po tenant.organization.id)
- 3 React Context-a u hijerarhiji: `OrganizationContext` → `TenantContext` → `SubscriptionContext`
- Svaki context: fetch hook, localStorage persistence, auto-select first, grouping
- Subscription zavisi od Tenant-a (`enabled: isLoggedIn && !!tenant?.organization.id`)

**Kljucni oci-ui fajlovi za kopiranje**:

| Fajl | Lokacija u oci-ui | Opis |
|------|-------------------|------|
| `TenantContext.tsx` | `src/context/TenantContext.tsx` | Fetch tenanti, grupiraj po org, localStorage persist |
| `OrganizationContext.tsx` | `src/context/OrganizationContext.tsx` | Fetch org-e, localStorage persist |
| `SubscriptionContext.tsx` | `src/context/SubscriptionContext.tsx` | Fetch subskripcije filtrirane po tenant org |
| `TenantSelect.tsx` | `src/widgets/TenantSelect/TenantSelect.tsx` | Dual select (tenant + subscription) |
| `AccountMenu.tsx` | `src/widgets/Navbar/AccountMenu.tsx` | Desna strana headera: tenant + lang + avatar |
| `Navbar.tsx` | `src/widgets/Navbar/Navbar.tsx` | Wrapper: logo + NavMenu + AccountMenu |
| `NavMenu.tsx` | `src/widgets/Navbar/NavMenu.tsx` | Navigation items sa dropdownima |
| `Layout.tsx` | `src/Layout.tsx` | Layout sa Navbar/Footer + Outlet |

**Sta kopiramo za POC (prilagodjeno za shadcn/ui stack)**:

```
KREIRANJE (novi fajlovi):
  src/context/
  ├── TenantContext.tsx      ← kopija iz oci-ui, prilagodjena
  ├── OrganizationContext.tsx ← kopija iz oci-ui, prilagodjena
  └── SubscriptionContext.tsx ← kopija iz oci-ui, prilagodjena

  src/components/
  └── TenantSelect.tsx       ← shadcn/ui Select umesto Mantine Select

IZMENA (postojeci fajlovi):
  src/components/SlaNavigation.tsx  ← dodati TenantSelect u desnu stranu headera
  src/hooks/useAuth.ts              ← dodati useFetchMeQuery pattern (opciono)
  src/constants.ts                  ← dodati LocalStorageKeys za tenant/org/subscription
```

**Kljucna razlika u POC-u**:
- oci-ui koristi **Mantine `<Select>`** sa `ComboboxData` grouping API
- POC koristi **shadcn/ui `<Select>`** (Radix UI) — nema native grouping
- Resenje: koristiti shadcn/ui `<SelectGroup>` sa `<SelectLabel>` za grouping, ili koristiti vec postojecu `SearchableSelect` komponentu

**Kako to izgleda u POC header-u (wireframe)**:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ [SLA icon] SLA Management   [SLA ▼] [Notifications]    Tenant [____▼] [___▼]  │
│                                                          🔔  [Logout]          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                                           ↑         ↑
                                                      Tenant     Subscription
                                                      Select      Select
```

**Provider hijerarhija u App.tsx (ista kao oci-ui)**:

```tsx
<QueryClientProvider client={queryClient}>
  <OrganizationContextProvider>
    <TenantContextProvider>
      <SubscriptionContextProvider>
        <SlaFeaturesProvider>
          <Pages />      {/* routing */}
        </SlaFeaturesProvider>
      </SubscriptionContextProvider>
    </TenantContextProvider>
  </OrganizationContextProvider>
  <Toaster />
</QueryClientProvider>
```

**API endpointi potrebni za context-e**:
- `GET /codebook/organizations` — vec postoji u POC-u (organizationService)
- `GET /codebook/tenants` ili ekvivalent — **PROVERITI da li backend ima tenant list endpoint**
- `GET /codebook/subscriptions` ili ekvivalent — **PROVERITI da li backend ima subscription endpoint**

**VAZNO**: Ako backend nema dedicirane tenant/subscription list endpointe, mozemo:
1. Koristiti samo OrganizationContext (organizacije su vec dostupne)
2. Tenant i Subscription selektore dodati kad backend bude spreman
3. Ili: dodati samo Organization selector (1 dropdown) umesto punog tenant+subscription pattern-a

**Effort**: 3-4h (context-i + TenantSelect + header integracija)
**Rizik**: Srednji — zavisi od backend endpoint dostupnosti
**Preporuka**: Implementirati barem OrganizationContext + dropdown. Tenant + Subscription dodati ako endpointi postoje.

#### Kako tenant/subscription selekcija utice na ponasanje aplikacije u oci-ui

**Pattern u oci-ui**: Svaka stranica koja prikazuje podatke koristi `useTenantContext()` i/ili `useSubscriptionContext()` da dobije izabranu vrednost, pa je prosledi u API pozive:

```typescript
// DashboardPage.tsx, MonitorPage.tsx, BillingPage.tsx, itd.
const { tenant } = useTenantContext()
const { subscription } = useSubscriptionContext()

// Query koristi tenant.id / tenant.ocid kao parametar
const { data } = useFetchSomething({
  params: { tenantocid: tenant?.ocid, subscriptionid: subscription?.subscriptionID },
  enabled: !!tenant,  // query ne ide dok tenant nije izabran
})
```

**Stranice koje koriste tenant u oci-ui**:
| Stranica | Koristi tenant | Koristi subscription | Kako |
|----------|---------------|---------------------|------|
| DashboardPage | Da | Da | Svi chartovi filtrirani po tenant+subscription |
| MonitorPage | Da | Ne | Metrike za izabrani tenant |
| BillingPage | Da | Da | Troskovi za tenant+subscription |
| BillingReportPage | Da | Da | Usage report |
| ResourcesPage | Da | Ne | Resursi za izabrani tenant |
| MetricNotificationListPage | Da | Da | Notifikacije za tenant |
| BudgetNotificationsPage | Da | Da | Budget notifikacije |
| CompartmentNotificationsPage | Da | Da | Compartment notifikacije |
| SCNotificationPage | Ne | Da | SC notifikacije po subscription |
| OCIQueryListPage | Da | Ne | OCI upiti za tenant |

**Kad korisnik promeni tenant u dropdown-u**:
1. `TenantContext.setTenant(newTenantOcid)` → state se menja
2. `localStorage` se azurira (persist za refresh)
3. Sve komponente koje koriste `useTenantContext()` se re-renderuju
4. React Query hookovi dobijaju novi `queryKey` (sadrzi tenant ID) → cache miss → novi fetch
5. `SubscriptionContext` automatski re-filtrira subskripcije za novu organizaciju tenant-a
6. Podaci na stranici se osvezavaju za novog tenant-a

**Kad korisnik promeni subscription**:
1. `SubscriptionContext.setSubscription(newId)` → state se menja
2. Stranice koje koriste subscription se re-renderuju sa novim podacima

#### Sta treba izmeniti u SLA POC-u da selekcija odrazi na podatke

**Trenutno stanje POC-a**:
- SLA definicije se ucitavaju BEZ tenant parametra — backend filtrira po JWT tokenu (user's organization)
- SlaFormPage koristi `formData.tenantId` za kaskadne dropdown-ove (Organization → Compartment → Resource → Metric)
- Ali `tenantId` je manuelno izabran u formi, NIJE iz header dropdown-a

**Potrebne izmene za SLA POC**:

| # | Izmena | Opis | Fajlovi |
|---|--------|------|---------|
| 1 | **Kreirati OrganizationContext** | Fetch organizacije, persist izabranu, auto-select first | `src/context/OrganizationContext.tsx` |
| 2 | **Kreirati TenantContext** (ako endpoint postoji) | Fetch tenante za izabranu organizaciju | `src/context/TenantContext.tsx` |
| 3 | **Dodati TenantSelect u header** | Dropdown u SlaNavigation desna strana | `src/components/TenantSelect.tsx`, `SlaNavigation.tsx` |
| 4 | **Wrap App sa Context providerima** | Isti pattern kao oci-ui | `App.tsx` |
| 5 | **SlaListPage — filtriranje po organizaciji** | `useOrganizationContext()` → prosledi u API | `SlaListPage.tsx`, `slaDefinitionService.ts` |
| 6 | **SlaFormPage — pre-popuni organizaciju** | Umesto rucnog biranja u formi, koristi iz context-a | `SlaFormPage.tsx` |
| 7 | **SlaBreachListPage — filtriranje** | Breach-evi za izabranu organizaciju | `SlaBreachListPage.tsx` |
| 8 | **SlaNotificationListPage — filtriranje** | Notifikacije za izabranu organizaciju | `SlaNotificationListPage.tsx` |
| 9 | **StoredSlaReportListPage — filtriranje** | Stored reporti za izabranu organizaciju | `StoredSlaReportListPage.tsx` |
| 10 | **SlaReportScheduleListPage — filtriranje** | Scheduli za izabranu organizaciju | `SlaReportScheduleListPage.tsx` |

**Kljucno pitanje**: Da li backend SLA API-ji prihvataju `organizationId` / `tenantId` kao query parametar?

- Ako **DA** → prosleđujemo iz context-a u svaki API poziv, podaci se filtriraju
- Ako **NE** (backend filtrira po JWT) → dropdown je informativan (prikazuje koja org je korisnikova), ali ne menja podatke

**Scenario A (backend podrzava filter)**:
```typescript
// SlaListPage.tsx
const { organization } = useOrganizationContext()

const { data: definitions } = useQuery({
  queryKey: ['sla-definitions', organization?.id],  // ← org u key-u
  queryFn: () => slaDefinitionService.getAll({ organizationId: organization?.id }),
  enabled: !!organization,
})
```

**Scenario B (backend filtrira po JWT, dropdown informativan)**:
```typescript
// SlaListPage.tsx - podaci se ne menjaju, ali:
// 1. Header prikazuje korisnikovu organizaciju (UX)
// 2. SlaFormPage koristi organization.id umesto manuelnog biranja
// 3. Kad se integruje u oci-ui, pattern je vec spreman za Scenario A

const { organization } = useOrganizationContext()
// organization se koristi za display i za pre-popunjavanje formi
```

**Preporuka**: Implementirati **Scenario B** za sada (informativan dropdown + pre-popunjavanje formi), sa strukturom spremnom za **Scenario A** kad backend dobije filter parametre. Ovo je isti pristup koji oci-ui koristi — context pruza vrednost, stranice odlucuju kako da je koriste.

**Cascading efekat u SlaFormPage (vec postoji, treba povezati sa context-om)**:
```
[Header: Organization ▼]  ←── iz OrganizationContext (automatski)
         │
         ▼
[Form Step 2: Compartment ▼]  ←── filtriran po organization.id
         │
         ▼
[Form Step 2: Resource ▼]     ←── filtriran po compartment
         │
         ▼
[Form Step 2: Metric ▼]      ←── filtriran po resource/namespace
```

Trenutno `tenantId` se bira rucno u formi (Step 1). Sa context-om, automatski se popunjava iz header-a — korisnik ne mora rucno da bira organizaciju svaki put.

---

### Generalni princip: Kopiranje koda iz oci-ui

Za SVE stavke (A-01 do A-11), princip implementacije je:

1. **Pronadji originalan fajl u oci-ui**
2. **Kopiraj strukturu, naming i logiku 1:1**
3. **Zameni samo UI framework pozive** (Mantine → shadcn/ui + Tailwind):
   - `<Select>` (Mantine) → `<Select>` (shadcn/ui Radix)
   - `<TextInput>` → `<Input>`
   - `<Button>` → `<Button>`
   - `<Menu>` → custom dropdown (vec postoji `NavDropdown`)
   - `<Modal>` → `<Dialog>` (shadcn/ui)
   - `useDisclosure()` (Mantine hook) → `useState(false)`
   - `useTForm()` → `useForm()` (react-hook-form)
4. **Zadrzi iste nazive fajlova, hookova, konteksta, tipova**
5. **Zadrzi isti import pattern** (`@/` aliasi, organizacija po direktorijumima)

**Primer**: `TenantContext.tsx` iz oci-ui se kopira skoro 1:1 — jedina razlika je sto se `ComboboxData` tip (Mantine) zamenjuje prostim `{ group: string, items: { value: string, label: string }[] }` tipom.

**Primer**: `Layout.tsx` iz oci-ui se kopira 1:1 — `<Navbar />`, `<Outlet />`, `<Footer />`. Footer je trivijalan (`Developed by: Sistemi`).

**Primer**: `queryKeys.ts` iz oci-ui se kopira 1:1 — ista factory struktura, isti naming.

Ovaj princip maksimalno olaksava posao UI tima — kad otvore POC kod, prepoznaju svaki fajl, svaki pattern, svaku konvenciju.

---

## 4. Prioritetna matrica

```
              VISOK IMPACT NA TRANZICIJU
                        │
          A-03           │  A-10       A-11
     (queryKeys)         │  (i18n)  (tenant select)
          A-02           │
     (Pages/Layout)      │
          A-05           │  A-08
     (toast)             │  (widgets)
                         │
  ────────────────────── ┼ ────────────────────── EFFORT
                         │
          A-01           │  A-09
     (path alias)        │  (mutations)
          A-06           │  A-04
     (constants/)        │  (Api objekat)
          A-07           │
     (hooks/api/)        │
                         │
              NIZAK IMPACT NA TRANZICIJU
```

### Preporuceni redosled

| Prioritet | ID | Zadatak | Effort | Obrazlozenje |
|-----------|-----|---------|--------|-------------|
| 1 (must) | A-01 | ~~Path alias `@`~~ | ~~15min~~ | ✅ **DONE** (2026-03-13): vite.config.ts + tsconfig.app.json + 153 importa zamenjeno |
| 2 (must) | A-06 | ~~Constants reorganizacija~~ | ~~30min~~ | ✅ **DONE** (2026-03-13): constants/ dir sa index.ts + routes.ts, svi importi rade |
| 3 (must) | A-07 | ~~Hooks reorganizacija (hooks/api/)~~ | ~~30min~~ | ✅ **DONE** (2026-03-13): 9 API hookova premesteno u hooks/api/, useAuth i useSlaFeatures ostaju u hooks/ |
| 4 (must) | A-03 | ~~Query keys factory~~ | ~~1-2h~~ | ✅ **DONE** (2026-03-13): hooks/api/queryKeys.ts sa 11 key factory-ja, svi hookovi koriste factory |
| 5 (must) | A-02 | ~~Pages.tsx + Layout.tsx~~ | ~~1-2h~~ | ✅ **DONE** (2026-03-13): App=providers, Pages=routes, Layout=SlaNavigation+Outlet+Footer, SlaNavigation uklonjeno iz 9 stranica |
| 6 (must) | A-11 | ~~Tenant/Org selector u header~~ | ~~3-4h~~ | ✅ **DONE** (2026-03-13): 3 context-a (Org/Tenant/Sub), TenantSelect u header, servisi, hookovi, tipovi, localStorage persist |
| 7 (should) | A-05 | ~~Toast sistem (Sonner)~~ | ~~1-2h~~ | ✅ **DONE** (2026-03-13): sonner instaliran, Toaster u App.tsx, sve alert() zamenjene sa toast.success/error |
| 8 (should) | A-09 | ~~Mutation hookovi~~ | ~~2-3h~~ | ✅ **DONE** (2026-03-13): 6 mutation hook fajlova (17 hookova) u hooks/api/. Integracija u stranice kad se reads prebace na useQuery |
| 9 (nice) | A-10 | ~~i18n setup~~ | ~~3-4h~~ | ✅ **DONE** (2026-03-13): i18next + HttpBackend, 2 jezika (cyril/latin), 3 namespace-a (common/sla/navbar), SlaNavigation potpuno prevedena |
| 10 (nice) | A-08 | ~~Widget pattern (tabele)~~ | ~~4-6h~~ | ✅ **DONE** (2026-03-13): 5 widgeta ekstrahovano (SlaDefinitionsTable, BreachTable, ScheduleTable, StoredReportTable, NotificationTable). Stranice su tanak wrapper (header + widget) |
| 11 (skip) | A-04 | Api objekat konverzija | 2-3h | Service pattern je OK |

---

## 5. Implementacioni plan

### Faza 1: Quick wins (1-2h)

Trivijalne promene koje odmah priblizavaju strukturu.

```
A-01: Path alias
A-06: constants/ direktorijum
A-07: hooks/api/ poddirektorijum
```

**Rezultat**: Struktura direktorijuma izgleda slicnije oci-ui. Importi su cistiji.

### Faza 2: Arhitekturne promene (3-5h)

Promene koje menjaju nacin rada ali bez rizika.

```
A-03: Query keys factory
A-02: Pages.tsx + Layout.tsx (+ Footer)
A-05: Toast sistem (Sonner)
```

**Rezultat**: Routing, cache keys i user feedback prate oci-ui pattern.

### Faza 3: Tenant/Org context + Header (3-4h)

Kljucna faza za vizuelni i strukturni paritet sa oci-ui header-om.

```
A-11: OrganizationContext + TenantContext + TenantSelect u header
      - Kopirati context pattern iz oci-ui (1:1 struktura)
      - Dodati shadcn/ui Select umesto Mantine Select
      - Wrap App sa context providerima (isti redosled kao oci-ui)
      - Povezati SlaFormPage da koristi org iz context-a umesto rucnog biranja
      - Svi ostali list page-ovi: prepared za filtriranje (queryKey sadrzi org.id)
```

**Rezultat**: Header izgleda i ponasa se kao oci-ui. Organizacija se bira jednom u header-u, odrazi se na celu aplikaciju.

### Faza 4: Konzistentnost (2-3h)

Uskladjivanje hook patterna sa oci-ui.

```
A-09: Mutation hookovi (odvojeni fajlovi)
```

**Rezultat**: Svi API hookovi (query + mutation) prate oci-ui konvenciju.

### Faza 5: Opciono (3-6h)

Radi se samo ako ima vremena i potrebe.

```
A-10: i18n setup (infrastruktura + ~30% stringova)
A-08: Widget pattern (izvlacenje tabela iz stranica)
```

**Rezultat**: Kompletna uskladjenost sa oci-ui patternom.

### Ukupna procena

```
Faza 1 (Quick wins):              ~1-2h
Faza 2 (Arhitektura):             ~3-5h
Faza 3 (Tenant/Org context):      ~3-4h
Faza 4 (Konzistentnost):          ~2-3h
Faza 5 (Opciono):                 ~3-6h (A-10) + 4-6h (A-08)
──────────────────────────────────────────
Must + Should:                     9-14h
Sa opcionalnim:                   16-26h
```

---

## Napomene

- **Mantine migracija se NE radi** — to je posao UI tima pri integraciji. POC ostaje na shadcn/ui.
- **React Hook Form ostaje** — konverzija na @mantine/form je posao UI tima.
- **Tabele ostaju rucne** — konverzija na MRT je posao UI tima.
- **Cilj je da UI tim prepozna strukturu** — fajlovi na pravim mestima, hookovi po konvenciji, routing razdvojen.
- Service fajlovi su cisti i dobro organizovani — UI tim ih lako konvertuje u Api namespace.
- Tipovi u `types/` su vec u dobrom formatu — mapiraju 1:1 na backend DTO-ove.

### Sta UI tim dobija od uskladjivanja

| Pre uskladjivanja | Posle uskladjivanja |
|-------------------|-------------------|
| Importi sa `../../` | Importi sa `@/` |
| Routing u App.tsx | Routing u Pages.tsx + Layout |
| Inline query keys | Factory u queryKeys.ts |
| window.alert | Sonner toast |
| Flat hooks/ | hooks/api/ poddirektorijum |
| Jedan constants.ts | constants/ direktorijum |
| Inline mutacije | Odvojeni mutation hookovi |
| Nema tenant selectora u header-u | Tenant + Org dropdown kao u oci-ui |
| Rucno biranje org-e u formi | Auto-popunjavanje iz context-a |
| Nema context provider hijerarhije | Org → Tenant → Subscription context-i |
| Nema i18n infrastructure | i18next + HttpBackend, 2 jezika, 3 namespace-a, SlaNavigation prevedena |
| Monolitne stranice (300-870 linija) | widgets/ dir sa self-contained tabelama, stranice su tanak wrapper |

UI tim pri integraciji treba samo:
1. Kopira `pages/`, `hooks/api/`, `types/`, `services/`, `context/`
2. Zameni shadcn/ui sa Mantine komponentama u JSX
3. Zameni react-hook-form sa @mantine/form u formama
4. Zameni rucne tabele sa Mantine React Table
5. ~~Prevede hardcoded stringove u i18n kljuceve~~ → i18n infrastruktura je vec na mestu, treba samo dodati preostale kljuceve za stranice
6. Doda PermissionControl gde treba
7. Context providers su **vec na mestu** — samo zamene shadcn Select sa Mantine Select u TenantSelect
8. i18n namespace-i i prevodi za navbar su **vec na mestu** — dodaju namespace-e za ostale stranice
