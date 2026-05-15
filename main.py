import argparse
import json
import logging
import sys
from pathlib import Path

from config import Config
# from verify import verify_advisors  # TODO: arxiv verify temporarily disabled
from feishu_writer import write_advisors
from mailer import send_emails


def _load_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array in {path}, got {type(data).__name__}")
    return data


def _save_json(data: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Orchestrate verify, write, and send phases.")
    parser.add_argument("json_path", help="Input JSON file path")
    # parser.add_argument("--verify", action="store_true", help="Only run arxiv verification")
    parser.add_argument("--write", action="store_true", help="Only run Feishu write")
    parser.add_argument("--send", action="store_true", help="Only run email send")
    parser.add_argument("--all", action="store_true", help="Run write -> send in sequence")
    parser.add_argument("--add", metavar="JSON", help="Append a new advisor entry (JSON string) and save")
    parser.add_argument("--dry-run", action="store_true", help="Preview mode, skip external calls")
    parser.add_argument("--output", default=None, help="Output JSON path (defaults to input file)")
    args = parser.parse_args()

    if not (args.add or args.write or args.send or args.all):
        parser.error("Must specify one of --add, --write, --send, or --all")

    data = _load_json(args.json_path)
    output_path = args.output or args.json_path

    if args.add:
        entry = json.loads(args.add)
        entry.setdefault("sent", False)
        entry.setdefault("verified", None)
        data.append(entry)
        _save_json(data, output_path)
        print(f"Appended advisor: {entry.get('name_zh', entry.get('name_en', 'unknown'))}")
        return 0

    need_config = not args.dry_run and (args.write or args.send or args.all)
    config = Config() if need_config else None

    try:
        # TODO: arxiv verify temporarily disabled due to API timeout issues.
        # if args.verify or args.all:
        #     if args.dry_run:
        #         print("[dry-run] Would verify advisors")
        #     else:
        #         data = verify_advisors(data)
        #     _save_json(data, output_path)
        #     print(f"Saved verified data to {output_path}")

        if args.write or args.all:
            if args.dry_run:
                print("[dry-run] Would write advisors to Feishu")
            else:
                data = write_advisors(data, config)
            _save_json(data, output_path)
            print(f"Saved written data to {output_path}")

        if args.send or args.all:
            if args.dry_run:
                print("[dry-run] Would send emails")
            else:
                data = send_emails(data, config)
            _save_json(data, output_path)
            print(f"Saved sent data to {output_path}")

    except (ValueError, OSError) as e:
        logging.exception("Phase failed")
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
