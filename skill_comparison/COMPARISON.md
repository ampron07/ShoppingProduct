# Explicit skill invocation comparison

## Scope and method

This is a narrow, isolated ranking-function comparison, not a change to the
shopping application. Both attempts began as byte-identical copies of
`starter.py`. The initial SHA-256 for the starter and both copies was:

`2102545C29D3CCE27515C1E72F477F825E7D08DE834F56541CAA3500C21C18AB`

One test file, `test_comparison.py`, was written before either implementation
and was unchanged between runs. `conftest.py` selects the implementation using
`--attempt`. Both functions receive already eligible products; this comparison
tests scoring and selection, not HTTP retrieval or mandatory filtering.

Codex carried out both attempts sequentially in the same conversation. The
task instructions are preserved in `prompt_without.txt` and `prompt_with.txt`.
They specify the same behavior; the latter adds explicit `$product-ranking`
invocation (and each names its own output file). These were task instructions
followed within this session, not prompts submitted to separate fresh Codex
sessions. The second implementation started from its unchanged starter copy,
not from the first implementation.

## Context limitation

The first task prompt has no explicit skill invocation, but the conversation
already contained the skill, AGENTS.md requires it, and Codex read it for this
workflow. The second prompt explicitly invokes the skill, which was read again
before that attempt. Therefore this compares explicit versus nonexplicit
invocation in an informed session; it does not compare skill knowledge versus
no skill knowledge. The second attempt also had access to the first attempt's
context. Neither attempt was blind or independently generated in a fresh
context. No causal benefit from the skill or speed advantage can be inferred.

## Actual test evidence

| Attempt | Command | Recorded output |
| --- | --- | --- |
| Without explicit invocation | `.\.venv\Scripts\python.exe -m pytest skill_comparison\test_comparison.py --attempt without -q` | 24 passed in 0.15s |
| With explicit invocation | `.\.venv\Scripts\python.exe -m pytest skill_comparison\test_comparison.py --attempt with -q` | 24 passed in 0.05s |

Full terminal summaries are saved as `results_without.txt` and
`results_with.txt`. Both passed on their first test run; neither required a
post-test correction. Timing is incidental and is not a performance benchmark.

The shared tests cover hand-calculated totals (0.64 and 0.60), a winning product
outside the cheapest five, equal prices, a single result, missing/invalid
ratings, nonfinite/negative/boolean weights, invalid sums, tolerance, empty
input, zero/one weights, deterministic ties under permutations, preservation of
input data, and unrounded scoring.

## Observed similarity and difference

Both implementations calculate scores for the complete eligible set before
limiting to five, penalize unknown ratings without inventing a displayed
rating, and reject invalid weights even for an empty list. Both passed every
shared behavior test; there was no observed correctness improvement from
explicit invocation on this task.

The nonexplicit attempt builds `(sort_key, scored_record)` pairs inside one
loop and sorts those pairs. The explicit attempt separates rating validation
and tie-breaking into `_rating` and `_tie_key` helpers and sorts scored records
directly. This is an observable organization difference, not evidence that the
skill caused a better implementation. Both prompts already specified detailed
ranking rules, which also limits the comparison's ability to distinguish skill
effects. No artificial bug was added to make either attempt fail.

## Application unchanged

The following SHA-256 hashes matched before and after both attempts:

| File | SHA-256 |
| --- | --- |
| app.py | 40376112A8A145FB8EE6F87CBB593A727ED84DBC85439DCF640D79209672F02A |
| product_search.py | A83CB422F666A5833F3AA6FB393EEEE965BFD3B83C40DC3A979C15C23A5E92E5 |
| product_ranking.py | A40B43EEF90675E4DE7F44859DCDD544EA97C836C5DA6E3D183C5EB4F50D08BD |
| requirements.txt | BDA5C1B55E404E27DB57FB1188C79E1B4B9A992B9215CA5C8ABD800A2D9578F7 |
| requirements-dev.txt | 502AF188E657FC51B5E6ABC16C3E7754EBD0BDFB85D0908AD4AAED7A746F5724 |

Only comparison artifacts were added under `skill_comparison/`. The isolated
implementations do not import the application or replace its ranking function.
Student review is pending; this report does not claim personal verification
by the student or completion of the remaining assignment deliverables.
