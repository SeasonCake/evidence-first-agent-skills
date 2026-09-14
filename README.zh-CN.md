# Evidence-first agent skills

把工程主张核实清楚，把关键选择交给用户，然后顺畅完成已选工作。
这七个 Codex skill 来自 BidKing、LC2 与配套数学仓
[`bidking-inference`](https://github.com/SeasonCake/bidking-inference) 的工程经验，可独立安装和修改。

| 技能 | 用途 |
| --- | --- |
| `browser-workflow` | 完成多步骤浏览器编辑，回读已保存结果，异常恢复时避免重复提交 |
| `grok-bridge` | 使用已安装运行时建立持久Grok任务、刷新规范并配置有限完成回传 |
| `intent-checkpoint` | 用简短原生问答澄清真正影响范围的决定，已明确的小事不反复问 |
| `architecture-survey` | 沿调用与测试找有证据的架构改进点，不把大文件直接判成问题 |
| `verify-claim` | 用同口径证据验证一个行为或性能主张 |
| `cli-contract-review` | 检查非交互执行、真实读取上限、失败分类与恢复 |
| `agent-compatibility` | 验证新代理能否从仓库说明和样例启动、检查并恢复工作 |

## 完整集成与指令Skill分开

[Grok ↔ Codex完整集成](integrations/grok-codex-bridge/README.md)放在`integrations/`，包含运行代码、
配置/恢复流程、兼容补丁和测试；配套Skill放在`skills/grok-bridge/`指导调用。仅复制Skill不等于
安装了provider或运行时。原生GPT保持独立路由，实验宿主范围与未测项在集成文档中明确。

原六项仍是指令/验证工作流，不把新集成的安装依赖强加给它们。

新增可选的[原生模型按钮接入](integrations/grok-codex-bridge/MODEL_PICKER.md)：在创建任务及空闲切换时，
将 Grok 模型与对应提供方配对。包含 stdio 路由器和 Windows 启动入口源码；认证、工具和历史仍由
原版 Codex 后端处理。

[68秒中文实录：BidKing 与 Codex 中的 Grok](https://www.bilibili.com/video/BV1rRYk63ER5/) ·
[English on X](https://x.com/zheng_qili666/status/2099349396895019095)

视频还展示竞价估值、结算复盘和公共数据筛选。生图使用单独安装的本地原生 Imagine 包装器，
不随此公开集成分发。各段对应的源码与运行示例见
[演示阅读路线](https://github.com/SeasonCake/bidking-inference/blob/main/docs/DEMO_GUIDE.zh-CN.md)。

## 简短问答，明确下一步

```text
用 $intent-checkpoint 帮我区分本次发布修复和额外签名提案。
只把真正会改变范围的决定做成简短问答，明确的工作继续做。
```

宿主支持时优先使用原生问题卡，例如可用的 `request_user_input_async`；否则用简短文字。
原四项保持显式调用，`intent-checkpoint`、`browser-workflow` 和 `grok-bridge` 允许按声明场景匹配。
查看[技能正文](skills/intent-checkpoint/SKILL.md)与[十二个合成正反例](skills/intent-checkpoint/references/synthetic-example.md)，
包括延迟答复、转述限制的来源，以及整体目标未完时怎样处理局部完成。

## 浏览器编辑，以保存回读收尾

```text
用 $browser-workflow 在我指定的浏览器中更新这三项说明。
价格不变，每项都核对真正保存的内容。
```

保存前核草稿、结果未知先查回执、错误导航不读成旧页面，保留指定浏览器和当前工具权限。
CLI只是条件性选择，不强行替换现有会话。查看[工作流](skills/browser-workflow/SKILL.md)、
[九个合成情境](skills/browser-workflow/references/synthetic-example.md)与
[可选AGENTS入口示例](INSTALL.md#optional-standing-route)。
技能可发现、情境检查和真实浏览器执行分别验证；不承诺原生焦点问题已修好或所有任务都更快。

[浏览器读回与录屏恢复改进](docs/BROWSER_RECORDING_REVIEW_2026-09-15.zh-CN.md)附独立假数据表单、
不可读字段处理和可选 FFmpeg 合成测试，说明为什么“读回为空”或“文件能播放”不足以判断任务结果。

## 安装与验证

```powershell
python scripts/verify.py
```

安装和调用方法见 `INSTALL.md`。每个 skill 都链接一份 synthetic known-good/known-fail 示例，
机器可读用例矩阵位于 `examples/synthetic_cases.json`。贡献、维护、支持与变更记录分别见
`CONTRIBUTING.md`、`MAINTAINING.md`、`SUPPORT.md` 和 `CHANGELOG.md`。

上游来源和本地改造分别记录在 `UPSTREAM.md` 与每个 skill 的 `ATTRIBUTION.md`。
版本尚未完成时，查看[中间态维护与分享](docs/INTERIM_MAINTENANCE.zh-CN.md)：
小范围定期检查、带日期的进展记录、证据变化合成例，以及明确的公开边界。
热修1的证据核验案例见[工程案例](docs/HOTFIX1_CLAIM_REVIEW.zh-CN.md)，项目关系见 `PROJECT_ORIGIN.md`。
若这些流程对你有帮助，欢迎 Star、提供可复现的 Issue，或提交改进 PR。

Copyright (c) 2026 SeasonCake，以 MIT License 发布。贡献采用 Developer Certificate of
Origin 1.1（提交时使用 `git commit -s`），不要求 CLA。
