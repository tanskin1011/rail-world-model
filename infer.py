"""Repository entry point; no installation required."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from rail_world_model.infer_cli import main

if __name__ == '__main__':
    main()
