from .base import BaseAdapter
class SupplierNet(BaseAdapter):
    def alternate_supplier(self, sku:str): return {'sku':sku,'alt_supplier':'Supplier Y','available_qty':500,'eta_days':2}
