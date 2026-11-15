import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app import create_app

app = create_app("production")

# WSGI handler for Vercel
if __name__ == "__main__":
    app.run()
