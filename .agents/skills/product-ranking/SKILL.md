---
name: product-ranking
description: Implement and verify deterministic mandatory filtering and weighted price/rating recommendations for the Stage 2 DummyJSON Streamlit assignment while preserving Stage 1 lowest-price behavior.
---

# Product ranking

Read root AGENTS.md and existing code/tests. Complete only the requested development step, report checks, and stop for review. This skill guides Codex during development; Python functions perform runtime filtering and ranking.

## Rules and rationale

- **Filter the full matching set before scoring or truncating.** Fetch all records with `limit=0`; never rank Stage 1's five-item output. Otherwise an eligible high-rating product outside the five cheapest matches can never win.
- **Unknown required attributes fail active constraints.** Preserve missing brand/category/rating/dimensions as unknown. Otherwise an unverified product could be presented as satisfying a mandatory condition.
- Retain Stage 1 lowest-price mode and public behavior. Inactive filters are no-ops. Do not silently switch modes or relax conditions.
- Preserve readable validation errors for invalid required titles/prices. Reject boolean, negative, and nonfinite prices. Missing/invalid optional attributes remain unknown and are labeled accordingly.
- Apply mandatory conditions together: price <= maximum budget, rating >= minimum rating, and trimmed case-insensitive exact brand/category matches. Validate finite constraints, nonnegative budgets, and rating bounds [0, 5]. Unknown constrained attributes fail even when the threshold is zero.
- Expose dimensions only after verifying supported axes and units in actual dataset documentation/data. A dimensions object alone does not establish units or clothing size. Omit unsupported controls and explain the limitation.

## Implementation steps

1. Add a full-match retrieval path without changing Stage 1's five-cheapest wrapper. Normalize supported attributes while preserving unknowns. Keep API failures distinct from empty results.
2. Implement pure mandatory filtering over all normalized matches, separate from HTTP and Streamlit rendering.
3. Implement weighted mode over every eligible product using this explicit contract unless the user requests a different documented one:
   - Price score: `(max_price - price) / (max_price - min_price)` over eligible prices. If all prices are equal, assign every price score 1.
   - Rating score: `rating / 5` for valid ratings in [0, 5]. Unknown/invalid ratings contribute 0 as a documented scoring penalty, not a fabricated rating; display the rating as unknown. An active rating constraint excludes these records first.
   - Total: `price_weight * price_score + rating_weight * rating_score`.
   - Accept finite nonnegative weights summing to 1 within absolute tolerance `1e-9`. Reject invalid weights rather than silently normalizing. A UI can accept one weight and derive the other as `1 - weight`.
   - Sort by total score descending, price ascending, valid rating descending (unknown last), normalized title ascending, and numeric dataset ID ascending (unknown last). Preserve input order only for records indistinguishable on those keys. Round only for display.
   - Take at most five after sorting. Return an empty list without calculating min/max when none qualify.
4. Integrate selectable lowest-price and weighted modes. Display conditions, names, prices, brands, ratings, images, score components/weights, and a brief explanation. Explain that normalization depends on the eligible set. Suggest user-controlled changes on no matches; never apply them automatically.
5. Document formulas and unknown-value handling. Record actual prompts, changes, review findings, and test results when the development-log step is requested.

## Verification instructions

- Use pytest with mocked API responses and retain Stage 1 regressions. Mock fixtures are test data only, never real screenshot results.
- Test combined conditions, exact budget/rating boundaries, blank searches, missing constrained fields, unsupported dimensions, invalid numbers, empty results, fewer than five matches, and API errors.
- Hand-check scores: eligible prices 10 and 30, ratings 2 and 5, and weights 0.4 price/0.6 rating produce totals 0.64 and 0.60. Cover equal prices, unknown ratings, zero/one weights, invalid sums, deterministic ties, and input permutations of distinct IDs.
- Include more than five eligible products with a high-rating winner outside the five cheapest. Confirm ineligible products cannot influence normalization or recommendations.
- For the comparison, preserve an identical isolated function stub and test set. Attempt the same narrow implementation/testing task once without explicit invocation and once with `$product-ranking`, leaving main application code unchanged during comparison. Record full prompts, actual skill context, test output, and one observed difference or similarity. Automatic skill discovery may occur without explicit invocation; do not call that attempt skill-free unless verified.
- During final verification, run pytest and manually check real multi-condition results, exact boundaries, and no matches. Capture the running Streamlit page with actual DummyJSON data. Record an actual bug/edge case, its cause, correction, and regression test. Do not claim checks or human review that have not happened.
