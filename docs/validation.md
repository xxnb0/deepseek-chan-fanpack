# 使用验收、维护与回滚

## 普通使用：一句话之后看结果

不需要主人先安装 Python 或运行脚本。目标 AI 按 [START_HERE.md](../START_HERE.md) 理解角色、映射已有载体，并说明：当前会话还是已验证的持久范围，哪些媒体实际可用，以及持久修改怎样恢复。

人工在目标宿主用 [14 个场景案例](../tests/persona-cases.json) 验收：普通聊天、技术任务、受夸、纠错、严肃场景、其他助手、无媒体、真实卡住、图片、声音与会话限定。再做连续 12 轮混合对话，确认角色有轻重变化，不每轮傲娇或米饭/Token复读。案例是验收材料，文件测试通过不等于模型行为已评测通过。

## 维护者离线检查

仅维护脚本需要 Python 3.10+，角色文本无需 Python。

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s skills/whale-stickers/tests -v
python3 scripts/verify.py
```

完整克隆应跑默认 `verify.py`，核验核心所有文件字节。只有文本和少量样本的稀疏审查可显式运行 `python3 scripts/verify.py --metadata-only`：检查现有字节、全部索引/文档/语法，逐项列出未获取的图片，输出 `full_media_verification: false`。这不是完整图片校验。归档另取得并安全解压后可跑 `--archive`，不可与 metadata-only 混用。

## 可选资料放置与兼容入口

只想把资料放到指定目录：

```sh
python3 scripts/install.py --target bundle --workspace /明确选择的资料目录 --dry-run
python3 scripts/install.py --target bundle --workspace /明确选择的资料目录
```

`bundle` 也是默认 target，只复制 `deepseek-chan/`，不改宿主人格、不注册 skills。默认复制归档索引而不复制 518 张归档图片。它不是目标 AI 启用角色的必要步骤。

历史 `generic`、`hermes`、`cursor`、`openclaw` target 仍保留，仅在明确需要旧文件布局时使用，不视为当前各产品接口保证。所有 target 都要选择显式目录；`--dry-run` 输出将改的路径、冲突和备份位置。旧 target 替换现有人格须显式 `--replace-persona`；不要仅为兼容仓库强行创建宿主没有使用的文件。

## 回滚

- 角色字段/自定义指令：适配前保存原值，回滚时只恢复本次改变的字段；无法导出且修改不可恢复时先停止并问主人。
- 仅当前会话：停用该角色模式或开启未应用该角色的新会话；不能说撤销了不存在的全局安装。
- 可选安装器：已存在的受影响路径备份到工作目录 `.deepseek-chan-backups/<时间>/`。对照 dry-run 的 touched 路径和备份，停止相关宿主后逐项恢复。首次新增路径没有旧备份，确认没有后续用户文件后仅移除本次新增内容；不要整目录覆盖或抹掉后续编辑。
- 后续修改过同一文件时先比较差异并保留新内容，不能拿旧备份盲目覆盖。数据包与两个技能的复制，不等于任何模型、消息渠道或认证已安装。

以上检查不替代真实宿主权限与消息契约；有未知项就明确写未知，不把读取成功、生成成功、发送成功和持久化成功混成一个状态。
