# manufacturing-ai-assist/utils/nudges.py
# -*- coding: utf-8 -*-
import pandas as pd
from typing import List, Dict

def sales_nudges(df_orders: pd.DataFrame, df_inv: pd.DataFrame) -> List[Dict]:
    nudges = []

    # Stale quotes (mock: orders with status 'Quoted' older than 3 days)
    if "status" in df_orders and "created_at" in df_orders:
        stale = df_orders[(df_orders["status"]=="Quoted") & (pd.Timestamp.today()-pd.to_datetime(df_orders["created_at"])>pd.Timedelta(days=3))]
        if len(stale) > 0:
            nudges.append({
                "title": f"{len(stale)} stale quote(s)",
                "body": "Suggest: send a friendly follow-up and set a 3-day reminder.",
                "action": {"type":"follow_up", "account": stale.iloc[0].get("customer","ACME Mfg")}
            })

    # Cross-sell suggestion based on popular assemblies
    nudges.append({
        "title": "Cross-sell opportunity",
        "body": "Customers who buy **ASSY-100** often add **KIT-19**. Offer a 5% bundle discount.",
        "action": {"type":"propose_xsell", "assembly":"ASSY-100"}
    })

    # Margin guard (mock)
    nudges.append({
        "title": "Margin guard",
        "body": "Recent quotes for **ASSY-100** fell below 20% margin. Propose price = cost × 1.22.",
        "action": {"type":"open_quote_wizard", "assembly":"ASSY-100", "qty":25}
    })

    return nudges

def sc_nudges(df_inv: pd.DataFrame) -> List[Dict]:
    nudges = []
    if "sku" in df_inv and "on_hand" in df_inv and "safety_stock" in df_inv:
        at_risk = df_inv[df_inv["on_hand"] < df_inv["safety_stock"]]
        if not at_risk.empty:
            sku = at_risk.iloc[0]["sku"]
            nudges.append({
                "title": f"{sku} below safety stock",
                "body": f"Replenish {sku}. Recommend **expedite PO** and evaluate **alternate supplier**.",
                "action": {"type":"sc_expedite_po", "sku": sku, "days_pull": 2}
            })
    nudges.append({
        "title": "Late ASNs detected",
        "body": "Two inbound shipments are late >24h. Suggest upgrading next leg to **air**.",
        "action": {"type":"sc_upgrade_carrier"}
    })
    return nudges

def plant_nudges(df_down: pd.DataFrame, df_quality: pd.DataFrame) -> List[Dict]:
    nudges = []
    if not df_down.empty and "line" in df_down and "minutes" in df_down:
        l2 = df_down[df_down["line"]=="L2"]["minutes"].sum()
        if l2 > 60:
            nudges.append({
                "title": "Changeovers driving downtime",
                "body": "Line L2 downtime >60m today. Recommend **batching changeovers** and **re-sequence L2**.",
                "action": {"type":"plant_batch_changeovers", "line":"L2"}
            })
    if not df_quality.empty and "defect_family" in df_quality:
        fam = df_quality["defect_family"].value_counts().idxmax()
        nudges.append({
            "title": "SPC breach risk",
            "body": f"Defects concentrated in **{fam}**. Fast-track QA for affected SKUs.",
            "action": {"type":"plant_qa_fast_track", "sku":"SKU-19"}
        })
    return nudges
