# 平台适配速查（2026-10-06）

核心始终是平台中立的。这里是**有来源的映射说明和待导入材料**，不是已在所有平台安装成功的回执。默认不更改任何宿主设置；导出脚本只创建新的交付目录。

| 宿主 | 人格放哪里 | 外观／声音路线 | 本包交付与验证边界 |
| --- | --- | --- | --- |
| Muse | 目标实例真实支持的角色说明／等价载体，先发现再映射 | 参考角色图交给原生头像能力；实时声音优先原生调节 | 人格提示、参考图、同文试听说明；Edge 文件合成有历史云端证据，实时替换未证实 |
| ChatGPT / Dot | 获准的当前会话或持久角色说明，不能假定任意仓库文件会自动注入 | Dot 资料页支持选择角色／宠物，也能生成宠物 | 准备提示与宠物规范；必须读当前账户的实际接口，未做账户级头像激活 |
| Hermes | 当前实例的 `$HERMES_HOME/SOUL.md`；默认 `~/.hermes/SOUL.md` | 终端 skin 与对话人格是两条设置；渠道媒体单独核验 | 导出 SOUL 候选，不覆盖已有人格；未安装 Hermes 验收 |
| OpenClaw | 实际 agent workspace 的 SOUL / IDENTITY；工作约定归 AGENTS | 渠道头像与音频能力分别处理 | 导出 SOUL、IDENTITY 和可人工合并的 Tools 片段，不整份覆盖 AGENTS |
| 支持 Character Card v2 的角色前端 | 导入 JSON 角色卡 | 头像、TTS 由前端另配 | 提供标准字段的 JSON；格式测试通过不等于所有前端导入已验证 |
| 其他支持提示字段的 AI | 独立 system prompt 或会话模式 | 静态图／附件能力优先 | 使用通用导出即可；没有证据时不新增平台专属后端 |

## Muse：不要把「选声音」等同于「换 TTS 服务」

[Meta 的 Connect 公告](https://about.fb.com/ja/news/2026/09/meta-connect-2026-everything-we-announced/) 说明实时声线可通过描述调整快慢和口音。[Muse Realtime Avatar 技术说明](https://research.meta.ai/blog/bringing-your-muse-to-life) 则明确声音与头像消费同一语音令牌流，并以参考媒体保持形象。由此，本包优先给它一张清晰参考图和表达方向，**不先替 Muse 做整套逐帧口型动画**。研究演示能力不保证每个账户均开放对应入口。

原生语音调整先从语音会话中的自然语言要求开始：改变语速或口音，也可尝试要求表达更轻松、解释时停顿更清楚，再比较实际听到的变化。角色音色描述可以尝试，但**基础音色可调范围、中文效果、跨会话持久化和专用声音设计入口均未确认**。未取得第三方 TTS 或上传音频接管 Muse 原生实时声音的公开配置契约，也不能据此断言它仅支持内置声线。

这也解释了为什么外部 MP3 成功不能证明实时声线已经替换。具体的两条声音路径、试听短句和旧故障的真实边界见 [TTS 排障](tts-troubleshooting.md)。本轮没有更改 Muse 已有头像或声线偏好。

## ChatGPT / Dot：人格、宠物与授权分开

[OpenAI 官方上手说明](https://help.openai.com/en/articles/20001530-getting-started-with-your-dot) 的资料编辑入口可改名字和头像，并支持宠物选择／生成；没有说宠物文件天然携带这份助手人格。先应用文字，再准备外观，最后核对资料页真实生效。名字改变、候选图生成、宠物导入、人格持久化是四个不同验收项。

普通 ChatGPT 对话、Codex 桌面宠物和 Dot 不应被视为同一个文件系统或自动共用安装路径。云端已有工作能力足以处理本包，不需要打开用户关机的电脑。公开 Codex atlas 可以做一种资源导出，但不代表 Dot 当前接口无条件接受该格式；见 [宠物适配](pets.md)。

## Hermes：避免写对了文件名，却写错位置

[Hermes 官方说明](https://hermes-agent.nousresearch.com/docs/user-guide/features/personality/) 指定只从实例的 `HERMES_HOME` 取 SOUL，不从当前项目目录寻找同名文件。`/personality` 是会话覆盖层，`AGENTS.md` 是项目工作约定，不能拿角色包根目录 AGENTS 覆盖全局行为。导出后由实际宿主确认实例 home 和现有内容，备份并只做获准合并；身份含义可合并到 SOUL，不假定 Hermes 会自动读取 IDENTITY 文件。

项目上下文只选择一种类型：`.hermes.md` → `AGENTS.override.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`；被选中的 AGENTS 可按目录层级合并。因此新增 AGENTS 不一定改变实际载入的规则。SOUL 或项目上下文修改后，应开启**新会话**核验加载与表现，而不只是给原会话再发一条消息。[上下文发现](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files/) · [文件职责与刷新时机](https://hermes-agent.nousresearch.com/docs/user-guide/which-file-does-what)

## OpenClaw：按当前工作区，而不是旧模板机械复制

[OpenClaw 工作区文档](https://docs.openclaw.ai/concepts/agent-workspace) 中 SOUL 管语气与边界，IDENTITY 管名称与身份；当前文档将本地工具说明放进 AGENTS 的 `## Tools` 节，并说明 TOOLS.md 已退役。旧实例须先检查自己的版本与读取行为，不删除它仍使用的文件。本包根目录 TOOLS.md 是可移植资料，不是要求目标平台照搬的布局。

执行目录 `cwd` 可以与人格 workspace 分开；项目 AGENTS 可以追加，但执行目录中的 SOUL／IDENTITY 不会自动替换主 agent 身份。`skipBootstrap` 只控制文件自动创建，不关闭已有文件注入；若文件已保存而角色未生效，还要核对实际 runtime 的上下文注入设置。[提示拼装](https://docs.openclaw.ai/concepts/system-prompt) · [工作区与注入配置](https://docs.openclaw.ai/gateway/config-agents/workspace-and-bootstrap)

界面与渠道显示身份单独验收：官方启动流程同时维护人格文件和 `openclaw agents set-identity` 对应的显示配置，只改 IDENTITY 正文不能证明所有名称与头像已经同步。[身份启动说明](https://docs.openclaw.ai/start/bootstrapping)

`USER.md`、MEMORY、凭据和权限均不属于角色包。导出的 `AGENTS.fragment.md` 只是一段可审阅的角色／媒体约定，不是全局文件替代品。

## 额外覆盖的价值排序

先保证任意提示字段都能使用的轻量文本，再提供 [Character Card v2](https://github.com/malfoyslastname/character-card-spec-v2) 的 JSON 交换格式。桌宠只对已知 atlas 协议制作，实时 avatar 走原生能力。无需为每个聊天软件建立一套重复人格、固定目录与 TTS 代理。

导出命令见 [导出说明](export.md)。所有新目标先在独立目录生成，再由宿主检查差异并应用；「文件存在」不是「已激活」。
