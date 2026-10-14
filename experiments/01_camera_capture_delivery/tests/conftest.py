import sys
from pathlib import Path

# the host modules import each other by file name; fake_phone is shared with open_vio and src/live tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
