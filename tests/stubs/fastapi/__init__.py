class HTTPException(Exception):
    def __init__(self, status_code, detail=""):
        super().__init__(detail); self.status_code = status_code; self.detail = detail
def Header(default=""): return default
class FastAPI:
    def __init__(self, **k): pass
    def get(self, *a, **k): return lambda f: f
    def post(self, *a, **k): return lambda f: f
    def put(self, *a, **k): return lambda f: f
    def delete(self, *a, **k): return lambda f: f
    def middleware(self, *a, **k): return lambda f: f
    def exception_handler(self, *a, **k): return lambda f: f
    routes = []
