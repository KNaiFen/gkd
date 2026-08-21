---
name: gkd-review-remediation
description: Guide explicit review findings through partial approval, resume, and recovery using redacted machine facts.
---

# GKD Review Remediation

1. Start with the shared review core. Use `targeted` only for an explicit target and intent; use `guided` or `recon` when the request needs clarification.
2. Keep ambiguous intent in recommendation state. Never silently approve, merge, rerun, or dispatch.
3. Record findings as redacted identifiers, severities, summaries, and digests. Never retain credentials, authorization headers, transcripts, raw logs, or machine paths.
4. Partial approval must name the approved findings or review action. Resume requires an explicit continuation and preserves the prior cursor and machine facts.
5. On interruption, use recovery to return the canonical state and continue only after the user or trusted main supplies the next explicit decision.
6. Stop at a remediation plan. File edits, CI reruns, merge, and external settings remain outside this Skill.
