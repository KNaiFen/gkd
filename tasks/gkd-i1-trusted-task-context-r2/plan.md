# GKD I1 Trusted Task Context Plan

## Goal

让 trusted main 在不执行生命周期写入的前提下，从唯一受信事实源形成 task context 与 planning package，消除最早一层的 Agent 定位、路径和空包交接错误。

## User Decisions

- 固定基线 `bdfb493e7566fb936195352812bd0ae048f409a8`，execution bundle `e22f2a44ce0e4e8ac62fe449a8d6c64446d5f20fac9ee03f234e0406724249ce`。
- P1 是输入面收敛的只读基础；R1 preclaim race 已退役，R2 executor 必须在 post-claim activation message 后才读取任务。automatic route、host spawn/claim、delivery/CI/accept/rework、document renderer 和 project-stage 收敛均留给 P2-P5。

## Behavior And Defaults

- high-level normal path 优先 candidate cwd；trusted main cwd 必须有显式 task selector，attachment fallback 必须唯一且重验 candidate/task identity。显式 selector 直接定位匹配 task record，不得先递归读取或校验无关历史 task；歧义和 drift 一律拒绝。
- context 的 bundle 只能来自 high-level CLI 自身已验证 payload，并与 project inventory/policy 比对；不可由 repo、candidate 或任意 source/target 路径猜测。
- planning package 由三份人类文档内容生成受管 selector；既有 parser 是唯一格式校验器，空模板和空 package 不是有效替代。

## Scope

- 在 `gkd_task.locator` 增加 context 解析与 runtime 的只读现有根打开/严格 attachment 枚举，新增薄 `gkd_task.orchestrator`/`gkd-main` CLI。
- 提供 inspect/preflight/planning create/planning inspect 的 canonical path-free machine output，更新 bundle source/manifest/lock/install 合同与 focused tests。

## Non-Goals

- 不修改 TaskService 的写入 transition、bridge execution context、offer/claim/activation、public automatic CLI 的 fail-closed 边界或 production migration。
- 不删除低层 `gkd-task` CLI、既有 documents、legacy reader 或 P5 才负责的 development bundle/stage transition。

## Acceptance Criteria

- 三种合法 locator 结果一致；显式 selector 不受无关历史 task drift 影响；所有不唯一/漂移/泄漏/写入反例拒绝；受管 planning package 可复读且失败无发布。
- installed `gkd-main`/library、manifest/lock、Python 3.9.6/3.14.6 verifier、CI 与 independent acceptance 成功。

## Compatibility

- 现有 low-level CLI 与 task/runtime/document schema 字节兼容；新增 high-level CLI 只读且不占用旧命令名。历史 candidate、attachment、source 和 installed bundle 继续按现有 read/reject 规则处理。

## Security And Data

- 不输出或持久化 capability、envelope、activation、receipt、绝对 production path；所有 candidate/task/runtime/source/bundle/project 路径拒绝 symlink、跨 common-dir 或未验证身份。缺失 runtime 不创建目录。

## Migration

- 合并后只刷新未发布 development bundle/project stage。P2 可依赖 context API；现有 Skills 和低层调用暂不迁移，避免一次改变执行边界。

## Public Interfaces

- 新增 `gkd-main inspect [--task-id]`、`preflight [--task-id]`、`planning create`、`planning inspect`；仅允许必要的人类文档/selector 输入。输出为 canonical JSON，不含机器路径或秘密。

## Execution Route

- gkd-main 完成 planning/authorization/offer/claim；spawn 前固定 acknowledgement 与 status CAS，spawn 后立即 bridge claim。executor 只交付，acceptor 只验收，trusted main 合并清理。

## External Side Effects

- 仅允许 task worktree/branch/PR、verifier/evidence 和只读 CI；P1 normal interface 本身不写 task/runtime/Git。禁止 production、AIO、GitHub settings、Secrets、runner、tag/Release 写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- `TrustedTaskContext` 必须在 locator 层而非 bridge；先复用现有 `_validated_candidate`、state policy/origin revalidation 和 `TaskService.status`，但为 runtime 增加不创建目录的打开与严格 attachment 枚举。`task_id` selector 必须走确定性索引或直接候选路径读取，不能调用会扫描全部 `tasks/**/task.json` 的宽泛历史校验；只有选中的 task 才执行 `read_state`。
- high-level bundle identity 仅从 self payload `verify_bundle_root` 和 current project inventory 推导；P1 只分类 canonical source 与 installed layout，不实现 P5 的 build/stage transition。
- package create 使用临时受管目录、现有 `inspect_package` 与原子 publish；implementation commit 后 delivery.md 是唯一直接子提交，delivery 后不再加入实现提交。
