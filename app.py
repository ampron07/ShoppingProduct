"""Streamlit interface for sample product filtering and recommendations."""

import streamlit as st

from product_ranking import filter_products, rank_products
from product_search import ProductSearchError, search_all_products

st.set_page_config(page_title="Product Search", page_icon="🛍️", layout="wide")
st.title("Shopping Product Search")
st.write("Search a keyword. Choose the lowest prices or weighted recommendations.")
st.info("Sample product information from the DummyJSON dataset — not live retailer offers. Prices shown in USD.")

# Keep the weight outside the batched form so slider reruns persist its value
# before Search submits the remaining conditions.
price_weight = st.slider("Price weight (weighted mode only)", 0.0, 1.0, 0.5, 0.05,
                         key="price_weight",
                         help="Rating weight is 1 minus this value. Lowest-price mode ignores these weights.")
rating_weight = 1 - price_weight
st.caption(f"Selected weights: price {price_weight:.0%}, rating {rating_weight:.0%}. Click Search to apply.")

with st.form("product_search"):
    keyword = st.text_input("Product keyword", placeholder="Try laptop, phone, or watch")
    mode = st.radio("Ranking mode", ["Lowest price (Stage 1)", "Weighted recommendations"], horizontal=True)
    first, second = st.columns(2)
    with first:
        budget = st.number_input("Maximum budget (USD)", min_value=0.0, value=None, step=10.0,
                                 help="Leave blank for no budget limit. Zero is an active limit.")
        brand = st.text_input("Brand", help="Optional exact name; capitalization does not matter.")
    with second:
        rating = st.number_input("Minimum rating", min_value=0.0, max_value=5.0, value=None, step=0.1,
                                 help="Leave blank for no rating requirement. Unknown ratings fail an active requirement.")
        category = st.text_input("Category", help="Optional exact dataset category, for example smartphones.")
    st.caption("Blank filters are unused. Brand/category use exact matches ignoring case and surrounding spaces. "
               "Size and dimension filters are unavailable because units and size specifications are unverified.")
    submitted = st.form_submit_button("Search", type="primary")

if submitted:
    query = keyword.strip()
    if not query:
        st.warning("Enter a product keyword to search.")
    else:
        constraints = dict(max_budget=budget, min_rating=rating, brand=brand, category=category)
        weighted = mode == "Weighted recommendations"
        st.write(f"Conditions: budget {'any' if budget is None else f'<= ${budget:,.2f}'}; "
                 f"rating {'any' if rating is None else f'>= {rating:g}/5'}; "
                 f"brand {brand.strip() or 'any'}; category {category.strip() or 'any'}.")
        try:
            with st.spinner("Searching the sample dataset…"):
                matches = search_all_products(query)
                eligible = filter_products(matches, **constraints)
                if weighted:
                    products = rank_products(matches, price_weight=price_weight,
                                             rating_weight=rating_weight, **constraints)
                else:
                    products = sorted(eligible, key=lambda product: product["price"])[:5]
            if not products:
                st.info(f'No products match "{query}" with these conditions.')
                suggestions = ["Try another keyword"]
                if budget is not None:
                    suggestions.append("increase or clear the maximum budget")
                if rating is not None:
                    suggestions.append("lower or clear the minimum rating")
                if brand.strip() or category.strip():
                    suggestions.append("check the exact brand/category spelling or clear those fields")
                st.write("; ".join(suggestions) + ". Then click Search again. No conditions were relaxed.")
            else:
                st.subheader(f'Results for "{query}"')
                st.caption(f"Showing {len(products)} of {len(eligible)} eligible matches • "
                           + ("Weighted score: high to low" if weighted else "Price: low to high"))
                if weighted:
                    st.caption(f"Weights: price {price_weight:.0%}, rating {rating_weight:.0%}. "
                               "Price score = (maximum eligible price - price) / eligible price range; "
                               "equal prices score 1. Rating score = rating / 5; unknown ratings contribute 0. "
                               "Scores depend on the eligible set. Ties: price, rating, title, then ID.")
                for rank, product in enumerate(products, start=1):
                    with st.container(border=True):
                        image_column, name_column, price_column = st.columns([1, 5, 2], vertical_alignment="center")
                        with image_column:
                            if product["image"]:
                                st.image(product["image"], width=80)
                            else:
                                st.caption("No image available")
                        with name_column:
                            st.write(f"{rank}. {product['title']}")
                            displayed_rating = "Unknown" if product["rating"] is None else f"{product['rating']:g}/5"
                            st.caption(f"Brand: {product['brand'] or 'Unknown'} • "
                                       f"Category: {product['category'] or 'Unknown'} • Rating: {displayed_rating}")
                            if weighted:
                                st.write(f"Weighted score: {product['score']:.4f}")
                                st.caption(f"Meets all selected conditions. "
                                           f"Price component {product['price_score']:.4f} × {price_weight:.2f} + "
                                           f"rating component {product['rating_score']:.4f} × {rating_weight:.2f}.")
                            else:
                                st.caption("Meets all selected conditions; ordered by lowest price.")
                        with price_column:
                            st.metric("Sample price (USD)", f"${product['price']:,.2f}")
        except (ProductSearchError, ValueError) as exc:
            st.error(str(exc))

st.caption("Source: dummyjson.com • Educational product search exercise")
