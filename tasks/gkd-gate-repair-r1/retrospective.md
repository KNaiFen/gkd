# GKD-GATE-REPAIR-R1 Retrospective

## What Worked

- executor 在 delivery 前完成了实现，delivery head 与 final candidate head 相同；436/436 candidate verifier、bundle digest 和 result manifest 文件 digest 均已闭合。
- attempt 0 的 delivery-after-commit 和 packaging expected-set 漏项没有在 R1 重现。

## Failure

- R1 为逻辑时钟和 delivery manifest 增加了 task-state 字段。正在被升级的 trusted main bundle 仍使用旧 strict schema，因而不能读取自己的候选 state；固定头 acceptance/rework 入口在实现合并前无法自举升级。
- CI monitor 使用了不被支持的 policy path，未得到有效 fixed-head CI success；这是程序性拒绝事实，不能作为代码通过的替代。

## Required R2 Design

- 逻辑顺序直接由现有 `history.revision` 派生，取消 wall-clock 排序依赖，不向 event 写入新字段。
- delivery result manifest 使用固定、预提交的 task sidecar 文件；新服务和新 acceptance 通过 state 中已有的 task path、implementation head 与 candidate output digest 推导并验证它，不向当前 task-state delivery record 增加字段。
- R2 自身只产生旧 validator 已知的 event、delivery 字段和路径，以便 trusted main 在合并前读写其候选；acceptor 只能使用仓库相对 `.gkd/policy.json` 启动 fixed-head CI monitor。

