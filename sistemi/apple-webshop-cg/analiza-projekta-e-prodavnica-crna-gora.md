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

### 3.1. ABACUS API — Pristup i konfiguracija (BLOKIRAJUĆE)

> Bez odgovora na ova pitanja ne možemo početi razvoj. Najviši prioritet.

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **1** | **Koji su production URL, klijent ID i token za Abacus API?** Format: `api.bencomltd.com/{klijent}/Main/{funkcija}?token=...` | ERP/Abacus | 🔴 Kritično | **Blokirajuće.** Bez kredencijala ne možemo pristupiti nijednom endpoint-u. |
| **2** | **Da li postoji TEST okruženje za API** (vidimo `APITest` u dokumentaciji URL-u)? Da li možemo dobiti test token? | ERP/Abacus | 🔴 Kritično | **Blokirajuće za razvoj.** Testiranje na produkciji rizično — ne želimo slučajno kreirati narudžbine. |
| **3** | **Da li je API dokumentacija (v_20250325) aktuelna?** Da li su svi endpoint-i aktivni? Ima li nedokumentovanih? | ERP/Abacus | 🔴 Kritično | Ako neki endpoint ne radi ili se promijenio, moramo prilagoditi plan. |

### 3.2. ABACUS API — getItems: Proizvodi, zalihe, cijene (CORE INTEGRACIJA)

> Ovo je srce integracije. `getItems` je najbitniji endpoint za Fazu 1.

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **4** | **Da li `getItems` bez parametara vraća SVE artikle?** Ili samo aktivne? Da li ima neaktivnih/skrivenih? | ERP/Abacus | 🟠 Visok | Ako vraća neaktivne, moramo filtrirati. Ako ne → prikazaćemo artikle kojih nema. |
| **5** | **Koliko artikala ukupno vraća `getItems`?** Procjena: 200-400? Ili više? | ERP/Abacus | 🟠 Visok | Utiče na performanse sync-a. Sa <500 trivijalno. |
| **6** | **Šta tačno sadrži `image[]` polje?** Pune URL adrese, relativne putanje, ili base64? Gdje su hostovane? | ERP/Abacus | 🟠 Visok | URL → direktno. Putanje → base URL. Nema → ručni upload. |
| **7** | **Kako radi `details[]`?** Da li su Apple konfiguracije (128/256/512GB, boja) `details`, ili zasebni artikli? | ERP/Abacus | 🟠 Visok | MedusaJS varijante (1 proizvod, više opcija) vs zasebni proizvodi. |
| **8** | **Da li `group` odgovara kategorijama na sajtu?** (Mac, iPhone, iPad...) Nivoi dubine? | ERP/Abacus | 🟡 Srednji | Mapiranje na MedusaJS kategorije. |
| **9** | **Da li se `price` i `price_rrp` razlikuju?** Koji za online? | Poslovno/ERP | 🟠 Visok | Pogrešna cijena = poslovni gubitak. |
| **10** | **Postoji li poseban cijenovnik za online?** Ili online = offline? Koji `id_c`? | Poslovno/ERP | 🟠 Visok | Ako različite → moramo koristiti `id_c` u sync-u. |
| **11** | **Koliko često se mijenjaju cijene i zalihe?** | Poslovno | 🟡 Srednji | Frekvencija sync-a: 15 min vs 60 min. |
| **12** | **Da li `getItems(ids=[X,Y], id_m=Z)` odgovara brzo?** <2 sekunde za 1-5 artikala? | ERP/Abacus | 🟠 Visok | Na checkout-u (real-time check). Spor → kupac odustaje. |
| **13** | **Da li `quantity` reflektuje TRENUTNO stanje?** Ažurira li se odmah po prodaji sa kase? | ERP/Abacus | 🟠 Visok | Ako kasni → overselling moguć i pored real-time check-a. |
| **14** | **Postoji li API za REZERVACIJU količine?** Privremeno zaključavanje bez prodajnog dokumenta? | ERP/Abacus | 🟡 Srednji | DA → idealan (lock→pay→confirm). NE → lokalni MedusaJS ReservationItem (vidi 2.3). |

