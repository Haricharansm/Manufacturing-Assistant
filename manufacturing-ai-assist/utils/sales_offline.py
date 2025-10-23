# utils/sales_offline.py
from __future__ import annotations
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import math, random

DATA = Path(__file__).resolve().parents[1] / "data"

def _csv(name: str) -> pd.DataFrame:
    df = pd.read_csv(DATA / name)
    for c in df.columns:
        if "date" in c.lower():
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def load_bom() -> pd.DataFrame:
    return _csv("bom.csv")

def load_products() -> pd.DataFrame:
    return _csv("products.csv")

def load_prospects() -> pd.DataFrame:
    return _csv("prospects.csv")

def price_from_bom(assembly: str, qty: int, margin_pct: float = 22.0) -> dict:
    bom = load_bom()
    items = bom[bom["assembly"] == assembly].copy()
    if items.empty:
        raise ValueError(f"BOM not found for '{assembly}'")
    items["extended"] = items["qty_per"] * qty * items["unit_cost"]
    material_cost = float(items["extended"].sum())
    std_cost = float(items["std_cost"].sum() * qty)
    base_cost = material_cost + std_cost
    price = base_cost * (1 + margin_pct/100.0)
    lead_time_days = math.ceil(items["lead_time_days"].max())
    return {
        "assembly": assembly,
        "qty": int(qty),
        "material_cost": round(material_cost, 2),
        "std_cost": round(std_cost, 2),
        "base_cost": round(base_cost, 2),
        "margin_pct": margin_pct,
        "price": round(price, 2),
        "lead_time_days": int(lead_time_days),
        "line_items": items[["part","desc","qty_per","unit_cost","extended"]].to_dict("records"),
    }

def generate_quote(assembly: str, qty: int, prospect: str = "ACME Mfg", terms: str = "Net 30") -> dict:
    q = price_from_bom(assembly, qty)
    quote_id = f"Q-{int(datetime.utcnow().timestamp())}"
    ship_eta = (datetime.utcnow() + timedelta(days=q["lead_time_days"])).date()
    body = (
        f"**Quote {quote_id}**\n\n"
        f"- Customer: **{prospect}**\n"
        f"- Item: **{assembly}**  • Qty: **{qty}**\n"
        f"- Price: **${q['price']:,}**  (margin {q['margin_pct']}%)\n"
        f"- Est. ship date: **{ship_eta}**\n"
        f"- Terms: {terms}\n\n"
        f"**Cost breakdown**  \n"
        f"- Material: ${q['material_cost']:,}  \n"
        f"- Std cost: ${q['std_cost']:,}  \n"
        f"- Base cost: ${q['base_cost']:,}\n"
    )
    return {"quote_id": quote_id, "ship_eta": str(ship_eta), "body": body, "rollup": q}

def follow_up_email(prospect: str, quote_id: str, tone: str = "crisp") -> str:
    openers = {
        "crisp": f"Checking in on quote {quote_id} —",
        "warm": f"Following up on quote {quote_id}.",
        "friendly": f"Hope you’re well! Re: quote {quote_id} —",
    }
    opener = openers.get(tone, openers["crisp"])
    nudge = random.choice([
        "we can hold this price through Friday.",
        "we’ve reserved capacity on L2 if you’re ready.",
        "we can include a sample with the first lot.",
    ])
    return (
        f"{opener}\n\n"
        f"Happy to answer any questions or adjust quantities. "
        f"If timing is critical, we can pull ship in by ~2 days.\n\n"
        f"FYI: {nudge}\n\n"
        f"Best,\nSales — Manufacturing AI Assist"
    )

def propose_new_product(assembly: str) -> str:
    p = load_products()
    row = p[p["sku"] == assembly]
    if row.empty:
        return "I don’t see this item in the catalog yet."
    fam = row.iloc[0]["family"]
    peers = p[(p["family"] == fam) & (p["sku"] != assembly)].sort_values("recent_demand", ascending=False).head(2)
    if peers.empty:
        return "No related products to suggest."
    bullets = "\n".join([f"- **{r.sku}** — {r.desc}  (90d demand: {int(r.recent_demand)})" for _, r in peers.iterrows()])
    return f"Based on interest in **{assembly}**, consider:\n{bullets}\n\nHappy to include an alt-line in the quote."
