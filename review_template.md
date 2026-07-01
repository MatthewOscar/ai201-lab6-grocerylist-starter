# Code Review Notes

Fill this in as you work through the milestones. Each section mirrors the structure of a real GitHub pull request review.

---

## PR #1 - Bulk Purchase (`pr1_bulk_purchase.py`)

### Summary
*What does this PR do? (1–2 sentences in your own words)*

> Adds a bulk endpoint that marks every item in a list as purchased in one request. The simple case works, but the implementation updates too many rows and can corrupt existing purchase attribution.

### Issues

For each issue you find, note: where it is (file + function), what's wrong, and why it matters in production.

**Issue 1**
- Location: `prs/pr1_bulk_purchase.py`, `purchase_all_items()`
- What's wrong: The query uses `Item.query.filter_by(list_id=list_id).all()`, so it selects every item in the list instead of only unpurchased items.
- Why it matters: Already-purchased items get rewritten. In the seeded Weekly Shop list, `Olive Oil` started with `purchased_by` set to Leo, but after Maya called `purchase-all`, it was overwritten with Maya's user ID.
- Suggested fix: First verify the list exists, then query only `list_id=list_id, is_purchased=False`. Only update those rows so existing `purchased_by` and `purchased_at` values are preserved.

**Issue 2**
- Location: `prs/pr1_bulk_purchase.py`, `purchase_all_items()`
- What's wrong: The function returns `len(items)`, but `items` contains all list items, not the items newly purchased by the request.
- Why it matters: The API reported `{"purchased": 8}` on Weekly Shop even though only 5 items were unpurchased. A caller tracking progress would receive an inflated count.
- Suggested fix: Return the length of the same unpurchased-item collection that the service updates. That makes the response count match the rows newly changed by this request.

**Issue 3** *(if found)*
- Location: `prs/pr1_bulk_purchase.py`, `purchase_all()`
- What's wrong: The route reads `user_id = data.get("user_id")` but never validates that the required field is present before calling the service.
- Why it matters: A request with `{}` returned `200` and rewrote every item's `purchased_by` to `null`, destroying attribution data.
- Suggested fix: Match the existing `mark_purchased` route pattern: return `400` with `{"error": "Missing required field: user_id"}` before calling the service. Keep that validation in the route so no database changes can happen for a malformed request.

### Questions for the Author
*Things you're uncertain about: design choices that could be intentional or bugs depending on intent.*

> Should this endpoint also validate that the list exists and return a clean 404 when it does not? The current PR code would return `{"purchased": 0}` for a bad list ID, which may not match the rest of the API.

### Impact Analysis

> If this endpoint runs without a `user_id`, every item it touches can lose the record of who purchased it. That affects shoppers who need to know who picked up an item, support staff investigating list history, and any audit or analytics feature built on `purchased_by`. A downstream report could undercount real user activity or show purchased items with no accountable shopper. Since the bad write is committed to the database, the original attribution is not available through the normal app after the request completes.

### Verdict
- [ ] Approve: ship it
- [x] Request Changes: needs fixes before merging
- [ ] Comment: needs discussion before a verdict

**Rationale** *(1–2 sentences)*:

> Request changes because the endpoint can overwrite existing `purchased_by` / `purchased_at` values and can write `null` attribution when `user_id` is omitted. Those are data integrity bugs, and the endpoint should not merge until they are fixed.

---

## PR #2 - List Stats (`pr2_list_stats.py`)

### Summary
*What does this PR do? (1–2 sentences in your own words)*

> Adds a stats endpoint with total, purchased, remaining, and category counts for a list. The total fields are plausible, but the category breakdown does not match the active-shopping use case and the endpoint treats missing lists as empty lists.

### Issues

**Issue 1**
- Location: `prs/pr2_list_stats.py`, `get_list_stats()`
- What's wrong: `by_category` loops over `items`, and `items` contains every item in the list. The PR description asks for a breakdown of what is remaining by category.
- Why it matters: Weekly Shop returned `remaining: 5`, but `by_category` summed to 8 because it included purchased items. A shopper could be told to visit sections for items already in the cart.
- Suggested fix: Build `by_category` from the same remaining-item subset used for the `remaining` count. The sum of `by_category` should equal `remaining`.

**Issue 2**
- Location: `prs/pr2_list_stats.py`, `get_list_stats()` / `list_stats()`
- What's wrong: The service never checks whether the grocery list exists, so `/lists/bad-list-id/stats` returns `200` with zero counts.
- Why it matters: Callers cannot distinguish an empty existing list from a missing list. This also disagrees with the existing `/lists/<list_id>/items` endpoint, which returns `404` for the same bad ID.
- Suggested fix: Look up the `GroceryList` before computing stats. If it does not exist, raise a service-layer error and have the route return the same `404` JSON shape used by the existing list item routes.

**Issue 3** *(if found)*
- Location: N/A
- What's wrong: No third blocking issue found.
- Why it matters: N/A
- Suggested fix: N/A

### Questions for the Author
*A good code review often surfaces design questions as well as bugs. What would you want to clarify before approving?*

> Should `by_category` omit categories that only have purchased items, or include them with a zero count? The frontend request sounds like omitting them is fine, but the API contract should be explicit.

### Verdict
- [ ] Approve: ship it
- [x] Request Changes: needs fixes before merging
- [ ] Comment: needs discussion before a verdict

**Rationale** *(1–2 sentences)*:

> Request changes because the response does not provide the remaining-by-category data the frontend requested, and the missing-list behavior is inconsistent with the existing API.

---

## Reflection

*Answer after completing both reviews.*

**1.** Which issue was hardest to spot, and why?

> PR #2's `by_category` bug was hardest because the code is internally consistent and returns plausible JSON. The mismatch only appears when comparing the frontend's "what's remaining" request against the exact set of items being counted.

**2.** Which issues do you think an LLM reviewer (like Claude reviewing its own code) would most likely miss? Why?

> It would be most likely to miss the semantic mismatch in PR #2 and the already-purchased overwrite in PR #1. Both require testing or reasoning about pre-existing state, beyond checking whether the happy path compiles and returns data.

**3.** One thing you'd add to a code review checklist for AI-generated backend code:

> For every query, ask whether it selects exactly the records the PR description says should be read or changed, then test at least one pre-existing-state case, one missing-input case, and one missing-resource case.
