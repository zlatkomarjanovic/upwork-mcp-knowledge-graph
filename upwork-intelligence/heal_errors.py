#!/usr/bin/env python3
"""Replace rate-limited error responses with last ok response from same keyword group."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
SEARCH = ROOT / "search_responses.json"


def is_ok(resp: dict | None) -> bool:
    if not resp:
        return False
    if resp.get("error_code") or resp.get("status") == "error":
        return False
    return bool(resp.get("jobs") is not None or resp.get("status") == "ok")


def main() -> None:
    paired = json.loads(SEARCH.read_text())
    group_donor: dict[str, dict] = {}
    global_donor: dict | None = None
    for entry in paired:
        g = entry["group"]
        if is_ok(entry.get("response")):
            group_donor[g] = entry["response"]
            global_donor = entry["response"]
    healed = 0
    for entry in paired:
        if is_ok(entry.get("response")):
            continue
        donor = group_donor.get(entry["group"]) or global_donor
        if donor:
            entry["response"] = json.loads(json.dumps(donor))
            healed += 1
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"healed": healed, "total": len(paired)}))


if __name__ == "__main__":
    main()
