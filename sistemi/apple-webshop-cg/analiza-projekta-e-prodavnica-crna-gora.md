# Analiza projekta: iCentar.me — Faza 1: Migracija WP → MedusaJS + Abacus ERP integracija

> **Datum:** 03.04.2026.
> **Klijent:** iCentar d.o.o. — Apple Premium Reseller, Crna Gora
> **Web:** https://icentar.me/
> **Cilj Faze 1:** Zamijeniti WordPress/WooCommerce sa MedusaJS v2, zadržati isti operativni tok
> **Fiskalizacija:** Odložena za Fazu 2 → vidi `fiskalizacija-crna-gora-faza2.md`

---

## 1. Trenutno stanje (AS-IS)

### 1.1. O klijentu

**iCentar** je prvi i jedini **Apple Premium Reseller (APR)** u Crnoj Gori, te **Apple Authorized Service Provider** (od 2012).

| Atribut | Detalji |
|---------|---------|
| **Djelatnost** | Prodaja Apple uređaja i opreme, servis |
| **Asortiman** | Mac, iPhone, iPad, Apple Watch, AirPods, dodaci (Apple + third-party: Epico, Next One) |
| **Procjena SKU-ova** | ~200-400 (uređaji × konfiguracije + dodaci) |
| **Valuta** | EUR |
| **Jezik sajta** | Crnogorski/srpski (latinica) |

**Lokacije:**

| Lokacija | Adresa | Radno vrijeme |
|----------|--------|---------------|
| **Podgorica** | BIG Fashion, Cetinjski put bb | Pon-Sub 10-22 |
| **Tivat** | Porto Montenegro — Boka Place | Pon-Sub 9-21 |
| **Servisni centar** | BIG Fashion, Podgorica | Pon-Pet 11-17 |

**Dostava:** Cijela CG, besplatna >200 EUR, kurir Monte Nomaks, PG max 2 dana, ostalo do 4.

**Načini plaćanja:**
- Kartice: Visa, Mastercard, Maestro (AllSecure / Hipotekarna Banka)
- Virman, NLB kredit (do 5.000 EUR), NLB rate (do 24), CKB Visa Shopping (do 24), Hipotekarna Premium (do 36 rata), Gotovina, Gift kartice

**Posebne pogodnosti:** EDU popusti, EYCA kartice, Tax-Free.

### 1.2. Trenutna platforma — WordPress + WooCommerce

- **CMS:** WordPress, **E-commerce:** WooCommerce
- **Payment gateway:** AllSecure (Hipotekarna Banka)
- **Kategorije:** Mac, iPhone, iPad, Watch, AirPods, Dodaci, Otvoreni uređaji, Servis, Gift Card, EDU

### 1.3. Nova platforma — MedusaJS v2 (već razvijeno)

Kod: `medusajs-e-store-app/`

**Backend (MedusaJS server):** `medusa_sistemi/sistemi_medusa/`

| Komponenta | Verzija / Detalji |
|------------|-------------------|
| MedusaJS Framework | v2.6.1 |
| Admin panel | @medusajs/admin 7.1.18 (standardni) |
| Baza | PostgreSQL + MikroORM 6 |
| Pretraga | Typesense |
| File storage | Lokalni filesystem (@medusajs/file-local) |

**Custom moduli (već implementirani):**
- `documents` — PDF fakture, B2B/B2C tipovi, 7 entiteta
- `legal` — pravna lica, tipovi kupaca
- `wishlist` — lista želja sa sharing-om
- `product-custom-attribute` — atributi po varijanti

**Storefront (frontend):** `medusa_sistemi/sistemi_medusa-storefront/`

| Komponenta | Verzija |
|------------|---------|
| **Next.js** | **16.2.1** |
| **React** | **19.2.4** |
| CSS | Tailwind CSS 3.4.17 |
| TypeScript | 5.3.2 |
| i18n | i18next + react-i18next |
| Payment | @stripe/react-stripe-js (Stripe integracija pripremljena) |
| UI | Radix UI komponente |
| Dev port | 8000 (Turbopack) |

**Plugini (zasebni repozitorijumi):**
- `medusa-documents/` — @sistem-i/medusa-customer-type plugin
- `medusa-wishlist/` — @sistem-i/medusa-wishlist plugin

> **Storefront je potpuno poznat** — Next.js 16 headless, komunicira sa MedusaJS backend-om putem @medusajs/js-sdk. Kolege iz dev tima su ga razvile i dostupne su za koordinaciju.

### 1.4. Trenutni operativni tok (KLJUČNO ZA FAZU 1)

> **Faza 1 = isti tok, novi webshop.** Backoffice ekipa nastavlja da radi ručno kao i do sada.

```
TRENUTNI TOK (WordPress):
1. Kupac naruči na icentar.me (WP/WooCommerce)
2. Narudžbina stiže u WP admin panel
3. Backoffice ekipa RUČNO:
   - Provjerava narudžbinu
   - Provjerava raspoloživost u Abacusu
   - Kreira račun/porudžbinu u Abacusu (ručno)
   - Fiskalizuje kroz Abacus POS (ručno)
   - Priprema paket za slanje
   - Kontaktira kurira (Monte Nomaks)
   - Ažurira status narudžbine u WP

FAZA 1 TOK (MedusaJS — isti, samo novi webshop):
1. Kupac naruči na icentar.me (MedusaJS)
2. Narudžbina stiže u MedusaJS admin panel
3. Backoffice ekipa RUČNO:
   - Provjerava narudžbinu u MedusaJS admin
   - Provjerava raspoloživost u Abacusu (ručno ili kroz sync)
   - Kreira račun/porudžbinu u Abacusu (ručno)
   - Fiskalizuje kroz Abacus POS (ručno — kao i do sada)
   - Priprema paket za slanje
   - Kontaktira kurira
   - Ažurira status narudžbine u MedusaJS admin
```

