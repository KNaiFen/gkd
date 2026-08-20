# 验收与收尾：GKD-M2-C 自动运行时桥

## 最终结果

- 结果：完成
- 功能 PR：[KNaiFen/gkd#7](https://github.com/KNaiFen/gkd/pull/7)
- 被验收 head：`b25637d8f0989427f9bfe0cc46e603ffd3c79550`
- merge commit：`b16349af24ae76055f86f3b02437168404b97ff8`
- 候选与 merge tree：`1fca9da644148631b541dc61f58d670dd0917ceb`
- 必需 CI：无 configured checks；main branch 未保护，事实为 `required_checks_not_configured_bootstrap`，不视为 CI 成功
- 日期：2026-08-20

## 验收结论

- M2-C：两个隔离临时根与 fixed-head `git archive` 各通过 32/32；三份 fresh evidence 逐字节一致，archive payload 无 `.pyc` 或 `__pycache__`。
- 保留回归：task-core 104/104、role-routing 70/70、foundation 53/53、watcher core 47/47、watcher live-negative 15/15。task-core 首次因随机 capability 以 `-` 开头触发既有 `git grep` 参数歧义，完整重跑 104/104 通过；该测试与本任务 diff 无关。
- 提交证据：bundle digest `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad`；evidence file SHA-256 `c24847ff3390cbb72260d9b8b007846c0fc7eadf2840702f21748c5b9efe562b`；内部 evidence digest `ab6efbc3cded637edc1fd0acd155958a3949566d48282fa1c4bfa81b266bbb82`。
- Fresh evidence：验收时生产保护面的宿主元数据已较交付时漂移，因此 fresh 文件 SHA 为 `d3db4579c22477cd35a904c750fec9d4cfe03b0400a6c882d50f83c250777457`、内部 digest 为 `9f6fc240ad390a89c7b3df8739c06582831c4cf79c5f7f1ae91298389f1f37ae`；三次 fresh 输出一致且每次 production/AIO 均 before=after，未发现本任务污染。
- F-001：bridge 在构造、prepare、claim、recover 重新验证当前 bundle 实体、manifest/lock、content digest 及 role/config/Skill catalog；正常工作流中的删除或替换在新增写入前失败，恢复原 bundle 后可继续确定性 recovery。
- F-002：README 已明确 Python 3.11+；默认环境合同使用 Python 3.14.6 且未设置 `PYTHONDONTWRITEBYTECODE`。
- 历史 watcher evidence runner 因 Codex 从固定 `0.147.0` 漂移至 `0.148.0` 而拒绝重发版本绑定 evidence；47 项 core 与 15 项 live-negative 独立通过，未重跑历史 live probe。

## 接受的边界与风险

- M2-C 继续保留一次性 bootstrap 事实：task 为 `planning / epoch 1 / revision 5`，无 claim、delivery、activation 或 receipt；不得补造这些记录。该例外随本次合并终止，M3 及以后必须使用正式 automatic bridge。
- 同一 OS 用户在单次 bridge 调用内部通过 private API、monkeypatch 或并发直接篡改 bundle/runtime 不属于批准的威胁模型；不为此增加 bundle 锁、签名、daemon、IPC 或权限隔离。
- `project-remove` 在 inventory 被外部删除后无法重新证明文件归属，按用户明确放宽保留为非阻塞 residual risk。
- 本仓库没有 `scripts/check-local-verification.mjs` 或 `.trellis/scripts/task.py`；未伪造 `local_ready`、task accept、archive 或 validate 结果。

## 长期记录

- `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad` 成为已接受的 M2-C execution-bundle upgrade；M2-A custom-role、M2-B 一小时等待事实与 M2-C bridge 合同均保留各自固定证据。
- 当前 Session 启动时尚未从 accepted staged project 发现 exact `gkd_executor`，因此不在本 Session 启动 M3。后续必须先 staging、验证 accepted bundle/role/config/offer-claim/wait gates，并从 fresh main 精确发现 `gkd_executor`；任一不匹配继续 fail-closed，禁止 generic worker、角色替换、模型降级或 fallback。
- M3 继续按 A fixed-head CI/policy、B 资源与数据保护 core、C review core/两项新 Skill 的依赖顺序实施。

## 归档与清理

- 归档路径：任务资料保留在 `tasks/m2-automatic-runtime-bridge/`；本仓库无 Trellis archive 入口。
- records-only 提交：终态验收记录由 `ed03708bfd067715bf1935a15bfa928dd8d7adf7` 先进入 main；本次提交回填实际清理结果。
- worktree：`/Users/knaifen/Documents/Codex/gkd-worktrees/m2-automatic-runtime-bridge` 删除前已确认 clean、head 为被验收 fixed head、tree 与 merge tree 一致，随后已删除。
- 本地/远端分支：`task/m2-automatic-runtime-bridge` 与远端同名分支均已删除；worktree 列表仅保留 main。
