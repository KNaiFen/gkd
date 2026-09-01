# turn/steer 退场适配

## 目标

修正 GKD 对当前 Codex CLI `turn/steer` 的运行时假设：feature registry 已将 `steer` 标记为 removed，不能因为生成 schema 仍保留 `turn/steer` 字段就执行或宣称支持该调用。当前路径必须显式返回 unsupported；历史 `0.147.0` 读取和既有负向证据保持可复核。

## 范围

- `src/gkd_watchdog/watcher.py`、`src/gkd_watchdog/jsonrpc.py` 或能力门禁所需的最小 runtime 模块
- turn/steer 相关测试、夹具、contract catalog、README/evidence
- 本任务 `progress.md`、`review.md` 和必要 `.agents/` 状态记录

## 约束

- 本阶段是本修复计划最后一个过时点；不要再扩展到新的 CLI/MCP 能力。
- 以本机 CLI feature capture 为事实：`steer=removed`；schema 中存在不等于运行时可调用。
- 当前 `0.152.0` 不发送真实 `turn/steer`；在调用前稳定 fail-closed/unsupported，并保留可审查原因。
- 历史 `0.147.0` watcher 读取、CAS/interrupt 负向和旧证据不删除、不重写为当前支持。
- 不修改生产 `~/.codex`、AIO、GitHub、Secrets、runner 或 release；不保存原始 payload。

## 完成标准

1. 当前运行时路径不会把 `turn/steer` 当作可调用能力，且有稳定负向测试。
2. schema presence 与 runtime feature availability 的区别在代码/文档中明确记录。
3. 历史 lane 继续通过，现有 watcher 的其他终止/取消语义不被扩大改动。
4. 相关专项、watchdog、仓库校验、bundle 生成和 `git diff --check` 通过，并在进度/审查记录中说明已知 legacy/manual-first 失败边界。
