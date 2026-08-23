# GKD Runner Resource Fact Binding Implementation

## Internal Design

- recommendation 把 resource fact source 与 runner fact 视为同一容量结论的共同前提。
- current runner 是唯一可验证的 runner 候选；没有候选集合时不生成更高容量选择断言。

## Execution Details

1. 收紧 normalized facts 和 speed-first preset/runner action 的选择。
2. 添加 host、observed、unknown、runner-bound 正反例并更新 resource docs。
3. 运行版本化 verifier，交付固定 PR head 与 evidence。
