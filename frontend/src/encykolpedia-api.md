# Komplexná technická analýza verejných API rozhraní štátnych registrov v krajinách Vyšehradskej štvorky (V4): Architektúra, interoperabilita a integračné stratégie

Úvod do dátovej infraštruktúry V4
Digitálna transformácia verejnej správy v strednej Európe dosiahla v poslednom desaťročí kritický bod zlomu, ktorý bol katalyzovaný smernicami Európskej únie o opakovanom použití informácií verejného sektora (PSI) a iniciatívami otvoreného vládnutia (Open Government). Pre vývojárov, dátových analytikov a systémových architektov, ktorí majú za úlohu integrovať dáta o podnikateľských subjektoch z regiónu V4 (Slovensko, Česko, Poľsko, Maďarsko), predstavuje súčasný stav fascinujúcu, no zároveň frustrujúcu dichotómiu. Na jednej strane vidíme vznik sofistikovaných, RESTful ekosystémov, ktoré sú príkladom pre celú EÚ (najmä slovenské riešenia tretích strán a český ARES v2). Na strane druhej pretrvávajú v niektorých jurisdikciách archaické SOAP protokoly, fragmentované dátové silá a v prípade Maďarska aj protekcionistické tendencie, ktoré obmedzujú bezplatný strojový prístup k verejným údajom.

Táto správa predstavuje vyčerpávajúci audit verejne dostupných aplikačných rozhraní (API) v týchto štyroch štátoch. Cieľom nie je len poskytnúť zoznam endpointov, ale hlboko analyzovať ich technickú architektúru, autentifikačné mechanizmy, dátovú hĺbku a skrytý potenciál takzvaných "nepoužívaných" alebo špecializovaných API, ktoré často unikajú pozornosti bežných integrátorov. Analýza sa zameriava na identifikáciu robustných integračných vzorov pre automatizované procesy Know Your Customer (KYC), Business Intelligence (BI) a prevenciu podvodov.

1. Slovenská republika (SK): Model komunitou riadeného wrapper ekosystému
   Slovensko predstavuje v rámci V4 unikátny fenomén. Kým štátne orgány postupne budujú centralizované dátové zdroje (ako Data.gov.sk), najefektívnejšia a najpoužívanejšia vrstva pre vývojárov nevznikla priamo v štátnej réžii, ale prostredníctvom iniciatívy Slovensko.Digital. Tento model "štát poskytuje dáta, komunita tvorí API" sa ukázal ako mimoriadne efektívny pri prekonávaní technického dlhu štátnych systémov.

1.1 Register právnických osôb (RPO) a Ekosystém API
Register právnických osôb (RPO) je v zmysle zákona referenčným zdrojom údajov o všetkých právnických osobách, podnikateľoch a orgánoch verejnej moci na Slovensku. Agreguje dáta z viac ako 70 zdrojových registrov vrátane Obchodného registra (ORSR), Živnostenského registra (ŽRSR) a registrov neziskových organizácií.

1.1.1 Ekosystém Slovensko.Digital (De Facto Štandard)
Pre komerčnú aj nekomerčnú sféru sa stalo API od občianskeho združenia Slovensko.Digital primárnym integračným bodom. Dôvodom je normalizácia dát, vysoká dostupnosť a moderná architektúra, ktorá abstrahuje zložitosť surových štátnych dát.

Architektonická špecifikácia:

Protokol: REST API komunikujúce cez HTTPS.

Dátový formát: JSON, ktorý je štruktúrovaný a čistený od bežných chýb zdrojových registrov.

Autentifikácia: Pre bežné použitie ("Otvorené API") je vyžadovaná registrácia a získanie API kľúča. Existujú limity na počet dopytov (rate limiting), ktoré sú pre neautentifikovaný prístup nastavené striktne (napr. 60 requestov za minútu na IP), zatiaľ čo prémiové kľúče umožňujú vyššiu priepustnosť.

