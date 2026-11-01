"""Titan Watch Intelligence - data access, analysis and forecasting engine (no UI code here)."""
import os, sqlite3, calendar
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "titan.db")
MONTHS = [calendar.month_abbr[i] for i in range(1, 13)]
PRICE_LABELS = ["Under ₹3K", "₹3–6K", "₹6–12K", "₹12K+"]
DISC_LABELS = ["0–5%", "6–10%", "11–15%", "16–20%", "20%+"]

# ------------------------------------------------------------------ database
def q(sql, params=()):
    with sqlite3.connect(DB) as c:
        return pd.read_sql_query(sql, c, params=params)

def run_readonly(sql):
    """SQL explorer: a single SELECT/WITH statement on a read-only connection."""
    s = sql.strip().rstrip(";")
    if ";" in s:
        raise ValueError("Only one statement at a time.")
    if not s.lower().startswith(("select", "with")):
        raise ValueError("Only SELECT queries are allowed.")
    with sqlite3.connect(Path(DB).as_uri() + "?mode=ro", uri=True) as c:
        return pd.read_sql_query(s, c)

def row_count():
    return int(q("SELECT COUNT(*) n FROM sales").iloc[0, 0])

def load_sales():
    """One denormalised frame (sales + product + store + avg rating) pulled with a single SQL JOIN."""
    df = q("""
        SELECT s.sale_id, s.sale_date, s.quantity AS units, s.discount_pct, s.selling_price, s.revenue,
               p.product_id, p.model_name, p.collection, p.gender, p.strap, p.movement, p.mrp,
               st.city, st.region, st.channel, r.avg_rating
        FROM sales s
        JOIN products p  ON p.product_id = s.product_id
        JOIN stores  st  ON st.store_id  = s.store_id
        LEFT JOIN (SELECT product_id, AVG(rating) avg_rating FROM reviews GROUP BY product_id) r
               ON r.product_id = p.product_id""")
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["month"] = df["sale_date"].dt.to_period("M").dt.to_timestamp()
    df["year"] = df["sale_date"].dt.year
    df["month_no"] = df["sale_date"].dt.month
    last = df["sale_date"].max()
    last_m = last.to_period("M")
    df["complete"] = (df["month"] < last_m.to_timestamp()) | (last.day == last_m.days_in_month)
    df["price_band"] = pd.cut(df["mrp"], [0, 3000, 6000, 12000, 1e12], labels=PRICE_LABELS)
    df["disc_band"] = pd.cut(df["discount_pct"], [-1, 5, 10, 15, 20, 100], labels=DISC_LABELS)
    return df

def add_sale(product_id, store_id, sale_date, quantity, discount_pct):
    mrp = float(q("SELECT mrp FROM products WHERE product_id=?", (product_id,)).iloc[0, 0])
    price = round(mrp * (1 - discount_pct / 100), 2)
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO sales(product_id,store_id,sale_date,quantity,discount_pct,selling_price,revenue) "
                  "VALUES (?,?,?,?,?,?,?)",
                  (product_id, store_id, str(sale_date), int(quantity), float(discount_pct), price,
                   round(price * quantity, 2)))

def import_sales_csv(df):
    """Bulk append. Required columns: product_id, store_id, sale_date, quantity, discount_pct."""
    req = {"product_id", "store_id", "sale_date", "quantity", "discount_pct"}
    missing = req - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    prods, stores = q("SELECT product_id, mrp FROM products"), q("SELECT store_id FROM stores")
    df = df.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    bad = df["sale_date"].isna() | ~df["product_id"].isin(prods["product_id"]) \
        | ~df["store_id"].isin(stores["store_id"]) | (df["quantity"] <= 0) | ~df["discount_pct"].between(0, 90)
    if bad.any():
        raise ValueError(f"{int(bad.sum())} invalid rows (bad date / unknown product or store / quantity / discount).")
    df = df.merge(prods, on="product_id")
    df["selling_price"] = (df["mrp"] * (1 - df["discount_pct"] / 100)).round(2)
    df["revenue"] = (df["selling_price"] * df["quantity"]).round(2)
    rows = [(int(r.product_id), int(r.store_id), r.sale_date.date().isoformat(), int(r.quantity),
             float(r.discount_pct), float(r.selling_price), float(r.revenue)) for r in df.itertuples()]
    with sqlite3.connect(DB) as c:
        c.executemany("INSERT INTO sales(product_id,store_id,sale_date,quantity,discount_pct,selling_price,revenue) "
                      "VALUES (?,?,?,?,?,?,?)", rows)
    return len(rows)

