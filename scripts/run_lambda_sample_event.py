#!/usr/bin/env python3
"""Invoca ``lambda_function.lambda_handler`` com ``events/sample-sqs-event.json`` (debug local)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lambda_function import lambda_handler


def main() -> None:
    path = _ROOT / "events" / "sample-sqs-event.json"
    event = json.loads(path.read_text(encoding="utf-8"))
    result = lambda_handler(event, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
