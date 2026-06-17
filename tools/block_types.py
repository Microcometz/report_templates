"""Schema metadata for every block the designer supports.

Each block type is described as:

    {
        "type":         identifier used in the design's block list
        "label":        human-readable name (shown in palette / list)
        "icon":         single character / emoji shown next to the label
        "category":     "header" | "content" | "items" | "totals" | "layout"
        "description":  short tooltip
        "defaultConfig": dict used when adding a new block
        "fields":       list of editor fields rendered in the per-block panel
    }

A field is one of:

    {"k": "label",    "type": "text",   "label": "Label", "placeholder": "..."}
    {"k": "align",    "type": "select", "label": "Align", "options": ["left", "right", "center"]}
    {"k": "showLogo", "type": "checkbox", "label": "Show logo"}
    {"k": "items",    "type": "list", "label": "Items", "fields": [...inner...]}
    {"k": "content",  "type": "textarea", "label": "Content", "rows": 4}
"""

from __future__ import annotations


_F_ALIGN = {
    "k": "align",
    "type": "select",
    "label": "Align",
    "options": [
        {"value": "left", "label": "Left"},
        {"value": "center", "label": "Center"},
        {"value": "right", "label": "Right"},
    ],
}


BLOCK_TYPES: list[dict] = [
    {
        "type": "title",
        "label": "Title",
        "icon": "T",
        "category": "header",
        "description": "Large centered heading (e.g. SALES INVOICE).",
        "defaultConfig": {"text": "TITLE", "level": 1, "align": "center"},
        "fields": [
            {"k": "text",  "type": "text",  "label": "Text", "placeholder": "SALES INVOICE"},
            {"k": "level", "type": "select", "label": "Heading level",
             "options": [{"value": 1, "label": "H1"}, {"value": 2, "label": "H2"}, {"value": 3, "label": "H3"}]},
            _F_ALIGN,
        ],
    },
    {
        "type": "company-header",
        "label": "Company header",
        "icon": "C",
        "category": "header",
        "description": "Company logo + name/address/phone block.",
        "defaultConfig": {
            "showLogo": False,
            "logoField": "image",
            "fields": ["companyName", "companyAddress", "companyPhone"],
            "layout": "centered",
        },
        "fields": [
            {"k": "showLogo",  "type": "checkbox", "label": "Show logo"},
            {"k": "logoField", "type": "text",     "label": "Logo data field", "placeholder": "image"},
            {"k": "layout",    "type": "select",   "label": "Layout",
             "options": [
                 {"value": "centered", "label": "Centered"},
                 {"value": "two-col",  "label": "Logo + text (two columns)"},
             ]},
            {"k": "fields", "type": "csv", "label": "Fields (comma-separated)",
             "placeholder": "companyName,companyAddress,companyPhone"},
        ],
    },
    {
        "type": "info-row",
        "label": "Info row",
        "icon": "i",
        "category": "header",
        "description": "Labelled fields like Date, Doc #, Customer.",
        "defaultConfig": {
            "layout": "stacked",
            "items": [
                {"label": "Date",     "field": "docDate"},
                {"label": "Document", "field": "docCode"},
            ],
        },
        "fields": [
            {"k": "layout", "type": "select", "label": "Layout",
             "options": [
                 {"value": "stacked",       "label": "Stacked (label : value)"},
                 {"value": "two-col",       "label": "Two-column table"},
                 {"value": "right-aligned", "label": "Right-aligned"},
             ]},
            {"k": "items", "type": "list", "label": "Items",
             "fields": [
                 {"k": "label", "type": "text", "label": "Label"},
                 {"k": "field", "type": "text", "label": "Data field"},
             ]},
        ],
    },
    {
        "type": "party-block",
        "label": "Party block",
        "icon": "P",
        "category": "header",
        "description": "Customer / vendor / ship-to columns.",
        "defaultConfig": {
            "columns": [
                {"label": "Customer", "fields": ["customer", "mobile"]},
            ],
        },
        "fields": [
            {"k": "columns", "type": "list", "label": "Columns",
             "fields": [
                 {"k": "label",  "type": "text", "label": "Column label"},
                 {"k": "fields", "type": "csv",  "label": "Fields (comma-separated)"},
             ]},
        ],
    },
    {
        "type": "meta-table",
        "label": "Meta table",
        "icon": "M",
        "category": "content",
        "description": "Small key/value table (Order Details, Currency, ...).",
        "defaultConfig": {
            "title": "",
            "rows": [{"label": "Currency", "field": "currencyId"}],
        },
        "fields": [
            {"k": "title", "type": "text", "label": "Title (optional)"},
            {"k": "rows", "type": "list", "label": "Rows",
             "fields": [
                 {"k": "label", "type": "text", "label": "Label"},
                 {"k": "field", "type": "text", "label": "Data field"},
             ]},
        ],
    },
    {
        "type": "items-table",
        "label": "Items table",
        "icon": "#",
        "category": "items",
        "description": "Main repeating product/items table.",
        "defaultConfig": {
            "showHeader": True,
            "headerStyle": "underline",
            "productAsRow": False,
            "columns": [
                {"label": "Description", "field": "product",     "align": "left",   "width": "40%"},
                {"label": "Qty",         "field": "qty",         "align": "center", "width": "10%", "default": "0"},
                {"label": "Rate",        "field": "rate",        "align": "right",  "width": "20%", "default": "0.00"},
                {"label": "Net",         "field": "netAmount",   "align": "right",  "width": "30%", "default": "0.00"},
            ],
        },
        "fields": [
            {"k": "showHeader", "type": "checkbox", "label": "Show header row"},
            {"k": "headerStyle", "type": "select", "label": "Header style",
             "options": [
                 {"value": "underline", "label": "Underline (POS)"},
                 {"value": "dark",      "label": "Dark fill"},
                 {"value": "bordered",  "label": "Bordered"},
             ]},
            {"k": "productAsRow", "type": "checkbox",
             "label": "Product name on its own row (POS layout)"},
            {"k": "columns", "type": "list", "label": "Columns",
             "fields": [
                 {"k": "label",   "type": "text",   "label": "Header"},
                 {"k": "field",   "type": "text",   "label": "Data field"},
                 {"k": "align",   "type": "select", "label": "Align",
                  "options": [
                      {"value": "left",   "label": "Left"},
                      {"value": "center", "label": "Center"},
                      {"value": "right",  "label": "Right"},
                  ]},
                 {"k": "width",   "type": "text", "label": "Width", "placeholder": "20%"},
                 {"k": "default", "type": "text", "label": "Default if empty"},
                 {"k": "suffix",  "type": "text", "label": "Suffix (e.g. ' PCS')"},
             ]},
        ],
    },
    {
        "type": "totals-table",
        "label": "Totals",
        "icon": "\u03A3",
        "category": "totals",
        "description": "Right-aligned totals rows.",
        "defaultConfig": {
            "style": "underline",
            "rows": [
                {"label": "Gross Total",   "field": "grossAmount", "default": "0.00"},
                {"label": "Tax",           "field": "taxAmount",   "default": "0.00"},
                {"label": "Discount",      "field": "discountAmount", "default": "0.00"},
            ],
        },
        "fields": [
            {"k": "style", "type": "select", "label": "Style",
             "options": [
                 {"value": "underline", "label": "Underline"},
                 {"value": "bordered",  "label": "Bordered"},
             ]},
            {"k": "rows", "type": "list", "label": "Rows",
             "fields": [
                 {"k": "label",   "type": "text", "label": "Label"},
                 {"k": "field",   "type": "text", "label": "Data field"},
                 {"k": "default", "type": "text", "label": "Default"},
             ]},
        ],
    },
    {
        "type": "grand-total",
        "label": "Grand total",
        "icon": "=",
        "category": "totals",
        "description": "Emphasised final total row.",
        "defaultConfig": {
            "label": "TOTAL",
            "field": "totalAmount",
            "default": "0.00",
            "fontSize": "14px",
        },
        "fields": [
            {"k": "label",    "type": "text", "label": "Label"},
            {"k": "field",    "type": "text", "label": "Data field"},
            {"k": "default",  "type": "text", "label": "Default"},
            {"k": "fontSize", "type": "text", "label": "Font size", "placeholder": "14px"},
        ],
    },
    {
        "type": "footer",
        "label": "Footer",
        "icon": "F",
        "category": "header",
        "description": "Centered footer text (Thank you / Visit again).",
        "defaultConfig": {"text": "Thank you", "align": "center"},
        "fields": [
            {"k": "text",  "type": "textarea", "label": "Text", "rows": 3},
            _F_ALIGN,
        ],
    },
    {
        "type": "divider",
        "label": "Divider",
        "icon": "\u2014",
        "category": "layout",
        "description": "Horizontal rule (solid or dashed).",
        "defaultConfig": {"style": "dashed", "thickness": "1px", "spacing": "6px"},
        "fields": [
            {"k": "style", "type": "select", "label": "Style",
             "options": [
                 {"value": "solid",  "label": "Solid"},
                 {"value": "dashed", "label": "Dashed"},
                 {"value": "dotted", "label": "Dotted"},
                 {"value": "double", "label": "Double"},
             ]},
            {"k": "thickness", "type": "text", "label": "Thickness", "placeholder": "1px"},
            {"k": "spacing",   "type": "text", "label": "Spacing",   "placeholder": "6px"},
        ],
    },
    {
        "type": "spacer",
        "label": "Spacer",
        "icon": "\u2195",
        "category": "layout",
        "description": "Empty vertical space.",
        "defaultConfig": {"height": "10px"},
        "fields": [
            {"k": "height", "type": "text", "label": "Height", "placeholder": "10px"},
        ],
    },
    {
        "type": "text",
        "label": "Text",
        "icon": "\u00B6",
        "category": "content",
        "description": "Free text paragraph.",
        "defaultConfig": {"content": "", "align": "left", "size": "inherit", "bold": False},
        "fields": [
            {"k": "content", "type": "textarea", "label": "Text", "rows": 4},
            _F_ALIGN,
            {"k": "size", "type": "text", "label": "Font size", "placeholder": "inherit"},
            {"k": "bold", "type": "checkbox", "label": "Bold"},
        ],
    },
    {
        "type": "image",
        "label": "Image",
        "icon": "\u25A1",
        "category": "content",
        "description": "Embedded image (data URL field).",
        "defaultConfig": {"field": "image", "width": "75px", "align": "center"},
        "fields": [
            {"k": "field",  "type": "text", "label": "Data field", "placeholder": "image"},
            {"k": "width",  "type": "text", "label": "Width",      "placeholder": "75px"},
            {"k": "height", "type": "text", "label": "Height",     "placeholder": "(auto)"},
            _F_ALIGN,
        ],
    },
    {
        "type": "html",
        "label": "Raw HTML",
        "icon": "\u2329\u232A",
        "category": "content",
        "description": "Escape hatch for arbitrary HTML / Handlebars.",
        "defaultConfig": {"content": ""},
        "fields": [
            {"k": "content", "type": "textarea", "label": "HTML", "rows": 6},
        ],
    },
]


CATEGORIES: list[dict] = [
    {"id": "header",  "label": "Header"},
    {"id": "content", "label": "Content"},
    {"id": "items",   "label": "Items"},
    {"id": "totals",  "label": "Totals"},
    {"id": "layout",  "label": "Layout"},
]


def by_type(t: str) -> dict | None:
    for b in BLOCK_TYPES:
        if b["type"] == t:
            return b
    return None
