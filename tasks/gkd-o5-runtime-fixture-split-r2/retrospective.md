# GKD O5 Runtime Fixture Split R2 Retrospective

## 结果

O5 已把测试与 release verification 输入从 core runtime 安装面拆出，同时保留原内容、schema、release traceability 和固定树验证能力。默认安装不再携带四个 fixture，显式输入仍可独立复现、校验和追溯。

## 经验

- 测试输入需要成为 manifest/lock 的一等声明面；仅从 payload 删除文件会丢失 mode、size、digest 与消费者之间的可验证关系。
- 安装面和验证输入面必须分别 fail closed：core install 拒绝 fixture 泄漏，`verify-input` 拒绝缺失、篡改和隐式安装路径回退。
- automatic executor 的路径交接仍然脆弱。R2 使用短 candidate/runtime 路径，并在 claim 后显式转交完整 execution context，才避免了 attempt 0/R1 的 pre-claim 与 identity drift。
- CI monitor 的 policy 参数必须始终是 checkout-relative `.gkd/policy.json`。绝对路径错误属于 terminal attempt，需保留失败事实并启用全新 acceptor，不能在同一 monitor attempt 重试。
- accepted candidate 与 squash merge 只有 tree 一致，不要求 commit ancestry；清理前应独立比较 tree SHA。

## 后续

从 merge `03524c0070bb3b13b5417239cdad37b21922c278` 的 fresh development bundle 建立 O6 默认角色与 optional pack 拆分任务。
