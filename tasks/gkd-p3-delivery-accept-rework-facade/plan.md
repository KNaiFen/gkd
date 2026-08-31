# P3 交付、CI、验收与返工外观实施计划

## Design

- 在 trusted-main orchestration 层复用 `TaskService`、`gkd_role` project/policy、CI monitor 和 acceptance/rework service，不复制状态机。
- 增加只读事实解析与最小意图入口：delivery 只接收完成意图，CI 只接收固定 PR 观测意图，accept/rework 只接收独立 review 与 merge/rework 意图。
- 所有生成事实在外部写入前从 canonical state、固定 tree、policy/origin 和 PR snapshot 重算；任何不一致返回稳定错误且不改状态。
- 通过兼容适配保持 legacy CLI 和历史 record 的读取与拒绝路径，不改变 task state schema。

## Verification

- 为每个 facade 增加正向、缺失、替换、漂移、重复和写前不变合同；重点覆盖 O4/R7/R8/R9 记录的真实失败形态。
- 使用 Python 3.9.6 与 3.14.6 运行完整 `scripts/gkd-verify --base-sha 142429bb0d70717afc92a2740832a111a186a16b`，并生成双运行一致 evidence。
- 由 trusted main 创建 PR，使用相对 `.gkd/policy.json` 的 fixed-head monitor；独立 acceptor 在 merge 前完成 review，随后才允许精确 merge。

## Boundaries

executor 只实现本任务并停在 delivery；不验收、合并、返工、归档或清理。trusted main 独占 acceptance、merge、rework 和 cleanup；本任务不触碰生产或 AIO。
