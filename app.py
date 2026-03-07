from __future__ import annotations

import os
from datetime import date, datetime, time

import pandas as pd
import plotly.express as px
import streamlit as st

from src import db
from src.fx import convert, fetch_live_rate


APP_TITLE = "Paycheck Analyzer"
DEFAULT_CURRENCY = "USD"


def _db_path() -> str:
    return os.path.join(os.path.dirname(__file__), "data", "paycheck.db")


@st.cache_resource
def _get_con() -> db.sqlite3.Connection:  # type: ignore[attr-defined]
    con = db.connect(db.DBConfig(path=_db_path()))
    db.init_db(con)
    return con


def _as_df(rows: list[db.sqlite3.Row]) -> pd.DataFrame:  # type: ignore[attr-defined]
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def _week_start(d: pd.Timestamp) -> pd.Timestamp:
    return (d - pd.to_timedelta(d.dayofweek, unit="D")).normalize()


def _pick_currency(codes: list[str], default: str) -> str:
    codes_u = sorted({c.strip().upper() for c in codes if c and str(c).strip()})
    if default not in codes_u:
        codes_u = [default] + codes_u
    return st.selectbox("Currency (display)", options=codes_u, index=codes_u.index(default))


def _infer_known_currencies(purchases_df: pd.DataFrame, prices_df: pd.DataFrame) -> list[str]:
    codes: list[str] = [DEFAULT_CURRENCY, "EUR", "GBP"]
    for df in (purchases_df, prices_df):
        if not df.empty and "currency" in df.columns:
            codes.extend([str(x) for x in df["currency"].dropna().unique().tolist()])
    return sorted({c.strip().upper() for c in codes if c})


def _get_rate(con, as_of_: date, from_cur: str, to_cur: str) -> tuple[float, str]:
    from_cur = from_cur.strip().upper()
    to_cur = to_cur.strip().upper()
    if from_cur == to_cur:
        return 1.0, "identity"

    manual = db.get_fx_rate(con, as_of_, from_cur, to_cur)
    if manual is not None:
        return float(manual), "manual(db)"

    live = fetch_live_rate(from_cur, to_cur)
    if live is not None:
        return float(live.rate), live.source

    return 1.0, "fallback:1.0"


