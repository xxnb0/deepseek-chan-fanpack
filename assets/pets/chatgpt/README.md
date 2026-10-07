# 鲸鱼娘 · 大肥鱼 — ChatGPT 宠物动作

本仓库参考形象新生成的可选动作包。共九种连续动作；v2 另有十六方向。没有改变用户当前宠物、人格或账户设置。

![九种动作](previews/all-states.gif)

| 版本 | 图集 | 配套信息 |
| --- | --- | --- |
| v1 | [1536 × 1872 PNG](v1/spritesheet.png) | [pet.json](v1/pet.json)；公开 Web 文档当前列出的九行格式 |
| v2 | [1536 × 2288 PNG](v2/spritesheet.png) | [pet.json](v2/pet.json)；仅用于明确支持 v2 的入口 |

两版在 2026-10-06 均通过 Pets MCP 只读预检；GUI 导入和 Dot 绑定未实测。v2 四个正方向通过盲审，中间角度有已复核警告，247.5° 的向下分量仍有歧义。不要把结构通过理解为所有方向完全精准或所有平台通用。

- [完整用法、动作表和实际限制](../../../docs/pets.md)
- [清单、文件尺寸与校验值](manifest.json)
- [连续动作 MP4](previews/all-states.mp4) · [单动作预览](previews/states/) · [十六方向循环](previews/look-loop.gif)
- [只读校验与视觉检查记录](qa/)
- [制作方法与参考指纹](production.json)
- [来源、署名和衍生许可](NOTICE.md)

`previews/` 用来观看，上传时使用对应版本目录的 `spritesheet.png`。两版标准动作像素相同，v1 是 v2 前九行的无缩放裁切。
