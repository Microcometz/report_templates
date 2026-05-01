"""Block-based template designer.

A *design* is a JSON-serialisable dict with this shape:

    {
        "name":  "salesInvoice",
        "title": "SALES INVOICE",
        "data":  {"main": "invoiceMainData", "details": "invoiceDetailsData"},
        "page":  {"size": "80mm", "margin": "5mm",
                  "orientation": "portrait"},
        "theme": {"preset": "pos", "font": "...",
                  "fontSize": "11px", "color": "#222",
                  "background": "#fff", "accent": "#444",
                  "borderColor": "#cccccc", "borderStyle": "solid",
                  "uppercase": True},
        "blocks": [
            {"id": "b1", "type": "title",
             "config": {"text": "SALES INVOICE"}},
            ...
        ],
    }

`render_design(design)` returns a Handlebars-flavoured HTML string with
inline CSS, ready to drop into a reporting engine. Each block is wrapped
in a `<section data-block-id="...">` so the GUI can highlight blocks in
the live preview.
"""

from __future__ import annotations

import html as _html
from typing import Any, Callable


# ----------------------------- Theme presets ------------------------------

THEME_PRESETS: dict[str, dict] = {
    "pos": {
        "font": "'Courier New', Courier, monospace",
        "fontSize": "11px",
        "color": "#000000",
        "background": "#ffffff",
        "accent": "#000000",
        "borderColor": "#000000",
        "borderStyle": "dashed",
        "uppercase": True,
        "padding": "0",
    },
    "a4-modern": {
        "font": "Arial, Helvetica, sans-serif",
        "fontSize": "13px",
        "color": "#222222",
        "background": "#ffffff",
        "accent": "#444444",
        "borderColor": "#cccccc",
        "borderStyle": "solid",
        "uppercase": False,
        "padding": "0",
    },
    "a4-minimal": {
        "font": "Helvetica, Arial, sans-serif",
        "fontSize": "12px",
        "color": "#333333",
        "background": "#ffffff",
        "accent": "#666666",
        "borderColor": "#dddddd",
        "borderStyle": "solid",
        "uppercase": False,
        "padding": "0",
    },
    "a4-dark": {
        "font": "Inter, 'Segoe UI', Arial, sans-serif",
        "fontSize": "13px",
        "color": "#1f2937",
        "background": "#ffffff",
        "accent": "#0f172a",
        "borderColor": "#cbd5e1",
        "borderStyle": "solid",
        "uppercase": False,
        "padding": "0",
    },
}


# ----------------------------- Page presets -------------------------------

PAGE_PRESETS: dict[str, dict] = {
    "80mm":   {"width": "80mm",   "margin": "3mm"},
    "58mm":   {"width": "58mm",   "margin": "2mm"},
    "a4":     {"width": "210mm",  "margin": "20mm"},
    "letter": {"width": "8.5in",  "margin": "0.75in"},
    "custom": {"width": "210mm",  "margin": "10mm"},
}


# ----------------------------- Helpers ------------------------------------

def _esc(s: Any) -> str:
    if s is None:
        return ""
    return _html.escape(str(s), quote=True)


def _hbs_default(path: str, default: str | None) -> str:
    """Emit `{{path}}` with optional fallback default."""
    if not default:
        return "{{" + path + "}}"
    return (
        "{{#if " + path + "}}{{" + path + "}}{{else}}"
        + _esc(default)
        + "{{/if}}"
    )


def _theme(design: dict) -> dict:
    """Resolve theme: preset overlaid with custom overrides."""
    theme = dict(design.get("theme") or {})
    preset = theme.get("preset") or "pos"
    base = dict(THEME_PRESETS.get(preset) or THEME_PRESETS["pos"])
    base.update({k: v for k, v in theme.items() if v not in ("", None)})
    base["preset"] = preset
    return base


def _page(design: dict) -> dict:
    page = dict(design.get("page") or {})
    size = page.get("size") or "80mm"
    base = dict(PAGE_PRESETS.get(size) or PAGE_PRESETS["80mm"])
    base.update({k: v for k, v in page.items() if v not in ("", None)})
    base["size"] = size
    base.setdefault("orientation", "portrait")
    return base


def _data_paths(design: dict) -> tuple[str, str]:
    data = design.get("data") or {}
    return (
        data.get("main") or "mainData",
        data.get("details") or "detailsData",
    )


