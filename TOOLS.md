# 鲸鱼娘媒体工具契约

## 选图

```sh
python3 deepseek-chan/skills/whale-stickers/scripts/pick.py list
python3 deepseek-chan/skills/whale-stickers/scripts/pick.py pick 新Q_04 --verify-sha256 --format json
```

脚本返回实际文件路径、语义和使用范围。宿主先确认语义，再把路径交给自己的消息附件发送工具；工具名和参数以宿主真实文档为准。不能猜测文件名、截断URL或把本地文件路径当公网链接。

## 语音

```sh
python3 deepseek-chan/skills/minis-tts/scripts/generate.py --text '哼～，交给本鲸鱼娘。' --output-dir /实际可发送的媒体目录
```

默认 `zh-CN-XiaoyiNeural`、音高 `+22Hz`、语速 `+0%`。需要 Python3、edge-tts 和在线服务可达；依赖见 `requirements-tts.txt`。文件生成且非空后才能发送。一次一两句真实角色语音作点缀，不自动开启设备扬声器。

## 分层媒体

- `deepseek-chan/assets/reference/character-fullbody.webp`：最高级形象基准（三视图）。
- `deepseek-chan/assets/stickers/common/`：33张已校准常用表情；`index.json`是语义真源，`variants.json`记录实际透明状态。
- `deepseek-chan/archive/reference-library/`：可选518张参考杂物间，不参与默认运行。

仓库位置不一定等于工作目录。脚本会从自身路径向上找包根目录，也可设置 `WHALE_CHAN_ROOT`。语音可用 `WHALE_AUDIO_DIR` 指向宿主允许发送的媒体目录。脚本返回的路径需要由宿主支持的媒体工具处理；文本人格能迁移不等于所有前端都支持图片/音频。
