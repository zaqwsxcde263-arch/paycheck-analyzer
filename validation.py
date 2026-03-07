"""Validation for cost form items."""
from datetime import datetime
from typing import Any


def validate_cost_item(
    item: dict[str, Any],
    *,
    category_ids: set[int],
    product_ids: set[int],
    product_to_category: dict[int, int],
) -> tuple[bool, dict[str, str]]:
    """
    Validate a single cost item. Returns (is_valid, errors_dict).
    """
    errors: dict[str, str] = {}

    # date
    raw_date = item.get("date")
    if not raw_date or not str(raw_date).strip():
        errors["date"] = "Date is required."
    else:
        try:
            datetime.strptime(str(raw_date).strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            errors["date"] = "Invalid date format (use YYYY-MM-DD)."

    # price
    raw_price = item.get("price")
    if raw_price is None or raw_price == "":
        errors["price"] = "Price is required."
    else:
        try:
            p = float(raw_price)
            if p <= 0:
                errors["price"] = "Price must be greater than 0."
        except (TypeError, ValueError):
            errors["price"] = "Price must be a number."

    # category
    raw_cat = item.get("category_id") or item.get("category")
    if raw_cat is None or raw_cat == "":
        errors["category"] = "Category is required."
    else:
        try:
            cid = int(raw_cat)
            if cid not in category_ids:
                errors["category"] = "Invalid category."
        except (TypeError, ValueError):
            errors["category"] = "Invalid category."

    # product
    raw_prod = item.get("product_id") or item.get("product")
    if raw_prod is None or raw_prod == "":
        errors["product"] = "Product is required."
    else:
        try:
            pid = int(raw_prod)
            if pid not in product_ids:
                errors["product"] = "Invalid product."
            elif "category_id" not in errors and "category" not in errors:
                cat_id = int(raw_cat) if raw_cat else None
                if cat_id is not None and product_to_category.get(pid) != cat_id:
                    errors["product"] = "Product does not belong to selected category."
        except (TypeError, ValueError):
            errors["product"] = "Invalid product."

    # quantity
    raw_qty = item.get("quantity")
    if raw_qty is None or raw_qty == "":
        errors["quantity"] = "Quantity is required."
    else:
        try:
            q = int(raw_qty)
            if q < 1:
                errors["quantity"] = "Quantity must be at least 1."
        except (TypeError, ValueError):
            errors["quantity"] = "Quantity must be a whole number."

    return (len(errors) == 0, errors)
