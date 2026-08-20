# GKD-M2-J Implementation Notes

## Internal Design

- Add a delivery-document binding to the versioned delivery record and validate the exact parent/document/state sequence in fixed-candidate acceptance.
- Make the service and CLI accept one canonical delivery-document path/digest; reject missing or ambiguous facts before task/runtime writes.
- Update `gkd-execute` with the required ordering and add focused service/acceptance/mutation tests.

## Execution Details

- Begin with installed status/doctor and inspect task model, service deliver, fixed-candidate acceptance, executor Skill and retained tests.
- Add failing tests for the M2-I post-delivery-document shape, then implement the smallest additive contract.
- Run `scripts/gkd-verify --base-sha 6b5d5b78a3c5f5cc98d0659167b5d3838d14f518`, generate two byte-identical evidence sets, regenerate manifest/lock, deliver one PR and stop before acceptance/merge/cleanup.
