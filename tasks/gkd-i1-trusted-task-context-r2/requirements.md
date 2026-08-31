# GKD I1 Trusted Task Context Requirements

## Goal

交付只读的 trusted-main task context 与受管 planning package/preflight，使 Agent 在正常任务定位和规划包准备中不再手填 repository、branch、task path、candidate/runtime root、完整 status/doctor argv 或 package root，同时保持现有任务状态、CAS 与信任边界不变。

## User Decisions

- 基线为 trusted main `bdfb493e7566fb936195352812bd0ae048f409a8`；execution bundle 为 `e22f2a44ce0e4e8ac62fe449a8d6c64446d5f20fac9ee03f234e0406724249ce`，project inventory 为 `e32e966206fa7ea3a9cfda64e5e8b9f32d9ae26bfbc5667be7fcf0766b41b78e`。
- 本任务是编排输入面收敛计划 P1 的 fresh R2 lifecycle。R1 已因 executor 在 claim 前观测 offer head 而 block；一个精确 executor 交付，一个独立 acceptor 验收，trusted main 合并和清理；不复用 R1 的 task、offer、claim、runtime、candidate、patch 或提交。
- P1 仅增加只读 context/preflight 与受管 planning package 入口；不改变 bootstrap、stage、automatic route/claim/wait、delivery、CI、accept/rework、production、AIO、settings、Secrets、runner、tag 或 Release。R2 executor 在收到 trusted main post-claim activation message前不得读取 task 状态。

## Scope

- 在 task-core locator 层建立不可变 `TrustedTaskContext`：从 candidate cwd、trusted-main cwd 加显式 task selector，或唯一 runtime attachment 安全解析 candidate、runtime、task identity、repository/base/branch/path、policy、当前 snapshot 和 self-verified bundle/project inventory binding。
- 新增已安装的 trusted `gkd-main` CLI，提供只读 `inspect`/`preflight` 以及 `planning create`/`planning inspect`；正常输入不再接收或输出 filesystem root、repository、branch、task path、runtime root、CAS、capability、envelope 或绝对 production path。
- `planning create` 接收三份实际人类 Markdown 内容，先以现有 strict parser 原子校验再发布受管 package selector；`planning inspect` 只返回 digest/status/缺失人类内容，消除空 package root 的人工交接。
- 扩展 manifest/lock、安装、source/installed layout 分类和正反合同；P1 不改低层 `gkd-task` 参数契约，后续高层 transition 才消费 context。

## Non-Goals

- 不让高层 CLI 自动 bootstrap、创建 worktree、写 runtime attachment/capability/offer/claim/receipt，或调用任何 `gkd-role automatic-*`、candidate-side claim、route、wait、delivery、accept/rework。
- 不从 cwd/source/candidate 推断 bundle identity，不默认 production root，不改变 existing low-level diagnostic/compatibility CLI 或历史任务 documents/schema。

## Acceptance Criteria

1. candidate cwd、trusted-main cwd 加 selector、唯一 attachment 三条允许路径解析出等价 context；零/多匹配、symlink、identity/origin/policy/bundle/project-inventory drift 全部 fail closed，且 inspect 前后不产生 Git、runtime 或 task 状态写入。
2. `gkd-main inspect/preflight` 只输出 path-free selector、policy/bundle binding、snapshot、允许下一动作和仍需人类输入；不泄漏 capability、envelope、absolute candidate/runtime/production path 或 CAS 写入输入。
3. `planning create` 不接受 package root，成功包可由现有 `inspect_package` 重读；缺失、空、symlink、UTF-8/line ending/heading/section 不合法或写前失败时不发布 package，也不写 Git/runtime。
4. canonical source 与 installed bundle layout 严格分类；`gkd-main` 在已安装 core bundle 可执行并从 installed library 导入，manifest/lock/inventory 完整覆盖。
5. Python 3.9.6 与 Python 3.14.6 的 core verifier、bundle/install、P1 focused contracts、fixed-head CI 和 independent acceptance 均通过；不引入绝对路径、凭据、外部依赖或未授权副作用。
