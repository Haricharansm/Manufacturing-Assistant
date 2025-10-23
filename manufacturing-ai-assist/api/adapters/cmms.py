from .base import BaseAdapter
class CMMS(BaseAdapter):
    def create_work_order(self, asset:str, desc:str): return {'status':'CREATED','wo':'CMMS-1234','asset':asset,'desc':desc}
