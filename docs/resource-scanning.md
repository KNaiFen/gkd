# Resource And Scanner Layer

M3-B 为通用 CI 工作流提供两组机器接口：资源/产物分类与固定范围 scanner。接口只消费调用者明确提供的事实，不读取仓库外文件、环境变量或凭据。

## 产物与资源

`gkd_ci.resources.classify_artifacts` 将声明分类为 `zero`、`bounded` 或 `build-or-unknown`。没有可复核上界的构建始终是 `build-or-unknown` 并阻塞；事后清理不会改变峰值磁盘门禁。默认 preset 是 `resource-constrained`。`standard` 和 `high-capacity` 只有在资源事实完整且标记为已验证时才可选择。

三个 preset 只表达通用边界，不绑定某个仓库、runner、机器或付费服务。候选输出包含峰值预算、结果原因和 preset digest，便于固定事实复核。

## Facts And Recommendations

`gkd_ci.recommendations.parse_ci_facts` 接受 visibility、runner、policy、billing 和 resource 五类显式事实。`recommend_ci` 支持 `speed-first`、`balanced` 与 `cost-aware` 目标。非保守 preset 只接受 `source=runner`、完整且已验证的资源事实，并且只能选择当前已验证 runner 声明且由这些资源支持的容量。host、observed 和 unknown 资源事实始终只描述各自来源，不能证明云端 runner 容量；未提供 runner 候选集合时，recommendation 只保留当前 runner，不会声明可选择更高容量或更低价格的 runner。价格只有在来源、币种、数值和检查时刻均存在且 `verified` 为 true 时才进入推荐；其他情况输出 `unverified`，不会声称价格或成本。

## Fixed Scanner

`gkd_ci.scanner` 只接受 `diff`、`pull-request` 和 `artifact` 三种 surface。每种 surface 有固定输入形状和大小上限，路径只能是相对 surface 路径。输出只保留规则、行号、相对路径和 `full-value` 脱敏标记，不保留匹配文本。发现 credential、private key 或 credential assignment 时结果为 `terminal`，调用方必须停止后续动作。

CLI `gkd-resource-scanner` 提供 `classify`、`recommend` 和 `scan` 子命令；输入 JSON 使用 `--input` 明确传入，输出为单个 canonical JSON 对象。