def _apply_currency(con, df: pd.DataFrame, display_currency: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["purchased_at"] = pd.to_datetime(out["purchased_at"], errors="coerce")
    out["purchased_date"] = out["purchased_at"].dt.date
    out["currency"] = out["currency"].astype(str).str.upper()
    display_currency = display_currency.strip().upper()

    rates = []
    sources = []
    for _, row in out.iterrows():
        as_of_ = row["purchased_date"]
        fc = row["currency"]
        r, src = _get_rate(con, as_of_, fc, display_currency)
        rates.append(r)
        sources.append(src)
    out["fx_rate"] = rates
    out["fx_source"] = sources
    out["total_display"] = out["total"] * out["fx_rate"]
    out["unit_price_display"] = out["unit_price"] * out["fx_rate"]
    out["display_currency"] = display_currency
    return out


def page_data_entry(con) -> None:
    st.subheader("Manual data entry")

    with st.expander("Categories", expanded=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            cat_name = st.text_input("New category name", placeholder="e.g. Groceries")
        with c2:
            if st.button("Add category", use_container_width=True):
                try:
                    db.upsert_category(con, cat_name)
                    st.success("Saved.")
                except Exception as e:
                    st.error(str(e))

        cats = _as_df(db.list_categories(con))
        if not cats.empty:
            st.dataframe(cats, hide_index=True, use_container_width=True)
        else:
            st.info("No categories yet.")

    with st.expander("Products", expanded=True):
        cats = _as_df(db.list_categories(con))
        cat_options = [("(none)", None)]
        if not cats.empty:
            cat_options += [(row["name"], int(row["id"])) for _, row in cats.iterrows()]

        p1, p2, p3 = st.columns([2, 2, 1])
        with p1:
            prod_name = st.text_input("Product name", placeholder="e.g. Milk 1L")
        with p2:
            cat_label = st.selectbox("Category", options=[x[0] for x in cat_options])
            cat_id = dict(cat_options).get(cat_label)
        with p3:
            unit = st.text_input("Unit (optional)", placeholder="e.g. L, kg")

        if st.button("Add / update product", use_container_width=True):
            try:
                db.upsert_product(con, prod_name, cat_id, unit)
                st.success("Saved.")
            except Exception as e:
                st.error(str(e))

        prods = _as_df(db.list_products(con))
        if not prods.empty:
            st.dataframe(prods[["id", "name", "category_name", "unit"]], hide_index=True, use_container_width=True)
        else:
            st.info("No products yet.")

    with st.expander("Product prices (history)", expanded=False):
        prods = _as_df(db.list_products(con))
        if prods.empty:
            st.warning("Add at least one product first.")
        else:
            name_to_id = {r["name"]: int(r["id"]) for _, r in prods.iterrows()}
            pr1, pr2, pr3, pr4 = st.columns([2, 1, 1, 2])
            with pr1:
                prod_sel = st.selectbox("Product", options=sorted(name_to_id.keys()))
                product_id = name_to_id[prod_sel]
            with pr2:
                price = st.number_input("Price", min_value=0.0, value=0.0, step=0.01)
            with pr3:
                currency = st.text_input("Currency", value=DEFAULT_CURRENCY, max_chars=5)
            with pr4:
                eff = st.date_input("Effective date", value=date.today())
            note = st.text_input("Note (optional)", placeholder="e.g. store / brand / promo")

            if st.button("Record price", use_container_width=True):
                try:
                    db.record_price(con, product_id, price, currency, eff, note=note)
                    st.success("Recorded.")
                except Exception as e:
                    st.error(str(e))

            prices = _as_df(db.list_prices(con, product_id=product_id))
            if not prices.empty:
                st.dataframe(
                    prices[["effective_date", "currency", "price", "note"]],
                    hide_index=True,
                    use_container_width=True,
                )

    with st.expander("Purchases (spend entries)", expanded=True):
        prods = _as_df(db.list_products(con))
        if prods.empty:
            st.warning("Add at least one product first.")
            return

        name_to_row = {r["name"]: r for _, r in prods.iterrows()}
        pc1, pc2, pc3, pc4 = st.columns([2, 1, 1, 1])
        with pc1:
            prod_name = st.selectbox("Product", options=sorted(name_to_row.keys()))
            prod_row = name_to_row[prod_name]
            product_id = int(prod_row["id"])
            category_id = int(prod_row["category_id"]) if pd.notna(prod_row["category_id"]) else None
        with pc2:
            qty = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.5)
        with pc3:
            unit_price = st.number_input("Unit price", min_value=0.0, value=0.0, step=0.01)
        with pc4:
            currency = st.text_input("Currency", value=DEFAULT_CURRENCY, max_chars=5, key="purchase_currency")

        dt1, dt2 = st.columns([1, 1])
        with dt1:
            d = st.date_input("Date", value=date.today(), key="purchase_date")
        with dt2:
            t = st.time_input("Time", value=datetime.now().time().replace(second=0, microsecond=0), key="purchase_time")
        purchased_at = datetime.combine(d, t if isinstance(t, time) else datetime.now().time())
        note = st.text_input("Note (optional)", placeholder="e.g. store / receipt")

        st.caption(f"Total: {qty * unit_price:.2f} {currency.strip().upper()}")
        if st.button("Add purchase", use_container_width=True):
            try:
                db.add_purchase(con, purchased_at, product_id, category_id, qty, unit_price, currency, note=note)
                st.success("Added.")
            except Exception as e:
                st.error(str(e))

        purchases = _as_df(db.list_purchases(con))
        if not purchases.empty:
            show = purchases[["purchased_at", "product_name", "category_name", "quantity", "unit_price", "currency", "total", "note"]]
            st.dataframe(show, hide_index=True, use_container_width=True)

    with st.expander("FX rates (manual override)", expanded=False):
        st.write("If you add a manual FX rate for a date, it will be used before live FX.")
        fx1, fx2, fx3, fx4 = st.columns([1, 1, 1, 1])
        with fx1:
            as_of_ = st.date_input("As-of date", value=date.today(), key="fx_asof")
        with fx2:
            from_cur = st.text_input("From", value="USD", max_chars=5, key="fx_from")
        with fx3:
            to_cur = st.text_input("To", value="EUR", max_chars=5, key="fx_to")
        with fx4:
            rate = st.number_input("Rate", min_value=0.0, value=1.0, step=0.0001, key="fx_rate")
        if st.button("Save FX rate", use_container_width=True):
            try:
                db.upsert_fx_rate(con, as_of_, from_cur, to_cur, rate, source="manual")
                st.success("Saved.")
            except Exception as e:
                st.error(str(e))


def page_dashboards(con) -> None:
    st.subheader("Dashboards")
    purchases = _as_df(db.list_purchases(con))
    prices = _as_df(db.list_prices(con))

    if purchases.empty:
        st.info("Add some purchases to see dashboards.")
        return

    display_currency = _pick_currency(_infer_known_currencies(purchases, prices), DEFAULT_CURRENCY)
    p = _apply_currency(con, purchases, display_currency)
    p["purchased_at"] = pd.to_datetime(p["purchased_at"], errors="coerce")
    p["month"] = p["purchased_at"].dt.to_period("M").astype(str)
    p["week_start"] = p["purchased_at"].apply(lambda x: _week_start(pd.Timestamp(x)) if pd.notna(x) else pd.NaT)
    p["week_start"] = pd.to_datetime(p["week_start"], errors="coerce")
    p["week"] = p["week_start"].dt.date.astype(str)
    p["category_name"] = p["category_name"].fillna("(uncategorized)")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total spend", f"{p['total_display'].sum():.2f} {display_currency}")
    with m2:
        st.metric("Avg per purchase", f"{p['total_display'].mean():.2f} {display_currency}")
    with m3:
        st.metric("Purchases", f"{len(p):,}")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        by_month = p.groupby("month", as_index=False)["total_display"].sum().sort_values("month")
        fig = px.bar(by_month, x="month", y="total_display", title="Spend by month")
        fig.update_yaxes(title=f"Total ({display_currency})")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        by_week = p.groupby("week", as_index=False)["total_display"].sum().sort_values("week")
        fig = px.line(by_week, x="week", y="total_display", markers=True, title="Spend by week")
        fig.update_yaxes(title=f"Total ({display_currency})")
        st.plotly_chart(fig, use_container_width=True)

    by_cat = p.groupby("category_name", as_index=False)["total_display"].sum().sort_values("total_display", ascending=False)
    fig = px.bar(by_cat, x="category_name", y="total_display", title="Spend by category")
    fig.update_xaxes(title="Category")
    fig.update_yaxes(title=f"Total ({display_currency})")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("FX details (per row)", expanded=False):
        st.dataframe(
            p[["purchased_at", "product_name", "currency", "total", "fx_rate", "fx_source", "total_display"]],
            hide_index=True,
            use_container_width=True,
        )


def page_price_changes(con) -> None:
    st.subheader("Product price changes")
    prices = _as_df(db.list_prices(con))
    if prices.empty:
        st.info("Record product prices to see changes over time.")
        return

    prices["effective_date"] = pd.to_datetime(prices["effective_date"], errors="coerce")
    prices["currency"] = prices["currency"].astype(str).str.upper()

    cur = _pick_currency(sorted(prices["currency"].dropna().unique().tolist()), DEFAULT_CURRENCY)
    view = prices[prices["currency"] == cur].copy()
    if view.empty:
        st.info(f"No price history in {cur}.")
        return

    prods = sorted(view["product_name"].dropna().unique().tolist())
    selected = st.multiselect("Products", options=prods, default=prods[: min(5, len(prods))])
    if selected:
        view = view[view["product_name"].isin(selected)]

    fig = px.line(
        view.sort_values(["product_name", "effective_date"]),
        x="effective_date",
        y="price",
        color="product_name",
        markers=True,
        title=f"Price history ({cur})",
    )
    st.plotly_chart(fig, use_container_width=True)

    latest = (
        view.sort_values(["product_name", "effective_date"])
        .groupby("product_name", as_index=False)
        .tail(1)
        .sort_values("price", ascending=False)
    )
    st.divider()
    st.write("Latest recorded price per product")
    st.dataframe(latest[["product_name", "effective_date", "price", "note"]], hide_index=True, use_container_width=True)

    changes = view.sort_values(["product_name", "effective_date"]).copy()
    changes["prev_price"] = changes.groupby("product_name")["price"].shift(1)
    changes["delta"] = changes["price"] - changes["prev_price"]
    changes["delta_pct"] = (changes["delta"] / changes["prev_price"]) * 100.0
    changes = changes.dropna(subset=["prev_price"])
    if not changes.empty:
        st.write("Price changes (event-to-event)")
        st.dataframe(
            changes[["product_name", "effective_date", "prev_price", "price", "delta", "delta_pct", "note"]],
            hide_index=True,
            use_container_width=True,
        )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    con = _get_con()

    page = st.sidebar.radio(
        "Navigate",
        options=["Data entry", "Dashboards", "Price changes"],
    )

    if page == "Data entry":
        page_data_entry(con)
    elif page == "Dashboards":
        page_dashboards(con)
    else:
        page_price_changes(con)


if __name__ == "__main__":
    main()