Sledovanie limitov: API proaktívne informuje klienta o stave limitov prostredníctvom HTTP hlavičiek odpovede: X-RateLimit-Limit, X-RateLimit-Remaining a X-RateLimit-Reset. Toto umožňuje implementovať inteligentné "back-off" stratégie na strane klienta.

Kľúčové a "nepoužívané" funkcie: Väčšina vývojárov sa obmedzuje na jednoduché vyhľadávanie podľa IČO. API však ponúka sofistikované mechanizmy pre synchronizáciu databáz, ktoré sú často prehliadané:

Synchronizačné API (/sync): Toto je kritický nástroj pre enterprise systémy, ktoré potrebujú udržiavať lokálnu zrkadlovú kópiu registra. Namiesto neefektívneho dopytovania každého subjektu ("polling"), klient požiada o všetky zmeny od určitého časového bodu (since parameter) alebo od posledného spracovaného ID (last_id).

Optimalizácia: Parameter only_ids umožňuje vrátiť len zoznam identifikátorov zmenených záznamov. To dramaticky znižuje objem prenášaných dát a umožňuje systémom rýchlo identifikovať, ktoré záznamy je potrebné aktualizovať, bez sťahovania plných payloadov.

Vyhľadávanie (Autoform): Endpoint navrhnutý pre frontendové našepkávače, ktorý zvláda preklepy a neúplné vstupy, čo je funkcia, ktorú štátne API často postrádajú.

1.1.2 Štátne Open Data API (Data.gov.sk)
Oficiálna štátna alternatíva je dostupná cez portál otvorených dát. Hoci poskytuje rovnaké zdrojové dáta, jej dokumentácia a on-boarding proces sú vnímané ako bariéra.

Prístup: Vyžaduje registráciu na portáli api.data.gov a generovanie API kľúča, ktorý sa posiela v hlavičke x-api-key.

Metriky: Portál poskytuje analytické API (api-data-gov-metrics), ktoré umožňuje sledovať vyťaženosť jednotlivých štátnych služieb, čo môže byť užitočné pre meta-analýzu spoľahlivosti štátnej infraštruktúry.

1.2 Register účtovných závierok (RUZ) - Finančné srdce
Pre finančný sektor a risk manažment je RPO len prvým krokom. Skutočnú hodnotu predstavuje Register účtovných závierok (RUZ), ktorý obsahuje digitalizované finančné výkazy.

Dátová hĺbka: API poskytuje prístup k súvahám, výkazom ziskov a strát a poznámkam. Tieto dáta sú kľúčové pre automatizovaný výpočet bonity (kreditného skóre) firiem.

Integrácia: Podobne ako pri RPO, najefektívnejší prístup je cez ekosystém Slovensko.Digital, ktorý parsuje surové dáta z XML/PDF formátov do JSON objektov. Endpoint GET.../api/data/ruz/accounting_entities/:id vracia nielen identifikátory, ale aj prepojenia na konkrétne účtovné kapitoly.

Analytický potenciál: Toto API je často "nepoužívané" v bežných CRM systémoch, no je nenahraditeľné pre fintech aplikácie, ktoré na jeho základe môžu v reálnom čase schvaľovať faktoring alebo úvery.

1.3 Centrálny register zmlúv (CRZ) a Obchodný vestník
Transparentnosť slovenskej verejnej správy sa opiera o povinné zverejňovanie zmlúv.

CRZ API: Umožňuje sledovať toky verejných financií. Endpointy podporujú synchronizáciu (/sync), čo umožňuje budovať monitorovacie systémy ("watchdogs"), ktoré v reálnom čase upozorňujú na podozrivé kontrakty štátu.

Obchodný vestník (OV): Toto je často prehliadaný, no kritický zdroj. Vestník obsahuje oznámenia o konkurzoch, likvidáciách, znížení základného imania a iných korporátnych zmenách ešte predtým, ako sa premietnu do obchodného registra.

