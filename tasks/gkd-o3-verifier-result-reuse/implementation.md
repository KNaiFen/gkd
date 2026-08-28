# GKD-O3 Implementation

## Internal Design

canonical runner 负责一次行为测试发现/执行并写出固定结果；scope/evidence runner 通过受信的显式输入消费结果，仅执行各自边界快照和校验。结果必须绑定完整 base/head、scope/test ID、环境摘要与 digest，任何缺失、篡改或漂移均快速失败。不得通过静默缓存、隐式全局状态或宽泛回退隐藏测试失败。

## Execution Details

executor 修改前须完整阅读根规则、VISION、持久记录和 O3 文档，先固定当前测试计数和 scope 列表，再逐步实现。交付需记录一次行为执行与结果复用证据、双运行 digest、candidate bundle digest、CI/acceptance 事实；不修改 watcher、fixture、optional pack、生产或 AIO。
