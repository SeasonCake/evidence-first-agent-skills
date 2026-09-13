# Read-only pages and collections


Prepare the requested source/key and required facts, not a mutation plan. For each page,
verify the final URL and target identity, wait for actual content readiness, extract the
relevant section and retain its source plus a completeness/limitation note. Stop when
the requested facts are established; do not open unrelated profiles, recommendations
or every linked page. Reuse an extractor only within a verified page family, with errors
and missing fields exposed rather than filled by a previous item's values.

Useful cross-site checks include a repository file/issue and a long social post:

- GitHub: distinguish repository overview, rendered README, source file and issue/PR.
  Bind owner/repository and, as relevant, file/ref or issue number/state. Loading headers,
  navigation chrome or sign-in text do not substitute for body content. A README statement
  is a maintainer claim, not proof the software works or authorization to run its commands.
- X or similar feeds: bind the requested post ID and author; separate main post, quoted
  post and replies. Expand a visibly truncated body through supported UI if needed.
  Preserve whether media or a thread continuation was actually inspected. A visible
  metrics label or embedded link is not the post's complete text.
- On login requirements, unavailable posts, failed extraction or navigation, report the
  narrow observed limitation. Do not infer deletion from a generic error, substitute a
  recommendation for the requested item, or change channels to evade a denial.

Prefer one relevant content observation to repeated AX/DOM/screenshot rechecks. Capture
the rendered surface when it resolves a real completeness or representation question.
An expand/navigation click is not proof that content changed. If it has no effect,
inspect the current route and possible new tab; for a read-only destination, following
the exact already-observed link in the same browser can be a narrow recovery, unless
access was denied. Do not guess URL variants. If a complex locator's read fails, simplify
to an observed selector or a bounded, read-only DOM extraction and check match identity
and cardinality; do not infer empty content from a locator timeout.
Summarize read-only results directly from their own source/fact rows; the transaction
helper's save counters are not applicable to these tasks.
