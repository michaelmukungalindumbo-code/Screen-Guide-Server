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
class Request:   # v0.84 (/ads/ssv reads the raw query string): tests build one with the query they want
    def __init__(self, query=""):
        class _U: pass
        self.url = _U(); self.url.query = query
