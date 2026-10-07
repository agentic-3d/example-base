"""Usage: uv run python tools/build.py <model>   (run from the project root)

Imports models/<model>.py and exports its `result` to out/<model>.stl.
"""
import importlib
import sys
from pathlib import Path

from build123d import export_stl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root, so `models` imports work

name = sys.argv[1]
result = importlib.import_module(f"models.{name}").result
Path("out").mkdir(exist_ok=True)
export_stl(result, f"out/{name}.stl", tolerance=0.01, angular_tolerance=0.1)
print(f"wrote out/{name}.stl")
