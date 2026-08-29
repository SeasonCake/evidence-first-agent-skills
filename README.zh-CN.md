# Evidence-first agent skills

本仓包含四个显式调用的小 skill：只读架构调查、单一主张验证、CLI 合同复核与新代理兼容性检查。
它们由 BidKing 私有计算器项目及其公开数学配套仓
[`bidking-inference`](https://github.com/SeasonCake/bidking-inference) 的工程经验抽象而来，覆盖证据分级、
发布连续性、CLI 合同、UI 验证、交接恢复与 fresh-clone 真相核验。仓内不含私有源码、客户数据、
事故原始记录、凭据或生产拓扑；详见 `PROJECT_ORIGIN.md`。

```powershell
python scripts/verify.py
```

上游来源和本地改造分别记录在 `UPSTREAM.md` 与每个 skill 的 `ATTRIBUTION.md`。

Copyright (c) 2026 SeasonCake，以 MIT License 发布。贡献采用 Developer Certificate of
Origin 1.1（提交时使用 `git commit -s`），不要求 CLA。