### 3.3. ABACUS API — getWorkUnits: Magacini i lokacije

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **15** | **Koliko radnih jedinica (magacina) vraća `getWorkUnits`?** Podgorica + Tivat? Centralni? | ERP/Abacus | 🟠 Visok | Mapiranje na MedusaJS stock lokacije. |
| **16** | **Koji `id_m` odgovara kojoj lokaciji?** Tačni ID-ovi za PG i Tivat. | ERP/Abacus | 🟠 Visok | Bez ovoga nema prikaza stanja po lokaciji. |
| **17** | **Da li online narudžbine uvijek idu sa jednog magacina?** Ili zavisi od kupca? | Poslovno | 🟡 Srednji | Fulfillment logika — odakle se šalje? |

### 3.4. ABACUS API — postSale: Narudžbine (ZA PRIPREMU FAZE 2)

> U Fazi 1 narudžbine se ručno unose u Abacus. Ali moramo razumjeti `postSale` za planiranje automatizacije.

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **18** | **Šta tačno kreira `postSale`?** Prodajni nalog, predračun, otpremnica? | ERP/Abacus | 🟡 Srednji | Da znamo šta operater ručno radi i šta ćemo automatizovati. |
| **19** | **Da li `postSale` automatski smanjuje stanje zaliha?** Ili tek kad se potvrdi? | ERP/Abacus | 🟡 Srednji | Da li sync odmah reflektuje online narudžbinu. |
| **20** | **Da li `postSale` pokreće fiskalizaciju?** Ili samo kreira dokument? | ERP/Abacus | 🟡 Srednji | Za Fazu 2 — ako DA → fiskalizacija "besplatna" uz postSale. |
| **21** | **Da li `postSale` vraća ID dokumenta?** U kom polju? | ERP/Abacus | 🟡 Srednji | Tracking: MedusaJS order ↔ Abacus document. |
| **22** | **Da li `id_partner` mora biti prethodno kreiran?** Ili narudžbina može bez partnera (B2C)? | ERP/Abacus | 🟡 Srednji | Ako mora → AddPartner pa postSale. Ako ne → jednostavnije. |

### 3.5. ABACUS API — Tehnički detalji

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **23** | **Da li API ima rate limiting?** Koliko poziva/min? | ERP/Abacus | 🟡 Srednji | Checkout real-time check + scheduled sync. Treba kapacitet. |
| **24** | **Da li API podržava pagination?** Ili sve u jednom odgovoru? | ERP/Abacus | 🟡 Srednji | Sa <500 artikala vjerovatno ok, ali potvrditi. |
| **25** | **Mehanizam za detekciju promjena?** Timestamp, verzija, change feed? | ERP/Abacus | 🟡 Srednji | DA → delta sync. NE → full sync (ok za mali katalog). |
| **26** | **Da li API radi 24/7?** Maintenance window? | ERP/Abacus | 🟡 Srednji | Downtime → checkout fallback na lokalne zalihe (vidi 2.3, Scenario A). |
| **27** | **Ponašanje pri neispravnom request-u?** Uvijek `Error` polje ili HTTP 500 bez tijela? | ERP/Abacus | 🟢 Nizak | Error handling robustnost. |

### 3.6. INFRASTRUKTURA I MIGRACIJA

| # | Pitanje | Kategorija | Važnost | Uticaj |
|---|---------|-----------|---------|--------|
| **28** | **Da li ostajemo na domenu icentar.me?** | DevOps | 🟠 Visok | DNS, SSL, SEO redirecti. |
| **29** | **Gdje će se hostovati MedusaJS?** Cloud (AWS, DigitalOcean, Hetzner) ili lokalno? | DevOps | 🟠 Visok | Infrastruktura, troškovi, latencija. |
| **30** | **Da li AllSecure Payment Gateway ima API dokumentaciju?** Podržava li integraciju sa custom platformama? | Payment | 🟠 Visok | Bez payment-a nema checkout-a. Backup: Stripe (već pripremljen u kodu). |
| **31** | **Da li postoje sadržaji na WP sajtu koji se moraju migrirati?** Blog, landing stranice, SEO linkovi? | Migracija | 🟡 Srednji | Obim WP → MedusaJS migracije. |

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
