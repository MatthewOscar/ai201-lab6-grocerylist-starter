# Code Review Notes

Fill this in as you work through the milestones. Each section mirrors the structure of a real GitHub pull request review.

---

## PR #1 — Bulk Purchase (`pr1_bulk_purchase.py`)

### Summary
*What does this PR do? (1–2 sentences in your own words)*

> Adds a bulk endpoint that marks every item in a list as purchased in one request. The happy path runs, but the implementation updates too many rows and can corrupt existing purchase attribution.

### Issues

For each issue you find, note: where it is (file + function), what's wrong, and why it matters in production.

**Issue 1**
- Location: `prs/pr1_bulk_purchase.py`, `purchase_all_items()`
- What's wrong: The query uses `Item.query.filter_by(list_id=list_id).all()`, so it selects every item in the list instead of only unpurchased items.
- Why it matters: Already-purchased items get rewritten. In the seeded Weekly Shop list, `Olive Oil` started with `purchased_by` set to Leo, but after Maya called `purchase-all`, it was overwritten with Maya's user ID.
- Suggested fix: Filter the query to `list_id=list_id, is_purchased=False` so the operation only modifies items that this request actually purchases.

**Issue 2**
- Location: `prs/pr1_bulk_purchase.py`, `purchase_all_items()`
- What's wrong: The function returns `len(items)`, but `items` contains all list items, not the items newly purchased by the request.
- Why it matters: The API reported `{"purchased": 8}` on Weekly Shop even though only 5 items were unpurchased. A caller tracking progress would receive an inflated count.
- Suggested fix: Return the length of the unpurchased-item query result after narrowing the query, or otherwise track the count of items changed by this request.

**Issue 3** *(if found)*
- Location: `prs/pr1_bulk_purchase.py`, `purchase_all()`
- What's wrong: The route reads `user_id = data.get("user_id")` but never validates that the required field is present before calling the service.
- Why it matters: A request with `{}` returned `200` and rewrote every item's `purchased_by` to `null`, destroying attribution data.
- Suggested fix: Match the existing `mark_purchased` route pattern: return `400` with `{"error": "Missing required field: user_id"}` before making any database changes.

### Questions for the Author
*Things you're uncertain about — design choices that could be intentional or bugs depending on intent.*

> Should this endpoint also validate that the list exists and return a clean 404 when it does not? The current PR code would return `{"purchased": 0}` for a bad list ID, which may not match the rest of the API.

### Verdict
- [ ] Approve — ship it
- [x] Request Changes — needs fixes before merging
- [ ] Comment — needs discussion before a verdict

**Rationale** *(1–2 sentences)*:

> Request changes because the endpoint can overwrite existing `purchased_by` / `purchased_at` values and can write `null` attribution when `user_id` is omitted. Those are data integrity bugs, not just response-format issues.

---

## PR #2 — List Stats (`pr2_list_stats.py`)

### Summary
*What does this PR do? (1–2 sentences in your own words)*

>

### Issues

**Issue 1**
- Location:
- What's wrong:
- Why it matters:
- Suggested fix:

**Issue 2**
- Location:
- What's wrong:
- Why it matters:
- Suggested fix:

**Issue 3** *(if found)*
- Location:
- What's wrong:
- Why it matters:
- Suggested fix:

### Questions for the Author
*A good code review often surfaces design questions, not just bugs. What would you want to clarify before approving?*

>

### Verdict
- [ ] Approve — ship it
- [ ] Request Changes — needs fixes before merging
- [ ] Comment — needs discussion before a verdict

**Rationale** *(1–2 sentences)*:

>

---

## Reflection

*Answer after completing both reviews.*

**1.** Which issue was hardest to spot, and why?

>

**2.** Which issues do you think an LLM reviewer (like Claude reviewing its own code) would most likely miss? Why?

>

**3.** One thing you'd add to a code review checklist for AI-generated backend code:

>