# ----------------------------- Block renderers ----------------------------

def _r_title(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    text = cfg.get("text") or ""
    level = int(cfg.get("level") or 1)
    align = cfg.get("align") or "center"
    return (
        f'<div class="rt-title" style="text-align:{_esc(align)};">'
        f'<h{level} style="margin:0;letter-spacing:2px;">{_esc(text)}</h{level}>'
        f'</div>'
    )


def _r_company_header(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    main = ctx["main"]
    fields = cfg.get("fields") or ["companyName", "companyAddress"]
    show_logo = bool(cfg.get("showLogo", False))
    layout = cfg.get("layout") or "centered"
    logo_field = cfg.get("logoField") or "image"

    def line(field: str, first: bool) -> str:
        path = f"{main}.{field}"
        wrap = (
            f'<strong>{{{{{path}}}}}</strong>'
            if first
            else f'{{{{{path}}}}}'
        )
        return wrap

    body_lines = "<br>\n".join(line(f, i == 0) for i, f in enumerate(fields))

    if show_logo:
        logo_html = (
            f'<img class="rt-logo" '
            f'src="data:image/png;base64,{{{{{logo_field}}}}}" alt="logo">'
        )
    else:
        logo_html = ""

    if layout == "two-col":
        return (
            f'<table class="rt-company-header rt-two-col">'
            f'<tr>'
            f'<td class="rt-logo-cell">{logo_html}</td>'
            f'<td class="rt-company-cell">{body_lines}</td>'
            f'</tr></table>'
        )

    # centered (default)
    return (
        f'<div class="rt-company-header rt-centered">'
        + (f'<div class="rt-logo-row">{logo_html}</div>' if show_logo else "")
        + f'<div class="rt-company-text">{body_lines}</div>'
        + f'</div>'
    )


def _r_info_row(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    main = ctx["main"]
    items = cfg.get("items") or []
    layout = cfg.get("layout") or "stacked"

    def cell(it: dict) -> str:
        label = _esc(it.get("label") or "")
        path = f"{main}.{it.get('field') or ''}"
        sep = " : " if layout == "stacked" else ": "
        if layout == "two-col":
            return (
                f'<tr><td class="rt-info-label"><strong>{label}:</strong></td>'
                f'<td class="rt-info-value">{{{{{path}}}}}</td></tr>'
            )
        return f'<div class="rt-info-line">{label}{sep}{{{{{path}}}}}</div>'

    if layout == "two-col":
        rows = "\n".join(cell(it) for it in items)
        return f'<table class="rt-info-row rt-info-two-col">{rows}</table>'

    if layout == "right-aligned":
        rows = "<br>\n".join(
            f'<strong>{_esc(it.get("label") or "")}:</strong> '
            f'{{{{{main}.{it.get("field") or ""}}}}}'
            for it in items
        )
        return f'<div class="rt-info-row rt-info-right">{rows}</div>'

    return f'<div class="rt-info-row rt-info-stacked">{"".join(cell(it) for it in items)}</div>'


def _r_party_block(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    main = ctx["main"]
    columns = cfg.get("columns") or []

    def col(col_cfg: dict) -> str:
        label = _esc(col_cfg.get("label") or "")
        fields = col_cfg.get("fields") or []
        if not fields:
            return ""
        first, *rest = fields
        body = (
            f'<strong>{{{{{main}.{first}}}}}</strong>'
            + "".join(f"<br>{{{{{main}.{f}}}}}" for f in rest)
        )
        return (
            f'<td class="rt-party-col">'
            f'<div class="rt-section-title">{label}</div>'
            f'<div class="rt-party-body">{body}</div>'
            f'</td>'
        )

    cells = "".join(col(c) for c in columns)
    return f'<table class="rt-party"><tr>{cells}</tr></table>'


def _r_divider(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    style = cfg.get("style") or "solid"
    thickness = cfg.get("thickness") or "1px"
    spacing = cfg.get("spacing") or "6px"
    return (
        f'<div class="rt-divider" '
        f'style="border-top:{_esc(thickness)} {_esc(style)} currentColor;'
        f'margin:{_esc(spacing)} 0;"></div>'
    )


def _r_spacer(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    h = cfg.get("height") or "10px"
    return f'<div class="rt-spacer" style="height:{_esc(h)};"></div>'


def _r_text(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    content = cfg.get("content") or ""
    align = cfg.get("align") or "left"
    size = cfg.get("size") or "inherit"
    bold = bool(cfg.get("bold"))
    weight = "bold" if bold else "normal"
    safe = _esc(content).replace("\n", "<br>")
    return (
        f'<div class="rt-text" '
        f'style="text-align:{_esc(align)};font-size:{_esc(size)};'
        f'font-weight:{weight};">{safe}</div>'
    )


def _r_image(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    field = cfg.get("field") or "image"
    width = cfg.get("width") or "75px"
    height = cfg.get("height") or ""
    align = cfg.get("align") or "center"
    style = f"width:{_esc(width)};"
    if height:
        style += f"height:{_esc(height)};"
    return (
        f'<div class="rt-image" style="text-align:{_esc(align)};">'
        f'<img src="data:image/png;base64,{{{{{field}}}}}" alt="image" '
        f'style="{style}">'
        f'</div>'
    )


def _r_meta_table(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    main = ctx["main"]
    title = cfg.get("title") or ""
    rows = cfg.get("rows") or []

    title_html = (
        f'<div class="rt-section-title">{_esc(title)}</div>' if title else ""
    )
    body = "".join(
        f'<tr><td>{_esc(r.get("label") or "")}</td>'
        f'<td>{{{{{main}.{r.get("field") or ""}}}}}</td></tr>'
        for r in rows
    )
    return f'<div class="rt-meta-block">{title_html}<table class="rt-meta-table">{body}</table></div>'


def _r_items_table(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    details = ctx["details"]
    cols = cfg.get("columns") or []
    show_header = cfg.get("showHeader", True)
    header_style = cfg.get("headerStyle") or "underline"
    product_as_row = bool(cfg.get("productAsRow", False))

    if not cols:
        return '<div class="rt-empty">(items table — add columns)</div>'

    def th(c: dict) -> str:
        align = c.get("align") or "left"
        width = c.get("width") or ""
        w = f' style="width:{_esc(width)};"' if width else ""
        return f'<th class="rt-col-{_esc(align)}"{w}>{_esc(c.get("label") or "")}</th>'

    def td(c: dict, with_class: bool = True) -> str:
        align = c.get("align") or "left"
        field = c.get("field") or ""
        default = c.get("default") or ""
        suffix = c.get("suffix") or ""
        cls = f' class="rt-col-{_esc(align)}"' if with_class else ""
        value = _hbs_default("this." + field, default)
        if suffix:
            return (
                f'<td{cls}>'
                f'<span class="rt-nowrap">{value}{_esc(suffix)}</span>'
                f'</td>'
            )
        return f'<td{cls}>{value}</td>'

    head = ""
    if show_header:
        head = (
            f'<thead class="rt-thead-{_esc(header_style)}">'
            f'<tr>{"".join(th(c) for c in cols)}</tr>'
            f'</thead>'
        )

    if product_as_row:
        product_field = cols[0].get("field") or "product"
        col_count = len(cols)
        body = (
            "{{#each " + details + "}}"
            f'<tr class="rt-item-name-row">'
            f'<td colspan="{col_count}">'
            f'<span class="rt-item-name">{{{{this.{product_field}}}}}</span>'
            f'</td></tr>'
            f'<tr class="rt-item-values">'
            + "".join(td(c) for c in cols)
            + f'</tr>'
            "{{/each}}"
        )
    else:
        first = cols[0]
        first_field = first.get("field") or "product"
        first_align = first.get("align") or "left"
        body = (
            "{{#each " + details + "}}"
            f'<tr>'
            f'<td class="rt-col-{_esc(first_align)}">'
            f'<strong>{{{{this.{first_field}}}}}</strong></td>'
            + "".join(td(c) for c in cols[1:])
            + f'</tr>'
            "{{/each}}"
        )

    return f'<table class="rt-items-table">{head}<tbody>{body}</tbody></table>'


def _r_totals_table(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    main = ctx["main"]
    rows = cfg.get("rows") or []
    style = cfg.get("style") or "underline"

    def row(r: dict, idx: int) -> str:
        width = ' style="width:70%;"' if idx == 0 else ""
        return (
            f'<tr><td class="rt-col-right rt-total-label"{width}>'
            f'{_esc(r.get("label") or "")}</td>'
            f'<td class="rt-col-right">'
            f'{_hbs_default(main + "." + (r.get("field") or ""), r.get("default") or "")}'
            f'</td></tr>'
        )

    body = "".join(row(r, i) for i, r in enumerate(rows))
    return f'<table class="rt-totals rt-totals-{_esc(style)}">{body}</table>'


def _r_grand_total(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    main = ctx["main"]
    label = cfg.get("label") or "TOTAL"
    field = cfg.get("field") or "totalAmount"
    default = cfg.get("default") or "0.00"
    size = cfg.get("fontSize") or "14px"
    return (
        f'<table class="rt-grand-total" style="font-size:{_esc(size)};">'
        f'<tr><td class="rt-col-right rt-total-label" style="width:70%;">'
        f'<strong>{_esc(label)}</strong></td>'
        f'<td class="rt-col-right"><strong>'
        f'{_hbs_default(main + "." + field, default)}'
        f'</strong></td></tr></table>'
    )


def _r_footer(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    text = cfg.get("text") or ""
    align = cfg.get("align") or "center"
    safe = _esc(text).replace("\n", "<br>")
    return f'<div class="rt-footer" style="text-align:{_esc(align)};">{safe}</div>'


def _r_html(blk: dict, ctx: dict) -> str:
    cfg = blk.get("config") or {}
    return f'<div class="rt-raw-html">{cfg.get("content") or ""}</div>'


# Block-type table; the GUI discovers available block types via
# block_types.BLOCK_TYPES (a parallel pure-data list).
RENDERERS: dict[str, Callable[[dict, dict], str]] = {
    "title":          _r_title,
    "company-header": _r_company_header,
    "info-row":       _r_info_row,
    "party-block":    _r_party_block,
    "divider":        _r_divider,
    "spacer":         _r_spacer,
    "text":           _r_text,
    "image":          _r_image,
    "meta-table":     _r_meta_table,
    "items-table":    _r_items_table,
    "totals-table":   _r_totals_table,
    "grand-total":    _r_grand_total,
    "footer":         _r_footer,
    "html":           _r_html,
}


# ------------------------------- CSS --------------------------------------

def _css(theme: dict, page: dict) -> str:
    accent = theme["accent"]
    border_color = theme["borderColor"]
    border_style = theme["borderStyle"]
    page_width = page["width"]
    margin = page["margin"]

    transform = "uppercase" if theme.get("uppercase") else "none"

    # Use @page only for a4/letter; for thermal sizes we constrain body width.
    is_paper = page["size"] in ("a4", "letter")
    page_block = (
        f'@page{{ size:{page["width"]} auto; margin:{margin}; }}'
        if is_paper
        else f'@page{{ margin:0; }}'
    )

    body_width = (
        f'max-width:{page_width};margin:0 auto;padding:{margin};'
        if not is_paper
        else 'margin:0;'
    )

    return f"""
{page_block}

body{{
    font-family:{theme["font"]};
    font-size:{theme["fontSize"]};
    color:{theme["color"]};
    background:{theme["background"]};
    text-transform:{transform};
    {body_width}
}}

.rt-block{{ margin-bottom:6px; }}
.rt-section-title{{
    font-size:0.85em;
    font-weight:bold;
    text-transform:uppercase;
    letter-spacing:0.5px;
    margin-bottom:4px;
}}

.rt-title{{ margin:6px 0 12px; }}

.rt-company-header.rt-centered{{ text-align:center; }}
.rt-company-header .rt-logo-row{{ margin-bottom:4px; }}
.rt-company-header .rt-company-text{{ line-height:1.4; }}
.rt-company-header.rt-two-col{{ width:100%; border-collapse:collapse; }}
.rt-company-header.rt-two-col td{{ vertical-align:middle; padding:6px; }}
.rt-company-header .rt-logo-cell{{ width:25%; text-align:center; }}
.rt-company-header .rt-company-cell{{ width:75%; text-align:left; }}
.rt-logo{{ width:75px; height:auto; max-height:30px; object-fit:contain; }}

.rt-info-row.rt-info-stacked .rt-info-line{{ margin-bottom:2px; }}
.rt-info-row.rt-info-right{{ text-align:right; }}
.rt-info-row.rt-info-two-col{{ width:100%; border-collapse:collapse; }}
.rt-info-row.rt-info-two-col td{{ padding:2px 4px; }}

.rt-party{{ width:100%; border-collapse:collapse; }}
.rt-party .rt-party-col{{ vertical-align:top; padding:6px 8px; line-height:1.4; }}
.rt-party .rt-party-body{{ font-size:0.95em; }}

.rt-spacer{{ width:100%; }}
.rt-text{{ line-height:1.4; }}
.rt-image img{{ display:inline-block; }}

.rt-meta-block{{ margin-bottom:8px; }}
.rt-meta-table{{
    width:100%; border-collapse:collapse;
}}
.rt-meta-table td{{
    padding:4px 6px;
    border:1px {border_style} {border_color};
    font-size:0.95em;
}}
.rt-meta-table td:first-child{{ font-weight:bold; width:45%; }}

.rt-items-table{{ width:100%; border-collapse:collapse; margin:6px 0; }}
.rt-items-table td, .rt-items-table th{{ padding:5px 6px; }}
.rt-items-table .rt-col-left{{ text-align:left; }}
.rt-items-table .rt-col-right{{ text-align:right; }}
.rt-items-table .rt-col-center{{ text-align:center; }}

.rt-thead-bordered th{{
    border:1px {border_style} {accent};
    background:{accent};
    color:#ffffff;
    font-weight:bold;
}}
.rt-thead-bordered + tbody td{{ border:1px {border_style} {border_color}; }}

.rt-thead-dark th{{
    background:{accent};
    color:#ffffff;
    border:none;
    font-weight:bold;
}}

.rt-thead-underline th{{
    border-bottom:1px solid currentColor;
    font-weight:normal;
    padding-bottom:4px;
    font-size:0.95em;
}}

.rt-item-name{{
    display:block;
    font-weight:bold;
    padding-top:6px;
}}
.rt-item-values td{{ padding-bottom:6px; }}
.rt-nowrap{{ white-space:nowrap; }}

.rt-totals{{ width:100%; border-collapse:collapse; margin-top:6px; }}
.rt-totals td{{ padding:3px 6px; }}
.rt-totals.rt-totals-underline{{ border-top:1px solid currentColor; padding-top:4px; }}
.rt-totals.rt-totals-bordered td{{ border:1px {border_style} {border_color}; }}
.rt-totals.rt-totals-bordered td.rt-total-label{{ background:{accent}; color:#ffffff; font-weight:bold; }}

.rt-grand-total{{ width:100%; border-collapse:collapse; margin-top:4px; }}
.rt-grand-total td{{ padding:6px; border-top:2px solid currentColor; }}

.rt-footer{{
    margin-top:12px;
    padding-top:8px;
    border-top:1px {border_style} {border_color};
    line-height:1.4;
    font-size:0.95em;
}}

.rt-divider{{ width:100%; }}

thead{{ display:table-header-group; }}
tr{{ page-break-inside:avoid; }}

.rt-empty{{ color:#999; font-style:italic; padding:6px 0; }}
"""


# --------------------------------- API ------------------------------------

def render_design(design: dict, *, with_block_ids: bool = True) -> str:
    """Render a design dict into a complete HTML document."""
    main, details = _data_paths(design)
    ctx = {"main": main, "details": details}
    theme = _theme(design)
    page = _page(design)
    title = design.get("title") or design.get("name") or "Template"

    parts: list[str] = []
    for blk in (design.get("blocks") or []):
        bid = _esc(blk.get("id") or "")
        kind = blk.get("type")
        renderer = RENDERERS.get(kind)
        if renderer is None:
            inner = f'<div class="rt-empty">[unknown block: {_esc(kind)}]</div>'
        else:
            try:
                inner = renderer(blk, ctx)
            except Exception as exc:  # noqa: BLE001
                inner = f'<div class="rt-empty">[block error: {_esc(exc)}]</div>'
        attr = f' data-block-id="{bid}"' if with_block_ids and bid else ""
        parts.append(f'<section class="rt-block"{attr}>{inner}</section>')

    body_html = "\n".join(parts)
    css = _css(theme, page)

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        f'<title>{_esc(title)}</title>\n'
        f'<style>{css}</style>\n'
        '</head>\n<body>\n'
        f'{body_html}\n'
        '</body>\n</html>\n'
    )
