# GKD-O2 Implementation

## Internal Design

O2 只整理持久上下文的事实层级：保留当前状态、授权边界和下一任务；历史版本、失败尝试、完整 digest 和清理记录引用 decisions/open-items/task records。不得改变这些历史记录的语义，也不得将 host-level recovery 配置复制到 GKD 安装面。

## Execution Details

executor 在修改前须完整阅读根 AGENTS.md、VISION.md、`.agents/` 持久记录及 O2 文档；交付时记录实际 diff、文档检查、candidate head、review/CI/acceptance 结果。发现状态事实无法判定时停止并报告 finding，不以猜测覆盖历史。
