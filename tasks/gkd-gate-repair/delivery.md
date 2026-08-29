# GKD Gate Repair Delivery

## Implementation

Implementation commits `2ef5b669088ee7804a361b8f724e943acb634ad2` and `48463279a469e28e77bae7e0614f2410571ab69b` add persistent logical ordering for lifecycle events while retaining UTC audit timestamps and accepting legacy states without the new field. The canonical `planning-refresh` CAS transition recomputes the three tracked document digests only in `planning`; later phases remain immutable and fail closed on drift. Automatic delivery validates a canonical result manifest bound to task, base, implementation head, claim, execution bundle, candidate output bundle, scope digest and generation facts before writing state.

## Verification

The focused contract set passed: 84 task-core/planning/lifecycle/mutation/runtime-bridge tests, including the three gate-repair tests. Bundle generation produced 104 files with candidate output bundle digest `f39700161c8b416f97a8ac7cb2c20ada70d4d12dcb3b2575b4134268c74a8e5d`; evidence digest is `d81e86c6bf0ed7035d4a780f3e833a68e88b064df27c8d555dd54803b058904e`. The result manifest is `tasks/gkd-gate-repair/result-manifest.json`, its file digest is `361de8ee13c1f2d332f44ad827a65ce4f624fa5a0f4880425f4aa57cc3affb4c`, and its internal manifest digest is `a788ca6e4e99835ff4813ad5074f17e221a5659baf39e19bbf5dd9e78131e636`.

## Fixed Facts

Base SHA: `69cd40d0fa31b45ba3ce36e24eda2c42125fcd15`.

Claim ID: `17ee31c22f39949ba12457935e65979e3b9ad2229dbacae62aa9424283dae637`.

Execution bundle digest: `06095243b2199672243b559e0af2798fb9e051e33281775b98bc68c8b16ac48a`.

Host contract: `host-spawn-acknowledgement-v1`; executor attempt is bound by the trusted bridge claim.

Cleanup: no production, AIO, GitHub settings/Secrets, tag, Release or published asset was changed; candidate and runtime roots remain in place for trusted main acceptance and cleanup.
