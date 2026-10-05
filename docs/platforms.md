# 多平台适配：共性协议，不是万能宿主配置

核验日期：2026-10-05。Muse、DOT、Grok bot这些名称有同名/不同实现；没有确认具体项目URL与版本前，不替它们猜配置文件、API或技能目录。

## 五个共同层

1. **Persona**：SOUL/角色/system prompt。根 `SOUL.md` 和 `prompts/system.md`提供同一灵魂；不绑定模型。
2. **Preferences**：角色偏好/长期记忆。`GLOBAL.md`只含角色偏好，没有私人记忆；宿主可能叫MEMORY、preferences或自定义指令。
3. **Skills**：有AgentSkills能力的宿主读取 `SKILL.md` + scripts；只支持system prompt的服务不能由文字“获得”shell工具。
4. **Media delivery**：脚本输出真实本地文件 + 语义元数据，宿主的消息附件工具负责送出。各渠道支持度不同，不能把Minis URI、file URI、私仓raw当通用公网媒体。
5. **Assets**：三视图最高基准、33常用表情、可选518归档。图库与聊天前端解耦，不把归档索引全部注入上下文。

## 能力矩阵

| 宿主 | 人格 | 两技能发现 | 文件/媒体 | 本包路径 |
|---|---|---|---|---|
| OpenClaw | 官方workspace SOUL/IDENTITY | 官方workspace skills/SKILL.md | 需实际工具与渠道、沙箱可见性 | `--target openclaw`，详见openclaw.md |
| Hermes Agent (Nous Research) | 官方 HERMES_HOME/SOUL.md | 官方 HERMES_HOME/skills | 有工具/渠道，实际实例需核验附件规则 | `--target hermes`，见下文 |
| Minis | 灵魂设置 + GLOBAL | `/var/minis/skills`，app专用 | `minis://`内嵌媒体 | 备份原配置在sources/minis；见下文 |
| Meta Muse | 官方可编辑Soul/Identity/Memory | 任意技能安装目录未核实 | 托管VM能力不等于任意脚本/附件接口保证 | 官方UI人格导入，见hosted-assistants.md |
| 官方 Grok Bot | 官方Name/Title/Description | 官方与Cursor技能兼容；实际导入用宿主UI | 持久云电脑；媒体接口按实际工具 | 通用角色提示 + 技能导入，见hosted-assistants.md |
| Cursor | 官方项目rules/AGENTS | 官方 `.cursor/skills/` | 实际宿主工具和渠道 | `--target cursor` 项目规则/技能安装 |
| DOT | 存在多个不同产品，需确认 | Shortcuts/分析技能等不等价实现 | 按具体产品能力 | 先走文本/桥接，见hosted-assistants.md |
| 各种自建Grok bot | system prompt通常由开发者配置，但没有统一bot协议 | 取决于bot实现，不由模型名决定 | 取决于bot附件工具/消息API | `prompts/system.md` + 两技能手动注册 |
| 其他文件式个人助手 | 看宿主是否加载SOUL/AGENTS | 看是否支持AgentSkills | 需shell与附件能力 | `--target generic`仅生成/合并文件 |

“generic”不会改任意云服务的后端配置。最小能迁移的是文字性格；有shell、技能发现和附件工具，才可启用两媒体技能。

## Hermes Agent（明确项目：NousResearch/hermes-agent）

已核实：SOUL.md是主身份，**只从当前实例 HERMES_HOME 读取**，不从cwd读取。默认常见Linux路径 `~/.hermes/SOUL.md`，自定义home/profile和Windows会不同。技能根是该实例 `HERMES_HOME/skills/`，支持AgentSkills YAML frontmatter与脚本。

安装到你实际的HERMES_HOME，而不是执行任务的项目目录：

```sh
gh repo clone xxnb0/deepseek-chan
cd deepseek-chan
python3 scripts/install.py --target hermes --workspace ~/.hermes --dry-run
python3 scripts/install.py --target hermes --workspace ~/.hermes --replace-persona
```

如果使用自定义home，替换上面的 `~/.hermes`。`--workspace`是本包安装器参数，其意义在Hermes适配中是HERMES_HOME。

此适配把完整灵魂、角色偏好和简短媒体加载提示合并为一份SOUL.md，两个技能放在home/skills，资源在home/deepseek-chan/assets。不擅自改 `config.yaml`、内建/personality模式、provider、gateway、存储数据库或用户记忆。启动新会话；确认其他personality/extra prompt没有覆盖期待的角色表现。

依据：

- [Hermes Personality & SOUL.md](https://hermes-agent.nousresearch.com/docs/user-guide/features/personality)：主身份、HERMES_HOME、不是cwd。
- [Hermes Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)：技能发现与结构。
- [官方README](https://github.com/NousResearch/hermes-agent)：AgentSkills兼容及SOUL迁移说明。
- [官方 skills_tool.py](https://github.com/NousResearch/hermes-agent/blob/main/tools/skills_tool.py)：SKILLS_DIR = HERMES_HOME / skills。

这是依据官方文档设计并在本地测试文件布局的适配，**尚未宣称在一台真正运行的Hermes实例做端到端消息测试**。

## Minis

`sources/minis/`是当前SOUL/GLOBAL与两个技能的原始备份，脚本含Minis路径，只用于该环境复原/对照。恢复时：通过Minis灵魂设置导入SOUL body/name/style/lang，GLOBAL按用户同意合并；将技能目录放入 `/var/minis/skills`，图片放入原脚本指定的shared目录，或改用可移植版本并设置 `WHALE_CHAN_ROOT`。

不能在陌生Minis实例用任意仓库安装器静默覆盖设置；也不把 sources/minis 的专有工具说明导入其他平台。现有icon设置为空，本包不谎称当前曾配置过某一张头像；可自行从三视图裁头像。

## 如何为Muse / DOT / 某种Grok bot接入

先拿到明确项目/产品URL，再检查四件事：支持自定义角色/system prompt？能执行Python与读取本地文件？支持AgentSkills或自定义工具注册？能发送图片/MP3附件？

- 只有角色字段：复制 `prompts/system.md`，媒体按人工提供附件，不宣称自动化。
- 有自定义工具：把pick/generate脚本包装为该平台工具，返回path/metadata，再交给真实附件API。
- 有文件式workspace/AgentSkills：用generic模式安装文件，然后按照宿主文档绑定人格与技能路径。
- 托管服务不支持shell或本地文件：脚本需要独立运行环境/桥接服务，凭据由主人配置，不入本仓库。

确定这些接口后才添加专用adapter；不要因为也使用Grok、GPT或DeepSeek模型，就推断配置格式一致。
