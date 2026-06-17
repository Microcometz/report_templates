"""Built-in design presets.

Each preset is a self-contained design dict ready to feed into
`designer.render_design`. They mirror the document types found in the
existing repo (sales invoice POS, sales invoice A4, purchase order,
GRN) so users can pick one and tweak.
"""

from __future__ import annotations

from copy import deepcopy
from itertools import count


_id = count(1)


def _b(t: str, **cfg) -> dict:
    """Shorthand: build a block."""
    return {"id": f"b{next(_id)}", "type": t, "config": cfg}


# --------------------------- Sales Invoice (POS) --------------------------

SALES_INVOICE_POS: dict = {
    "name":  "salesInvoicePOS",
    "title": "SALES INVOICE",
    "data":  {"main": "invoiceMainData", "details": "invoiceDetailsData"},
    "page":  {"size": "80mm", "margin": "3mm", "orientation": "portrait"},
    "theme": {"preset": "pos"},
    "blocks": [
        _b("company-header",
            showLogo=True, layout="two-col", logoField="image",
            fields=["companyName", "companyAddress", "companyPhone"]),
        _b("divider", style="dashed", thickness="1px", spacing="6px"),
        _b("info-row",
            layout="stacked",
            items=[
                {"label": "Date",     "field": "docDate"},
                {"label": "Invoice",  "field": "docCode"},
                {"label": "Customer", "field": "customer"},
                {"label": "Phone",    "field": "mobile"},
            ]),
        _b("divider", style="dashed", thickness="1px", spacing="6px"),
        _b("items-table",
            showHeader=True, headerStyle="underline", productAsRow=True,
            columns=[
                {"label": "QTY",     "field": "qty",         "align": "left",  "width": "14%", "default": "0",    "suffix": " PCS"},
                {"label": "RATE",    "field": "rate",        "align": "right", "width": "17%", "default": "0.00"},
                {"label": "GROSS",   "field": "grossAmount", "align": "right", "width": "17%", "default": "0.00"},
                {"label": "DISC",    "field": "discount",    "align": "right", "width": "16%", "default": "0.00"},
                {"label": "TAX",     "field": "taxAmount",   "align": "right", "width": "16%", "default": "0.00"},
                {"label": "N.TOTAL", "field": "netAmount",   "align": "right", "width": "20%", "default": "0.00"},
            ]),
        _b("totals-table",
            style="underline",
            rows=[
                {"label": "Gross Total",          "field": "grossAmount",     "default": "0.00"},
                {"label": "(-) Item Discount",    "field": "itemDiscount",    "default": "0.00"},
                {"label": "(-) Invoice Discount", "field": "invoiceDiscount", "default": "0.00"},
                {"label": "(-) Coupon Discount",  "field": "couponDiscount",  "default": "0.00"},
                {"label": "(-) Total Tax",        "field": "taxAmount",       "default": "0.00"},
            ]),
        _b("grand-total",
            label="(=) Net Amount", field="invoiceTotal",
            default="0.00", fontSize="13px"),
        _b("spacer", height="8px"),
        _b("footer", text="Thank you for shopping with us\nVISIT AGAIN!", align="center"),
    ],
}


# --------------------------- Sales Invoice (A4) ---------------------------

SALES_INVOICE_A4: dict = {
    "name":  "salesInvoiceReport",
    "title": "SALES INVOICE",
    "data":  {"main": "invoiceMainData", "details": "invoiceDetailsData"},
    "page":  {"size": "a4", "margin": "20mm", "orientation": "portrait"},
    "theme": {"preset": "a4-modern"},
    "blocks": [
        _b("title", text="SALES INVOICE", level=1, align="center"),
        _b("company-header",
            showLogo=False, layout="two-col",
            fields=["companyName", "companyAddress", "companyPhone"]),
        _b("info-row",
            layout="right-aligned",
            items=[
                {"label": "INVOICE", "field": "docCode"},
                {"label": "DATE",    "field": "docDate"},
            ]),
        _b("party-block",
            columns=[
                {"label": "Customer", "fields": ["customer", "mobile"]},
            ]),
        _b("items-table",
            showHeader=True, headerStyle="dark", productAsRow=False,
            columns=[
                {"label": "Description", "field": "product",     "align": "left",   "width": "35%"},
                {"label": "Qty",         "field": "qty",         "align": "center", "width": "10%", "default": "0", "suffix": " PCS"},
                {"label": "Rate",        "field": "rate",        "align": "right",  "width": "15%", "default": "0.00"},
                {"label": "Gross",       "field": "grossAmount", "align": "right",  "width": "15%", "default": "0.00"},
                {"label": "Discount",    "field": "discount",    "align": "right",  "width": "10%", "default": "0.00"},
                {"label": "Net",         "field": "netAmount",   "align": "right",  "width": "15%", "default": "0.00"},
            ]),
        _b("totals-table",
            style="bordered",
            rows=[
                {"label": "Gross Total",      "field": "grossAmount",     "default": "0.00"},
                {"label": "Item Discount",    "field": "itemDiscount",    "default": "0.00"},
                {"label": "Invoice Discount", "field": "invoiceDiscount", "default": "0.00"},
                {"label": "Coupon Discount",  "field": "couponDiscount",  "default": "0.00"},
            ]),
        _b("grand-total", label="Net Total", field="invoiceTotal", default="0.00", fontSize="16px"),
        _b("spacer", height="20px"),
        _b("footer", text="Thank you for your business", align="center"),
    ],
}


# ----------------------------- Purchase Order -----------------------------

