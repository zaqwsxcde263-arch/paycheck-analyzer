# Paycheck Analyzer

Local paycheck/purchase analyzer with:
- Manual data entry (products, categories, prices, purchases)
- Dashboards by month, week, category
- Currency selector (with optional live FX + manual override)
- Product price-change dashboard

## Setup

### Option A (recommended): install venv support

On Ubuntu/Debian, install venv + pip:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
```

Then:

```bash
cd paycheck-analyzer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Option B: no venv (not recommended)

```bash
sudo apt update
sudo apt install -y python3-pip
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Data storage

- SQLite DB file: `data/paycheck.db`
- You can delete `data/paycheck.db` to reset everything.

