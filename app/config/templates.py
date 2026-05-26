from pathlib import Path

from fastapi.templating import Jinja2Templates

# Absolute path so it works regardless of working directory
TEMPLATES_DIR = Path(__file__).parent.parent / "endpoint" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
