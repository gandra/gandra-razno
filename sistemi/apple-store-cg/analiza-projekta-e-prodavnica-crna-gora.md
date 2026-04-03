# Analiza projekta: Online prodavnica — Crna Gora

> **Datum:** 02.04.2026.
> **Sastanak:** 03.04.2026. (inicijalni)
> **Cilj:** Integracija MedusaJS e-prodavnice sa Abacus ERP sistemom

---

## 1. Trenutno stanje (AS-IS)

### 1.1. Fizička infrastruktura

| Komponenta | Detalji |
|------------|---------|
| **Prodajni centri** | 2 lokacije u Crnoj Gori (Podgorica + drugi grad — za potvrdu) |
| **Magacini** | Najverovatnije 2 odvojena (po lokaciji) — **za potvrdu na sastanku** |
| **Asortiman** | Mali katalog — **<100 artikala** (tačan broj za potvrdu na sastanku) |
| **POS distributer** | POS4.me (Podgorica) — ekskluzivni distributer Abacus softvera |
| **ERP sistem** | Abacus ERP (Bencom d.o.o., Herceg Novi) |
| **Fiskalizacija** | Elektronska fiskalizacija prema crnogorskom zakonu (EFI sistem) |

### 1.2. Abacus ERP — Ključne karakteristike

**Developer:** Bencom d.o.o., Herceg Novi (od 2009, 700+ klijenata, 2300+ licenci)

**Moduli u upotrebi (za potvrdu):**

| Modul | Funkcija |
|-------|----------|
| Finansije | Glavna knjiga, PDV, bankovni izvodi, finansijski izvještaji |
| Roba/Materijal | Neograničen broj magacina, prosječna nabavna cijena, zalihe u realnom vremenu |
| Abacus POS | Maloprodaja, fiskalni štampač, fiskalizacija |
| Kadrovi/Primanja | Plate, doprinosi, poreske prijave |
| Analize | Izvještaji, analitike |

**Kritični nalaz — API:**
- **Abacus ERP (Bencom) NEMA javno dokumentovani API** (REST, SOAP, niti bilo koji drugi)
- Nema developer portala, SDK-a, ni tehničke dokumentacije za integraciju
- Integracije postoje samo unutar Abacus ekosistema (ERP ↔ POS, ERP ↔ RMS)
- Baza podataka: **nije javno objavljeno** koji engine koriste
- Za bilo kakvu integraciju sa spoljnim sistemima — **obavezan direktan kontakt sa Bencom-om**

> **Kontakt Bencom:** it@bencomltd.com | +381 31/332-302
> **Kontakt POS4.me:** info@pos4.me | +382 20 221 750

### 1.3. E-prodavnica — MedusaJS aplikacija (razvijeno)

**Verzija:** MedusaJS v2 (2.6.1)
**Lokacija koda:** `medusajs-e-store-app/medusa_sistemi/`

**Implementirani custom moduli:**

| Modul | Opis |
|-------|------|
| **Documents** | 7 entiteta (Document, Vendor, BankAccount, DocumentType, DocumentStatus, DocumentVersion, DocumentCounter). PDF generisanje faktura, B2B/B2C tipovi dokumenata, automatsko kreiranje na order.placed |
| **Legal Entity** | B2B podrška — pravna lica (PIB, matični broj, naziv firme). CustomerType klasifikacija (pravno/fizičko lice) |
| **Wishlist** | Lista želja po kupcu i sales channel-u, dijeljenje putem linka, validacija dostupnosti |
| **Product Custom Attributes** | Atributi po varijanti proizvoda, indeksiranje u Typesense |

**Integracije:**

| Sistem | Status |
|--------|--------|
| **Typesense** | Aktivan — full-text pretraga, faceted filtering, region-aware |
| **Mailtrap** | Konfigurisano ali isključeno — email notifikacije |
| **Magento migracija** | Plugin za migraciju proizvoda/kategorija iz Magento 2.x (dev/lokalno) |
| **Stripe/PayPal/COD** | Podržani u kodu (subscriber prepoznaje), ali plugini nisu učitani |
| **Redis** | Konfigurisano ali isključeno (cache, event bus, workflow engine) |

**Plugini:**
- `medusa-documents` (plugin verzija) — Customer type management + document framework
- `medusa-wishlist` — Wishlist funkcionalnost sa sharing-om

**Ključne tehničke odluke već donesene:**
- PostgreSQL + MikroORM 6
- Typesense za pretragu (ne Meilisearch)
- Lokalno skladištenje fajlova (PDF-ovi faktura)
- Event-driven arhitektura (subscribers za order lifecycle)
- Workflow engine za složene poslovne procese

### 1.4. Fiskalizacija u Crnoj Gori — Regulatorni okvir

Od 01.01.2021. obavezna elektronska fiskalizacija:
1. POS generiše **IKOF** (identifikacioni kod fiskalnog obveznika) — 32-karakterni kod
2. XML poruka se **digitalno potpisuje** kvalifikovanim certifikatom
3. Šalje se u realnom vremenu Poreskoj upravi (UPR/CFCR)
4. Poreska uprava vraća **JIKR** (jedinstveni identifikacioni kod) + QR kod
5. JIKR se štampa na računu

**Ovo važi i za online prodaju** — svaki račun mora proći fiskalizaciju.

### 1.5. Fiskalizacija — Trenutno nepoznato stanje (KRITIČNO)

> **Ne znamo kako se fiskalizacija trenutno obavlja u fizičkim prodavnicama.**
> Ovo je pitanje br. 1 za sutrašnji sastanak jer drastično utiče na obim posla.

**Ono što pretpostavljamo (za potvrdu):**
- Fizičke prodavnice koriste **Abacus POS** koji ima ugrađenu fiskalizaciju
- Abacus POS komunicira sa Poreskom upravom CG putem XML poruka
- Digitalni certifikati (Pošta CG ili CoreIT) su već nabavljeni i konfigurisani
- ENU (Elektronsko Naplatno Uređaj) registracija je već obavljena za fizičke prodajne tačke

**Ono što ne znamo:**
- Da li Abacus POS može fiskalizovati i račune koji dolaze sa online prodavnice?
- Da li postoji Abacus API/mehanizam za programsko kreiranje fiskalnog računa?
- Da li je za online prodavnicu potreban **zaseban ENU** registrovan u CRPS-u?
- Da li Abacus Invoicing (web verzija za fiskalizaciju) može biti alternativa?
- Ko ima pristup digitalnim certifikatima i može li se certifikat koristiti za oba kanala?

---

## 2. Željeno stanje (TO-BE)

### 2.1. Ciljna arhitektura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KUPAC (Web / Mobile)                        │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   MedusaJS E-PRODAVNICA                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ Katalog  │  │  Korpa   │  │ Checkout │  │ Upravljanje narudž.│  │
│  │ proizvoda│  │  (Cart)  │  │ & Plaćanje│  │ (Order Management)│  │
│  └────┬─────┘  └──────────┘  └────┬─────┘  └────────┬───────────┘  │
│       │                           │                  │              │
│  ┌────┴─────────────────────────┐ │                  │              │
│  │  INTEGRACIJA (middleware)    ├─┤──────────────────┘              │
│  │  ┌─────────────────────┐    │ │                                  │
│  │  │ Sync modul          │    │ │                                  │
│  │  │ (proizvodi, zalihe, │    │ │                                  │
│  │  │  narudžbine, cijene)│    │ │                                  │
│  │  └─────────────────────┘    │ │                                  │
│  └──────────┬──────────────────┘ │                                  │
│             │                    │                                  │
└─────────────┼────────────────────┼──────────────────────────────────┘
              │                    │
              ▼                    ▼
