# 可选媒体工具契约

[START_HERE.md](START_HERE.md) 与 [宿主自检](docs/platforms.md) 描述能力和路由。工具名称、配置目录与发送方式由实际宿主决定；这些脚本不注册或修改宿主身份。

## 既有图片

在包根目录运行：

```sh
python3 skills/whale-stickers/scripts/pick.py pick 新Q_04 --format json
```

输出真实路径、用途和校验信息。选择前看 index 的 meaning/usage/text_note；若贴图带「制作中」「等确认」等文字，必须符合当前事实。先用宿主原生附件工具发送，再判断结果；JSON 或本地路径本身不是已发送。

已有参考图生图工具可直接用三视图和一张基础表情，无需调用选图脚本。失败回退适合的原图，详见 [图片规范](docs/assets.md)。

## 可替换语音参考

优先用宿主已有 TTS，参考 [语音参考](docs/voice.md) 的角色气质自行挑声线。确需可选 Edge 实现且已获准联网时：

```sh
python3 skills/whale-tts/scripts/generate.py --text '让我看看，这里还有一个更省事的办法。' --voice zh-CN-XiaoyiNeural --pitch +22Hz --rate +0% --output-dir /实际可发送的媒体目录
```

Edge 参数只是参考。脚本输出 MP3 与元数据，不自动发送、不自动播放，不检查宿主的消息能力。在线服务会接收朗读文本；私人或敏感内容按宿主规则处理。详见 [语音说明](docs/voice.md)。

`WHALE_CHAN_ROOT` 和 `WHALE_AUDIO_DIR` 是可选显式路径，非强制配置。本地文件由宿主原生附件工具发送。

## 可选检查与导出

`scripts/voice_doctor.py` 默认只读检查当前解释器、Edge 模块／CLI 与解码工具，不联网、不安装、不选择声线。实际 MP3 可加 `--audio` 检查；明确加 `--decode` 才进行有界完整解码，详见 [TTS 排障](docs/tts-troubleshooting.md)。

`scripts/export_persona.py` 将一致的人格导出到新目录，不安装宿主设置；`scripts/pet_asset.py` 验收实际候选 atlas 并可打包，不生成缺失动作。分别见 [导出](docs/export.md) 与 [宠物](docs/pets.md)。宿主已具备这些能力时，直接使用资料，不必重复装工具。
