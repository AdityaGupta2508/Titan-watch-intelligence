# Titan Watch Intelligence (white + navy royal theme)

1. **Analyse** how many Titan watches are sold - by month, year, collection, city, channel, price band, discount.
2. **Predict** future watches sold (months to 5 years) with revenue and profit under different discount strategies.

## Run
One click: double-click `run.bat` (Windows) / `run.command` (Mac). Or:
    pip install -r requirements.txt
    python setup_db.py
    streamlit run app.py

## Pages
- Command Center - KPIs, **animated model showcase (watch + units sold, Next/Prev, auto-play)**, insights, heatmap, treemap
- Sales Deep-Dive - collections, geography, channel, price bands, top models
- Future Forecast - scenario controls, **predicted units per model carousel**, year-by-year outlook, backtest, CSV
- Discount Lab - discount curve, profit-maximising discount, what-if calculator, demand map
- Data Manager - add sales, bulk CSV import, SQL explorer, schema

## Watch images
Each collection has its own drawn watch (watch_art.py). For real photos put files in `images/` named after the
model or collection (see images/README.txt) and they replace the drawings.

## Files
schema.sql | setup_db.py | engine.py (SQL + analysis + forecasting) | watch_art.py (SVG watches) |
showcase.py (carousel) | app.py (UI) | .streamlit/config.toml (theme)