┌──────────────────────┐  ┌───────────────────────┐
│    ABACUS ERP        │  │   FISKALIZACIJA       │
│  ┌───────────────┐   │  │  (Poreska uprava CG)  │
│  │ Roba/Magacini │   │  │  IKOF → JIKR + QR     │
│  │ Finansije     │   │  └───────────────────────┘
│  │ POS           │   │
│  │ Kupci/Partneri│   │
│  └───────────────┘   │
│                      │
│  Magacin Podgorica   │
│  Magacin [Grad 2]    │
│  [Centralni magacin?]│
└──────────────────────┘
```

### 2.2. Scenariji fiskalizacije online narudžbina — UTICAJ NA SCOPE

> **Ovo je najvažnija tačka za razjašnjavanje na sastanku.**
> Zavisno od scenarija, obim posla se razlikuje za **3-8 sedmica** razvoja.

---

#### Scenario F1: Abacus POS fiskalizuje i online račune (IDEALAN)

```
Kupac → MedusaJS (narudžbina) → Abacus ERP/POS (kreira fiskalni račun)
                                        │
                                        ▼
                                 Poreska uprava CG
                                 (IKOF → JIKR + QR)
                                        │
                                        ▼
                                 Abacus → MedusaJS
                                 (JIKR, QR kod, PDF računa)
                                        │
                                        ▼
                                 MedusaJS → Kupac (email sa fiskalnim računom)
```

**Kako bi radilo:**
1. MedusaJS prima narudžbinu od kupca
2. MedusaJS šalje podatke o narudžbini Abacus-u (via API/file/DB)
3. Abacus POS kreira fiskalni račun, potpisuje ga certifikatom, šalje Poreskoj upravi
4. Abacus dobija JIKR + QR od Poreske uprave
5. MedusaJS dobija natrag JIKR/QR (via API/file/polling) i uključuje u email/PDF kupcu

**Preduslov:**
- Abacus POS mora moći da primi narudžbinu programski (ne samo sa fizičke kase)
- Mora postojati mehanizam za prosljeđivanje JIKR/QR nazad ka MedusaJS
- Online prodavnica možda treba zaseban ENU, ali isti certifikat

**Uticaj na scope:**

| Komponenta | Status |
|------------|--------|
| Fiskalizacioni engine u MedusaJS | ❌ NIJE POTREBAN |
| Digitalni certifikati | ❌ Koriste se Abacusovi |
| XML potpisivanje i slanje | ❌ Radi Abacus |
| Registracija ENU za online | ⚠️ Vjerovatno potrebna, ali admin posao |
| Integracija: Medusa → Abacus (narudžbina) | ✅ Potrebna |
| Integracija: Abacus → Medusa (JIKR, QR) | ✅ Potrebna |
| Ukupni dodatni posao | **~1-2 sedmice** (u okviru ERP integracije) |

**Procjena vjerovatnoće:** Srednja-Visoka. Abacus POS ima ugrađenu fiskalizaciju. Pitanje je samo da li može primiti narudžbinu programski (a ne samo sa fizičke kase). Abacus Invoicing (web verzija) je dodatni indikator da ovakav tok može biti podržan.

---

#### Scenario F2: Abacus ne može fiskalizovati online — koristimo Abacus Invoicing

```
Kupac → MedusaJS (narudžbina) → Abacus Invoicing (web portal za fiskalizaciju)
                                        │
                                        ▼
                                 Poreska uprava CG
                                 (IKOF → JIKR + QR)
