"""Entry point: `uvicorn booking.main:app --app-dir src --reload`"""
from .api import create_app

app = create_app()
