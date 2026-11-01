import copy
class BaseModel:
    def __init__(self, **kw):
        for k, v in type(self).__dict__.items():
            if not k.startswith("_") and not callable(v): setattr(self, k, copy.deepcopy(v))
        for k, v in kw.items(): setattr(self, k, v)
