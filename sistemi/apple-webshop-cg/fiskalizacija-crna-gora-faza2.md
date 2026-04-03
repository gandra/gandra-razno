# Fiskalizacija u Crnoj Gori — Detaljna analiza (Faza 2)

> **Status:** Odloženo za Fazu 2 (odluka sa sastanka 03.04.2026.)
> **Kontekst:** Glavni dokument projekta: `analiza-projekta-e-prodavnica-crna-gora.md`
> **Klijent:** iCentar d.o.o. — Apple Premium Reseller, Crna Gora

---

## 1. Pravni okvir

### Zakon i regulativa

- **Zakon o fiskalizaciji u prometu proizvoda i usluga** (Sl. list CG 46/2019, 73/2019, 8/2021)
- Obavezna od **01.01.2021**, potpuna primjena od **01.06.2021.**
- **Online prodavnica MORA fiskalizovati** sve račune — i gotovinske i bezgotovinske

### Ključni pojmovi

| Pojam | Objašnjenje |
|-------|-------------|
| **ENU** | Elektronski Naplatni Uređaj — uređaj (ili softver!) sa fiskalnim softverom |
| **IKOF (IIC)** | Identifikacioni Kod Obveznika Fiskalizacije — 32-karakterni kod, generiše ga PRODAVAC |
| **JIKR (FIC)** | Jedinstveni Identifikacioni Kod Računa — UUID, generiše ga PORESKA UPRAVA |
| **SEP** | Self-Care EFI Portal — portal za registraciju ENU, operatera, poslovnih prostora |
| **EFI** | Elektronska Fiskalna Infrastruktura |

### PDV stope (od 01.2025.)

| Stopa | Primjena |
|-------|----------|
| **21%** | Standardna (elektronika, Apple proizvodi) |
| **15%** | Knjige, smještaj, hrana (bez alkohola) |
| **7%** | Osnovna hrana, lijekovi, udžbenici |
| **0%** | Izvoz |

### Kazne za nepoštovanje

| Subjekat | Kazna |
|----------|-------|
| Pravna lica | **8.000 — 40.000 EUR** |
| Preduzetnici | 2.000 — 12.000 EUR |
| Odgovorna lica | 1.300 — 4.000 EUR |

> U 2025. izdato **271.900 EUR** kazni — aktivno se provodi.

### Rokovi za fiskalizaciju

| Tip plaćanja | Rok za slanje | Format računa |
|-------------|---------------|---------------|
| **Gotovinski** | 2 sekunde | Mora se **odštampati** |
| **Bezgotovinski** (kartica, virman) | **48 sati** | Može biti **elektronski** (sa saglasnošću kupca) |

> **Za online prodavnicu:** Plaćanje karticom = bezgotovinski = 48h rok = e-račun. Ovo je KLJUČNA prednost — ne blokiramo checkout.

### Korektivni računi (storno/povrat)

- Izdaje se novi fiskalni račun sa **negativnim iznosima**
- Mora referencirati **IKOF originalnog računa**
- Korektivni račun se takođe fiskalizuje (šalje Poreskoj upravi)

### Softverska kasa

CG zakon eksplicitno dozvoljava **softversku kasu** — web aplikacija MOŽE biti ENU. Nema zahtjeva za specijalizovanim hardverom. Za bezgotovinske transakcije nije potreban ni štampač.

---

## 2. Tehnička specifikacija

### Komunikacija sa Poreskom upravom

| Atribut | Vrijednost |
|---------|-----------|
| **Protokol** | SOAP 1.1 preko HTTPS |
| **Format** | XML |
| **Namespace** | `https://efi.tax.gov.me/fs/schema` |
| **Test endpoint** | `https://efitest.tax.gov.me:443/fs-v1` |
| **Produkcija endpoint** | `https://efi.tax.gov.me:443/fs-v1` |
| **Test SEP portal** | `https://efitest.tax.gov.me/self-care` |
| **Prod SEP portal** | `https://sep.tax.gov.me/self-care` |
| **Verifikacija računa** | `https://efi.tax.gov.me/ic/#/verify?iic=...&tin=...` |

### Tri SOAP operacije

| Operacija | Opis | Kada |
|-----------|------|-----|
| **RegisterTCR** | Registracija ENU (terminal/kasa) | Jednom, pri prvom pokretanju |
| **RegisterCashDeposit** | Registracija dnevnog depozita | Svaki dan prije prvog računa |
| **RegisterInvoice** | Fiskalizacija računa | Za svaki račun |

