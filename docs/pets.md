# 宠物、多动作图与通用性

结论：**值得为桌宠单独准备真正的多动作素材；不值得假设一张 atlas 可直接覆盖所有平台。** 角色外观共用三视图，文件格式按宿主明确契约导出，人格与声音保持独立。

## 当前证据

[Dot 官方帮助](https://help.openai.com/en/articles/20001530-getting-started-with-your-dot) 明确可选或生成宠物。[OpenAI hatch-pet 的公开动画行说明](https://raw.githubusercontent.com/openai/skills/main/skills/.curated/hatch-pet/references/animation-rows.md) 给出8列9行、单元192×208的 Codex 参考布局，共1536×1872；九种状态合计57帧，剩余15格必须透明。

[社区维护的 hatch-pet 变体](https://github.com/cjahv/codex-AGENTS/blob/main/skills/hatch-pet/SKILL.md) 还出现11行及额外视线的约定。它说明存在格式差异，不足以证明所有 Dot／Codex 安装都接受同一版本。本包只实现已逐项核对的公开九行校验，不自动把十一行裁成九行，也不凭猜测补 `spriteVersionNumber`。目标要求十一行时，先读取其完整行序、视线定义和元数据。

已有 [Petty](https://github.com/LeslieLeung/petty) 和 [Clawdex](https://github.com/danielkempe/clawdex/blob/main/skill/hatch-pet/SKILL.md) 等第三方复用入口，但这里只做文档级兼容性判断，没有安装或端到端验收。图片的可移植性高于宿主安装协议的可移植性。

Muse 的[原生实时头像](https://research.meta.ai/blog/bringing-your-muse-to-life) 使用参考媒体与语音令牌同步生成，不依赖本包提供桌宠格子图。不要为它额外维护同一套帧动画或承诺外部 MP3 能驱动原生口型。

## 本轮真正交付了什么

[atlas-profile.json](../assets/pet/atlas-profile.json) 是可机读协议；[generation-brief.md](../assets/pet/generation-brief.md) 是对应角色的逐状态简报；`scripts/pet_asset.py` 可对真实候选图校验、无损转码并打包，同时生成本地状态预览页面。工具不会生成缺少的动作，也不安装到任何平台。

**没有随本次提交提供已经视觉验收的角色 atlas。** 上一会话声称生成的九行／十一行图片未能从本轮实际文件中找回；不能靠旧文字记录证明存在或质量通过。这里没有以重复贴图、几何测试图或空占位文件冒充成品。

## 使用工具

可选图像校验依赖单独列在 `requirements-media.txt`，不影响纯文字使用。应在获准的新隔离环境安装该依赖。

```sh
python3 scripts/pet_asset.py --input /实际候选图.png
python3 scripts/pet_asset.py --input /实际候选图.png --output-dir output/whale-pet --visual-review-confirmed
```

第二条只应在人工真正看过候选后使用。输出包含 `pet.json`、`spritesheet.webp`、`preview.html` 与独立验收回执。回执把视觉审查标成**调用者声明**，不是自动模型视觉评分；客户端导入和实际显示仍未验收。必须选择不存在的新输出目录，不覆盖旧宠物。

校验检查尺寸、真实透明度、有效格非空、空格全透明、边界裁切风险、过小主体和整行动画完全相同。最后两项是本包质量门槛，不冒充上游协议。通过这些数字检查仍不能证明语义动作正确、步态顺畅或尾巴自然，需要观看预览。

## 复用层次

**参考图**用于不同生成模型保持同一外观；**状态帧**可经宿主允许的转换服务不同桌宠；**预览播放器**用于离线审查；**人格文本**用于对话；**TTS 配置**用于声音。共享来源和角色锚点，不把它们硬捆成一个必须全平台支持的安装器。
