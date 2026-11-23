import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))


def params():
    return yaml.safe_load((RAIZ / "config" / "parametros.yaml").read_text(encoding="utf-8"))
