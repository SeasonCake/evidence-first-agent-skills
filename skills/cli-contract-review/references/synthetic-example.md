# Synthetic example

Use this example to review setup failure versus product failure.

## Command contract

```text
sample-build --input fixture.json --output out --preflight --receipt receipt.json
```

## Known-fail behavior

When `--output` is missing, the command writes a partial stage and then asks an interactive
question. Both malformed input and a compiler error return exit code 1 with no receipt.

## Known-good behavior

- `--preflight` validates exact inputs and writable paths without creating output.
- Missing input returns a setup/input receipt and no partial stage.
- Compiler failure returns a distinct product-failure receipt.
- Repeating a successful command reports `already complete` or deterministically replaces
  its owned output.
- Help identifies shell/interpreter assumptions and shows a copyable non-interactive call.

The review reports gaps; it does not execute the build or grant release authority.
