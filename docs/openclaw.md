# OpenClaw 适配（文件式工作区）

这是供需要旧文件布局的用户参考的兼容入口。实际目录以宿主设置为准。

## 已核实的加载契约

- 默认工作区 `~/.openclaw/workspace`，可由配置/profile/state directory改变；多agent各自有工作区。先确认真实路径，不把默认路径当绝对保证。
- 工作区 `SOUL.md` 是persona/tone，`IDENTITY.md`是身份，`AGENTS.md`是行为/加载约定，`TOOLS.md`是本地工具笔记。
- `MEMORY.md`是可选长期记忆；默认只在主私有会话加载，不能依靠它在所有群聊/子会话都生效。本包把核心声线留在SOUL，MEMORY只合并角色偏好。
- 工作区 `skills/<name>/SKILL.md`支持AgentSkills格式（至少name、description frontmatter）和辅助脚本。这两个技能不会自动安装TTS运行依赖。
- workspace是默认cwd，不等于硬沙箱；启用sandbox时可见目录、Python、edge-tts和媒体路径需在沙箱内实际可用。

## 安装

先确认能读取仓库与所需资源，在工作区**之外**克隆本包：

```sh
gh repo clone xxnb0/deepseek-chan-fanpack
cd deepseek-chan-fanpack
python3 scripts/verify.py
python3 scripts/install.py --target openclaw --workspace ~/.openclaw/workspace --dry-run
```

审核计划后执行：

```sh
python3 scripts/install.py --target openclaw --workspace ~/.openclaw/workspace --replace-persona
```

`--replace-persona`是本仓库安装器参数，不是OpenClaw的CLI。它明确同意替换SOUL/IDENTITY，先备份被改文件；AGENTS、TOOLS、MEMORY按标记合并，重复执行不重复追加角色块。配置/provider认证/个人USER.md/历史记忆不导入，也不擦掉宿主约定。

布局：

```text
<workspace>/
  SOUL.md                 # 当前鲸鱼娘灵魂
  IDENTITY.md             # 身份
  AGENTS.md               # 原有内容 + 角色加载块
  TOOLS.md                # 原有内容 + 媒体工具块
  MEMORY.md               # 原有内容 + 角色偏好块
  skills/whale-stickers/
  skills/minis-tts/
  deepseek-chan/assets/    # 三视图与常用表情
```

装好后开启新会话，检查实际技能发现状态；媒体用宿主实际支持的消息工具发送本地文件，而不是复用Minis URI。宿主缺附件能力时只迁移文字角色，缺网络/Python/edge-tts时不假称TTS可用。

## 官方依据

- [Agent workspace](https://docs.openclaw.ai/concepts/agent-workspace)：默认目录、注入文件、MEMORY私有主会话加载、非硬沙箱。
- [Skills](https://docs.openclaw.ai/tools/skills)：workspace技能发现、SKILL.md格式与AgentSkills。
- [Sandboxing](https://docs.openclaw.ai/gateway/sandboxing)：运行环境/工作区可见性。
- [System prompt](https://docs.openclaw.ai/concepts/system-prompt)：系统上下文与workspace注入。

这是一套角色工作区内容，不建议将整个Minis系统提示（包含Android专用命令）复制到OpenClaw，更不要搬运API keys/cookies。
