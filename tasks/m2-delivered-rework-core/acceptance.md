# 验收与收尾：GKD-M2-D delivered rework core

## 最终结果

- 结果：完成
- 功能 PR：[KNaiFen/gkd#9](https://github.com/KNaiFen/gkd/pull/9)
- 被验收 head：`e8729934f567d74ee19e7583b8f8433dacb9ac60`
- squash merge commit：`0976b4900346e972bd8e03f6e8fa4ab761fe8952`
- 候选与 merge tree：`a25603809da5b87ed814be0841217c372a92d8ee`
- 必需 CI：无 configured checks；事实为 `required_checks_not_configured_bootstrap`，不视为 CI 成功
- 日期：2026-08-20

## 验收结论

- 独立审查完整 requirements、任务状态转换、事务恢复、GitHub fixed-head 校验、CLI、schema、Skills、测试与完整 diff，未发现阻塞 finding。
- canonical accepted review digest：`893f53d79e3442c2881d528173f9fd23e6c3bcb9bcb294ae5a8da9a015d61655`。
- `scripts/gkd-verify --base-sha 5cc7f6bbc61c2a06ecdf2104a6e7cd3129f23959` 在候选 worktree 与 fixed-head archive 各通过一次：task-core 118/118、M2-C 32/32、M2-A 70/70、foundation 53/53、watcher core 47/47、live-negative 15/15。
- 交付 evidence digest 为 `da884bc1efe152ed983deda4c04d02bf95eafad17b2f61bd2f2067b729a2324d`，文件 SHA-256 为 `304a76c876677660fab22afded03c9257ed023fefc2673d05235defb281fc121`。
- 任务 claim 继续绑定旧 accepted execution bundle `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad`；候选输出 bundle `71c4b2d3562c2e5a6a784bf3436a7d5920cd00b3ad387f320a2563d4b5b88766` 经合并后成为新的 accepted execution-bundle upgrade。

## 接受边界

- 新能力仅允许 trusted main/acceptor 对 exact clean delivered candidate 和独立 rejected review 执行一次原子 rework；executor、旧 offer、旧 envelope、旧 activation 和旧 claim 均不能恢复执行。
- rework 保留旧 attempt、撤销旧 offer、递增 epoch 并返回已授权 planning；fresh automatic repair 必须重新生成完整六门 decision、offer、envelope、activation 和 claim。
- 本任务不实现 M3 policy/monitor、资源/scanner、review Skills、finalization 或 release，也未修改 PR #8 候选。
- 未重跑历史 custom-role probe、真实一小时实验或 M2-B early-final 实验；生产 `~/.codex` 与 AIO 未修改。

## 安装与清理

- accepted bundle 已安装到隔离临时根 `/var/folders/dv/7psz5djd3537ghdrhkpzy7dw0000gn/T/gkd-m2d-accepted.EofTm4/accepted/gkd` 并通过 installed `gkd-bundle verify`。
- 本仓库机器本地 staging 已原子替换并通过 `project-verify`：role/config/project-config/inventory digest 分别为 `880e1855cfdeb50ba890a3023c818cde377b9c6a71c230360154b79ecc16d680`、`10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`、`9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0`、`ce434766ef460d83d86bd8cdc6bae0822636f729086bf13031b18a32bf44500c`。
- 候选 worktree 删除前已确认 clean 且固定在被验收 head；`/Users/knaifen/Documents/Codex/gkd-worktrees/m2-delivered-rework-core`、本地和远端 `task/m2-delivered-rework-core` 分支均已删除。
- 任务资料原位保留；本仓库无 Trellis archive 入口。