PURCHASE_ORDER_A4: dict = {
    "name":  "purchaseOrder",
    "title": "PURCHASE ORDER",
    "data":  {"main": "poMainData", "details": "poDetailsData"},
    "page":  {"size": "a4", "margin": "20mm", "orientation": "portrait"},
    "theme": {"preset": "a4-modern"},
    "blocks": [
        _b("title", text="PURCHASE ORDER", level=1, align="center"),
        _b("company-header",
            showLogo=False, layout="two-col",
            fields=["companyName", "companyAddress", "email"]),
        _b("info-row",
            layout="right-aligned",
            items=[
                {"label": "PO NUMBER", "field": "documentNumber"},
                {"label": "DATE",      "field": "documentDate"},
            ]),
        _b("party-block",
            columns=[
                {"label": "Vendor",   "fields": ["partyName", "partyAddress", "contactPerson"]},
                {"label": "Ship To",  "fields": ["companyName", "shippingAddress"]},
            ]),
        _b("meta-table",
            title="Order Details",
            rows=[
                {"label": "Shipment Terms", "field": "shipmentTerms"},
                {"label": "Delivery Terms", "field": "deliveryTerms"},
                {"label": "Payment Terms",  "field": "paymentTerms"},
            ]),
        _b("items-table",
            showHeader=True, headerStyle="dark", productAsRow=False,
            columns=[
                {"label": "Description", "field": "product",     "align": "left",   "width": "40%"},
                {"label": "Qty",         "field": "qty",         "align": "center", "width": "15%", "default": "0"},
                {"label": "Unit Price",  "field": "rate",        "align": "right",  "width": "20%", "default": "0.00"},
                {"label": "Total",       "field": "grossAmount", "align": "right",  "width": "25%", "default": "0.00"},
            ]),
        _b("totals-table",
            style="bordered",
            rows=[
                {"label": "Subtotal", "field": "grossAmount", "default": "0.00"},
                {"label": "Tax",      "field": "taxAmount",   "default": "0.00"},
            ]),
        _b("grand-total", label="TOTAL", field="totalAmount", default="0.00", fontSize="16px"),
        _b("spacer", height="20px"),
        _b("footer", text="{{poMainData.companyName}}", align="center"),
    ],
}


# --------------------------------- GRN ------------------------------------

GRN_A4: dict = {
    "name":  "grnReport",
    "title": "GOODS RECEIVED NOTE",
    "data":  {"main": "grnMainData", "details": "grnDetailsData"},
    "page":  {"size": "a4", "margin": "20mm", "orientation": "portrait"},
    "theme": {"preset": "a4-modern"},
    "blocks": [
        _b("title", text="GOODS RECEIVED NOTE", level=1, align="center"),
        _b("company-header",
            showLogo=False, layout="two-col",
            fields=["companyName", "companyAddress"]),
        _b("info-row",
            layout="right-aligned",
            items=[
                {"label": "GRN No", "field": "documentNumber"},
                {"label": "Date",   "field": "documentDate"},
            ]),
        _b("party-block",
            columns=[
                {"label": "Supplier", "fields": ["partyName", "partyAddress", "contactPerson", "contactNumber"]},
            ]),
        _b("meta-table",
            title="Supplier DN",
            rows=[
                {"label": "DN Number", "field": "supplierDnNo"},
                {"label": "DN Date",   "field": "supplierDnDate"},
                {"label": "PO Numbers", "field": "poDocCodes"},
            ]),
        _b("items-table",
            showHeader=True, headerStyle="dark", productAsRow=False,
            columns=[
                {"label": "Product",  "field": "product",     "align": "left",   "width": "20%"},
                {"label": "Brand",    "field": "brand",       "align": "center", "width": "10%"},
                {"label": "Unit",     "field": "unit",        "align": "center", "width": "8%"},
                {"label": "Qty",      "field": "qty",         "align": "center", "width": "8%"},
                {"label": "Rate",     "field": "rate",        "align": "right",  "width": "12%", "default": "0.00"},
                {"label": "Gross",    "field": "grossAmount", "align": "right",  "width": "12%", "default": "0.00"},
                {"label": "Discount", "field": "discount",    "align": "right",  "width": "10%", "default": "0.00"},
                {"label": "Tax",      "field": "taxAmount",   "align": "right",  "width": "10%", "default": "0.00"},
                {"label": "Net",      "field": "netAmount",   "align": "right",  "width": "10%", "default": "0.00"},
            ]),
        _b("totals-table",
            style="bordered",
            rows=[
                {"label": "Gross",    "field": "grossAmount",    "default": "0.00"},
                {"label": "Discount", "field": "discountAmount", "default": "0.00"},
                {"label": "Tax",      "field": "taxAmount",      "default": "0.00"},
            ]),
        _b("grand-total", label="Total", field="totalAmount", default="0.00", fontSize="16px"),
        _b("spacer", height="20px"),
        _b("text", content="Remarks: {{grnMainData.remarks}}", align="left", size="12px"),
    ],
}


# ----------------------------- Blank -------------------------------------

BLANK: dict = {
    "name":   "newTemplate",
    "title":  "NEW TEMPLATE",
    "data":   {"main": "mainData", "details": "detailsData"},
    "page":   {"size": "a4", "margin": "20mm", "orientation": "portrait"},
    "theme":  {"preset": "a4-modern"},
    "blocks": [],
}


PRESETS: dict[str, dict] = {
    "Blank":                          BLANK,
    "Sales Invoice (POS receipt)":    SALES_INVOICE_POS,
    "Sales Invoice (A4 report)":      SALES_INVOICE_A4,
    "Purchase Order (A4)":            PURCHASE_ORDER_A4,
    "Goods Received Note (A4)":       GRN_A4,
}


def get(name: str) -> dict:
    return deepcopy(PRESETS[name])


def names() -> list[str]:
    return list(PRESETS.keys())