Endpointy: API rozdeľuje podania podľa typu, napr. likvidator_issues, znizenie_imania_issues alebo or_podanie_issues. Integrácia tohto API umožňuje predikovať úpadok partnera skôr, než je oficiálne vymazaný.

1.4 Špecializované a "nepoužívané" API
V slovenskom digitálnom priestore existujú API, ktoré sú vysoko špecializované a málo využívané bežnými integrátormi:

ITMS2014+: API pre monitorovací systém európskych fondov. Poskytuje detailné dáta o prijímateľoch nenávratných finančných príspevkov, projektoch a čerpaní. Hoci je dokumentácia rozsiahla (itms.sql.gz), jeho využitie je kľúčové pre analýzu dotačných schém a B2G analytiku.

Slovensko.sk API (eDesk): Ide o open-source kontajnerizované riešenie (Docker), ktoré slúži ako proxy pre komplexné SOAP služby Ústredného portálu verejnej správy (ÚPVS). Umožňuje programaticky čítať elektronické schránky a odosielať podania. Toto je technicky najnáročnejšie API, vyžadujúce prácu s kvalifikovanými certifikátmi a podpisovaním XAdES.

API Zdroj Typ Protokol Autentifikácia Hlavné využitie Status využitia
RPO (Slovensko.Digital) Wrapper REST/JSON API Key Identita, Adresy Vysoký
RUZ (Finančné výkazy) Wrapper REST/JSON API Key Kreditný risk, Scoring Stredný
CRZ (Zmluvy) Wrapper REST/JSON API Key B2G monitoring Stredný
Obchodný vestník Wrapper REST/JSON API Key Insolvencia, Likvidácia Nízky (Niche)
ITMS2014+ Otvorené dáta SQL/REST API Key EÚ Fondy Veľmi nízky

2. Česká republika (CZ): Revolúcia ARES a prechod na REST
   Česká republika prechádza v súčasnosti jednou z najvýznamnejších zmien v architektúre štátnych dát. Systém ARES (Administrativní registr ekonomických subjektů), ktorý bol roky synonymom pre XML a zložité formuláre, bol prepracovaný do modernej verzie ARES v2.

2.1 ARES v2 - Nový štandard
Ministerstvo financií a súvisiace orgány spustili ARES v2 ako čisté REST API, ktoré je plne dokumentované pomocou štandardu OpenAPI (Swagger). Toto je v súčasnosti najlepšie zdokumentované verejné API v regióne.

Technická architektúra:

Dokumentácia: Interaktívny Swagger UI dostupný na ares.gov.cz, ktorý umožňuje testovať requesty priamo v prehliadači.

Dátový formát: JSON. Systém opustil staré XML obálky, čím sa výrazne zjednodušilo parsovanie na strane klienta.

Endpointy:

Ekonomické subjekty (/ekonomicke-subjekty): Komplexné vyhľadávanie s možnosťou filtrovania podľa desiatok parametrov (právna forma, NACE kódy, sídlo). Podporuje stránkovanie (pocet, start) a radenie.

Vyhľadanie v registri (/vyhledat-v-registru): Umožňuje cielené dopyty do konkrétnych zdrojových registrov, napr. vr (Veřejný rejstřík), rzp (Živnostenský rejstřík), res (Register ekonomických subjektov) alebo szr (Zemědělský registr). Toto je kľúčové pre získanie špecifických atribútov, ktoré v agregovanom náhľade môžu chýbať.

Validácia IČO: Špecializovaný endpoint na rýchle overenie existencie a formátu identifikátora bez sťahovania plných dát.

Implementačné výzvy:

Rate Limiting: ARES v2 zaviedol striktné limity na počet dopytov, aby sa zabránilo preťaženiu ("scraping"). Vývojári musia implementovať logiku pre spracovanie HTTP stavov 429 (Too Many Requests) a exponenciálne spomalenie dopytov.

