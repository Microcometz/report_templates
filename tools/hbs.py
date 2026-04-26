"""Tiny Handlebars-compatible renderer.

Supports just the subset used by templates in this repo:
    - {{path.to.value}}        simple substitution
    - {{#if path}}A{{else}}B{{/if}}
    - {{#each list}}...{{this.field}}...{{/each}} (with `if` allowed inside)

Rendering is best-effort and intended only for the live preview pane;
the real rendering still happens server-side wherever the templates are
consumed.
"""

from __future__ import annotations

import re
from typing import Any


_EACH_RE = re.compile(
    r"\{\{#each\s+([\w.]+)\}\}([\s\S]*?)\{\{/each\}\}"
)
_IF_RE = re.compile(
    r"\{\{#if\s+([\w.]+)\}\}([\s\S]*?)(?:\{\{else\}\}([\s\S]*?))?\{\{/if\}\}"
)
_VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def _resolve(data: dict, path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
    return cur


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip() != ""
    return bool(value)


def render(template: str, data: dict) -> str:
    """Render a Handlebars-flavoured template with the supplied data."""

    def each_repl(m: "re.Match[str]") -> str:
        path = m.group(1)
        body = m.group(2)
        items = _resolve(data, path) or []
        out: list[str] = []
        for item in items:
            ctx = dict(data)
            ctx["this"] = item
            out.append(render(body, ctx))
        return "".join(out)

    template = _EACH_RE.sub(each_repl, template)

    def if_repl(m: "re.Match[str]") -> str:
        path = m.group(1)
        truthy_branch = m.group(2)
        falsy_branch = m.group(3) or ""
        chosen = truthy_branch if _truthy(_resolve(data, path)) else falsy_branch
        return render(chosen, data)

    # Apply repeatedly so nested ifs (rare) collapse cleanly.
    while _IF_RE.search(template):
        template = _IF_RE.sub(if_repl, template)

    def var_repl(m: "re.Match[str]") -> str:
        v = _resolve(data, m.group(1))
        return "" if v is None else str(v)

    template = _VAR_RE.sub(var_repl, template)

    # Strip any remaining helper expressions we don't understand
    # (e.g. `{{lookup ../barcodes this.barcodeKey}}`) so the preview
    # never shows raw braces; templates using such helpers still render
    # cleanly at runtime via the real Handlebars engine.
    template = re.sub(r"\{\{[^{}]+\}\}", "", template)
    return template
