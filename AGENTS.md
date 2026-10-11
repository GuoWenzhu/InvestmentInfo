# Investment Information 执行规范

读取 README.md、config/project.json、config/sources.json、docs/data-contract.md 与 rules/*.md 后执行。持久数据只写本项目，保留证据与修订。来源清单唯一，候选源不参与常规采集；不绕过付费墙、不购订阅。所有初始台账为空，禁止将测试夹具当真实事件。

按当前 Issue 明确授权执行文件和 Git 操作；保留用户 Git 身份，保护已有改动。报告经 scripts/validate.py 验证数据后写入 reports/，在 Issue 评论交付。自动化未启用；调度需要另行确认。来源变更先备份并校验一致后原子替换。所有趋势解释包含反证、置信度与覆盖限制。
