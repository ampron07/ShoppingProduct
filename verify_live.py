"""Optional live API check; run separately from the offline unit tests."""

from product_search import search_products

for keyword in ("laptop", "phone", "watch", "zzzznonexistentproduct987654321"):
    products = search_products(keyword)
    prices = [product["price"] for product in products]
    assert len(products) <= 5
    assert prices == sorted(prices)
    if keyword.startswith("zzzz"):
        assert not products
    else:
        assert products
    print(keyword, [(product["title"], product["price"]) for product in products])
