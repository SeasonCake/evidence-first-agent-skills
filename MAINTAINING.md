# Maintaining and releases

The repository uses Semantic Versioning. A skill behavior change requires a synthetic
known-good and known-fail case plus a forward validation; wording-only changes still run
the repository verifier.

## Pull requests

- Keep skills project-neutral, explicit-only, and usable without hidden inputs.
- Preserve attribution and distinguish upstream inspiration from local project origin.
- Avoid universal rules based on one incident; encode only a generalizable decision.
- Require DCO sign-off and a clean `python scripts/verify.py` result.

## Release checklist

1. Review the exact commit range, skill descriptions, invocation policy, and public boundary.
2. Run the repository verifier, unit tests, and current Codex skill validator for all skills.
3. Install each skill into a clean temporary Codex home and verify discovery plus explicit invocation metadata.
4. Verify README links, attribution, license, changelog, source archive, and checksum.
5. Tag `vX.Y.Z` only after the version and changelog agree.

Creating a remote repository, pushing, changing visibility, and publishing a release are
separate maintainer actions; this document does not authorize them.
