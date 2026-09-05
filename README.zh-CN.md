# Evidence-first agent skills

把工程主张核实清楚，把关键选择交给用户，然后顺畅完成已选工作。
这五个 Codex skill 来自 BidKing、LC2 与配套数学仓
[`bidking-inference`](https://github.com/SeasonCake/bidking-inference) 的工程经验，可独立安装和修改。

| 技能 | 用途 |
| --- | --- |
| `intent-checkpoint` | 用简短原生问答澄清真正影响范围的决定，已明确的小事不反复问 |
| `architecture-survey` | 沿调用与测试找有证据的架构改进点，不把大文件直接判成问题 |
| `verify-claim` | 用同口径证据验证一个行为或性能主张 |
| `cli-contract-review` | 检查非交互执行、真实读取上限、失败分类与恢复 |
| `agent-compatibility` | 验证新代理能否从仓库说明和样例启动、检查并恢复工作 |

## 简短问答，明确下一步

```text
用 $intent-checkpoint 帮我区分本次发布修复和额外签名提案。
只把真正会改变范围的决定做成简短问答，明确的工作继续做。
```

宿主支持时优先使用原生问题卡，例如可用的 `request_user_input_async`；否则用简短文字。
原四项保持显式调用，新 `intent-checkpoint` 同时允许按任务描述自动匹配。
查看[技能正文](skills/intent-checkpoint/SKILL.md)与[八个合成正反例](skills/intent-checkpoint/references/synthetic-example.md)。

## 安装与验证

```powershell
python scripts/verify.py
```

安装和调用方法见 `INSTALL.md`。每个 skill 都链接一份 synthetic known-good/known-fail 示例，
机器可读用例矩阵位于 `examples/synthetic_cases.json`。贡献、维护、支持与变更记录分别见
`CONTRIBUTING.md`、`MAINTAINING.md`、`SUPPORT.md` 和 `CHANGELOG.md`。

上游来源和本地改造分别记录在 `UPSTREAM.md` 与每个 skill 的 `ATTRIBUTION.md`。
热修1的证据核验案例见[工程案例](docs/HOTFIX1_CLAIM_REVIEW.zh-CN.md)，项目关系见 `PROJECT_ORIGIN.md`。
若这些流程对你有帮助，欢迎 Star、提供可复现的 Issue，或提交改进 PR。

Copyright (c) 2026 SeasonCake，以 MIT License 发布。贡献采用 Developer Certificate of
Origin 1.1（提交时使用 `git commit -s`），不要求 CLA。
