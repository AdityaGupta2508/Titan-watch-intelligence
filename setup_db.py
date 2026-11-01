"""Builds titan.db and fills it with SYNTHETIC Titan-style watch sales (4 years).
Swap the generator for your real data any time:
    pd.read_csv("real_sales.csv").to_sql("sales", conn, if_exists="append", index=False)
Run:  python setup_db.py      (re-running resets the database)
"""
import os, sqlite3, random
from datetime import date, timedelta
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "titan.db")
random.seed(42); np.random.seed(42)

COLLECTIONS = {  # name: (base MRP, gender, movement)
    "Raga": (6500, "Women", "Analog"), "Edge": (11000, "Men", "Analog"),
    "Nebula": (45000, "Men", "Analog"), "Karishma": (2800, "Unisex", "Analog"),
    "Octane": (7500, "Men", "Analog"), "Regalia": (9500, "Women", "Analog"),
    "Neo": (3500, "Men", "Analog"), "Smart": (5500, "Unisex", "Smart"),
    "Automatic": (18000, "Men", "Automatic"),
}
STRAPS = ["Leather", "Metal", "Silicone"]
CITIES = [("Mumbai", "West"), ("Delhi", "North"), ("Bengaluru", "South"), ("Chennai", "South"),
          ("Kolkata", "East"), ("Pune", "West"), ("Hyderabad", "South"), ("Jaipur", "North"),
          ("Ahmedabad", "West"), ("Lucknow", "North")]
CHANNELS = ["World of Titan", "Mall", "Online"]
SEASON = {1: .9, 2: .95, 3: .9, 4: .85, 5: .9, 6: .8, 7: .85, 8: 1.0, 9: 1.0, 10: 1.5, 11: 1.6, 12: 1.25}

def main():
    conn = sqlite3.connect(DB)
    conn.executescript(open(os.path.join(HERE, "schema.sql")).read())
    conn.executescript("DELETE FROM reviews; DELETE FROM sales; DELETE FROM stores; DELETE FROM products;")

    products, pid = [], 1
    for coll, (base, gender, mov) in COLLECTIONS.items():
        for strap in STRAPS:
            mrp = round(base * random.uniform(.85, 1.2) / 50) * 50
            products.append((pid, f"{coll} {strap[:3].upper()}-{pid:02d}", coll, gender, strap, mov, mrp,
                             random.randint(2016, 2025)))
            pid += 1
    conn.executemany("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)", products)

    stores, sid = [], 1
    for city, region in CITIES:
        for ch in CHANNELS:
            stores.append((sid, city, region, ch)); sid += 1
    conn.executemany("INSERT INTO stores VALUES (?,?,?,?)", stores)

    start, end = date(2022, 11, 1), date(2026, 10, 24)
    span = (end - start).days
    campaign, rows, d = {}, [], start
    while d <= end:
        key = (d.year, d.month)
        if key not in campaign:   # each month runs a discount campaign -> lets the model learn elasticity
            campaign[key] = random.choice([5, 8, 10, 12, 15, 18, 20]) + (5 if d.month in (10, 11) else 0)
        camp = campaign[key]
        trend = 1 + 0.30 * ((d - start).days / span)
        n_tx = int(np.random.poisson(14 * SEASON[d.month] * trend * (1 + 0.02 * (camp - 12))))
        for _ in range(n_tx):
            p, s = random.choice(products), random.choice(stores)
            disc = max(0, camp + random.choice([-5, 0, 0, 5]))
            price = round(p[6] * (1 - disc / 100), 2)
            lam = max(.3, 1.6 - p[6] / 30000 + disc / 50 + (.3 if s[3] == "Online" else 0))
            qty = max(1, int(np.random.poisson(lam)))
            rows.append((p[0], s[0], d.isoformat(), qty, disc, price, round(price * qty, 2)))
        d += timedelta(days=1)
    conn.executemany("INSERT INTO sales(product_id,store_id,sale_date,quantity,discount_pct,selling_price,revenue) "
                     "VALUES (?,?,?,?,?,?,?)", rows)

    rv = [(p[0], int(np.clip(np.random.normal(4.1, .8), 1, 5)),
           (start + timedelta(days=random.randint(0, span))).isoformat())
          for p in products for _ in range(60)]
    conn.executemany("INSERT INTO reviews(product_id,rating,review_date) VALUES (?,?,?)", rv)
    conn.commit(); conn.close()
    print(f"titan.db ready: {len(products)} products, {len(stores)} stores, {len(rows):,} sales rows")

if __name__ == "__main__":
    main()
