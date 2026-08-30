# GKD O5 Runtime Fixture Split R2 Implementation

## Internal Design

以 source declaration 区分 core install file 与 fixture/test input。fixture consumer 接受显式的可验证根或 release-verification input，并对文件集合和 digest 执行严格校验；core 安装验证拒绝 fixture 泄漏，release traceability 仍绑定相同内容事实。

## Execution Details

第一步执行 bridge execution context 提供的精确 status/doctor argv，禁止裸 `gkd-task` 或 cwd 推断。先记录四个 fixture 与 consumer 的实际路径，再以共享声明最小迁移，不用删除验证或硬编码通过缩短路径。final implementation commit 必须含实际 verifier result/evidence/result-manifest；delivery 后停止。