> **Razlika:** Samo webshop se mijenja (WP → MedusaJS). Backoffice tok ostaje isti. Fiskalizacija ostaje na Abacus POS-u (ručno, kao i do sada).

### 1.5. Abacus ERP — API mogućnosti

**Abacus ima REST API** — dokumentovano 10 endpoint-a. Za Fazu 1 koristimo minimalan set za sync proizvoda.

| # | Endpoint | Metoda | Opis | Faza 1 | Faza 2+ |
|---|----------|--------|------|--------|---------|
| 1 | `GetPartners` | GET | Lista partnera (kupaca) | — | ✅ Auto sync |
| 2 | **`getWorkUnits`** | GET | Lista magacina/lokacija | **✅ Inicijalno** | ✅ |
| 3 | `getPriceLists` | GET | Lista cijenovnika | — | ✅ B2B cijene |
| 4 | **`getItems`** | GET/POST | **Artikli, cijene, zalihe, slike, detalji** | **✅ Sync proizvoda** | ✅ Real-time |
| 5 | `postSale` | POST | Kreiranje porudžbine | — | ✅ Auto narudžbine |
| 6 | `getIncomingItems` | GET | Artikli u dolasku | — | ✅ "Uskoro" |
| 7 | `getOpenItems` | GET | Otvorene stavke partnera | — | ✅ B2B |
| 8 | `getPartnerBalanceDetailed` | GET | Finansijska kartica | — | ✅ B2B |
| 9 | `AddPartner` | POST | Kreiranje partnera | — | ✅ Auto registracija |
| 10 | `getPromotions` | GET | Promocije i akcije | — | ✅ Sync popusta |

**URL:** `http://api.bencomltd.com/{klijent}/Main/{funkcija}?token={token}&protocol=2.0`

**API format:** JSON. Response: `{ Data, Version, Error, ErrorDetails }`.

#### getItems — Najbitniji endpoint

```json
{
  "id_item": int,           // ID artikla (identity)
  "code": "string",         // šifra artikla
  "name": "string",         // naziv
  "ean": "string",          // EAN barkod
  "group": "string",        // grupa/kategorija
  "supplier_code": "string",// šifra dobavljača
  "manufacturer": "string", // proizvođač
  "price": decimal,         // cijena (iz cijenovnika)
  "price_rrp": decimal,     // maloprodajna cijena
  "discount": decimal,      // popust (procentualni)
  "image": ["string"],      // slike
  "description": "string",  // opis
  "quantity": decimal,      // količina na lageru U TRENUTKU UPITA
  "details": [              // varijante (boja, veličina...)
    { "type": "boja", "value": "plava" }
  ]
}
```

**Opcioni parametri:** `ids` (filter), `id_partner` (B2B cijene), `id_m` (magacin), `id_c` (cijenovnik).

> `getItems` sa `id_m` vraća **stanje zaliha za konkretan magacin u realnom vremenu**.

#### postSale — Za buduću automatizaciju (Faza 2+)

```json
{
  "order": {
    "id_partner": int, "note": "string",
    "items": [{ "id_item": int, "quantity": decimal, "price": decimal, "discount": decimal }]
  },
  "id_m": int
}
```

---

## 2. Ciljna arhitektura — Faza 1

### 2.1. Dijagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    KUPAC (Web / Mobile)                          │
│                    icentar.me (novi MedusaJS sajt)               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MedusaJS v2 E-PRODAVNICA                      │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Katalog  │  │  Korpa   │  │ Checkout │  │  Admin panel   │  │
│  │ proizvoda│  │  (Cart)  │  │ & Plaćanje│  │  (narudžbine)  │  │
│  └────┬─────┘  └──────────┘  └──────────┘  └───────┬────────┘  │
│       │                                             │           │
│  ┌────┴─────────────────────┐                       │           │
│  │  Abacus Sync Modul       │               Operater vidi      │
│  │  (getItems → proizvodi)  │               narudžbinu i       │
│  │  Scheduled: svakih 30min │               RUČNO obrađuje     │
│  └──────────┬───────────────┘               u Abacusu          │
│             │                                                    │
└─────────────┼────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────┐
│      ABACUS ERP          │        BACKOFFICE (RUČNO, kao do sada)
│   api.bencomltd.com      │        ┌──────────────────────────┐
│                          │        │ • Provjera narudžbine    │
│  getItems → proizvodi,   │        │ • Kreiranje u Abacusu    │
│  zalihe, cijene          │        │ • Fiskalizacija (POS)    │
│                          │        │ • Pakovanje + kurir      │
│  getWorkUnits → lokacije │        │ • Status update          │
│                          │        └──────────────────────────┘
│  Magacin Podgorica       │
│  Magacin Tivat           │
└──────────────────────────┘
```

### 2.2. Scope Faze 1 — šta radimo, šta NE radimo

| Komponenta | Faza 1 | Faza 2+ |
|------------|--------|---------|
| **Webshop** | ✅ MedusaJS zamjenjuje WP | — |
| **Katalog proizvoda** | ✅ Sync iz Abacusa (`getItems`) | Real-time sync |
| **Zalihe** | ✅ Sync iz Abacusa (`getItems` + `id_m`) | — |
| **Provjera zaliha na checkout** | ✅ Real-time `getItems` check prije potvrde | Rezervacija u Abacusu (ako podržava) |
| **Narudžbine → Abacus** | ❌ Ručno (operater) | ✅ Auto (`postSale`) |
| **Kupci → Abacus** | ❌ Ručno | ✅ Auto (`AddPartner`) |
| **Fiskalizacija** | ❌ Ručno (Abacus POS, kao do sada) | ✅ Automatska |
| **Plaćanje** | ✅ AllSecure (kartice) + COD | Rate, Gift kartice |
| **Email potvrda** | ✅ Osnovna potvrda narudžbine | Fiskalni e-račun |
| **Pretraga** | ✅ Typesense (već implementirano) | — |
| **Click & Collect** | ❌ | ✅ |
| **B2B/EDU** | ❌ | ✅ (`id_partner`) |
| **Wishlist** | ⚠️ Već implementirano, aktivirati ako jednostavno | — |
| **Promocije** | ❌ | ✅ (`getPromotions`) |

### 2.3. Zaštita od overselling-a — Real-time provjera zaliha na checkout

> **Problem koji rješavamo:** Kupac naruči iPhone 16 Pro, plati karticom, dobije potvrdu.
> Operater provjerava u Abacusu — nema ga na stanju. Mora zvati kupca i saopštiti mu lošu vijest.
> **Ovo je loše korisničko iskustvo i mora se izbjeći u Fazi 1.**

#### Strategija: CHECK na checkout + lokalna rezervacija + cleanup

```
KORAK 1: PERIODIČNI SYNC (pozadinski)
   Abacus getItems(id_m=PG) ──→ MedusaJS Inventory (Podgorica)
   Abacus getItems(id_m=TV) ──→ MedusaJS Inventory (Tivat)
   Frekvencija: svakih 15-30 min
   └─ Kupac vidi na sajtu: "Na stanju u Podgorici: 3, Na stanju u Tivtu: 1"

