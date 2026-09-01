# 审查

## 结论

通过。当前 `0.152.0` 的 `steer=removed` 已成为显式 runtime feature 门禁；schema 中存在 `TurnSteerParams` 不再被解释为可调用能力。调用前返回 `protocol_error/turn_steer_unsupported`，session、transport 和真实 `turn/steer` 均不启动。

## 证据

- current feature registry fixture 与脱敏摘要：`tests/watchdog/fixtures/feature-registry-0.152.0.json`、`evidence/turn-steer-retirement/feature-registry.json`。
- current digest negative contract：`test_current_removed_steer_fails_closed_before_session_or_control`、`test_factory_rejects_removed_current_steer_before_transport`。
- legacy lane tests continue to cover interrupt confirmation, expected-turn rejection and steer error classification.

## 已知边界

默认全量 legacy verifier 在本开发线仍受 manual-first bundle 与旧 workflow/release packaging 断言不一致影响；专项 watchdog、仓库 `validate-repo`、bundle generate/validate 与 diff 检查均通过。没有保存原始 feature 输出、schema payload、对话正文或本机路径，也没有触碰生产 `~/.codex`、AIO、GitHub、Secrets、runner、tag 或 Release。

## 主代理复核

- 已核对 `evidence/turn-steer-retirement/feature-registry.json` 与当前本机 feature capture 的路径和字段，确认 `steer=removed` 与 schema presence 分开记录。
- 已核对 current digest 的拒绝发生在 WatchService session 创建和 AppServerFactory transport 创建之前；历史 digest 的 CAS/interrupt 读取路径未被移除。
- 已接受该阶段为本修复计划最后一个过时点，后续不再继续扩大 CLI 能力修复范围。
