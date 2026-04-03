# Platforma za građanski aktivizam — „Cigla po cigla"

> *Zamislite milion ljudi dobre volje. Svako od njih je jedna cigla. Neko može da priloži 30 evra mesečno, neko da tabana, neko da ponudi 3 sata programiranja nedeljno, neko 2 sata advokatskih usluga. Trenutno imamo milion cigli — ali nemamo kuću. Nemamo platformu da to kapitalizujemo. Ovaj dokument menja to.*

---

## Sadržaj

1. [Vizija i filozofija](#1-vizija-i-filozofija)
2. [Ključni koncepti](#2-ključni-koncepti)
3. [Tipovi korisnika — pojedinci i organizacije](#3-tipovi-korisnika--pojedinci-i-organizacije)
4. [Životni ciklus, rokovi i reaktivacija](#4-životni-ciklus-rokovi-i-reaktivacija)
5. [Vidljivost i domet inicijative](#5-vidljivost-i-domet-inicijative)
6. [Timovi, radne grupe, kolaboracija i koordinacija](#6-timovi-radne-grupe-kolaboracija-i-koordinacija)
7. [QR kod sistem](#7-qr-kod-sistem)
8. [Sistem preduslova i pledževa](#8-sistem-preduslova-i-pledževa)
9. [Plaćeni aktivizam — model kompenzacije](#9-plaćeni-aktivizam--model-kompenzacije)
10. [Tender model i šabloni inicijativa](#10-tender-model-i-šabloni-inicijativa)
11. [Kalendar — planiranje, koordinacija i vidljivost](#11-kalendar--planiranje-koordinacija-i-vidljivost)
12. [Lokacija, online opcije i način izvršenja](#12-lokacija-online-opcije-i-način-izvršenja)
13. [Oglasi i otvorene pozicije](#13-oglasi-i-otvorene-pozicije)
14. [Volonterski profili, dostupnost i matching](#14-volonterski-profili-dostupnost-i-matching)
15. [Članarine, donacije i sponzorstva](#15-članarine-donacije-i-sponzorstva)
16. [Fundraising — prikupljanje sredstava](#16-fundraising--prikupljanje-sredstava)
17. [Galerija — vizuelna dokumentacija](#17-galerija--vizuelna-dokumentacija)
18. [Sistem interakcija](#18-sistem-interakcija)
19. [Bounty koncept](#19-bounty-koncept)
20. [Rating sistem — sveobuhvatno ocenjivanje](#20-rating-sistem--sveobuhvatno-ocenjivanje)
21. [Monitoring i evaluacija dugotrajnih inicijativa](#21-monitoring-i-evaluacija-dugotrajnih-inicijativa)
22. [Finansijska transparentnost](#22-finansijska-transparentnost)
23. [Graf baza — veze, preporuke, mreža aktivista](#23-graf-baza--veze-preporuke-mreža-aktivista)
24. [Mikro-sajt inicijative i custom domeni](#24-mikro-sajt-inicijative-i-custom-domeni)
25. [Početna strana — UX arhitektura](#25-početna-strana--ux-arhitektura)
26. [Liquid Democracy — delegiranje glasa](#26-liquid-democracy--delegiranje-glasa)
27. [Profili korisnika i reputacija](#27-profili-korisnika-i-reputacija)
28. [Notifikacije i komunikacija](#28-notifikacije-i-komunikacija)
29. [Primer: „Topli kutak" kao prva inicijativa](#29-primer-topli-kutak-kao-prva-inicijativa)
30. [Tehnička arhitektura — pregled](#30-tehnička-arhitektura--pregled)
31. [Bezbednost, moderacija i zloupotrebe](#31-bezbednost-moderacija-i-zloupotrebe)
32. [Faze razvoja](#32-faze-razvoja)

---

## 1. Vizija i filozofija

### 1.1. Problem

U svakoj zajednici postoje ljudi koji žele da pomognu — ali ne znaju kako, kome, niti gde. Istovremeno, postoje inicijative koje propadaju jer ne mogu da privuku dovoljno resursa: novca, volontera, stručnih usluga. **Fali infrastruktura koja povezuje dobre namere sa konkretnim akcijama.**

Ali problem je i dublji: mnogi stručnjaci **žele** da pomognu, ali ne mogu da rade potpuno besplatno. **Aktivizam ne sme da bude luksuz koji samo bogati mogu sebi priuštiti.**

### 1.2. Metafora cigle

```
┌─────────────────────────────────────────────────────────────────────┐
│   Svaki čovek dobre volje je CIGLA.                                │
│   Ali cigle nisu sve iste. I to je OK.                             │
│                                                                     │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│   │  30 EUR │ │ 20h pro-│ │ 50h pro-│ │ 2h advo-│ │ fizički │   │
│   │ donacija│ │gramiranj│ │gramiranj│ │ katskih │ │   rad   │   │
│   │ (bespl.)│ │(besplat)│ │(20€/sat)│ │ (bespl.)│ │ vikend  │   │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│        │            │           │            │          │          │
│   DVOSMERNI TOK: Aktivisti DAJU i PRIMAJU vrednost                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3. Osnovni principi

| Princip | Objašnjenje |
|---------|-------------|
| **Transparentnost** | Svaki dinar, svaki sat rada, svaka isplata — vidljivo svima |
| **Dostupnost** | Nema minimalnog doprinosa. I 1 EUR je cigla |
| **Dostojanstvo** | Svaki doprinos je jednako važan |
| **Decentralizacija** | Inicijative dolaze odozdo — od građana |
| **Odgovornost** | Ko obeća — preuzima obavezu |
| **Inkluzivnost** | Pristupačno za sve — jezički, tehnološki, fizički |
| **Fer kompenzacija** | Aktivisti mogu (ali ne moraju) biti plaćeni |
| **Dvosmerni tok** | Vrednost se daje I prima — novac, vreme, resursi, znanje |
| **Evaluacija** | Svaki doprinos se prati, ocenjuje, transparentno izveštava |
| **Smart matching** | Platforma inteligentno spaja ljude sa inicijativama |
| **Održivost** | Članarine i fundraising obezbeđuju dugoročno funkcionisanje |

---

## 2. Ključni koncepti

### 2.1. Rečnik pojmova

| Pojam | Definicija |
|-------|-----------|
| **Inicijativa** | Konkretna akcija sa ciljem, opisom, timom, budžetom, i opcionalno preduslovima |
| **Owner** | Vlasnik inicijative — odgovoran za realizaciju |
| **Tim** | Grupa ljudi sa dodeljenim ulogama. Samo tim vidi Draft inicijativu |
| **Radna grupa** | Specijalizovani pod-tim unutar inicijative za konkretan aspekt (logistika, dizajn, PR...) |
| **Preduslov** | Resurs koji mora biti obezbeđen pre pokretanja |
| **Pledž (Cigla)** | Obećanje doprinosa — besplatno ili uz kompenzaciju |
| **Tender** | Strukturirani poziv za ponude |
| **Oglas (Pozicija)** | Otvoreno radno mesto unutar inicijative |
| **Volonterski profil** | CV-sličan profil sa veštinama, dostupnošću, i preferencijama |
| **Kompenzacija** | Finansijska nadoknada — u tiered modelu |
| **Bounty** | Specifičan zadatak sa jasnim uslovima |
| **Rating** | Višedimenzionalna ocena aktivista, inicijative, saradnje |
| **Članarina** | Periodična uplata korisnika platformi za pristup premium funkcijama |
| **Donacija** | Jednokratna ili rekurentna uplata platformi ili inicijativi |
| **Fundraising kampanja** | Strukturirano prikupljanje sredstava za inicijativu sa ciljem, rokom, i strategijom |
| **Galerija** | Vizuelna dokumentacija inicijative — before/after, progress, event fotografije |
| **Graf baza** | Baza podataka za veze između korisnika i inicijativa |
| **QR invite** | QR kod za brz poziv u inicijativu |
| **Mikro-sajt** | Javna prezentaciona stranica inicijative |
| **Proxy kreiranje** | Kreiranje inicijative u ime druge osobe |
| **Escrow** | Namenski račun gde se čuva novac do ispunjenja uslova |

---

## 3. Tipovi korisnika — Pojedinci i organizacije

### 3.1. Koncept: Ko se registruje

Platforma nije samo za pojedince. Registrovati se mogu i organizacije, pokreti, političke partije, firme. Svaki tip entiteta ima **različit profil, mogućnosti, odgovornosti, i pravila**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TIPOVI KORISNIKA                                  │
│                                                                     │
│  ┌─── 👤 POJEDINAC (Individual) ────────────────────────────────┐  │
│  │                                                               │  │
│  │  Fizičko lice. Najčešći tip korisnika.                       │  │
│  │  Može kreirati inicijative, volontirati, davati/primati      │  │
│  │  kompenzaciju, glasati, delegirati glas.                     │  │
│  │                                                               │  │
│  │  Verifikacija: email (osnovno) + opciono telefon / lična k. │  │
│  │  Primer: Ana Marković, programer iz Zvezdare                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🏢 ORGANIZACIJA (Organization) ──────────────────────────┐  │
│  │                                                               │  │
│  │  Pravno lice — NVO, udruženje građana, fondacija, firma.    │  │
│  │  Ima admin korisnike (ljudi koji upravljaju profilom).       │  │
│  │  Može kreirati inicijative u ime organizacije, sponzorisati, │  │
│  │  otvarati tendere, zapošljavati aktiviste.                   │  │
│  │                                                               │  │
│  │  Verifikacija: email + APR broj / registracija + dokument    │  │
│  │  Primer: NVO „Dečji osmeh", Crveni krst Zvezdara           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── ✊ POKRET (Movement) ─────────────────────────────────────┐  │
│  │                                                               │  │
│  │  Neformalna grupa ljudi ujedinjena oko zajedničkog cilja.    │  │
│  │  NEMA pravni subjektivitet (nije registrovana u APR-u).      │  │
│  │  Ima osnivače i članove, ali bez formalne hijerarhije.      │  │
│  │  Može kreirati inicijative, prikupljati pledževe.           │  │
│  │                                                               │  │
│  │  Verifikacija: email + min 3 osnivača (pojedinaca)          │  │
│  │  Primer: „Čist vazduh Beograd", „Roditelji za inkluziju"   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🏛️ POLITIČKA PARTIJA / LISTA (Political Entity) ────────┐  │
│  │                                                               │  │
│  │  Registrovana politička organizacija.                        │  │
│  │  POSEBNA PRAVILA: obavezna transparentnost finansiranja,    │  │
│  │  geo-restrikcija za glasanje, oznaka „Politička",           │  │
│  │  zabrana anonimnih donacija > 10€.                           │  │
│  │                                                               │  │
│  │  Verifikacija: APR + RIK registracija + odgovorno lice      │  │
│  │  Primer: „Lista za Zvezdaru", „Zelena koalicija"           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🏫 INSTITUCIJA (Institution) ────────────────────────────┐  │
│  │                                                               │  │
│  │  Javna ustanova — škola, bolnica, MZ, biblioteka, dom        │  │
│  │  zdravlja, opština. Može kreirati inicijative kao partner    │  │
│  │  ili pokrovitelj. NE može prikupljati sredstva bez           │  │
│  │  posebnog odobrenja.                                         │  │
│  │                                                               │  │
│  │  Verifikacija: službeni email + ovlašćenje institucije       │  │
│  │  Primer: MZ Zvezdara, OŠ „Banović Strahinja"               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2. Komparativna tabela tipova

| Mogućnost | 👤 Pojedinac | 🏢 Organizacija | ✊ Pokret | 🏛️ Pol. partija | 🏫 Institucija |
|-----------|:------------:|:---------------:|:--------:|:---------------:|:-------------:|
| Kreiranje inicijative | ✅ | ✅ | ✅ | ✅ (sa oznakom) | ✅ (partner) |
| Volontiranje | ✅ | — | — | — | — |
| Plaćeni rad (primanje) | ✅ | — | — | — | — |
| Doniranje inicijativi | ✅ | ✅ | ✅ | ✅ (transparentno) | ⚠️ Odobrenje |
| Sponzorstvo | — | ✅ | — | ⚠️ Ograničeno | ✅ |
| Tender (kreiranje) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tender (ponuda) | ✅ | ✅ | — | — | — |
| Glasanje (Liquid Dem.) | ✅ | — | — | — | — |
| Delegiranje glasa | ✅ | — | — | — | — |
| Match funding | — | ✅ | — | — | ✅ |
| Prikupljanje donacija | ✅ | ✅ | ✅ | ✅ (strože) | ⚠️ Odobrenje |
| Višestruki admini | — | ✅ | ✅ (osnivači) | ✅ | ✅ |
| Organizacioni profil | — | ✅ | ✅ | ✅ | ✅ |
| Custom domen | Pro plan | Org plan | Org plan | Org plan | Org plan |
| KYC verifikacija | Opciono | Obavezno | Min 3 osnivača | Obavezno (APR+RIK) | Obavezno |

### 3.3. Pojedinac vs Organizacija — Vlasništvo inicijative

Inicijativu može kreirati i pojedinac i organizacija. Ključna razlika:

```
POJEDINAC kreira inicijativu:
┌─────────────────────────────────────┐
│  Inicijativa: Topli kutak           │
│  Owner: 👤 Đuka Nikolić             │
│  Odgovornost: LIČNA                 │
│  Profil: prikazan na profilu Đuke   │
│  Finansije: Đukin escrow            │
└─────────────────────────────────────┘

ORGANIZACIJA kreira inicijativu:
┌─────────────────────────────────────┐
│  Inicijativa: Topli kutak           │
│  Owner: 🏢 NVO „Dečji osmeh"       │
│  Admini: Ana M., Petar D.          │
│  Odgovornost: ORGANIZACIONA         │
│  Profil: prikazan na profilu NVO    │
│  Finansije: escrow organizacije     │
└─────────────────────────────────────┘

POKRET kreira inicijativu:
┌─────────────────────────────────────┐
│  Inicijativa: Čist vazduh BGD       │
│  Owner: ✊ „Čist vazduh Beograd"    │
│  Osnivači: Marko P., Ana S., J. K. │
│  Odgovornost: KOLEKTIVNA (osnivači) │
│  Profil: prikazan na profilu pokreta│
│  Finansije: zajednički escrow       │
└─────────────────────────────────────┘
```

### 3.4. Profil organizacije

```
┌─────────────────────────────────────────────────────────────────┐
│  🏢 NVO „Dečji osmeh"                                           │
│  Udruženje građana · Zvezdara, Beograd                          │
│  Registrovano: 2019. · APR: 12345678                            │
│  Verifikovano ✅                                                 │
│                                                                  │
│  📋 O organizaciji:                                              │
│  Udruženje koje se bavi zaštitom prava dece i porodica          │
│  u riziku. Fokus: inkluzija, pristupačnost, socijalna zaštita. │
│                                                                  │
│  ┌─── Inicijative ──────────────────────────────────────────┐   │
│  │  ✅ Topli kutak Zvezdara (completed) · Rating ★★★★★      │   │
│  │  🔄 Topli kutak Voždovac (active) · 62% milestone        │   │
│  │  📋 Senzorna soba (draft)                                 │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─── Statistika ───────────────────────────────────────────┐   │
│  │  Inicijativa kreirano: 5 │ Uspešnih: 3 │ Aktivnih: 1     │   │
│  │  Volontera angažovano: 47 │ Donacija: 8.400€             │   │
│  │  Sponzor: Firma ABC (match funding)                       │   │
│  │  Rating organizacije: ★★★★★ 4.9 (23 evaluacije)         │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─── Tim organizacije ─────────────────────────────────────┐   │
│  │  👤 Ana M. — Admin │ 👤 Petar D. — Admin                 │   │
│  │  👤 Jelena S. — Član │ 👤 Marko P. — Član                │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─── Transparentnost ──────────────────────────────────────┐   │
│  │  💰 Ukupno prikupljeno: 12.600€                          │   │
│  │  💰 Ukupno utrošeno: 9.200€                              │   │
│  │  📄 Godišnji izveštaj: [PDF 2025]                        │   │
│  │  📄 Statut: [PDF]                                         │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [🔔 Prati]  [💳 Doniraj organizaciji]  [📧 Kontakt]          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5. Profil pokreta

```
┌─────────────────────────────────────────────────────────────────┐
│  ✊ „Čist vazduh Beograd"                                       │
│  Neformalni pokret · Beograd                                    │
│  Osnovan: februar 2026. · Osnivača: 3 · Članova: 134          │
│                                                                  │
│  📋 O pokretu:                                                   │
│  Grupa građana koja se bori za čist vazduh u Beogradu.          │
│  Monitoring AQI, zahtevi prema gradskoj upravi, edukacija.      │
│                                                                  │
│  ┌─── Osnivači ─────────────────────────────────────────────┐   │
│  │  👤 Marko P. (⭐ 4.7) │ 👤 Ana S. (⭐ 4.5)              │   │
│  │  👤 Jovan K. (⭐ 4.8)                                     │   │
│  │  Kolektivna odgovornost za finansije i inicijative        │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ⚠️ Neformalan pokret — nema pravni subjektivitet.             │
│  Za donacije > 500€ potrebna verifikacija jednog od osnivača.  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.6. Politička partija — Posebna pravila

| Pravilo | Obrazloženje |
|---------|-------------|
| **Obavezna APR + RIK verifikacija** | Sprečava lažne političke entitete |
| **Sve donacije javne** | Zakon o finansiranju političkih aktivnosti |
| **Anonimne donacije do max 10€** | Minimizira netransparentno finansiranje |
| **Oznaka „Politička"** na svakoj inicijativi | Korisnik odmah zna kontekst |
| **Geo-restrikcija glasanja** | Samo državljani / stanovnici mogu glasati |
| **Zabrana plaćenog aktivizma** | Sprečava kupovinu podrške |
| **Pojačana moderacija** | AI + community za dezinformacije |
| **Periodični finansijski izveštaji** | Obavezni mesečni, javno dostupni |

### 3.7. Pristup za tipove korisnika — Poređenje

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Samo pojedinci** | Nema organizacionih profila — sve su fizička lica | Jednostavno | Ne pokriva realnost, NVO moraju koristiti lične naloge |
| **B. Pojedinac + Organizacija** | Dva tipa, organizacija kao krovni profil | Pokriva 80% | Ne razlikuje NVO od firme od pokreta |
| **C. Pet tipova (⭐ Preporuka)** | Pojedinac, Organizacija, Pokret, Pol. partija, Institucija | Pokriva sve realne scenarije | Složeniji onboarding |
| **D. Free-form** | Korisnik sam bira tagove (osoba, NVO, firma...) | Fleksibilno | Nekonzistentno, teško za pravila |

**Preporuka: Pristup C (Pet tipova)**

**Obrazloženje:**
1. **Organizacija** (NVO, udruženje, firma) — pravno lice sa APR registracijom, višestruki admini, sponzorski paketi
2. **Pokret** — neformalna grupa bez pravnog subjektiviteta — kritično jer većina građanskog aktivizma počinje kao neformalni pokret, pre nego što (ako ikad) dobije pravni oblik
3. **Politička partija** — zahteva strože pravila transparentnosti — MORA biti odvojena jer miša politiku i aktivizam bez jasnog razgraničenja je opasno
4. **Institucija** — javne ustanove ne bi trebalo da „prikupljaju sredstva" kao NVO, ali bi trebalo da budu partneri i pokrovitelji
5. Onboarding komplikacija se rešava tako što se na registraciji **default je Pojedinac** — ostali tipovi su u „Kreiraj organizacioni profil" koji se može otvoriti kasnije

### 3.8. Registracija — Flow

```
REGISTRACIJA
     │
     ▼
┌─────────────────────────────────────────┐
│  Registrujem se kao:                     │
│                                         │
│  ● 👤 Pojedinac (osoba)                │ ← default
│  ○ 🏢 Organizacija (NVO, firma)        │
│  ○ ✊ Pokret (neformalna grupa)         │
│  ○ 🏛️ Politička organizacija           │
│  ○ 🏫 Institucija (javna ustanova)      │
│                                         │
│  [Nastavi →]                             │
└─────────────────────────────────────────┘
     │
     ├── Pojedinac: ime, email, lokacija → gotovo (2 min)
     │
     ├── Organizacija: ime org, APR broj, email, admin korisnici
     │   → verifikacija dokument (1-3 dana)
     │
     ├── Pokret: ime pokreta, opis, min 3 osnivača (email-ovi)
     │   → osnivači potvrde emailom → pokret aktivan
     │
     ├── Pol. partija: ime, APR, RIK registracija, odgovorno lice
     │   → manualna verifikacija admin tima (3-7 dana)
     │
     └── Institucija: ime, tip, službeni email, ovlašćenje
         → manualna verifikacija (3-7 dana)
```

### 3.9. Pojedinac može biti član organizacije

Isti čovek može imati **lični profil** (👤) I biti admin/član jedne ili više organizacija (🏢/✊). Prebacivanje konteksta:

```
┌─────────────────────────────────────────────────────────────────┐
│  Prijavljeni ste kao:                                            │
│                                                                  │
│  ● 👤 Ana Marković (lični profil)                               │
│  ○ 🏢 NVO „Dečji osmeh" (admin)                                │
│  ○ ✊ „Čist vazduh Beograd" (osnivač)                           │
│                                                                  │
│  [Prebaci kontekst]                                              │
│                                                                  │
│  Kad kreirate inicijativu kao organizacija,                     │
│  ona pripada organizaciji, ne vašem ličnom profilu.             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Životni ciklus inicijative — State Management

### 4.1. Kompletni state dijagram

```
                                PROXY KREIRANJE
                                      │
                                      ▼
┌─────────┐   invite    ┌────────────────┐   owner    ┌─────────┐
│ IDEA    │───────────▶ │ PENDING_OWNER  │──prihvata─▶│  DRAFT  │
│         │  + QR kod   │ (čeka vlasnika) │            │         │
└─────────┘             └────────────────┘            └────┬────┘
     │                        │                            │
     │  direktno              │ owner odbija               │
     │  kreiranje             ▼                            │
     │                  ┌───────────┐                      │
     │                  │ ABANDONED │                      │
     │                  └───────────┘                      │
     │                                                     │
     └─────────────────────────────────────────────┐       │
                                                   ▼       ▼
                                              ┌─────────────────┐
                                              │     DRAFT       │
                                              │  Vidljivo SAMO  │
                                              │  timu           │
                                              └────────┬────────┘
                                                       │
                                             owner klikne „Objavi"
                                                       │
                                          ┌────────────┴────────────┐
                                          │                         │
                                          ▼                         ▼
                                   ┌──────────┐            ┌───────────────┐
                           (nema   │PUBLISHED │   (ima     │  GATHERING    │
                          predus.) │          │  predusl.)  │  Prikupljanje │
                                   └─────┬────┘            └───────┬───────┘
                                         │              ┌──────────┴──────┐
                                         │         100% ispunjeno    rok istekao
                                         │              │                 │
                                         │              ▼                 ▼
                                         │        ┌───────────┐    ┌──────────┐
                                         └───────▶│  ACTIVE   │    │ EXPIRED  │
                                                  └─────┬──────┘   └──────────┘
                                              ┌─────────┼──────────┐
                                              ▼         ▼          ▼
                                       ┌──────────┐ ┌────────┐ ┌──────────┐
                                       │ PAUSED   │ │COMPLET.│ │CANCELLED │
                                       └──────────┘ └───┬────┘ └──────────┘
                                                        ▼
                                                  ┌───────────┐
                                                  │ ARCHIVED  │
                                                  └───────────┘
```

### 4.2. Proxy kreiranje i ownership transfer

Đuka opisuje ideju Draganu. Dragan kreira inicijativu sa Đukinim emailom. Platforma šalje invite (email + QR). Đuka prihvata → postaje Owner, Dragan postaje tim member (Creator role).

### 4.3. Rokovi, trajanje i reaktivacija

#### 4.3.1. Tri režima trajanja

Svaka inicijativa pri kreiranju definiše **režim trajanja**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     REŽIMI TRAJANJA INICIJATIVE                     │
│                                                                     │
│  ┌─── ♾️ OTVORENA (neograničeno) ──────────────────────────────┐   │
│  │                                                               │  │
│  │  Nema roka. Inicijativa živi dok Owner ne odluči da je       │  │
│  │  zatvori, ili dok se ne završi prirodno.                     │  │
│  │                                                               │  │
│  │  Idealno za: Topli kutak (trajan prostor), rekurentne        │  │
│  │  akcije (čišćenje parka svake subote), dugoročne projekte    │  │
│  │                                                               │  │
│  │  Zaštita: Sistem pita Owner-a svakih 90 dana:               │  │
│  │  „Inicijativa je i dalje aktivna? [Da] [Pauziraj] [Zatvori]"│  │
│  │  Ako ne odgovori 14 dana → automatski PAUSED                │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── ⏰ SA ROKOM (deadline) ──────────────────────────────────┐   │
│  │                                                               │  │
│  │  Fiksni datum do koga preduslovi moraju biti ispunjeni.      │  │
│  │  Posle roka: EXPIRED (ako preduslovi nisu ispunjeni)         │  │
│  │              ili ACTIVE (ako jesu).                           │  │
│  │                                                               │  │
│  │  Idealno za: Kampanje, fundraising, jednokratne akcije       │  │
│  │                                                               │  │
│  │  Primer: „Skupiti 2500€ do 30. aprila"                      │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── ⏰+ SA ROKOM + GRACE PERIOD ────────────────────────────┐   │
│  │                                                               │  │
│  │  Isti kao „sa rokom" ali sa dodatnim periodom posle roka.    │  │
│  │  Grace period: 7/14/30 dana posle deadline-a.                │  │
│  │                                                               │  │
│  │  Tokom grace perioda:                                        │  │
│  │  • Inicijativa ostaje vidljiva sa oznakom ⚠️ „Rok istekao"  │  │
│  │  • Pledževi se i dalje primaju                               │  │
│  │  • Owner može produžiti rok ili zatvoriti                    │  │
│  │  • Posle grace perioda → EXPIRED                            │  │
│  │                                                               │  │
│  │  Idealno za: Kampanje koje su „skoro" stigle do cilja       │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.3.2. Životni tok sa rokovima

```
                        GATHERING faza
                             │
                    ┌────────┴────────┐
                    │                 │
              Rok NIJE istekao   Rok ISTEKAO
                    │                 │
                    │            ┌────┴─────┐
                    │            │          │
                    │       Grace period  Nema grace
                    │       definisan     perioda
                    │            │          │
                    │            ▼          ▼
                    │     ┌──────────┐  ┌──────────┐
                    │     │ GRACE    │  │ EXPIRED  │
                    │     │ PERIOD   │  └─────┬────┘
                    │     │ ⚠️ 14 d. │        │
                    │     └────┬─────┘        │
                    │          │              │
                    │    ┌─────┴──────┐       │
                    │    │            │       │
                    │ Prikupljeno  Grace      │
                    │ dovoljno     istekao    │
                    │    │            │       │
                    │    ▼            ▼       │
                    │ ┌──────┐  ┌──────────┐ │
                    │ │ACTIVE│  │ EXPIRED  │ │
                    │ └──────┘  └─────┬────┘ │
                    │                 │      │
              100%  │                 │      │
              ispunj│            ┌────┴──────┤
                    │            │           │
                    ▼            ▼           │
              ┌──────────┐ ┌──────────────┐ │
              │  ACTIVE  │ │Owner odlučuje│ │
              └──────────┘ │             │ │
                           │ [Reaktiviraj]│ │
                           │ [Zatvori]    │ │
                           │ [Produži rok]│ │
                           └──────────────┘ │
                                │           │
                           Reaktiviraj      │
                                │           │
                                ▼           │
                          ┌───────────┐     │
                          │ GATHERING │◄────┘
                          │ (novi rok) │ ← Owner može reaktivirati
                          └───────────┘   EXPIRED inicijativu
```

#### 4.3.3. Reaktivacija — Flow

Expired inicijativa se može **reaktivirati** pod sledećim uslovima:

| Uslov | Opis |
|-------|------|
| **Ko može** | Samo Owner |
| **Kad** | U roku od 6 meseci od expiracije (posle toga → ARCHIVED) |
| **Šta se dešava** | Inicijativa se vraća u GATHERING sa novim rokom |
| **Pledževi** | Postojeći pledževi ostaju (ako pledžeri ne povuku) |
| **Escrow** | Novac ostaje na escrow-u — ne vraća se automatski pri expiraciji (tek pri CANCELLED) |
| **Notifikacija** | Svi followeri i pledžeri dobijaju: „Inicijativa je reaktivirana sa novim rokom" |
| **Ograničenje** | Max 2 reaktivacije — posle toga mora nova inicijativa |

```
┌─────────────────────────────────────────────────────────────────┐
│  ♻️ REAKTIVACIJA — Topli kutak Zvezdara                         │
│                                                                  │
│  Inicijativa je istekla 30. aprila sa 74% ispunjenih preduslova.│
│                                                                  │
│  Razlog isteka: Nedovoljno finansijskih sredstava u roku        │
│  Trenutni pledževi: 1.850€ od 2.500€ cilja                     │
│  Pledžeri: 67 (svi zadržali pledževe)                           │
│                                                                  │
│  ┌─── Opcije ────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  ● Reaktiviraj sa novim rokom                              │  │
│  │    Novi rok: [31. maj 2026.]                               │  │
│  │    Poruka za followere: [Produžavamo kampanju jer smo     │  │
│  │    skoro stigli! Fali još samo 650€.]                     │  │
│  │                                                            │  │
│  │  ○ Smanji cilj i aktiviraj                                │  │
│  │    Novi cilj: [1.850€] (koliko je prikupljeno)            │  │
│  │    Napomena: Inicijativa kreće sa smanjenim obimom         │  │
│  │                                                            │  │
│  │  ○ Zatvori (CANCELLED)                                    │  │
│  │    Novac se vraća svim donatorima sa escrow-a             │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Reaktivacije do sad: 0/2 (max 2)                               │
│                                                                  │
│  [Potvrdi]                                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.3.4. Automatski checkovi za otvorene (neograničene) inicijative

| Check | Kad | Akcija |
|-------|-----|--------|
| **90-dnevni ping** | Svakih 90 dana za otvorene inicijative | Owner potvrdi da je i dalje aktivna |
| **Neodgovor 14 dana** | Owner ne odgovori na ping | Automatski PAUSED |
| **Neaktivnost 30 dana** | Nema nijedan update/komentar/pledž 30 dana | Banner ⚠️ „Inicijativa neaktivna" |
| **Neaktivnost 90 dana** | Nema aktivnosti 90 dana + Owner ne odgovara | Automatski PAUSED + notif followerima |
| **PAUSED > 6 meseci** | Pauza traje više od 6 meseci | Automatski ARCHIVED |

---

## 5. Vidljivost i domet inicijative

### 4.1. Zašto je ovo fundamentalno

Nije svaka inicijativa za svakoga. Neke su javne za ceo svet. Neke su relevantne samo za jedan kvart. Neke su političke i tiču se samo državljana jedne zemlje. Neke su poverljive — u fazi pripreme, samo za odabrane ljude.

**Vidljivost** odgovara na pitanje: **KO može da vidi inicijativu?**
**Domet** odgovara na pitanje: **ZA KOGA je inicijativa relevantna i GDE deluje?**

Ova dva koncepta su nezavisna ali komplementarna:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   VIDLJIVOST (ko vidi)          DOMET (za koga / gde)             │
│   ════════════════════          ══════════════════════             │
│                                                                     │
│   Ko ima PRISTUP da             Koja je GEOGRAFSKA i               │
│   vidi inicijativu?             TEMATSKA oblast delovanja?         │
│                                                                     │
│   • Javno (svi)                 • Mikro-lokalna (ulica, blok)     │
│   • Registrovani korisnici      • Lokalna (kvart, MZ, opština)    │
│   • Specifične grupe            • Gradska (ceo grad)              │
│   • Samo tim                    • Regionalna (više gradova)       │
│   • Samo državljani X           • Nacionalna (cela država)        │
│   • Custom lista                • Dijaspora (srbi u inostr.)      │
│                                 • Međunarodna (više država)        │
│   Primer:                       • Globalna (svet)                 │
│   Inicijativa je JAVNA          • Tematska (ne-geo, po domenu)   │
│   ali njen domet je             • Politička (izbori, zakoni)      │
│   LOKALAN (Zvezdara)                                               │
│                                 Primer:                            │
│                                 Topli kutak = Lokalna (Zvezdara)  │
│                                 IT obuka = Online/Globalna        │
│                                 Peticija = Nacionalna/Politička   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2. Vidljivost — Ko može da vidi inicijativu

#### 4.2.1. Nivoi vidljivosti

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NIVOI VIDLJIVOSTI                                │
│                                                                     │
│  ┌─── 🌍 JAVNA (Public) ───────────────────────────────────────┐   │
│  │  Svi mogu da vide — uključujući neregistrovane posetioce.   │  │
│  │  Indeksira se u pretrazi. Deli se na društvenim mrežama.    │  │
│  │  Mikro-sajt je javno dostupan.                              │  │
│  │                                                              │  │
│  │  Primena: većina inicijativa — čišćenje, renoviranje,      │  │
│  │  kulturni događaji, humanitarne akcije                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 👤 REGISTROVANI (Members Only) ──────────────────────────┐   │
│  │  Samo registrovani korisnici platforme mogu da vide.        │  │
│  │  Posetilac bez naloga vidi samo naslov i poziv za regist.   │  │
│  │  Ne indeksira se javno.                                     │  │
│  │                                                              │  │
│  │  Primena: inicijative koje traže verifikovane učesnike,     │  │
│  │  rad sa osetljivim grupama, polujavni projekti              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🔗 PO POZIVU (Invite Only) ─────────────────────────────┐   │
│  │  Vidljivo samo korisnicima koji su eksplicitno pozvani      │  │
│  │  (email, QR, direktan link sa tokenom).                     │  │
│  │  Idealno za rane faze ili osetljive inicijative.            │  │
│  │                                                              │  │
│  │  Primena: inicijative u fazi pripreme, pravni slučajevi,   │  │
│  │  osetljive humanitarne situacije                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🤝 PARTNERSKE INICIJATIVE (Network) ─────────────────────┐  │
│  │  Vidljivo članovima DRUGIH specifičnih inicijativa.         │  │
│  │  Inicijativa A kaže: „Vidljivo za članove inicijative B i C"│  │
│  │  Stvara mrežu međusobno povezanih inicijativa.              │  │
│  │                                                              │  │
│  │  Primena: koalicije inicijativa, koordinirane kampanje,     │  │
│  │  mreže NVO organizacija                                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🏛️ GEO-OGRANIČENA (Geo-restricted) ─────────────────────┐  │
│  │  Vidljivo samo korisnicima iz određene lokacije/države.     │  │
│  │  Verifikacija: IP geolokacija, profil korisnika, ili       │  │
│  │  self-deklaracija sa mogućnošću provere.                    │  │
│  │                                                              │  │
│  │  Primena: politička inicijativa relevantna samo za          │  │
│  │  državljane Srbije, lokalna peticija samo za stanovnike     │  │
│  │  Beograda, glasanje koje zahteva lokalnu verifikaciju       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🔒 PRIVATNA (Tim Only) ─────────────────────────────────┐   │
│  │  Vidljivo SAMO članovima tima inicijative.                  │  │
│  │  Potpuno nevidljivo svima ostalim. Ne pojavljuje se u       │  │
│  │  pretrazi, na mapi, u kalendaru.                            │  │
│  │                                                              │  │
│  │  Primena: Draft faza (automatski), interno planiranje,      │  │
│  │  testne inicijative                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🔧 CUSTOM (Prilagođena pravila) ────────────────────────┐   │
│  │  Vlasnik definiše specifična pravila vidljivosti:           │  │
│  │  • Lista dozvoljenih email domena (@nvo.org, @opština.rs)  │  │
│  │  • Lista konkretnih korisnika (whitelist)                   │  │
│  │  • Kombinacija uslova (registrovan + iz Beograda + član    │  │
│  │    inicijative X)                                           │  │
│  │                                                              │  │
│  │  Primena: specijalni projekti, partnerstva sa institucijama │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.2.2. Komparativna tabela vidljivosti

| Nivo | Ko vidi | Pretraga | Mapa | Deljenje | SEO | Primena |
|------|---------|:--------:|:----:|:--------:|:---:|---------|
| 🌍 **Javna** | Svi (i neregistrovani) | ✅ | ✅ | ✅ | ✅ | Većina inicijativa |
| 👤 **Registrovani** | Samo sa nalogom | ✅ (za reg.) | ✅ (za reg.) | Link → registracija | — | Polujavni projekti |
| 🔗 **Po pozivu** | Samo pozvani | — | — | Invite link/QR | — | Osetljive inicijative |
| 🤝 **Partnerske** | Članovi povezanih inicijativa | Unutar mreže | Unutar mreže | Interno | — | Koalicije, mreže |
| 🏛️ **Geo-ograničena** | Korisnici iz određene lokacije | ✅ (za njih) | ✅ (za njih) | ✅ (ali pristup ograničen) | Delimično | Politička, lokalna |
| 🔒 **Privatna** | Samo tim | — | — | — | — | Draft, interno |
| 🔧 **Custom** | Po pravilima Ownera | Po pravilu | Po pravilu | Po pravilu | — | Specijalni projekti |

#### 4.2.3. Pristup za vidljivost — Poređenje

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Samo javno + privatno** | Dva nivoa: svi vide ili niko | Jednostavno | Nema nijansa, ne pokriva realne potrebe |
| **B. Tri nivoa (javno/registrovani/tim)** | Dodaje registrovane kao srednji nivo | Pokriva 80% slučajeva | Ne pokriva koalicije, geo-restrikciju |
| **C. Slojevita vidljivost (⭐ Preporuka)** | Svih 7 nivoa sa jasnim pravilima | Pokriva sve realne scenarije | Složenije za implementaciju i UI |
| **D. ACL (Access Control List)** | Potpuno granularan pristup, po korisniku | Maksimalna kontrola | Komplikovan UI, teško za održavanje |

**Preporuka: Pristup C (Slojevita vidljivost)**

**Obrazloženje:**
1. **Javno** je default i pokriva 70%+ inicijativa — nema komplikacije za većinu
2. **Registrovani** je bitan za inicijative koje zahtevaju odgovornost učesnika
3. **Po pozivu** je kritičan za osetljive situacije (pravni slučajevi, ranjive grupe)
4. **Partnerske** omogućavaju mrežu inicijativa koja sarađuje — koalicije su temelj aktivizma
5. **Geo-ograničena** je neophodna za političke inicijative i lokalna glasanja
6. **Privatna** već postoji (Draft stanje) — samo formalizujemo
7. **Custom** je safety net za sve što gornji nivoi ne pokrivaju

UI komplikacija se rešava tako što se **default stavlja na Javno** a ostali nivoi su u „Napredna podešavanja" — prosečan korisnik nikad ne mora da ih vidi.

#### 4.2.4. UI za podešavanje vidljivosti

```
┌─────────────────────────────────────────────────────────────────┐
│  👁️ VIDLJIVOST INICIJATIVE                                      │
│                                                                  │
│  ● 🌍 Javna — svi mogu da vide (preporučeno)                   │
│  ○ 👤 Samo registrovani korisnici                               │
│  ○ 🔗 Po pozivu (invite only)                                   │
│                                                                  │
│  ─── Napredne opcije ────────────────────────────────────────   │
│                                                                  │
│  ○ 🤝 Partnerske inicijative                                    │
│     Vidljivo za članove: [+ Dodaj inicijativu]                  │
│     Trenutno povezane: Čist park Kalemegdan, IT obuka BGD      │
│                                                                  │
│  ○ 🏛️ Geo-ograničena                                            │
│     Vidljivo samo za korisnike iz:                              │
│     ○ Grada: [Beograd ▾]                                       │
│     ○ Regiona: [Srbija ▾]                                       │
│     ○ Država: [☑ Srbija] [☑ Crna Gora] [☐ BiH]               │
│     Verifikacija: [Self-deklaracija ▾]                          │
│                                                                  │
│  ○ 🔧 Custom pravila                                            │
│     Email domeni: [@nvo.org, @opstina-zvezdara.rs]              │
│     Whitelist korisnika: [+ Dodaj korisnika]                    │
│                                                                  │
│  ⓘ Vidljivost se može promeniti u svakom trenutku.             │
│  ⓘ Promena sa javne na restriktivnu NE briše postojeće         │
│    followere — ali novi neće moći da pristupe.                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3. Domet — Geografska i tematska oblast delovanja

#### 4.3.1. Tipovi dometa

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DOMET INICIJATIVE                            │
│                                                                     │
│  ═══════════════════════════════════════                            │
│  GEOGRAFSKI DOMET (gde deluje)                                      │
│  ═══════════════════════════════════════                            │
│                                                                     │
│  ┌─── 🏠 MIKRO-LOKALNA ───────────────────────────────────────┐   │
│  │  Ulica, blok, zgrada, mesna zajednica.                      │  │
│  │  Primer: „Klupa ispred zgrade u Bloku 45"                  │  │
│  │  Primer: „Čišćenje dvorišta MZ Mirijevo"                   │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🏘️ LOKALNA ────────────────────────────────────────────┐    │
│  │  Kvart, opština, deo grada.                                 │  │
│  │  Primer: „Topli kutak — opština Zvezdara"                  │  │
│  │  Primer: „Rampa za školu Đuka — Voždovac"                  │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🏙️ GRADSKA ────────────────────────────────────────────┐    │
│  │  Ceo grad.                                                  │  │
│  │  Primer: „Mreža Toplih kutaka — Beograd"                   │  │
│  │  Primer: „Čist vazduh — monitoring AQI Beograd"            │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🗺️ REGIONALNA ─────────────────────────────────────────┐    │
│  │  Više gradova, okrug, pokrajina, ili geografski region.     │  │
│  │  Primer: „IT obuka za mlade — Vojvodina"                   │  │
│  │  Primer: „Zaštita reke Morave — Pomoravlje"                │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🇷🇸 NACIONALNA ─────────────────────────────────────────┐   │
│  │  Cela država.                                               │  │
│  │  Primer: „Peticija za zakon o čistom vazduhu — Srbija"     │  │
│  │  Primer: „Baza podataka pristupačnih prostora — Srbija"    │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🌐 DIJASPORA ───────────────────────────────────────────┐   │
│  │  Zajednica državljana u inostranstvu.                       │  │
│  │  Primer: „Humanitarna pomoć iz dijaspore — poplave 2026"   │  │
│  │  Primer: „Glasaj iz inostranstva — logistička podrška"     │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🌍 MEĐUNARODNA ─────────────────────────────────────────┐   │
│  │  Više država, prekogranična saradnja.                       │  │
│  │  Primer: „Čišćenje Dunava — Srbija + Rumunija + Bugarska"  │  │
│  │  Primer: „Balkanska mreža za zaštitu dece"                 │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🌐 GLOBALNA ────────────────────────────────────────────┐   │
│  │  Bez geografskog ograničenja. Svet.                         │  │
│  │  Primer: „Open-source platforma za aktivizam" (ova platf.) │  │
│  │  Primer: „Globalni dan čišćenja parkova"                   │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ═══════════════════════════════════════                            │
│  TEMATSKI DOMET (o čemu se radi)                                    │
│  ═══════════════════════════════════════                            │
│                                                                     │
│  ┌─── 🏛️ POLITIČKA ───────────────────────────────────────────┐   │
│  │  Tiče se političkih procesa, zakona, izbora, peticija.      │  │
│  │  Posebna pravila: verifikacija glasača, geo-restrikcija,   │  │
│  │  transparentnost finansiranja, moderacija kampanja.         │  │
│  │                                                              │  │
│  │  Primer: „Peticija za izmenu zakona o socijalnoj zaštiti"   │  │
│  │  Primer: „Izborna inicijativa — nezavisni posmatrači"      │  │
│  │  Primer: „Zahtev za transparentnost opštinskog budžeta"    │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🤝 SOCIJALNA ───────────────────────────────────────────┐   │
│  │  Fokus na socijalnu zaštitu, ranjive grupe, jednakost.      │  │
│  │  Primer: Topli kutak, pomoć starijima, inkluzija           │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🌿 EKOLOŠKA ────────────────────────────────────────────┐   │
│  │  Životna sredina, čist vazduh, voda, parkovi.               │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🏗️ INFRASTRUKTURNA ────────────────────────────────────┐    │
│  │  Fizička infrastruktura — putevi, rampe, klupe, osvetljenje.│  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 📚 OBRAZOVNA ───────────────────────────────────────────┐   │
│  │  Edukacija, obuke, digitalna pismenost, mentorstvo.        │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🎭 KULTURNA ────────────────────────────────────────────┐   │
│  │  Umetnost, kultura, baština, murali, festivali.            │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── 🔍 TRANSPARENTNOST / WATCHDOG ──────────────────────────┐   │
│  │  Monitoring javnih institucija, zahtevi za informacije,     │  │
│  │  anti-korupcija, odgovornost vlasti.                        │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── ⚖️ PRAVNA ──────────────────────────────────────────────┐   │
│  │  Zaštita prava, besplatna pravna pomoć, zagovaranje.       │  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ℹ️ Inicijativa može imati VIŠE tematskih dometa (tagovi).        │
│  ℹ️ Geografski domet je uvek JEDAN (najuži koji pokriva).         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.3.2. Veza geografskog dometa i lokacije

| Geo-domet | Lokacija na mapi | Radius pretrage | Relevantnost za korisnika |
|-----------|:----------------:|:---------------:|--------------------------|
| 🏠 Mikro-lokalna | 📍 Tačan pin | < 2 km | Samo najbliži komšije |
| 🏘️ Lokalna | 📍 Pin + oblast | 2–10 km | Stanovnici opštine/kvarta |
| 🏙️ Gradska | 📍 Centar grada | Ceo grad | Svi u gradu |
| 🗺️ Regionalna | 📍 Više pinova | 50–200 km | Više gradova |
| 🇷🇸 Nacionalna | 🗺️ Mapa zemlje | Cela država | Svi državljani |
| 🌐 Dijaspora | 🌍 Globalno + SR | Svet (sr. zajednica) | Srbi u inostranstvu |
| 🌍 Međunarodna | 🌍 Više zemalja | Definisane zemlje | Državljani tih zemalja |
| 🌐 Globalna | 🌍 Svet | Neograničeno | Svi |

#### 4.3.3. Politička inicijativa — Posebna pravila

Političke inicijative zahtevaju **strožija pravila** jer direktno utiču na demokratske procese:

| Pravilo | Opis | Zašto |
|---------|------|-------|
| **Obavezna verifikacija kreatora** | KYC / lična karta za kreiranje političke inicijative | Sprečava anonimne manipulacije |
| **Geo-restrikcija za glasanje** | Samo državljani / stanovnici mogu glasati | Sprečava strano mešanje |
| **Transparentnost finansiranja** | SVE donacije javne, bez anonimnih > 10€ | Zakon o finansiranju kampanja |
| **Moderacija sadržaja** | Pojačana moderacija za govor mržnje, dezinformacije | Zaštita demokratskog procesa |
| **Oznaka „Politička"** | Jasna vizuelna oznaka da je inicijativa politička | Korisnik zna kontekst |
| **Cooling period za glasanje** | Glasanje je otvoreno min. 7 dana | Sprečava impulzivne odluke |
| **Zabrana plaćenih pozicija** | Nema plaćenog aktivizma u političkim inicijativama | Sprečava kupovinu podrške |

### 4.4. Matrica: Vidljivost × Domet

```
                         VIDLJIVOST
                 Javna  Reg.  Poziv  Geo   Privatna
              ┌───────┬──────┬──────┬─────┬────────┐
  Mikro-lok.  │  ✅   │  ✅  │  ✅  │  —  │   ✅   │
  Lokalna     │  ✅   │  ✅  │  ✅  │  ✅ │   ✅   │
  Gradska     │  ✅   │  ✅  │  ✅  │  ✅ │   ✅   │
D Regionalna  │  ✅   │  ✅  │  ✅  │  ✅ │   ✅   │
O Nacionalna  │  ✅   │  ✅  │  ✅  │  ✅ │   ✅   │
M Dijaspora   │  ✅   │  ✅  │  ✅  │  ✅ │   ✅   │
E Međunarodna │  ✅   │  ✅  │  ✅  │  ✅ │   ✅   │
T Globalna    │  ✅   │  ✅  │  ✅  │  —  │   ✅   │
  Politička   │  ✅   │  ✅  │  —*  │  ✅ │   —*   │
              └───────┴──────┴──────┴─────┴────────┘

  ✅ = dozvoljena kombinacija
  —  = ne preporučuje se / nema smisla
  —* = zabranjeno (politička mora biti transparentna)
```

**Napomena:** Politička inicijativa NE MOŽE biti po pozivu ili privatna — mora imati javnu transparentnost. Jedina dozvoljana restrikcija je geo (samo državljani).

### 4.5. Kako domet utiče na platformu

| Funkcija | Uticaj dometa |
|----------|--------------|
| **Pretraga** | Default filtrira po dometu korisnikove lokacije. Gradska = prikazuje se samo korisnicima u tom gradu (ali svi mogu pronaći ako traže) |
| **Home strana** | „Hot" inicijative prioritizuju korisnikov domet. Lokalne se prikazuju prve |
| **Kalendar** | Javni kalendar filtrira po dometu — korisnik vidi akcije iz svog grada |
| **Oglasna tabla** | Geo-filter na oglasima prati domet inicijative |
| **Matching** | Matching engine koristi domet kao signal — ne šalje poziv za mikro-lokalnu inicijativu korisniku sa drugog kraja grada |
| **Liquid Democracy** | Glasanje ograničeno na domet — za lokalnu inic. glasaju samo lokalni |
| **Fundraising** | Kampanja prikazuje „od 67 donatora, 54 su iz Zvezdare" — lokalni kontekst |
| **Mapa** | Zoom level mape se automatski prilagođava dometu |

### 4.6. UI za podešavanje dometa

```
┌─────────────────────────────────────────────────────────────────┐
│  🗺️ DOMET INICIJATIVE                                           │
│                                                                  │
│  Geografski domet:                                               │
│  ○ 🏠 Mikro-lokalna (ulica, blok, zgrada)                      │
│     Opis: [Blok 45, Novi Beograd]                               │
│  ● 🏘️ Lokalna (kvart, opština, MZ)                              │
│     Opština: [Zvezdara ▾]   MZ: [Cvetkova pijaca ▾]           │
│  ○ 🏙️ Gradska                                                   │
│     Grad: [Beograd ▾]                                           │
│  ○ 🗺️ Regionalna                                                │
│     Region: [Beogradski okrug ▾]                                │
│  ○ 🇷🇸 Nacionalna                                               │
│     Država: [Srbija ▾]                                          │
│  ○ 🌐 Dijaspora                                                 │
│     Zemlja porekla: [Srbija ▾]                                  │
│  ○ 🌍 Međunarodna                                               │
│     Zemlje: [☑ Srbija] [☑ Crna Gora] [+ Dodaj]                │
│  ○ 🌐 Globalna                                                  │
│                                                                  │
│  Tematski domet (izaberi jedan ili više):                        │
│  [☐ Politička] [☑ Socijalna] [☐ Ekološka]                     │
│  [☐ Infrastrukturna] [☐ Obrazovna] [☑ Kulturna]               │
│  [☐ Transparentnost] [☐ Pravna]                                │
│                                                                  │
│  ⚠️ Ako izabereš „Politička" — primenjuju se posebna pravila   │
│     (obavezna verifikacija, geo-restrikcija za glasanje,        │
│      transparentnost finansiranja).                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.7. Promena vidljivosti i dometa tokom života inicijative

```
TIPIČAN ŽIVOTNI PUT VIDLJIVOSTI:

  DRAFT           →  🔒 Privatna (automatski)
                     Samo tim vidi

  PUBLISHED /     →  Owner bira:
  GATHERING          🌍 Javna (najčešće)
                     👤 Registrovani
                     🏛️ Geo-ograničena (za političke)

  ACTIVE          →  Može se suziti ali NE proširiti
                     (ako je bila „po pozivu", ne može postati javna
                      bez eksplicitne odluke i perioda najave)

  COMPLETED       →  🌍 Javna (preporučeno za inspiraciju)
                     Before/After galerija, finansijski izveštaj

  ARCHIVED        →  🌍 Javna (čuva se kao inspiracija)
```

**Važno pravilo:** Vidljivost se može **suziti** u svakom trenutku (javno → registrovani), ali **proširivanje** (pozivno → javno) zahteva 48h najavu svim postojećim učesnicima — jer su možda učestvovali pod pretpostavkom privatnosti.

### 4.8. Pristup za domet — Poređenje

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Bez dometa (samo lokacija)** | Inicijativa ima lokaciju ali ne i formalni domet | Jednostavno | Nema filtriranja po relevantnosti |
| **B. Jednostavno: lokalna/nacionalna/globalna** | Tri nivoa geo-dometa | Brzo, razumljivo | Nedovoljno granularno |
| **C. Slojevit geo + tematski (⭐ Preporuka)** | 8 geo-nivoa + tematski tagovi + posebna pravila za političke | Pokriva sve scenarije, precizno filtriranje | Složeniji UI (rešivo sa smart default-ima) |
| **D. Free-form tags** | Korisnik sam definiše domet tekstualno | Maksimalna fleksibilnost | Nekonzistentno, teško za filtriranje |

**Preporuka: Pristup C (Slojevit geo + tematski)**

**Obrazloženje:**
1. **8 geo-nivoa** pokrivaju sve realne scenarije — od klupe ispred zgrade do globalne kampanje
2. **Tematski tagovi** omogućavaju cross-geo pretragu — „prikaži mi sve ekološke inicijative u Srbiji"
3. **Posebna pravila za političke** su neophodna — politički aktivizam zahteva transparentnost i verifikaciju
4. **Smart default-i** rešavaju UI složenost: ako korisnik izabere lokaciju „Zvezdara", domet se automatski postavlja na „Lokalna (Zvezdara)" — ne mora ručno
5. **Matching engine** koristi domet kao jak signal — ne šalje notifikaciju za mikro-lokalnu inicijativu korisniku na drugom kraju grada

---

## 6. Timovi, radne grupe, kolaboracija i koordinacija

### 4.1. Tri nivoa organizacije

```
┌─────────────────────────────────────────────────────────────────────┐
│                   TRI NIVOA ORGANIZACIJE                            │
│                                                                     │
│  ┌─── NIVO 1: TIM INICIJATIVE ──────────────────────────────────┐  │
│  │  Ceo tim koji radi na inicijativi.                           │  │
│  │  Owner, Admini, svi članovi.                                 │  │
│  │  Vidi sve, koordinira sve.                                   │  │
│  │                                                              │  │
│  │  Primer: Tim „Topli kutak" — 12 članova                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── NIVO 2: RADNE GRUPE ─────────────────────────────────────┐   │
│  │  Specijalizovani pod-timovi za konkretne aspekte.            │  │
│  │  Svaka radna grupa ima svog vođu, zadatke, rok.             │  │
│  │  Članovi mogu biti u više radnih grupa.                      │  │
│  │                                                              │  │
│  │  Primer: RG Logistika (3 čl.), RG Dizajn (2 čl.),          │  │
│  │          RG PR/Komunikacije (2 čl.), RG Finansije (2 čl.)   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── NIVO 3: AD-HOC TASKOVI ──────────────────────────────────┐   │
│  │  Pojedinačni zadaci dodeljeni članovima.                     │  │
│  │  Deadline, prioritet, status, komentar.                      │  │
│  │  Prate se na kanban tabli ili u listi.                       │  │
│  │                                                              │  │
│  │  Primer: „Pozvati firmu ABC za donaciju" — rok: petak       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2. Uloge u timu

| Uloga | Opis | Ključne dozvole |
|-------|------|----------------|
| **Owner** | Vlasnik — brisanje, publish, transfer | Sve |
| **Admin** | Upravljanje — sve osim brisanja/transfera | Tim, stanje, odobrenja |
| **Editor** | Sadržaj — tekst, slike, milestones | Uređivanje |
| **Coordinator** | Operativni — organizuje volontere, verifikuje | Pledževi, verifikacija |
| **Reviewer** | Evaluacija — ocenjuje rad | Rating |
| **Finance** | Finansije — isplate, izveštaji | Fin. dashboard |
| **Activist** | Radnik — izvršava, logira vreme | Timesheet |
| **Observer** | Čita sve — savetnik, mentor | Read-only |

### 4.3. Radne grupe — Detaljno

#### 4.3.1. Struktura radne grupe

```
┌─────────────────────────────────────────────────────────────────┐
│  👥 RADNA GRUPA: Logistika                                      │
│  Inicijativa: Topli kutak Zvezdara                               │
│                                                                  │
│  Vođa: Marko P. (Coordinator)                                   │
│  Članovi: Ana S., Jovan K.                                      │
│  Kreirana: 5. apr 2026.                                          │
│                                                                  │
│  📋 OPIS:                                                        │
│  Nabavka materijala, transport igračaka, organizacija prostora,  │
│  koordinacija sa MZ Zvezdara za ključeve i raspored.            │
│                                                                  │
│  ┌─── ZADACI (Kanban) ────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  TODO              U TOKU             ZAVRŠENO             │ │
│  │  ─────             ──────             ────────             │ │
│  │  ┌──────────┐      ┌──────────┐      ┌──────────┐        │ │
│  │  │Nabaviti  │      │Kontakt   │      │Ključevi  │        │ │
│  │  │grijalicu │      │sa MZ za  │      │od MZ ✅  │        │ │
│  │  │          │      │raspored  │      │          │        │ │
│  │  │📅 15.apr │      │👤 Marko  │      │👤 Ana    │        │ │
│  │  │👤 Jovan  │      │📅 10.apr │      │📅 3.apr  │        │ │
│  │  └──────────┘      └──────────┘      └──────────┘        │ │
│  │  ┌──────────┐                        ┌──────────┐        │ │
│  │  │Transport │                        │Igračke   │        │ │
│  │  │tepih 2x3m│                        │donirane ✅│       │ │
│  │  │          │                        │          │        │ │
│  │  │📅 18.apr │                        │👤 Ana    │        │ │
│  │  │👤 ?      │                        └──────────┘        │ │
│  │  └──────────┘                                             │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─── KOMUNIKACIJA ──────────────────────────────────────────┐  │
│  │  💬 Grupni chat (samo članovi RG)                         │  │
│  │  📎 Deljeni fajlovi: 3 dokumenta                         │  │
│  │  📅 Sledeći sastanak: 8. apr, 18h (online)               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  [➕ Dodaj zadatak]  [👤 Dodaj člana]  [📊 Izveštaj]           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.3.2. Predefinisane radne grupe (šabloni)

| Radna grupa | Opis | Tipične pozicije |
|-------------|------|------------------|
| **Logistika** | Nabavka, transport, prostor, oprema | Koordinator, vozač, majstor |
| **Dizajn & Kreativa** | Vizuelni identitet, posteri, flajeri, brending | Grafički dizajner, fotograf |
| **PR & Komunikacije** | Društvene mreže, mediji, flajeri, outreach | Social media manager, PR |
| **Finansije** | Budžet, donacije, izveštaji, transparentnost | Računovođa, finance lead |
| **Pravni tim** | Dozvole, ugovori, pravna analiza | Advokat, pravnik |
| **IT & Digitalno** | Sajt, email, digitalni alati, automatizacija | DevOps, programer |
| **Volonteri & HR** | Regrutacija, raspored, koordinacija volontera | Koordinator volontera |
| **Fundraising** | Prikupljanje sredstava, kampanje, sponzori | Fundraiser, kampanja menadžer |

#### 4.3.3. Cross-inicijativne radne grupe

Radna grupa može biti **deljena između više inicijativa**. Na primer, „PR tim Zvezdara" može raditi na PR-u za Topli kutak I za Čist park istovremeno.

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│   Inicijativa A              Inicijativa B            │
│   Topli kutak                Čist park                │
│        │                         │                    │
│        │    ┌─────────────┐      │                    │
│        └───▶│  RG: PR tim │◄─────┘                    │
│             │  Zvezdara   │                            │
│             │             │                            │
│             │  Ana — SM   │                            │
│             │  Petar — PR │                            │
│             └─────────────┘                            │
│                                                       │
│   Deljeni resursi, jedan report za obe inicijative    │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 4.4. Alati za kolaboraciju

#### 4.4.1. Pristup za kolaboracione alate — Poređenje

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Minimalan (samo komentari)** | Komunikacija kroz komentare na inicijativi | Jednostavno, nema novog UI-ja | Haotično za veće timove, nema strukture |
| **B. Integrisani kanban + chat (⭐ Preporuka)** | Built-in kanban tabla, grupni chat, deljeni fajlovi, kalendar | Sve na jednom mestu, kontekst očuvan | Srednja složenost implementacije |
| **C. Eksterni alati (Slack/Trello integracija)** | Platforma se integriše sa eksternim alatima | Korisnici već znaju alate | Fragmentacija, kontekst se gubi, zavisnost od 3rd party |
| **D. Full project management** | Gantt chart, zavisnosti, resource planning | Moćno za velike inicijative | Previše za male inicijative, zastrašujuće za ne-tehničke korisnike |

**Preporuka: Pristup B (Integrisani kanban + chat)**

**Obrazloženje:**
1. **Kontekst ostaje na platformi** — ne trebaju eksterni alati, sve je vezano za inicijativu
2. **Kanban je intuitivno** — TODO / U TOKU / ZAVRŠENO razumeju i ne-tehnički korisnici
3. **Grupni chat po radnoj grupi** — ciljana komunikacija, ne zagušuje ceo tim
4. **Kalendar za akcije** — vizuelni pregled svih planiranih aktivnosti
5. **Deljeni fajlovi** — dokumenti, slike, specifikacije vezane za kontekst
6. Pristup D (full PM) je previše za većinu građanskih inicijativa — ciljna grupa su obični građani, ne project manageri

#### 4.4.2. Integrisani alati — Pregled

```
┌─────────────────────────────────────────────────────────────────────┐
│                   KOLABORACIONI ALATI                                │
│                                                                     │
│  ┌─── 📋 KANBAN TABLA ──────────────────────────────────────────┐  │
│  │  Vizuelni pregled zadataka po radnim grupama.                │  │
│  │  Drag & drop. Filtriranje po članu, roku, prioritetu.       │  │
│  │  Pogled: Po radnoj grupi │ Po članu │ Po roku               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 💬 GRUPNI CHAT ───────────────────────────────────────────┐  │
│  │  Svaka radna grupa ima svoj chat kanal.                      │  │
│  │  + Opšti kanal za ceo tim inicijative.                      │  │
│  │  Mention (@Ana), reakcije, pinovanje poruka.                │  │
│  │  Fajlovi i slike direktno u chatu.                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 📅 KALENDAR AKTIVNOSTI ───────────────────────────────────┐  │
│  │  Vizuelni kalendar svih planiranih akcija.                   │  │
│  │  Sastanci, akcije, rokovi milestones-a.                     │  │
│  │  Integrisano sa notifikacijama.                             │  │
│  │  Export u iCal / Google Calendar.                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 📁 DELJENI FAJLOVI ──────────────────────────────────────┐  │
│  │  Dokumenti, specifikacije, ugovori, dozvole.               │  │
│  │  Organizovano po radnoj grupi.                              │  │
│  │  Verzionisanje — vidi ko je šta menjao.                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 📊 DASHBOARD NAPRETKA ───────────────────────────────────┐  │
│  │  Real-time pregled: koliko zadataka je završeno, ko radi,   │  │
│  │  koliko je utrošeno iz budžeta, koje radne grupe kaskaju.   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.4.3. Koordinacija aktivnosti — Kalendar

```
┌─────────────────────────────────────────────────────────────────┐
│  📅 KALENDAR — Topli kutak Zvezdara — April 2026               │
│                                                                  │
│  Pon    Uto    Sre    Čet    Pet    Sub    Ned                   │
│  ────── ────── ────── ────── ────── ────── ──────               │
│                1      2      3      4      5                     │
│                              │             │                     │
│                              │      ┌──────┤                     │
│                              │      │AKCIJA│                     │
│                              │      │Čišće-│                     │
│                              │      │nje   │                     │
│                              │      │10-14h│                     │
│                              │      └──────┘                     │
│  6      7      8      9      10     11     12                    │
│                │                    │                             │
│         ┌──────┤             ┌──────┤                             │
│         │Online│             │Rok:  │                             │
│         │sast. │             │Nabav.│                             │
│         │18h   │             │tepih │                             │
│         └──────┘             └──────┘                             │
│  13     14     15     16     17     18     19                    │
│                │                           │                     │
│         ┌──────┤                    ┌──────┤                     │
│         │Dead- │                    │VELIKO│                     │
│         │line: │                    │OTVAR-│                     │
│         │dizajn│                    │ANJE  │                     │
│         │flaj. │                    │10-18h│                     │
│         └──────┘                    └──────┘                     │
│                                                                  │
│  🟢 Akcija  🟡 Rok  🔵 Sastanak  🟣 Event                      │
│  [+ Dodaj]  [iCal export]  [Google sync]                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5. Komunikacija unutar tima

```
NIVO KOMUNIKACIJE          KANAL                    KO VIDI
─────────────────          ──────                    ────────
Ceo tim inicijative   →    #general                  Svi članovi tima
Radna grupa           →    #rg-logistika             Samo članovi RG
                           #rg-dizajn
                           #rg-pr
Owner + Admin         →    #admin (privatan)         Owner + Admini
1-na-1                →    Direktna poruka            Dva korisnika
Javno                 →    Komentari na inicijativi   Svi registrovani
```

---

## 7. QR kod sistem

### 5.1. Use cases

| # | Tip | Opis |
|---|-----|------|
| 1 | Invite u tim | QR na flajeru → prijava kao volonter |
| 2 | Ownership transfer | Proxy kreiranje → QR za prihvatanje |
| 3 | Pledž / Donacija | QR na posteru → pledge stranica |
| 4 | Prijava na poziciju | QR na oglasu → prijava |
| 5 | Tender ponuda | QR → forma za ponudu |
| 6 | Event check-in | Dan akcije → logira prisustvo |
| 7 | Fundraising kampanja | QR → donacija stranica kampanje |

### 5.2. Dinamički QR sa praćenjem (⭐ Preporuka)

- Owner vidi koliko je ljudi skeniralo QR (analytics)
- QR može istići posle definisanog roka
- Limitira se na N skeniranja
- Podržava različite kontekste
- URL je kratak i čitljiv

---

## 8. Sistem preduslova i pledževa

### 6.1. Tipovi preduslova

| Tip | Primeri |
|-----|---------|
| 💰 Finansijski | Fiksni iznos, raspon, po stavkama, budžet za kompenzacije |
| 👷 Volonterski | Broj ljudi, profil, trajanje |
| 🎓 Stručne usluge | Advokat, programer, dizajner (besplatno/plaćeno/hybrid) |
| 🧱 Materijal | Građevinski, IT oprema, igračke |
| 📋 Administrativni | Dozvola opštine, saglasnost, ugovor |
| ⏰ Vremenski | Rok, sezona, zavisnost |

### 6.2. Escrow model (⭐ Preporuka)

Novac se uplaćuje na namenski račun, čuva se do aktivacije, vraća se ako inicijativa ne uspe.

---

## 9. Plaćeni aktivizam — Model kompenzacije

### 7.1. Tiered pricing (⭐ Preporuka)

```
  30€ ┤                                    ┌──────────
      │                                    │ Tier 3
  20€ ┤                        ┌───────────┤
      │                        │  Tier 2   │
   0€ ┤────────────────────────┤           │
      │    Tier 1 (volonterski)│           │
      ├────────────┬───────────┼───────────┼────────
      0           10h        30h         50h+
```

Aktivista definiše: koliko sati daje besplatno (Tier 1), po kojoj sniženoj ceni nastavlja (Tier 2), i tržišnu cenu za ostalo (Tier 3).

---

## 10. Tender model i šabloni inicijativa

### 8.1. Tipovi tendera

Tender je **strukturirani poziv za ponude**. Postoje dva osnovna tipa:

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SINGLE TENDER vs MULTI-TENDER                      │
│                                                                     │
│  ┌─── SINGLE TENDER ────────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  Jedan zadatak → više ponuda → Owner bira JEDNU najbolju     │  │
│  │                                                               │  │
│  │  Primer: „Treba nam sajt"                                    │  │
│  │  Ponuda 1: Milan — 300€, 25h                                │  │
│  │  Ponuda 2: Ana — 0€ (vol.), 40h                              │  │
│  │  Ponuda 3: Petar — 400€, 20h                                │  │
│  │  → Owner bira jednu                                          │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── MULTI-TENDER (⭐) ────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  Jedan kompleksan zadatak → razbijen na LOT-ove →            │  │
│  │  svaki LOT prima ponude → Owner bira PO JEDNU za svaki LOT  │  │
│  │  ILI prihvata više ponuda                                    │  │
│  │                                                               │  │
│  │  Primer: „Uređivanje prostorije"                             │  │
│  │  LOT 1: Krečenje         → 2 ponude → Owner bira jednu      │  │
│  │  LOT 2: Elektroinstalac. → 1 ponuda → Owner prihvata        │  │
│  │  LOT 3: Admin/birokratija→ 3 ponude → Owner bira jednu      │  │
│  │  LOT 4: Nadzor/kontrola  → 1 ponuda → Owner prihvata        │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2. Multi-tender — Detaljno

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 MULTI-TENDER — „Uređivanje prostorije za Topli kutak"      │
│  Tip: Multi-tender (više LOT-ova)                                │
│  Status: OTVORENO │ Rok za ponude: 20. apr 2026.                │
│                                                                  │
│  ┌─── LOT 1: Krečenje i farbanje ────────────────────────────┐  │
│  │  📋 Krečenje 2 sobe (~40m²), boja po dogovoru            │  │
│  │  📍 On-premise: Zvezdara, MZ prostorija 3                │  │
│  │  💰 Budžet: 100–200€ (ili volonterski/hybrid)            │  │
│  │  ⏰ Period: 10–15. april                                  │  │
│  │                                                            │  │
│  │  Ponude (2):                                               │  │
│  │  ├── Petar D. — 120€, 2 dana — ★★★★☆ 4.2               │  │
│  │  └── Marko K. — hybrid (8h vol. + 80€) — ★★★★★ 4.8     │  │
│  │                                                            │  │
│  │  [Prihvati ponudu]  [Više detalja]                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── LOT 2: Elektroinstalacije ─────────────────────────────┐  │
│  │  📋 Pregled instalacija, zamena 3 utičnice, osvetljenje   │  │
│  │  📍 On-premise: Zvezdara                                  │  │
│  │  💰 Budžet: 80–150€                                       │  │
│  │  🎓 Zahtev: licencirani električar                        │  │
│  │                                                            │  │
│  │  Ponude (1):                                               │  │
│  │  └── Jovan S. — 100€, 1 dan — ★★★★★ 4.9                │  │
│  │                                                            │  │
│  │  [Prihvati ponudu]                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── LOT 3: Administrativno-birokratski poslovi ────────────┐  │
│  │  📋 Komunikacija sa opštinom, dozvole, dokumentacija      │  │
│  │  📍 Hybrid: opština (on-premise) + email/telefon (online) │  │
│  │  💰 Volonterski ili do 50€                                │  │
│  │                                                            │  │
│  │  Ponude (3):                                               │  │
│  │  ├── Ana M. — volonterski — ★★★★★ 4.7                   │  │
│  │  ├── Jelena P. — 30€ — ★★★★☆ 4.3                        │  │
│  │  └── Milica R. — hybrid (2h vol. + 15€/sat) — ★★★☆☆ 3.8│  │
│  │                                                            │  │
│  │  [Prihvati ponudu]                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── LOT 4: Nadzor i kontrola kvaliteta ────────────────────┐  │
│  │  📋 Praćenje svih LOT-ova, kontrola kvaliteta, primopred.│  │
│  │  📍 On-premise (periodične posete) + online (koordinacija)│  │
│  │  💰 Volonterski                                            │  │
│  │                                                            │  │
│  │  Ponude (1):                                               │  │
│  │  └── Đuka N. (Owner) — volonterski (sam preuzima)         │  │
│  │                                                            │  │
│  │  [Prihvati]                                                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  📊 SUMARNO:                                                    │
│  LOT-ova: 4 │ Ukupno ponuda: 7 │ Prihvaćeno: 0/4              │
│  Procenjeni ukupni budžet: 250–450€                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3. Single vs Multi-tender — Poređenje

| Kriterijum | Single tender | Multi-tender (⭐ za kompleksne) |
|-----------|:------------:|:-----------------------------:|
| Jednostavnost | ★★★★★ | ★★★☆☆ |
| Granularnost | ★★☆☆☆ | ★★★★★ |
| Kombinovanje vol. + plaćeno | ★★★☆☆ | ★★★★★ |
| Paralelizacija rada | ★☆☆☆☆ | ★★★★★ |
| Kontrola kvaliteta po aspektu | ★★☆☆☆ | ★★★★★ |
| Primena | Jednostavni zadaci | Kompleksni projekti |

**Preporuka:** Single tender za jednostavne zadatke (sajt, dizajn, prevod). **Multi-tender za kompleksne** (renoviranje, organizacija eventa, pokretanje prostora) — gde jedan zadatak ima više aspekata koje rade različiti ljudi.

### 8.4. Šabloni inicijativa

| Šablon | Automatski kreira |
|--------|------------------|
| Čišćenje prostora | Oglas: volonteri, Tender: transport |
| Renoviranje | **Multi-tender**: krečenje, instalacije, admin, nadzor |
| Edukativna radionica | Tender: predavač, Oglas: organizator |
| Kampanja/Peticija | Oglas: dizajner, raznosači, Tender: pravnik |
| Digitalni projekat | Tender: programer, dizajner, DevOps |
| Organizacija eventa | **Multi-tender**: lokacija, tehnika, catering, program |

---

## 11. Kalendar — Planiranje, koordinacija i vidljivost

### 9.1. Zašto je kalendar kritičan

Kalendar je **nervni sistem** svake inicijative. Bez njega:
- Volonteri ne znaju kad je akcija — dolaze na pogrešan dan
- Rokovi se propuštaju jer niko ne vidi šta kad ističe
- Koordinator ne može da organizuje ljude ako ne vidi ko je kad slobodan
- Zajednica ne vidi šta se dešava u njihovom kvartu ove nedelje
- Inicijative se preklapaju — dve akcije u istom parku iste subote

Kalendar na platformi ima **četiri nivoa vidljivosti** i služi svim akterima — od vlasnika inicijative do slučajnog posetioca sajta.

### 9.2. Četiri nivoa kalendara

```
┌─────────────────────────────────────────────────────────────────────┐
│                 ČETIRI NIVOA KALENDARA                               │
│                                                                     │
│  ┌─── NIVO 1: JAVNI KALENDAR ZAJEDNICE ────────────────────────┐  │
│  │                                                               │  │
│  │  Vidljiv svima — i neregistrovanim korisnicima.              │  │
│  │  Prikazuje SVE javne akcije, evente, i rokove kampanja       │  │
│  │  iz SVIH inicijativa u gradu/regionu.                        │  │
│  │                                                               │  │
│  │  „Šta se dešava u Beogradu ove nedelje?"                    │  │
│  │  „Gde mogu da volontiram ove subote?"                       │  │
│  │                                                               │  │
│  │  Filteri: grad, opština, kategorija, režim (on-prem/online) │  │
│  │  Integracija: embed na sajtove MZ, opštine, NVO             │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── NIVO 2: KALENDAR INICIJATIVE ────────────────────────────┐   │
│  │                                                               │  │
│  │  Sve aktivnosti jedne inicijative:                           │  │
│  │  akcije, rokovi milestones, sastanci, tender rokovi,        │  │
│  │  fundraising rokovi, eventi.                                 │  │
│  │                                                               │  │
│  │  Javni deo vide svi. Interni (sastanci tima) samo tim.      │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── NIVO 3: KALENDAR RADNE GRUPE ───────────────────────────┐   │
│  │                                                               │  │
│  │  Zadaci i sastanci specifični za radnu grupu.                │  │
│  │  Vide samo članovi RG + Owner/Admin.                        │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── NIVO 4: MOJ LIČNI KALENDAR ─────────────────────────────┐   │
│  │                                                               │  │
│  │  Agregat SVIH mojih obaveza iz svih inicijativa/RG.         │  │
│  │  „Šta ja treba da radim ove nedelje?"                       │  │
│  │  Moji zadaci, akcije na kojima učestvujem, rokovi,          │  │
│  │  sastanci, check-in obaveze.                                │  │
│  │                                                               │  │
│  │  Sync sa eksternim kalendarom (Google/Apple/Outlook).       │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.3. Tipovi događaja u kalendaru

| Tip | Ikona | Vidljivost | Lokacija obavezna? | Primer |
|-----|:-----:|:----------:|:------------------:|--------|
| **Akcija** | 🟢 | Javna | ✅ Da (📍/💻/🔀) | Čišćenje parka, sub 10–14h |
| **Event** | 🟣 | Javna | ✅ Da | Otvaranje Toplog kutka |
| **Sastanak tima** | 🔵 | Tim | ✅ Da (📍/💻) | Online meeting, uto 18h |
| **Rok (milestone)** | 🟡 | Javna | — | Rok za nabavku opreme |
| **Tender rok** | 🟡 | Javna | — | Rok za slanje ponuda |
| **Fundraising rok** | 🟡 | Javna | — | Rok kampanje za donacije |
| **Zadatak** | ⚪ | Tim/RG | Opciono | Pozvati firmu ABC |
| **Check-in** | 🟠 | Tim | ✅ Da | QR prijava na lokaciji |
| **Radionica** | 🟤 | Javna | ✅ Da (📍/💻/🔀) | IT obuka za mlade |

### 9.4. Javni kalendar zajednice — UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  📅 KALENDAR ZAJEDNICE — Beograd                                    │
│                                                                     │
│  ┌─── Filteri ─────────────────────────────────────────────────┐   │
│  │  Opština: [Sve ▾]  Kategorija: [Sve ▾]  Tip: [Sve ▾]      │   │
│  │  Režim: [📍 Fizički] [💻 Online] [🔀 Hybrid]              │   │
│  │  Prikaz: ● Mesec  ○ Nedelja  ○ Lista  ○ Mapa               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ◄ Mart 2026                  APRIL 2026                 Maj ▶     │
│                                                                     │
│  Pon    Uto    Sre    Čet    Pet    Sub         Ned                 │
│  ────── ────── ────── ────── ────── ──────────  ──────             │
│                1      2      3      4            5                  │
│                                            ┌──────────┐            │
│                                            │🟢 AKCIJA │            │
│                                            │Čišćenje  │            │
│                                            │parka     │            │
│                                            │Kalemegdan│            │
│                                            │📍 10–14h │            │
│                                            │12 vol.   │            │
│                                            └──────────┘            │
│  6      7      8      9      10     11           12                │
│                ┌──────┐                    ┌──────────┐            │
│                │🟤 RAD│             ┌──────┤🟢 AKCIJA │            │
│                │IT ob.│             │🟡 ROK│Topli kut.│            │
│                │💻 onl│             │Tender│renovir.  │            │
│                │18-20h│             │sitošt│📍 9–17h  │            │
│                └──────┘             └──────┤8 vol.    │            │
│                                            └──────────┘            │
│  13     14     15     16     17     18           19                │
│                ┌──────┐                    ┌──────────┐            │
│                │🟡 ROK│                    │🟣 EVENT  │            │
│                │Dizajn│                    │OTVARANJE │            │
│                │flaj. │                    │Topli kut.│            │
│                └──────┘                    │📍 10–18h │            │
│                                            │Zvezdara  │            │
│                                            │JAVNO     │            │
│                                            └──────────┘            │
│  20     21     22     23     24     25           26                │
│  ┌──────┐                                 ┌──────────┐            │
│  │🟤 RAD│                                 │🟢 AKCIJA │            │
│  │Pravna│                                 │Mural     │            │
│  │💻 onl│                                 │Dorćol    │            │
│  │17-19h│                                 │📍 10–16h │            │
│  └──────┘                                 │15 vol.   │            │
│                                            └──────────┘            │
│                                                                     │
│  📊 Ovaj mesec: 8 akcija │ 4 eventa │ 12 rokova │ 3 radionice     │
│  👥 Potrebno volontera: 47 │ Prijavljeno: 31 │ Fali: 16           │
│                                                                     │
│  [📱 Dodaj u moj kalendar]  [📤 iCal export]  [🗺️ Prikaži na mapi]│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.5. Prikaz događaja sa lokacijom

Svaki događaj u kalendaru jasno ističe **režim izvršenja**:

```
┌─────────────────────────────────────────────────────────────────┐
│  🟢 AKCIJA: Čišćenje parka Kalemegdan                           │
│                                                                  │
│  📅 Subota, 4. april 2026. │ ⏰ 10:00 – 14:00                  │
│                                                                  │
│  📍 ON-PREMISE                                                   │
│  ──────────────                                                  │
│  Lokacija: Park Kalemegdan, ulaz kod Despota Stefana            │
│  Adresa: Bulevar vojvode Bojovića bb, Beograd                   │
│  GPS: 44.8225° N, 20.4533° E                                    │
│                                                                  │
│  ┌───────────────────────────────────┐                           │
│  │         [INTERAKTIVNA MAPA]       │                           │
│  │                                   │                           │
│  │        📍 ← tačka okupljanja     │                           │
│  │                                   │                           │
│  │   [Google Maps ▸]  [Waze ▸]      │                           │
│  └───────────────────────────────────┘                           │
│                                                                  │
│  🚌 Kako doći:                                                   │
│  • Autobus: 31, 35 — stanica „Kalemegdan"                      │
│  • Tramvaj: 2 — stanica „Bulevar"                               │
│  • Parking: Ulica Tadeuša Košćuška (besplatan vikendom)         │
│                                                                  │
│  👥 Volonteri: 12 potrebno │ 8 prijavljeno │ fali 4             │
│  🧤 Poneti: rukavice, udobnu obuću                              │
│  ☕ Obezbeđeni: voda, kafa, sendviči za učesnike                │
│                                                                  │
│  Inicijativa: Čist park Kalemegdan                               │
│  Organizator: Marko P. (Coordinator) │ ☎ vidljiv timu          │
│                                                                  │
│  [🙋 Prijavi se]  [📅 Dodaj u kalendar]  [📢 Deli]  [📱 QR]   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  🟤 RADIONICA: IT obuka za mlade — Osnove HTML/CSS             │
│                                                                  │
│  📅 Utorak, 7. april 2026. │ ⏰ 18:00 – 20:00                  │
│                                                                  │
│  💻 ONLINE                                                      │
│  ─────────                                                       │
│  Platforma: Zoom                                                 │
│  Link: [Biće objavljen 1h pre početka]                          │
│  Potrebno: računar ili tablet, internet veza                    │
│  Znanje: nije potrebno prethodno iskustvo                       │
│                                                                  │
│  👥 Polaznici: maks 20 │ 14 prijavljeno │ slobodno 6            │
│  🎓 Predavač: Milan K. (⭐ 4.8)                                │
│                                                                  │
│  [🙋 Prijavi se]  [📅 Dodaj u kalendar]  [📢 Deli]             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  🟢 AKCIJA: Renoviranje prostorije — Dan 1 (krečenje)          │
│                                                                  │
│  📅 Subota, 11. april 2026. │ ⏰ 09:00 – 17:00                 │
│                                                                  │
│  🔀 HYBRID                                                      │
│  ──────────                                                      │
│  📍 Fizički deo: MZ Zvezdara, prostorija 3                     │
│     Adresa: Bulevar Kralja Aleksandra 73                        │
│     [Mapa ▸]                                                     │
│  💻 Online deo: Koordinacija i nabavka — Viber grupa            │
│                                                                  │
│  👥 Na lokaciji: 8 volontera │ 6 prijavljeno │ fali 2          │
│  💻 Online podrška: 2 osobe (nabavka, koordinacija)            │
│                                                                  │
│  [🙋 Prijavi se — Fizički]  [🙋 Prijavi se — Online]           │
│  [📅 Dodaj u kalendar]  [📱 QR check-in]                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.6. Lični kalendar — „Moje obaveze"

```
┌─────────────────────────────────────────────────────────────────┐
│  📅 MOJ KALENDAR — Ana Marković                                 │
│                                                                  │
│  Ova nedelja (6–12. april 2026.)                                │
│                                                                  │
│  Pon 6                                                           │
│    (ništa)                                                       │
│                                                                  │
│  Uto 7                                                           │
│    🟤 18:00 IT obuka — predavač — 💻 Online (Zoom)             │
│                                                                  │
│  Sre 8                                                           │
│    🔵 18:00 Sastanak tima „Topli kutak" — 💻 Google Meet       │
│    ⚪ Zadatak: Završiti dizajn flajera (rok: petak)              │
│                                                                  │
│  Čet 9                                                           │
│    (ništa)                                                       │
│                                                                  │
│  Pet 10                                                          │
│    🟡 ROK: Dizajn flajera (Topli kutak)                         │
│    🟡 ROK: Tender ponude za sitostampu                           │
│                                                                  │
│  Sub 11                                                          │
│    🟢 09:00–17:00 Renoviranje Topli kutak — 📍 MZ Zvezdara     │
│       [📱 QR check-in]  [🗺️ Navigacija]                        │
│                                                                  │
│  Ned 12                                                          │
│    (slobodno)                                                    │
│                                                                  │
│  ┌─── Sukobi / Upozorenja ──────────────────────────────────┐   │
│  │  ⚠️ Pet 10: Dva roka istog dana — prioritizuj!           │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [🔄 Sync sa Google Calendar]  [📥 iCal download]               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.7. Kalendar prikaz — Pristup za implementaciju

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Samo lista (agenda view)** | Hronološka lista događaja bez vizuelnog kalendara | Jednostavno, radi na mobilnom | Teško sagledati nedelju/mesec |
| **B. Kalendar grid + lista (⭐ Preporuka)** | Mesečni/nedeljni grid + agenda lista + mapa view | Vizuelno, preglednost, tri pogleda | Srednja složenost |
| **C. Full timeline (Gantt-like)** | Horizontalni timeline sa trakama za svaki zadatak | Dobro za dugotrajne projekte | Previše za tipičnu inicijativu |
| **D. Eksterni (Google Calendar embed)** | Koristi Google Calendar za sve | Zero effort, svi znaju | Nema kontrole, fragmentacija, branding |

**Preporuka: Pristup B (Kalendar grid + lista)**

**Obrazloženje:**
1. **Tri pogleda** pokrivaju sve potrebe: mesečni grid za pregled, nedeljni za detalj, lista za mobilni
2. **Mapa view** dodaje prostornu dimenziju — „Šta se dešava blizu mene ove subote?"
3. **iCal sync** omogućava da korisnici vide sve u svom postojećem kalendaru bez duplog unosa
4. **Javni kalendar zajednice** je moćan alat za vidljivost — može se embed-ovati na sajtove opština i MZ

### 9.8. Funkcije kalendara

| Funkcija | Opis |
|----------|------|
| **Prikazivanje po filterima** | Grad, opština, kategorija, tip, režim (📍/💻/🔀) |
| **Prijava na akciju** | Direktno iz kalendara — klik → „Prijavi se" |
| **Automatski podsetnici** | 24h i 2h pre akcije — push + email |
| **Konflikti** | Upozorenje kad se dva događaja preklapaju |
| **iCal/Google sync** | Dvosmerni sync sa eksternim kalendarima |
| **Embed widget** | HTML/iframe za ugradnju na eksterne sajtove |
| **QR check-in link** | Svaki fizički događaj generiše QR za prijavu dolaska |
| **Ponavljajući događaji** | „Svake subote 10–14h" — automatsko kreiranje |
| **Praćenje prisustva** | Ko se prijavio, ko je došao (QR check-in), ko nije |
| **Mapa view** | Svi događaji ove nedelje na mapi grada |
| **Kapacitet** | Maksimalan broj učesnika + waitlist |
| **Vremenska prognoza** | Za on-premise akcije: automatski prikaz prognoze za taj dan |

### 9.9. Kalendar + Lokacija — Mapa-kalendar hybrid

```
┌─────────────────────────────────────────────────────────────────────┐
│  🗺️📅 MAPA-KALENDAR — Beograd — Ova nedelja (6–12. april)         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │         🟢 Uto 7                                             │  │
│  │         IT obuka (💻 online — nema pin)                     │  │
│  │                                                              │  │
│  │                                                              │  │
│  │                    📍🟢 Sub 11                               │  │
│  │                    Renoviranje                               │  │
│  │                    Topli kutak                                │  │
│  │                    MZ Zvezdara                                │  │
│  │                    09–17h                                     │  │
│  │                    fali 2 vol.                                │  │
│  │                                                              │  │
│  │   📍🟢 Sub 11                                                │  │
│  │   Čišćenje                                                   │  │
│  │   Dorćol                         📍🟣 Ned 12                │  │
│  │   10–13h                         Humanitarni                 │  │
│  │                                  bazar                       │  │
│  │                                  Vračar 10–16h               │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Klikni na pin za detalje │ Filteri: [Volontiraj ▸] [Doniraj ▸]  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

Ovo je **najmoćniji alat za angažovanje** — korisnik otvori mapa-kalendar i u 3 sekunde vidi: „Ove subote u mom kvartu se čisti park i renovira prostorija — na kojoj akciji da učestvujem?"

---

## 12. Lokacija, online opcije i način izvršenja

### 10.1. Tri režima izvršenja

| Režim | Ikona | Opis | Primer |
|-------|:-----:|------|--------|
| **On-premise** | 📍 | Fizička lokacija, učesnik mora doći | Krečenje, čišćenje, podela flajera |
| **Online** | 💻 | Remote, učesnik radi od bilo gde | Programiranje, dizajn, online konsultacije |
| **Hybrid** | 🔀 | Kombinacija fizičkog i online | Nadzor (posete + koordinacija), PR (foto na terenu + dizajn online) |

### 10.2. Lokacija na svim nivoima platforme

| Element | Lokacija? | Opis |
|---------|:---------:|------|
| **Inicijativa** | ✅ Uvek | 📍 pin na mapi + adresa + opština + grad + GPS |
| **Tender (LOT)** | ✅ Po LOT-u | Svaki LOT može imati drugačiji režim |
| **Oglas/Pozicija** | ✅ | Jasno istaknut režim (📍/💻/🔀) |
| **Bounty** | ✅ | 📍/💻/🔀 |
| **Akcija/Event** | ✅ Obavezno | Precizna lokacija + datum + vreme + uputstvo |
| **Radna grupa** | ✅ Opciono | Remote ili lokalna |
| **Kalendar događaj** | ✅ Za fizičke | Pin na mapi + navigacija + prognoza |

### 10.3. Lokacija i matching engine

```
MATCHING FORMULA — lokacijski faktor:

  ON_PREMISE:  geo_score = max(0, 1 - dist_km / max_radius)  │ weight = 3.0
  ONLINE:      geo_score = 1.0 (svi jednaki)                  │ weight = 0.0
  HYBRID:      geo_score = max(0.3, 1 - dist_km / max_radius) │ weight = 1.0
```

### 10.4. Interaktivna mapa inicijativa

```
┌─────────────────────────────────────────────────────────────────┐
│  🗺️ MAPA INICIJATIVA — Beograd                                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │       📍 Čist park (Kalemegdan)                         │   │
│  │                     📍 Topli kutak (Zvezdara)           │   │
│  │  📍 Mural (Dorćol)                                      │   │
│  │                           📍 Rampa za školu (Voždovac)  │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Filteri: [📍 On-premise] [💻 Online] [🔀 Hybrid] [Sve]       │
│  Radius: [5km ▾]  Kategorija: [Sve ▾]  Status: [Active ▾]     │
│                                                                  │
│  💻 Online inicijative: lista ispod mape (nema pin)            │
│  🔀 Hybrid: pin na lokaciji fizičkog dela                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.5. Lokacijski detalji na inicijativi

```
┌─────────────────────────────────────────────────────────────────┐
│  📍 LOKACIJA — Topli kutak Zvezdara                             │
│                                                                  │
│  Adresa: Bulevar Kralja Aleksandra 73, Zvezdara                 │
│  GPS: 44.7934° N, 20.4744° E                                    │
│  Objekat: MZ Zvezdara, prostorija 3, prizemlje                 │
│                                                                  │
│  ┌───────────────────────────────────┐                           │
│  │         [MAPA]                    │                           │
│  │                                   │                           │
│  │        📍                         │                           │
│  │                                   │                           │
│  │  [Google Maps]  [Waze]  [Kopira] │                           │
│  └───────────────────────────────────┘                           │
│                                                                  │
│  🚌 Javni prevoz:                                                │
│  • Autobus: 31, 35 — stanica „Cvetkova pijaca" (3 min)        │
│  • Tramvaj: 7, 14 — stanica „Vukov spomenik" (7 min)          │
│  • Trolejbus: 28 — stanica „Zvezdara" (5 min)                  │
│                                                                  │
│  🅿️ Parking:                                                     │
│  • Zona 3 (40 din/sat)                                          │
│  • Besplatan vikendom                                            │
│                                                                  │
│  ♿ Pristupačnost:                                                │
│  • Ulaz bez stepenica ✅                                         │
│  • Vrata 90cm+ ✅                                                │
│  • Pristupačan toalet ✅                                         │
│  • Lift — nije potreban (prizemlje) ✅                           │
│                                                                  │
│  📸 Slike lokacije: [3 fotografije prostora]                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.6. Pristup za mape — Poređenje

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Google Maps embed** | Standardni Google Maps iframe | Poznato, besplatno do limita, Street View | API limiti, Google branding, zavisnost |
| **B. Leaflet + OpenStreetMap (⭐ Preporuka)** | Open-source mapa, custom dizajn, puni kontrol | Besplatno bez limita, customizable, offline | Manje slike satelita, nema Street View |
| **C. Mapbox** | Premium mape sa custom stilovima | Prelepe mape, 3D, dobra doku | Košta za veći traffic |

**Preporuka: Pristup B (Leaflet + OSM)** za primarnu mapu, sa opcionalnim Google Maps linkom za navigaciju.

**Obrazloženje:**
1. **Besplatno bez limita** — kritično za platformu koja nema budžet za API pozive
2. **Custom prikaz** — boja pinova po kategoriji, režimu, statusu
3. **Offline podrška** — tile caching za PWA
4. Google Maps link za navigaciju (korisniku koji klikne „Kako doći")

---

## 13. Oglasi i otvorene pozicije

### 11.1. Koncept: Oglasna tabla zajednice

Platforma ima **centralnu oglasnu tablu** — jedno mesto gde korisnik može da vidi SVE otvorene pozicije iz SVIH inicijativa. Ovo je ključno jer korisnik ne mora da pretražuje inicijativu po inicijativu — dolazi na oglasnu tablu i kaže: „Šta mogu da radim? Šta je blizu mene? Šta odgovara mojim veštinama?"

```
┌─────────────────────────────────────────────────────────────────────┐
│                   DVA POGLEDA NA OGLASE                              │
│                                                                     │
│  ┌─── POGLED 1: IZ INICIJATIVE ────────────────────────────────┐   │
│  │                                                               │  │
│  │  Korisnik gleda konkretnu inicijativu → vidi njene oglase    │  │
│  │  „Šta Topli kutak traži?"                                    │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── POGLED 2: CENTRALNA OGLASNA TABLA (⭐ ključni) ──────────┐  │
│  │                                                               │  │
│  │  Korisnik dolazi na /oglasi → vidi SVE otvorene pozicije     │  │
│  │  iz svih inicijativa, filtrirane po lokaciji, veštinama,     │  │
│  │  kompenzaciji, režimu rada...                                │  │
│  │                                                               │  │
│  │  „Tražim nešto da radim, šta ima?"                           │  │
│  │  „Koji fizički poslovi postoje u krugu od 20km?"             │  │
│  │  „Šta mogu da radim online iz Niša?"                         │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2. Struktura oglasa/pozicije

Svaki oglas sadrži:

```
┌─────────────────────────────────────────────────────────────────┐
│  💼 OGLAS                                                        │
│                                                                  │
│  Naslov:         „Raznosač flajera"                             │
│  Inicijativa:    Topli kutak Zvezdara                            │
│  Opis:           Podela 500 flajera po opštini Zvezdara         │
│                                                                  │
│  ┌─── Režim i lokacija ──────────────────────────────────────┐  │
│  │  📍 On-premise                                             │  │
│  │  Lokacija: Zvezdara, Beograd                               │  │
│  │  Adresa: centar Zvezdare (tačne rute po dogovoru)         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── Detalji ───────────────────────────────────────────────┐  │
│  │  👥 Traži se:      3 osobe                                 │  │
│  │  ⏰ Period:         5–12. april (fleksibilno)              │  │
│  │  ⏱️ Obim:           ~3h po osobi                           │  │
│  │  💰 Kompenzacija:   Volonterski + pokriveni troškovi puta │  │
│  │  📊 Složenost:      Niska                                  │  │
│  │  💪 Fizički zahtevi: Niski (hodanje)                       │  │
│  │  🎓 Zahtevane veštine: —                                   │  │
│  │  📂 Kategorija:     Fizički rad / PR                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  👤 Prijavljeno: 2/3                                             │
│  📅 Oglas objavljen: 1. april │ Aktivan do: 10. april           │
│                                                                  │
│  [📝 Prijavi se]  [📱 QR]  [📢 Deli]  [⭐ Sačuvaj]            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.3. Centralna oglasna tabla — UI sa geo-filterom

```
┌─────────────────────────────────────────────────────────────────────┐
│  💼 OGLASNA TABLA — Pronađi gde možeš da doprineseš                │
│                                                                     │
│  ┌─── LOKACIJSKI FILTER ───────────────────────────────────────┐   │
│  │                                                              │   │
│  │  Gde tražiš?                                                 │   │
│  │                                                              │   │
│  │  ○ 💻 Samo online / remote                                  │   │
│  │  ● 📍 U blizini moje lokacije                               │   │
│  │     Radius: [5km] [10km] [●20km] [50km] [100km]            │   │
│  │     📍 Zvezdara, Beograd  [🔄 Promeni] [📍 Koristi GPS]   │   │
│  │  ○ 🏙️ Konkretan grad                                       │   │
│  │     [Beograd ▾]                                              │   │
│  │  ○ 🏙️🏙️ Više gradova                                       │   │
│  │     [☑ Beograd] [☑ Novi Sad] [☐ Niš] [☐ Kragujevac]       │   │
│  │  ○ 🌍 Grad + okolina (region)                               │   │
│  │     [Beograd + 30km okolina ▾]                               │   │
│  │  ○ 🔀 Online + u blizini (oba)                              │   │
│  │  ○ 🌐 Bilo gde (sve)                                        │   │
│  │                                                              │   │
│  │  ⓘ Platforma ne čuva vašu lokaciju. Koristi se samo        │   │
│  │    za filtriranje i briše se posle sesije.                   │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── DODATNI FILTERI ────────────────────────────────────────┐    │
│  │                                                             │    │
│  │  Tip rada:                                                  │    │
│  │  [☑ Fizički rad] [☐ IT/Programiranje] [☐ Dizajn]          │    │
│  │  [☐ Pravo] [☐ Administracija] [☐ PR/Marketing]            │    │
│  │  [☐ Obrazovanje] [☐ Transport] [☐ Zanatstvo]              │    │
│  │  [☐ Sve]                                                    │    │
│  │                                                             │    │
│  │  Kompenzacija:                                              │    │
│  │  [☑ Volonterski] [☑ Plaćeni] [☑ Hybrid]                   │    │
│  │                                                             │    │
│  │  Obim:                                                      │    │
│  │  [☑ Jednokratno (<8h)] [☑ Kratkoročno (1-4 ned.)]         │    │
│  │  [☐ Dugoročno (1+ mesec)]                                  │    │
│  │                                                             │    │
│  │  Fizički zahtevi:                                           │    │
│  │  [☑ Niski] [☑ Srednji] [☐ Visoki]                         │    │
│  │                                                             │    │
│  │  Sortiraj:                                                  │    │
│  │  ● Najbliže meni  ○ Najnovije  ○ Najpopularnije           │    │
│  │  ○ Najbolje plaćeno  ○ Ističe uskoro                       │    │
│  │                                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  📊 Pronađeno: 23 oglasa u krugu od 20km (fizički rad)             │
│  🗺️ [Prikaži na mapi]  📋 [Lista]                                 │
│                                                                     │
│  ┌─── REZULTATI ──────────────────────────────────────────────┐    │
│  │                                                             │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │ 💼 Raznosač flajera                    📍 1.2 km    │  │    │
│  │  │ Topli kutak Zvezdara                                 │  │    │
│  │  │ 📍 On-premise · Zvezdara · ~3h · Volonterski        │  │    │
│  │  │ 👥 2/3 prijavljeno · 💪 Niski fiz. zahtevi          │  │    │
│  │  │ ⏰ 5–12. apr · Oglas ističe za 6 dana               │  │    │
│  │  │                                                      │  │    │
│  │  │ [📝 Prijavi se]  [📋 Detalji]  [📍 Mapa]           │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  │                                                             │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │ 💼 Pomoć pri renoviranju (krečenje)    📍 1.2 km    │  │    │
│  │  │ Topli kutak Zvezdara                                 │  │    │
│  │  │ 📍 On-premise · Zvezdara · 6h (subota) · Volonterski│  │    │
│  │  │ 👥 6/8 prijavljeno · 💪 Srednji fiz. zahtevi        │  │    │
│  │  │ ⏰ Sub 11. apr 09–17h · 📅 U kalendaru              │  │    │
│  │  │                                                      │  │    │
│  │  │ [📝 Prijavi se]  [📋 Detalji]  [📍 Mapa]           │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  │                                                             │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │ 💼 Čišćenje parka                      📍 4.8 km    │  │    │
│  │  │ Čist park Kalemegdan                                 │  │    │
│  │  │ 📍 On-premise · Kalemegdan · 4h (sub) · Volonterski │  │    │
│  │  │ 👥 8/12 prijavljeno · 💪 Srednji fiz. zahtevi       │  │    │
│  │  │ ⏰ Sub 4. apr 10–14h · ☕ Obezbeđen obrok           │  │    │
│  │  │                                                      │  │    │
│  │  │ [📝 Prijavi se]  [📋 Detalji]  [📍 Mapa]           │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  │                                                             │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │ 💼 Farbanje murala                     📍 7.3 km    │  │    │
│  │  │ Mural Dorćol                                         │  │    │
│  │  │ 📍 On-premise · Dorćol · 2 dana · Hybrid (vol+15€/h)│  │    │
│  │  │ 👥 3/5 prijavljeno · 💪 Srednji · 🎨 Potrebno iskustvo│ │   │
│  │  │                                                      │  │    │
│  │  │ [📝 Prijavi se]  [📋 Detalji]  [📍 Mapa]           │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  │                                                             │    │
│  │  ... još 19 rezultata [Učitaj više ▼]                      │    │
│  │                                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.4. Mapa prikaz oglasa

```
┌─────────────────────────────────────────────────────────────────────┐
│  🗺️💼 OGLASI NA MAPI — Fizički rad · 20km od moje lokacije         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │        💼 Čišćenje parka                                     │  │
│  │           Kalemegdan                                         │  │
│  │           4.8 km · sub 10–14h                                │  │
│  │           12 vol. potrebno                                   │  │
│  │                                                              │  │
│  │                  ⭐ (moja lokacija)                          │  │
│  │                                                              │  │
│  │                  💼💼 Topli kutak                             │  │
│  │                     Zvezdara · 1.2 km                       │  │
│  │                     2 oglasa                                 │  │
│  │                                                              │  │
│  │    💼 Mural                                                  │  │
│  │       Dorćol · 7.3 km                                       │  │
│  │                                                              │  │
│  │                            💼 Sadnja                         │  │
│  │                               Voždovac · 12 km              │  │
│  │                                                              │  │
│  │                                                              │  │
│  │  ┌─────── kliknuti pin ──────────────────────┐              │  │
│  │  │ 💼 Čišćenje parka Kalemegdan              │              │  │
│  │  │ 📍 4.8 km · Subota 10–14h                │              │  │
│  │  │ 👥 8/12 · Volonterski · ☕ Obrok          │              │  │
│  │  │ [Prijavi se]  [Detalji]  [Navigacija]     │              │  │
│  │  └───────────────────────────────────────────┘              │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ○──────────●───────────────○ Radius: 20 km                       │
│  5km       20km            50km                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.5. Geo-lokacija — Flow korisničkog iskustva

```
KORISNIK OTVARA OGLASNU TABLU
            │
            ▼
┌──────────────────────────────────────┐
│  Sistem pita:                        │
│  „Da li želiš da pronađemo oglase    │
│   blizu tebe?"                       │
│                                      │
│  [📍 Da, koristi moju lokaciju]      │
│  [🏙️ Ne, biram grad ručno]          │
│  [💻 Samo online oglase]            │
│  [🌐 Prikaži sve]                   │
└──────────────┬───────────────────────┘
               │
       ┌───────┴───────┐
       │               │
  📍 GPS           🏙️ Ručno
       │               │
       ▼               ▼
┌────────────┐  ┌──────────────────┐
│ Browser:   │  │ Izaberi:         │
│ „Sajt želi │  │ ● Grad           │
│  pristup   │  │   [Beograd ▾]    │
│  lokaciji" │  │ ○ Više gradova   │
│            │  │ ○ Region         │
│ [Dozvoli]  │  │   (grad+okolina) │
│ [Blokiraj] │  └──────────────────┘
└──────┬─────┘
       │
       ▼
┌──────────────────────────────────┐
│  Izaberi radius:                 │
│                                  │
│  [5km] [10km] [●20km] [50km]   │
│                                  │
│  📍 Zvezdara, Beograd           │
│  23 oglasa u ovom krugu          │
│                                  │
│  ⓘ Ne čuvamo vašu lokaciju.    │
│    Koristi se samo za pretragu. │
└──────────────────────────────────┘
```

### 11.6. Lokacijski filteri — Sve opcije

| Opcija | Ikona | Opis | Primena |
|--------|:-----:|------|---------|
| **Samo online** | 💻 | Prikazuje samo remote/online oglase | Korisnik iz manjeg mesta ili želi remote |
| **GPS + radius** | 📍 | Koristi lokaciju uređaja + definisan krug | Najčešće — „šta ima blizu mene" |
| **Konkretan grad** | 🏙️ | Bira jedan grad iz liste | Zna gde želi da radi |
| **Više gradova** | 🏙️🏙️ | Bira 2+ gradova | Putuje između gradova, fleksibilan |
| **Grad + okolina** | 🌍 | Grad + definisan radius | „Beograd i okolina do 30km" |
| **Online + blizina** | 🔀 | Obe opcije — online I fizički blizu | Najfleksibilniji korisnik |
| **Bilo gde** | 🌐 | Bez filtera — svi oglasi | Istraživanje, radoznalost |

### 11.7. Kategorizacija oglasa

| Kategorija | Primeri | Režim |
|------------|---------|:-----:|
| **Fizički rad** | Čišćenje, renoviranje, transport, seljenje | 📍 |
| **Zanatstvo** | Moler, električar, vodoinstalater, stolar | 📍 |
| **Transport / Vožnja** | Dostava materijala, prevoz opreme | 📍 |
| **Distribucija** | Podela flajera, postavljanje postera | 📍 |
| **IT / Programiranje** | Web razvoj, DevOps, baze podataka | 💻 |
| **Dizajn** | Grafički, UX/UI, fotografija, video | 💻/🔀 |
| **PR / Marketing** | Social media, copywriting, mediji | 💻/🔀 |
| **Pravo** | Pravni pregled, konsultacije, dokumenti | 💻/🔀 |
| **Administracija** | Birokratija, dozvole, komunikacija sa opštinom | 🔀 |
| **Obrazovanje** | Predavanja, radionice, mentorstvo | 💻/📍 |
| **Finansije** | Računovodstvo, izveštaji, revizija | 💻 |
| **Koordinacija** | Vođenje tima, organizacija akcija | 🔀 |
| **EU / Projekti** | Prijava na fondove, grant dokumentacija | 💻 |
| **Prevodilačke usluge** | Prevod dokumenata, lokalizacija | 💻 |

### 11.8. Prijava na oglas

```
┌─────────────────────────────────────────────────────────────────┐
│  📝 PRIJAVA — „Čišćenje parka Kalemegdan"                       │
│                                                                  │
│  Vaš profil:                                                     │
│  👤 Petar D. · ⭐ 4.6 · 📍 Zvezdara (4.8 km od lokacije)      │
│                                                                  │
│  Dostupnost za ovaj termin (Sub 4. apr 10–14h):                 │
│  ● Mogu ceo termin (10–14h)                                     │
│  ○ Mogu deo termina: od [__:__] do [__:__]                      │
│  ○ Ne mogu ovaj termin, ali sledećeg puta DA — obavesti me     │
│                                                                  │
│  Kako planirate da dođete?                                       │
│  ○ Pešice   ● Javni prevoz   ○ Auto   ○ Bicikl                 │
│                                                                  │
│  Imate li iskustva sa sličnim radom?                             │
│  [Čistio sam park u Nišu prošle godine, organizovao 10 vol.]   │
│                                                                  │
│  Dodatne napomene (opciono):                                     │
│  [Mogu poneti rukavice i vreće za đubre za 3 osobe]            │
│                                                                  │
│  [Pošalji prijavu]                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.9. Notifikacije i pretraga po preferencijama

Korisnik može podesiti **trajne preferencije pretrage** — sistem ga automatski obaveštava kad se pojavi novi oglas koji odgovara:

```
┌─────────────────────────────────────────────────────────────────┐
│  🔔 MOJA PODEŠAVANJA OGLASNE TABLE                              │
│                                                                  │
│  Obaveštavaj me o novim oglasima:                               │
│                                                                  │
│  Lokacija:  📍 U krugu od [20] km od Zvezdare                  │
│             + 💻 Online oglasi                                  │
│                                                                  │
│  Kategorije:                                                     │
│  [☑ Fizički rad] [☑ Dizajn] [☐ IT] [☐ Pravo]                  │
│  [☐ Sve ostalo]                                                  │
│                                                                  │
│  Kompenzacija:                                                   │
│  [☑ Volonterski] [☑ Plaćeni] [☑ Hybrid]                       │
│                                                                  │
│  Fizički zahtevi (za on-premise):                                │
│  [☑ Niski] [☑ Srednji] [☐ Visoki]                              │
│                                                                  │
│  Frekvencija obaveštenja:                                        │
│  ○ Odmah (push za svaki novi oglas)                              │
│  ● Dnevni digest (jednom dnevno, ujutru)                        │
│  ○ Nedeljni digest (ponedeljkom)                                 │
│                                                                  │
│  [Sačuvaj]                                                       │
│                                                                  │
│  Trenutni match: 5 aktivnih oglasa odgovara tvojim podešavanjima│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.10. Pristup za oglasnu tablu — Poređenje

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Samo unutar inicijative** | Oglasi vidljivi samo na stranici inicijative | Jednostavno | Korisnik mora da traži inicijativu da bi našao oglas |
| **B. Centralna tabla sa filterima (⭐ Preporuka)** | Jedno mesto, svi oglasi, geo-filter + kategorije + kompenzacija | Korisnik dolazi i odmah vidi šta ima | Srednja složenost |
| **C. AI-driven feed** | Personalizovani feed — sistem bira šta da prikaže | Minimum napora za korisnika | „Crna kutija", manje kontrole |
| **D. Job board stil (Indeed/LinkedIn)** | Puna pretraga sa keyword, lokacija, cena | Moćno, poznato | Preterano za aktivizam, hladan UX |

**Preporuka: Pristup B (Centralna tabla) + elementi C (smart preporuke na vrhu)**

**Obrazloženje:**
1. **Centralna tabla** je najvažnija — korisnik mora imati **jedno mesto** gde vidi sve
2. **Geo-filter sa GPS-om** je kritičan — najčešći use case je „šta ima blizu mene"
3. **Trajne preferencije** sa notifikacijama sprečavaju da korisnik mora svaki dan da proverava ručno
4. **Smart preporuke** (bazirane na profilu, veštinama, lokaciji, prethodnom radu) se prikazuju na vrhu — ali korisnik uvek ima punu kontrolu da filtrira sam
5. **Mapa view** je obavezan za on-premise — korisnik na mapi vidi pinove i odatle bira
6. **Privatnost lokacije** — GPS se koristi samo za filtriranje u sesiji, ne čuva se trajno. Korisnik može birati i ručni unos grada

### 11.11. Oglasna tabla u navigaciji

Oglasna tabla dobija **istaknuto mesto u glavnoj navigaciji** — nije sakrivena negde u podmeniju:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🧱 CIGLA PO CIGLA                                                     │
│                                                                         │
│  Početna   Istraži   📅 Kalendar   💼 Oglasi   Moje   Zajednica      │
│                                       ▲                                 │
│                                       │                                 │
│                              istaknuto u nav baru                       │
│                              badge sa brojem novih                      │
│                              oglasa koji matchuju                       │
│                              korisnikove preferencije                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Volonterski profili, dostupnost i matching

Korisnici proaktivno objavljuju **dostupnost, veštine, preferencije, lokaciju, i režim rada** (on-premise, online, ili oba). Matching engine koristi sve signale uključujući geo-blizinu (jak faktor za on-premise, ignorisan za online). Kad se pojavi inicijativa sa događajem u kalendaru ili novi oglas, matching engine automatski spaja aktiviste čija dostupnost se poklapa i šalje personalizovane pozive.

---

## 15. Članarine, donacije i sponzorstva

### 11.1. Zašto je ovo potrebno

Platforma sama po sebi zahteva resurse — serveri, razvoj, podrška, moderacija. Inicijative zahtevaju finansiranje. Bez održivog modela finansiranja, platforma postaje zavisna od jednog donora ili propada.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   TRI TOKA FINANSIRANJA                              │
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│   │  1. PLATFORMA│    │ 2. INICIJAT. │    │ 3. FOND      │         │
│   │              │    │              │    │  ZAJEDNICE    │         │
│   │  Članarine   │    │  Pledževi    │    │              │         │
│   │  Pro planovi │    │  Donacije    │    │  Zajednički  │         │
│   │  Platform fee│    │  Fundraising │    │  budžet za   │         │
│   │              │    │  Sponzori    │    │  hitne/male  │         │
│   │  → Održava   │    │  Grantovi    │    │  inicijative │         │
│   │    platformu │    │              │    │              │         │
│   │              │    │  → Finansira │    │  → Demokrat. │         │
│   │              │    │    konkretnu │    │    raspodela  │         │
│   │              │    │    inicijat. │    │    (glasanje) │         │
│   └──────────────┘    └──────────────┘    └──────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2. Članarine — Model za platformu

#### 11.2.1. Pristupi za članarine — Poređenje

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Potpuno besplatno** | Nema članarina, finansiranje iz grantova/donacija | Maksimalna dostupnost | Neodrživo dugoročno, zavisnost |
| **B. Freemium (⭐ Preporuka)** | Osnovno besplatno, premium za napredne funkcije | Dostupno svima, prihod od power korisnika | Treba pažljivo definisati šta je free vs premium |
| **C. Obavezna članarina** | Svi korisnici plaćaju | Predvidljiv prihod | Isključuje ljude bez sredstava, smanjuje bazu |
| **D. Pay-what-you-can** | Korisnik sam bira iznos (uključujući 0) | Inkluzivno, fer | Nepredvidljiv prihod |

**Preporuka: Pristup B (Freemium) + elementi D (pay-what-you-can za donaciju platformi)**

**Obrazloženje:**
1. **Osnovno korišćenje MORA biti besplatno** — platforma je za građanski aktivizam, ne za privilegovane
2. **Premium funkcije** su za organizacije i napredne korisnike koji imaju budžet
3. **Pay-what-you-can donacija** se opciono nudi svim korisnicima — „Podržite platformu sa koliko možete"
4. Kombinacija obezbeđuje i **dostupnost** i **održivost**

#### 11.2.2. Planska struktura

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PLANOVI PLATFORME                               │
│                                                                     │
│  ┌─── 🌱 BESPLATNO (Citizen) ────────────────────────────────────┐ │
│  │                                                                │ │
│  │  ✅ Kreiranje do 3 aktivne inicijative                        │ │
│  │  ✅ Učešće u neograničenom broju inicijativa                  │ │
│  │  ✅ Pledževi i donacije                                       │ │
│  │  ✅ Volonterski profil i matching                             │ │
│  │  ✅ Komentari, like, follow, glasanje                         │ │
│  │  ✅ Osnovni mikro-sajt (slug URL)                             │ │
│  │  ✅ Galerija (do 50 slika po inicijativi)                    │ │
│  │  ✅ 1 radna grupa po inicijativi                              │ │
│  │  ✅ Liquid Democracy delegiranje                              │ │
│  │                                                                │ │
│  │  Cena: 0 EUR                                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─── 🧱 AKTIVISTA (Pro) ───────────────────────────────────────┐  │
│  │                                                               │  │
│  │  Sve iz Citizen +                                             │  │
│  │  ✅ Neograničen broj aktivnih inicijativa                     │  │
│  │  ✅ Neograničen broj radnih grupa                             │  │
│  │  ✅ Subdomen mikro-sajt                                       │  │
│  │  ✅ Galerija (do 500 slika)                                  │  │
│  │  ✅ Kanban tabla sa naprednim filterima                       │  │
│  │  ✅ Kalendar sa iCal sync                                    │  │
│  │  ✅ Tenderi (do 5 po inicijativi)                             │  │
│  │  ✅ Napredni finansijski izveštaji (PDF export)               │  │
│  │  ✅ Prioritetni matching (profil se prikazuje prvi)           │  │
│  │  ✅ Badge „Pro aktivista" na profilu                          │  │
│  │                                                               │  │
│  │  Cena: 5 EUR/mesec ili 50 EUR/godišnje                      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🏛️ ORGANIZACIJA ─────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  Sve iz Pro +                                                 │  │
│  │  ✅ Custom domen za mikro-sajt                                │  │
│  │  ✅ Neograničena galerija                                     │  │
│  │  ✅ Organizacioni profil (NVO, firma, udruženje)              │  │
│  │  ✅ Višestruki admini sa granularnim dozvolama                │  │
│  │  ✅ Cross-inicijativne radne grupe                            │  │
│  │  ✅ API pristup                                               │  │
│  │  ✅ Sponzorski paket (logo na inicijativama)                  │  │
│  │  ✅ Prioritetna podrška                                       │  │
│  │  ✅ White-label opcija za sub-platformu                      │  │
│  │                                                               │  │
│  │  Cena: 20 EUR/mesec ili 200 EUR/godišnje                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.3. Donacije platformi

```
┌─────────────────────────────────────────────────────────────────┐
│  ❤️ PODRŽI PLATFORMU                                            │
│                                                                  │
│  „Cigla po cigla" je besplatna za sve. Ali serveri,             │
│  razvoj i moderacija koštaju. Pomozi da ostane besplatna.       │
│                                                                  │
│  Jednokratna donacija:                                           │
│  [5€]  [10€]  [25€]  [50€]  [___] EUR                         │
│                                                                  │
│  Mesečna podrška:                                                │
│  ○ ☕ 2 EUR/mesec — „Kafa za tim"                               │
│  ○ 🧱 5 EUR/mesec — „Cigla za platformu"                       │
│  ● 🏗️ 10 EUR/mesec — „Graditelj"                               │
│  ○ 🏛️ 25 EUR/mesec — „Stub zajednice"                          │
│  ○ ❤️ [___] EUR/mesec — Koliko želiš                            │
│                                                                  │
│  Svi mesečni donatori dobijaju:                                  │
│  ✅ Badge „Podržavalac platforme" na profilu                    │
│  ✅ Ime na zidu zahvalnosti                                      │
│  ✅ Mesečni newsletter sa uticajem                               │
│                                                                  │
│  [Doniraj]                                                       │
│                                                                  │
│  💰 Ovog meseca: 1.240€ od 178 donatora                        │
│  📊 Troškovi platforme: ~800€/mesec                             │
│  ✅ Pokriveno za: 1.5 mesec unapred                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.4. Sponzorstva

| Tip sponzorstva | Opis | Vidljivost | Cena (primer) |
|-----------------|------|-----------|:-------------:|
| **Sponzor inicijative** | Firma sponzoriše konkretnu inicijativu | Logo na mikro-sajtu + galeriji | Dogovor |
| **Match funding** | „Za svaki 1€ građana, mi dajemo 1€" | Banner na inicijativi | × donacija |
| **Sponzor platforme** | Godišnji sponzor cele platforme | Logo u footeru svih stranica | 500-5000€/god |
| **Sponzor kategorije** | Sponzoriše sve inicijative u kategoriji (npr. Ekologija) | Logo na kategoriji | 200-2000€/god |
| **In-kind sponzor** | Donira usluge umesto novca (hosting, pravne usluge) | Mention na zahvalnici | Vrednost usluge |

### 11.5. Platform fee — provizija

| Model | Opis | Procenat | Primena |
|-------|------|:--------:|---------|
| **Za donacije inicijativama** | Platforma uzima mali procenat od svake donacije | 3-5% | Pokriva troškove payment processing-a |
| **Za plaćeni rad** | Procenat od kompenzacija aktivistima | 5-8% | Pokriva matching, escrow, administraciju |
| **Za tender** | Procenat od vrednosti prihvaćene ponude | 3-5% | Pokriva tender infrastrukturu |
| **Volunteerski pledževi** | Besplatno | 0% | Volontiranje se ne oporezuje |

**Važno:** Procenat MORA biti transparentan i vidljiv. Korisnik pre donacije vidi: „Od vaših 50€, 47.50€ ide inicijativi, 2.50€ pokriva troškove platforme."

---

## 16. Fundraising — Prikupljanje sredstava

### 12.1. Zašto posebna sekcija za fundraising

Pledževi i preduslovi pokrivaju **osnovno prikupljanje** — ali za veće inicijative potrebno je **strateško prikupljanje sredstava** sa kampanjama, ciljevima, rokovima, i različitim modalitetima. Fundraising je aktivna, vođena akcija — ne pasivno čekanje da neko pledžuje.

### 12.2. Modaliteti prikupljanja sredstava

```
┌─────────────────────────────────────────────────────────────────────┐
│                   MODALITETI FUNDRAISINGA                            │
│                                                                     │
│  ┌─── 1. CROWDFUNDING KAMPANJA ─────────────────────────────────┐  │
│  │  Klasičan model: cilj + rok + javno prikupljanje             │  │
│  │  „Prikupimo 2000€ za Topli kutak do 30. aprila"             │  │
│  │  Progress bar, rewards/perks, urgency                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 2. REKURENTNE DONACIJE ───────────────────────────────────┐  │
│  │  Mesečne donacije za dugotrajne inicijative                   │  │
│  │  „5€/mesec za režije Toplog kutka"                           │  │
│  │  Pretplatni model — stabilan priliv                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 3. MATCH FUNDING ────────────────────────────────────────┐   │
│  │  Sponzor duplira svaku donaciju građana                      │  │
│  │  „Firma ABC: za svaki vaš 1€, mi dajemo 1€"                │  │
│  │  Psihološki efekat: donacija vredi duplo                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 4. PEER-TO-PEER FUNDRAISING ─────────────────────────────┐  │
│  │  Aktivisti kreiraju lične stranice za prikupljanje           │  │
│  │  „Ana prikuplja za Topli kutak — pomozite njenoj kampanji"  │  │
│  │  Svaki aktivista ima svoj link i progress                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 5. EVENT-BASED FUNDRAISING ──────────────────────────────┐  │
│  │  Prikupljanje na fizičkom događaju                           │  │
│  │  Bazar, koncert, prodaja ručnih radova, humanitarna večera   │  │
│  │  QR kodovi na eventu za instant donacije                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 6. GRANT PRIJAVE ────────────────────────────────────────┐  │
│  │  Pomoć pri prijavljivanju na fondove (EU IPA, lokalni)       │  │
│  │  Template dokumenta, iskustva drugih inicijativa             │  │
│  │  Baza dostupnih grantova sa rokovima                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 7. IN-KIND DONACIJE ─────────────────────────────────────┐  │
│  │  Donacija stvari umesto novca                                │  │
│  │  „Doniram tepih 2x3m" — platforma prati i vrednuje          │  │
│  │  Wishlist: inicijativa objavi šta joj treba materialno       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 8. MICRO-DONACIJE ──────────────────────────────────────┐   │
│  │  Zaokruživanje transakcija, „spare change" model             │  │
│  │  „Zaokruži na sledeći euro — razlika ide inicijativi"       │  │
│  │  Integracija sa payment apps                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.3. Crowdfunding kampanja — Detaljno

```
┌─────────────────────────────────────────────────────────────────┐
│  🎯 FUNDRAISING KAMPANJA — Topli kutak Zvezdara                 │
│                                                                  │
│  ┌─── STATUS ────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  Cilj: 2.500 EUR                                          │  │
│  │  Prikupljeno: 1.850 EUR                                   │  │
│  │  ████████████████████████████████░░░░░░░░  74%             │  │
│  │                                                            │  │
│  │  Donatori: 67 osoba │ Prosečna donacija: 27.60€           │  │
│  │  Rok: 30. april 2026. (ostalo 27 dana)                    │  │
│  │                                                            │  │
│  │  🔥 MATCH FUNDING AKTIVAN!                                │  │
│  │  Firma ABC duplira svaku donaciju do ukupno 500€          │  │
│  │  Iskorišćeno: 320€ od 500€ match fonda                   │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── DONACIJA ──────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  [5€]  [10€]  [25€]  [50€]  [100€]  [___] EUR           │  │
│  │                                                            │  │
│  │  ☑ Prikaži me javno kao donatora                          │  │
│  │  ☐ Anonimna donacija                                      │  │
│  │  ☐ Donacija u ime organizacije                            │  │
│  │                                                            │  │
│  │  ☐ Pretplati me na mesečnu donaciju: [10€/mesec]          │  │
│  │                                                            │  │
│  │  [💳 Doniraj]  [📱 QR za donaciju]  [📢 Deli kampanju]   │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── WISHLIST (in-kind) ────────────────────────────────────┐  │
│  │                                                            │  │
│  │  ☐ Tepih za igru 2x3m (~45€)                              │  │
│  │  ✅ Igračke za uzrast 2-6 — DONIRANO od Slavice M.       │  │
│  │  ☐ Grijalica 2kW (~240€)                                  │  │
│  │  ✅ Knjige za decu — DONIRANO od Biblioteke Zvezdara      │  │
│  │  ☐ Kuvalo za vodu + 6 šolja (~30€)                        │  │
│  │                                                            │  │
│  │  [Doniram nešto sa liste]                                  │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── NEDAVNI DONATORI ──────────────────────────────────────┐  │
│  │                                                            │  │
│  │  🧱 Ana S. — 30€ — pre 2h — „Svaka čast za inicijativu!" │  │
│  │  🧱 Anonimno — 50€ — pre 5h                               │  │
│  │  🧱 Firma ABC (match) — 30€ — pre 5h (match za Anu)      │  │
│  │  🧱 Marko P. — 10€/mesec (rekurentna) — pre 1d           │  │
│  │  🧱 Petar D. — 25€ — pre 2d                              │  │
│  │                                                            │  │
│  │  [Prikaži sve 67 donatora]                                 │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── STRETCH GOALS ─────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  2.500€ — Osnovno: prostor + oprema + 3 meseca režije     │  │
│  │  3.000€ — + Senzorna soba za decu sa autizmom             │  │
│  │  4.000€ — + Digitalni kutak (tablet + Wi-Fi)              │  │
│  │  5.000€ — + Drugi Topli kutak u susednoj opštini          │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 12.4. Peer-to-Peer fundraising

```
KAKO RADI P2P FUNDRAISING:

  INICIJATIVA                AKTIVISTA              AKTIVISTINA
  Topli kutak                Ana                    MREŽA
       │                       │                       │
       │  1. Ana kreira svoju  │                       │
       │  P2P stranicu za      │                       │
       │  prikupljanje         │                       │
       │◄──────────────────────│                       │
       │                       │                       │
       │                       │  2. Deli link/QR     │
       │                       │  sa svojom mrežom     │
       │                       │──────────────────────▶│
       │                       │                       │
       │                       │  3. Anini kontakti   │
       │                       │  doniraju KROZ       │
       │                       │  Aninu stranicu       │
       │◄──────────────────────│◄──────────────────────│
       │                       │                       │
       │  4. Sve donacije      │  4. Ana vidi koliko  │
       │  idu na escrow        │  je prikupila         │
       │  inicijative          │  (njen progress bar) │
       │                       │                       │

  Anina P2P stranica:
  ┌───────────────────────────────────────────────┐
  │  Ana prikuplja za Topli kutak!                │
  │                                               │
  │  Moj cilj: 200€                               │
  │  Prikupljeno: 135€  ████████████░░░░ 67%      │
  │                                               │
  │  „Pomozite mi da obezbedim topao prostor      │
  │   za decu u Zvezdari. Svaki euro se broji!"   │
  │                                               │
  │  [Doniraj kroz Aninu kampanju]                │
  └───────────────────────────────────────────────┘
```

### 12.5. Pristup za fundraising — Poređenje

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Samo pledževi** | Pledževi kao jedini način finansiranja | Jednostavno | Ograničen doseg, pasivno |
| **B. Crowdfunding kampanja** | Cilj + rok + urgency + progress | Motiviše, socijalni pritisak | Sve-ili-ništa može demotivisati |
| **C. Hybrid: kampanja + rekurentne + P2P (⭐ Preporuka)** | Svi modaliteti na raspolaganju, owner bira | Maksimalna fleksibilnost | Složenije za implementaciju |
| **D. Full platform a la GoFundMe** | Potpuno odvojena fundraising platforma | Specijalizovano | Dupla platforma, fragmentacija |

**Preporuka: Pristup C (Hybrid)**

**Obrazloženje:**
1. **Različite inicijative zahtevaju različite pristupe** — mala inicijativa treba samo pledževe, velika treba crowdfunding kampanju sa stretch goals
2. **P2P fundraising** eksponencijalno povećava doseg — umesto da samo owner deli, svaki aktivista postaje fundraiser
3. **Match funding** duplira efekat svake donacije — psihološki veoma moćno
4. **Rekurentne donacije** obezbeđuju stabilnost za dugotrajne inicijative (režije, održavanje)
5. **Wishlist** za in-kind donacije smanjuje finansijski teret — neko donira tepih umesto da inicijativa kupuje

### 12.6. All-or-nothing vs Keep-it-all

| Model | Opis | Kad koristiti | Rizik |
|-------|------|---------------|-------|
| **All-or-nothing** | Ako cilj nije dostignut, novac se vraća donatorima | Kad inicijativa NE MOŽE da se realizuje sa manje od cilja | Nizak (za donatora) |
| **Keep-it-all (⭐ Preporuka za default)** | Inicijativa zadržava koliko god da se prikupi | Kad i parcijalno finansiranje ima smisla | Srednji (šta ako je premalo?) |
| **Milestone-based** | Novac se otključava po etapama kako se milestones dostižu | Za velike, dugotrajne inicijative | Nizak (postepeno otključavanje) |

**Preporuka:** Default je **Keep-it-all** sa opcionalnim **Milestone-based** za inicijative sa budžetom > 5000€.

---

## 17. Galerija — Vizuelna dokumentacija

### 13.1. Zašto je galerija kritična

Slika vredi 1000 reči. U građanskom aktivizmu, vizuelna dokumentacija:
- **Gradi poverenje** — „Pogledajte šta smo uradili sa vašim donacijama"
- **Motiviše nove donatore** — Before/After je najjači motivator
- **Dokumentuje napredak** — hronološki vizuelni dnevnik
- **Pruža socijalni dokaz** — slike sa akcija pokazuju da se nešto zaista dešava
- **Štiti od zloupotrebe** — vizuelni dokaz da su sredstva upotrebljena kako treba

### 13.2. Tipovi galerija

```
┌─────────────────────────────────────────────────────────────────────┐
│                       TIPOVI GALERIJA                                │
│                                                                     │
│  ┌─── 📸 BEFORE / AFTER ────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  Najmoćniji format. Dva uporedna prikaza istog prostora      │  │
│  │  pre i posle inicijative.                                     │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐                          │  │
│  │  │              │  │              │                          │  │
│  │  │   BEFORE     │  │    AFTER     │                          │  │
│  │  │              │  │              │                          │  │
│  │  │  Prazna,     │  │  Topla soba  │                          │  │
│  │  │  hladna      │  │  sa decom    │                          │  │
│  │  │  prostorija  │  │  i igračkama │                          │  │
│  │  │              │  │              │                          │  │
│  │  └──────────────┘  └──────────────┘                          │  │
│  │                                                               │  │
│  │  Slider: ◄═══════════╪══════════► za interaktivno poređenje  │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 📅 HRONOLOŠKA GALERIJA ───────────────────────────────────┐  │
│  │  Slike organizovane po datumima — vizuelni dnevnik           │  │
│  │                                                               │  │
│  │  5. apr — Čišćenje prostora (8 slika)                        │  │
│  │  12. apr — Farbanje zidova (12 slika)                        │  │
│  │  18. apr — Nameštanje i oprema (6 slika)                     │  │
│  │  19. apr — OTVARANJE! (24 slike)                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🎉 EVENT GALERIJA ───────────────────────────────────────┐   │
│  │  Slike sa konkretnog događaja (akcija čišćenja, otvaranje)   │  │
│  │  Ko je učestvovao, šta se radilo, atmosfera                  │  │
│  │  Automatski tagovanje učesnika (sa dozvolom)                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 📊 PROGRESS GALERIJA ────────────────────────────────────┐  │
│  │  Slike vezane za specifične milestones                       │  │
│  │                                                               │  │
│  │  Milestone 1: Prostor obezbeđen ✅ → [3 slike]              │  │
│  │  Milestone 2: Renoviranje ✅ → [8 slika]                    │  │
│  │  Milestone 3: Oprema nabavljena ✅ → [5 slika]              │  │
│  │  Milestone 4: Otvaranje ✅ → [15 slika]                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🧾 RECEIPT GALERIJA (finansijska) ───────────────────────┐  │
│  │  Fotografije računa i potvrda o kupovini                     │  │
│  │  Vezane za transakcije u finansijskom izveštaju              │  │
│  │  Javno vidljive — transparentnost                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── 🎥 VIDEO GALERIJA ──────────────────────────────────────┐   │
│  │  Kratki snimci (do 2 min) sa akcija, intervjui, reportaže   │  │
│  │  Embed YouTube/Vimeo ili direktan upload                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.3. UI galerije na inicijativi

```
┌─────────────────────────────────────────────────────────────────┐
│  📸 GALERIJA — Topli kutak Zvezdara                             │
│                                                                  │
│  [Sve]  [Before/After]  [Hronološki]  [Po milestone]  [Računi] │
│                                                                  │
│  ┌─── 🏆 BEFORE / AFTER (pinned) ────────────────────────────┐ │
│  │                                                             │ │
│  │  ┌────────────────────────────────────────────────────┐    │ │
│  │  │  ◄════════════╪═══════════►                        │    │ │
│  │  │                                                    │    │ │
│  │  │  BEFORE ←─────┤────→ AFTER                         │    │ │
│  │  │                                                    │    │ │
│  │  └────────────────────────────────────────────────────┘    │ │
│  │  „Od prazne prostorije do Toplog kutka — 18 dana rada"    │ │
│  │  ❤️ 234  💬 45  📢 89 deljenja                            │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─── 📅 19. april — Otvaranje! (24 slike) ──────────────────┐ │
│  │                                                             │ │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐              │ │
│  │  │📷 1│ │📷 2│ │📷 3│ │📷 4│ │📷 5│ │📷 6│  +18 ▸      │ │
│  │  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘              │ │
│  │  👤 Tagovan: Đuka N., Ana M., Petar D. + 8 drugih        │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─── 📅 12. april — Farbanje (12 slika) ────────────────────┐ │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐  +6 ▸       │ │
│  │  │📷  │ │📷  │ │📷  │ │📷  │ │📷  │ │📷  │              │ │
│  │  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [📤 Dodaj slike]  [🔗 Poveži sa milestone]  [📊 Statistika]  │
│                                                                  │
│  📊 Ukupno: 55 slika │ 2 videa │ 4 before/after                │
│  👁️ Pregleda: 3.400 │ ❤️ Reakcija: 567 │ 📢 Deljenja: 234     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 13.4. Upload i moderacija slika

| Pravilo | Opis |
|---------|------|
| **Ko upload-uje** | Tim članovi (sve uloge osim Observer) |
| **Formati** | JPG, PNG, WebP, HEIC (auto-konverzija) |
| **Max veličina** | 10MB po slici (auto resize na 2048px) |
| **EXIF stripping** | Automatski se uklanjaju GPS koordinate iz metapodataka (privatnost) |
| **Lica dece** | Upozorenje: „Ova slika sadrži lica dece. Da li imate dozvolu roditelja?" |
| **Moderacija** | AI auto-detekcija neprimerenog sadržaja + community report |
| **Watermark** | Opcioni watermark sa nazivom inicijative |
| **Before/After** | Specijalan upload flow: upload BEFORE → upload AFTER → automatski slider |

### 13.5. Pristup za galeriju — Poređenje

| Pristup | Opis | Prednosti | Mane |
|---------|------|-----------|------|
| **A. Minimalan (flat lista)** | Slike u hronološkom redu bez kategorija | Jednostavno | Nepregledno za veće galerije |
| **B. Kategorisana galerija (⭐ Preporuka)** | Galerija sa tabovima (Before/After, hronološki, po milestone, računi) | Preglednost, kontekst | Srednja složenost |
| **C. Social media stil** | Feed sa slikama, komentarima, reakcijama (Instagram-like) | Engagement, poznato | Manje strukture |
| **D. Full DAM (Digital Asset Management)** | Tagovi, pretraga, verzije, rights management | Profesionalno | Previše za građanske inicijative |

**Preporuka: Pristup B (Kategorisana galerija)**

**Obrazloženje:**
1. **Before/After** je najmoćniji alat za demonstriranje uticaja — zaslužuje poseban tab
2. **Hronološki pregled** daje osećaj napretka — korisnik vidi kako se projekat razvijao
3. **Milestone galerija** povezuje vizuelne dokaze sa konkretnim koracima
4. **Receipt galerija** obezbeđuje finansijsku transparentnost
5. Ne preopterećuje korisnike koji samo žele da pregledaju slike

### 13.6. Galerija na mikro-sajtu

Galerija je **ključna sekcija mikro-sajta** — često prva stvar koju posetilac želi da vidi. Before/After slider se automatski prikazuje na hero sekciji mikro-sajta ako postoji.

---

## 18. Sistem interakcija

```
Emocionalne:      👍 Like  👎 Dislike  ❤️ Inspirisano  🔥 Hitno
Angažovanje:      🔔 Follow  ⭐ Favorite  🙋 Zainteresovan
                  🧱 Pledž  💼 Prijava za rad  📢 Share  💳 Donacija
Komunikacija:     💬 Komentar  📝 Predlog  ❓ Pitanje  📢 Update
Tender:           📋 Ponuda  🤝 Prihvatanje
Glasanje:         🗳️ Glas ZA/PROTIV  🤝 Delegacija
Evaluacija:       ⭐ Rating  📋 Report
```

---

## 19. Bounty koncept

Specifičan, jasno definisan zadatak sa fiksnim uslovima — volonterski ili plaćen.

---

## 20. Rating sistem — Sveobuhvatno ocenjivanje

### 16.1. Četiri dimenzije ratinga

| Dimenzija | Ko ocenjuje | Kriterijumi |
|-----------|-------------|-------------|
| **Rating aktiviste** | Owner, Coordinator, Reviewer | Kvalitet, rokovi, komunikacija, profesionalnost, proaktivnost, pouzdanost (1-5) |
| **Rating inicijative** | Aktivisti, pledžeri, učesnici | Organizacija, transparentnost, komunikacija, fer kompenzacija, uticaj (1-5) |
| **Rating saradnje** | Oba učesnika (owner ↔ aktivista) | Ukupno zadovoljstvo, ponovo bih sarađivao, preporuka |
| **Community rating** | Šira zajednica | Like/Dislike + komentar |

### 16.2. Multi-dimenzionalni scorecard + reputation-weighted (⭐ Preporuka)

Anti-manipulacija: samo verifikovani učesnici, cooling period (24-72h), outlier detekcija, reputation weight, pravo na odgovor, medijan umesto proseka.

---

## 21. Monitoring i evaluacija dugotrajnih inicijativa

Health dashboard sa progress barovima (milestones, budžet, vreme), alarm sistemom (neaktivan aktivista, milestone kasni, budžet prekoračen), i timesheet sistemom.

---

## 22. Finansijska transparentnost

Javni finansijski dashboard za svaku inicijativu. Svaki rashod sa priloženim računom. Dual approval za isplate > 200€. Mesečni automatski izveštaji. Whistleblower kanal. Galerija računa (sekcija 13 — Receipt galerija) obezbeđuje vizuelni dokaz.

---

## 23. Graf baza — Veze, preporuke, mreža aktivista

### 22.1. Čvorovi i veze

**Čvorovi:** User, Initiative, Skill, Category, Tender, Position, Bounty

**Ključne veze:** POZNAJE, PREPORUČUJE, RADIO_SA, UČESTVUJE, POSEDUJE (skill), ZAHTEVA, PRATI, PLEDŽ, LIKE, DELEGIRA_GLAS

### 22.2. Poređenje graf baza

| Kriterijum | Neo4j | Dgraph | TigerGraph | Apache AGE (PG ext.) | ArangoDB |
|-----------|:-----:|:------:|:----------:|:-------------------:|:--------:|
| **Tip** | Native graf | Native graf (GraphQL) | Native graf (MPP) | PG extension | Multi-model |
| **Query jezik** | Cypher | GraphQL± / DQL | GSQL | openCypher | AQL |
| **Performanse traversal** | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★★☆ | ★★★★☆ |
| **Horizontalno skaliranje** | ★★★☆☆ (Enterprise) | ★★★★★ | ★★★★★ | ★★☆☆☆ (PG limit) | ★★★★☆ |
| **Lakost učenja** | ★★★★★ (Cypher intuitivan) | ★★★★☆ (GraphQL poznat) | ★★★☆☆ (GSQL specifičan) | ★★★★☆ (Cypher) | ★★★☆☆ |
| **Community / Ekosistem** | ★★★★★ (najveći) | ★★★☆☆ | ★★★☆☆ | ★★☆☆☆ (mlad) | ★★★☆☆ |
| **Vizuelizacija** | ★★★★★ (Neo4j Browser, Bloom) | ★★★☆☆ (Ratel) | ★★★★☆ (GraphStudio) | ★★☆☆☆ | ★★★☆☆ |
| **Licenca** | Community: GPLv3, Enterprise: komercijalna | Apache 2.0 | Freemium (Enterprise) | Apache 2.0 | Apache 2.0 |
| **Cena (self-hosted)** | Besplatno (Community) | Besplatno | Besplatno (Community) | Besplatno | Besplatno |
| **Managed cloud** | Aura (od $65/mes) | Dgraph Cloud ($) | TigerGraph Cloud ($$$) | — | ArangoDB Oasis ($) |
| **Real-time analytics** | ★★★☆☆ | ★★★★☆ | ★★★★★ | ★★☆☆☆ | ★★★☆☆ |
| **Full-text search** | Ugradjen (Lucene) | Ugradjen | Ugradjen | PG tsvector | Ugradjen |
| **Pogodnost za preporuke** | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| **Operativna složenost** | ★★★★☆ (dobra doku) | ★★★☆☆ (manje doku) | ★★★☆☆ (složeniji setup) | ★★★★★ (samo PG ext.) | ★★★☆☆ |
| **Zrelost** | Od 2007. (najzreliji) | Od 2017. | Od 2012. | Od 2020. (najmlađi) | Od 2011. |

### 22.3. Detaljne karakteristike

#### Neo4j
- **Prednosti:** Najveći ekosistem, Cypher je najintuitivniji graf query jezik, odlična vizuelizacija (Browser, Bloom), ogromna zajednica i dokumentacija, GDS (Graph Data Science) biblioteka sa 60+ algoritama (PageRank, community detection, shortest path), APOC proceduralna biblioteka
- **Mane:** Horizontalno skaliranje samo u Enterprise ($$$), single-server Community edition, heavy na memoriji za velike grafove
- **Za platformu:** Idealan za naš use case — socijalni graf, preporuke, matching. Community edition pokriva početne potrebe

#### Dgraph
- **Prednosti:** Native GraphQL podrška (nije wrapper), horizontalno skalabilan od starta, Apache 2.0 licenca, Badger key-value store (brz), dobar za real-time upite
- **Mane:** Manji ekosistem nego Neo4j, manje vizuelnih alata, GraphQL± specifičan (nije standard Cypher), manje third-party integracija, kompanija imala turbulentnu istoriju
- **Za platformu:** Dobar izbor ako tim zna GraphQL i treba skaliranje od starta

#### TigerGraph
- **Prednosti:** Najbrži za deep-link analytics (10+ hops), MPP (massively parallel processing), GSQL je moćan za kompleksne analitičke upite, odličan za real-time graph analytics, GraphStudio vizuelni alat
- **Mane:** GSQL je specifičan jezik (learning curve), Community edition ograničena, komercijalno fokusiran, manje open-source prijateljski
- **Za platformu:** Overengineered za naš use case — osmišljen za enterprise analytics na grafovima sa milijardama čvorova

#### Apache AGE
- **Prednosti:** Extension za PostgreSQL — jedan sistem za sve, openCypher kompatibilan, nema novog servisa za maintenance, besplatno
- **Mane:** Najmlađe rešenje (2020), manja zajednica, performanse ograničene PostgreSQL-om za duboke traversale, manje GDS algoritama
- **Za platformu:** Najjednostavnija integracija jer već koristimo PostgreSQL. Dobro za MVP ali potencijalno nedovoljno za napredni matching

#### ArangoDB
- **Prednosti:** Multi-model (dokument + graf + key-value u jednom), AQL je fleksibilan, ArangoSearch za full-text, horizontal sharding, dobra za polyglot use case
- **Mane:** Jack-of-all-trades — ni u čemu nije best-in-class, manji graf ekosistem nego Neo4j, manje specijalizovan za graf algoritme
- **Za platformu:** Zanimljiv ako želimo da konsolidujemo baze, ali za čist graf use case Neo4j je bolji

### 22.4. Preporuka: Dvofazni pristup

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  FAZA 1 (MVP): Apache AGE (PostgreSQL extension)                │
│  ─────────────────────────────────────────────                   │
│  Zašto: Nema novog servisa. PostgreSQL je već tu.               │
│  Cypher upiti rade direktno u PG.                               │
│  Pokriva: osnovno praćenje veza, jednostavne preporuke.         │
│                                                                  │
│            │                                                     │
│            ▼  Kad AGE postane bottleneck (> 100K korisnika)     │
│                                                                  │
│  FAZA 2 (Scale): Neo4j Community Edition (⭐ Preporuka)         │
│  ─────────────────────────────────────────────                   │
│  Zašto: Najzreliji, Cypher (kompatibilan sa AGE upitima),      │
│  GDS biblioteka za napredni matching, odlična vizuelizacija,   │
│  najveća zajednica za podršku i hiring.                         │
│                                                                  │
│  PostgreSQL ostaje primary za CRUD.                             │
│  Neo4j čuva SAMO veze. Sync kroz RabbitMQ evente.              │
│                                                                  │
│            │                                                     │
│            ▼  Ako bude > 10M korisnika (malo verovatno skoro)  │
│                                                                  │
│  FAZA 3 (Enterprise): Neo4j Enterprise ili Dgraph               │
│  Za horizontalno skaliranje.                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Obrazloženje preporuke:**
1. **AGE za MVP** — zero overhead, nema novog servisa, tim uči Cypher koji je kompatibilan sa Neo4j
2. **Neo4j za Scale** — migracija je glatka jer AGE i Neo4j oba koriste Cypher, a Neo4j donosi GDS algoritme za napredni matching, community detection, i PageRank za reputaciju
3. **Dgraph ili TigerGraph** se razmatraju samo ako platforma dostigne milione korisnika — što je unlikely u prvih par godina

---

## 24. Mikro-sajt inicijative i custom domeni

### 20.1. Slojevit pristup (⭐ Preporuka)

| Nivo | URL | Trošak | Plan |
|------|-----|--------|------|
| A. Slug | `ciglaporika.rs/i/topli-kutak` | Besplatno | Citizen |
| B. Subdomen | `topli-kutak.ciglaporika.rs` | Besplatno | Pro |
| C. Custom domen | `toplikutak.rs` | ~10€/god | Organizacija |

### 20.2. Sekcije mikro-sajta

O inicijativi │ Tim │ Napredak │ Finansije │ **Galerija** │ Blog │ Donacija │ FAQ

Galerija sa Before/After sliderom se automatski prikazuje na hero sekciji.

---

## 25. Početna strana — UX arhitektura

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🧱 CIGLA PO CIGLA              🔍 Pretraži...     [🔔] [👤 Profil]  │
│  Početna  Istraži  Moje  Pledževi  Zajednica  💼 Banka aktivista     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─── 🔥 HERO — Na ivici uspeha + Before/After slider ─────────────┐  │
│  │  „Topli kutak — Voždovac"  ████████████████████░░ 92%           │  │
│  │  [Before ◄═══╪═══▶ After]  Fali: 65€ + 1 vol.  [🧱 Cigla]     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── 🔥 VRUĆE INICIJATIVE ────────────────────────────────────────┐  │
│  │  [Čist park +47] [Rampa +32] [IT obuka +28] [Mural +21]        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── 🎯 AKTIVNE KAMPANJE (fundraising) ───────────────────────────┐  │
│  │  💳 Topli kutak: 1850/2500€ (74%) — match funding aktivan!     │  │
│  │  💳 Čist park: 320/800€ (40%) — rok: 15 dana                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── 💼 TRAŽE SE AKTIVISTI ───────────────────────────────────────┐  │
│  │  🎯 Programer — IT obuka — 25€/sat                              │  │
│  │  📋 TENDER: Sitostampa — Topli kutak — ponude do 20.apr        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── 🏆 REALIZOVANE (Before/After galerija) ──────────────────────┐  │
│  │  [📸 ◄═╪═▶ Park] [📸 ◄═╪═▶ Rampa] [📸 ◄═╪═▶ Topli kutak #1] │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── 📊 STATISTIKA ──────────────────────────────────────────────┐  │
│  │  🧱 12.450 cigli │ ✅ 87 realizovano │ 💰 45.600€ prikupljeno │  │
│  │  👥 3.200 aktivnih │ 📸 12.300 slika u galerijama              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 26. Liquid Democracy — Delegiranje glasa

### 22.1. Hibridni model sa prioritetima (⭐ Preporuka)

```
Prioritet 1:  KONKRETNA INICIJATIVA → delegiraj Jeleni
Prioritet 2:  KATEGORIJA / DOMEN → delegiraj Ani za ekologiju
Prioritet 3:  GEOGRAFSKA OBLAST → delegiraj Petru za Zvezdaru
Prioritet 4:  GLOBALNI DELEGAT → delegiraj Milanu za sve ostalo
Prioritet 5:  LIČNI GLAS (default)
```

Bezbednost: nema tranzitivnosti, instant revoke, max glasova po delegatu, cooling period, notifikacija pre glasanja.

---

## 27. Profili korisnika i reputacija

### 23.1. Profil sa svim tokovima

```
┌─────────────────────────────────────────────────────────────────┐
│  👤 Ana Marković · Zvezdara · Članica od mart 2026.            │
│  ⭐ Rating: 4.72/5.0 (14 eval.) · Plan: 🧱 Pro Aktivista     │
│                                                                  │
│  Dao/la:  💰 320€ priloženo │ ⏰ 24h volonterski (720€ vred.) │
│  Primio:  💼 1.200€ zarađeno │ 60h plaćenog rada               │
│                                                                  │
│  Veštine: 🎨 Dizajn (30€/sat) │ 📸 Foto (25€/sat)            │
│  Mreža:   34 kontakata │ 12 preporuka │ 8 saradnji             │
│  Galerija: 45 slika uploadovano │ 3 before/after               │
│  Reputacija: 480 bodova · 🏗️ Aktivista                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 23.2. Reputacioni bodovi

| Akcija | Bodovi |
|--------|:------:|
| Ispunjen pledž (novčani) | +10 |
| Ispunjen pledž (vreme/rad) | +15 |
| Ispunjen pledž (stručna usluga) | +20 |
| Kreirana inicijativa (uspešna) | +50 |
| Bounty ispunjen | +25 |
| Evaluacija ≥ 4.5 | +15 |
| Evaluacija < 3.0 | -20 |
| Neispunjen pledž | -30 |
| Upload galerije sa before/after | +10 |
| P2P fundraising > 100€ prikupljeno | +15 |
| Rekurentna donacija (6+ meseci) | +20 |
| Tender ponuda prihvaćena i ispunjena | +20 |
| Preporuka aktiviste (potvrđena) | +10 |
| Prijava za zloupotrebu (potvrđena) | -100 |

### 23.3. Nivoi

```
  0–50      🌱 Novi član
  51–150    🧱 Graditelj
  151–300   🏗️ Aktivista
  301–500   🏛️ Lider zajednice
  501+      ⭐ Ambasador
```

---

## 28. Notifikacije i komunikacija

| Tip | Kanal |
|-----|-------|
| Pledž / Donacija | Push + email |
| Milestone dostignut | Push + email |
| Preduslovi 100% | Push + email + SMS |
| Invite (tim/ownership) | Push + email |
| QR skeniranje | Push |
| Tender ponuda | Push + email |
| Oglas prijava | Push + email |
| Matching | Push + email |
| Evaluacija | Push + email |
| Isplata | Push + email + SMS |
| Fundraising: cilj dostignut | Push + email + SMS |
| Fundraising: match activated | Push + email |
| Nova slika u galeriji | Push |
| Zadatak dodeljen (kanban) | Push |
| Chat poruka u RG | Push |
| Alarm (neaktivnost) | Push + email |

---

## 29. Primer: „Topli kutak" kao prva inicijativa

```
┌─────────────────────────────────────────────────────────────────┐
│  🤝 SOCIJALNA ZAŠTITA                       📍 Zvezdara, BG    │
│  Topli kutak — Opština Zvezdara                                 │
│  Owner: Đuka N. (proxy: Dragan M.) │ Tim: 12 │ Rating: ★★★★★  │
│                                                                  │
│  ┌─── RADNE GRUPE ───────────────────────────────────────────┐  │
│  │  👥 Logistika (3 čl.) — Marko P.                          │  │
│  │  👥 Dizajn (2 čl.) — Ana M.                               │  │
│  │  👥 PR (2 čl.) — Jelena S.                                │  │
│  │  👥 Fundraising (2 čl.) — Petar D.                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── FUNDRAISING KAMPANJA ──────────────────────────────────┐  │
│  │  🎯 Cilj: 2.500€ │ Prikupljeno: 1.850€ │ 74%            │  │
│  │  🔥 Match funding: Firma ABC (+320€)                      │  │
│  │  📅 Rok: 30. apr │ 67 donatora                            │  │
│  │  [💳 Doniraj]  [📱 QR]                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── GALERIJA ──────────────────────────────────────────────┐  │
│  │  📸 Before/After: [◄═══╪═══▶] 234 ❤️                     │  │
│  │  📅 55 slika │ 2 videa │ 4 milestone galerije             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── WISHLIST ──────────────────────────────────────────────┐  │
│  │  ☐ Grijalica 2kW (~240€)  ✅ Igračke  ✅ Knjige          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── FINANSIJE (javno) ─────────────────────────────────────┐  │
│  │  Prikupljeno: 2.850€ │ Potrošeno: 1.620€ │ Ostaje: 1.230€│  │
│  │  Doniran rad: 1.840€ (tržišna vred.)                      │  │
│  │  📸 12 računa u Receipt galeriji                           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 30. Tehnička arhitektura — pregled

### 26.1. Stack

| Sloj | Tehnologija |
|------|-------------|
| Frontend | Vue 3 + Nuxt 3 (SSR/SPA) |
| UI | Vuetify ili Quasar |
| Backend | Java 21+ / Spring Boot 3 |
| AI servis | FastAPI / Python (matching, NLP, moderacija slika) |
| Primary DB | PostgreSQL + pgvector |
| Graf DB | Neo4j (veze, preporuke, matching) |
| Search | Meilisearch |
| Cache | Redis |
| Messaging | RabbitMQ |
| Payment | Stripe Connect (escrow, payouts, subscriptions, donations) |
| Files/Images | S3 / MinIO (galerija, dokumenti, receipts) |
| Image processing | Sharp / libvips (resize, watermark, EXIF strip) |
| Real-time | WebSocket (STOMP) — chat, kanban updates |
| Mobile | PWA |
| Reverse proxy | Caddy (auto SSL, custom domeni) |
| QR | Server-side QR (zxing / qrcode.js) |

### 26.2. Arhitektura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KLIJENTI                                    │
│  [Web/Nuxt]  [PWA]  [Custom domeni]  [Admin]  [QR Scanner]        │
│                         │                                           │
│                    [Caddy proxy]  ← Auto SSL + custom domains      │
│                         │                                           │
│    ┌────────────────────┼────────────────────┐                      │
│    ▼                    ▼                    ▼                      │
│ ┌──────────┐     ┌──────────┐         ┌──────────┐                │
│ │ Spring   │     │ FastAPI  │         │ Notif.   │                │
│ │ Boot API │     │ (AI)     │         │ Servis   │                │
│ │          │     │          │         │          │                │
│ │Inicijat. │     │Matching  │         │Push/Email│                │
│ │Tender    │     │NLP       │         │SMS/Chat  │                │
│ │Fundrais. │     │Image mod.│         │WebSocket │                │
│ │Rating    │     │Preporuke │         │          │                │
│ │Galerija  │     │          │         │          │                │
│ │Članarine │     │          │         │          │                │
│ │QR gen.   │     │          │         │          │                │
│ └────┬─────┘     └────┬─────┘         └────┬─────┘                │
│      └────────────────┼────────────────────┘                       │
│                       │                                             │
│  ┌────────────────────┼──────────────────────────┐                  │
│  ▼         ▼          ▼           ▼              ▼                  │
│ ┌──────┐┌──────┐ ┌──────┐  ┌──────────┐  ┌──────────┐             │
│ │Postgr││Redis │ │Meili │  │ RabbitMQ │  │  Neo4j   │             │
│ │  SQL ││      │ │search│  │ (events) │  │ (graf)   │             │
│ └──────┘└──────┘ └──────┘  └──────────┘  └──────────┘             │
│    │                                           ▲                    │
│    │              event sync                   │                    │
│    └───────────────────────────────────────────┘                    │
│                                                                     │
│ ┌──────────┐  ┌──────────────┐  ┌──────────┐                      │
│ │  Stripe  │  │ S3/MinIO     │  │Prometheus│                      │
│ │ Connect  │  │ (Images/     │  │+ Grafana │                      │
│ │(payments,│  │  Files/      │  │          │                      │
│ │ subs,    │  │  Receipts)   │  │          │                      │
│ │ donations│  │              │  │          │                      │
│ └──────────┘  └──────────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 31. Bezbednost, moderacija i zloupotrebe

| Zloupotreba | Rizik | Zaštita |
|-------------|:-----:|---------|
| Lažni pledževi | Visok | Escrow + verifikacija + reputacija |
| Lažni timesheet | Visok | Dual verifikacija |
| Fake evaluacije | Srednji | Samo verifikovani + reputation weight |
| Fraudulentna kampanja | Visok | KYC za kampanje > 1000€, moderacija, milestone-based release |
| Zloupotreba donacija | Visok | Escrow, receipt galerija, community audit |
| Neprimerene slike | Srednji | AI moderacija + community report |
| Lica dece bez dozvole | Srednji | AI face detection + obavezna potvrda |
| Tender manipulacija | Srednji | Anonimne ponude do roka |
| Spam QR | Nizak | Rate limiting + expiration |
| Spam članarine (pranje) | Nizak | KYC za > 500€ |

**Moderacija:** Nivo 1: AI → Nivo 2: Community (500+ rep.) → Nivo 3: Admin tim

---

## 32. Faze razvoja

### 28.1. MVP (Faza 1) — 3-4 meseca

| Funkcionalnost | P |
|----------------|:-:|
| Registracija / Login | P0 |
| Kreiranje inicijative (state management) | P0 |
| Proxy kreiranje i ownership transfer | P0 |
| Tim sa osnovnim rolama (Owner, Admin, Activist, Observer) | P0 |
| Preduslovi i pledževi | P0 |
| Like / Follow / Favorite / Zainteresovan | P0 |
| Komentari (flat) | P0 |
| Home strana (Hot / Blizu cilja / Nove) | P0 |
| Profil korisnika | P0 |
| Mikro-sajt — slug URL | P0 |
| QR kodovi (invite + pledž + donacija) | P0 |
| Oglasi/Pozicije (osnovno) | P0 |
| Galerija (osnovna — hronološka + before/after) | P0 |
| Donacije inicijativama (jednokratne) | P0 |
| Email notifikacije | P0 |
| i18n: SR-Cyrl + EN | P0 |

### 28.2. Faza 2 — 2-3 meseca

| Funkcionalnost | P |
|----------------|:-:|
| Plaćeni aktivizam — tiered pricing | P1 |
| Timesheet sistem | P1 |
| Tender model + ponude | P1 |
| Escrow (Stripe Connect) | P1 |
| Finansijski dashboard (javni) | P1 |
| Receipt galerija (računi) | P1 |
| Rating sistem (multi-dimenzionalni scorecard) | P1 |
| Bounty sistem | P1 |
| Sve uloge u timu | P1 |
| Radne grupe (osnovno — kanban + chat) | P1 |
| Crowdfunding kampanje (cilj + rok + progress) | P1 |
| Rekurentne donacije | P1 |
| Threadovani komentari sa kategorijama | P1 |
| Push notifikacije (PWA) | P1 |
| Pretraga sa filterima (Meilisearch) | P1 |
| Admin panel | P1 |

### 28.3. Faza 3 — 2-3 meseca

| Funkcionalnost | P |
|----------------|:-:|
| Volonterski profili + dostupnost | P2 |
| Matching engine (AI semantic) | P2 |
| Neo4j graf baza — veze, preporuke | P2 |
| Članarine (Freemium model — Citizen/Pro/Org) | P2 |
| Platform fee (provizija na donacije/plaćeni rad) | P2 |
| P2P Fundraising (lične stranice za prikupljanje) | P2 |
| Match funding | P2 |
| Wishlist (in-kind donacije) | P2 |
| Stretch goals | P2 |
| Cross-inicijativne radne grupe | P2 |
| Kalendar aktivnosti sa iCal sync | P2 |
| Progress galerija (vezana za milestones) | P2 |
| Video galerija | P2 |
| Monitoring dashboard za dugotrajne inicijative | P2 |
| Subdomen za mikro-sajt | P2 |
| Custom domen podrška (Caddy) | P2 |
| Liquid Democracy — hibridni model | P2 |
| Šabloni inicijativa (templates) | P2 |
| Sponzorski paketi | P2 |

### 28.4. Faza 4 — kontinualno

| Funkcionalnost | P |
|----------------|:-:|
| Donacija platformi (pay-what-you-can) | P3 |
| Organizacioni profili (NVO, firme) | P3 |
| White-label / sub-platforme | P3 |
| Grant baza (dostupni fondovi sa rokovima) | P3 |
| Milestone-based fund release | P3 |
| Micro-donacije (zaokruživanje) | P3 |
| AI moderacija slika (lica dece, neprimeren sadržaj) | P3 |
| Periodični finansijski izveštaji (PDF) | P3 |
| Geo-mapa inicijativa | P3 |
| Fork inicijative | P3 |
| QR event check-in | P3 |
| API za eksterne integracije | P3 |
| Gamifikacija (badge-evi) | P3 |
| Multi-tenant | P3 |
| Mobile app (Flutter) | P3 |

---

## 33. Zaključak

Platforma „Cigla po cigla" je **kompletna infrastruktura za građanski aktivizam** koja:

1. **Demokratizuje inicijativu** — svako može predložiti, svako može doprineti
2. **Organizuje rad** — radne grupe, kanban, kalendar, chat — sve na jednom mestu
3. **Fer kompenzuje** — tiered model, tender, oglasi — aktivisti daju i primaju
4. **Prikuplja sredstva** — crowdfunding, P2P, match funding, rekurentne donacije, wishlist
5. **Dokumentuje vizuelno** — galerija, before/after, progress, receipt — svaka slika priča priču
6. **Gradi poverenje** — transparentne finansije, rating, evaluacije, escrow, receipt galerija
7. **Inteligentno matchuje** — graf baza + AI = pravi ljudi na pravom mestu
8. **Održiva je** — freemium članarine, platform fee, sponzorstva, donacije platformi
9. **Skalira** — QR kodovi, šabloni, mikro-sajtovi, fork inicijativa

```
   Milion cigli leži razbacano po zemlji.
   Neke su besplatne. Neke koštaju. Sve su vredne.

   Platforma ih organizuje u radne grupe,
   fundraising kampanja im daje gorivo,
   galerija dokumentuje svaku ugrađenu ciglu,
   a članarine i donacije obezbeđuju
   da gradilište nikada ne zatvori kapiju.

   Počnimo da gradimo.
```

---

*Dokument pripremljen kao polazna osnova za elaboraciju platforme za građanski aktivizam. April 2026.*
*Referentna inicijativa: `djuka-prostor-deca-opstine/docs/elaboracija-inicijativa.md` — „Topli kutak"*