# ------------------------------------------------------------------ analysis
def monthly_series(df):
    d = df[df["complete"]]
    cols = ["month", "units", "revenue", "avg_disc", "avg_mrp", "mxu", "tx"]
    if d.empty:
        return pd.DataFrame(columns=cols)
    g = (d.assign(dxu=d["discount_pct"] * d["units"], mxu=d["mrp"] * d["units"])
           .groupby("month").agg(units=("units", "sum"), revenue=("revenue", "sum"), dxu=("dxu", "sum"),
                                 mxu=("mxu", "sum"), tx=("sale_id", "count")).reset_index())
    g["avg_disc"] = g["dxu"] / g["units"]
    g["avg_mrp"] = g["mxu"] / g["units"]
    return g[cols]

def yearly(df):
    d = df[df["complete"]]
    g = d.groupby("year").agg(units=("units", "sum"), revenue=("revenue", "sum"),
                              months=("month", "nunique")).reset_index()
    g["yoy"] = np.where((g["months"] == 12) & (g["months"].shift() == 12), g["units"].pct_change(), np.nan)
    return g

def kpis(df):
    d = df[df["complete"]]
    units = int(d["units"].sum())
    out = dict(units=units, revenue=float(d["revenue"].sum()),
               avg_disc=float((d["discount_pct"] * d["units"]).sum() / max(units, 1)),
               yoy=None, best="-", best_share=0.0)
    m = monthly_series(df)
    if len(m) >= 24:
        out["yoy"] = float(m["units"].tail(12).sum() / m["units"].iloc[-24:-12].sum() - 1)
    if len(d):
        c = d.groupby("collection")["units"].sum().sort_values(ascending=False)
        out["best"], out["best_share"] = c.index[0], float(c.iloc[0] / units)
    return out

def insights(df):
    d = df[df["complete"]]
    if d.empty:
        return []
    tot, out = d["units"].sum(), []
    c = d.groupby("collection")["units"].sum().sort_values(ascending=False)
    out.append(f"<b>{c.index[0]}</b> is the #1 collection with {c.iloc[0]/tot:.0%} of units sold; "
               f"<b>{c.index[-1]}</b> is the smallest at {c.iloc[-1]/tot:.0%}.")
    mm = d.groupby(["year", "month_no"])["units"].sum().groupby("month_no").mean()
    out.append(f"Peak season is <b>{MONTHS[mm.idxmax()-1]}</b> at {mm.max()/mm.mean():.1f}× an average month; "
               f"the slowest is <b>{MONTHS[mm.idxmin()-1]}</b> at {mm.min()/mm.mean():.1f}×.")
    r = d.groupby("region")["units"].sum().sort_values(ascending=False)
    out.append(f"<b>{r.index[0]}</b> India leads with {r.iloc[0]/tot:.0%} of units; "
               f"<b>{r.index[-1]}</b> trails at {r.iloc[-1]/tot:.0%}.")
    out.append(f"The Online channel contributes <b>{d[d.channel == 'Online']['units'].sum()/tot:.0%}</b> of all units.")
    dd = d.groupby("disc_band", observed=True)["units"].mean().dropna()
    if len(dd) > 1:
        out.append(f"Deeper discounts grow the basket: <b>{dd.index[-1]}</b> deals average {dd.iloc[-1]:.2f} watches "
                   f"per sale vs {dd.iloc[0]:.2f} at {dd.index[0]}.")
    return out

# ------------------------------------------------------------------ forecasting
# Model:  log(units_m) = a*t + b*avg_discount_m + month-of-year effects     (least squares on monthly history)
#   a -> underlying growth trend, b -> discount elasticity, month effects -> seasonality (Diwali etc.)
def _X(t, mo, disc):
    t, mo, disc = np.asarray(t, float), np.asarray(mo), np.asarray(disc, float)
    return np.column_stack([t, disc] + [(mo == k).astype(float) for k in range(1, 13)])

def _tidx(months, first):
    return ((months.dt.year - first.year) * 12 + (months.dt.month - first.month)).values.astype(float)

