# GKD-O3 Requirements

## Goal

消除 `gkd-verify` 与各 scope/evidence runner 对同一行为测试的默认重复执行，同时保留 protected surface、temporary/output、digest、environment 和 evidence 边界校验。

## User Decisions

- O3 从 O2 accepted merge `2107ebccfb1f11979cf38d5b6ce1281bfb122bbb` 之后的 trusted main 完整 SHA 启动。
- 默认只执行一次 canonical scope 行为断言；重复执行必须显式标注为不同 evidence lane。
- `gkd_executor` 交付、`gkd_acceptor` 独立验收、trusted main 合并和收尾；失败 attempt 不沿旧 head 重试。
- 不移动 watcher/probe、fixture、optional pack，不改生产 `~/.codex`、AIO、settings、Secrets、付费 runner、tag/Release。

## Scope

- 让 `scripts/gkd-verify` 生成固定 scope、test ID、结果和环境摘要，并提供 evidence runner 可消费的稳定结果格式。
- 修改 scope `run_contracts.py` 或共享 wrapper，使其在复用 canonical 结果时不重复执行同一行为测试。
- 保留 evidence runner 特有的 protected/temporary/output、manifest/lock、路径泄漏和双运行字节一致检查。
- 为结果复用、缺失/篡改/固定 head 不匹配和显式重复 lane 增加契约与 mutation 覆盖。
- 更新 manifest/lock、docs、task evidence；不改变测试语义或默认 core scope 列表之外的历史 lane。

## Non-Goals

- 不移出 `watchdog-core-and-live-negative`（留给 O4），不拆 runtime fixture（O5），不拆 optional Skill/pack（O6），不做 contract index（O7）。
- 不删除 protected surface 或把失败结果降级为 warning；不新增第三方依赖。

## Acceptance Criteria

1. 默认 canonical verifier 对每个 scope 的行为测试只执行一次，结果包含固定 head、scope、test ID、状态和环境摘要。
2. evidence runner 能消费 canonical 结果并继续执行自身边界校验；缺失、篡改、head/digest 不匹配均 fail closed。
3. 现有 scope/test 覆盖不下降，task/role/foundation/CI/review/release/watchdog 行为断言保持通过。
4. 两次完整 verifier/evidence 输出在同一输入下字节一致，路径和凭据不泄漏，manifest/lock 自洽。
5. `gkd_executor` 交付、独立 fixed-head CI/acceptance 和 trusted merge 成功，生产/AIO 等禁区无变化。
