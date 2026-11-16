# Shopping Product Search

Python + Streamlit assignment using actual DummyJSON search responses.

## Run in VS Code

Open this folder in VS Code. Select `.venv\Scripts\python.exe` through **Python: Select Interpreter**. In the PowerShell terminal run:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501, enter `phone`, and click **Search**. Try `laptop`, `watch`, and a nonsense keyword as well. Anaconda users can instead select their environment and run `python -m pip install -r requirements.txt` and `python -m streamlit run app.py` there.

## Explicit custom skill prompt

Use this prompt in Codex in VS Code to explicitly invoke the assignment's skill:

> Use $product-search from .agents/skills/product-search/SKILL.md and follow AGENTS.md to implement and verify this Streamlit application. Query all matching DummyJSON products, sort numeric prices ascending, show the five cheapest results with names and images, and handle blank input, no matches, and API errors.

The custom skill was read and applied during implementation in this session. The prompt above can also be used to review or refine the app in VS Code.

## Checks

Stage 2 Steps 2 through 4 add normalization, mandatory filtering, weighted
ranking, and Streamlit controls with integration tests. Install test
dependencies and run all tests with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

`search_all_products(keyword)` returns all normalized matches in API order.
`filter_products(products, max_budget=..., brand=..., category=..., min_rating=...)`
applies all active constraints together without sorting or truncating. Budget
and rating comparisons are inclusive. Text matches are exact after trimming
and case folding; blank text and `None` disable a filter, but numeric zero is
active. Unknown required attributes fail an active constraint. Missing or
invalid optional attributes remain `None`; invalid required titles/prices
raise a readable error. Filtering does not modify the input products.

Dimension axes are preserved as reported numbers or unknown values, but units
are unverified. Physical-dimension and clothing-size filters are unsupported
in this step. No units or specifications are invented. `search_products`
retains its original Stage 1 result shape and five-cheapest behavior.

### Weighted ranking (Step 3 backend)

Call `rank_products(search_all_products(keyword), price_weight=0.4,
rating_weight=0.6, max_budget=100, min_rating=4)` from Python. It applies all
mandatory filters first, scores every eligible match, and returns at most five.
It does not fetch data itself; the Streamlit interface calls it in weighted mode.

- Price score: `(maximum eligible price - price) / (maximum - minimum)`.
  When all eligible prices are equal (including one result), price score is 1.
- Rating score: `rating / 5`. An unknown rating contributes zero to scoring,
  remains unknown in the returned data, and fails any active minimum-rating
  constraint.
- Final `score`: `price_weight * price_score + rating_weight * rating_score`.
  Results also include `price_score` and `rating_score` for later explanations.
- Weights must be finite, nonnegative, at most 1, and sum to 1 within absolute
  tolerance `1e-9`; invalid weights raise `ValueError`, even for empty input.
- Sort by score descending, price ascending, valid rating descending (unknown
  last), trimmed case-folded title ascending, then numeric ID ascending (unknown
  last). Indistinguishable records retain input order. Do not round before sorting.

Normalization uses the eligible set, so scores can change when filters change.
The input products are not modified. Never pass the already truncated output
of Stage 1 `search_products` to weighted ranking.

### Streamlit controls (Step 4)

Run the app using the command above. The default mode is **Lowest price
(Stage 1)** with unused filters, preserving the original five-cheapest results.
Optionally enter a maximum budget, minimum rating, exact brand, and exact
dataset category. Leave numeric fields blank to disable them; zero activates
a zero threshold. Brand/category matching ignores case and surrounding spaces.

Select **Weighted recommendations** to use the price-weight slider; rating
weight is its complement. Click **Search** after changing any conditions.
Results show brand, category, rating, and image availability in both modes.
Weighted results also explain the total score, component scores, and weights.
Unknown attributes are labeled rather than invented.

No-match messages suggest changes to active conditions, but the user must make
those changes and search again. API failures are reported separately. Size and
physical-dimension controls remain unavailable because their units and meaning
are unverified. Streamlit AppTest integration tests mock the API; no real-site
screenshot or live verification was performed as part of Step 4.

The original unittest suite can also be run separately:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Network errors are displayed to the user; no fabricated or offline products replace failed requests. Search logic requests `limit=0` so the five-item selection is made after sorting every match.

## Blackboard submission

1. Root `AGENTS.md`.
2. `.agents/skills/product-search/SKILL.md` (upload the file named SKILL.md).
3. A screenshot of the running Streamlit website with the entered keyword, actual results, and ascending prices visible. Search `phone` and use Windows Snipping Tool (`Win+Shift+S`) if a screenshot has not already been generated. Save as `website_screenshot.png`.

Review the code and run the searches yourself so you can explain how the API request, numeric sorting, and five-result limit work.
