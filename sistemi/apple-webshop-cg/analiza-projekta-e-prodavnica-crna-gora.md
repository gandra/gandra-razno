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

### 1.3. Trenutni operativni tok (KLJUČNO ZA FAZU 1)

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

### 1.4. Abacus ERP — API mogućnosti (za buduću automatizaciju)

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
| **Zalihe** | ✅ Sync iz Abacusa (`getItems` + `id_m`) | Rezervacija na checkout |
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

### 2.3. Tok narudžbine — Faza 1

```
1. Kupac pretražuje katalog na icentar.me (MedusaJS)
   └─ Proizvodi sinhronizovani iz Abacusa (scheduled job, svakih 30 min)
   └─ Zalihe prikazane po lokaciji (Podgorica / Tivat)

2. Kupac dodaje u korpu i završava checkout
   └─ AllSecure gateway procesuira karticu (ili bira pouzeće)
   └─ MedusaJS kreira narudžbinu

3. MedusaJS šalje email kupcu: "Narudžbina primljena"

4. Operater u backoffice-u:
   └─ Vidi narudžbinu u MedusaJS admin panelu
   └─ Provjerava raspoloživost u Abacusu (pomoć: sync zaliha)
   └─ RUČNO kreira porudžbinu u Abacusu
   └─ RUČNO fiskalizuje putem Abacus POS-a (kao i do sada)
   └─ Priprema paket, predaje kuriru (Monte Nomaks)
   └─ Ažurira status narudžbine u MedusaJS: "Poslato"

5. MedusaJS šalje email kupcu: "Vaša narudžbina je poslata"
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

| # | Pitanje | Važnost | Uticaj |
|---|---------|---------|--------|
| **1** | **Koji su production URL, klijent ID i token za Abacus API?** Format: `api.bencomltd.com/{klijent}/Main/{funkcija}?token=...` | 🔴 Kritično | **Blokirajuće.** Bez kredencijala ne možemo pristupiti nijednom endpoint-u. |
| **2** | **Da li postoji TEST okruženje za API** (vidimo `APITest` u dokumentaciji URL-u)? Da li možemo dobiti test token? | 🔴 Kritično | **Blokirajuće za razvoj.** Testiranje na produkciji je rizično — ne želimo slučajno kreirati narudžbine. |
| **3** | **Da li je API dokumentacija (v_20250325) aktuelna?** Da li su svi endpoint-i aktivni i stabilni? Da li ima nedokumentovanih endpoint-a? | 🔴 Kritično | Ako neki endpoint ne radi ili se promijenio, moramo prilagoditi plan. |

### 3.2. ABACUS API — getItems: Proizvodi, zalihe, cijene (CORE INTEGRACIJA)

> Ovo je srce integracije. `getItems` je najbitniji endpoint za Fazu 1.

| # | Pitanje | Važnost | Uticaj |
|---|---------|---------|--------|
| **4** | **Da li `getItems` bez parametara vraća SVE artikle?** Ili samo aktivne? Da li ima neaktivnih/skrivenih artikala koje ne treba prikazivati online? | 🟠 Visok | Ako vraća neaktivne, moramo filtrirati. Ako ne → prikazaćemo artikle kojih nema. |
| **5** | **Koliko artikala ukupno vraća `getItems`?** Procjena: 200-400? Ili značajno više? | 🟠 Visok | Utiče na performanse sync-a i frekvenciju poziva. Sa <500 artikala sync je trivijalan. |
| **6** | **Šta tačno sadrži `image[]` polje?** Da li su to pune URL adrese (https://...), relativne putanje, ili base64 kodirane slike? Gdje su slike hostovane? | 🟠 Visok | Ako su URL-ovi → koristimo direktno. Ako putanje → trebamo znati base URL. Ako base64 → treba konverzija. Ako nema slika → ručni upload. |
| **7** | **Kako radi `details[]` polje?** Za Apple proizvode: da li su konfiguracije (memorija 128/256/512GB, boja) modelovane kao `details`, ili su to zasebni artikli? | 🟠 Visok | Određuje da li koristimo MedusaJS varijante (1 proizvod, više opcija) ili zasebne proizvode. |
| **8** | **Da li `group` polje odgovara kategorijama na sajtu?** (Mac, iPhone, iPad...) Koliko nivoa dubine ima? | 🟡 Srednji | Mapiranje na MedusaJS kategorije. Ako nema dovoljno granularnosti → ručno kreiranje kategorija. |
| **9** | **Da li se `price` i `price_rrp` razlikuju?** Koji od ta dva se koristi za online prodaju? | 🟠 Visok | Krivo postavljene cijene = direktan poslovni gubitak. Moramo znati koji je maloprodajni. |
| **10** | **Da li postoji poseban cijenovnik za online prodaju?** Ili su online i offline cijene iste? Ako su različite — koji `id_c` koristiti? | 🟠 Visok | Ako su iste → jednostavno. Ako su različite → moramo koristiti `id_c` parametar u svakom sync pozivu. |
| **11** | **Koliko često se mijenjaju cijene i zalihe?** Dnevno, sedmično, rijetko? | 🟡 Srednji | Određuje frekvenciju sync-a. Ako se mijenjaju rijetko → svakih 60 min je dovoljno. Ako često → svakih 15 min. |

### 3.3. ABACUS API — getWorkUnits: Magacini i lokacije

| # | Pitanje | Važnost | Uticaj |
|---|---------|---------|--------|
| **12** | **Koliko radnih jedinica (magacina) vraća `getWorkUnits`?** Da li su to Podgorica i Tivat? Da li postoji centralni magacin? | 🟠 Visok | Mapiranje na MedusaJS stock lokacije. Ako ima centralni → to je treća lokacija za zalihe. |
| **13** | **Koji `id_m` odgovara kojoj lokaciji?** Trebaju nam tačni ID-ovi za Podgorica i Tivat. | 🟠 Visok | Bez ovoga ne možemo prikazati "Na stanju u Podgorici: 3" vs "Na stanju u Tivtu: 1". |
| **14** | **Da li online narudžbine uvijek idu sa jednog magacina?** Ili zavisi od lokacije kupca? Ili uvijek iz centralnog? | 🟡 Srednji | Utiče na fulfillment logiku — iz kog magacina se šalje? |

### 3.4. ABACUS API — postSale: Narudžbine (ZA PRIPREMU FAZE 2)

> U Fazi 1 narudžbine se ručno unose u Abacus. Ali moramo razumjeti `postSale` za planiranje automatizacije.

| # | Pitanje | Važnost | Uticaj |
|---|---------|---------|--------|
| **15** | **Šta tačno kreira `postSale`?** Da li je to prodajni nalog, predračun, otpremnica, ili nešto drugo? | 🟡 Srednji | Da znamo šta operater danas ručno kreira i šta ćemo automatizovati u Fazi 2. |
| **16** | **Da li `postSale` automatski smanjuje stanje zaliha?** Ili se zalihe smanjuju tek kad se dokument potvrdi u Abacusu? | 🟡 Srednji | Utiče na to da li će sync zaliha odmah reflektovati online narudžbinu. |
| **17** | **Da li `postSale` pokreće fiskalizaciju?** Ili samo kreira dokument bez fiskalizacije? | 🟡 Srednji | Ključno za Fazu 2 — ako DA, onda je automatska fiskalizacija "besplatna" uz `postSale`. |
| **18** | **Da li `postSale` vraća ID kreiranog dokumenta?** Ako da, u kom polju response-a? | 🟡 Srednji | Za tracking narudžbine: MedusaJS order ID ↔ Abacus document ID. |
| **19** | **Da li `id_partner` u `postSale` mora biti prethodno kreiran?** Ili možemo slati narudžbinu bez partnera (za B2C kupce)? | 🟡 Srednji | Ako mora → moramo prvo `AddPartner` pa onda `postSale`. Ako ne → jednostavnije. |

### 3.5. ABACUS API — Tehnički detalji

| # | Pitanje | Važnost | Uticaj |
|---|---------|---------|--------|
| **20** | **Da li API ima rate limiting?** Koliko poziva po minuti/satu je dozvoljeno? | 🟡 Srednji | Ako postoji limit, moramo prilagoditi frekvenciju sync-a. |
| **21** | **Da li API podržava pagination?** Ili `getItems` uvijek vraća SVE artikle u jednom odgovoru? | 🟡 Srednji | Sa 200-400 artikala vjerovatno nije problem, ali treba potvrditi. |
| **22** | **Da li postoji mehanizam za detekciju promjena?** (timestamp poslednje izmjene, verzija, change feed?) | 🟡 Srednji | Ako DA → delta sync (samo promijenjene). Ako NE → full sync svaki put (ok za <500 artikala). |
| **23** | **Da li API radi 24/7?** Ili ima maintenance window? | 🟡 Srednji | Ako ima downtime → sync mora handlovati grešku gracefully. |
| **24** | **Šta se desi ako pošaljemo neispravan request?** Da li API uvijek vraća `Error` polje, ili može vratiti HTTP 500 bez tijela? | 🟢 Nizak | Za robustan error handling. |

### 3.6. WEBSHOP I MIGRACIJA

| # | Pitanje | Važnost | Uticaj |
|---|---------|---------|--------|
| **25** | **Da li ostajemo na domenu icentar.me?** | 🟠 Visok | DNS, SSL, SEO. |
| **26** | **Gdje će se hostovati MedusaJS?** Cloud ili lokalno? Ko je hosting provajder? | 🟠 Visok | Moramo znati infrastrukturu. |
| **27** | **Ko je razvio MedusaJS aplikaciju?** Da li će biti dostupni za koordinaciju? | 🟠 Visok | Saradnja za migraciju. |
| **28** | **Kakav je storefront?** Koji framework (Next.js, Gatsby, custom)? | 🟠 Visok | Moramo pregledati frontend kod. |
| **29** | **Da li AllSecure Payment Gateway ima API dokumentaciju?** | 🟠 Visok | Bez payment integracije nema checkout-a. |
| **30** | **Da li postoje sadržaji na WP sajtu koji se moraju migrirati?** Blog, landing stranice, SEO linkovi? | 🟡 Srednji | Obim WP → MedusaJS migracije. |

---

## 4. Tehnička arhitektura — Faza 1

### 4.1. Abacus Sync Modul (minimalan za Fazu 1)

```
src/modules/abacus-erp/
├── service.ts                     # AbacusErpService
│   ├── getItems(id_m?, ids?)      # Proizvodi, zalihe, cijene
│   └── getWorkUnits()             # Radne jedinice (magacini)
└── index.ts

