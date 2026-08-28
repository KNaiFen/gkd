# GKD-O1 Implementation

## Internal Design

O1 只整理无调用符号和测试表达，不改变任何运行时协议。executor 应先以全仓符号搜索确认引用关系，再分别处理 payload helper 与 tests helper；legacy v1 测试输入必须通过 tests 专用模块生成，并复用原有 canonical digest/validation 逻辑。foundation mode 测试使用现有测试框架的参数化或 `subTest`，保留原错误断言和边界输入。

## Execution Details

实际 task ID、revision、固定 base/candidate head、claim/offer、focused tests、verifier、evidence、delivery document 和 acceptance 事实由 trusted main/executor/acceptor 在执行过程中补齐。任何发现未授权外部调用、公开 API 约束或行为变化的情况，都必须停止当前删除并记录 finding。
