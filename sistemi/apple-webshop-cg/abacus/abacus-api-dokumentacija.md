# Abacus® API

> **Verzija dokumenta:** 03.2025.
> **Klijent:** KLIJENT
> **Token:** TOKEN

---

## Opšti podaci

Upit uvjek vrati JSON serijalizovan objekat sa 3 property-a:

- **Data** - sadrži suštinu odziva. Uglavnom, to će biti lista objekata u zavisnosti od upita, takođe JSON.
- **Version** - nije veoma bitno u ovom trenutku
- **Error** - ako nije bilo grešaka prilikom izvršenja, ovaj property će biti `null`, u suprotnom biće neki opis problema.

**URL struktura:**

```
http://{server}/{klijent}/{modul}/{funkcija}?token={token}&protocol={verzija}
```

- Server
- Klijent
- Modul
- Funkcija koja se poziva
- Token
- Verzija API protokola

---

## 1. GetPartners

Primjer upita koji će vratiti listu partnera:

```
GET http://api.bencomltd.com/APITest/Main/GetPartners?token=12345678&protocol=2.0
```

Ovaj upit vratiće listu objekata sledećeg tipa:

```json
{
  "id_partner": int,       // ID partnera, identity column
  "code": "string",        // šifra partnera, ako postoji
  "name": "string",        // Naziv partnera
  "tax_id": "string",      // poreski ID broj partnera
  "phone": "string",       // tel broj partnera
  "address": "string",     // adresa partnera
  "city": "string",        // grad partnera
  "country": "string",     // drzava partnera
  "zip_code": "string",    // post. br. partnera
  "email": "string",       // email partnera
  "first_name": "string",  // ime partnera
  "last_name": "string"    // prezime partnera
}
```

---

## 2. getWorkUnits

Funkcija `getWorkUnits` koja će vratiti listu svih radnih jedinica iz baze podataka klijenta.

```
GET http://api.bencomltd.com/APITest/Main/getWorkUnits?token=12345678&protocol=2.0
```

Objekat:

```json
{
  "id": int,          // ID radne jedinice, identity column
  "name": "string",   // naziv radne jedinice
  "code": "string"    // kod radne jedinice
}
```

ID radne jedinice se može dalje koristiti u funkcijama `getItems` i `postSale`.

---

## 3. getPriceLists

Funkcija `getPriceLists` koja će vratiti listu svih cijenovnika iz baze podataka klijenta.

```
GET http://api.bencomltd.com/APITest/Main/getPriceLists?token=12345678&protocol=2.0
```

Objekat:

```json
{
  "id": int,         // ID cijenovnika, identity column
  "name": "string"   // naziv cijenovnika
}
```

---

## 4. getItems

Funkcija **getItems** koja će vratiti listu svih artikala iz baze podataka klijenta, stanje na lageru, cijene itd.

```
GET http://api.bencomltd.com/APITest/Main/getItems?token=12345678&protocol=2.0
```

Objekat:

```json
{
  "id_item": int,                // ID artikla, identity column
  "code": "string",              // šifra artikla
  "name": "string",              // naziv artikla
  "ean": "string",               // ean artikla
  "group": "string",             // naziv grupe kojoj artikal pripada
  "supplier_code": "string",     // šifra dobavljača
  "manufacturer": "string",      // naziv proizvođača
  "price": decimal,              // cijena *
  "price_rrp": decimal,          // maloprodajna cijena
  "discount": decimal,           // popust (procentualni)
  "image": ["string"],           // slika/e artikla
  "description": "string",       // opis artikla
  "quantity": decimal,            // količina na lageru, u trenutku upita
  "details": [                    // detalji artikla **
    {
      "type": "string",
      "value": "string"
    }
  ]
}
```

\* Cijena artikla u osnovnom cijenovniku.

\*\* Ovaj property je, ako detalji postoje, lista objekata sa 2 property-a: `type` i `value`. Npr:

