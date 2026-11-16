import unittest
from pathlib import Path
from unittest.mock import patch

import requests
from streamlit.testing.v1 import AppTest

from product_search import ProductSearchError, cheapest_products, search_products


class ProductSearchTests(unittest.TestCase):
    def test_numeric_sort_before_limit(self):
        records = [{"title": str(price), "price": price} for price in [100, "20", 3, 9, 1, 2, 4]]
        self.assertEqual([p["price"] for p in cheapest_products(records)], [1, 2, 3, 4, 9])

    def test_fewer_results_and_image_fallback(self):
        result = cheapest_products([{"title": "Watch", "price": 12, "images": ["https://example.com/watch.png"]}])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["image"], "https://example.com/watch.png")
        self.assertEqual(cheapest_products([]), [])

    def test_invalid_records(self):
        for price in [None, True, "bad", -1, "nan", "inf"]:
            with self.subTest(price=price), self.assertRaises(ProductSearchError):
                cheapest_products([{"title": "Watch", "price": price}])

    @patch("product_search.requests.get")
    def test_request_and_blank_input(self, get):
        self.assertEqual(search_products("   "), [])
        get.assert_not_called()
        get.return_value.json.return_value = {"products": []}
        self.assertEqual(search_products(" phone "), [])
        self.assertEqual(get.call_args.kwargs["params"], {"q": "phone", "limit": 0})
        self.assertEqual(get.call_args.kwargs["timeout"], 15)

    @patch("product_search.requests.get")
    def test_api_failures(self, get):
        for error in [requests.Timeout(), requests.HTTPError(), ValueError("bad JSON")]:
            get.side_effect = error
            with self.subTest(error=error), self.assertRaises(ProductSearchError):
                search_products("phone")
        get.side_effect = None
        get.return_value.json.side_effect = ValueError("bad JSON")
        with self.assertRaises(ProductSearchError):
            search_products("phone")
        get.return_value.json.side_effect = None
        get.return_value.raise_for_status.side_effect = requests.HTTPError()
        with self.assertRaises(ProductSearchError):
            search_products("phone")
        get.return_value.raise_for_status.side_effect = None
        for data in [{}, {"products": None}, []]:
            get.return_value.json.return_value = data
            with self.assertRaises(ProductSearchError):
                search_products("phone")

    @patch("product_search.requests.get")
    def test_streamlit_search(self, get):
        get.return_value.json.return_value = {"products": [
            {"title": "Expensive phone", "price": 99},
            {"title": "Budget phone", "price": 9},
        ]}
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
        app.text_input[0].set_value("phone")
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual([metric.value for metric in app.metric], ["$9.00", "$99.00"])
        app.text_input[0].set_value(" ")
        app.button[0].click().run()
        self.assertTrue(app.warning)
        self.assertEqual(len(app.metric), 0)

    @patch("product_search.requests.get")
    def test_streamlit_empty_and_failure(self, get):
        get.return_value.json.return_value = {"products": []}
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
        app.text_input[0].set_value("nonsensekeyword")
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("No products match" in message.value for message in app.info))
        get.side_effect = requests.Timeout()
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)


if __name__ == "__main__":
    unittest.main()