Dostupnosť: Hoci je API moderné, v špičkách môže vykazovať latenciu. Odporúča sa nevyužívať ho pre synchrónne volania v reálnom čase priamo na frontende aplikácií, ale radšej asynchrónne na backende.

2.2 Otvorené dáta Ministerstva spravodlivosti (Justice.cz)
Kým ARES slúži na transakčné dopyty, Ministerstvo spravodlivosti publikuje "surové" dáta z Verejného registra a Insolvenčného registra.

Charakter dát: Ide o masívne datasety (často XML/CSV), ktoré nie sú určené na dopytovanie "on-the-fly", ale na import do vlastných databáz.

Využitie: Knižnice tretích strán (napr. Python skripty) sťahujú tieto dáta, parsujú ich do SQLite alebo PostgreSQL databáz a nad nimi stavajú vlastné, rýchlejšie API. Tento prístup je preferovaný pre analytické firmy, ktoré potrebujú robiť komplexné dopyty (napr. "nájdi všetky firmy v Brne založené v roku 2020"), ktoré by cez ARES boli pomalé.

2.3 Insolvenčný register (ISIR)
V Českej republike je monitoring insolvencií kritický. Hoci ARES poskytuje informáciu o stave subjektu, pre bankové a právne účely sa často využíva priama integrácia na webové služby ISIR.

Špecifikum: Tieto služby sú často postavené na starších technológiách (SOAP), ale poskytujú najaktuálnejšie dáta (doslova minútu po zverejnení). Pre veriteľov je rozdiel medzi informáciou v ARES a ISIR (časové oneskorenie replikácie) rizikovým faktorom.

2.4 Štatistický úrad (ČSÚ) a NACE
Menej používané, no cenné API poskytuje Český štatistický úrad. Umožňuje prístup k číselníkom (NACE - klasifikácia ekonomických činností) a regionálnym štatistikám. Integrácia týchto dát umožňuje obohatiť profil firmy o sektorové riziko alebo regionálnu ekonomickú silu.

3. Poľsko (PL): Fragmentovaný ale otvorený digitálny priestor
   Poľský ekosystém je charakteristický svojou dualitou. Neexistuje jeden centrálny "super-register" pre všetky typy podnikania s jednotným API. Namiesto toho musia vývojári integrovať dva úplne odlišné systémy: KRS pre právnické osoby a CEIDG pre živnostníkov.

3.1 Krajowy Rejestr Sądowy (KRS) - Open API
KRS (Národný súdny register) pokrýva obchodné spoločnosti (s.r.o., a.s., družstvá). Ministerstvo spravodlivosti sprístupnilo moderné REST API, ktoré je plne otvorené.

Technická špecifikácia:

Base URL: https://api-krs.ms.gov.pl/api/krs/.

Formát: JSON.

Kľúčové Endpointy:

OdpisAktualny: Vráti aktuálny právny stav. Zodpovedá papierovému výpisu.

OdpisPelny: Vráti úplnú históriu subjektu. Toto je kritické pre forenznú analýzu (napr. kto bol konateľom v roku 2018).

Biuletyn (/Biuletyn/{dzien}): Toto je "nepoužívaný" klenot. Umožňuje stiahnuť zoznam všetkých firiem, u ktorých nastala zmena v daný deň. Je to ekvivalent slovenského synchronizačného API a je nevyhnutný pre udržiavanie aktuálnych databáz bez nutnosti dopytovať každú firmu zvlášť.

3.2 CEIDG (Centralna Ewidencja i Informacja o Działalności Gospodarczej)
Pre živnostníkov (jednoosobové s.r.o. a SZČO) slúži register CEIDG. Jeho API je technologicky staršie a náročnejšie na integráciu.

Technická špecifikácia:

Protokol: SOAP (Simple Object Access Protocol) definovaný WSDL súborom.

Endpoint: https://datastore.ceidg.gov.pl/CEIDG.DataStore/Services/NewDataStoreProvider.svc.