```json
[
  { "type": "boja", "value": "plava" },
  { "type": "velicina", "value": "XL" }
]
```

### Opcioni parametri

Funkcija `getItems` se može pozvati sa **4 opciona parametra** (šalju se kao JSON u body-u):

| Parametar | Tip | Opis |
|-----------|-----|------|
| `ids` | `int[]` | Niz UID artikala — ako je prisutan, odgovor će sadržati samo te artikle |
| `id_partner` | `int` | UID partnera (iz `GetPartners`). Cijene i popusti će biti proračunati za datog partnera (na nivou artikla, grupe artikla, partnera, dodatnog cijenovnika itd.) |
| `id_m` | `int` | Interna Abacus oznaka radne jedinice čiji se lager posmatra (`id` iz `getWorkUnits`). **Ako u sistemu nije podešena podrazumjevana radna jedinica, ovaj parametar postaje obavezan.** |
| `id_c` | `string` | Interna Abacus oznaka dodatnog cijenovnika za proračun cijena (`id` iz `getPriceLists`) |

> Napominjemo da je cijena proračunata, i da je popust tu samo ako je potrebno da ga prikažete, nema potrebe da išta preračunavate. U skladu sa ovim, rezultat funkcije `getItems` ima jedno dodatno polje tipa decimal, sa nazivom `discount`.

Primjer body-a:

```json
{
  "ids": [3131, 1235],
  "id_partner": 3658,
  "id_m": 8,
  "id_c": "001"
}
```

Pozivanje `getItems` funkcije sa ovim parametrima bi kao rezultat dalo 2 prethodno opisana objekta, za artikle sa UID 3131 i 1235, i cijenama i popustom validnim za partnera (klijenta) čiji je UID 3658, gdje bi početna cijena bila uzeta iz cijenovnika 001, i gdje bi posmatrani lager bio lager radne jedinice 8.

---

## 5. postSale

Funkcija **postSale** se koristi za postovanje porudžbenica. Prethodno je potrebno kreirati objekat naziva `order` sledeće strukture:

```json
{
  "order": {
    "id_partner": int,       // UID partnera
    "note": "string",        // napomena
    "items": [
      {
        "id_item": int,      // UID artikla
        "quantity": decimal,  // količina
        "price": decimal,     // cijena (nije neophodan, koristi se za override)
        "discount": decimal   // popust (nije neophodan, koristi se za override)
      }
    ]
  },
  "id_m": int                // opciono — radna jedinica sa koje se vrši prodaja
}
```

Primjer:

```
POST http://api.bencomltd.com/APITest/Main/postSale?token=12345678&protocol=2.0
```

Body:

```json
{
  "order": {
    "id_partner": 3658,
    "note": "test",
    "items": [
      {
        "id_item": 6003,
        "quantity": 1,
        "price": 100,
        "discount": 25
      },
      {
        "id_item": 2474,
        "quantity": 4,
        "price": 100,
        "discount": 50
      }
    ]
  },
  "id_m": 8
}
```

U ovom primjeru, kreirana je porudžba za partnera sa UID 3658, u kojoj postoje 2 stavke: artikal 6003 količina 1, artikal 2474 količina 4.

**Response:** Status code `200` ako je porudžba uspješno kreirana, `500` ako je došlo do neke greške.

Opcioni parametar `id_m` (cijeli broj) predstavlja internu Abacus oznaku radne jedinice u Abacusu sa koje se vrši prodaja (`id` iz `getWorkUnits`).

---

## 6. getIncomingItems

Primjer upita koji će vratiti listu artikala u dolasku:

```
GET http://api.bencomltd.com/APITest/Main/getIncomingItems?token=12345678&protocol=2.0
```

Ovaj upit vratiće listu objekata sledećeg tipa:

```json
{
  "id_item": int,      // ID artikla, identity column
  "code": "string",    // šifra artikla
  "item": "string",    // naziv artikla
  "date": "date"       // datum dokumenta
}
```

