"""Entrypoint.

Local:   python wsgi.py
Container: gunicorn --bind 0.0.0.0:8000 --workers 2 --access-logfile - wsgi:app
"""
from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=False, threaded=True)
