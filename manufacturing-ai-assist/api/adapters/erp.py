from .base import BaseAdapter
class DynamicsERP(BaseAdapter):
    def get_inventory(self, sku:str): return {'sku':sku,'on_hand':1200,'safety_stock':800,'open_pos':2,'lead_time_days':7}
    def create_po(self, sku:str, qty:int, supplier:str, expedite:bool=False): return {'status':'CREATED','po_id':'PO-DYN-001','sku':sku,'qty':qty,'supplier':supplier,'expedite':expedite}
class SAPERP(BaseAdapter):
    def get_inventory(self, sku:str): return {'sku':sku,'on_hand':1150,'safety_stock':900,'open_pos':1,'lead_time_days':9}
    def create_po(self, sku:str, qty:int, supplier:str, expedite:bool=False): return {'status':'CREATED','po_id':'PO-SAP-001','sku':sku,'qty':qty,'supplier':supplier,'expedite':expedite}

def make_erp(kind:str, **cfg)->BaseAdapter:
    if (kind or '').upper().startswith('SAP'): return SAPERP(**cfg)
    return DynamicsERP(**cfg)
