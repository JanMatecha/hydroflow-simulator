# HydroFlow

Webová aplikace pro dynamickou simulaci dvou otevřených nádob propojených
trubkou. Rozdíl počátečních hladin vyvolá proudění, které OpenModelica počítá
nestacionární Bernoulliho rovnicí společně s bilancí objemu obou nádob.

Web zobrazuje animaci skutečného časového průběhu, graf hladin, graf průtoku,
maximální průtok a dobu přibližného vyrovnání.

## Fyzikální předpoklady

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
- `POST /api/simulations` – spuštění dynamické simulace
- `GET /docs` – interaktivní dokumentace API
