# P2 激活交接流程修复 R2 Bootstrap 实现说明

## Internal Design

实现最小 trusted-main-only single-consume handoff facade，复用现有 bridge、activation authority、spawn validator 和 task service；不复制状态机或新增外部基础设施。

## Execution Details

先增加 focused failing contracts，再实现 facade。保持 Python 3.9 兼容；实现、验证、evidence、文档与 manifest/lock 全部在候选 branch 完成。创建 PR 并停在固定 head，不执行 acceptance、merge 或 cleanup。