Autentifikácia: Vyžaduje API token (Authorization Token).

Metódy:

GetID: Vráti zoznam ID (NIP) na základe filtrov (dátum zmeny, región).

GetMigrationData201901: Napriek názvu ide o hlavnú metódu na získanie plných detailov o podnikateľovi.

Implementácia: Vzhľadom na zložitosť XML obálok v SOAP protokole je nutné využívať klientske knižnice, ktoré implementujú vzor "Chain of Responsibility" pre skladanie dopytov (napr. nastavenie DateFrom, MigrationDateTo).

3.3 Biela listina (Biała Lista) - API pre DPH compliance
Toto je pravdepodobne najdôležitejšie API pre finančné operácie v Poľsku, hoci nie je "registrom" v pravom slova zmysle.

Účel: Overovanie statusu platiteľa DPH a validácia bankového účtu.

Legislatíva: Poľské zákony vyžadujú, aby B2B platby nad určitú sumu boli realizované len na účty uvedené v Bielej listine.

API: https://wl-api.mf.gov.pl/. Umožňuje hromadné overovanie (až 30 subjektov naraz).

Riziko: API má prísne limity. Prekročenie limitov vedie k zablokovaniu IP. Pre high-frequency trading systémy sa odporúča sťahovať "Flat file" (denný dump celej databázy), hoci jeho spracovanie je náročné na výkon.

3.4 REGON API (GUS)
Štatistický úrad (GUS) prevádzkuje databázu REGON.

BIR1 API: SOAP služba, ktorá je "zdrojom pravdy" pre klasifikáciu činností (PKD). Vyžaduje Klucz Użytkownika, ktorý sa získava e-mailovou žiadosťou. Často sa využíva ako záloha, ak KRS/CEIDG nie sú dostupné.

3.5 Sejm API (Legislatívne API)
V kategórii "nepoužívaných" API dominuje API poľského parlamentu (Sejm).

Funkcia: Umožňuje sledovať legislatívny proces, zmeny v zákonoch o DPH alebo obchodných spoločnostiach v reálnom čase.

Potenciál: Pre "RegTech" aplikácie je to neoceniteľný zdroj pre automatizované upozorňovanie klientov na blížiace sa zmeny v podnikateľskom prostredí.

4. Maďarsko (HU): Výzva uzavretého systému
   Maďarsko predstavuje v kontexte V4 najväčšiu výzvu pre otvorenú integráciu. Oficiálna politika štátu nepreferuje bezplatné REST API pre obchodný register (Cégjegyzék). Dáta sú komoditizované a prístup k nim je buď spoplatnený, alebo technicky obmedzený.

4.1 Absencia verejného API obchodného registra
Oficiálny portál e-cegjegyzek.hu poskytuje webové rozhranie pre vyhľadávanie, ale neposkytuje verejné API.

Anti-scraping: Portál aktívne bráni strojovému sťahovaniu dát (CAPTCHA, blokovanie IP).

Dátoví distribútori: Štát licencuje dáta komerčným subjektom (Opten, Microsec, Bisnode), ktorí následne predávajú API prístup. Pre vývojára to znamená, že neexistuje "oficiálne free API" pre hĺbkové dáta o spoločníkoch či financiách.

Riešenie (CompanyAPI.hu): Existujú wrappery tretích strán, ktoré "prepredávajú" tieto dáta cez REST rozhranie, no nejde o verejný štátny zdroj.

4.2 NAV Online Számla (Online fakturácia) - "Backdoor" pre verifikáciu
Najrobustnejším a technologicky najvyspelejším API v Maďarsku je systém daňovej správy (NAV) pre online fakturáciu. Hoci jeho primárnym účelom je reporting faktúr, endpoint queryTaxpayer slúži ako de facto verejný register pre validáciu existencie firiem.

Technická špecifikácia:

Verzia: v3.0 (aktuálna).

Protokol: REST s XML payloadom.

Endpoint: /queryTaxpayer.