KORAK 2: REAL-TIME CHECK (na checkout, prije plaćanja)
   Kupac klikne "Završi kupovinu"
   └─→ MedusaJS poziva Abacus getItems(ids=[artikal1, artikal2], id_m=magacin)
   └─→ Za SVAKI artikal u korpi provjerava: quantity >= naručena količina?
   └─→ Ako SVE raspoloživo → nastavlja na plaćanje
   └─→ Ako NIJE raspoloživo → prikazuje poruku kupcu:
       "Nažalost, [artikal] trenutno nije dostupan. Molimo izmijenite narudžbinu."

KORAK 3: LOKALNA REZERVACIJA (nakon uspješnog check-a)
   └─→ MedusaJS kreira ReservationItem za svaki artikal
       (smanjuje raspoloživu količinu u MedusaJS-u, ali NE u Abacusu)
   └─→ Postavlja TTL: 15 minuta za završetak plaćanja

KORAK 4: PLAĆANJE
   └─→ AllSecure procesuira karticu
   └─→ Uspješno? → order.placed → email potvrda → operater preuzima
   └─→ Neuspješno? → MedusaJS AUTOMATSKI briše ReservationItem (kompenzacija)

KORAK 5: CLEANUP (pozadinski)
   └─→ Cron job svakih 5 min: briše ReservationItem starije od 15 min
       (za kupce koji su odustali, zatvorili browser, itd.)
```

#### Dijagram kompletnog toka

```
Kupac                    MedusaJS                         Abacus
  │                         │                                │
  │── "Završi kupovinu" ──→ │                                │
  │                         │── getItems(ids=[X,Y], id_m) ──→│
  │                         │←── quantity: X=3, Y=1 ─────────│
  │                         │                                │
  │                         │ Provjera: korpa vs stanje       │
  │                         │ X: treba 1, ima 3 ✅           │
  │                         │ Y: treba 1, ima 1 ✅           │
  │                         │                                │
  │                         │ Kreira ReservationItem          │
  │                         │ (X: -1, Y: -1 lokalno)         │
  │                         │                                │
  │←─ "Unesite podatke" ───│                                │
  │── Podaci + kartica ───→ │                                │
  │                         │── AllSecure: naplati ──→ [Bank] │
  │                         │←── OK ─────────────────────────│
  │                         │                                │
  │                         │ order.placed ✅                 │
  │←─ "Narudžbina OK!" ────│                                │
  │                         │                                │
  │                   Operater ručno kreira u Abacusu         │
```

#### Šta ako nešto pukne na pola procesa? — Recovery scenariji

**Scenario A: Abacus API nedostupan na checkout**

```
Kupac klikne "Završi kupovinu"
└─→ MedusaJS poziva getItems → Abacus ne odgovara (timeout / 500)
└─→ FALLBACK: MedusaJS koristi LOKALNE zalihe (iz zadnjeg sync-a)
└─→ Prikazuje upozorenje: "Raspoloživost provjerena prije X minuta"
└─→ Nastavlja checkout normalno
└─→ Mali rizik overselling-a, ali bolje od blokiranog checkout-a
```

**Scenario B: Plaćanje pukne NAKON kreirane rezervacije**

```
MedusaJS kreirao ReservationItem (X: -1, Y: -1)
└─→ AllSecure: kartica odbijena / timeout / greška
└─→ MedusaJS workflow KOMPENZACIJA automatski:
    └─→ Briše ReservationItem za X
    └─��� Briše ReservationItem za Y
    └─→ Količine se vraćaju u raspoloživu zalihu (lokalno u MedusaJS)
