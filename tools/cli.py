"""Interactive CLI for generating report templates.

Usage:
    python3 tools/cli.py

The CLI walks through a series of prompts, lets you start from a preset,
and writes the generated template into ./generated/.
"""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

# Make `tools` importable when invoked from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from builder import build  # noqa: E402
from presets import PRESETS, list_names  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "generated"


# ----------------------------- Prompt helpers -----------------------------

def _ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        ans = input(f"{prompt}{suffix}: ").strip()
        if ans:
            return ans
        if default is not None:
            return default
        print("  please enter a value")


def _ask_choice(prompt: str, choices: list[str], default_index: int = 0) -> int:
    print(f"\n{prompt}")
    for i, c in enumerate(choices, 1):
        marker = " (default)" if i - 1 == default_index else ""
        print(f"  {i}. {c}{marker}")
    while True:
        raw = input("> ").strip()
        if raw == "":
            return default_index
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return int(raw) - 1
        print("  invalid choice, try again")


def _ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        ans = input(f"{prompt}{suffix}: ").strip().lower()
        if ans == "":
            return default
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False


def _edit_list(label: str, items: list[dict], fields: list[tuple[str, str]]) -> list[dict]:
    """Generic editor for a list of dicts. `fields` is a list of
    (key, prompt) pairs. Returns the (possibly modified) list."""

    while True:
        print(f"\n{label}:")
        if not items:
            print("  (empty)")
        for i, it in enumerate(items, 1):
            summary = " | ".join(f"{k}={it.get(k, '')}" for k, _ in fields)
            print(f"  {i}. {summary}")
        print("\n  a) add  e) edit  d) delete  k) keep & continue")
        op = input("> ").strip().lower()
        if op == "k" or op == "":
            return items
        if op == "a":
            new = {}
            for key, prompt in fields:
                new[key] = _ask(f"  {prompt}", default="")
            items.append(new)
        elif op == "e":
            idx = input("  index to edit: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(items):
                target = items[int(idx) - 1]
                for key, prompt in fields:
                    target[key] = _ask(f"  {prompt}", default=str(target.get(key, "")))
        elif op == "d":
            idx = input("  index to delete: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(items):
                items.pop(int(idx) - 1)


# -------------------------------- Workflow --------------------------------

def _interactive() -> dict:
    print("=" * 60)
    print("Report template generator")
    print("=" * 60)

    preset_names = ["(start from scratch)"] + list_names()
    pi = _ask_choice("Start from a preset?", preset_names, default_index=1)
    if pi == 0:
        spec: dict = {
            "name": "myTemplate",
            "style": "pos",
            "title": "MY TEMPLATE",
            "mainData": "mainData",
            "detailsData": "detailsData",
            "header": {
                "showLogo": True,
                "companyFields": ["companyName", "companyAddress"],
                "infoFields": [],
                "partyLabel": "Customer",
                "partyFields": ["customer"],
            },
            "columns": [],
            "totals": [],
            "grandTotal": None,
            "footer": "",
        }
    else:
        spec = deepcopy(PRESETS[preset_names[pi]])

    spec["name"] = _ask("Output file name (without .html)", default=spec["name"])

    si = _ask_choice(
        "Style:",
        ["POS / 80 mm receipt", "A4 / full-page report"],
        default_index=0 if spec["style"] == "pos" else 1,
    )
    spec["style"] = "pos" if si == 0 else "a4"

    spec["title"] = _ask("Title (shown for A4, ignored for POS)", default=spec.get("title", ""))
    spec["mainData"] = _ask("Main data namespace", default=spec["mainData"])
    spec["detailsData"] = _ask("Details (items array) namespace", default=spec["detailsData"])

    header = spec.setdefault("header", {})
    if spec["style"] == "pos":
        header["showLogo"] = _ask_yes_no("Show logo?", default=bool(header.get("showLogo", True)))

    print("\nCompany fields shown in the header (top-to-bottom).")
    print("Current: " + ", ".join(header.get("companyFields", []) or []))
    if _ask_yes_no("Edit company fields?", default=False):
        raw = _ask("Comma-separated field names",
                   default=",".join(header.get("companyFields", [])))
        header["companyFields"] = [s.strip() for s in raw.split(",") if s.strip()]

    if _ask_yes_no("Edit document info fields (Date / Doc # / etc.)?", default=False):
        header["infoFields"] = _edit_list(
            "Info fields",
            list(header.get("infoFields", []) or []),
            [("label", "label"), ("field", "data field")],
        )

    if _ask_yes_no("Edit party (customer/vendor) block?", default=False):
        header["partyLabel"] = _ask("Party label", default=header.get("partyLabel", "Customer"))
        raw = _ask("Comma-separated party fields",
                   default=",".join(header.get("partyFields", [])))
        header["partyFields"] = [s.strip() for s in raw.split(",") if s.strip()]

    if _ask_yes_no("Edit item-table columns?", default=False):
        spec["columns"] = _edit_list(
            "Item columns",
            list(spec.get("columns", []) or []),
            [
                ("label", "header label"),
                ("field", "data field"),
                ("align", "align (left/right/center)"),
                ("width", "width (e.g. 17%)"),
                ("default", "default if missing"),
                ("suffix", "suffix (e.g. ' PCS')"),
            ],
        )

    if _ask_yes_no("Edit totals rows?", default=False):
        spec["totals"] = _edit_list(
            "Totals",
            list(spec.get("totals", []) or []),
            [("label", "label"), ("field", "data field"), ("default", "default")],
        )

    if _ask_yes_no("Edit grand total?", default=False):
        gt = spec.get("grandTotal") or {"label": "TOTAL", "field": "totalAmount", "default": "0.00"}
        gt["label"] = _ask("Grand total label", default=gt.get("label", "TOTAL"))
        gt["field"] = _ask("Grand total data field", default=gt.get("field", "totalAmount"))
        gt["default"] = _ask("Grand total default", default=gt.get("default", "0.00"))
        spec["grandTotal"] = gt

    if _ask_yes_no("Edit footer text?", default=False):
        print("Enter footer text. Blank line ends input.")
        lines = []
        while True:
            line = input("> ")
            if line == "":
                break
            lines.append(line)
        spec["footer"] = "\n".join(lines)

    return spec


def _save(spec: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html = build(spec)
    name = spec["name"].strip() or "template"
    if not name.endswith(".html"):
        name = name + ".html"
    target = OUTPUT_DIR / name
    target.write_text(html, encoding="utf-8")
    return target


def main() -> int:
    try:
        spec = _interactive()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        return 1

    target = _save(spec)
    print(f"\n[OK] Wrote {target.relative_to(REPO_ROOT)}  ({target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
