
import pandas as pd
def compute_kpis(df_orders, df_quality, df_down, df_inv):
    k = {}
    recent = df_orders[df_orders['order_date'] >= (df_orders['order_date'].max() - pd.Timedelta(days=6))]
    k['throughput_per_day'] = recent['qty_produced'].sum() / max(1,(recent['order_date'].nunique()))
    k['on_time_pct'] = (df_orders['actual_ship_date'] <= df_orders['promised_ship_date']).mean() * 100
    total_units = df_quality['units_inspected'].sum(); defects = df_quality['defects_found'].sum()
    k['defect_rate_pct'] = (defects/total_units*100) if total_units else 0.0
    down_recent = df_down[df_down['start'] >= (df_down['start'].max() - pd.Timedelta(days=6))]
    k['downtime_hours'] = down_recent['duration_min'].sum()/60.0
    k['inventory_risk_count'] = (df_inv['on_hand'] < df_inv['safety_stock']).sum()
    last3 = recent[recent['order_date'] >= (df_orders['order_date'].max() - pd.Timedelta(days=2))]['qty_produced'].mean()
    prev4 = recent[recent['order_date'] < (df_orders['order_date'].max() - pd.Timedelta(days=2))]['qty_produced'].mean()
    k['throughput_trend'] = 'up' if last3 > prev4 else 'down' if last3 < prev4 else 'flat'
    k['top_downtime_cause'] = df_down.groupby('cause')['duration_min'].sum().sort_values(ascending=False).head(1).index.to_list()[0]
    fam = df_quality.groupby('defect_family')['defects_found'].sum().sort_values(ascending=False).head(1).index.to_list()[0]
    k['top_defect_family'] = fam
    k['lowest_stock_sku'] = df_inv.sort_values('on_hand').head(1)['sku'].iloc[0]
    return k
