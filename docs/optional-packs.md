# Optional Packs

GKD 的默认 core 安装只包含 task、role、local verify、fixed-head CI、acceptance 和 release 闭环。`gkd_executor` 默认只加载 `gkd-execute`、`gkd-local-verify` 和 `gkd-ci-monitor`；`gkd-main` 与 `gkd-accept` 继续保留在既有 trusted role 边界。

`ci-advice` 包含资源分类、CI recommendation、scanner、专用 schema 和 `gkd-optimize-ci` Skill。`review-remediation` 包含 review core、adapter、remediation、专用 schema/input 和 `gkd-review-remediation` Skill。两个 pack 都只接受声明名称，不接受自由路径。

在隔离安装中按需管理 pack：

```sh
gkd-bundle pack-stage --source-root canonical --temporary-root <root> --target <target> --pack ci-advice
gkd-bundle pack-verify --temporary-root <root> --target <target> --pack ci-advice
gkd-bundle pack-remove --temporary-root <root> --target <target> --pack ci-advice
```

`gkd-role context`、`project-stage` 和 `project-verify` 通过可重复的 `--pack` 选择已安装 pack。没有 `--pack` 时保持 core 默认。project inventory 绑定 pack 名称、pack digest、Skill digest 和全部受管文件；选择、文件、mode、内容或 inventory 漂移都会拒绝。

验证 lane 为 `optional-ci-advice`、`optional-review-remediation` 和组合的 `optional-packs`。旧 schema v1 full install 继续可读；新 schema v2 的 pack 声明、lock 和默认 core 安装严格绑定，不把旧格式静默解释为可选分层。
