import argparse
import json
from pathlib import Path
from .contracts import validate_action
from .actions import PROFILES,straight_action


def main():
    parser = argparse.ArgumentParser(description="Rail world-model CPU tools")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate-action")
    check.add_argument("path", type=Path)
    check.add_argument("--transitions", type=int, default=188)
    make = sub.add_parser("make-action",help="Explanatory straight plan, not pose GT")
    make.add_argument("--profile",choices=PROFILES,required=True)
    make.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    if args.command == "make-action":
        action=straight_action(args.profile)
        with args.output.open("x") as stream:
            json.dump(action,stream,indent=2)
        result={"path":str(args.output),"shape":[188,9],"source":"mathematical_camera_plan_not_pose_GT","profile":args.profile,"fps":24}
    else:
        result = validate_action(json.loads(args.path.read_text()), args.transitions)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