### IKOF (IIC) generisanje — algoritam

```
1. Spoji polja: PIB|DatumVrijeme|RedniBroj|PoslovniProstor|ENU|Softver|UkupnaCijena
   Primjer: "12345678|2026-04-03T10:30:00+02:00|1|BU001|CR001|SW001|599.00"

2. Potpiši RSA-SHA256 koristeći privatni ključ iz PKCS#12 certifikata
   → iicSignature (hex string)

3. MD5 hash potpisa
   → IIC/IKOF (32-karakterni hex string)
```

### Digitalno potpisivanje XML poruke

- **Algoritam:** RSA-SHA256
- **Canonicalization:** Exclusive C14N (`xml-exc-c14n#`)
- **Digest:** SHA-256
- **Transforms:** Enveloped Signature + Exclusive C14N
- **Reference URI:** `#Request`
- **Certifikat:** PKCS#12 (.pfx) — izdavači: Pošta CG, CoreIT, Crnogorski Telekom (~30 EUR, validnost 3-5 godina)

### RegisterInvoiceRequest — XML struktura

```xml
<RegisterInvoiceRequest Id="Request" Version="...">
  <Header UUID="..." SendDateTime="..." />
  <Invoice TypeOfInv="NONCASH" IssueDateTime="..."
           InvNum="..." InvOrdNum="..." TCRCode="..." OperatorCode="..."
           BusinUnitCode="..." SoftCode="..."
           IIC="..." IICSignature="..."
           IsIssuerInVAT="true" TotPriceWoVAT="..." TotVATAmt="..." TotPrice="...">
    <PayMethods>
      <PayMethod Type="ACCOUNT" Amt="..." />
    </PayMethods>
    <Seller IDType="TIN" IDNum="..." Name="..." />
    <Items>
      <I N="name" C="code" U="unit" Q="qty" UPB="unitPriceBefore"
         UPA="unitPriceAfter" VR="21.00" VA="vatAmt" PA="priceAfter" />
    </Items>
    <SameTaxes>
      <SameTax NumOfItems="..." PriceBefVAT="..." VATRate="21.00" VATAmt="..." />
    </SameTaxes>
  </Invoice>
</RegisterInvoiceRequest>
```

---

## 3. Opcije za implementaciju

### Opcija F-A: MedusaJS sam fiskalizuje (PREPORUČENO)

```
Kupac → MedusaJS → [Fiskalni modul] → Poreska uprava CG (SOAP/XML)
                                     ← JIKR + QR
```

| Aspekt | Detalji |
|--------|---------|
| **Kako radi** | MedusaJS custom fiskalni modul generiše IKOF, potpisuje XML, šalje SOAP poruku Poreskoj upravi, prima JIKR. |
| **Zašto DA** | Potpuna nezavisnost od Abacus-a. CG zakon dozvoljava softversku kasu. Bezgotovinski 48h rok. Open-source referentne implementacije u Node.js. |
| **Zašto NE** | Treba razviti fiskalni modul (~2-3 sedmice). Treba nabaviti certifikat. Treba registrovati ENU. |
| **Scope** | **~2-3 sedmice** |

> **Napomena:** Abacus `postSale` API kreira porudžbinu ali NE fiskalizuje — zato je ovo preporučen pristup.

### Opcija F-B: Delegiranje na Abacus POS

| Aspekt | Detalji |
|--------|---------|
| **Preduslov** | Bencom mora potvrditi da Abacus POS može primiti online narudžbinu I fiskalizovati je |
| **Procjena** | Dokumentovani API to NE podržava. Treba kontaktirati Bencom. |

### Opcija F-C: Cloud fiskalni SaaS

| SaaS | URL | Opis |
|------|-----|------|
| **DDD Invoices** | dddinvoices.com | API-first, podržava CG, JSON ulaz → oni rade SOAP/XML |
| **eFiskal.me** | efiskal.me | 7000+ klijenata u CG, Odoo-based, REST API |
| **VG eFISKAL** | fiskalizacija.me | Cloud POS + API |

| Aspekt | Detalji |
|--------|---------|
| **Scope** | **~1 sedmica** (samo API integracija) |
| **Mane** | Mjesečni trošak (20-100 EUR). Zavisnost od treće strane. |

