# GKD O6 Default Role And Optional Pack R2 Implementation

## Internal Design

以 source/manifest/lock 的版本化 pack 声明区分 core 与按需能力。默认 project stage 和 executor role 只解析 core skills/runtime；显式 pack 操作从同一声明生成受管文件清单、配置和 inventory，并对实际文件重算 digest。旧 manifest 继续通过既有兼容入口读取或明确拒绝，不用隐式 fallback 扩大默认面。

## Execution Details

第一步执行 bridge execution context 提供的精确 status/doctor argv，禁止裸 `gkd-task` 或 cwd 推断。先记录 default executor、main/acceptor、production migration 和两个 optional 能力的全部 consumer；以最小 API 实现 core/pack 分层，并覆盖未请求、组合 stage、remove、missing/extra/tampered/symlink/unknown pack 与 legacy migration。final implementation commit 必须含实际双解释器 verifier result/evidence/result-manifest；delivery 后停止。

Epoch 1 先重现并修复 P1：接受 schema-v1 的 source loader 不得访问 `packs`。以版本化 parser 分派保持 v1 source generate/verify 正常，v2 才要求并验证 pack declaration；新增 source-side v1 回归与 v2 negative contracts，随后重跑完整 core/optional 验证。
