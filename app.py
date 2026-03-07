"""PayCheck Analyzer - Flask application."""
import os
from flask import Flask, g, redirect, render_template, request, url_for

import db
from config import AVAILABLE_CURRENCIES, DEFAULT_CURRENCY
from validation import validate_cost_item

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")


@app.before_request
def before_request():
    db.init_db()
    g.currency = db.get_setting("currency") or DEFAULT_CURRENCY


@app.context_processor
def inject_currency():
    return {"currency": g.get("currency", DEFAULT_CURRENCY)}


@app.route("/")
def dashboard():
    count = db.count_costs()
    if count == 0:
        return render_template(
            "dashboard.html",
            empty=True,
            by_month=[],
            by_category=[],
            by_week=[],
        )
    return render_template(
        "dashboard.html",
        empty=False,
        by_month=db.stats_by_month(),
        by_category=db.stats_by_category(),
        by_week=db.stats_by_week(),
    )


@app.route("/paycheck/add", methods=["GET", "POST"])
def add_paycheck():
    categories = db.list_categories()
    products = db.list_products()
    products_by_category = {}
    for p in products:
        cid = p["category_id"]
        if cid not in products_by_category:
            products_by_category[cid] = []
        products_by_category[cid].append({"id": p["id"], "name": p["name"]})

    if not categories:
        return render_template(
            "add_paycheck.html",
            categories=[],
            products_by_category={},
            items=[],
            item_errors=[],
            no_categories=True,
        )

    if request.method == "GET":
        return render_template(
            "add_paycheck.html",
            categories=categories,
            products_by_category=products_by_category,
            items=[{}],
            item_errors=[],
            no_categories=False,
        )

    # POST: parse form items (items[0][date], items[0][price], ... or items_0_date, ...)
    raw = request.form
    items = []
    idx = 0
    while True:
        date_key = f"items_{idx}_date"
        if date_key not in raw and f"items[{idx}][date]" not in raw:
            break
        date = raw.get(f"items_{idx}_date") or raw.get(f"items[{idx}][date]")
        price = raw.get(f"items_{idx}_price") or raw.get(f"items[{idx}][price]")
        product_id = raw.get(f"items_{idx}_product_id") or raw.get(f"items[{idx}][product_id]")
        category_id = raw.get(f"items_{idx}_category_id") or raw.get(f"items[{idx}][category_id]")
        quantity = raw.get(f"items_{idx}_quantity") or raw.get(f"items[{idx}][quantity]")
        items.append({
            "date": date,
            "price": price,
            "product_id": product_id,
            "category_id": category_id,
            "quantity": quantity,
        })
        idx += 1

    if not items:
        return render_template(
            "add_paycheck.html",
            categories=categories,
            products_by_category=products_by_category,
            items=[{}],
            item_errors=[{"_": "Add at least one item."}],
            no_categories=False,
        ), 400

    category_ids = db.get_category_ids_set()
    product_ids = db.get_product_ids_set()
    product_to_category = db.get_product_to_category()
    item_errors = []
    all_valid = True
    for i, item in enumerate(items):
        ok, errs = validate_cost_item(
            {
                "date": item["date"],
                "price": item["price"],
                "product_id": item["product_id"],
                "category_id": item["category_id"],
                "quantity": item["quantity"],
            },
            category_ids=category_ids,
            product_ids=product_ids,
            product_to_category=product_to_category,
        )
        if not ok:
            all_valid = False
            item_errors.append(errs)
        else:
            item_errors.append({})

    if not all_valid:
        return (
            render_template(
                "add_paycheck.html",
                categories=categories,
                products_by_category=products_by_category,
                items=items,
                item_errors=item_errors,
                no_categories=False,
            ),
            400,
        )

    to_insert = []
    for item in items:
        to_insert.append({
            "date": item["date"].strip()[:10],
            "price": float(item["price"]),
            "product_id": int(item["product_id"]),
            "category_id": int(item["category_id"]),
            "quantity": int(item["quantity"]),
        })
    db.insert_costs(to_insert)
    return redirect(url_for("dashboard"))


