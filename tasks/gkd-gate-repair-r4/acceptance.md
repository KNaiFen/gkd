# GKD-GATE-REPAIR-R4 Acceptance

## Outcome

Blocked before implementation. Block head `1a8eadd935f30da2f7e84dff6a3173668d861bd1`，revision 8；未创建 PR、未交付、未验收或合并。

## Evidence

- executor 的 `/usr/bin/python3` 为 Python 3.9.6，payload wrapper `#!/usr/bin/env python3` 在其环境解析到该解释器。
- 使用该解释器的 `gkd-task status`/`doctor` 返回 `FILESYSTEM_ERROR`；直接调用显示根因是 `gkd_task/model.py` 的 `zip(..., strict=True)`，Python 3.9 抛出 `TypeError: zip() takes no keyword arguments`。
- `/opt/homebrew/bin/python3` 3.14.6 对同一 candidate/runtime 返回 status ok/implementing，证明路径、runtime 和 task state 并未损坏。
- trusted main 以 canonical `gkd-task block` 写入 `executor-python39-zip-strict-incompatibility`，没有手改状态。

## Boundary

R5 必须恢复 Python 3.9 兼容或在入口返回明确、非伪装的版本错误；不得依赖 executor 私有 PATH。生产、AIO、GitHub settings/Secrets、runner、tag/Release 未修改。

