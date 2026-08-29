# GKD Gate Repair R1 Implementation

## Internal Design

在现有 task-state 单一 writer 和事务 CAS 之上加入最小持久逻辑顺序，保证跨进程事件不依赖机器 wall-clock 单调性；将 planning 文档实际 digest 刷新纳入受控 transition，并让 delivery 读取、规范化和验证预提交 result manifest 后再创建最终状态。保留旧字段和既有 phase 矩阵，所有新绑定都进入 schema、model validator、packaging expected-set 和 acceptance/rework 的同一事实链，且所有修复在最终 delivery 前完成。

## Execution Details

executor 必须先建立 task-core、runtime-bridge、rework、结果消费者和 packaging expected-set 的基线，定位所有 task-state 写入、bundle manifest/lock 和 delivery manifest 生成入口；先完成全部代码、schema、测试和 bundle digest，再运行 trusted-main 可复核的最小合同与 mutation tests。交付文档必须列出逻辑顺序兼容策略、planning refresh 命令/边界、manifest canonical 格式、最终 candidate bundle digest、固定 head、测试摘要和清理事实；delivery coordination commit 后不得再产生任何修改，不得修改本任务之外的规划或旧 O4 状态。
