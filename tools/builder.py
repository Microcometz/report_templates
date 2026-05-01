"""Core template builder.

Takes a `spec` dictionary describing what the template should contain
and emits a Handlebars-flavoured HTML string matching the look-and-feel
of the existing templates in this repo.

Supported styles:
    - "pos": 80 mm thermal-receipt look (Courier New, dashed dividers).
    - "a4" : full-page report look (Arial, bordered tables).

Spec shape (see tools/sample_data.py for a working example):

    {
        "name":        "purchaseInvoice",        # output filename, no .html
        "style":       "pos" | "a4",
        "title":       "PURCHASE INVOICE",       # A4 only; ignored for POS
        "mainData":    "purchaseMainData",       # top-level data namespace
        "detailsData": "purchaseDetailsData",    # array namespace for items
        "header": {
            "showLogo":       True,              # POS only
            "companyFields":  ["companyName", "companyAddress", "companyPhone"],
            "infoFields":     [{"label": "Date",     "field": "docDate"}, ...],
            "partyLabel":     "Customer",
            "partyFields":    ["customer", "mobile"],
        },
        "columns": [
            {"label": "QTY",  "field": "qty",  "align": "left",
             "width": "14%", "default": "0", "suffix": " PCS"},
            ...
        ],
        "totals": [
            {"label": "Gross Total", "field": "grossAmount", "default": "0.00"},
            ...
        ],
        "grandTotal": {"label": "Net Amount", "field": "invoiceTotal",
                       "default": "0.00"},
        "footer": "Thank you for shopping with us\nVISIT AGAIN!",
    }
"""

from __future__ import annotations

from typing import Any


# ----------------------------- Shared helpers -----------------------------

def _esc(text: Any) -> str:
    """HTML-escape plain text. We only escape user-supplied labels/footers;
    Handlebars expressions are emitted verbatim."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _hbs_value(path: str, default: str | None) -> str:
    """Emit `{{path}}` or `{{#if path}}{{path}}{{else}}<default>{{/if}}`."""
    if default is None or default == "":
        return "{{" + path + "}}"
    return (
        "{{#if " + path + "}}{{" + path + "}}{{else}}"
        + _esc(default)
        + "{{/if}}"
    )


def _br_lines(*lines: str) -> str:
    return "<br>\n".join(line for line in lines if line)


# --------------------------------- CSS -----------------------------------

_POS_CSS = """\
body{
    font-family:'Courier New', Courier, monospace;
    font-size:11px;
    text-transform:uppercase;
    margin-left:3mm;
    margin-right:3mm;
}

table{
    width:100%;
    border-collapse:collapse;
    margin-bottom:5px;
}

.center{ text-align:center; }
.left{ text-align:left; }
.right{ text-align:right; }

.header-layout{
    width:100%;
    border-collapse:collapse;
    margin-bottom:5px;
}

.logo-cell{
    width:25%;
    text-align:center;
    vertical-align:middle;
}

.company-cell{
    width:75%;
    text-align:center;
    vertical-align:middle;
}

.logo{
    width:75px;
    height:25px;
}

.header-table th{
    font-weight:normal;
    border-bottom:1px solid #000;
    padding-bottom:5px;
    font-size:10px;
}

.item-name{
    padding-top:8px;
    font-weight:bold;
    display:block;
}

.item-values td{
    padding-bottom:8px;
}

.totals-table{
    margin-top:10px;
    border-top:1px solid #000;
    padding-top:5px;
}

.totals-table td{
    padding:2px 0;
}

.footer{
    text-align:center;
    margin-top:15px;
    font-size:12px;
}

.line{
    border-top:1px dashed #000;
    margin:6px 0;
}
"""

_A4_CSS = """\
@page{
    margin:20mm;
}

body{
    font-family: Arial, Helvetica, sans-serif;
    margin:0;
    color:#222;
}