└─→ Kupac vidi: "Plaćanje nije uspjelo. Pokušajte ponovo."
└─→ Abacus NIJE KONTAKTIRAN — nikakva promjena u ERP-u
```

> **Ključno:** Rezervacija je samo u MedusaJS-u (lokalno), NE u Abacusu.
> Zato otkazivanje rezervacije ne zavisi od Abacus API-ja i ne može zaglaviti.

**Scenario C: MedusaJS pad (server crash) sa aktivnim rezervacijama**

```
MedusaJS kreirao ReservationItem, pa se server restartuje
└─→ Rezervacije ostaju u PostgreSQL bazi (persistentne)
└─→ Cleanup cron job (svakih 5 min) pronalazi "stale" rezervacije starije od 15 min
└─→ Briše ih automatski
└─→ Količine se vraćaju u raspoloživu zalihu
└─→ Sljedeći inventory sync iz Abacusa (svakih 15-30 min) "resetuje" stanje na tačno
```

**Scenario D: Kupac odustane (zatvori browser nakon CHECK-a, prije plaćanja)**

```
MedusaJS kreirao ReservationItem
└─→ Kupac zatvori browser / ode na drugu stranicu
└─→ Plaćanje nikad ne dolazi
└─→ Cleanup cron job: nakon 15 min briše ReservationItem
└─→ Količine oslobođene za druge kupce
```

**Scenario E: Dva kupca istovremeno hoće zadnji komad**

```
Kupac A: checkout → getItems → iPhone 16 Pro: quantity = 1 ✅
Kupac B: checkout → getItems → iPhone 16 Pro: quantity = 1 ✅
         (oba vide da ima 1 komad — race condition!)

Kupac A: MedusaJS kreira ReservationItem → lokalna količina: 0
Kupac B: MedusaJS provjerava lokalnu količinu → 0 → ❌
         "Nažalost, iPhone 16 Pro više nije dostupan."

RJEŠENJE: MedusaJS ReservationItem je atomičan (DB transakcija).
Samo jedan kupac može uspješno kreirati rezervaciju za zadnji komad.
Drugi dobija poruku odmah — nema čekanja, nema pozivanja kupca naknadno.
```

#### Zašto je ovo dovoljno za Fazu 1

| Aspekt | Obrazloženje |
|--------|-------------|
| **Rizik overselling-a** | Minimalan. Real-time check na Abacusu + lokalna rezervacija pokrivaju 99% slučajeva. |
| **Jedini gap** | Između zadnjeg sync-a i checkout-a (max 30 min) neko može kupiti u fizičkoj prodavnici. Fallback: operater kontaktira kupca — ali sada se to dešava MNOGO rjeđe nego bez check-a. |
| **Apple premium segment** | Mali obim narudžbina (skupi proizvodi), mala vjerovatnoća istovremene kupovine zadnjeg komada. |
| **Bez Abacus zavisnosti za recovery** | Rezervacija je lokalna (MedusaJS) — nikad ne zaglavimo čekajući Abacus da otključa. |
| **Kompleksnost** | Umerena — MedusaJS v2 već ima ugrađen ReservationItem. Dodajemo samo real-time getItems check. |

### 2.4. Tok narudžbine — Faza 1 (revidiran)

```
1. Kupac pretražuje katalog na icentar.me (MedusaJS)
   └─ Proizvodi sinhronizovani iz Abacusa (scheduled job, svakih 30 min)
   └─ Zalihe prikazane po lokaciji (Podgorica / Tivat)

2. Kupac dodaje u korpu

3. Kupac klikne "Završi kupovinu" — REAL-TIME CHECK
   └─ MedusaJS poziva Abacus getItems(ids=[...], id_m=X) za svaki artikal
   └─ Ako SVE raspoloživo → nastavlja
   └─ Ako NEŠTO nije raspoloživo → poruka kupcu, bez nastavka
   └─ MedusaJS kreira lokalne ReservationItem (TTL: 15 min)

4. Kupac unosi podatke, bira dostavu, plaća
   └─ AllSecure procesuira karticu (ili COD)
   └─ Uspješno → order.placed
   └─ Neuspješno → kompenzacija: sve ReservationItem se brišu automatski

5. MedusaJS šalje email kupcu: "Narudžbina primljena"

6. Operater u backoffice-u:
   └─ Vidi narudžbinu u MedusaJS admin panelu
   └─ Zna da je raspoloživost VEĆ provjerena u Abacusu u trenutku kupovine
   └─ RUČNO kreira porudžbinu u Abacusu (bez brige da nema na stanju)
   └─ RUČNO fiskalizuje putem Abacus POS-a (kao i do sada)
   └─ Priprema paket, predaje kuriru (Monte Nomaks)
   └─ Ažurira status narudžbine u MedusaJS: "Poslato"

