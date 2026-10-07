# 宠物、多动作图与通用性

结论：**值得为桌宠单独准备真正的多动作素材；不值得假设一张 atlas 可直接覆盖所有平台。** 角色外观共用三视图，文件格式按宿主明确契约导出，人格与声音保持独立。

## 当前证据

[Dot 官方帮助](https://help.openai.com/en/articles/20001530-getting-started-with-your-dot) 明确可选或生成宠物。[OpenAI hatch-pet 的公开动画行说明](https://raw.githubusercontent.com/openai/skills/main/skills/.curated/hatch-pet/references/animation-rows.md) 给出8列9行、单元192×208的 Codex 参考布局，共1536×1872；九种状态合计57帧，剩余15格必须透明。

[社区维护的 hatch-pet 变体](https://github.com/cjahv/codex-AGENTS/blob/main/skills/hatch-pet/SKILL.md) 还出现11行及额外视线的约定。本次恢复的成品另有实际 Pets MCP 的 v1／v2 只读预检回执，两版均通过结构预检。这证明文件满足当时工具接受的对应协议，不证明所有 Dot／Codex 安装都支持两版。公开 Web 宠物上传说明使用1536×1872的九行图；只有目标入口明确支持 v2 时，才选择1536×2288的十一行图和对应元数据。

已有 [Petty](https://github.com/LeslieLeung/petty) 和 [Clawdex](https://github.com/danielkempe/clawdex/blob/main/skill/hatch-pet/SKILL.md) 等第三方复用入口，但这里只做文档级兼容性判断，没有安装或端到端验收。图片的可移植性高于宿主安装协议的可移植性。

Muse 的[原生实时头像](https://research.meta.ai/blog/bringing-your-muse-to-life) 使用参考媒体与语音令牌同步生成，不依赖本包提供桌宠格子图。不要为它额外维护同一套帧动画或承诺外部 MP3 能驱动原生口型。

## 本轮真正交付了什么

[atlas-profile.json](../assets/pet/atlas-profile.json) 是可机读协议；[generation-brief.md](../assets/pet/generation-brief.md) 是对应角色的逐状态简报；`scripts/pet_asset.py` 可对符合九行协议的真实候选图校验、无损转码并打包，同时生成本地状态预览页面。工具不会生成缺少的动作，也不安装到任何平台。

前次 PR #7 合并时没有找回实际 atlas，因此当时只交付规范和工具。后续恢复已找回图片、动作预览、制作记录与预检回执，并重新核对文件字节和视觉检查结果。现在可直接下载 [成品动作包](../assets/pets/chatgpt/README.md)：

| 版本 | 图集与元数据 | 实际内容 |
| --- | --- | --- |
| v1 | [spritesheet.png](../assets/pets/chatgpt/v1/spritesheet.png) · [pet.json](../assets/pets/chatgpt/v1/pet.json) | 1536×1872，RGBA，九种状态共57个有效帧 |
| v2 | [spritesheet.png](../assets/pets/chatgpt/v2/spritesheet.png) · [pet.json](../assets/pets/chatgpt/v2/pet.json) | 1536×2288，RGBA，相同九种状态，另加16个朝向帧 |

九种状态依次为待机、向右跑、向左跑、挥手、跳跃、失败、等待、工作／思考、审阅；每行有效帧数为 `6,8,8,4,5,8,6,6,6`。`running` 是工作／思考状态，与两个移动状态分开。左右跑分别制作，v1 为 v2 前九行的逐像素无缩放裁切；两版各有15个透明空格。

[九状态动态预览](../assets/pets/chatgpt/previews/all-states.gif) · [逐动作 GIF](../assets/pets/chatgpt/previews/states/) · [十六方向预览](../assets/pets/chatgpt/previews/look-loop.gif) · [制作与来源记录](../assets/pets/chatgpt/production.json)

**验收范围：**两版在2026-10-06通过 Pets MCP 只读预检，结构、透明度与帧内容检查通过，预览与源图对应关系有哈希记录。四个正方向通过盲审；若干中间角度与方向衔接保留已审阅警告，247.5° 的垂直分量仍有歧义，补充独立审查对67.5°／112.5°也记录了歧义。详见 [清单](../assets/pets/chatgpt/manifest.json)、[复检摘要](../assets/pets/chatgpt/qa/reinspection-20261006/summary.json) 与 [预览来源](../assets/pets/chatgpt/qa/preview-provenance.json)。MP4 未单独逐帧解码验收。

没有进行 GUI 导入、运行时事件播放或 Dot 绑定，也没有创建／切换用户宠物、改动人格或账户配置。上传时使用对应版本的 `spritesheet.png`，不要上传预览 GIF 或四宫格。图像许可及衍生署名见 [NOTICE](../assets/pets/chatgpt/NOTICE.md)。

## 使用工具

可选图像校验依赖单独列在 `requirements-media.txt`，不影响纯文字使用。应在获准的新隔离环境安装该依赖。

```sh
python3 scripts/pet_asset.py --input assets/pets/chatgpt/v1/spritesheet.png
python3 scripts/pet_asset.py --input /实际候选图.png --output-dir output/whale-pet --visual-review-confirmed
```

此工具仍只处理九行 v1，不把 v2 误报为九行合格；v2 的验收记录位于成品目录。第二条只应在人工真正看过候选后使用。输出包含 `pet.json`、`spritesheet.webp`、`preview.html` 与独立验收回执。回执把视觉审查标成**调用者声明**，不是自动模型视觉评分；客户端导入和实际显示仍未验收。必须选择不存在的新输出目录，不覆盖旧宠物。

校验检查尺寸、真实透明度、有效格非空、空格全透明、边界裁切风险、过小主体和整行动画完全相同。最后两项是本包质量门槛，不冒充上游协议。通过这些数字检查仍不能证明语义动作正确、步态顺畅或尾巴自然，需要观看预览。

## 复用层次

**参考图**用于不同生成模型保持同一外观；**状态帧**可经宿主允许的转换服务不同桌宠；**预览播放器**用于离线审查；**人格文本**用于对话；**TTS 配置**用于声音。共享来源和角色锚点，不把它们硬捆成一个必须全平台支持的安装器。