---

## 7. getOpenItems

Primjer upita koji će vratiti otvorene stavke za partnera:

```
GET http://api.bencomltd.com/APITest/Main/getOpenItems?token=12345678&protocol=2.0
```

Body:

```json
{
  "idPartner": 5361
}
```

- `idPartner` – `id_partnera` iz baze podataka

---

## 8. getPartnerBalanceDetailed

Primjer upita koji će vratiti finansijsku karticu za partnera:

```
GET http://api.bencomltd.com/APITest/Main/getPartnerBalanceDetailed?token=12345678&protocol=2.0
```

Body:

```json
{
  "idPartner": 5361,
  "datumDo": "2023-11-06"
}
```

- `idPartner` – `id_partnera` iz baze podataka
- `datumDo` – datum do kog se posmatra finansijsko stanje. Početni datum je 01.01. tekuće godine.

---

## 9. AddPartner

Primjer upita koji će kreirati partnera u Abacusu:

```
POST http://api.bencomltd.com/APITest/Main/AddPartner?token=12345678&protocol=2.0
```

Body:

```json
{
  "partner": {
    "idTip": "1",
    "isForeign": false,
    "naziv": "Test partner API",
    "maticni": "8888889",
    "pdv": "30/31-123456-76",
    "grad": "Podgorica",
    "adresa": "Ulica bb",
    "tel": "031332330",
    "email": "email@test.com",
    "kontakt": "Kontakt Osoba",
    "rabat": 0,
    "rok_placanja": 7,
    "fin_limit": 0,
    "dob_rokpla": 0,
    "dob_finlim": 0,
    "sifra": "081",
    "napomena": "",
    "fiscal_idType": 1
  }
}
```

### Objašnjenje polja

| Polje | Tip | Obavezno | Opis |
|-------|-----|----------|------|
| `idTip` | string | Da | ID tip šifrarnik iz tabele. Najčešće: `1` = d.o.o., `8` = fizičko lice |
| `isForeign` | boolean | Da | Da li je strani partner |
| `naziv` | string | Da | Naziv partnera |
| `maticni` | string | Da | Matični broj |
| `pdv` | string | Ne | PDV broj |
| `grad` | string | Da | Grad |
| `adresa` | string | Ne | Adresa |
| `tel` | string | Ne | Telefon |
| `email` | string | Ne | Email |
| `kontakt` | string | Ne | Kontakt osoba |
| `rabat` | decimal | Ne | Rabat (popust) |
| `rok_placanja` | int | Ne | Rok plaćanja (dani) |
| `fin_limit` | decimal | Ne | Finansijski limit |
| `dob_rokpla` | int | Ne | Dobavljač — rok plaćanja |
| `dob_finlim` | decimal | Ne | Dobavljač — finansijski limit |
| `sifra` | string | Ne | Šifra partnera |
| `napomena` | string | Ne | Napomena |
| `fiscal_idType` | int | Ne* | Tip fiskalnog ID-a. *Za strance je obavezan. |

Response:

```json
{
  "Data": 3668,
  "Version": "1.0",
  "Error": null,
  "ErrorDetails": null
}
```

U response-u se vraća `id_partnera` (u `Data` polju).

---

## 10. getPromotions

Primjer upita koji će vratiti promocije i akcije:

```
GET http://api.bencomltd.com/APITest/Main/getPromotions?token=12345678&protocol=2.0
```

### Parametri

| Parametar | Tip | Obavezno | Opis |
|-----------|-----|----------|------|
| `datumOd` | string (date) | Da | Početni datum |
| `datumDo` | string (date) | Da | Krajnji datum |
| `id_m` | int | Ne | ID radne jedinice |
| `id_partner` | int | Ne | ID partnera |
| `id_artikal` | int | Ne | ID artikla |

Primjer body-a:

```json
{
  "datumOd": "2023-01-01",
  "datumDo": "2024-12-31"
}
```
