# 进度

## 2026-09-02

- 已创建独立工作树，基于主分支 `6a41acb`。
- 已复核当前 `0.152.0` direct JSONL 与历史 `0.147.0` payload wrapper 解析边界；当前仅接受
  `thread.started`、`turn.started`、`item.started`、`item.completed`、`turn.completed`、
  `turn.failed`、`error` 外壳，协作 item 具体字段无脱敏 capture 时保持
  `UNSUPPORTED_*`。
- 收紧 current parser：`thread.started` 必须携带非空字符串身份；current 父/子 rollout
  缺少对应身份直接 `UNSUPPORTED_ROLLOUT_FORMAT`；parsed adapter metadata 的 CLI 版本、
  format、source 必须有效且一致，避免调用者伪造版本/格式关系。
- 将 `turn.failed` 作为 terminal lifecycle 事实记录，同时保留脱敏 host error；未改变
  legacy `0.147.0` spawn/task/fork 和 child terminal 语义。

## 验证

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:canonical/payload/lib:. python3 -m unittest tests.role_routing.test_handshake_preflight`：27 项通过。
- role-routing 全量：84 项中 81 项通过；3 项为 manual-first 默认 bundle 已移除
  `gkd-role` CLI/manifest 的既有 packaging 失败，与本任务无关。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib python3 canonical/payload/bin/gkd-bundle validate-repo --repo-root .`：通过，返回 `status=valid`、`visionSections=7`。
- `... gkd-bundle generate --source-root canonical`：通过，bundle `0.0.0-dev.1`、content digest
  `9a683001...`、115 个 source 文件，字节未漂移。
- 隔离 temporary root 的 `gkd-bundle install` + `verify`：通过，默认 core 16 文件、digest
  `9a683001...`。
- `compileall` 与 `git diff --check`：通过。
- 默认 `scripts/gkd-verify --base-sha 6a41acbf76bfa2f76303839a358d9742b4e52df8`：450 项中
  441 项通过；其余 9 项是 manual-first 默认 bundle/旧 workflow 与 legacy packaging
  断言不一致（以及既有 runtime bridge/import 夹具问题），不由本任务改动引入。
- 主代理已审查并接受该阶段，待主工作树提交。
