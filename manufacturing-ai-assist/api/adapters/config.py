import os
class Settings:
    ERP_KIND=os.getenv('ERP_KIND','DYNAMICS')
    ERP_URL=os.getenv('ERP_URL','')
    ERP_API_KEY=os.getenv('ERP_API_KEY','')
    WMS_URL=os.getenv('WMS_URL','')
    WMS_API_KEY=os.getenv('WMS_API_KEY','')
    CMMS_URL=os.getenv('CMMS_URL','')
    CMMS_API_KEY=os.getenv('CMMS_API_KEY','')
    SUPPLIER_URL=os.getenv('SUPPLIER_URL','')
    SUPPLIER_API_KEY=os.getenv('SUPPLIER_API_KEY','')
settings=Settings()
