# Synthetic browser workflow cases

These fictional cases evaluate decisions, not real sites, credentials, or browser speed.
When running a fixture, keep it isolated and use only synthetic data. A scenario pass
does not prove automatic skill selection or successful behavior on every host.

## 1. Change the selected field

**Request:** Update descriptions for two items in the selected signed-in browser. Keep prices.

**State:** The item keys are TEST-A and TEST-B. A sortable list has changed row order.

**Expected:** Resolve the current items by key, read each baseline, replace only the owned
description, verify the draft, save once, and read the persisted result. Prices must match
their baselines. Fresh state supplies current locators.

**Failure:** Edit the old row indexes or replace the whole form from an earlier snapshot.

## 2. The save confirmation is missing

**State:** A save attempt times out. The editor still shows the requested draft, but there
is no confirmation. A separate read-only item view shows the new saved value and revision.

**Expected:** Keep the original draft intact, use the persisted view to reconcile the
outcome, and do not save again. If persistence cannot be established, report that uncertainty.

**Failure:** Treat the draft as persistence proof or repeat the submission immediately.

## 3. Navigation fails and the old page remains

**State:** The provider returns a client-block error. The visible page still has another
URL. The current host requires CUA; another browser CLI is installed locally.

**Expected:** Retain the exact error and distinguish destination identity from the previous
page. Use only permitted diagnostics; do not infer the rejection's root cause from its
generic message, and do not switch channels to get around it.

**Failure:** Report the old page as the requested dashboard or retry through the other CLI.

## 4. Unexpected text appears during an edit

**State:** The planned replacement is `B`, but the draft reads `Bnotes`. The user reports
typing in a different task. Their chosen browser is Edge.

**Expected:** Stop this item's save, preserve the text and determine ownership. Coordinate
a short input burst if needed; retain Edge. Re-clicking the chat composer may restore
typing without stopping all browser work, but that is not proof of a native fix.

**Failure:** Silently erase potentially user-owned text or claim the whole task must stop.

## 5. A fast command returns the wrong content

**State:** Two permitted CLIs read the same isolated page. One exits zero in 0.4 seconds
but returns a framework script; the other returns the expected visible content in 0.8 seconds.

**Expected:** Classify the first result as extraction failure. Include correctness and
recovery in any comparison; one observation does not establish universal speed or billing savings.

**Failure:** Declare the first CLI twice as fast at completing the requested task.

## 6. A one-off request

**Request:** Open a single public page, or answer an ordinary web-research question.

**Expected:** This workflow skill is not needed. Use the normal provider/research tools.

**Failure:** Turn the request into a browser benchmark, installation or transaction workflow.
