"""Local web GUI for the report-template designer.

    python3 tools/server.py [--port 5173] [--host 127.0.0.1]

Then open http://127.0.0.1:5173 in your browser.

The designer is the primary mode. The legacy spec-form and raw-HTML
modes are still available as fallbacks; their endpoints are kept for
backwards compatibility.

API
---
GET  /                          static front-end
GET  /static/<file>             static asset
GET  /api/templates             list .html files in repo (excluding tools/)
GET  /api/template?path=...     read a file's raw content
POST /api/template/save         save raw content back to its original path
POST /api/render                render arbitrary HTML; body { html, data? }

GET  /api/block-types           designer: block schemas + theme/page presets
GET  /api/designs               designer: built-in design presets
GET  /api/sample-data           designer: default sample payload (for editor)
POST /api/design/render         designer: { design, data? } -> { html, rendered }
POST /api/design/save           designer: { design, path? } -> save .html
POST /api/design/save-as        designer: { design, path, overwrite? }
POST /api/design/load           designer: { path } -> { design? , content }

GET  /api/presets               legacy: spec presets
POST /api/preview               legacy: spec -> raw + rendered
POST /api/save                  legacy: spec -> generated/<name>.html
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from block_types import BLOCK_TYPES, CATEGORIES  # noqa: E402
from builder import build  # noqa: E402  (legacy)
from designer import PAGE_PRESETS, THEME_PRESETS, render_design  # noqa: E402
from designs import PRESETS as DESIGN_PRESETS  # noqa: E402
from hbs import render as hbs_render  # noqa: E402
from presets import PRESETS as SPEC_PRESETS  # noqa: E402  (legacy)
from sample_data import for_any as sample_for_any  # noqa: E402
from sample_data import for_spec as sample_for_spec  # noqa: E402


REPO_ROOT = TOOLS_DIR.parent
OUTPUT_DIR = REPO_ROOT / "generated"
PUBLIC_DIR = TOOLS_DIR / "public"

_FORBIDDEN_TOP_DIRS = {"tools", ".git", ".github", "node_modules"}

# Embedded design marker so re-opening a file restores the editor state.
# Sits in an HTML comment so it's invisible to reporting engines.
_DESIGN_MARKER_RE = re.compile(
    r"<!--\s*RT_DESIGN_V1:([A-Za-z0-9+/=\s]+)-->",
    re.DOTALL,
)


def _embed_design(html: str, design: dict) -> str:
    payload = base64.b64encode(json.dumps(design).encode("utf-8")).decode("ascii")
    marker = f"<!-- RT_DESIGN_V1:{payload} -->\n"
    # Place the marker right after </html> so it doesn't disturb output.
    if "</html>" in html:
        return html.replace("</html>", "</html>\n" + marker, 1)
    return html + "\n" + marker


def _extract_design(html: str) -> dict | None:
    m = _DESIGN_MARKER_RE.search(html)
    if not m:
        return None
    try:
        raw = base64.b64decode(m.group(1).strip().encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _safe_repo_path(rel: str, *, allow_create: bool = False) -> Path:
    """Resolve `rel` against REPO_ROOT and ensure it points at an `.html`
    file inside the repo (and outside forbidden folders)."""

    rel = (rel or "").lstrip("/").lstrip("\\")
    if not rel:
        raise ValueError("path is empty")
    target = (REPO_ROOT / rel).resolve()
    repo = REPO_ROOT.resolve()
    try:
        relative = target.relative_to(repo)
    except ValueError as exc:
        raise ValueError("path escapes repo root") from exc
    if target.suffix.lower() != ".html":
        raise ValueError("only .html files may be edited")
    if relative.parts and relative.parts[0] in _FORBIDDEN_TOP_DIRS:
        raise ValueError(f"editing inside '{relative.parts[0]}/' is not allowed")
    if not allow_create and not target.exists():
        # Allow path-resolution-only mode for callers that don't care
        # whether the file exists yet.
        pass
    return target


def _list_html_files() -> list[dict]:
    repo = REPO_ROOT.resolve()
    items: list[dict] = []
    for path in repo.rglob("*.html"):
        try:
            rel = path.relative_to(repo)
        except ValueError:
            continue
        if rel.parts and rel.parts[0] in _FORBIDDEN_TOP_DIRS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""
        has_design = "RT_DESIGN_V1:" in text
        items.append({
            "path": str(rel),
            "name": path.name,
            "folder": str(rel.parent) if str(rel.parent) != "." else "",
            "bytes": path.stat().st_size,
            "hasDesign": has_design,
        })
    items.sort(key=lambda x: (x["folder"], x["name"]))
    return items


def _list_folders() -> list[str]:
    repo = REPO_ROOT.resolve()
    out = set()
    for path in repo.rglob("*"):
        if not path.is_dir():
            continue
        try:
            rel = path.relative_to(repo)
        except ValueError:
            continue
        parts = rel.parts
        if not parts:
            continue
        if parts[0] in _FORBIDDEN_TOP_DIRS:
            continue
        out.add(str(rel))
    return sorted(out)


_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "ReportTemplateDesigner/2.0"

    def log_message(self, fmt, *args):  # noqa: A003
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # ----------------------------- helpers -----------------------------

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_text_error(self, status: int, message: str) -> None:
        self._send_bytes(status, "text/plain; charset=utf-8", message.encode("utf-8"))

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _serve_static(self, rel: str) -> None:
        target = (PUBLIC_DIR / rel).resolve()
        if not str(target).startswith(str(PUBLIC_DIR.resolve())):
            self._send_text_error(HTTPStatus.FORBIDDEN, "forbidden")
            return
        if not target.is_file():
            self._send_text_error(HTTPStatus.NOT_FOUND, f"not found: {rel}")
            return
        ctype = _MIME.get(target.suffix.lower(), "application/octet-stream")
        self._send_bytes(HTTPStatus.OK, ctype, target.read_bytes())

    def _query(self) -> dict:
        if "?" not in self.path:
            return {}
        qs = self.path.split("?", 1)[1]
        return {
            unquote(k): unquote(v)
            for k, _, v in (p.partition("=") for p in qs.split("&") if p)
        }

    # ------------------------------- GET -------------------------------

    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0]

        if path in ("/", "/index.html"):
            self._serve_static("index.html")
            return
        if path.startswith("/static/"):
            self._serve_static(path[len("/static/"):])
            return

        if path == "/api/block-types":
            self._send_json(HTTPStatus.OK, {
                "blockTypes": BLOCK_TYPES,
                "categories": CATEGORIES,
                "themePresets": list(THEME_PRESETS.keys()),
                "themeDefaults": THEME_PRESETS,
                "pagePresets": PAGE_PRESETS,
            })
            return

        if path == "/api/designs":
            self._send_json(HTTPStatus.OK, {"designs": DESIGN_PRESETS})
            return

        if path == "/api/sample-data":
            self._send_json(HTTPStatus.OK, {"data": sample_for_any()})
            return

        if path == "/api/templates":
            self._send_json(HTTPStatus.OK, {
                "templates": _list_html_files(),
                "folders": _list_folders(),
            })
            return

        if path == "/api/template":
            rel = self._query().get("path", "")
            try:
                target = _safe_repo_path(rel)
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            if not target.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            content = target.read_text(encoding="utf-8")
            self._send_json(HTTPStatus.OK, {
                "path": str(target.relative_to(REPO_ROOT)),
                "content": content,
                "bytes": len(content.encode("utf-8")),
                "design": _extract_design(content),
            })
            return

        if path == "/api/presets":
            self._send_json(HTTPStatus.OK, {"presets": SPEC_PRESETS})
            return

        self._send_text_error(HTTPStatus.NOT_FOUND, f"not found: {path}")

    # ------------------------------- POST ------------------------------

    def do_POST(self):  # noqa: N802
        path = self.path.split("?", 1)[0]

        try:
            payload = self._read_json()
        except json.JSONDecodeError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"invalid JSON: {exc}"})
            return

        # ----- designer endpoints -----
        if path == "/api/design/render":
            try:
                design = payload.get("design") or {}
                data = payload.get("data")
                if data is None:
                    data = sample_for_any()
                elif not isinstance(data, dict):
                    raise ValueError("data must be a JSON object")
                html = render_design(design)
                rendered = hbs_render(html, data)
            except Exception as exc:  # noqa: BLE001
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, {"html": html, "rendered": rendered})
            return

        if path in ("/api/design/save", "/api/design/save-as"):
            design = payload.get("design") or {}
            target_rel = (payload.get("path") or "").strip()
            overwrite = bool(payload.get("overwrite", path == "/api/design/save"))
            if not target_rel:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "path is required"})
                return
            try:
                target = _safe_repo_path(target_rel, allow_create=True)
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            if target.exists() and not overwrite:
                self._send_json(HTTPStatus.CONFLICT, {
                    "error": "file exists",
                    "path": str(target.relative_to(REPO_ROOT)),
                })
                return
            try:
                html = render_design(design)
                with_marker = _embed_design(html, design)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(with_marker, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, {
                "path": str(target.relative_to(REPO_ROOT)),
                "bytes": target.stat().st_size,
            })
            return

        if path == "/api/design/load":
            rel = (payload.get("path") or "").strip()
            try:
                target = _safe_repo_path(rel)
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            if not target.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            content = target.read_text(encoding="utf-8")
            design = _extract_design(content)
            self._send_json(HTTPStatus.OK, {
                "path": str(target.relative_to(REPO_ROOT)),
                "content": content,
                "design": design,
            })
            return

        # ----- raw HTML editor -----
        if path == "/api/render":
            try:
                html = payload.get("html") or ""
                data = payload.get("data")
                if data is None:
                    data = sample_for_any()
                elif not isinstance(data, dict):
                    raise ValueError("data must be a JSON object")
                rendered = hbs_render(html, data)
            except Exception as exc:  # noqa: BLE001
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, {"rendered": rendered})
            return

        if path == "/api/template/save":
            rel = payload.get("path") or ""
            content = payload.get("content")
            if not isinstance(content, str):
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "content must be a string"})
                return
            try:
                target = _safe_repo_path(rel, allow_create=True)
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            except OSError as exc:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, {
                "path": str(target.relative_to(REPO_ROOT)),
                "bytes": target.stat().st_size,
            })
            return

        # ----- legacy spec form -----
        if path == "/api/preview":
            try:
                spec = payload.get("spec") or {}
                raw = build(spec)
                rendered = hbs_render(raw, sample_for_spec(spec))
            except Exception as exc:  # noqa: BLE001
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, {"raw": raw, "rendered": rendered})
            return

        if path == "/api/save":
            try:
                spec = payload.get("spec") or {}
                html = build(spec)
            except Exception as exc:  # noqa: BLE001
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            name = (spec.get("name") or "template").strip()
            if not name.endswith(".html"):
                name = name + ".html"
            target = OUTPUT_DIR / name
            try:
                target.write_text(html, encoding="utf-8")
            except OSError as exc:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, {
                "path": str(target.relative_to(REPO_ROOT)),
                "bytes": target.stat().st_size,
            })
            return

        self._send_text_error(HTTPStatus.NOT_FOUND, f"not found: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5173)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"Report-template designer running at {url}")
    print(f"Repo root:         {REPO_ROOT}")
    print(f"Generated folder:  {OUTPUT_DIR}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
