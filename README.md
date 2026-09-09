# UPA - Universal Payment Agent

An open working draft of schemas for agentic payments: how an AI agent proves it is allowed to spend, and how much, enforced outside the model.

**Status:** UPA-2.0-RC1-BETA (working draft, June 2026). Expect breaking changes.  
**License:** MIT. Sole author so far - collaborators welcome.

## What this is

- `v2/payment-intent.json` - the transaction contract every agent payment must satisfy
- `v2/capability-token.json` - the signed spend-authority profile (caps, whitelists, expiry)
- `reference/` - test vectors and conformance notes (TV-001 live; TV-002 to TV-011 in progress)
- `v1/` - legacy UPA-1.2 schemas, kept for history

## What this is NOT

- Not affiliated to enterprises: UPA targets enterprise/B2B agentic payments, rail-agnostic.
- Not a finished standard. No conformance certification exists yet; "Working Group" is currently one person and this repo.

## Known issues

- Money fields are JSON numbers today; moving to minor-units integers next revision.
- More test vectors landing incrementally.

## Contributing

Feedback: open an issue or PR.

---

**Last Updated:** June 2026
