# GKD-GATE-REPAIR Retrospective

## What Worked

- executor 完成了逻辑顺序、planning refresh 和 result manifest 的主要实现，并在 candidate 自带 bundle 中通过 task-core 135/135、gate focused 29/29、runtime bridge 22/22。
- trusted bridge 的 offer/claim、candidate output 与 delivery document 绑定路径可运行，PR #39 和 fixed-head CI 事实可追溯。

## Failures

- executor 在第一次 `deliver` 后才发现旧历史兼容问题并提交 `1952745` 修复，破坏了 delivery writerless/fixed-head 约束；该修复必须回到 delivery 前的新 attempt。
- 新 `logicalOrder`/delivery 字段只在 candidate bundle 中可读，trusted main 的 acceptance validator 仍按旧 schema，造成 `status/doctor/rework` 无法读取已交付状态。
- 新增 `result-manifest.schema.json` 没有同步 packaging expected set，导致 fixed-head verifier 436 项中 1 项失败。
- candidate output digest 在中途重新生成后没有回写 delivery/result manifest，最终 bundle 与交付声明漂移。

## Required R1 Changes

- 所有状态 schema、validator、acceptance/rework 和 packaging manifest 必须在同一个 implementation head 完成，并在 delivery 前由 trusted main 可读取验证。
- delivery 后禁止任何代码或 manifest 提交；任何失败必须 canonical rework 到 planning 并新建 offer/claim。
- candidate bundle、result manifest、delivery state 和 delivery document 必须使用最终同一 digest/head；增加 packaging expected-set 与 digest drift 的负向合同。

