# 可移植导出，不自动安装

`SOUL.md` 是正文真源；`personality.json` 的 body 与 `prompts/system.md` 是等价入口，不应分别编辑出三种人格。新工具在维护时可同步它们，并将需要的内容导出到**不存在的新目录**。没有平台依赖，也没有网络请求。

```sh
python3 scripts/export_persona.py --check
python3 scripts/export_persona.py --output-dir output/whale-export
```

默认输出通用提示、SOUL 候选、身份资料、仅供合并的 AGENTS 片段、Character Card v2 JSON，以及包含内容哈希的 export-manifest.json。`--target` 可选择 `prompt`、`hermes`、`openclaw`、`card-v2` 或默认 `all`。语音、宠物和宿主设置不被自动修改。

```sh
python3 scripts/export_persona.py --target hermes --output-dir output/whale-hermes
python3 scripts/export_persona.py --target openclaw --output-dir output/whale-openclaw
python3 scripts/export_persona.py --target card-v2 --output-dir output/whale-card
```

文件正文和哈希按 LF 规范化；同样的输入用 CRLF 或 LF 保存，导出结果一致。身份资料中的本地 Markdown 资源链接转换为来源仓库地址，不假装只导出文字也拥有原图附件。纯文本中提及的 docs 路径属于来源仓库；离线使用需要另行取得所需材料。

维护者改过 SOUL 后，可明确执行 `--sync`，仅同步已有的两个派生文件，再运行测试与校验。`--check` 发现不一致会失败；正常导出也拒绝使用已知漂移的入口，不悄悄选择其中一份。

已有目标目录即拒绝，即使它为空；选择另一个新目录，不用强制覆盖。导出中断可能留下本次创建的不完整目录，只有全部文件写完才生成 export-manifest.json，不能把残留目录当成功交付。

导入前先按 [平台速查](platform-adapters.md) 确定真实角色载体，保存拟修改字段的原值。输出文件名不是授权，也不是已安装回执。场景测试仍应在真实宿主中进行。
