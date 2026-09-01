# 进度

主代理已审查并接受该阶段；这是本修复计划最后一个过时点。

## 2026-09-02

- 已创建独立工作树，基于主分支 `dce1d61`。
- 已确认本机 `codex-cli 0.152.0` feature registry 为 `steer=removed`，而生成 schema 仍列出 `turn/steer`；新增脱敏 fixture 与 `evidence/turn-steer-retirement/feature-registry.json` 保留这一区分。
- 已在 `constants.py` 登记版本绑定 feature registry；`WatchRequest` 接受已登记的 current digest 以进入能力门禁，`WatchService` 和 `AppServerFactory` 在启动 session/transport 前稳定返回 `turn_steer_unsupported`，不会发送真实 `turn/steer`。
- 历史 `0.147.0` lane 的读取、interrupt 确认、expected-turn CAS 与负向合同保持原行为；新增 current 负向测试并纳入 watchdog contract catalog。
- 专项验证：watchdog contract runner 52 项通过；官方 `gkd-verify --scope-internal watcher-core-and-live-negative` 64 项通过；bundle `generate` 输出 development digest `9a683001...` 且 `validate-repo` 返回 `valid`；`git diff --check` 通过。
- 已知边界：默认 `scripts/gkd-verify` 全量合同仍有既有 manual-first/开发 bundle 门不匹配（缺失 legacy `.github/workflows/gkd-ci.yml`、development manifest 与旧 release/packaging 断言不一致、安装临时文件缺失等），这些失败与本任务无关，未修改 legacy bundle、生产/AIO 或 GitHub 状态。
