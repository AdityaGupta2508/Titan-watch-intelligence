"""Titan Watch Intelligence  -  run:  streamlit run app.py
Function 1: analyse how many Titan watches are sold (where / what / when / at what discount)
Function 2: predict future units, revenue and profit under different discount strategies
"""
import calendar
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
import engine as E
import showcase as SC

st.set_page_config(page_title="Titan Watch Intelligence", page_icon="⌚", layout="wide")

NAVY, ROYAL, SKY, RED, GREY, GOLD = "#0A1F5C", "#2F4FB5", "#6F9BF2", "#C0392B", "#7B88AB", "#C9A24B"
GROWTH = {"Flat (no growth)": 0.0, "Conservative": 0.5, "Model trend": 1.0, "Aggressive": 1.5}
ICE = [[0, "#EEF3FD"], [1, NAVY]]

# ------------------------------------------------------------------ look & feel (white + navy, royal gold hairlines)
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Playfair+Display:wght@600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color:#0A1F5C; }
.stApp { background: linear-gradient(180deg,#F4F7FE 0%,#FFFFFF 38%); }
.block-container { padding-top: 1.1rem; max-width: 1450px; }
[data-testid="stSidebar"] { background: #F1F5FD; border-right: 2px solid #0A1F5C; }
[data-testid="stSidebar"] h3 { font-size:1rem; letter-spacing:.14em; text-transform:uppercase; color:#0A1F5C; }
#MainMenu, footer { visibility: hidden; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; letter-spacing:.01em; color:#0A1F5C; }
.hero { position:relative; display:flex; align-items:center; gap:24px; padding:20px 30px; margin-bottom:16px; border-radius:22px;
        background: radial-gradient(700px 240px at 90% -20%, #2A4FB8 0%, transparent 70%), linear-gradient(120deg,#08174D,#0A1F5C 60%,#16358F);
        border:1px solid #C9A24B; box-shadow:0 14px 40px rgba(10,31,92,.28), inset 0 0 0 5px rgba(255,255,255,.05); }
.hero h1 { margin:0; font-size:2.1rem; color:#FFFFFF !important; }
.hero h1 span { color:#E8D49A; font-weight:600; }
.hero p { margin:6px 0 0; color:#B9C8F2; font-size:.82rem; letter-spacing:.2em; }
.hero .rule { width:120px; height:2px; margin-top:10px; background:linear-gradient(90deg,#C9A24B,transparent); }
.sec { font-family:'Playfair Display',serif; font-size:1.3rem; font-weight:700; color:#0A1F5C; margin:22px 0 6px;
       padding-bottom:6px; border-bottom:2px solid #E3EAF8; position:relative; }
.sec:after { content:""; position:absolute; left:0; bottom:-2px; width:70px; height:2px; background:#C9A24B; }
.kpi { background:#FFFFFF; border:1px solid #DCE4F5; border-top:4px solid #0A1F5C; border-radius:16px; padding:15px 18px;
       height:100%; box-shadow:0 8px 22px rgba(10,31,92,.08); }
.kpi .l { font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; color:#6B7BA6; font-weight:600; }
.kpi .v { font-size:1.7rem; font-weight:800; color:#0A1F5C; line-height:1.25; font-family:'Playfair Display',serif; }
.kpi .s { font-size:.8rem; color:#6B7BA6; }
.kpi .s.up { color:#168A55; font-weight:600; } .kpi .s.down { color:#C0392B; font-weight:600; }
.insight { border-left:4px solid #0A1F5C; background:#EEF3FD; padding:10px 15px; margin:7px 0;
           border-radius:0 12px 12px 0; font-size:.93rem; color:#14295F; }
.note { color:#6B7BA6; font-size:.82rem; }
.spin { transform-origin: 50px 50px; animation: tick 60s steps(60) infinite; }
.spin2 { transform-origin: 50px 50px; animation: tick 3600s linear infinite; }
@keyframes tick { to { transform: rotate(360deg); } }
</style>"""

HERO = ("<div class='hero'><svg width='78' height='78' viewBox='0 0 100 100'>"
        "<circle cx='50' cy='50' r='46' fill='#FFFFFF' stroke='#C9A24B' stroke-width='3'/>"
        "<circle cx='50' cy='50' r='40' fill='none' stroke='rgba(10,31,92,.25)' stroke-width='1'/>"
        + "".join(f"<line x1='50' y1='10' x2='50' y2='{16 if i % 3 == 0 else 13}' stroke='#0A1F5C' "
                  f"stroke-width='{2.4 if i % 3 == 0 else 1}' transform='rotate({i*30} 50 50)'/>" for i in range(12)) +
        "<line class='spin2' x1='50' y1='50' x2='50' y2='20' stroke='#0A1F5C' stroke-width='3' stroke-linecap='round'/>"
        "<line x1='50' y1='50' x2='68' y2='58' stroke='#0A1F5C' stroke-width='3.4' stroke-linecap='round'/>"
        "<line class='spin' x1='50' y1='56' x2='50' y2='14' stroke='#C9A24B' stroke-width='1.4'/>"
        "<circle cx='50' cy='50' r='3' fill='#C9A24B'/></svg>"
        "<div><h1>♛ TITAN <span>Watch Intelligence</span></h1>"
        "<p>SALES ANALYTICS &nbsp;✦&nbsp; DEMAND FORECASTING &nbsp;✦&nbsp; DISCOUNT OPTIMISATION</p>"
        "<div class='rule'></div></div></div>")

st.markdown(CSS, unsafe_allow_html=True)
st.markdown(HERO, unsafe_allow_html=True)

# ------------------------------------------------------------------ helpers
def inr(x):
    return f"₹{x/1e7:,.2f} Cr" if abs(x) >= 1e7 else (f"₹{x/1e5:,.2f} L" if abs(x) >= 1e5 else f"₹{x:,.0f}")

def kpi(label, value, sub="", tone=""):
    return f"<div class='kpi'><div class='l'>{label}</div><div class='v'>{value}</div><div class='s {tone}'>{sub}</div></div>"

def sec(text):
    st.markdown(f"<div class='sec'>{text}</div>", unsafe_allow_html=True)

def style(fig, h=380):
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", color="#14295F"), height=h,
                      margin=dict(l=8, r=8, t=44, b=8), colorway=[NAVY, SKY, NAVY, ROYAL, RED, GREY],
                      legend=dict(orientation="h", y=1.12, x=0), title=dict(font=dict(size=15, color=NAVY)))
    fig.update_xaxes(gridcolor="rgba(10,31,92,.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(10,31,92,.08)", zeroline=False)
    return fig

def show(fig):
    try:
        st.plotly_chart(fig, theme=None, width="stretch")
    except TypeError:
        st.plotly_chart(fig, theme=None, use_container_width=True)

def table(df, **kw):
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kw)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True, **kw)


def model_table(d):
    g = (d.assign(dxu=d.discount_pct * d.units).groupby(["model_name", "collection", "strap"])
           .agg(units=("units", "sum"), revenue=("revenue", "sum"), mrp=("mrp", "first"), dxu=("dxu", "sum"),
                rating=("avg_rating", "first")).reset_index().sort_values("units", ascending=False))
    g["avg_disc"] = g.dxu / g.units
    return g

def showcase(items, title, height=700):
    html, h = SC.build(items, title, height)
    components.html(html, height=h)

def best_seller_items(d):
    g = model_table(d)
    tot, n = g.units.sum(), len(g)
    return [dict(name=r.model_name, collection=r.collection, strap=r.strap, value=r.units, label="WATCHES SOLD",
                 badge=("♛ BEST SELLER" if i == 1 else f"#{i} OF {n}"), short=r.model_name,
                 stats=[("Revenue", inr(r.revenue)), ("MRP", f"₹{r.mrp:,.0f}"), ("Avg discount", f"{r.avg_disc:.1f}%"),
                        ("Share of units", f"{r.units/tot:.1%}"), ("Rating", f"{r.rating:.2f} ★")])
            for i, r in enumerate(g.itertuples(), 1)]

def forecast_items(scope_df, nxt):
    months = sorted(scope_df[scope_df.complete].month.unique())[-12:]
    g = model_table(scope_df[scope_df.complete & scope_df.month.isin(months)])
    tot, n, units_total = g.units.sum(), len(g), nxt.units.sum()
    disc = nxt.disc.mean()
    items = []
    for i, r in enumerate(g.itertuples(), 1):
        share = r.units / tot
        fu = units_total * share
        items.append(dict(name=r.model_name, collection=r.collection, strap=r.strap, value=fu,
                          label=f"PREDICTED WATCHES - NEXT {len(nxt)} MONTHS",
                          badge=("♛ TOP FORECAST" if i == 1 else f"#{i} OF {n}"), short=r.model_name,
                          stats=[("Last 12 months", f"{r.units:,.0f}"), ("Expected revenue", inr(fu * r.mrp * (1 - disc / 100))),
                                 ("Share of units", f"{share:.1%}"), ("MRP", f"₹{r.mrp:,.0f}")]))
    return items

def cards(items):
    for col, html in zip(st.columns(len(items)), items):
        col.markdown(html, unsafe_allow_html=True)

# ------------------------------------------------------------------ data + filters
@st.cache_data(show_spinner=False)
def get_data(rows):          # `rows` changes whenever the DB grows -> cache refreshes automatically
    return E.load_sales()

df_all = get_data(E.row_count())

st.sidebar.markdown("### Navigate")
PAGES = ["Command Center", "Sales Deep-Dive", "Future Forecast", "Discount Lab", "Data Manager"]
page = st.sidebar.radio("Page", PAGES, key="nav", label_visibility="collapsed")
st.sidebar.markdown("### Filters")
reg = st.sidebar.multiselect("Region", sorted(df_all.region.unique()), default=sorted(df_all.region.unique()))
chn = st.sidebar.multiselect("Channel", sorted(df_all.channel.unique()), default=sorted(df_all.channel.unique()))
col = st.sidebar.multiselect("Collection", sorted(df_all.collection.unique()), default=sorted(df_all.collection.unique()))
yrs = st.sidebar.multiselect("Year (analysis pages)", sorted(df_all.year.unique()), default=sorted(df_all.year.unique()))
st.sidebar.markdown(f"<div class='note'>{len(df_all):,} sales rows in database<br>"
                    f"Data up to {df_all.sale_date.max():%d %b %Y}</div>", unsafe_allow_html=True)

f_scope = df_all[df_all.region.isin(reg) & df_all.channel.isin(chn) & df_all.collection.isin(col)]
f = f_scope[f_scope.year.isin(yrs)]
if f_scope.empty:
    st.warning("No data for these filters."); st.stop()

# ------------------------------------------------------------------ PAGE 1: command center
def page_command():
    k = E.kpis(f)
    yoy = k["yoy"]
    cards([kpi("Watches sold", f"{k['units']:,}", "complete months only"),
           kpi("Revenue", inr(k["revenue"]), "after discounts"),
           kpi("Avg discount", f"{k['avg_disc']:.1f}%", "unit-weighted"),
           kpi("Growth (last 12m)", "n/a" if yoy is None else f"{yoy:+.1%}",
               "units vs previous 12 months", "" if yoy is None else ("up" if yoy >= 0 else "down")),
           kpi("Best collection", k["best"], f"{k['best_share']:.0%} of units")])

    sec("Model showcase: best sellers")
    showcase(best_seller_items(f[f.complete]), "BEST-SELLING MODELS")

    sec("Auto-generated insights")
    for t in E.insights(f):
        st.markdown(f"<div class='insight'>{t}</div>", unsafe_allow_html=True)

    m = E.monthly_series(f)
    a, b = st.columns([2, 1])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m.month, y=m.units, name="Units sold", mode="lines", fill="tozeroy",
                             line=dict(color=NAVY, width=2.4), fillcolor="rgba(10,31,92,.08)"))
    fig.add_trace(go.Scatter(x=m.month, y=m.units.rolling(3).mean(), name="3-month average",
                             line=dict(color=SKY, width=2, dash="dot")))
    fig.update_layout(title="Watches sold per month")
    with a:
        show(style(fig))
    y = E.yearly(f)
    fig = go.Figure(go.Bar(x=y.year.astype(str), y=y.units, marker_color=NAVY, customdata=y.months,
                           text=[f"{u:,.0f}" for u in y.units], textposition="outside",
                           hovertemplate="%{x}: %{y:,} units (%{customdata} months)<extra></extra>"))
    fig.update_layout(title="Units by year (partial years have fewer months)")
    with b:
        show(style(fig))

    d = f[f.complete]
    a, b = st.columns(2)
    piv = d.pivot_table(index="year", columns="month_no", values="units", aggfunc="sum").reindex(columns=range(1, 13))
    fig = go.Figure(go.Heatmap(z=piv.values, x=E.MONTHS, y=piv.index.astype(str), xgap=3, ygap=3,
                               colorscale=ICE, hoverongaps=False,
                               texttemplate="%{z:,.0f}", colorbar=dict(title="Units")))
    fig.update_layout(title="Seasonality heatmap - when do watches sell?")
    with a:
        show(style(fig, 360))
    g = (d.assign(dxu=d.discount_pct * d.units).groupby(["collection", "strap"])
           .agg(units=("units", "sum"), dxu=("dxu", "sum")).reset_index())
    g["avg_disc"] = g.dxu / g.units
    fig = px.treemap(g, path=[px.Constant("Titan"), "collection", "strap"], values="units", color="avg_disc",
                     color_continuous_scale=[[0, "#DCE6FA"], [1, NAVY]])
    fig.update_layout(title="Collection × strap (size = units, colour = avg discount)",
                      coloraxis_colorbar=dict(title="Disc %"))
    with b:
        show(style(fig, 360))

# ------------------------------------------------------------------ PAGE 2: deep dive
def page_deep():
    d = f[f.complete]
    t1, t2, t3, t4 = st.tabs(["Collections", "Geography & channel", "Price & customer", "Top models"])
    with t1:
        c = d.groupby("collection").units.sum().sort_values()
        a, b = st.columns(2)
        fig = go.Figure(go.Bar(x=c.values, y=c.index, orientation="h", marker_color=NAVY,
                               text=[f"{v:,}" for v in c.values], textposition="outside"))
        fig.update_layout(title="Units by collection")
        with a:
            show(style(fig, 420))
        s = d.groupby(["year", "collection"]).units.sum().reset_index()
        fig = px.area(s, x="year", y="units", color="collection", groupnorm="percent")
        fig.update_layout(title="Collection share over time (%)")
        with b:
            show(style(fig, 420))
    with t2:
        a, b = st.columns(2)
        c = d.groupby(["city", "region"]).units.sum().reset_index().sort_values("units")
        fig = px.bar(c, x="units", y="city", color="region", orientation="h")
        fig.update_layout(title="Units by city")
        with a:
            show(style(fig, 420))
        ch = d.groupby("channel").units.sum().reset_index()
        fig = go.Figure(go.Pie(labels=ch.channel, values=ch.units, hole=.62,
                               marker=dict(colors=[NAVY, SKY, GOLD], line=dict(color="#FFFFFF", width=3))))
        fig.update_layout(title="Channel mix")
        with b:
            show(style(fig, 420))
        p = d.pivot_table(index="city", columns="collection", values="units", aggfunc="sum")
        fig = go.Figure(go.Heatmap(z=p.values, x=p.columns, y=p.index, colorscale=ICE,
                                   xgap=2, ygap=2))
        fig.update_layout(title="City × collection - where does each line win?")
        show(style(fig, 420))
    with t3:
        a, b, c = st.columns(3)
        pb = d.groupby("price_band", observed=True).units.sum().reindex(E.PRICE_LABELS)
        fig = go.Figure(go.Bar(x=pb.index, y=pb.values, marker_color=NAVY))
        fig.update_layout(title="Units by price band")
        with a:
            show(style(fig, 340))
        gd = d.groupby("gender").units.sum().reset_index()
        fig = go.Figure(go.Pie(labels=gd.gender, values=gd.units, hole=.6,
                               marker=dict(colors=[NAVY, SKY, GOLD], line=dict(color="#FFFFFF", width=3))))
        fig.update_layout(title="Men / Women / Unisex")
        with b:
            show(style(fig, 340))
        db = d.groupby("disc_band", observed=True).units.mean().reindex(E.DISC_LABELS)
        fig = go.Figure(go.Bar(x=db.index, y=db.values, marker_color=SKY, text=[f"{v:.2f}" for v in db.values],
                               textposition="outside"))
        fig.update_layout(title="Watches per sale by discount band")
        with c:
            show(style(fig, 340))
        stp = d.groupby("strap").units.sum().reset_index()
        mv = d.groupby("movement").units.sum().reset_index()
        a, b = st.columns(2)
        fig = go.Figure(go.Bar(x=stp.strap, y=stp.units, marker_color=ROYAL)); fig.update_layout(title="Strap type")
        with a:
            show(style(fig, 300))
        fig = go.Figure(go.Bar(x=mv.movement, y=mv.units, marker_color=RED)); fig.update_layout(title="Movement type")
        with b:
            show(style(fig, 300))
    with t4:
        tm = d.groupby(["model_name", "collection"]).agg(units=("units", "sum"), revenue=("revenue", "sum"),
                                                         mrp=("mrp", "first"), rating=("avg_rating", "first")
                                                         ).reset_index().sort_values("units", ascending=False).head(20)
        table(tm.rename(columns={"model_name": "Model", "collection": "Collection", "units": "Units",
                                 "revenue": "Revenue", "mrp": "MRP", "rating": "Rating"}),
              column_config={"Units": st.column_config.ProgressColumn("Units", min_value=0,
                                                                      max_value=int(tm.units.max()), format="%d"),
                             "Revenue": st.column_config.NumberColumn(format="₹%.0f"),
                             "MRP": st.column_config.NumberColumn(format="₹%.0f"),
                             "Rating": st.column_config.NumberColumn(format="%.2f ⭐")})

# ------------------------------------------------------------------ shared model fit
def get_fit():
    m = E.monthly_series(f_scope)
    if len(m) < 30:
        st.warning("Forecasting needs at least 30 months of history. Widen the filters.")
        return None, None
    if m.units.mean() < 250:
        st.warning("This segment sells few watches per month, so forecasts here are rough. "
                   "Broaden Region / Channel / Collection for a steadier model.")
    return m, E.fit_model(m)

# ------------------------------------------------------------------ PAGE 3: forecast
def page_forecast():
    m, fit = get_fit()
    if fit is None:
        return
    c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.2, 1.1])
    horizon = c1.select_slider("Forecast horizon", options=[6, 12, 18, 24, 36, 48, 60], value=24,
                               format_func=lambda x: f"{x} mo" if x < 12 else f"{x} mo ({x/12:g} yr)")
    growth = c2.select_slider("Market growth", options=list(GROWTH), value="Model trend")
    margin = c3.slider("Gross margin at MRP (%)", 20, 70, 50, 5) / 100
    strategy = c4.radio("Discount strategy", ["Historical pattern", "Flat discount", "Festive boost"], key="strategy")
    if strategy == "Flat discount":
        plan = E.plan_flat(st.slider("Discount on every sale (%)", 0, 40, 10))
    elif strategy == "Festive boost":
        x1, x2 = st.columns(2)
        plan = E.plan_festive(x1.slider("Regular-month discount (%)", 0, 40, 8),
                              x2.slider("Extra discount in Oct-Nov festive months (%)", 0, 25, 10))
    else:
        plan = E.plan_history(fit)

    base = E.forecast(fit, horizon, E.plan_history(fit), 1.0, margin)
    scn = E.forecast(fit, horizon, plan, GROWTH[growth], margin)
    mape, bt = E.backtest(m)
    n = min(12, horizon)
    nxt = scn.head(n)
    prev_idx = pd.DatetimeIndex(nxt.month) - pd.DateOffset(years=1)
    prev = m.set_index("month").units.reindex(prev_idx)
    vs_ly = None if prev.isna().any() else nxt.units.sum() / prev.sum() - 1
    dbase = nxt.units.sum() - base.head(n).units.sum()
    cards([kpi(f"Watches - next {n} months", f"{nxt.units.sum():,.0f}",
               "vs same months last year: n/a" if vs_ly is None else f"{vs_ly:+.1%} vs same months last year",
               "" if vs_ly is None else ("up" if vs_ly >= 0 else "down")),
           kpi("Revenue", inr(nxt.revenue.sum()), f"avg discount {nxt.disc.mean():.1f}%"),
           kpi("Gross profit", inr(nxt.profit.sum()), f"at {margin:.0%} margin on MRP"),
           kpi("vs 'business as usual'", f"{dbase:+,.0f} units", "scenario minus historical plan",
               "up" if dbase >= 0 else "down"),
           kpi("Model accuracy", f"{1-mape:.1%}", f"6-month backtest error {mape:.1%}")])

    hist = m.tail(36)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.month, y=hist.units, name="Actual", line=dict(color=NAVY, width=2.6)))
    fig.add_trace(go.Scatter(x=scn.month, y=scn.high, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=scn.month, y=scn.low, fill="tonexty", fillcolor="rgba(111,155,242,.22)",
                             line=dict(width=0), name="80% range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[hist.month.iloc[-1]] + list(base.month), y=[hist.units.iloc[-1]] + list(base.units),
                             name="Business as usual", line=dict(color=GREY, width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=[hist.month.iloc[-1]] + list(scn.month), y=[hist.units.iloc[-1]] + list(scn.units),
                             name="Your scenario", line=dict(color=SKY, width=3)))
    fig.add_shape(type="line", x0=hist.month.iloc[-1], x1=hist.month.iloc[-1], y0=0, y1=1, yref="paper",
                  line=dict(color=GREY, width=1, dash="dot"))
    fig.add_annotation(x=hist.month.iloc[-1], y=1, yref="paper", text="today", showarrow=False,
                       font=dict(color=GREY), xanchor="right")
    fig.update_layout(title="Monthly watches sold - actual vs forecast", hovermode="x unified")
    show(style(fig, 430))

    sec("Model showcase: predicted sales")
    showcase(forecast_items(f_scope, nxt), "FORECAST BY MODEL", 700)
    st.markdown("<div class='note'>Model-level numbers split the overall forecast by each model's share of the last 12 months of sales.</div>", unsafe_allow_html=True)

    sec("Year-by-year outlook")
    ao = E.annual_outlook(m, scn, fit["avg_mrp"] * (1 - margin))
    a, b = st.columns([1, 1])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=ao.year.astype(str), y=ao.units_actual, name="Actual", marker_color=NAVY))
    fig.add_trace(go.Bar(x=ao.year.astype(str), y=ao.units_forecast, name="Forecast", marker_color=SKY))
    fig.update_layout(barmode="stack", title="Units per calendar year")
    with a:
        show(style(fig, 340))
    disp = pd.DataFrame({"Year": ao.year, "Months (forecast)": [f"{r.months} ({r.fmonths})" for r in ao.itertuples()],
                         "Units": ao.units.round(0).astype(int), "Revenue (₹ Cr)": (ao.revenue / 1e7).round(2),
                         "Profit (₹ Cr)": (ao.profit / 1e7).round(2), "Avg discount %": ao.avg_disc.round(1)})
    with b:
        table(disp)
    st.markdown("<div class='note'>Years with fewer than 12 months are partial. Method: log-linear model with trend, "
                "month-of-year seasonality and discount elasticity, fitted on your monthly history. Forecast bands "
                "widen the further out you look, so treat multi-year numbers as scenarios, not promises.</div>",
                unsafe_allow_html=True)
    with st.expander("How reliable is the model? (backtest on the last 6 months)"):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bt.month, y=bt.actual, name="Actual", line=dict(color=NAVY, width=3)))
        fig.add_trace(go.Scatter(x=bt.month, y=bt.predicted, name="Predicted", line=dict(color=SKY, dash="dot", width=3)))
        show(style(fig, 300))
        st.write(f"Average error **{mape:.1%}**. Learned trend **{fit['annual_growth']:+.1%} per year**, "
                 f"discount effect **{(np.exp(fit['b'])-1):+.1%} units per +1 pp discount**.")
    st.download_button("⬇ Download forecast (CSV)", scn.assign(month=scn.month.dt.strftime("%Y-%m")).round(2).to_csv(index=False).encode(),
                       "titan_forecast.csv", "text/csv")

# ------------------------------------------------------------------ PAGE 4: discount lab
def page_lab():
    m, fit = get_fit()
    if fit is None:
        return
    c1, c2 = st.columns(2)
    mn = c1.selectbox("Calendar month to optimise", list(range(1, 13)), index=10,
                      format_func=lambda x: calendar.month_name[x])
    margin = c2.slider("Gross margin at MRP (%)", 20, 70, 50, 5, key="lab_margin") / 100
    d0 = float(fit["disc_by_month"][mn - 1])
    cur = E.discount_curve(fit, mn, margin)
    opt = cur.loc[cur.profit.idxmax()]
    now = E.discount_curve(fit, mn, margin, [d0]).iloc[0]
    uplift = opt.profit / now.profit - 1
    cards([kpi("Discount elasticity", f"{np.exp(fit['b'])-1:+.1%}", "units for every +1 pp discount"),
           kpi("Typical discount", f"{d0:.1f}%", f"historical average for {calendar.month_abbr[mn]}"),
           kpi("Profit-maximising discount", f"{opt.discount:.0f}%",
               f"{opt.units:,.0f} watches expected"),
           kpi("Profit vs typical plan", f"{uplift:+.1%}", f"{inr(opt.profit - now.profit)} extra profit",
               "up" if uplift >= 0 else "down")])

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=cur.discount, y=cur.units, name="Watches sold", line=dict(color=NAVY, width=3)),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=cur.discount, y=cur.revenue, name="Revenue", line=dict(color=SKY, width=2, dash="dot")),
                  secondary_y=True)
    fig.add_trace(go.Scatter(x=cur.discount, y=cur.profit, name="Profit", line=dict(color=GOLD, width=3)),
                  secondary_y=True)
    fig.add_trace(go.Scatter(x=[opt.discount], y=[opt.profit], mode="markers", name="Profit peak",
                             marker=dict(size=15, symbol="diamond", color=NAVY, line=dict(width=2, color="#FFFFFF"))),
                  secondary_y=True)
    fig.update_xaxes(title="Discount (%)")
    fig.update_yaxes(title="Watches", secondary_y=False)
    fig.update_yaxes(title="₹", secondary_y=True, showgrid=False)
    fig.update_layout(title=f"Discount curve for {calendar.month_name[mn]} - more discount sells more, but profit peaks earlier")
    show(style(fig, 420))

    sec("What-if calculator")
    x = st.slider("Try a discount (%)", 0, 40, int(round(d0)))
    w = E.discount_curve(fit, mn, margin, [x]).iloc[0]
    cards([kpi("Watches", f"{w.units:,.0f}", f"{w.units/now.units-1:+.1%} vs typical plan"),
           kpi("Revenue", inr(w.revenue), f"{w.revenue/now.revenue-1:+.1%}"),
           kpi("Profit", inr(w.profit), f"{w.profit/now.profit-1:+.1%}", "up" if w.profit >= now.profit else "down")])

    sec("Demand map: discount × month")
    mat = E.units_matrix(fit)
    fig = go.Figure(go.Heatmap(z=mat.values, x=list(mat.columns), y=[f"{i}%" for i in mat.index], xgap=2, ygap=2,
                               colorscale=ICE, texttemplate="%{z:,.0f}",
                               colorbar=dict(title="Units")))
    fig.update_layout(title="Expected watches sold next year, by month and discount level")
    show(style(fig, 420))

# ------------------------------------------------------------------ PAGE 5: data manager
def page_data():
    t1, t2, t3, t4 = st.tabs(["Add a sale", "Bulk CSV upload", "SQL explorer", "Database schema"])
    prods, stores = E.q("SELECT * FROM products"), E.q("SELECT * FROM stores")
    with t1:
        with st.form("new_sale"):
            p = st.selectbox("Product", prods.model_name)
            s = st.selectbox("Store", stores.apply(lambda r: f"{r.store_id} · {r.city} · {r.channel}", axis=1))
            d = st.date_input("Date")
            qty = st.number_input("Quantity", 1, 50, 1)
            disc = st.selectbox("Discount %", [0, 5, 10, 15, 20, 25, 30, 40])
            if st.form_submit_button("Save sale"):
                E.add_sale(int(prods[prods.model_name == p].product_id.iloc[0]), int(s.split(" · ")[0]), d, qty, disc)
                st.cache_data.clear()
                st.success("Saved. Every chart and the forecast now include this sale.")
    with t2:
        st.write("Upload a CSV with columns: `product_id, store_id, sale_date, quantity, discount_pct`.")
        tmpl = pd.DataFrame({"product_id": [1, 2], "store_id": [1, 5], "sale_date": ["2026-10-25", "2026-10-26"],
                             "quantity": [1, 2], "discount_pct": [10, 15]})
        st.download_button("Download template", tmpl.to_csv(index=False).encode(), "sales_template.csv", "text/csv")
        up = st.file_uploader("CSV file", type="csv")
        if up is not None:
            try:
                new = pd.read_csv(up)
                st.write(f"Preview ({len(new)} rows)")
                table(new.head(10))
                if st.button("Import into database"):
                    n = E.import_sales_csv(new)
                    st.cache_data.clear()
                    st.success(f"Imported {n} rows.")
            except Exception as e:
                st.error(str(e))
    with t3:
        st.write("Tables: `products`, `stores`, `sales`, `reviews`. Read-only; one SELECT at a time.")
        sql = st.text_area("SQL", "SELECT p.collection, SUM(s.quantity) AS units, ROUND(AVG(s.discount_pct),1) AS avg_disc\n"
                                  "FROM sales s JOIN products p ON p.product_id = s.product_id\n"
                                  "GROUP BY p.collection ORDER BY units DESC;", height=140)
        if st.button("Run query"):
            try:
                table(E.run_readonly(sql))
            except Exception as e:
                st.error(str(e))
    with t4:
        st.code(open(E.os.path.join(E.HERE, "schema.sql")).read(), language="sql")

{"Command Center": page_command, "Sales Deep-Dive": page_deep, "Future Forecast": page_forecast,
 "Discount Lab": page_lab, "Data Manager": page_data}[page]()
