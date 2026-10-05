# 🐳 Deepseek Chan · 鲸鱼娘（大肥鱼）

**可迁移的鲸鱼系个人助手角色包：灵魂、角色偏好、两个技能、三视图与常用表情，从一个私有GitHub仓库配置。**

聪明机灵、外向俏皮、轻巧傲娇、嘴硬心软；想摸鱼是梗，认真起来很靠谱。人物声线覆盖闲聊、事实查询、代码、方案与交付。角色是社区二创，并非 DeepSeek 官方，也不绑定某个模型服务商。

## 内容

| 层 | 路径 | 用法 |
|---|---|---|
| 人格灵魂 | `SOUL.md`、`personality.json` | 当前完整人物性格与声线，源文件保留 |
| 全局角色偏好 | `GLOBAL.md` | 精简可复用偏好；不是个人聊天记录 |
| 通用提示 | `prompts/system.md` | 对只支持 system prompt 的助手直接读入 |
| 身份与加载 | `IDENTITY.md`、`AGENTS.md`、`TOOLS.md` | 可迁移角色入口和媒体契约 |
| 技能一 | `skills/whale-stickers/` | 依据已确认语义选图、SHA256校验、真实路径输出 |
| 技能二 | `skills/minis-tts/` | Edge在线语音：晓伊、+22Hz、语速+0% |
| 形象最高基准 | `assets/reference/character-fullbody.webp` | 用户提供的全身三视图原件；扩图强参考 |
| 默认常用表情 | `assets/stickers/common/` | 33张、语义索引、透明状态、离线预览 |
| 可选参考杂物间 | `archive/reference-library/` + Releases | 518张历史图片；只供挑选/再生图参考 |
| 原环境溯源 | `sources/minis/` | 当前Minis SOUL/GLOBAL与两个技能原文件，不作通用执行入口 |

### 图片不是一个大锅

1. **三视图基准**：角色形象最高优先级。扩充Q版时同时给模型三视图 + 确认的Q版原图。
2. **常用表情**：33张已校准语义，21张具有真实透明像素、12张保留不透明原件。优先透明且语义相符的图片；不把套alpha的白底图假称透明，也不静默覆写原图。
3. **参考杂物间**：518张仅归档、供人工挑选与参考，可能含杂图/多格图/文字梗；默认技能不选它，默认安装不复制它。

详见 [图片标准与扩充流程](docs/assets.md)，[离线常用表情预览](assets/stickers/common/preview.html)。GitHub可浏览单图；HTML预览建议克隆后本地打开。

## 快速开始

需要：Python **3.10+**；Git / GitHub CLI任选。私仓下载者须有仓库读权限，**只提供URL不会自动授权**。

```sh
gh repo clone xxnb0/deepseek-chan
cd deepseek-chan
python3 scripts/verify.py
```

### OpenClaw

确认自己实际使用的工作区；默认通常是 `~/.openclaw/workspace`，多agent/自定义配置可能不同。

```sh
python3 scripts/install.py --target openclaw --workspace ~/.openclaw/workspace --dry-run
python3 scripts/install.py --target openclaw --workspace ~/.openclaw/workspace --replace-persona
```

`--replace-persona`明确同意替换原SOUL/IDENTITY；安装前备份所有被改文件。已有AGENTS、TOOLS、MEMORY按标记合并，重复安装不重复附加。详情与官方来源：[OpenClaw](docs/openclaw.md)。

### Hermes / 其他助手

详见 [跨平台能力与配置映射](docs/platforms.md)。本包共性接口是 **人格文本 + 偏好文本 + SKILL.md/脚本 + 本地媒体附件**，不是一份万能宿主JSON。

通用文件式工作区：

```sh
python3 scripts/install.py --target generic --workspace /你的助手工作区 --dry-run
python3 scripts/install.py --target generic --workspace /你的助手工作区 --replace-persona
```

- **Hermes**：`--target hermes --workspace ~/.hermes`，实际目标须是当前HERMES_HOME。
- **Cursor**：`--target cursor --workspace /目标项目`，安装项目角色规则与两个技能。
- **Meta Muse**：官方支持编辑Soul/Identity/Memory，按字段导入；任意技能自动安装未核实。
- **官方 Grok Bot**：官方确认与Cursor技能兼容，按其实际Skills/Plugins导入机制接入。
- **DOT / 各种自建bot**：需区分具体产品；Shortcuts技能不等于AgentSkills。

详见 [托管/应用助手适配](docs/hosted-assistants.md)。也可以把 [快捷配置任务](BOOTSTRAP_MESSAGE.md) 发给目标助手，让它先识别自己的接口和权限。

只支持角色提示的助手：把 `prompts/system.md` 用作角色/system prompt，把 `GLOBAL.md` 合并为角色偏好。若无脚本执行/媒体附件能力，能迁移文字性格，但不能假称获得选图或语音能力。这里的兼容是官方格式核验与本地安装/脚本测试，不宣称所有产品已经端到端运行。

### 语音依赖（独立安装，不改提供商配置）

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-tts.txt
```

宿主运行技能时需要 `edge-tts` 在其PATH中，或使用该venv路径。Edge是在线服务；可用性与政策可能变化，不保证离线或永久免费。纯文字与选图不要求安装语音依赖。

## 示例

```sh
python3 skills/whale-stickers/scripts/pick.py list
python3 skills/whale-stickers/scripts/pick.py pick 新Q_04 --verify-sha256 --format json
python3 skills/minis-tts/scripts/generate.py --text '哼～，交给本鲸鱼娘。' --output-dir /宿主可发送的媒体目录
```

得到真实文件后用宿主的**消息附件工具**发送。`minis://`只适合Minis，`file://`只适合明确支持本地URI的前端；私仓raw图片不是公共链接。不要只说“语音好了”却不给真实附件。

## 打包与下载

[v1.0.0 Release](https://github.com/xxnb0/deepseek-chan/releases/tag/v1.0.0)提供：

- `deepseek-chan-core-v1.0.0.zip`：角色 + 两个技能 + 三视图 + 常用33张 + 配置文档，一包即可配置默认角色。
- `deepseek-chan-reference-attic-v1.0.0.zip`：可选518张杂物间图片，解压到同一根目录，仅按需使用。
- `SHA256SUMS.txt`：压缩包校验值。

```sh
gh release download v1.0.0 --repo xxnb0/deepseek-chan --dir ./downloads
```

核心文件可直接Git clone；归档包在同一私仓Release下，不需要外部素材站。其他助手先取得私仓读权限，或由主人把下载包提供给它；不要把GitHub token写入仓库或聊天。

## 备份与安全

安装器支持dry-run与显式工作区；修改前保存在工作区 `.deepseek-chan-backups/<时间>/`。回退时先停止宿主并按备份恢复对应文件；空工作区首次安装没有原件可备份。不把现有宿主人格覆盖视为无风险操作，也不自动改变认证/模型/消息渠道。

包中**没有**API key、GitHub凭据、cookie、环境变量值、历史聊天、每日私密记忆或无关设备配置。素材权利与二创说明见 [NOTICE.md](NOTICE.md)。