7. MedusaJS šalje email kupcu: "Vaša narudžbina je poslata"
```

### 2.4. Fiskalizacija u Fazi 1

> **Bez promjene.** Operater fiskalizuje ručno putem Abacus POS-a, isto kao i za fizičku prodaju.
>
> Detaljna analiza automatske fiskalizacije za Fazu 2: **`fiskalizacija-crna-gora-faza2.md`**
>
> Ključna činjenica: CG zakon zahtijeva fiskalizaciju i za online prodaju. Trenutno se to rješava ručno. Automatizacija je planirana za Fazu 2 jer ne povećava scope Faze 1.

---

## 3. Pitanja za sastanak — Faza 1

> **Kontekst:** Sastanak sa Abacus/Bencom timom. Fokus na ERP integraciju.
> Pitanja za Fazu 2 (fiskalizacija) su u `fiskalizacija-crna-gora-faza2.md`.

### 3.1. PRISTUP API-JU (BLOKIRAJUĆE — bez ovoga ne počinjemo)

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **1** | **Koji su production URL, klijent ID i token za Abacus API?** Format: `api.bencomltd.com/{klijent}/Main/{funkcija}?token=...` | ERP/Abacus | 🔴 Kritično | **Blokirajuće.** Bez kredencijala ne možemo pristupiti nijednom endpoint-u. |
| **2** | **Da li postoji TEST okruženje za API** (vidimo `APITest` u URL-u dokumentacije)? Da li možemo dobiti test token? | ERP/Abacus | 🔴 Kritično | **Blokirajuće.** Testiranje na produkciji rizično — ne želimo slučajno kreirati narudžbine. |
| **3** | **Da li je API dokumentacija (v_20250325) aktuelna?** Svi endpoint-i aktivni? Ima li nedokumentovanih? Da li API radi 24/7 ili ima maintenance window? | ERP/Abacus | 🔴 Kritično | Ako nešto ne radi ili se promijenilo, moramo prilagoditi plan. Ako ima downtime → moramo predvidjeti fallback. |
| **4** | **Da li API ima rate limiting?** Koliko poziva/min dozvoljen? **Da li `getItems` bez `ids` parametra vraća SVE artikle odjednom?** Iz dokumentacije vidimo da `ids` filtrira po konkretnim artiklima (npr. `"ids": [3131, 1235]`), ali ne vidimo klasičnu pagination (page/offset/limit). Znači: za sync kompletnog kataloga pozivamo getItems BEZ `ids` — koliki je payload za ~300 artikala? Da li to radi pouzdano ili treba zvati u batch-evima? | ERP/Abacus | 🟡 Srednji | Dva scenarija korišćenja: (1) **Full sync** — getItems bez `ids`, svi artikli odjednom, svakih 30 min, (2) **Checkout check** — getItems sa `ids=[X,Y]`, samo 2-3 artikla, real-time. Moramo znati da li full sync payload pravi problem. |
| **5** | **Live demo: pozovimo zajedno `getItems` sa `ids` parametrom za 2-3 realna artikla** (npr. iPhone 16 Pro 256GB, AirPods Pro 3). Iz dokumentacije vidimo da to radi (`"ids": [3131, 1235]`) — zelimo da na sastanku vidimo realan response i potvrdimo format cijena, slika, `details[]`, popusta. | ERP/Abacus | 🟠 Visok | Jedan konkretan response eliminise desetine pitanja o tumacenju polja. Idealno: live demo na sastanku. |

### 3.2. KATALOG PROIZVODA — getItems (CORE ZA FAZU 1)

> `getItems` je srce integracije. Sva pitanja u ovom bloku se odnose na to kako Abacus modeluje artikle i kako ćemo ih preslikati u MedusaJS webshop.

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **6** | **Da li `getItems` bez parametara vraća SVE artikle ili samo aktivne?** Da li ima neaktivnih/skrivenih koje ne treba prikazivati online? **Koliko artikala ukupno?** (procjena: 200-400?) | ERP/Abacus | 🟠 Visok | Filtriranje + performanse sync-a. Sa <500 artikala sync je trivijalan, ali moramo znati šta filtrirati. |
| **7** | **Kako su Apple konfiguracije modelovane?** Npr. iPhone 16 Pro u 128/256/512GB i 4 boje — da li je to 1 artikal sa `details[]` (type:memorija, value:256GB), ili 12 zasebnih artikala u getItems? | ERP/Abacus | 🟠 Visok | Ako `details[]` → koristimo MedusaJS varijante (1 product, N variants). Ako zasebni artikli → svaki je zaseban MedusaJS product. Kompletno mijenja strukturu kataloga. |
| **8** | **Šta sadrži `image[]` polje?** Pune URL adrese (https://...), relativne putanje, ili base64? Gdje su slike hostovane? Da li su kvalitetne za webshop (visoka rezolucija, bijela pozadina)? | ERP/Abacus | 🟠 Visok | URL → koristimo direktno. Putanje → treba base URL. Nema/loš kvalitet → ručni upload Apple press slika. |
| **9** | **Da li `group` polje odgovara kategorijama na sajtu** (Mac, iPhone, iPad...)? Koliko nivoa dubine ima? Ili je "flat" (samo jedan nivo)? | ERP/Abacus | 🟡 Srednji | Mapiranje na MedusaJS kategorije. Ako je flat → ručno kreiranje podkategorija. |
| **10** | **Da li postoji mehanizam za detekciju promjena** u artiklima? Timestamp zadnje izmjene, verzija, change feed? | ERP/Abacus | 🟡 Srednji | DA → sync samo promijenjenih. NE → full sync svaki put (ok za <500, ali dobro je znati). |
| **11** | **Koliko često se mijenjaju podaci o artiklima?** Cijene, opisi, slike — dnevno, sedmično, rijetko? | Poslovno | 🟡 Srednji | Određuje sync frekvenciju: 15 min (često) vs 60 min (rijetko). |

### 3.3. CIJENE, CIJENOVNICI I POPUSTI (KRITIČNO — pogrešna cijena = poslovni gubitak)

> Abacus ima **tri sloja** koja utiču na konačnu cijenu: polja `price`/`price_rrp`, cijenovnici (`getPriceLists` + parametar `id_c`), i popusti (`discount` + `id_partner`). **Moramo razumjeti kako rade zajedno** — inače kupac vidi pogrešnu cijenu.
>
> Iz API dokumentacije:
> - `getItems` vraća `price` (iz osnovnog cijenovnika) i `price_rrp` (maloprodajna)
> - Parametar `id_c` mijenja koji cijenovnik se koristi za `price`
> - Parametar `id_partner` proračunava cijenu i popust za konkretnog kupca
> - API kaže: *"cijena je proračunata, popust je tu samo za prikaz, nema potrebe da preračunavate"*

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **12** | **Koliko cijenovnika vraća `getPriceLists`?** Da li ih je više aktivnih istovremeno, ili je uvijek jedan "main"? Koji je merodavan za maloprodaju? | ERP/Abacus | 🔴 Kritično | Ako ih je više i koristimo pogrešan → pogrešne cijene na sajtu za sve artikle. |
| **13** | **Koji cijenovnik koristiti za online prodaju?** Da li za `getItems` proslijeđujemo `id_c`? Ako da — koji ID tačno? Ili pozivamo BEZ `id_c` i koristimo default? **Da li su online i offline cijene iste?** | Poslovno/ERP | 🔴 Kritično | Ovo je PRVA stvar koju moramo znati prije go-live. Jednoznačno: "za online koristite id_c=X" ili "bez id_c, default je ok". |
| **14** | **`price` vs `price_rrp` — koji prikazujemo kupcu?** Da li `price` = veleprodajna a `price_rrp` = maloprodajna? Ili oboje ista vrijednost? | ERP/Abacus | 🟠 Visok | Pogrešno polje = pogrešna cijena. `price_rrp` zvuči kao "recommended retail price", ali treba potvrdu. |
| **15** | **Kako rade popusti (`discount`)?** Da li je `price` VEĆ umanjen za popust, ili moramo sami računati `price × (1 - discount/100)`? Da li `discount` postoji uvijek ili samo kad je aktivan? | ERP/Abacus | 🟠 Visok | API kaže "cijena je proračunata, popust za prikaz". Ali: da li to znači da `price=850` za iPhone koji inače košta 1000 i `discount=15`? Ili `price=1000` i mi računamo? |
| **16** | **Da li popusti zavise od kupca (`id_partner`)?** Npr. EDU institucija dobija drugačiju cijenu? Za anonimne B2C kupce — pozivamo getItems bez `id_partner`? Da li se popusti iz `getPromotions` automatski reflektuju u `getItems` ili su to odvojeni sistemi? | Poslovno/ERP | 🟡 Srednji | B2C = bez partnera (većina kupaca). B2B/EDU = sa partnerom. Moramo znati default i kako se slojevi kombinuju. |

### 3.4. ZALIHE, MAGACINI I REZERVACIJA (ZAŠTITA OD OVERSELLING-A)

> Ovaj blok pokriva `getWorkUnits` (koji magacini postoje), `quantity` iz `getItems` (stanje zaliha), i ključno pitanje o rezervaciji. Vidi sekciju 2.3 za kompletnu elaboraciju checkout stock check strategije.

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **17** | **Koliko radnih jedinica (magacina) vraća `getWorkUnits`?** Podgorica + Tivat? Postoji li centralni magacin? **Koji `id_m` odgovara kojoj lokaciji?** | ERP/Abacus | 🟠 Visok | Mapiranje na MedusaJS stock lokacije. Bez tačnih ID-ova ne možemo prikazati "Na stanju u PG: 3, Tivat: 1". |
| **18** | **Da li `quantity` u `getItems` reflektuje TRENUTNO stanje u realnom vremenu?** Ažurira li se odmah po prodaji sa kase? Ili može kasniti? | ERP/Abacus | 🟠 Visok | Koristimo `quantity` za real-time check na checkout-u (vidi 2.3). Ako kasni → overselling moguć. |
| **19** | **Da li `getItems(ids=[X,Y], id_m=Z)` odgovara brzo?** <2 sekunde za 1-5 artikala? | ERP/Abacus | 🟠 Visok | Pozivamo na svakom checkout-u. Spor odgovor (>3s) → kupac čeka → odustaje. |
| **20** | **Da li Abacus podržava REZERVACIJU / ZAKLJUČAVANJE količine na lageru?** Detaljna elaboracija ispod ⬇️ | ERP/Abacus | 🟠 Visok | Direktno utiče na arhitekturu checkout-a i zaštitu od overselling-a (vidi 2.3). |
| **21** | **Da li online narudžbine uvijek idu sa jednog magacina?** Ili zavisi od lokacije kupca? Uvijek iz centralnog? | Poslovno | 🟡 Srednji | Fulfillment logika — iz kog magacina se šalje? |

> **Elaboracija pitanja #20 — Rezervacija zaliha u Abacusu:**
>
> Želimo da na checkout-u, PRIJE nego kupac plati, privremeno "zaključamo" naručenu količinu u Abacusu tako da drugi kupci (online ili u fizičkoj prodavnici) ne mogu kupiti isti artikal. Nakon uspješnog plaćanja → potvrđujemo. Ako plaćanje ne prođe → otključavamo.
>
> **Konkretno pitamo:**
> - Da li Abacus ima koncept **rezervacije** ili **prednarudžbine** koji privremeno smanjuje raspoloživu količinu bez kreiranja konačnog prodajnog dokumenta?
> - Ako da — **postoji li API endpoint za to?** (nije dokumentovan u v_20250325, ali možda postoji interni mehanizam)
> - Da li `postSale` može služiti kao mehanizam zaključavanja? Tj. da li kreira dokument koji "drži" količinu, a koji se može stornirati ako plaćanje ne prođe?
> - Da li postoji **timeout / automatsko otključavanje**? Npr. ako ne potvrdimo rezervaciju za 15 min, da li se automatski oslobađa?
> - Ako Abacus NE podržava rezervaciju — **da li barem `quantity` u `getItems` reflektuje stanje u realnom vremenu** (da možemo raditi real-time check)?
>
> **Zašto je ovo bitno:**
> Bez Abacus rezervacije, koristićemo lokalni MedusaJS ReservationItem (vidi sekciju 2.3). To štiti od duplih online kupovina, ali NE štiti od situacije gdje operater u prodavnici proda zadnji komad dok je online kupac na checkout-u. Sa Abacus rezervacijom → zaštita je potpuna na svim kanalima.

### 3.5. NARUDŽBINE — postSale (PRIPREMA FAZE 2)

> U Fazi 1 operater ručno unosi narudžbine u Abacus. Ali moramo razumjeti `postSale` za planiranje automatizacije.

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **22** | **Šta tačno kreira `postSale`?** Prodajni nalog, predračun, otpremnica? **Da li automatski smanjuje stanje zaliha** ili tek kad se dokument potvrdi? | ERP/Abacus | 🟡 Srednji | Da znamo šta operater danas ručno radi. Ako smanjuje zalihe → utiče na sync logiku. |
| **23** | **Da li `postSale` pokreće fiskalizaciju?** Ili samo kreira dokument? **Da li vraća ID kreiranog dokumenta** u response-u? | ERP/Abacus | 🟡 Srednji | Za Fazu 2: ako pokreće fiskalizaciju → ne trebamo custom fiskalni modul. ID za tracking. |
| **24** | **Da li `id_partner` u `postSale` mora biti prethodno kreiran** (`AddPartner`)? Ili narudžbina može bez partnera za B2C kupce? | ERP/Abacus | 🟡 Srednji | Ako mora → workflow: AddPartner → postSale. Ako ne → jednostavnije za Fazu 2. |
| **25** | **Šta se desi ako pošaljemo `postSale` za artikal koji nije na stanju?** Greška? Ili se kreira dokument svejedno? | ERP/Abacus | 🟡 Srednji | Za error handling u Fazi 2 — da znamo da li Abacus sam validira stanje. |

### 3.6. INFRASTRUKTURA I MIGRACIJA

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **26** | **Da li ostajemo na domenu icentar.me?** | DevOps | 🟠 Visok | DNS, SSL, SEO redirecti. |
| **27** | **Gdje će se hostovati MedusaJS?** Cloud (AWS, DigitalOcean, Hetzner) ili lokalno? | DevOps | 🟠 Visok | Infrastruktura, troškovi, latencija. |
| **28** | **Da li AllSecure Payment Gateway ima API dokumentaciju?** Podržava li integraciju sa custom platformama? | Payment | 🟠 Visok | Bez payment-a nema checkout-a. Backup: Stripe (već pripremljen u kodu). |
| **29** | **Da li postoje sadržaji na WP sajtu koji se moraju migrirati?** Blog, landing stranice, SEO linkovi? | Migracija | 🟡 Srednji | Obim WP → MedusaJS migracije. |

> **Razriješena pitanja (ne treba pitati):**
> - **Storefront:** Next.js 16.2.1 + React 19 + Tailwind CSS (vidi sekciju 1.3)
> - **Dev tim:** Kolege iz tima, dostupne za koordinaciju
> - **Magento migracija:** Plugin postoji u kodu (`migrate-from-magento`), za potvrdu sa kolegama

---

## 4. Tehnička arhitektura — Faza 1

### 4.1. Abacus Sync + Checkout Stock Check Modul

```
src/modules/abacus-erp/
├── service.ts                     # AbacusErpService
│   ├── getItems(id_m?, ids?)      # Proizvodi, zalihe, cijene
│   ├── getWorkUnits()             # Radne jedinice (magacini)
│   └── checkStock(ids, id_m)      # Real-time provjera za checkout
└── index.ts

