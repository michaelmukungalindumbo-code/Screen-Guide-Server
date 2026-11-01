class HTMLResponse:
    def __init__(self, content="", status_code=200): self.body = content; self.status_code = status_code
class JSONResponse:
    def __init__(self, content=None, status_code=200): self.body = content; self.status_code = status_code
