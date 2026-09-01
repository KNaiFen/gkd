# P3 交付、CI、验收与返工外观实现说明

## Internal Design

实现前先锁定 requirements/plan 的 digest 与当前 trusted main；只修改 P3 facade、必要的 schema/adapter/test 和生成式 manifest/lock。实现必须复用已有单 writer、CAS、fixed-head 与 policy boundary，不新增 daemon、IPC、签名或生产写入口。

## Execution Details

交付物包括实现代码、focused contracts、canonical bundle/lock、双解释器验证结果和 delivery 文档。所有机器事实由 trusted main/CLI 生成；文档中的人类解释不得成为 acceptance 的事实来源。
