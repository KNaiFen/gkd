# P4 文档事实渲染与 schema 实现说明

## Internal Design

实现一个纯函数式 canonical facts renderer，输入受校验的 task/result/review/CI 对象，输出版本化 machine facts JSON 与可嵌入 Markdown 的稳定 facts 区段。trusted-main CLI 负责定位输入并写入临时或任务受管路径。

## Execution Details

复用现有 canonical/digest/schema 工具；新增 focused contracts 验证 determinism、path/capability redaction、human narrative isolation、legacy readability 与 drift fail-closed。不得修改状态机或生产安装面。
