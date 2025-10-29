# manufacturing-ai-assist/utils/search.py
# -*- coding: utf-8 -*-
import pandas as pd
from typing import Dict, Tuple

def search_sales(q: str, dfs: Dict[str, pd.DataFrame]) -> Tuple[str, pd.DataFrame]:
    ql = q.lower()
    if "bom" in ql or "assy" in ql:
        df = dfs["inv"]
        mask = df["sku"].str.contains("ASSY|KIT|COMP", case=False, regex=True)
        return ("BOM / Catalog", df[mask].head(50))
    if "quote" in ql or "customer" in ql:
        df = dfs["orders"]
        cols = [c for c in df.columns if c in ("customer","status","sku","qty","created_at")]
        return ("Quotes", df[cols].head(50))
    return ("Sales search", dfs["orders"].head(50))

def search_sc(q: str, dfs: Dict[str, pd.DataFrame]) -> Tuple[str, pd.DataFrame]:
    ql = q.lower()
    if "sku-" in ql:
        sku = q.upper().split()[-1]
        df = dfs["inv"]
        return (f"Inventory for {sku}", df[df["sku"]==sku])
    if "po" in ql:
        df = dfs.get("pos", dfs["orders"])
        return ("Open POs", df.head(50))
    return ("Supply chain search", dfs["inv"].head(50))

def search_plant(q: str, dfs: Dict[str, pd.DataFrame]) -> Tuple[str, pd.DataFrame]:
    ql = q.lower()
    if "downtime" in ql or "line" in ql:
        df = dfs["down"]
        return ("Downtime by line", df.groupby("line")["minutes"].sum().reset_index().sort_values("minutes", ascending=False))
    if "defect" in ql or "spc" in ql:
        df = dfs["quality"]
        return ("Defects by family", df.groupby("defect_family").size().reset_index(name="count").sort_values("count", ascending=False))
    return ("Plant search", dfs["down"].head(50))
