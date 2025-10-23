from .base import BaseAdapter
class WMS(BaseAdapter):
    def get_asn(self, supplier:str, sku:str): return {'supplier':supplier,'sku':sku,'eta_days':4,'status':'DELAYED'}