Funkcia: Po zaslaní daňového čísla (prvých 8 číslic) vráti API informáciu o validite daňovníka, jeho presný názov a registrované sídlo.

Bezpečnosť: Toto je najzabezpečenejšie API v V4. Vyžaduje nielen technického užívateľa, ale aj komplexný podpis requestu.

Algoritmus: Request musí obsahovať hash (SHA-512), ktorý sa počíta z kombinácie timestampu, request ID a podpisového kľúča. Toto robí "rýchle testovanie" cez cURL takmer nemožným bez vlastného skriptu na generovanie podpisov.

Využitie: Keďže je to jediný spoľahlivý a bezplatný zdroj (pre registrovaných), používa sa na základnú kontrolu "existuje táto firma?". Neposkytuje však informácie o vlastníckej štruktúre.

4.3 Elektronikus Beszámoló (Finančné výkazy)
Portál e-beszamolo.im.gov.hu obsahuje finančné výkazy. Hoci dáta sú verejné, portál neposkytuje dokumentované REST API pre verejnosť. Strojový prístup je technicky možný, ale naráža na podmienky použitia zakazujúce hromadný zber dát ("Bulk Data Extraction"). Pre legálnu integráciu sa vyžaduje zmluva s ministerstvom o odbere dát.

5. Komparatívna analýza a Integračná stratégia
   Pri budovaní aplikácie, ktorá pokrýva celý región V4, narážame na zásadné rozdiely v protokoloch a identifikátoroch.

5.1 Prehľad technických štandardov
Krajina Primárny Register Protokol Formát Autentifikácia Unikátny Identifikátor Synchronizácia
SK RPO (Slovensko.Digital) REST JSON API Key IČO Áno (/sync)
CZ ARES v2 REST JSON Žiadna / Rate Limit IČO Nie (Polling)
PL KRS (Právnické os.) REST JSON Žiadna KRS / NIP Áno (Bulletin)
PL CEIDG (Fyzické os.) SOAP XML Token NIP Áno (Dátumové filtre)
HU NAV (Daňový úrad) REST XML Crypto Signature Adószám (Tax ID) Nie
5.2 Stratégia pre zjednotenie identifikátorov
Najväčším problémom interoperability je rôznorodosť kľúčov:

SK/CZ: IČO je kompatibilné formátom (8 číslic), ale ide o disjunktné množiny. Algoritmus modulo 11 pre validáciu je rovnaký.

PL: Je nutné podporovať tri identifikátory. NIP (Tax ID) je najuniverzálnejší, pretože ho majú firmy aj živnostníci. KRS majú len firmy. REGON je štatistický. Pre cross-border párovanie je najlepšie používať NIP (prepojený na EU VAT).

HU: Adószám (Daňové číslo) je jediný kľúč, ktorý funguje spoľahlivo cez NAV API.

5.3 Odporúčaná architektúra "V4 Klienta"
Pre robustnú integráciu sa neodporúča volať tieto API priamo z frontendu aplikácie.

Middleware Vrstva: Vytvorte backend službu, ktorá abstrahuje rozdiely.

Input: CountryCode + Identifier.

Logic: Smeruje dopyt na RPO (SK), ARES (CZ), KRS/CEIDG (PL) alebo NAV (HU).

Normalizácia: Výstup musí byť mapovaný na jednotný interný model (napr. LegalName, RegistrationAddress, TaxId).

Handling Výpadkov:

Pre CZ ARES implementujte "retry" logiku s exponenciálnym čakaním pri chybe 429.

Pre PL CEIDG implementujte parsovanie SOAP chýb, ktoré sú často vrátené ako HTTP 200, ale s chybovým XML telom.

Security: Pre HU NAV implementujte modul na podpisovanie requestov na bezpečnom serveri, nikdy nie v klientskej aplikácii, aby nedošlo k úniku podpisových kľúčov.