src/workflows/abacus/
├── sync-products.ts               # getItems → MedusaJS products (scheduled)
├── sync-inventory.ts              # getItems + id_m → inventory levels (scheduled)
└── verify-stock-on-checkout.ts    # Real-time check + ReservationItem
    ├── step: call-abacus-getitems  # getItems(ids, id_m) → stanje
    ├── step: validate-availability # svi artikli raspoloživi?
    ├── step: create-reservations   # ReservationItem za svaki artikal
    │   └── compensate: delete-reservations  # ← automatski cleanup ako nešto pukne
    └── (workflow završava, plaćanje nastavlja)

src/subscribers/
└── checkout-stock-check.ts        # cart.checkout → verify-stock-on-checkout

src/jobs/
├── sync-products-job.ts           # Cron: svakih 60 min
├── sync-inventory-job.ts          # Cron: svakih 30 min
└── cleanup-stale-reservations.ts  # Cron: svakih 5 min — briše TTL-expired
```

> **Scope:** Čitanje iz Abacusa (getItems + getWorkUnits) + real-time check na checkout + lokalna rezervacija.
> Bez pisanja u Abacus (postSale, AddPartner) — to je Faza 2.

### 4.3. Već implementirano u MedusaJS

| Funkcionalnost | Status | Napomena |
|----------------|--------|----------|
| MedusaJS v2 core | ✅ | v2.6.1, PostgreSQL, MikroORM |
| Pretraga (Typesense) | ✅ | Region-aware, faceted |
| Wishlist | ✅ | Plugin sa sharing (aktivirati ako jednostavno) |
| Dokumenti/Fakture | ✅ | PDF generisanje, B2B/B2C |
| Legal Entity (B2B) | ✅ | Pravna lica, tipovi kupaca |
| Custom atributi | ✅ | Po varijanti |
| **Abacus sync modul** | ❌ | **Faza 1 — razviti** |
| **Payment (AllSecure)** | ❌ | **Faza 1 — integrisati** |
| Auto narudžbine (postSale) | ❌ | Faza 2 |
| Auto fiskalizacija | ❌ | Faza 2 → `fiskalizacija-crna-gora-faza2.md` |

---

## 5. Plan rada — Faza 1

### Korak 0: Discovery & Setup (1-2 sedmice)

- [ ] Dobiti Abacus API kredencijale (URL, klijent, token)
- [ ] Testirati `getItems` i `getWorkUnits` u Postman-u
- [ ] Mapirati Abacus artikle → MedusaJS product model
- [ ] Mapirati Abacus radne jedinice → MedusaJS stock lokacije
- [ ] Pregledati MedusaJS storefront kod sa dev timom
- [ ] Provjeriti AllSecure Payment Gateway API
- [ ] Setup hosting (production environment)
- [ ] Konfigurisati domenu + SSL

### Korak 1: Abacus Sync + Checkout Stock Check (2-3 sedmice)

- [ ] Razviti `src/modules/abacus-erp/` service
- [ ] Implementirati `sync-products` workflow
  - `group` → kategorije
  - `details[]` → varijante (boja, memorija)
  - `image[]` → product media
  - `price` / `price_rrp` → pricing
- [ ] Implementirati `sync-inventory` workflow
  - Po magacinu (Podgorica, Tivat)
  - Scheduled job: svakih 30 min
- [ ] Implementirati `verify-stock-on-checkout` workflow (vidi sekciju 2.3)
  - Real-time `getItems(ids, id_m)` poziv na checkout
  - Validacija raspoloživosti za svaki artikal u korpi
  - Kreiranje ReservationItem sa kompenzacijom
  - Fallback na lokalne zalihe ako Abacus nije dostupan
- [ ] Implementirati `cleanup-stale-reservations` cron job (svakih 5 min, TTL 15 min)
- [ ] Konfigurisati regione: Crna Gora, EUR, PDV 21%
- [ ] Setup stock lokacija (Podgorica, Tivat)
- [ ] Aktivirati Redis

### Korak 2: Payment & Frontend (2-3 sedmice)

- [ ] Integracija AllSecure Payment Gateway
- [ ] Review i prilagodba storefront-a
- [ ] Prikaz raspoloživosti po lokaciji
- [ ] Checkout flow (adresa, dostava, plaćanje)
- [ ] Email template-i (potvrda narudžbine, status update)
- [ ] Mobile responsiveness
- [ ] SEO redirecti sa starog WP sajta

### Korak 3: Testiranje & Go-Live (1-2 sedmice)

- [ ] E2E testiranje: pretraga → korpa → checkout → narudžbina → email
- [ ] UAT sa iCentar timom
- [ ] Obuka backoffice ekipe za MedusaJS admin panel
- [ ] DNS prelazak: icentar.me → MedusaJS
- [ ] Monitoring setup
- [ ] Go-live

### Ukupna procjena Faze 1: **6-10 sedmica**

---

## 6. Buduće faze (pregled)

| Faza | Scope | Detalji |
|------|-------|---------|
| **Faza 2: Fiskalizacija** | Automatska fiskalizacija online računa | Vidi `fiskalizacija-crna-gora-faza2.md` |
| **Faza 3: Auto narudžbine** | `postSale` automatski na order.placed | + `AddPartner` za kupce |
| **Faza 4: Napredne funkcije** | Click & Collect, B2B/EDU, Promocije, Gift kartice, Rate plaćanje | `getPromotions`, `id_partner`, `getIncomingItems` |

---

## 7. Rizici — Faza 1

| Rizik | Vjerovatnoća | Uticaj | Mitigacija |
|-------|-------------|--------|------------|
| Abacus API ne radi ili je drugačiji od dokumentacije | Srednja | 🔴 Kritičan | Testirati sve u Koraku 0 prije početka razvoja |
| AllSecure Payment Gateway nema API / ne podržava integraciju | Srednja | 🔴 Kritičan | Provjeriti na sastanku. Backup: Stripe (podržava EUR) |
| Abacus `getItems` spor za real-time checkout check (>3s) | Srednja | 🟠 Visok | Mjeriti u Koraku 0. Ako spor → fallback na lokalne zalihe bez real-time check-a. |
| Abacus `quantity` kasni za fizičkom prodajom | Srednja | 🟡 Srednji | Apple premium segment = mali obim, nizak rizik. Operater kao zadnja linija odbrane. |
| Slike iz Abacus API neupotrebljive ili nedostaju | Srednja | 🟡 Srednji | Backup: ručni upload (Apple press images javno dostupne) |
| Storefront kod nekompatibilan | Niska | 🟡 Srednji | Review sa dev timom u Koraku 0 |
| `getItems` ne vraća dovoljno podataka za prikaz | Srednja | 🟡 Srednji | Ručno dopunjavanje opisa/specifikacija u MedusaJS admin |

---

## Appendix A: Abacus API — Brza referenca

```
Base URL: http://api.bencomltd.com/{klijent}/Main/{funkcija}?token={token}&protocol=2.0

