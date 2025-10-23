
from textwrap import dedent
def draft_brief(persona:str, k:dict, note:str|None=None)->str:
    extras = f"\n**Note:** {note}" if note else ""
    return dedent(f"""
    **Persona:** {persona}

    **Snapshot**
    - Throughput: {k['throughput_per_day']:.0f} units/day
    - On-time Delivery: {k['on_time_pct']:.1f}%
    - Defect Rate: {k['defect_rate_pct']:.2f}%
    - Unplanned Downtime: {k['downtime_hours']:.1f} hrs
    - Inventory Risk Items: {k['inventory_risk_count']}

    **Highlights**
    - Throughput trend: {k['throughput_trend']}.
    - Top downtime cause: {k['top_downtime_cause']}.
    - Focus defect family: {k['top_defect_family']}.

    **Next Actions**
    - Re-sequence where feasible and batch changeovers.
    - Address {k['top_defect_family']} defects with a quick huddle.
    - Review {k['lowest_stock_sku']} vs safety stock.
    {extras}
    """)