def fit_model(m):
    m = m.sort_values("month").reset_index(drop=True)
    first = m["month"].iloc[0]
    t, mo = _tidx(m["month"], first), m["month"].dt.month.values
    X, y = _X(t, mo, m["avg_disc"].values), np.log(m["units"].values.astype(float))
    mdl = LinearRegression(fit_intercept=False).fit(X, y)
    res = y - mdl.predict(X)
    sd = float(np.sqrt((res ** 2).sum() / max(len(y) - X.shape[1], 1)))
    g, b = float(mdl.coef_[0]), float(mdl.coef_[1])
    rec = m.tail(12)
    dbm = m.groupby(m["month"].dt.month)["avg_disc"].mean().reindex(range(1, 13)).fillna(m["avg_disc"].mean())
    return dict(model=mdl, first=first, t_last=int(t.max()), last_month=m["month"].iloc[-1], sd=sd, b=b,
                b_used=float(np.clip(b, 0.0, 0.08)), annual_growth=float(np.exp(12 * g) - 1),
                disc_by_month=dbm.values, avg_mrp=float(rec["mxu"].sum() / rec["units"].sum()), n=len(m))

def predict_units(fit, t, mo, disc, trend_mult=1.0):
    t = np.asarray(t, float)
    t_eff = np.where(t > fit["t_last"], fit["t_last"] + (t - fit["t_last"]) * trend_mult, t)
    return np.exp(fit["model"].predict(_X(t_eff, mo, disc)))

def plan_history(fit):          return fit["disc_by_month"].copy()
def plan_flat(d):               return np.full(12, float(d))
def plan_festive(base, extra, months=(10, 11)):
    p = np.full(12, float(base))
    for mth in months:
        p[mth - 1] += extra
    return p

def forecast(fit, horizon, plan, trend_mult=1.0, margin=0.5, z=1.28):
    months = pd.date_range(fit["last_month"] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    t, mo = fit["t_last"] + np.arange(1, horizon + 1), months.month.values
    disc = np.asarray(plan, float)[mo - 1]
    u = predict_units(fit, t, mo, disc, trend_mult)
    band = z * fit["sd"] * np.sqrt(1 + np.arange(1, horizon + 1) / 12)
    price = fit["avg_mrp"] * (1 - disc / 100)
    cost = fit["avg_mrp"] * (1 - margin)
    return pd.DataFrame(dict(month=months, disc=disc, units=u, low=u * np.exp(-band), high=u * np.exp(band),
                             revenue=u * price, profit=u * (price - cost)))

def backtest(m, holdout=6):
    m = m.sort_values("month").reset_index(drop=True)
    tr, te = m.iloc[:-holdout], m.iloc[-holdout:]
    fit = fit_model(tr)
    t = _tidx(te["month"], fit["first"])
    pred = np.exp(fit["model"].predict(_X(t, te["month"].dt.month.values, te["avg_disc"].values)))
    mape = float(np.mean(np.abs(pred - te["units"].values) / te["units"].values))
    return mape, pd.DataFrame(dict(month=te["month"].values, actual=te["units"].values, predicted=pred))

def discount_curve(fit, month_no, margin, grid=range(0, 41)):
    k = ((month_no - fit["last_month"].month - 1) % 12) + 1
    d = np.array(list(grid), float)
    u = predict_units(fit, np.full(len(d), fit["t_last"] + k), np.full(len(d), month_no), d)
    price, cost = fit["avg_mrp"] * (1 - d / 100), fit["avg_mrp"] * (1 - margin)
    return pd.DataFrame(dict(discount=d, units=u, revenue=u * price, profit=u * (price - cost)))

def units_matrix(fit, grid=range(0, 41, 5)):
    return pd.DataFrame({MONTHS[mn - 1]: discount_curve(fit, mn, 0.5, grid)["units"].values for mn in range(1, 13)},
                        index=list(grid))

def annual_outlook(m, fc, cost_per_unit):
    h = m[["month", "units", "revenue", "avg_disc"]].copy()
    h["profit"], h["kind"] = h["revenue"] - h["units"] * cost_per_unit, "A"
    f = fc[["month", "units", "revenue", "disc", "profit"]].rename(columns={"disc": "avg_disc"})
    f["kind"] = "F"
    a = pd.concat([h, f], ignore_index=True)
    a["year"] = a["month"].dt.year
    a["ua"], a["uf"] = np.where(a["kind"] == "A", a["units"], 0.0), np.where(a["kind"] == "F", a["units"], 0.0)
    out = a.groupby("year").agg(months=("month", "count"), units_actual=("ua", "sum"), units_forecast=("uf", "sum"),
                                units=("units", "sum"), revenue=("revenue", "sum"), profit=("profit", "sum"),
                                avg_disc=("avg_disc", "mean"), fmonths=("kind", lambda s: (s == "F").sum())).reset_index()
    return out
