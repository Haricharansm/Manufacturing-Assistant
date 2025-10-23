
import pandas as pd
from pathlib import Path
DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
def load_csv(name:str)->pd.DataFrame:
    df = pd.read_csv(DATA_DIR / f"{name}.csv")
    for col in df.columns:
        if any(tag in col.lower() for tag in ['date','start','end','planned']):
            df[col] = pd.to_datetime(df[col])
    return df
def load_all_data():
    return (load_csv('orders'),
            load_csv('quality_inspections'),
            load_csv('downtime_log'),
            load_csv('inventory'),
            load_csv('work_orders'))
