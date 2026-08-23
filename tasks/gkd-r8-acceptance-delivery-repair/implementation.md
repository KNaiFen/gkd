# GKD Acceptance Adapter And Delivery Repair Implementation

## Internal Design

新增窄 adapter 命令并修正 executor Skill 的 delivery CAS 示例；core 保持 authorization、snapshot 和 final state writer 职责。

## Execution Details

executor 从注册 worktree 实现、验证、提交、推送、CI 和 canonical delivery；trusted main 仅验收和合并。