src/workflows/abacus/
├── sync-products.ts               # getItems → MedusaJS products
└── sync-inventory.ts              # getItems + id_m → inventory levels

src/jobs/
├── sync-products-job.ts           # Cron: svakih 60 min
└── sync-inventory-job.ts          # Cron: svakih 30 min
```

> **Minimalan scope:** Samo čitanje iz Abacusa (getItems + getWorkUnits). Bez pisanja (postSale, AddPartner) — to je Faza 2.

### 4.2. Checkout flow — Faza 1

```
1. Kupac pretražuje katalog (sinhronizovan iz Abacusa svakih 30 min)
2. Kupac dodaje u korpu → MedusaJS provjerava lokalne zalihe
3. Checkout → AllSecure procesuira karticu (ili COD)
4. MedusaJS kreira narudžbinu → šalje email potvrdu kupcu
5. Operater vidi narudžbinu u MedusaJS admin → RUČNO obrađuje u Abacusu
6. Operater RUČNO fiskalizuje putem Abacus POS (kao do sada)
7. Operater ažurira status u MedusaJS → email kupcu "Poslato"
```

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

### Korak 1: Abacus Sync (1-2 sedmice)

- [ ] Razviti `src/modules/abacus-erp/` service
- [ ] Implementirati `sync-products` workflow
  - `group` → kategorije
  - `details[]` → varijante (boja, memorija)
  - `image[]` → product media
  - `price` / `price_rrp` → pricing
- [ ] Implementirati `sync-inventory` workflow
  - Po magacinu (Podgorica, Tivat)
  - Scheduled job: svakih 30 min
- [ ] Konfigurisati regione: Crna Gora, EUR, PDV 21%
- [ ] Setup stock lokacija
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

### Ukupna procjena Faze 1: **5-9 sedmica**

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
