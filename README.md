# HydroFlow

Webová aplikace pro simulaci ustáleného proudění vody v rovné kruhové trubce.
Uživatel zadá tlakový rozdíl, geometrii trubky, drsnost a teplotu vody. Výpočet
provede OpenModelica a web zobrazí průtok, rychlost, Reynoldsovo číslo,
součinitel tření a průběh tlakové ztráty.

Model používá Darcyho–Weisbachovu rovnici. Nezahrnuje místní odpory, převýšení,
stlačitelnost ani přechodové jevy.

## Spuštění v Dockeru

Požadavkem je Docker s podporou Compose. Oficiální obraz OpenModelicy je
dostupný pro platformy podporované zvoleným tagem.

```powershell
docker compose up --build
```

Aplikace bude dostupná na <http://localhost:8000>. Ukončení:

```powershell
docker compose down
```

Port na hostiteli lze změnit v souboru `compose.yaml`, například záznamem
`8080:8000`.

## Lokální vývoj

Lokální spuštění vyžaduje Python 3.10 nebo novější a příkaz `omc` dostupný
v systémové cestě.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Kontroly

```powershell
pytest
ruff check .
ruff format --check .
```

Automatická oprava a formátování:

```powershell
ruff check --fix .
ruff format .
```

## API

- `GET /api/health` – kontrola dostupnosti aplikace
- `POST /api/simulations` – spuštění simulace
- `GET /docs` – interaktivní dokumentace API
