# Local AI Test

Malý ukázkový Python projekt sloužící k ověření lokálního běhového prostředí.

## Požadavky

- Python 3.10 nebo novější

## Instalace

Vytvořte virtuální prostředí a nainstalujte projekt včetně vývojových závislostí:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Spuštění

```powershell
python test_script.py
```

## Testy

```powershell
pytest
```

## Kontrola a formátování kódu

```powershell
ruff check .
ruff format --check .
```

Automatickou opravu a formátování lze provést příkazy:

```powershell
ruff check --fix .
ruff format .
```
