---
name: product-search
description: Implement and test the DummyJSON keyword search and five cheapest results workflow in this Python Streamlit assignment.
---

# Product search workflow

- Read the root AGENTS.md before changing the application.
- Trim the keyword; show a prompt for blank input without calling the API.
- GET `https://dummyjson.com/products/search` with request parameters `q=<keyword>` and `limit=0`, and a finite timeout. Fetch all matching records before selecting the cheapest five; limiting the API response to five first can miss cheaper matches.
- Check the HTTP status and JSON structure. Validate each title and price; convert numeric prices to numbers, rejecting booleans, negative values, nonfinite values, and missing or invalid prices.
- Sort all valid records by numeric price ascending, then return the first five. Preserve the original title and image URL; use the thumbnail or first available image.
- Keep network and selection logic separate from the Streamlit UI so they can be tested without a browser.
- Show a clear no-matches message for an empty response. Distinguish API failures from empty results and show a retry message without displaying a traceback.
- Display the keyword, product names, formatted prices, and images when available. Label the page as sample DummyJSON product information, not live retailer offers.
- Test with an unsorted response of more than five products, including numeric strings; verify global numeric ordering and the result cap. Cover fewer than five results, blank input, empty results, timeouts, HTTP errors, malformed JSON, and invalid product records.
- Run the app with actual API searches such as laptop, phone, and watch. Capture a screenshot of the running Streamlit page with the keyword and ascending prices; never create a mock screenshot.