.header-table{
    width:100%;
    border-collapse:collapse;
    border-bottom:4px solid #333;
    margin-bottom:25px;
}

.header-table td{
    vertical-align:top;
    padding:15px;
}

.title{
    text-align:center;
}

.title h1{
    margin:0;
    letter-spacing:2px;
}

.address-table, .items-table, .totals-table{
    width:100%;
    border-collapse:collapse;
}

.address-table td{
    padding:10px;
    vertical-align:top;
}

.section-title{
    font-weight:bold;
    text-transform:uppercase;
    font-size:12px;
    margin-bottom:5px;
}

.address-text{
    font-size:13px;
    line-height:1.4;
}

.items-table{
    margin-bottom:20px;
}

.items-table th{
    background:#444;
    color:#fff;
    padding:8px;
    font-size:12px;
    border:1px solid #333;
    text-transform:uppercase;
}

.items-table td{
    border:1px solid #ccc;
    padding:8px;
    font-size:13px;
}

.text-right{ text-align:right; }
.text-center{ text-align:center; }

.totals-wrapper{
    width:100%;
}

.totals-table{
    width:320px;
    border-collapse:collapse;
    margin-left:auto;
}

.totals-table td{
    padding:7px;
    border:1px solid #ccc;
}

.total-label{
    background:#444;
    color:#fff;
    font-weight:bold;
}

.grand-total{
    font-weight:bold;
    font-size:16px;
}

.footer{
    margin-top:25px;
    border-top:1px solid #ccc;
    padding-top:10px;
    text-align:center;
    font-size:12px;
}