```

**Kako bi radilo:**
Bencom nudi **Abacus Invoicing** — mobilna/web aplikacija za fiskalizaciju faktura, nezavisna od pune ERP/POS instalacije. Ako Abacus POS ne može programski primiti online narudžbine, ova aplikacija može biti alternativa.

**Preduslov:**
- Abacus Invoicing mora imati API ili programski interfejs
- Ili: operater ručno unosi online narudžbine u Abacus Invoicing

**Uticaj na scope:**

| Komponenta | Status |
|------------|--------|
| Fiskalizacioni engine u MedusaJS | ❌ NIJE POTREBAN |
| Automatizacija | ⚠️ Zavisi od Abacus Invoicing API-ja |
| Ručni rad | ⚠️ Moguć (operater kreira račun za svaku online narudžbinu) |
| Ukupni dodatni posao | **~1-3 sedmice** (zavisno od automatizacije) |

**Procjena vjerovatnoće:** Srednja. Dobar fallback ako F1 nije moguć.

---

#### Scenario F3: Samostalna fiskalizacija u MedusaJS (NAJVEĆI SCOPE)

```
Kupac → MedusaJS (narudžbina) → MedusaJS Fiskalni modul
                                        │
                                        ├── Generisanje IKOF koda
                                        ├── Kreiranje XML poruke
                                        ├── Digitalno potpisivanje (PKCS#12 certifikat)
                                        ├── HTTPS poziv ka Poreskoj upravi
                                        ▼
                                 Poreska uprava CG
                                 (verifikacija → JIKR + QR)
                                        │
                                        ▼
                                 MedusaJS → Kupac (račun sa JIKR + QR)
```

**Kako bi radilo:**
MedusaJS sam implementira kompletan fiskalizacioni protokol Crne Gore.

**Što bi trebalo razviti:**
1. **IKOF Generator** — algoritam za generisanje 32-karakternog identifikacionog koda
2. **XML Builder** — kreiranje XML poruke prema CG fiskalnoj šemi (specifičan XSD)
3. **XML Digital Signing** — potpisivanje PKI certifikatom (Pošta CG / CoreIT)
4. **HTTPS Client** — komunikacija sa serverom Poreske uprave u realnom vremenu
5. **JIKR Parser** — parsiranje odgovora, skladištenje QR koda
6. **Error handling** — retry logika, offline režim, timeout scenariji
7. **Fiskalni arhiv** — čuvanje svih fiskalnih dokumenata 10 godina (zakonska obaveza)
8. **ENU registracija** — online prodavnica mora biti registrovana kao zaseban ENU u CRPS
9. **Operator management** — svaki operater mora biti registrovan
10. **Korektivni računi** — mogućnost storniranja (negativan iznos, referencira originalni IKOF)

**Uticaj na scope:**

| Komponenta | Status |
|------------|--------|
| Fiskalizacioni engine | ✅ KOMPLETAN RAZVOJ — custom MedusaJS modul |
| Digitalni certifikat | ✅ Nabavka + integracija (PKCS#12) |
| Registracija ENU | ✅ Administrativni + tehnički posao |
| Testiranje sa Poreskom upravom | ✅ Potrebno (test okruženje ako postoji) |
| Pravna validacija | ✅ Mora provjeriti advokat/računovođa |
| Ukupni dodatni posao | **~5-8 sedmica** (samo fiskalizacija!) |

**Procjena vjerovatnoće da bude potreban:** Niska. Ovo je scenario samo ako Abacus ne može nikako pomoći sa fiskalizacijom. Ekonomski je neisplativo razvijati custom fiskalizaciju kada Abacus to već ima.

---

#### Scenario F4: Hibridni — polu-automatski (REALISTIČNI FALLBACK)

```
Kupac → MedusaJS (narudžbina) → Notifikacija operateru
                                        │
                                        ▼
                                 Operater u Abacus POS/ERP
                                 (ručno kreira račun za online narudžbinu)
                                        │
                                        ▼
                                 Abacus → Poreska uprava (automatski)
                                        │
                                        ▼
                                 Operater potvrđuje u MedusaJS (JIKR unos ili scan)
```

**Kako bi radilo:**
1. MedusaJS prima narudžbinu i šalje notifikaciju (email/dashboard) operateru
2. Operater u prodavnici kreira račun u Abacus POS na osnovu podataka iz narudžbine
3. Abacus POS automatski fiskalizuje račun (kao da je fizička prodaja)
4. Operater ažurira status narudžbine u MedusaJS (opciono unosi JIKR)

**Prednosti:** Nulti razvoj fiskalizacije. Koristi postojeći Abacus POS. Zakonski ispravno.
**Mane:** Ručni rad. Delay između narudžbine i fiskalizacije. Ne skalira se za veliki obim.

**Uticaj na scope:**

| Komponenta | Status |
|------------|--------|
| Fiskalizacioni engine u MedusaJS | ❌ NIJE POTREBAN |
| Notifikacioni sistem | ✅ Email/dashboard alert (jednostavno) |
| Admin panel za tracking | ✅ Pregled narudžbina sa statusom fiskalizacije |
| Ukupni dodatni posao | **~0.5-1 sedmica** |

**Procjena vjerovatnoće:** Realistični MVP pristup ako automatska integracija (F1/F2) nije odmah moguća.

---

#### Uporedni pregled scenarija — UTICAJ NA SCOPE

| Scenario | Ko fiskalizuje | Automatizacija | Dodatni scope | Rizik | Preporuka |
|----------|---------------|----------------|---------------|-------|-----------|
| **F1** — Abacus POS programski | Abacus | Potpuna | ~1-2 sed. | Nizak | **Cilj** |
| **F2** — Abacus Invoicing | Abacus Inv. | Djelimična/Potpuna | ~1-3 sed. | Srednji | Alternativa |
| **F4** — Polu-automatski | Abacus POS (ručno) | Ručna | ~0.5-1 sed. | Nizak | **MVP fallback** |
| **F3** — Custom u MedusaJS | MedusaJS | Potpuna | ~5-8 sed. | Visok | Izbjegavati |

> **Ključna poruka:** Razlika između F1 i F3 je **4-7 sedmica razvoja**.
> Zato je sutrašnje razjašnjavanje o fiskalizaciji **najvažnije pitanje sastanka**.

---

#### ODLUKA: Ko treba da bude vlasnik fiskalizacije — Abacus ili MedusaJS?

Ovo je **arhitekturalna odluka** koja se donosi na sastanku i koja oblikuje cijeli projekat.

**Opcija A: Abacus je vlasnik fiskalizacije (PREPORUČENO)**

```
MedusaJS ──narudžbina──→ Abacus ──fiskalizuje──→ Poreska uprava
                                                        │
                                         JIKR + QR ←────┘
```

| Aspekt | Detalji |
|--------|---------|
| **Princip** | Abacus je **jedini sistem koji komunicira sa Poreskom upravom**. MedusaJS šalje narudžbine Abacus-u, Abacus fiskalizuje i vraća potvrdu. |
| **Zašto da** | Abacus VEĆ IMA fiskalizaciju — zašto graditi nešto što postoji? Jedan sistem, jedan certifikat, jedna tačka za reviziju. Fizička i online prodaja imaju isti fiskalni tok — jednostavnije za računovodstvo i poreske kontrole. |
| **Zašto ne** | Zavisnost od Abacus-a za svaku online transakciju. Ako Abacus padne, online prodavnica ne može izdavati račune. Latencija (Medusa mora čekati Abacus odgovor). |
| **Preduslov** | Abacus mora imati NEKI mehanizam za prijem narudžbina programski (API, file watch, DB insert, Abacus Invoicing API...) |
| **Uticaj na naš scope** | **Minimalan** — mi gradimo samo integraciju za prosljeđivanje narudžbine + prijem potvrde. Nulti razvoj fiskalizacionog engine-a. |
| **Scenariji** | F1 (automatski), F2 (Invoicing), F4 (ručno) |

**Opcija B: MedusaJS je vlasnik fiskalizacije**

```
MedusaJS ──fiskalizuje──→ Poreska uprava
    │                           │
    │        JIKR + QR ←────────┘
    │
    └──narudžbina──→ Abacus (samo za ERP/magacin, BEZ fiskalizacije)
```

| Aspekt | Detalji |
|--------|---------|
| **Princip** | MedusaJS **sam komunicira sa Poreskom upravom**. Abacus prima samo informaciju o narudžbini za potrebe magacina/finansija, ali ne fiskalizuje online račune. |
| **Zašto da** | Potpuna nezavisnost od Abacus-a za online kanal. Brži odgovor kupcu (nema čekanja na Abacus). Moderan stack, lakše za održavanje dugoročno. |
| **Zašto ne** | **Ogroman razvoj** (~5-8 sedmica samo za fiskalizaciju). Potreban zaseban digitalni certifikat i ENU. Dva sistema fiskalizuju — komplikuje reviziju i PDV prijave. Svaka promjena u CG fiskalnim propisima zahtijeva promjene na DVA mjesta. Dupli trošak održavanja. |
| **Preduslov** | Nabavka certifikata, registracija ENU, implementacija XML potpisivanja, testiranje sa Poreskom upravom. |
| **Uticaj na naš scope** | **Masivan** — custom fiskalizacioni modul, PKI infrastruktura, compliance testiranje. |
| **Scenariji** | Samo F3 |

**Preporuka:**

| Kriterijum | Abacus (Opcija A) | MedusaJS (Opcija B) |
|------------|-------------------|---------------------|
| Razvoj | ~1-2 sed (integracija) | ~5-8 sed (engine) |
| Trošak | Nizak | Visok |
| Kompleksnost | Niska | Visoka |
| Nezavisnost od Abacus-a | ❌ Zavisan | ✅ Nezavisan |
| Jedan izvor istine za fiskalizaciju | ✅ Da | ❌ Ne (dva sistema) |
| Računovodstvena jednostavnost | ✅ Sve u Abacusu | ⚠️ Razdvojeno |
| Revizija / poreski nadzor | ✅ Jednostavno | ⚠️ Komplikovano |
| Održavanje propisa | ✅ Bencom ažurira | ❌ Mi ažuriramo |
| Skalabilnost online kanala | ⚠️ Bottleneck na Abacusu | ✅ Nezavisan scaling |

> **Jasna preporuka: Opcija A — Abacus fiskalizuje.**
>
> Čak i u najgorem slučaju (F4: operater ručno), ovo je bolje od gradnje custom fiskalizacije.
> MedusaJS treba da se bavi onim u čemu je dobar — e-commerce. Abacus treba da se bavi onim u čemu je dobar — fiskalizacija i računovodstvo u CG.
>
> Opcija B ima smisla SAMO ako:
> - Abacus apsolutno ne može primiti podatke ni na koji način
> - I polu-automatski tok (F4) je neprihvatljiv
> - I postoji dugoročna strategija zamjene Abacus-a

**Pitanje za sastanak:**

> *"Naša preporuka je da Abacus ostane vlasnik fiskalizacije i za online kanal — to značajno smanjuje obim posla i rizik. Da li postoji razlog zašto bi MedusaJS trebalo sam da fiskalizuje? Da li vidite problem u tome da online narudžbine prolaze kroz Abacus za fiskalizaciju?"*

---

### 2.3. Ključni tokovi podataka

| Tok | Pravac | Opis |
|-----|--------|------|
| **Proizvodi** | ERP → Medusa | Master podaci o proizvodima (naziv, cijena, šifra, kategorija) |
| **Zalihe** | ERP → Medusa | Stanje zaliha po magacinu, u realnom vremenu ili periodično |
| **Cijene** | ERP → Medusa | Maloprodajne cijene, popusti, akcije |
| **Narudžbine** | Medusa → ERP | Online narudžbine za obradu, fakturisanje i isporuku |
| **Kupci** | Medusa ↔ ERP | Sinhronizacija podataka o kupcima (B2B: PIB, matični broj) |
| **Fiskalizacija** | Zavisi od scenarija (vidi 2.2.) | F1/F2: Abacus fiskalizuje; F3: MedusaJS fiskalizuje; F4: operater ručno |
| **Dokumenti** | Medusa (generisanje) | Fakture, otpremnice, potvrde narudžbina |

### 2.4. Rezervacija zaliha tokom kupovine — CHECK → RESERVE → CONFIRM/RELEASE

> **Ovo je ključan arhitekturalni tok koji zavisi od mogućnosti Abacus-a.**
> Određuje da li kupac može biti siguran da će dobiti ono što naruči.

#### Problem

Kupac dodaje artikal u korpu. Između tog trenutka i završetka plaćanja može proći 5-30 minuta. U tom periodu:
- Drugi online kupac može naručiti isti artikal
- Operater u fizičkoj prodavnici može prodati zadnji komad sa kase
- Rezultat: **overselling** — prodali smo ono što nemamo

#### Idealan tok: CHECK → RESERVE → CONFIRM / RELEASE

```
                            KUPAC
                              │
                    ┌─────────▼──────────┐
                    │  1. DODAJ U KORPU   │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐         ┌──────────────────────┐
                    │  2. CHECK           │────────→│  Abacus: provjeri    │
                    │  (provjera stanja)  │←────────│  raspoloživu količ.  │
                    └─────────┬──────────┘         └──────────────────────┘
                              │
                      Raspoloživo?
                     /           \
                   DA             NE → "Nema na stanju" (kupac vidi odmah)
                   │
          ┌────────▼─────────┐         ┌──────────────────────────────┐
          │  3. RESERVE       │────────→│  Abacus: ZAKLJUČAJ količinu  │
          │  (rezervacija)    │←────────│  (smanji raspoloživu, ali   │
          └────────┬─────────┘         │   ne pravi prodajni dokument) │
                   │                    └──────────────────────────────┘
                   │
          ┌────────▼─────────┐
          │  4. CHECKOUT      │
          │  (unos adrese,    │
          │   izbor dostave,  │  ← Kupac ima X minuta da završi
          │   plaćanje)       │
          └────────┬─────────┘
                   │
              Uspješno?
             /         \
           DA           NE (greška plaćanja, timeout, odustanak)
           │             │
  ┌────────▼────────┐   ┌──────────▼──────────────┐   ┌────────────────────────┐
  │  5a. CONFIRM    │   │  5b. RELEASE             │──→│  Abacus: OTKLJUČAJ     │
  │  (potvrda)      │   │  (otkazivanje rezerv.)   │   │  količinu (vrati u     │
  └────────┬────────┘   └──────────────────────────┘   │  raspoloživu zalihu)   │
           │                                            └────────────────────────┘
           ▼
  ┌──────────────────┐         ┌─────────────────────────────┐
  │  Abacus: CONFIRM │────────→│  Kreira prodajni dokument,   │
  │  (kreiranje      │         │  trajno smanjuje zalihu,     │
  │   narudžbine)    │         │  pokreće fiskalizaciju       │
  └──────────────────┘         └─────────────────────────────┘
```

#### Scenariji za rezervaciju zaliha — zavisno od Abacus mogućnosti

---

**Scenario Z1: Abacus podržava programsku rezervaciju (IDEALAN)**

| Aspekt | Detalji |
|--------|---------|
| **Preduslov** | Abacus ima API/mehanizam za: (1) provjeru stanja, (2) kreiranje rezervacije, (3) potvrdu, (4) otkazivanje |
| **Kako radi** | MedusaJS poziva Abacus na checkout start → Abacus zaključava količinu → MedusaJS završava plaćanje → Abacus potvrđuje ili otključava |
| **Mehanizam zaključavanja** | Abacus kreira "pending" dokument (predračun, rezervacija) koji privremeno smanjuje raspoloživu količinu ali ne pravi konačnu prodaju |
| **Otključavanje pri grešci** | Abacus briše/stornira pending dokument → količina se vraća u raspoloživu |
| **Timeout** | Ako MedusaJS ne pošalje ni CONFIRM ni RELEASE u roku od X minuta → Abacus automatski otključava (ako podržava TTL na rezervaciji) |
| **Procjena** | ⚠️ Zavisi od Abacus mogućnosti — vjerovatno zahtijeva podršku Bencom-a |

**MedusaJS implementacija za Z1:**
```
src/modules/abacus-erp/
  service.ts:
    checkStock(sku, quantity, locationId)     → boolean + raspoloživa količina
    reserveStock(sku, quantity, locationId)    → reservationId
    confirmReservation(reservationId)          → orderId u Abacusu
    releaseReservation(reservationId)          → void (otključava)

src/workflows/checkout/
  reserve-stock-step.ts                       → poziva reserveStock()
  confirm-stock-step.ts                       → poziva confirmReservation()
  release-stock-step.ts (KOMPENZACIJA)        → poziva releaseReservation()
```

MedusaJS Workflow sa kompenzacijom:
```
createWorkflow("checkout-with-reservation", (input) => {
  // Korak 1: Rezerviši u Abacusu
  const reservation = reserveStockStep(input)
    .compensate(releaseStockStep)    // ← AKO BILO ŠTA PADNE POSLE OVOG KORAKA,
                                     //    AUTOMATSKI SE POZIVA RELEASE

  // Korak 2: Procesiraj plaćanje
  const payment = processPaymentStep(input)
    .compensate(refundPaymentStep)

  // Korak 3: Potvrdi rezervaciju u Abacusu
  const order = confirmReservationStep(reservation)

  return order
})
```

> **Ključno:** MedusaJS workflow engine ima ugrađene **kompenzacione funkcije**. Ako korak 2 (plaćanje) padne, automatski se poziva `releaseStockStep` koji otključava količinu u Abacusu. Nije potrebna ručna intervencija.

---

**Scenario Z2: Abacus nema rezervaciju, ali ima provjeru stanja (REALAN)**

| Aspekt | Detalji |
|--------|---------|
| **Preduslov** | Abacus dozvoljava provjeru stanja (read-only) ali nema koncept rezervacije |
| **Kako radi** | MedusaJS provjerava stanje na Abacusu u trenutku checkout-a. Ako je raspoloživo → procesuira. Nema zaključavanja — postoji mali rizik od race condition-a. |
| **Race condition** | Dva kupca istovremeno vide "1 komad na stanju" → oba naruče → overselling |
| **Mitigacija** | Sa <100 artikala i niskim prometom, rizik je minimalan. Dodati double-check nakon plaćanja. Operater ručno rješava konflikte. |

**Tok:**
```
Kupac → Checkout → MedusaJS provjerava Abacus stanje (CHECK samo, bez RESERVE)
  → Raspoloživo? → DA → Plaćanje → Uspješno?
    → DA → Pošalji narudžbinu Abacusu → Abacus smanjuje zalihu
    → NE → Obavijesti kupca, nema promjene na Abacusu
  → NE → "Nema na stanju"
```

**Rizik overselling-a:**

| Obim prodaje | Rizik | Komentar |
|-------------|-------|----------|
| <10 narudžbina/dan | Zanemarljiv | Za mali katalog i novi e-shop, ovo je realan obim |
| 10-50 narudžbina/dan | Nizak | Povremeni konflikti, rješavaju se operaterski |
| 50+ narudžbina/dan | Srednji | Treba razmotriti Z1 ili Z3 |

---

**Scenario Z3: Rezervacija u MedusaJS-u, ne u Abacusu (PRAGMATIČAN)**

| Aspekt | Detalji |
|--------|---------|
| **Preduslov** | Periodični sync zaliha Abacus → MedusaJS (makar 1-2x dnevno) |
| **Kako radi** | MedusaJS sam upravlja zarezerviranim količinama interno. Abacus ostaje izvor istine, ali MedusaJS vodi "shadow" inventar sa rezervacijama. |
| **Zaključavanje** | MedusaJS Inventory modul ima ugrađen **ReservationItem** — rezerviše količinu na stock lokaciji za pending narudžbinu |
| **Otključavanje** | MedusaJS automatski briše ReservationItem ako: (1) plaćanje ne uspije (workflow kompenzacija), (2) korpa istekne (TTL), (3) kupac odustane |
| **Sync sa Abacusom** | Nakon potvrde narudžbine, MedusaJS šalje narudžbinu Abacusu → Abacus smanjuje svoju zalihu |

**Tok:**
```
[Periodični sync]  Abacus ──zalihe──→ MedusaJS (1-2x dnevno, ili ručno)

[Kupovina]
Kupac → Korpa → MedusaJS provjerava LOKALNE zalihe (već sinhronizovane)
  → Raspoloživo? → DA → MedusaJS kreira ReservationItem (zaključava lokalno)
    → Checkout → Plaćanje
      → Uspješno → MedusaJS potvrđuje narudžbinu + šalje Abacusu
      → Neuspješno → MedusaJS briše ReservationItem (otključava lokalno)
  → NE → "Nema na stanju"
```

**Prednosti:**
- MedusaJS v2 **već ima ugrađen mehanizam** za ovo (Inventory Module + ReservationItem)
- Ne zavisi od Abacus API-ja za real-time operacije
- Brz odgovor kupcu (nema čekanja na Abacus za svaku provjeru)

**Mane:**
- Lokalna kopija zaliha može biti zastarjela (fizička prodaja u međuvremenu)
- Moguć overselling ako se fizički proda zadnji komad između dva sync-a

**Mitigacija:**
- Safety buffer: prikazivati "Na stanju" samo ako je količina ≥ 2 (zadržati 1 kao buffer)
- Ili: nakon plaćanja, double-check sa Abacusom prije konačne potvrde
- Ili: čekati fazu 2 da se automatizuje sync zaliha u kraćim intervalima

---

**Scenario Z4: Bez provjere stanja — ručno upravljanje (MVP MINIMUM)**

| Aspekt | Detalji |
|--------|---------|
| **Preduslov** | Nikakav |
| **Kako radi** | Svi proizvodi na sajtu su "Na stanju" (ili bez prikaza stanja). Operater ručno provjerava raspoloživost i potvrđuje narudžbinu. Ako nije raspoloživo — kontaktira kupca. |
| **Zaključavanje** | Nema |
| **Otključavanje** | N/A |
| **Procjena** | Prihvatljivo za prvih par sedmica sa <100 artikala i malim obimom narudžbina |

---

#### Uporedni pregled scenarija za zalihe

| Scenario | Provjera stanja | Rezervacija | Otključavanje | Rizik overselling | Zavisnost od Abacus API | Scope |
|----------|-----------------|-------------|---------------|-------------------|------------------------|-------|
| **Z1** — Abacus rezervacija | Abacus (real-time) | Abacus | Abacus (auto/manual) | Nulti | Potpuna | ~2-3 sed |
| **Z2** — Abacus check-only | Abacus (real-time) | Nema | N/A | Nizak | Djelimična (read) | ~1 sed |
| **Z3** — MedusaJS rezervacija | MedusaJS (lokalno) | MedusaJS | MedusaJS (automatski) | Nizak-Srednji | Nema (periodični sync) | ~1-2 sed |
| **Z4** — Ručno | Nema | Nema | N/A | Srednji | Nema | ~0 |

#### Mehanizmi otključavanja (RELEASE) — detaljno

Šta god da se desi, zaključana količina se MORA otključati. Ovo su mehanizmi:

| Situacija | Z1 (Abacus) | Z3 (MedusaJS) |
|-----------|-------------|---------------|
| **Plaćanje ne prođe** | MedusaJS workflow kompenzacija poziva `releaseReservation(id)` na Abacusu | MedusaJS automatski briše `ReservationItem` (workflow kompenzacija) |
| **Kupac odustane** (zatvori browser) | **Timeout (TTL)** — Abacus mora automatski otključati nakon X minuta. Ako nema TTL, MedusaJS cron job čisti stale rezervacije. | MedusaJS cron job: `cleanup-expired-reservations` — briše ReservationItem starije od X minuta (npr. 30 min) |
| **Greška u sistemu** (MedusaJS pad) | **Najkritičniji scenario.** Ako MedusaJS padne posle RESERVE a prije CONFIRM/RELEASE → količina ostaje zaključana na Abacusu. **Mora postojati:** (1) TTL na Abacusu, ILI (2) MedusaJS recovery job koji pri restartu čisti pending rezervacije | MedusaJS pri restartu čita pending ReservationItem-e i verificira da li je narudžbina završena. Ako nije → briše rezervaciju. |
| **Timeout korpe** (kupac ne završi za 30 min) | MedusaJS scheduled job poziva `releaseReservation()` za sve rezervacije starije od TTL-a | MedusaJS scheduled job briše istekle ReservationItem-e |
| **Parcijalni checkout** (2 od 3 artikla uspješno) | Workflow kompenzacija: otključavaju se SVI artikli, ne samo neuspješni (atomičnost — ili sve ili ništa) | Isto — MedusaJS workflow rollback briše sve ReservationItem-e iz tog checkout-a |

#### Preporuka za mali katalog (<100 artikala)

> **Za MVP: Scenario Z3 (MedusaJS rezervacija) ili Z4 (ručno).**
>
> Sa <100 artikala i očekivano malim obimom narudžbina u početku:
> - Z4 je najjednostavniji (nula razvoja), prihvatljiv za prvih par sedmica
> - Z3 je bolji jer MedusaJS v2 **već ima ugrađenu podršku** za ReservationItem —
>   samo treba konfigurisati, ne razvijati od nule
> - Z1 je cilj za fazu 2 — ali zavisi od Abacus API-ja
>
> **Ključno pitanje za sastanak:**
> *"Da li Abacus podržava koncept rezervacije zaliha — da privremeno zaključamo
> količinu za online kupca, pa potvrdimo ili otključamo? Ili barem: da li možemo
> programski provjeriti trenutno stanje zaliha u Abacusu?"*

---

### 2.5. Funkcionalnosti online prodavnice

**Minimalni scope (MVP):**
- Katalog proizvoda sinhronizovan sa ERP-om
- Online narudžbina sa potvrdom
- Plaćanje (kartica + pouzeće)
- Provjera raspoloživosti po magacinu/lokaciji
- Fiskalni račun za svaku transakciju
- Email notifikacija kupcu

**Prošireni scope (faza 2):**
- Click & Collect (naruči online, preuzmi u prodavnici)
- B2B portal (pravna lica, ugovorne cijene)
- Loyalty program
- Wishlist (već implementiran)
- Napredna pretraga (Typesense — već implementiran)

---

## 3. Ključna pitanja za prvi sastanak

### 3.1. KRITIČNA PITANJA — Integracija sa ERP-om

> Ova pitanja određuju izvodljivost i pristup cijelom projektu.

| # | Pitanje | Zašto je bitno |
|---|---------|----------------|
| **1** | **Da li Abacus ERP ima API ili bilo koji mehanizam za programsku razmjenu podataka?** (REST, SOAP, file export/import, direktan pristup bazi) | Bez API-ja ne možemo automatizovati integraciju. Moramo znati šta je tehnički moguće. |
| **2** | **Ko je vaš kontakt u Bencom-u (developer Abacus-a)?** Da li su otvoreni za saradnju na integraciji? | Potrebna nam je direktna komunikacija sa Bencom timom. |
| **3** | **Koja je baza podataka Abacus ERP-a?** (SQL Server, PostgreSQL, nešto drugo?) | Ako nema API-ja, direktan pristup bazi može biti alternativa (samo za čitanje). |
| **4** | **Da li Abacus podržava export/import podataka?** (CSV, XML, JSON, EDI?) Koji formati? | File-based integracija je najčešći fallback kada nema API-ja. |
| **5** | **Da li POS4.me ima iskustva sa integracijom Abacus-a sa spoljnim sistemima?** | Kao ekskluzivni distributer, možda imaju rješenja ili kontakte. |

### 3.2. ZALIHE I REZERVACIJA — PITANJA (vidi sekciju 2.4)

> Ova pitanja određuju da li možemo garantovati kupcu raspoloživost u trenutku kupovine.

| # | Pitanje | Zašto je bitno | Referenca |
|---|---------|----------------|-----------|
| **6** | **Da li Abacus podržava koncept REZERVACIJE zaliha?** Tj. da li može privremeno zaključati količinu za pending narudžbinu, bez kreiranja konačnog prodajnog dokumenta? | Ako DA → scenario Z1 (idealan, nulti rizik overselling). Ako NE → moramo koristiti Z2 ili Z3. | Scenario Z1 |
| **7** | **Ako podržava rezervaciju — da li postoji automatski TIMEOUT (TTL)?** Tj. da li se zaključana količina automatski otključava nakon X minuta ako narudžbina nije potvrđena? | Bez TTL-a, ako MedusaJS padne posle rezervacije — količina ostaje zaključana zauvijek. Moramo znati da li Abacus sam čisti stale rezervacije ili moramo mi. | Z1 — otključavanje |
| **8** | **Da li možemo barem PROGRAMSKI PROVJERITI trenutno stanje zaliha** za određeni artikal/magacin? (API, DB query, file export u realnom vremenu?) | Ako DA → Z2 (provjera bez rezervacije, nizak rizik). Ako NE → Z4 (ručno, ili oslanjamo se na periodični sync). | Scenario Z2 |
| **9** | **Da li se dešava da artikal bude pri kraju zalihe** (1-2 komada)? Koliko često? | Ako su zalihe uglavnom visoke (10+ komada) → rizik overselling-a je zanemarljiv čak i bez rezervacije. Ako su česti artikli sa 1-2 komada → rezervacija je kritičnija. | Svi scenariji |
| **10** | **Kako se sada rješavaju situacije kad POS proda zadnji komad?** Da li sistem automatski ažurira stanje ili je ručno? | Da razumijemo koliko je Abacus "real-time" za fizičku prodaju — ista logika važi i za online. | Kontekst |

### 3.3. INFRASTRUKTURNA PITANJA

| # | Pitanje | Zašto je bitno |
|---|---------|----------------|
| **11** | **Koliko magacina postoji?** Da li su odvojeni po lokaciji ili postoji centralni? | Određuje konfiguraciju stock lokacija u MedusaJS i logiku dostupnosti. |
| **12** | **Koji je drugi grad** (pored Podgorice) gdje je prodajni centar? | Potrebno za konfiguraciju regiona i isporuke. |
| **13** | **Gdje će se hostovati MedusaJS aplikacija?** Cloud (AWS, Azure, DigitalOcean) ili lokalno? | Utiče na latenciju, sigurnost i troškove. |
| **14** | **Da li postoji existing web sajt / domen za online prodavnicu?** | Potrebno za deployment i SEO konfiguraciju. |
| **15** | **Kakva je internet infrastruktura između lokacija?** VPN, cloud, javna mreža? | Utiče na arhitekturu integracije (real-time vs batch). |

### 3.4. POSLOVNI ZAHTJEVI

| # | Pitanje | Zašto je bitno |
|---|---------|----------------|
| **16** | **Koliko tačno artikala ide na online prodavnicu?** (procjena: <100). Da li su to svi proizvodi iz ERP-a ili podskup? Da li se asortiman često mijenja? | Mali katalog drastično pojednostavljuje sync — moguć čak i ručni unos za MVP. |
| **17** | **Koji načini plaćanja su potrebni?** (Kartica, pouzeće, virman, e-banking) | Određuje payment provider integraciju. |
| **18** | **Koji je model isporuke?** Vlastita dostava, kurirska služba, preuzimanje u prodavnici? | Utiče na fulfillment module i integraciju. |
| **19** | **Da li prodajete i B2B?** Pravnim licima, sa ugovornim cijenama? | B2B modul je već djelimično implementiran u MedusaJS. |
| **20** | **Kakva je politika cijena?** Iste online i offline? Posebne online akcije? | Utiče na sync logiku cijena sa ERP-om. |
| **21** | **Kakva je politika povrata/reklamacija za online narudžbine?** | Utiče na return/refund workflow. |

### 3.5. FISKALIZACIJA — KLJUČNA PITANJA (UTIČU NA SCOPE!)

> **Ova sekcija je najbitnija za sutrašnji sastanak.**
> Odgovori na ova pitanja određuju da li je posao na fiskalizaciji 1 sedmica ili 8 sedmica.
> Vidi sekciju 2.2. za detaljnu analizu scenarija.

| # | Pitanje | Zašto je bitno | Referenca |
|---|---------|----------------|-----------|
| **22** | **Kako TRENUTNO radite fiskalizaciju u fizičkim prodavnicama?** Opišite tok: operater kuca račun → šta se dešava? | Da razumijemo postojeći tok i šta možemo ponovo iskoristiti za online prodaju. | — |
| **23** | **Da li Abacus POS može primiti narudžbinu PROGRAMSKI** (ne sa fizičke kase) i automatski generisati fiskalni račun? | Ako DA → scenario F1, minimalan dodatni posao. Ako NE → moramo tražiti alternativu. | Scenario F1 |
| **24** | **Da li koristite Abacus Invoicing** (web/mobilna verzija za fiskalizaciju)? Da li ima API? | Alternativni kanal za fiskalizaciju online narudžbina. | Scenario F2 |
| **25** | **Da li je za online prodavnicu potreban zaseban ENU** (Elektronsko Naplatno Uređaj) u CRPS-u, ili može koristiti isti kao fizička prodavnica? | Administrativni preduslov — bez registrovanog ENU ne možemo fiskalizovati. | Svi scenariji |
| **26** | **Ko ima pristup digitalnim certifikatima za potpisivanje?** (Pošta CG / CoreIT) Da li se certifikat može koristiti sa više sistema? | Ako MedusaJS mora sam potpisivati, treba pristup certifikatu (PKCS#12 fajl + lozinka). | Scenario F3 |
| **27** | **Da li postoji TEST OKRUŽENJE** za fiskalizaciju kod Poreske uprave? | Za razvoj i testiranje bez slanja pravih računa. | Scenario F3 |
| **28** | **Koji je PDV režim za vaše proizvode?** Standardna stopa (21%), redukovana (7%), oslobođenje? Da li ima proizvoda sa različitim stopama? | Za ispravno obračunavanje poreza. Utiče na Documents modul. | Svi scenariji |
| **29** | **Da li ste spremni na polu-automatski pristup za MVP?** (operater ručno kreira fiskalni račun u Abacus-u za online narudžbine) | Realistični fallback ako potpuna automatizacija nije odmah moguća. Omogućava brži go-live. | Scenario F4 |
| **30** | **Da li ste razgovarali sa Bencom-om o ovom projektu?** Da li znaju da planirate online prodavnicu? | Bencom je ključan partner — njihova kooperativnost određuje izvodljivost scenarija F1/F2. | F1, F2 |

### 3.6. TEHNIČKA PITANJA (ZA DEVELOPMENT TIM)

| # | Pitanje | Zašto je bitno |
|---|---------|----------------|
| **31** | **Koja verzija Abacus ERP-a je instalirana?** | Može uticati na dostupne opcije integracije. |
| **32** | **Da li developeri imaju pristup Abacus bazi ili nekom admin panelu?** | Za razumijevanje strukture podataka. |
| **33** | **Kakav je frontend?** Ko ga je razvio? Koja tehnologija (Next.js, Gatsby, custom)? | MedusaJS backend, ali šta je storefront? |
| **34** | **Da li je Magento migracija završena?** Postoji plugin za migraciju iz Magento-a u kodu. | Da znamo da li je ovo legacy ili aktivan zahtjev. |
| **35** | **Ko održava MedusaJS aplikaciju?** Interni tim ili outsource? | Za koordinaciju razvoja. |

---

## 4. Pristupi za integraciju — Analiza opcija

### Opcija A: API integracija (idealan scenario)

```
MedusaJS  ←──REST/SOAP──→  Abacus ERP API
```

**Preduslov:** Bencom obezbijedi API ili middleware.

| Aspekt | Detalji |
|--------|---------|
| **Kako radi** | MedusaJS custom modul (`src/modules/abacus/`) sa service klasom koja komunicira sa Abacus API-jem. Workflows za svaku sync operaciju. Subscribers za real-time evente. |
| **Prednosti** | Real-time sync, čist kod, standardni pristup, lako održavanje |
| **Mane** | Zavisi od Bencom-a da obezbijedi API — trenutno ne postoji javno |
| **Procjena** | ⚠️ Malo vjerovatno bez angažmana Bencom-a |

### Opcija B: Database-level integracija (read-only)

```
MedusaJS  ←──SQL (read-only)──→  Abacus DB
MedusaJS  ──file/API──→  Abacus (za narudžbine)
```

**Preduslov:** Pristup Abacus bazi (barem read-only) + poznavanje šeme.

| Aspekt | Detalji |
|--------|---------|
| **Kako radi** | Scheduled jobs u MedusaJS čitaju podatke direktno iz Abacus baze (proizvodi, zalihe, cijene). Narudžbine se šalju nazad putem file export-a ili manualnog unosa. |
| **Prednosti** | Nezavisan od Bencom API-ja, brže za implementaciju |
| **Mane** | Krhko (promjena šeme baze može pokvariti sync), jednosmjerno za automatizaciju, sigurnosni rizik direktnog pristupa bazi |
| **Procjena** | ⚠️ Moguće ako dobijemo pristup i dokumentaciju šeme |

### Opcija C: File-based integracija (CSV/XML)

```
Abacus ERP  ──export CSV/XML──→  [shared folder]  ──import──→  MedusaJS
MedusaJS    ──export CSV/XML──→  [shared folder]  ──import──→  Abacus ERP
```

**Preduslov:** Abacus podržava export/import u nekom formatu.

| Aspekt | Detalji |
|--------|---------|
| **Kako radi** | Periodični export iz Abacus-a (proizvodi, zalihe) u CSV/XML. MedusaJS scheduled job čita fajlove i ažurira podatke. Online narudžbine se exportuju u format koji Abacus može importovati. |
| **Prednosti** | Najjednostavniji pristup, ne zahtijeva API, Abacus vjerovatno podržava neku vrstu exporta |
| **Mane** | Nije real-time (delay od minuta do sati), ručni koraci mogući, greške u parsiranju |
| **Procjena** | ✅ Najvjerovatniji inicijalni pristup |
| **Frekvencija** | Proizvodi: 1x dnevno (ali sa <100 artikala, i ručno je izvodljivo); Zalihe: svakih 15-30 min; Narudžbine: real-time (ili svakih 5 min) |

### Opcija D: Middleware / iPaaS rješenje

```
MedusaJS  ←──API──→  Middleware (n8n / Make / custom)  ←──→  Abacus ERP
```

**Preduslov:** Middleware koji može komunicirati sa oba sistema.

| Aspekt | Detalji |
|--------|---------|
| **Kako radi** | Intermedijarni sloj (n8n, Make/Integromat, ili custom Node.js servis) koji čita iz Abacus-a i piše u MedusaJS putem Admin API-ja, i obrnuto. |
| **Prednosti** | Razdvaja sisteme, fleksibilno, vizuelni workflow builder (n8n), monitoring |
| **Mane** | Dodatna infrastruktura za održavanje, latencija, kompleksnost |
| **Procjena** | ✅ Dobar pristup ako Abacus ima barem file export |

### Opcija E: Ručni unos proizvoda u MedusaJS (MOGUĆE ZBOG MALOG KATALOGA)

```
Operater ──ručno unosi/ažurira <100 artikala──→ MedusaJS Admin
Zalihe: Abacus ──CSV/ručno──→ MedusaJS (periodično)
Narudžbine: MedusaJS ──notifikacija──→ Operater ──ručno──→ Abacus
```

**Preduslov:** Nikakav — odmah izvodljivo.

| Aspekt | Detalji |
|--------|---------|
| **Kako radi** | Operater ručno unosi <100 proizvoda u MedusaJS Admin panel (jednokratno, ~1-2 dana posla). Zalihe ažurira ručno ili putem jednostavnog CSV importa. Narudžbine prepisuje u Abacus. |
| **Prednosti** | **Nula integracionog razvoja.** Nema zavisnosti od Abacus API-ja. Može se početi odmah. Rizik: minimalan. |
| **Mane** | Ručni rad za ažuriranje cijena/zaliha. Greške u prepisivanju. Ne skalira se ako asortiman poraste. |
| **Procjena** | ✅ **Realan MVP pristup za <100 artikala** — najbrži put do go-live |
| **Frekvencija** | Proizvodi: po potrebi (novi proizvod = ručni unos); Zalihe: 1-2x dnevno ručno; Narudžbine: po prijemu |

> **Sa <100 artikala, ovo nije "hack" — ovo je pragmatično rješenje.**
> Mnogi uspješni e-commerce biznisi sa malim katalogom rade upravo ovako.

### Preporučeni pristup — REVIDIRAN za mali katalog (<100 artikala)

> Originalna preporuka (hibridni C+D) je bila pisana pod pretpostavkom velikog kataloga.
> Sa <100 artikala, situacija se značajno pojednostavljuje.

**Faza 1 (MVP — najbrži go-live):**
- Proizvodi: **ručni unos u MedusaJS Admin** (Opcija E) — <100 artikala = 1-2 dana posla
- Zalihe: ručno ažuriranje ili jednostavan CSV import
- Narudžbine: notifikacija operateru koji unosi u Abacus
- Fiskalizacija: Abacus POS (scenario F1 ili F4)
- **Rezultat:** Online prodavnica živa bez ijedne linije integracionog koda

**Faza 2 (automatizacija — kad se dokaže model):**
- File-based ili DB sync za zalihe (Opcija C) — da ne ažuriraju ručno
- Automatsko prosljeđivanje narudžbina ka Abacus-u (Opcija C ili D)
- **Rezultat:** Smanjuje ručni rad, manje grešaka

**Faza 3 (full integracija — ako asortiman raste):**
- API integracija ako/kada Bencom obezbijedi API (Opcija A)
- Ili middleware (Opcija D) za potpunu automatizaciju
- **Rezultat:** Potrebno tek ako katalog preraste 100+ artikala

> **Ključna promjena u razmišljanju:** Sa malim katalogom, pitanje "kako automatizovati sync proizvoda" postaje manje hitno. Fokus se pomjera na **fiskalizaciju** i **tok narudžbina** kao primarne izazove.

---

## 5. Plan rada — Faze implementacije

### Faza 0: Discovery & Validacija (1-2 sedmice)

- [ ] Inicijalni sastanak — odgovoriti na kritična pitanja (sekcija 3)
- [ ] Kontaktirati Bencom — utvrditi mogućnosti integracije
- [ ] Dobiti pristup Abacus sistemu (demo ili produkcija)
- [ ] Mapirati strukturu podataka u Abacus-u (proizvodi, zalihe, cijene, kupci)
- [ ] Utvrditi fiskalizacioni tok za online prodaju
- [ ] Pregledati postojeći MedusaJS kod detaljnije sa development timom
- [ ] Definisati MVP scope

### Faza 1: Infrastruktura & Konfiguracija (2-3 sedmice)

- [ ] Setup hosting za MedusaJS (production environment)
- [ ] Konfigurisati PostgreSQL production bazu
- [ ] Aktivirati Redis (cache, event bus, workflow engine — već konfigurisano u kodu)
- [ ] Konfigurisati regione: Crna Gora, EUR valuta, PDV stope
- [ ] Setup stock lokacija (magacin Podgorica, magacin [grad 2], eventualno centralni)
- [ ] Konfigurisati payment providere (Stripe/kartica + COD)
- [ ] Setup email notifikacija (aktivirati Mailtrap ili zamijeniti providerom)
- [ ] Konfigurisati domenu i SSL

### Faza 2: Proizvodi & ERP Integracija (1-3 sedmice — REVIDIRANO za mali katalog)

> Sa <100 artikala, ova faza je značajno manja nego kod velikog kataloga.

- [ ] **Proizvodi — ručni unos u MedusaJS Admin** (~1-2 dana za <100 artikala)
  - Unos naziva, opisa, cijena, kategorija
  - Upload slika proizvoda
  - Konfiguracija varijanti (veličina, boja, itd. — ako postoje)
  - Konfiguracija zaliha po stock lokaciji
- [ ] Definisati proces za održavanje kataloga (ko ažurira cijene, ko dodaje nove proizvode)
- [ ] Implementirati tok narudžbina: MedusaJS → operater → Abacus
  - Notifikacija operateru (email / admin dashboard)
  - Operater ručno unosi narudžbinu u Abacus (za MVP)
  - Status tracking u MedusaJS
- [ ] Implementirati fiskalizaciju online računa (scope zavisi od scenarija — vidi 2.2)
  - **F1 (cilj):** Integracija Medusa → Abacus POS za programsko kreiranje fiskalnog računa (+1-2 sed)
  - **F4 (MVP fallback):** Operater fiskalizuje u Abacus POS ručno (+0.5-1 sed)
  - **F3 (izbjegavati):** Custom fiskalizacioni engine u MedusaJS (+5-8 sed)
- [ ] (Opciono) Jednostavan CSV import za periodično ažuriranje zaliha iz Abacus-a

### Faza 3: Frontend & UX (2-3 sedmice)

- [ ] Review i prilagodba storefront-a
- [ ] Implementacija prikaza raspoloživosti po lokaciji
- [ ] Checkout flow sa podrškom za odabrane načine plaćanja
- [ ] Email template-i (potvrda narudžbine, statusne promjene)
- [ ] Mobile responsiveness
- [ ] i18n (SR-Cyrl + EN ako je potrebno)

### Faza 4: Testiranje & Go-Live (2-3 sedmice)

- [ ] End-to-end testiranje (narudžbina → ERP → fiskalizacija)
- [ ] Load testing
- [ ] UAT (User Acceptance Testing) sa klijentom
- [ ] Soft launch (ograničen asortiman)
- [ ] Monitoring setup
- [ ] Go-live

### Faza 5: Post-Launch & Proširenja

- [ ] Automatizacija sync-a proizvoda/zaliha (Opcija C ili D) — **kad ručni unos postane teret**
- [ ] Automatsko prosljeđivanje narudžbina ka Abacus-u
- [ ] Click & Collect implementacija
- [ ] B2B portal (koristi postojeći Legal Entity modul)
- [ ] Napredne analitike
- [ ] Loyalty program

---

## 6. Tehnički pregled MedusaJS aplikacije

### 6.1. Struktura projekta

```
medusa_sistemi/sistemi_medusa/
├── src/
│   ├── modules/
│   │   ├── documents/        ← 7 entiteta, PDF generisanje, B2B/B2C
│   │   ├── legal/            ← Pravna lica, tipovi kupaca
│   │   ├── wishlist/         ← Lista želja, dijeljenje
│   │   └── product-custom-attribute/  ← Custom atributi po varijanti
│   ├── api/
│   │   ├── admin/            ← Admin API rute
│   │   └── store/            ← Store API rute (kupci, pretraga, wishlist)
│   ├── subscribers/          ← Event handlers (order, product, category)
│   ├── workflows/            ← Business logic orchestracija
│   ├── links/                ← 23 cross-module veze
│   ├── providers/            ← Mailtrap (email)
│   ├── lib/
│   │   ├── typesense.ts      ← Search engine konfiguracija
│   │   └── utils/pdf/        ← PDF generisanje faktura
│   └── jobs/                 ← Scheduled jobs (za budući ERP sync)
├── medusa-config.ts          ← Glavna konfiguracija
└── .yalc/
    └── migrate-from-magento/ ← Magento migracija (dev)
```

### 6.2. MedusaJS v2 — Mogućnosti za ERP integraciju

MedusaJS v2 ima odličnu arhitekturu za integracije:

- **Custom moduli** — izolovani, sa sopstvenim servisima, modelima i migracijama
- **Workflows** — orkestracioni engine sa kompenzacionim funkcijama (rollback)
- **Subscribers** — event-driven reakcija na order.placed, product.created, itd.
- **Scheduled jobs** — cron-based za periodičnu sinhronizaciju
- **Custom API routes** — za webhook endpoint-e (prijem podataka od ERP-a)
- **Multi-warehouse** — Stock Location modul, Inventory modul sa nivoom po lokaciji
- **Multi-region** — regioni sa različitim valutama, porezima, fulfillment opcijama

### 6.3. Već implementirano vs. potrebno

| Funkcionalnost | Status | Napomena |
|----------------|--------|----------|
| Katalog proizvoda | ✅ Osnova | Treba sync sa ERP-om |
| Pretraga (Typesense) | ✅ Implementirano | Region-aware, faceted — za <100 artikala možda overkill, ali ne smeta |
| Wishlist | ✅ Implementirano | Sa sharing funkcijom |
| Dokumenti/Fakture | ✅ Implementirano | PDF generisanje, B2B/B2C |
| Legal Entity (B2B) | ✅ Implementirano | Pravna lica, tipovi kupaca |
| Custom atributi | ✅ Implementirano | Po varijanti |
| ERP sync modul | ❌ Nije implementirano | Sa <100 artikala: ručni unos za MVP, automatizacija u fazi 2 |
| Fiskalizacija CG | ❌ Nije implementirano | **Kritično — scope zavisi od scenarija (vidi 2.2): F1=1-2 sed, F3=5-8 sed** |
| Payment provider | ⚠️ Konfigurisano, nije aktivirano | Stripe/PayPal/COD |
| Email notifikacije | ⚠️ Konfigurisano, isključeno | Mailtrap |
| Redis (production) | ⚠️ Konfigurisano, isključeno | Cache, events, workflows |
| Multi-warehouse | ⚠️ MedusaJS podržava | Treba konfigurisati za CG lokacije |

---

## 7. Rizici i mitigacija

| Rizik | Vjerovatnoća | Uticaj | Mitigacija |
|-------|-------------|--------|------------|
| Fiskalizacija online prodaje nije riješena | Visoka | **Kritičan** | Razjasniti na prvom sastanku (sekcija 2.2 + pitanja 17-25). Ako Abacus ne može → scope raste za 5-8 sedmica. Pripremiti F4 (polu-automatski) kao MVP fallback |
| Abacus nema API niti mogućnost programskog pristupa | Visoka | ~~Kritičan~~ **Srednji** (revidiran) | Sa <100 artikala, ručni unos proizvoda je izvodljiv MVP. API je bitan tek za automatizaciju zaliha i narudžbina — ali ne blokira go-live. |
| Kašnjenje sinhronizacije zaliha | Srednja | Srednji (revidiran) | Sa <100 artikala, ručno ažuriranje zaliha 1-2x dnevno je izvodljivo. Dodati disclaimer "dostupnost podložna promjeni" na sajt. |
| Nepoznat frontend stack | Srednja | Srednji | Pregledati sa development timom na sastanku |
| Hosting i infrastruktura nije definisana | Srednja | Srednji | Definisati u Fazi 0, uključiti u budžet |
| Oversized infrastruktura za mali katalog | Srednja | Nizak | Typesense, Redis, scheduled jobs — sve ovo je implementirano ali za <100 artikala može biti overkill. Razmotriti da li je sve neophodno za MVP ili se može pojednostaviti. |
| Ručni unos ne skalira ako asortiman poraste | Niska (za sada) | Srednji | Pratiti rast kataloga. Ako pređe 200+ artikala, planirati automatizovani sync (Opcija C ili D). |

---

## 8. Preporuke za sutrašnji sastanak

### Prioritet razgovora:

1. **Prvo 15 min — FISKALIZACIJA (#22-#30):** Kako trenutno radi fiskalizacija? Da li Abacus može fiskalizovati i online narudžbine? Ovo je pitanje koje **najviše utiče na obim posla** (razlika od 1 do 8 sedmica). Prezentovati scenarije F1-F4 i zajedno odabrati pristup.
2. **Sledećih 10 min — ZALIHE I REZERVACIJA (#6-#10):** Da li Abacus podržava provjeru stanja i rezervaciju? Ovo određuje da li možemo garantovati kupcu raspoloživost. Prezentovati scenarije Z1-Z4.
3. **Sledećih 10 min — ERP integracija (#1-#5):** API, pristup bazi, file export — šta je tehnički moguće? Kontakt u Bencom-u.
4. **Sledećih 10 min — Infrastruktura (#11-#15):** Magacini, hosting, lokacije.
5. **Sledećih 10 min — Poslovni zahtjevi (#16-#21):** Asortiman, plaćanja, isporuka.
6. **Poslednjih 5 min — Naredni koraci:** Dogovor ko šta radi do sledećeg sastanka.

### Ishod koji želimo sa sastanka:

- [ ] **NAJBITNIJE:** Razjašnjen fiskalizacioni tok za online prodaju — koji scenario (F1/F2/F3/F4)?
- [ ] Razjašnjeno upravljanje zalihama — da li Abacus podržava provjeru/rezervaciju (Z1/Z2/Z3/Z4)?
- [ ] Potvrda da li je Bencom kontaktiran i da li je kooperativan
- [ ] Potvrda mogućnosti integracije sa Abacus ERP-om (API/DB/file)
- [ ] Jasna slika o broju magacina i lokacija
- [ ] Definisan MVP scope i prioritet funkcionalnosti
- [ ] Dogovor o narednim koracima i vremenskom okviru
- [ ] Dogovor: ko kontaktira Bencom ako još nije kontaktiran

---

## Appendix A: Korisni linkovi

| Resurs | URL |
|--------|-----|
| MedusaJS dokumentacija | https://docs.medusajs.com |
| MedusaJS ERP integracija recipe | https://docs.medusajs.com/resources/recipes/erp |
| MedusaJS Odoo integracija (referenca) | https://docs.medusajs.com/resources/recipes/erp/odoo |
| Abacus ERP (Bencom) | https://www.abacuserp.me/abacus-erp/ |
| POS4.me | https://pos4.me/ |
| Bencom | https://www.bencomltd.com/ |
| CG Poreska uprava — e-fiskalizacija | https://epfi.tax.gov.me/ |
| CG fiskalni zahtjevi | https://www.fiscal-requirements.com/countries/14 |

## Appendix B: Abacus ERP — Kontakti

| Kontakt | Info |
|---------|------|
| **Bencom d.o.o.** (developer) | it@bencomltd.com, +381 31/332-302, Herceg Novi |
| **POS4.me** (distributer, Podgorica) | info@pos4.me, +382 20 221 750, City Kvart bb |
| **Bencom kancelarije CG** | Herceg Novi (HQ), Tivat, Kotor, Budva, Podgorica |
