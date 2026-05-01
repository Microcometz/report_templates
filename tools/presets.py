"""Reusable spec presets.

These mirror the documents already in the repo and double as starting
points for new templates so the user only has to tweak a few fields.
"""

from __future__ import annotations

from copy import deepcopy


SALES_INVOICE_POS: dict = {
    "name": "salesInvoice",
    "style": "pos",
    "title": "SALES INVOICE",
    "mainData": "invoiceMainData",
    "detailsData": "invoiceDetailsData",
    "header": {
        "showLogo": True,
        "companyFields": ["companyName", "companyAddress", "companyPhone"],
        "infoFields": [
            {"label": "Date",     "field": "docDate"},
            {"label": "Invoice",  "field": "docCode"},
        ],
        "partyLabel": "Customer",
        "partyFields": ["customer", "mobile"],
    },
    "columns": [
        {"label": "QTY",     "field": "qty",         "align": "left",  "width": "14%", "default": "0",    "suffix": " PCS"},
        {"label": "RATE",    "field": "rate",        "align": "right", "width": "17%", "default": "0.00"},
        {"label": "GROSS",   "field": "grossAmount", "align": "right", "width": "17%", "default": "0.00"},
        {"label": "DISC",    "field": "discount",    "align": "right", "width": "16%", "default": "0.00"},
        {"label": "TAX",     "field": "taxAmount",   "align": "right", "width": "16%", "default": "0.00"},
        {"label": "N.TOTAL", "field": "netAmount",   "align": "right", "width": "20%", "default": "0.00"},
    ],
    "totals": [
        {"label": "Gross Total",         "field": "grossAmount",     "default": "0.00"},
        {"label": "(-) Item Discount",   "field": "itemDiscount",    "default": "0.00"},
        {"label": "(-) Invoice Discount","field": "invoiceDiscount", "default": "0.00"},
        {"label": "(-) Coupon Discount", "field": "couponDiscount",  "default": "0.00"},
        {"label": "(-) Total Tax",       "field": "taxAmount",       "default": "0.00"},
    ],
    "grandTotal": {"label": "(=) Net Amount", "field": "invoiceTotal", "default": "0.00"},
    "footer": "Thank you for shopping with us\nVISIT AGAIN!",
}


SALES_INVOICE_A4: dict = {
    "name": "salesInvoiceReport",
    "style": "a4",
    "title": "SALES INVOICE",
    "mainData": "invoiceMainData",
    "detailsData": "invoiceDetailsData",
    "header": {
        "showLogo": False,
        "companyFields": ["companyName", "companyAddress", "companyPhone"],
        "infoFields": [
            {"label": "INVOICE", "field": "docCode"},
            {"label": "DATE",    "field": "docDate"},
        ],
        "partyLabel": "Customer",
        "partyFields": ["customer", "mobile"],
    },
    "columns": [
        {"label": "Description", "field": "product",     "align": "left",   "width": "35%"},
        {"label": "Qty",         "field": "qty",         "align": "center", "width": "10%", "default": "0",    "suffix": " PCS"},
        {"label": "Rate",        "field": "rate",        "align": "right",  "width": "15%", "default": "0.00"},
        {"label": "Gross",       "field": "grossAmount", "align": "right",  "width": "15%", "default": "0.00"},
        {"label": "Discount",    "field": "discount",    "align": "right",  "width": "10%", "default": "0.00"},
        {"label": "Net",         "field": "netAmount",   "align": "right",  "width": "15%", "default": "0.00"},
    ],
    "totals": [
        {"label": "Gross Total",      "field": "grossAmount",     "default": "0.00"},
        {"label": "Item Discount",    "field": "itemDiscount",    "default": "0.00"},
        {"label": "Invoice Discount", "field": "invoiceDiscount", "default": "0.00"},
        {"label": "Coupon Discount",  "field": "couponDiscount",  "default": "0.00"},
    ],
    "grandTotal": {"label": "Net Total", "field": "invoiceTotal", "default": "0.00"},
    "footer": "Thank you for your business",
}


PURCHASE_ORDER_A4: dict = {
    "name": "purchaseOrder",
    "style": "a4",
    "title": "PURCHASE ORDER",
    "mainData": "poMainData",
    "detailsData": "poDetailsData",
    "header": {
        "showLogo": False,
        "companyFields": ["companyName", "companyAddress", "email"],
        "infoFields": [
            {"label": "PO NUMBER", "field": "documentNumber"},
            {"label": "DATE",      "field": "documentDate"},
        ],
        "partyLabel": "Vendor",
        "partyFields": ["partyName", "partyAddress", "contactPerson"],
    },
    "columns": [
        {"label": "Description", "field": "product",     "align": "left",   "width": "40%"},
        {"label": "Qty",         "field": "qty",         "align": "center", "width": "15%", "default": "0"},
        {"label": "Unit Price",  "field": "rate",        "align": "right",  "width": "20%", "default": "0.00"},
        {"label": "Total",       "field": "grossAmount", "align": "right",  "width": "25%", "default": "0.00"},
    ],
    "totals": [
        {"label": "Subtotal", "field": "grossAmount", "default": "0.00"},
        {"label": "Tax",      "field": "taxAmount",   "default": "0.00"},
    ],
    "grandTotal": {"label": "TOTAL", "field": "totalAmount", "default": "0.00"},
    "footer": "{{poMainData.companyName}}",
}


PRESETS: dict[str, dict] = {
    "Sales Invoice (POS receipt)":  SALES_INVOICE_POS,
    "Sales Invoice (A4 report)":    SALES_INVOICE_A4,
    "Purchase Order (A4)":          PURCHASE_ORDER_A4,
}


def get(name: str) -> dict:
    """Return a deep copy so callers can mutate freely."""
    return deepcopy(PRESETS[name])


def list_names() -> list[str]:
    return list(PRESETS.keys())
