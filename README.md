# HydroFlow

Webová aplikace pro hydraulické simulace počítané v OpenModelice. Jednotlivé
úlohy jsou dostupné v samostatných záložkách; každá si při přepnutí zachovává
vlastní vstupy i výsledky.

## Dostupné modely

### Dvě propojené nádoby

Dynamická simulace dvou otevřených nádob propojených trubkou. Rozdíl
počátečních hladin vyvolá proudění, které model počítá nestacionární
Bernoulliho rovnicí společně s bilancí objemu obou nádob. Web zobrazuje animaci
časového průběhu, graf hladin, graf průtoku, maximální průtok a dobu přibližného
vyrovnání.

### Samostatná trubka

Ustálené proudění vody v rovné kruhové trubce vyvolané zadaným rozdílem tlaku.
Model počítá objemový a hmotnostní průtok, rychlost, Reynoldsovo číslo, režim
proudění a součinitel tření. Web navíc vykreslí tlakovou ztrátu po délce trubky.

### Kapková závlaha

Ustálený gravitační model dvou IBC nádrží, zón A a B, deseti záhonů A–J a
čtyřiceti kapkových řádků. Zahrnuje hydrostatický tlak, společné ztráty v
hlavních rozvodech, pevnou ztrátu filtru, nastavitelné vstupní ventily a
nelineární charakteristiku kapkovače bez tlakové kompenzace. Web nabízí scénář
jednoho záhonu, všech záhonů a počáteční návrh ručního vyvážení.

První verze používá každý řádek jako jeden ekvivalentní prvek. Pokles hladiny
IBC je zatím odhadnut bilancí z ustáleného průtoku; detailní dynamika hladiny a
segmenty mezi jednotlivými kapkovači jsou připravené jako další rozšíření.

## Fyzikální předpoklady modelu nádob

- válcové otevřené nádoby se dny ve stejné výšce,
- spojovací trubka připojená u dna,
- nestlačitelná voda s vlastnostmi závislými na teplotě,
- Darcyho tření a pevná vstupní/výstupní místní ztráta,
- obousměrné proudění bez čerpadla a ventilu.

## Lokální spuštění

Je potřeba Python 3.10 nebo novější a příkaz `omc` dostupný v systémové cestě.
Na Windows aplikace umí nalézt také běžnou instalaci OpenModelica 1.26/1.27.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Aplikace bude dostupná na <http://localhost:8000>.

## Spuštění v Dockeru

```powershell
docker compose up --build
```

## Kontroly

```powershell
pytest
ruff check .
ruff format --check .
```

## API

- `GET /api/health` – kontrola dostupnosti aplikace
- `GET /api/models` – seznam dostupných modelů
- `POST /api/models/two-tanks/simulations` – simulace dvou nádob
- `POST /api/models/water-pipe/simulations` – simulace samostatné trubky
- `POST /api/models/garden-irrigation/simulations` – gravitační kapková závlaha
- `POST /api/simulations` – původní alias simulace dvou nádob
- `GET /docs` – interaktivní dokumentace API