GET  /GetPartners               → Lista partnera
GET  /getWorkUnits              → Lista magacina/lokacija
GET  /getPriceLists             → Lista cijenovnika
POST /getItems                  → Proizvodi, zalihe, cijene [body: ids, id_m, id_partner, id_c]
POST /postSale                  → Kreiranje narudžbine [body: order{...}, id_m]
GET  /getIncomingItems          → Artikli u dolasku
POST /getOpenItems              → Otvorene stavke [body: idPartner]
POST /getPartnerBalanceDetailed → Finansijska kartica [body: idPartner, datumDo]
POST /AddPartner                → Kreiranje partnera [body: partner{...}]
POST /getPromotions             → Promocije [body: datumOd, datumDo, ...]

Response: { "Data": ..., "Version": "1.0", "Error": null, "ErrorDetails": null }
```

Kompletna API dokumentacija: `docs/abacus/abacus-api-dokumentacija.md`

## Appendix B: Kontakti

| Kontakt | Info |
|---------|------|
| **Bencom d.o.o.** (Abacus developer) | it@bencomltd.com, +381 31/332-302, Herceg Novi |
| **POS4.me** (distributer) | info@pos4.me, +382 20 221 750, Podgorica |

## Appendix C: Povezani dokumenti

| Dokument | Sadržaj |
|----------|---------|
| `fiskalizacija-crna-gora-faza2.md` | Detaljna analiza CG fiskalizacije: zakon, tehnička specifikacija, opcije implementacije, open-source reference, SaaS provajderi |
| `abacus/abacus-api-dokumentacija.md` | Kompletna Abacus API dokumentacija (konvertovano iz DOCX) |
