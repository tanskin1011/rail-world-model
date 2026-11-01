import argparse
import json
from pathlib import Path
from .contracts import validate_action


def main():
    parser = argparse.ArgumentParser(description="Rail world-model CPU tools")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate-action")
    check.add_argument("path", type=Path)
    check.add_argument("--transitions", type=int, default=188)
    args = parser.parse_args()
    result = validate_action(json.loads(args.path.read_text()), args.transitions)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
