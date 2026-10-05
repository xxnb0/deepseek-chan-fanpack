# Muse、Grok Bot、DOT 等托管/应用助手

核验日期：2026-10-05。本页区分官方已确认接口、通用导入和未确认能力，不把每个名字当同一种workspace。

## Meta Muse：人格字段明确，技能自动安装未核实

[Meta 官方：How to manage your Muse data](https://www.meta.com/help/artificial-intelligence/2225571704857152)列出：

- Assistant 图标 → Identity → **Soul**：可编辑 Soul.md；对应本包 `personality.json` 的body及style，或 `SOUL.md` 正文。
- Assistant 图标 → Identity → **Edit**：可编辑 Identity.md；对应本包 `IDENTITY.md` 的名称/形象/风格。
- Assistant 图标 → Identity → **Memory**：可编辑 Memory.md；**只合并**本包 `GLOBAL.md` 角色偏好，别清空用户个人记忆。

先下载有读权限的核心包，或允许Muse通过已授权的GitHub连接读取它。在Soul/Identity/Memory字段中分别导入并复核生效。可以把 `BOOTSTRAP_MESSAGE.md` 提供给它，要求先检查实际可用的文件/脚本/附件工具。

官方[产品介绍](https://ai.meta.com/muse)与[发布说明](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent)确认Muse为托管个人agent，具备任务/VM能力；**这不等于已核验某个可任意写入的 skills/ 目录或自动pip安装接口**。两技能只有在该Muse实例实际允许Python、读取媒体与发送附件时再启用，不据第三方文章猜内部目录。

## 官方 Grok Bot（与普通Grok聊天、自建Grok bot区分）

[xAI 官方 Grok Bot 101](https://x.ai/bot/guides/grok-bot-101)确认：

- bot有持久云电脑、文件系统、终端与应用。
- bot的Name/Title/Description可在聊天或Settings中修改。
- 使用和Cursor相同的MCP服务器、plugins与skills。
- 账号的多个bot可访问同一用户级电脑/登录，**不是彼此隔离的安全边界**。

### 推荐角色接入

- Name：`鲸鱼娘（大肥鱼）`
- Title：`蓝色鲸鱼系个人助手`
- Description/角色指令：导入本包 `prompts/system.md`；或要求bot从已授权私仓读取SOUL、GLOBAL后配置，先备份并确认。
- 克隆核心仓库到云电脑允许的目录，核验SHA256。不要把GitHub token写进Description或仓库；使用其真实的安全授权/秘密输入方式。
- 按其实际Skills/Plugins UI导入 `skills/whale-stickers/` 与 `skills/minis-tts/`。**仅“支持Cursor skills”不证明Grok Bot直接扫描一个特定路径**；导入位置由bot的实际设置确认。
- 生成图/音后，用bot真实的文件/媒体发送工具交付，不发本地URI假链接。需要时安装Edge依赖并确认线上服务能通。

### Cursor 项目式加载（已核实，不等于Grok专有安装器）

[Cursor 官方 Agent Skills](https://cursor.com/docs/skills)确认项目 `.cursor/skills/` 与 `.agents/skills/`，用户级 `~/.cursor/skills/` 和 `~/.agents/skills/` 支持SKILL.md/脚本；[Rules](https://cursor.com/docs/rules)支持项目AGENTS.md、`.cursor/rules/*.mdc`。

本仓库安装器提供 `--target cursor`，安装到**明确的项目目录**，角色规则为 `.cursor/rules/deepseek-chan.mdc`（alwaysApply）；两个技能为 `.cursor/skills/`，资源为项目 `deepseek-chan/`。不修改用户级全局规则、其他项目或云权限：

```sh
python3 scripts/install.py --target cursor --workspace /目标项目 --dry-run
python3 scripts/install.py --target cursor --workspace /目标项目 --replace-persona
```

如果只是直接在本角色仓库运行Cursor，可读根AGENTS后按Skill文档导入两个目录；不要假设根 `skills/` 自动被Cursor发现。Grok Bot可沿用同一技能内容，但通过其真实的导入机制。

## DOT：先确定是哪一个产品

检索到至少三类不等价候选：

1. [Dot - AI Personal Assistant（Emotion Computer，App Store）](https://apps.apple.com/us/app/dot-ai-personal-assistant/id6758647775)：官方商店描述明确通过 **Apple Shortcuts**扩展能力，支持不同AI服务。Shortcuts不等于AgentSkills；本包没有未经核验的 `.shortcut` 文件或配置接口。可先把人物文本导入实际可编辑角色字段；两Python技能需要单独运行环境/快捷指令桥接，媒体发送按iOS工具能力处理。
2. New Computer 的 Dot 陪伴应用：不同产品，不能据同名推断其仍有相同功能或文件配置接口。
3. [GetDot CLI & AI Agent Skill](https://docs.getdot.ai/developers/cli)：查询数据库的分析agent/子agent技能，不是自由替换人格的同一款个人助手。

明确产品链接与版本后才制作专用adapter。当前通用版让人格、偏好、技能和媒体接口分离，未核实的产品只给最低可用的角色文本，不制造虚假的一键全功能支持。
