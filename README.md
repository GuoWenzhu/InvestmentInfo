# Investment Information

创业与投资情报项目：用可追溯融资事件观察投资机构关注的领域，并结合产品、客户证据和反证解释变化。项目已初始化，尚无真实融资事件或正式日报。

## 启动方式

Python 3.10+，标准库即可运行：

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/validate.py --events data/events.jsonl
```

校验工具检查配置、事件数据契约、证据 URL 和冲突候选；不会自动合并融资或访问互联网。事件由智能体按原文核验后录入。首次仅手动运行，时区 Asia/Shanghai、回看 48 小时、报告最多 10 条，不足不凑数。

## 目录

- `config/`：项目参数、唯一来源清单、事件 JSON Schema。
- `data/`：公司、事件、机构、事件投资关系与证据 JSONL；初始为空。
- `state/`：跨日报 URL 台账、当日发布状态、来源健康与维护日志。
- `rules/`：智能体说明及五个规则模块。
- `templates/`：日报、周报、月报和手动运行 Issue 模板。
- `scripts/validate.py`：本地校验和疑似重复检查；`tests/` 是合成验收用例。
- `docs/design.md`：TECH-5 完整来源与分析设计；`docs/data-contract.md`：字段约束；`docs/implementation.md`：落地状态。

## 边界

只使用清单已启用入口；YC 与 36氪仍待浏览器正文接入验证。按事件核验公司官网允许扩展证据，但需确认官方域名。候选源不进入日常采集，免费可见内容与付费墙分开，未授权订阅或对外发布。

目录收录、机构观点、社区热度都不自动生成融资事件。没有金额用 null；股权、债务、混合、并购、基金募集分开。趋势需报告样本覆盖、披露率、集中度和反证，不能把单笔巨额融资视为赛道普遍增长。

来源修改前备份并校验字节一致，再原子替换。连续 3 次真实失败且替代入口失败才转观察；连续 30 个成功采集日无产出才降级；恢复需连续 2 次可达。网络失败、解析失败、付费墙与零产出分别记录。

后续手动任务参见 `templates/manual-issue.md`。两周试运行和真实事件验收尚未执行；验证达标后再单独确认 Autopilot。