thead{ display:table-header-group; }
tr{ page-break-inside:avoid; }
"""


# ------------------------------ POS renderer ------------------------------

def _render_pos(spec: dict) -> str:
    main = spec["mainData"]
    details = spec["detailsData"]
    header = spec.get("header", {}) or {}
    columns = spec.get("columns") or []
    totals = spec.get("totals") or []
    grand = spec.get("grandTotal")
    footer_text = spec.get("footer") or ""

    company_fields = header.get("companyFields") or []
    info_fields = header.get("infoFields") or []
    party_label = header.get("partyLabel") or ""
    party_fields = header.get("partyFields") or []
    show_logo = bool(header.get("showLogo", True))

    out: list[str] = []
    out.append("<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"UTF-8\">\n")
    if spec.get("title"):
        out.append(f"<title>{_esc(spec['title'])}</title>\n")
    out.append("\n<style>\n\n")
    out.append(_POS_CSS)
    out.append("\n</style>\n</head>\n\n<body>\n\n")
    out.append("<div class=\"receipt\">\n\n")

    # Company header
    out.append("<!-- Company Header -->\n\n")
    out.append("<table class=\"header-layout\">\n<tr>\n")
    if show_logo:
        out.append("<td class=\"logo-cell\">\n")
        out.append("<img class=\"logo\" src=\"data:image/png;base64,{{image}}\" alt=\"logo\"/>\n")
        out.append("</td>\n\n")
        out.append("<td class=\"company-cell\">\n")
    else:
        out.append("<td colspan=\"2\" class=\"company-cell\">\n")

    if company_fields:
        first, *rest = company_fields
        out.append("<b>{{" + main + "." + first + "}}</b>")
        for f in rest:
            out.append("<br>\n{{" + main + "." + f + "}}")
        out.append("\n")
    out.append("</td>\n</tr>\n</table>\n\n")
    out.append("<div class=\"line\"></div>\n\n")

    # Info block (date, doc no, etc) + party
    if info_fields or party_fields:
        out.append("<div>\n\n")
        for f in info_fields:
            out.append(_esc(f["label"]) + " : {{" + main + "." + f["field"] + "}} <br>\n\n")
        if party_label and party_fields:
            for i, fld in enumerate(party_fields):
                lbl = party_label if i == 0 else _esc(fld).title()
                out.append(_esc(lbl) + " : {{" + main + "." + fld + "}} <br>\n\n")
        out.append("</div>\n\n")
        out.append("<div class=\"line\"></div>\n\n")

    # Items table
    if columns:
        out.append("<table>\n\n<tr class=\"header-table\">\n")
        for c in columns:
            align = c.get("align", "left")
            width = c.get("width", "")
            w_attr = f' width="{_esc(width)}"' if width else ""
            out.append(f'    <th class="{align}"{w_attr}>{_esc(c["label"])}</th>\n')
        out.append("</tr>\n\n")

        out.append("{{#each " + details + "}}\n\n")
        # Product full-width row
        col_count = len(columns)
        out.append(f'<tr>\n<td colspan="{col_count}">\n')
        out.append('<span class="item-name">{{this.product}}</span>\n</td>\n</tr>\n\n')

        # Values row
        out.append('<tr class="item-values">\n\n')
        for c in columns:
            align = c.get("align", "left")
            field = c["field"]
            default = c.get("default", "")
            suffix = c.get("suffix", "")
            value_expr = _hbs_value("this." + field, default)
            if suffix:
                out.append(
                    f'<td class="{align}">\n'
                    f'<div style="white-space:nowrap;">\n'
                    f'{value_expr}{_esc(suffix)}\n'
                    f'</div>\n</td>\n\n'
                )
            else:
                out.append(f'<td class="{align}">\n{value_expr}\n</td>\n\n')
        out.append("</tr>\n\n")
        out.append("{{/each}}\n\n</table>\n\n")

    # Totals
    if totals or grand:
        out.append('<table class="totals-table">\n\n')
        for i, t in enumerate(totals):
            width_style = ' style="width:70%;"' if i == 0 else ""
            out.append(
                f'<tr>\n<td class="right"{width_style}>{_esc(t["label"])} -</td>\n'
                f'<td class="right">\n'
                f'{_hbs_value(main + "." + t["field"], t.get("default", "0.00"))}\n'
                f'</td>\n</tr>\n\n'
            )
        if grand:
            out.append('<tr style="font-size:13px;font-weight:bold;">\n')
            out.append(f'<td class="right">{_esc(grand["label"])} -</td>\n')
            out.append(
                '<td class="right">\n'
                + _hbs_value(main + "." + grand["field"], grand.get("default", "0.00"))
                + "\n</td>\n</tr>\n\n"
            )
        out.append("</table>\n\n")

    # Footer
    if footer_text:
        out.append('<div class="footer">\n\n')
        out.append("<br>\n".join(_esc(line) for line in footer_text.splitlines() if line))
        out.append("\n\n</div>\n\n")

    out.append("</div>\n\n</body>\n</html>\n")
    return "".join(out)


# ------------------------------- A4 renderer ------------------------------

def _render_a4(spec: dict) -> str:
    main = spec["mainData"]
    details = spec["detailsData"]
    title = spec.get("title") or ""
    header = spec.get("header", {}) or {}
    columns = spec.get("columns") or []
    totals = spec.get("totals") or []
    grand = spec.get("grandTotal")
    footer_text = spec.get("footer") or ""

    company_fields = header.get("companyFields") or []
    info_fields = header.get("infoFields") or []
    party_label = header.get("partyLabel") or "Customer"
    party_fields = header.get("partyFields") or []

    out: list[str] = []
    out.append('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n')
    if title:
        out.append(f"<title>{_esc(title)}</title>\n")
    out.append("\n<style>\n\n")
    out.append(_A4_CSS)
    out.append("\n</style>\n</head>\n\n<body>\n\n")

    # Header
    out.append("<!-- HEADER -->\n\n")
    out.append('<table class="header-table">\n\n')
    if title:
        out.append('<tr>\n<td colspan="2" class="title">\n')
        out.append(f"<h1>{_esc(title)}</h1>\n</td>\n</tr>\n\n")

    out.append("<tr>\n<td>\n")
    if company_fields:
        first, *rest = company_fields
        out.append("<strong>{{" + main + "." + first + "}}</strong>")
        for f in rest:
            out.append("<br>\n{{" + main + "." + f + "}}")
        out.append("\n")
    out.append("</td>\n\n")
    out.append('<td style="text-align:right">\n')
    for f in info_fields:
        out.append(
            f"<strong>{_esc(f['label'])}:</strong> "
            "{{" + main + "." + f["field"] + "}}<br>\n"
        )
    out.append("</td>\n</tr>\n\n</table>\n\n")

    # Party block
    if party_fields:
        out.append('<table class="address-table">\n<tr>\n<td>\n')
        out.append(f'<div class="section-title">{_esc(party_label)}</div>\n')
        out.append('<div class="address-text">\n')
        if party_fields:
            first, *rest = party_fields
            out.append("<strong>{{" + main + "." + first + "}}</strong>")
            for f in rest:
                out.append("<br>\n{{" + main + "." + f + "}}")
            out.append("\n")
        out.append("</div>\n</td>\n</tr>\n</table>\n\n")

    # Items
    if columns:
        out.append('<table class="items-table">\n\n<thead>\n<tr>\n')
        for c in columns:
            align = c.get("align", "left")
            width = c.get("width", "")
            cls = ""
            if align == "right":
                cls = ' class="text-right"'
            elif align == "center":
                cls = ' class="text-center"'
            w_attr = f' width="{_esc(width)}"' if width else ""
            out.append(f"<th{cls}{w_attr}>{_esc(c['label'])}</th>\n")
        out.append("</tr>\n</thead>\n\n<tbody>\n\n")

        out.append("{{#each " + details + "}}\n\n")
        out.append("<tr>\n")
        # First col is always product description
        first_col = columns[0]
        out.append(
            f'<td><strong>{{{{this.{first_col.get("field", "product")}}}}}</strong></td>\n'
        )
        for c in columns[1:]:
            align = c.get("align", "left")
            cls = ""
            if align == "right":
                cls = ' class="text-right"'
            elif align == "center":
                cls = ' class="text-center"'
            field = c["field"]
            default = c.get("default", "")
            suffix = c.get("suffix", "")
            value_expr = _hbs_value("this." + field, default)
            out.append(f"<td{cls}>{value_expr}{_esc(suffix)}</td>\n")
        out.append("</tr>\n\n")
        out.append("{{/each}}\n\n</tbody>\n</table>\n\n")

    # Totals
    if totals or grand:
        out.append('<div class="totals-wrapper">\n')
        out.append('<table class="totals-table">\n\n')
        for t in totals:
            out.append(
                f'<tr>\n<td class="total-label">{_esc(t["label"])}</td>\n'
                f'<td class="text-right">'
                f'{_hbs_value(main + "." + t["field"], t.get("default", "0.00"))}'
                f"</td>\n</tr>\n\n"
            )
        if grand:
            out.append('<tr class="grand-total">\n')
            out.append(f'<td class="total-label">{_esc(grand["label"])}</td>\n')
            out.append(
                '<td class="text-right">'
                + _hbs_value(main + "." + grand["field"], grand.get("default", "0.00"))
                + "</td>\n</tr>\n\n"
            )
        out.append("</table>\n</div>\n\n")

    # Footer
    if footer_text:
        out.append('<div class="footer">\n')
        out.append("<br>\n".join(_esc(line) for line in footer_text.splitlines() if line))
        out.append("\n</div>\n\n")

    out.append("</body>\n</html>\n")
    return "".join(out)


# -------------------------------- Public API ------------------------------

def build(spec: dict) -> str:
    """Return the Handlebars-flavoured HTML for the given spec."""
    style = (spec.get("style") or "pos").lower()
    if style == "pos":
        return _render_pos(spec)
    if style == "a4":
        return _render_a4(spec)
    raise ValueError(f"Unknown style: {style!r} (expected 'pos' or 'a4')")
