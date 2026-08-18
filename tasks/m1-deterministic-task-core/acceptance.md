# 验收与收尾：GKD-M1-A 确定性任务核心

> 仅记录 main 对固定 head 的终态验收。执行者交付事实保留在 `delivery.md`。

## 最终结果

- 结果：完成
- 功能 PR：https://github.com/KNaiFen/gkd/pull/5
- 被验收 head：`f0b339c0d52ae9325137e9f188b710645c2e2e80`
- implementation/evidence commit：`0548eb52ead7191733c32129241168c2e7035a9f`
- merge commit：`5eb3bd34ef389361be2ba22df899ad088ef22da1`
- 候选与 merge tree：`938d02ed18a3ff256a63e707e01cbd3dc86d6649`
- 必需 CI：无；仓库尚无 configured checks，状态为 `required_checks_not_configured_bootstrap`，不记为 CI 成功
- 日期：2026-08-19

## 验收结论

- AC：两轮续交共发现的 candidate-only claim、runtime/tracked 事务顺序、生命周期/历史不变量、resolve 前 symlink 拒绝和 stale migration CAS 五个阻塞反例全部闭环。
- 独立复验：task-core 104 项在两个隔离系统临时根各通过一次；foundation 53 项、watcher core 47 项和 watcher live-negative 15 项通过。未运行历史四场景 live probe。
- 确定性证据：两个 task-core 输出彼此及提交 evidence 逐字节一致；文件 SHA-256 为 `7df2d35021ba32eb93d1ebd84d3920e7ac4ee281a68e7c4da935cfcfa306bb65`，内部 evidence digest 为 `3f119831c41a18536318b621f21f13d8d18d115fce77e3fb97870a0148395569`，临时 fixture 根最终为空。
- 发行事实：development version 仍为 `0.0.0-dev.0`，content digest 为 `fc96a10cb82b628bd14280e4e878417a3fbc7a1d560fac5a61bb7abe7f3c3024`。
- 接受的缺口：main 无 branch protection 或 configured checks；固定角色、真实 runtime evidence provider、连续一小时等待门和 12 小时编排尚未实现或通过。
- 结论边界：只允许 `deterministic_task_core_ready`。里程碑 2 继续采用独立人工顶层 execution session；不得据此启用 auto route、生产安装、AIO 接入、tag 或 Release。

## 历史整改

- head `c35ac55fd299196a463bc31e8ff0f98ef37c3858` 因四项阻塞未通过且未合并；修复主体进入 `fee072bf6849d87ffd6a6323ea75a81af3504831`。
- head `f34152ddbe79c3b9ff12c6e2e97121c34fd8fffa` 因 stale migration CAS 会残留 attachment 未通过且未合并；最终修复进入 `0548eb52ead7191733c32129241168c2e7035a9f`。

## 长期记录

- 知识库与现行合同：`.agents/context.md`、`.agents/decisions.md` 和 `.agents/open-items.md`。
- PENDING：无。
- 下一步：清理 M1 worktree/分支后，按冻结计划规划里程碑 2 的角色、人工/自动路由、连续一小时等待、12 小时终止、最小角色上下文和 Skill 去重任务。

## 归档与清理

- 归档路径：`tasks/m1-deterministic-task-core/` 原位保留为 bootstrap 终态记录。
- 标准 `archive`/`validate`：未运行；本仓库没有 AIO `.trellis/scripts/task.py`，不伪造标准归档结果。
- `gkd-local-verify`：其指定的 `scripts/check-local-verification.mjs` 不存在于本仓库；records-only 变更改用固定 base 祖先关系、`git diff --check`、状态内容核对和 clean-main 检查。
- records-only 提交：终态记录由 `3a10658ef2d5940e7f38484e2fe9d31aa80fa3be` 写入 main；本次提交回填实际清理结果。
- worktree：`/Users/knaifen/Documents/Codex/gkd-worktrees/m1-deterministic-task-core` 已删除；删除前 Git 干净、head 为被验收的 `f0b339c0d52ae9325137e9f188b710645c2e2e80`，tree 与 merge commit 完全一致。
- 本地/远端分支：`task/m1-deterministic-task-core` 与 `origin/task/m1-deterministic-task-core` 均已删除。