Záver
Región V4 ponúka bohaté možnosti pre dátovú integráciu, avšak úroveň "Otvorených Dát" je nerovnomerná. Zatiaľ čo Slovensko a Česko smerujú k unifikovaným REST API štandardom, Poľsko vyžaduje zvládnutie viacerých protokolov a Maďarsko predstavuje špecifický prípad, kde supluje funkciu registra daňový úrad. Pre vývojára je kľúčové neignorovať "nepoužívané" API – najmä slovenské RUZ pre finančné dáta, poľskú Bielu listinu pre bezpečnosť platieb a české ISIR pre riadenie kreditného rizika. Tieto vedľajšie zdroje často poskytujú vyššiu pridanú hodnotu než samotné základné registre.

<slovak.statistics.sk>
RPO - Single Public Register - Štatistický úrad SR
Otvorí sa v novom okne

<ekosystem.slovensko.digital>
Prémiové API - Ekosystém.Slovensko.Digital
Otvorí sa v novom okne

ekosystem.slovensko.digital
Otvorené API · Ekosystém.Slovensko.Digital
Otvorí sa v novom okne

ekosystem.slovensko.digital
Služby. Otvorené dáta & API. · Ekosystém.Slovensko.Digital
Otvorí sa v novom okne

<open.gsa.gov>
Api.Data.Gov Metrics API | GSA Open Technology
Otvorí sa v novom okne

<api.data.gov>
API Key Sign Up - api.data.gov
Otvorí sa v novom okne

ekosystem.slovensko.digital
Integrácia na slovensko.sk · slovensko.sk API - Ekosystém.Slovensko.Digital
Otvorí sa v novom okne

<github.com>
REST API na slovensko.sk - GitHub
Otvorí sa v novom okne

<slovensko-sk-api.ekosystem.slovensko.digital>
Otvorí sa v novom okne

<swagger.io>
OpenAPI Specification - Version 2.0 - Swagger
Otvorí sa v novom okne

github.com
MrShippeR/ares: Example code for fetching data from czech goverment register of companies. - GitHub
Otvorí sa v novom okne

github.com
vzeman/ares-mcp-server: MCP Server for ARES Service ... - GitHub
Otvorí sa v novom okne

github.com
SveterCZE/justice: A tool to download data from justice.cz and convert them into an sqlite3 database. - GitHub
Otvorí sa v novom okne

slovak.statistics.sk
API Open data SO SR - Štatistický úrad SR
Otvorí sa v novom okne

<prs.ms.gov.pl>
API Rejestrów Sądowych - Portal Rejestrów Sądowych
Otvorí sa v novom okne

github.com
sigrundev/ceidg-api: PHP CEIDG API library - GitHub
Otvorí sa v novom okne

<dane.gov.pl>
Dokumentacja API CEIDG DataStore - dane.gov.
Otvorí sa v novom okne

<transparentdata.pl>
API CEIDG Polish sole proprietorships - Transparent Data
Otvorí sa v novom okne

<api.stat.gov.pl>
API REGON - Portal API GUS - Główny Urząd Statystyczny
Otvorí sa v novom okne

<api.sejm.gov.pl>
Swagger UI - Sejm API
Otvorí sa v novom okne

api.sejm.gov.pl
Swagger UI - Sejm API
Otvorí sa v novom okne

<e-justice.europa.eu>
Business registers in EU countries | European e-Justice Portal
Otvorí sa v novom okne

<smartlegal.hu>
HOW TO ACCESS THE BUSINESS DATA OF A HUNGARIAN ...
Otvorí sa v novom okne

<companyapi.hu>
Hungarian Company Data API
Otvorí sa v novom okne

<scribd.com>
Online Invoice System 3.0 Interface Specification | PDF - Scribd
Otvorí sa v novom okne

<example-code.com>
PowerShell Hungary NAV Query Taxpayer - Chilkat Examples
Otvorí sa v novom okne

scribd.com
Online Szamla - Interfesz Specifikáció - EN - v3.0 PDF