### Preporučeni redosljed

| Prioritet | Opcija | Razlog |
|-----------|--------|--------|
| **1.** | **F-A: MedusaJS fiskalizuje** | Potpuna kontrola, open-source referenca, bez mjesečnih troškova |
| **2.** | F-C: Cloud SaaS | Ako je prioritet brzina nad kontrolom |
| **3.** | F-B: Abacus POS | Samo ako Bencom potvrdi interni mehanizam |

---

## 4. Tehnička arhitektura — MedusaJS fiskalni modul

```
src/modules/fiscal/
├── models/
│   ├── fiscal-receipt.ts         # IKOF, JIKR, QR, status, order_id, timestamps
│   └── fiscal-config.ts          # PIB, ENU kod, softver kod, cert path
├── service.ts                     # FiscalService
│   ├── generateIIC(invoice)       # RSA-SHA256 + MD5
│   ├── buildXml(invoice)          # XML per CG schema
│   ├── signXml(xml, cert)         # PKCS#12 digitalno potpisivanje
│   ├── registerInvoice(xml)       # SOAP poziv ka efi.tax.gov.me
│   ├── registerTCR(config)        # Registracija ENU (jednom)
│   ├── registerCashDeposit()      # Dnevni depozit
│   └── generateQR(iic, tin, ...)  # QR kod za verifikaciju
├── lib/
│   ├── soap-client.ts             # HTTPS + SOAP envelope
│   ├── xml-signer.ts              # xml-crypto + PKCS#12
│   └── iic-generator.ts           # Pipe-delimited → RSA-SHA256 → MD5
└── index.ts

src/workflows/fiscal/
├── fiscalize-order.ts             # Glavni workflow sa kompenzacijom
└── retry-failed-fiscalization.ts  # Za neuspjele pokušaje

src/subscribers/
└── fiscal-on-order-placed.ts      # order.placed → fiscalize-order workflow

src/jobs/
├── retry-fiscalization-job.ts     # Cron: svakih 5 min — retry neuspjelih
└── daily-cash-deposit-job.ts      # Cron: 00:01 — RegisterCashDeposit
```

**Node.js dependencije:**
- `xml-crypto` — XML digitalno potpisivanje
- `xmlbuilder2` — XML konstrukcija
- `axios` — HTTPS/SOAP komunikacija
- `node-rsa` ili `crypto` (native) — RSA operacije
- `md5` — MD5 hash za IIC
- `qrcode` — QR kod generisanje
- `pem` — PKCS#12 ekstrakcija

---

## 5. Pitanja za Fazu 2

| # | Pitanje | Zašto je bitno |
|---|---------|----------------|
| 1 | Kako TRENUTNO fiskalizujete u fizičkim prodavnicama? Preko Abacus POS-a? | Da razumijemo postojeći tok |
| 2 | Da li imate digitalni certifikat (soft certifikat / napredni elektronski pečat)? Ko ga je izdao? | Može li se isti koristiti i za online? |
| 3 | Da li ste registrovali poslovni prostor za online prodaju na SEP portalu? | Zakonski preduslov |
| 4 | Da li prihvatate da MedusaJS bude registrovan kao zaseban ENU (softverska kasa)? | Naša preporuka — nezavisnost online kanala |
| 5 | Da li postoji interni mehanizam u Abacusu za fiskalizaciju online narudžbina? (Pitanje za Bencom) | Backup opcija F-B |
| 6 | Kakva je politika povrata za online kupovinu? | Korektivni fiskalni račun (storno) |

---

## 6. Open-source referentne implementacije

### Crna Gora (direktna primjena)

| Repo | Jezik | Operacije | GitHub |
|------|-------|-----------|--------|
| **ElektronskaFiskalizacijaNodeJS** | JS/Node | RegisterInvoice | github.com/djordjen/ElektronskaFiskalizacijaNodeJS |
| **ElektronskaFiskalizacijaPython** | Python (Jupyter) | RegisterInvoice + QR | github.com/djordjen/ElektronskaFiskalizacijaPython |
| **Fiscal.MNE** | C# (.NET) | **RegisterTCR + CashDeposit + Invoice** | github.com/andrija-mitrovic/Fiscal.MNE |
| **OpenMicroFiscal** | C# (.NET) | RegisterInvoice (production-ready) | github.com/dalrankov/OpenMicroFiscal |
| **fiskalapi** | Python | eFiskal.me REST wrapper | github.com/digitalsolutionsmontenegro/fiskalapi |
| PHP SOAP Gist | PHP | RegisterTCR signing | gist.github.com/odan/9ae2d36d5970cde6f5acc661b8b725f7 |

