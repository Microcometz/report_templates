"""Sample data used by the live preview.

The keys `mainData` and `detailsData` from the spec are mapped onto the
data dict so the generic preview values show up under whatever namespace
the user picked (e.g. `purchaseMainData`, `invoiceMainData`).
"""

from __future__ import annotations

# 1x1 transparent PNG so the <img> tag renders at logo size in the preview.
LOGO_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8A"
    "AAAASUVORK5CYII="
)

_MAIN = {
    "companyName": "ACME TRADING LLC",
    "companyAddress": "Building 42, Block C, Industrial Area, Dubai, UAE",
    "companyPhone": "+971 4 123 4567",
    "email": "info@acme.example",

    "docCode": "INV-2026-00042",
    "docDate": "26/04/2026",
    "documentNumber": "INV-2026-00042",
    "documentDate": "26/04/2026",

    "customer": "John Smith",
    "mobile": "+971 50 555 1234",
    "supplier": "Global Supply Co",
    "partyName": "Global Supply Co",
    "partyAddress": "Warehouse 7, Jebel Ali, Dubai, UAE",
    "contactPerson": "Sara Khan",

    "shippingAddress": "Building 42, Block C, Dubai, UAE",
    "shipmentTerms": "FOB",
    "deliveryTerms": "7 working days",
    "paymentTerms": "Net 30",

    "grossAmount": "1,250.00",
    "itemDiscount": "25.00",
    "invoiceDiscount": "50.00",
    "couponDiscount": "10.00",
    "ireturnDiscount": "15.00",
    "taxAmount": "62.50",
    "invoiceTotal": "1,227.50",
    "ireturnTotal": "615.00",
    "totalAmount": "1,312.50",
}

_DETAILS = [
    {
        "product": "WIRELESS MOUSE",
        "description": "2.4GHz USB receiver, 1600 DPI",
        "qty": 2,
        "rate": "75.00",
        "grossAmount": "150.00",
        "discount": "5.00",
        "taxAmount": "7.25",
        "netAmount": "152.25",
    },
    {
        "product": "MECHANICAL KEYBOARD",
        "description": "Tenkeyless, blue switches",
        "qty": 1,
        "rate": "320.00",
        "grossAmount": "320.00",
        "discount": "0.00",
        "taxAmount": "16.00",
        "netAmount": "336.00",
    },
    {
        "product": "27\" 4K MONITOR",
        "description": "IPS, HDR400",
        "qty": 1,
        "rate": "780.00",
        "grossAmount": "780.00",
        "discount": "20.00",
        "taxAmount": "38.00",
        "netAmount": "798.00",
    },
]


def for_spec(spec: dict) -> dict:
    """Build a Handlebars-render data dict for the given spec."""
    main_key = spec.get("mainData") or "mainData"
    details_key = spec.get("detailsData") or "detailsData"
    return {
        "image": LOGO_BASE64,
        main_key: dict(_MAIN),
        details_key: [dict(item) for item in _DETAILS],
    }


# Namespaces used by the existing templates in this repo. We supply the
# same sample data under every namespace so opening any template in the
# editor yields a sensible preview.
_KNOWN_MAIN_NAMESPACES = (
    "mainData",
    "invoiceMainData",
    "invoiceReturnMainData",
    "poMainData",
    "piMainData",
    "grnMainData",
)
_KNOWN_DETAIL_NAMESPACES = (
    "detailsData",
    "invoiceDetailsData",
    "invoiceReturnDetailsData",
    "poDetailsData",
    "piDetailsData",
    "grnDetailsData",
    "items",  # used by the barcode template
)


def for_any() -> dict:
    """Return sample data covering every namespace seen in the repo so
    arbitrary templates can be previewed without needing a spec."""
    data: dict = {"image": LOGO_BASE64, "barcodes": {}}
    for key in _KNOWN_MAIN_NAMESPACES:
        data[key] = dict(_MAIN)
    for key in _KNOWN_DETAIL_NAMESPACES:
        data[key] = [dict(item) for item in _DETAILS]
    # Barcode template uses a few extra item fields.
    for item in data["items"]:
        item.setdefault("productName", item.get("product"))
        item.setdefault("price", "75.00")
        item.setdefault("sku", "SKU-00042")
        item.setdefault("batchNo", "B-2026-04")
        item.setdefault("barcodeKey", "k1")
        item.setdefault("barcodeValue", "5901234123457")
    return data
