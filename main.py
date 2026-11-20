import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app, fastapi_app

if __name__ == "__main__":
    import uvicorn
    from app.config.settings import settings
    port = int(os.environ.get("PORT", settings.PORT or 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
