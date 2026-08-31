# GKD O8 Release Upgrade Compatibility Implementation

## Internal Design

实现一个版本化 legacy-format catalog，列出 format name、公开 surface、core read test ID、core reject-or-restore test ID 和 release-upgrade matrix test IDs。catalog 验证每个 ID 的存在、唯一归属、core/matrix 互补性和完整性。新 lane 由现有 canonical result 机制绑定严格 scope；迁入测试只移动执行归属，不改变其断言语义。ADR 记录两个 release domain 仍使用独立 CLI、record schema 和 authority，未来仅可提取无状态的 canonical helper。

## Execution Details

先拆分无法单独定位的 source-v1/result-v1 negative cases，新增 catalog 正反合同；再迁移稳定版本和组合 matrix 到 `tests/release_upgrade` 并接入 result/verifier lane。运行 Python 3.9.6 与 Python 3.14.6 的 core、historical、release-upgrade、bundle/install 与两次 evidence；确认 fixed-head CI 仍只跑 core。创建 ADR，形成 implementation commit、delivery document commit 和 canonical delivery；delivery 后不再加入实现提交。
