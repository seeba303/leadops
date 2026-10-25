"""Run: python -m leadops.cli --input examples/leads.csv --output decisions.json"""
import argparse
import json
from pathlib import Path
from .core import process_csv

def main():
    parser = argparse.ArgumentParser(description="Local-first B2B lead qualification")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = process_csv(args.input)
    data = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(data + "\n", encoding="utf-8")
        print(f"Saved {result['summary']['processed']} leads to {args.output}")
    else:
        print(data)

if __name__ == "__main__":
    main()
