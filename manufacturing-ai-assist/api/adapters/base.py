class AdapterError(Exception): pass
class BaseAdapter:
    def __init__(self, **kwargs): self.config = kwargs
    def ping(self): return True