### Hrvatska (sličan protokol — korisno kao referenca)

| Repo | Jezik | Stars | GitHub |
|------|-------|-------|--------|
| **nticaric/fiskalizacija** | PHP | 56 | github.com/nticaric/fiskalizacija |
| **tgrospic/Cis.Fiscalization** | C# | 22 | github.com/tgrospic/Cis.Fiscalization |
| **senko/fiskal-hr** | Python | 15 | github.com/senko/fiskal-hr |
| **shunkica/fiskalizacija2-js** | TypeScript | 11 | github.com/shunkica/fiskalizacija2-js |
| **aradovanJava/Fiskalizacija** | Java | 4 | github.com/aradovanJava/Fiskalizacija |
| **l-d-t/fiskalhrgo** | Go | 1 | github.com/l-d-t/fiskalhrgo |

### Ostali Balkan

| Repo | Zemlja | Jezik | GitHub |
|------|--------|-------|--------|
| **MPrtenjak/SLOTax** | Slovenija | C# | github.com/MPrtenjak/SLOTax |
| **theOriginalFelto/MEAN-full-stack-eFiskalizacija** | Srbija | TypeScript | github.com/theOriginalFelto/MEAN-full-stack-eFiskalizacija |
| **MewsSystems/fiscalizations** | AT/DE/HU/IT/ES | C# (61★) | github.com/MewsSystems/fiscalizations |

---

## 7. Cloud fiskalni SaaS provajderi

| Provajder | URL | Tip | Napomena |
|-----------|-----|-----|----------|
| **DDD Invoices** | dddinvoices.com | API-first SaaS | Podržava CG, JSON API, 10-godišnje čuvanje |
| **eFiskal.me** | efiskal.me | Odoo-based | 7000+ klijenata u CG, demo dostupan |
| **VG eFISKAL** | fiskalizacija.me | Cloud POS + API | Demo: demo.efiskal.me |
| **TiramisuERP** | tiramisuerp.com | ERP + fiskalizacija | Pokriva CG, SRB, BiH |
| **e-Invoices Online** | e-invoices.online | Cloud | Pomoć pri nabavci certifikata |

---

## 8. Izvori informacija

### Pravna regulativa
- Zakon o fiskalizaciji u prometu proizvoda i usluga, Sl. list CG 46/2019, 73/2019, 8/2021
- Fiskalni servis — Funkcionalna specifikacija v5 (Poreska uprava CG)
- Fiskalni servis — Tehnička specifikacija v5 (Poreska uprava CG)

### Tehnički izvori
- TiramisuERP: Electronic Fiscalization in Montenegro — tiramisuerp.com/en/electronic-fiscalization-in-montenegro
- DDD Invoices: Fiscalization and Real-Time Reporting in Montenegro — dddinvoices.com/learn/fiscalization-and-real-time-reporting-in-montenegro
- Fiscal Solutions: Montenegro — fiscal-requirements.com/countries/14
- Fiscal Solutions: IKOF Code — fiscal-requirements.com/news/5217
- Fiscal Solutions: Corrective Receipts — fiscal-requirements.com/news/2735
- Fiscal Solutions: Certificates Required — fiscal-requirements.com/news/3179
- Fiscal Solutions: E-Receipts Conditions — fiscal-requirements.com/news/2432
- Agencija Luna: New Law on Fiscalization — agencijaluna.me/en/new-law-on-fiscalization-in-montenegro/

### Portali Poreske uprave CG
- Elektronska fiskalizacija — gov.me/poreskauprava/elektronska-fiskalizacija
- Test SEP Portal — efitest.tax.gov.me/self-care
- Production SEP Portal — sep.tax.gov.me/self-care
- Verifikacija računa — efi.tax.gov.me/ic/#/verify

### Kontakti za certifikate
- Pošta CG — posta.me
- CoreIT — coreit.me
- Crnogorski Telekom — telekom.me (~30 EUR, validnost 3-5 godina)
