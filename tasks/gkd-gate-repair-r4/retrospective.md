# GKD-GATE-REPAIR-R4 Retrospective

## Finding

GKD executor 的实际 wrapper 解释器可为 macOS Python 3.9.6。payload 使用 Python 3.10 的 `zip(strict=True)` 却未声明版本门槛，也没有保留原始异常；顶层把它误报为 `FILESYSTEM_ERROR`。

## Consequence

不能通过指向 trusted main 的 Python 3.14 或要求 executor 临时调整 PATH 解决，因为后续自动 executor 仍会遇到相同故障。兼容性是 core workflow 前置条件。

## R5 Boundary

R5 先将所有必要 strict pairing 改为标准库 Python 3.9 可运行的显式长度/顺序校验，保持 fail-closed 语义；随后在同一任务完成 revision/refresh/fixed-tree sidecar/actual artifact binding。

