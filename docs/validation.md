# 使用验收、维护与回滚

## 普通使用：一句话之后看结果

不需要主人先安装 Python 或运行脚本。目标 AI 按 [START_HERE.md](../START_HERE.md) 理解角色、映射已有载体，并说明：当前会话还是已验证的持久范围，哪些媒体实际可用，以及持久修改怎样恢复。

人工在目标宿主用 [16 个场景案例](../tests/persona-cases.json) 验收：普通聊天、技术任务、受夸、纠错、严肃场景、其他助手、无媒体、真实卡住、图片、声音选择、分项配置验收与会话限定。再做连续 12 轮混合对话，确认角色有轻重变化，不每轮傲娇或米饭/Token复读。案例是验收材料，文件测试通过不等于模型行为已评测通过。

## 维护者离线检查

仅维护脚本需要 Python 3.10+，角色文本无需 Python。

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s skills/whale-stickers/tests -v
python3 scripts/verify.py
```

完整克隆应跑默认 `verify.py`，核验核心所有文件字节。只有文本和少量样本的稀疏审查可显式运行 `python3 scripts/verify.py --metadata-only`：检查现有字节、全部索引/文档/语法，逐项列出未获取的图片，输出 `full_media_verification: false`。这不是完整图片校验。归档另取得并安全解压后可跑 `--archive`，不可与 metadata-only 混用。

## 恢复角色设置

- 角色字段或自定义指令：适配前保存原值，需要恢复时只还原实际改变的字段。
- 仅当前会话：停用该角色模式，或开启未应用角色的新会话。
- 文件式载体：保留修改前的副本；恢复前比较后续改动，避免覆盖新内容。

角色生效、媒体生成、消息发送与持久保存分别验收。