@app.route("/categories")
def categories_list():
    categories = db.list_categories()
    return render_template("categories.html", categories=categories)


@app.route("/categories/add", methods=["GET", "POST"])
def category_add():
    if request.method == "GET":
        return render_template("category_edit.html", category=None)
    name = (request.form.get("name") or "").strip()
    if not name:
        return (
            render_template("category_edit.html", category=None, name=name, error="Name is required."),
            400,
        )
    try:
        db.create_category(name)
        return redirect(url_for("categories_list"))
    except Exception:
        return (
            render_template(
                "category_edit.html",
                category=None,
                name=name,
                error="Category with this name already exists.",
            ),
            400,
        )


@app.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
def category_edit(category_id):
    category = db.get_category(category_id)
    if not category:
        return "Category not found", 404
    if request.method == "GET":
        return render_template("category_edit.html", category=category)
    name = (request.form.get("name") or "").strip()
    if not name:
        return (
            render_template(
                "category_edit.html",
                category=category,
                name=name,
                error="Name is required.",
            ),
            400,
        )
    db.update_category(category_id, name)
    return redirect(url_for("categories_list"))


@app.route("/categories/<int:category_id>/delete", methods=["POST"])
def category_delete(category_id):
    db.delete_category(category_id)
    return redirect(url_for("categories_list"))


@app.route("/products")
def products_list():
    products = db.list_products()
    categories = db.list_categories()
    return render_template("products.html", products=products, categories=categories)


@app.route("/products/add", methods=["GET", "POST"])
def product_add():
    categories = db.list_categories()
    if not categories:
        return redirect(url_for("categories_list"))
    if request.method == "GET":
        return render_template("product_edit.html", product=None, categories=categories)
    name = (request.form.get("name") or "").strip()
    try:
        category_id = int(request.form.get("category_id") or 0)
    except ValueError:
        category_id = 0
    if not name:
        return (
            render_template(
                "product_edit.html",
                product=None,
                categories=categories,
                name=name,
                category_id=category_id,
                error="Name is required.",
            ),
            400,
        )
    if not category_id or not db.get_category(category_id):
        return (
            render_template(
                "product_edit.html",
                product=None,
                categories=categories,
                name=name,
                category_id=category_id,
                error="Please select a category.",
            ),
            400,
        )
    db.create_product(name, category_id)
    return redirect(url_for("products_list"))


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def product_edit(product_id):
    product = db.get_product(product_id)
    categories = db.list_categories()
    if not product:
        return "Product not found", 404
    if request.method == "GET":
        return render_template(
            "product_edit.html",
            product=product,
            categories=categories,
        )
    name = (request.form.get("name") or "").strip()
    try:
        category_id = int(request.form.get("category_id") or 0)
    except ValueError:
        category_id = 0
    if not name:
        return (
            render_template(
                "product_edit.html",
                product=product,
                categories=categories,
                name=name,
                category_id=category_id,
                error="Name is required.",
            ),
            400,
        )
    if not category_id or not db.get_category(category_id):
        return (
            render_template(
                "product_edit.html",
                product=product,
                categories=categories,
                name=name,
                category_id=category_id,
                error="Please select a category.",
            ),
            400,
        )
    db.update_product(product_id, name, category_id)
    return redirect(url_for("products_list"))


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def product_delete(product_id):
    db.delete_product(product_id)
    return redirect(url_for("products_list"))


@app.route("/product-trends")
def product_trends():
    count = db.count_costs()
    if count == 0:
        return render_template("product_trends.html", empty=True, trends=[])
    trends = db.product_trends()
    return render_template("product_trends.html", empty=False, trends=trends)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        currency = request.form.get("currency", "").strip()
        if currency in AVAILABLE_CURRENCIES:
            db.set_setting("currency", currency)
            return redirect(url_for("dashboard"))
    current = g.currency or DEFAULT_CURRENCY
    return render_template(
        "settings.html",
        currencies=AVAILABLE_CURRENCIES,
        current_currency=current,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
