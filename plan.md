# Legacy Compatibility Baseline

## 工作目标

为 GKD 的 legacy-automatic / historical lane 建立当前 Codex CLI 兼容基线，修复对 `codex-cli 0.147.0` 和单一旧 schema digest 的硬编码依赖。当前 CLI 是 `0.152.0`；本阶段只让版本与 schema 漂移被明确识别和记录，不恢复 automatic watcher，也不改变 manual-first 默认入口。

## 工作目录

当前 Git worktree。

## 行为约束

- 只修改本阶段需要的兼容实现、测试和说明文档。
- 保留 `v0.1.5` 以及旧 `0.147.0` acceptance/evidence 的原始事实，不覆盖、不重写、不伪装成当前支持。
- 不修改生产 `~/.codex`、AIO、GitHub 设置、Secrets、runner、tag 或 Release。
- 不启用 `multi_agent_v2` 作为默认能力，不把旧 automatic 路径放回默认 bundle。
- 本阶段不处理 `turn/steer`；该问题是整个修复计划的最后阶段。
- 不新增普通任务所需的机器合同、CAS、receipt 或额外状态副本。
- 重要判断、阻塞和验证结果持续写入 `progress.md`。

## 范围

- `src/gkd_watchdog/constants.py`
- `src/gkd_watchdog/runtime.py`
- `probes/multiagentv2/native_probe.py`
- 与上述实现直接相关的 watchdog/probe 测试
- `src/gkd_watchdog/README.md`、`probes/app-server-watcher/README.md` 中的兼容边界说明
- 必要时新增版本化、脱敏的 compatibility baseline 记录

## 非目标

- 不修改子代理事件归一化（阶段二）。
- 不修改 MCP 协商和 metadata adapter（阶段三）。
- 不修改 CLI 文本 parser（阶段四）。
- 不修改 app-server initialize 能力判断（阶段五）。
- 不修改或替换 `turn/steer`（阶段六）。

## 完成条件

1. 当前 CLI 能生成并记录自己的版本、schema digest 和必要 feature 摘要。
2. runtime verifier 支持显式版本化 baseline；未登记版本明确返回 unsupported/需要重新 capture，而不是普通启动失败。
3. 旧 `0.147.0` baseline 仍可读取，历史 evidence 不被改写。
4. 默认 manual-first bundle、入口和项目配置行为不变。
5. 覆盖新增行为的最小测试通过，且 `git diff --check` 通过。
6. `progress.md` 记录实际变更、未运行的检查和剩余风险；完成后停止等待主代理审查。
