# 验收与收尾：GKD-R2 发布 L3 宿主事实合同

## 最终结果

- 结果：完成
- 功能 PR：[KNaiFen/gkd#26](https://github.com/KNaiFen/gkd/pull/26)
- 被验收 head：`28387943cec3492c86d0f283d6207b008b63db99`
- merge commit：`dd7ec7a9d0b81acffc2730236a29f8fad128d5a9`
- 候选与 merge tree：完全一致
- 必需 CI：`GKD Verify` 在 fixed head 成功；policy digest：
  `d77e68152843dcc1f470d88c76fe8c249ef803854048f4a9d42ed5cc92cd54c2`
- 日期：2026-08-23

## 验收结论

- R2 将不可验证的 fresh-executor L3 轨迹替换为 schema v3 trusted-main release
  evaluation，且记录只包含 release source、candidate record、traceability 与 no-write
  boundary 的可核验 binding。
- 旧 L3 形状、source/candidate/traceability 替换、write-boundary drift 与 L4/asset
  替换都由 focused mutation contracts 拒绝。
- `scripts/gkd-verify --base-sha d5f1eef459eb1598e48c9d61135d9ec7a6b10e48` 通过
  `419/419`；两个不相交临时根产生相同的 15 项 release evidence。
- isolated install、Release asset redownload 和 asset-local install/verify 都返回
  `0.1.2`、103 files、bundle digest
  `83b0063fe1f59fa6843acbaa26f70de9e02a47430c1f6bc3a72a4d0204dffc28`。

## Bootstrap Exception

R2 修复的是当前已安装 `v0.1.1` 无法自托管验证的新 release L3 合同。任务状态因此
保留为 machine-generated `planning / revision 3`，没有 claim、activation、receipt 或
delivery。普通 `gkd-task accept` 要求这些不存在且禁止补造的 lifecycle facts，不能被
用于本任务；trusted main 按 task requirements 记录的 manual bootstrap exception 完成
独立 fixed-head review、policy monitor 与 exact merge，没有伪造普通 acceptance。

## 发布门与 Promotion

- Release candidate record digest：`0978cc264333726d6094afbbb4fdde5635a3598edbb6b5b5f7fabe96bddb1b57`
- L3 trusted-main record digest：`108e82afc80af294b0eb055549a8fcb7b73b81124691deea3e35c5cab5215847`
- L4 sandbox PR：[KNaiFen/gkd-sandbox#5](https://github.com/KNaiFen/gkd-sandbox/pull/5)，
  fixed head：`3c594ca2a5b5ed5a1e8106c6b367b214db6a5b7d`，`GKD Canary` 成功。
- L4 request/observed digest：
  `8e6a0ff8095ecad35fe1eadc1a97ac15c9e5c2f5c204b6fad4fdac0cde2f9d19` /
  `5780eabd3bd9fb94ef01d46f94a03e4135f86bc0bebf11b15dba94597e983ba3`。
- Final record/provenance digest：
  `f303ffbb1752e7173e73e4eb6d25e600a77218934a00649ba5b01b38d72504b2` /
  `852fb10891a2c857325bb8654d684e8639006b05cf76660e3ea448f6b4865652`。
- Tag/Release：[`v0.1.2`](https://github.com/KNaiFen/gkd/releases/tag/v0.1.2) 精确指向
  merge SHA；asset `gkd-0.1.2-final-dd7ec7a.tar.gz` SHA-256 为
  `2289f4cbe2b865931bb7e60cf222df538ebe7bcbead7891937cc664bb40476b9`。

## 后续与清理

- 生产安装、AIO 修改和其余 GitHub 设置不属于 R2，均未在本任务写入。
- R2 worktree、task branch、sandbox canary branch/PR 与临时验证根将在本 main 收尾提交
  推送后清理；发布 tag 和 Release 保留。
- 后续只能从已发布 asset 进行 isolated project restage，再开始独立的 AIO adoption
  inventory/mapping；不得 pin 未发布 canonical source。
