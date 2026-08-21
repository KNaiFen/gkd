# GKD-M2-I-R Requirements

## Goal

Re-deliver the already implemented generic M2-I trusted-host recovery bridge on the current main after M2-J fixed the delivery-document sequencing contract. This is a lifecycle redelivery task, not a new feature.

## User Decisions

- Continue automatically through M3, M4 and M5 with one exact accepted executor route.
- Keep the redelivery generic and do not weaken the M2-J contract or acceptance boundaries.

## Scope

- Port the M2-I bridge implementation and its focused tests from commit `27cf3293d6cc37c4f19a0b96d934d4b6c079db01` onto the current main.
- Preserve M2-J delivery sequencing: commit the canonical `delivery.md` alone, then invoke `gkd-task deliver` with its exact path and digest, and stop at the final task-state commit.
- Keep repository-neutral behavior, protected production/AIO surfaces, and the original M2-I acceptance criteria unchanged.

## Non-Goals

- No M3 policy/monitor, M3-B resources/scanner, M3-C review/Skills, release, production installation, AIO, or GitHub settings.
- No hand-edited task state, history rewrite, acceptance bypass, direct merge, or reuse of the old M2-I candidate.

## Acceptance Criteria

1. M2-I bridge implementation and focused tests are present on the current main base.
2. Approved local verification, deterministic evidence, and candidate bundle verification pass.
3. Delivery has the exact implementation -> delivery-document -> final state parent chain required by M2-J.
4. Trusted main independently accepts and merges only the exact fixed head.
