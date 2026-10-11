# 数据契约 v1

`config/event.schema.json` 是事件完整结构定义；`scripts/validate.py` 实现离线严格结构检查及日期/证据/金额联动约束。

## 实体表

- companies.jsonl：company_id、name、aliases、official_domain、sector、business_scenario、registered_country、hq_country、operating_regions。
- investors.jsonl：investor_id、name、aliases、parent_id（不能确认时 null）。
- event-investors.jsonl：event_id、investor_id、role（lead/co_lead/participant/undisclosed）、investment_amount、currency、evidence_ids。
- evidence.jsonl：evidence_id、event_id、source_id、url、canonical_url、publisher、published_at、collected_at、tier、evidence_type、field_claims、confidence、conflicts、revision。

初期事件内的 investors 与 evidence_urls 是报告校验所需的引用投影；实体和证据表尚未接入自动外键校验，录入时须人工复核一致。这些表只存公开业务信息，不录入个人联系方式或凭证。

## 事件规则

金额未披露时 amount=null；其他状态金额须为非负数。range 的 amount 仅在明确约定为下界时可用，区间上界与原文保存在 evidence.field_claims，统计不得把它当精确金额。约数保留原文；currency 只用三位大写代码，未知用 UNK，不虚构换算。

financing_date 与 disclosed_date 分开：前者未知为 null，披露日期使用实际原文日期。日期不够精确时使用 YYYY 或 YYYY-MM 并标记精度，不填猜测的某天。collected_at 必须为有时区的 ISO 时间。历史回填设置 historical_backfill=true。

每轮融资与基金募集分开；混合融资没有分项时不重复生成股权与债务总额。融资额、估值和累计金额不能混用；默认不录入估值到 amount。

规范化 URL 只去明确跟踪参数，保留语义参数。公司+标准轮次+事件类型仅产生疑似重复组，工具永不自动吞并扩展轮。event_id 重复报错，event_group_id 用于人工关联追加/分批交割。目录新增不能写入事件表。

报告主口径按披露日；高/中置信事件进入主样本，低置信只观察。日报 runs 记录 date、issue_id、event_ids、revision、status；同日重跑先复用 issue_id、只报告新增证据和更正。
