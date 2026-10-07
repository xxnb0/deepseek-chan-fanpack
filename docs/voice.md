# 语音：气质可迁移，参数可替换

Muse 的原生实时声音与 Edge 独立音频是两条路径；先看 [TTS 分流与排障](tts-troubleshooting.md)。该页保留已有云端合成成功记录，同时明确未验证实时声线替换。只读检查可用 `scripts/voice_doctor.py`，它默认不会联网或生成声音。

现有可选脚本采用 **Edge TTS**：`zh-CN-XiaoyiNeural`（晓伊）、音高 `+22Hz`、语速 `+0%`。这些是参考参数，不是角色的官方配音或跨服务通用参数。已有 TTS 的宿主可以自行选择贴合的声音；不同服务按各自支持的参数调整。

[听听语音样例](../assets/audio/whale-chan-voice-sample.mp3) · [台词与参数](../assets/audio/README.md)

## 选择已有声音

优先使用宿主已经配置、获准调用的 TTS。选择清晰自然、灵动但不过尖、轻松时明快、认真时稳当的声音；以可懂度和长时间听感为先。不要为了「少女感」持续撒娇、夹嗓、尖叫或每句笑声。选择可用的合成声音即可。

首次用同一句短样本试听少量候选；已有确认偏好则直接沿用。保存最终确认的声线及该提供商支持的语速等参数，媒介设置与角色文本分别保留。不建立付费调用、不创建密钥、不克隆真人。已有模型提供试听功能不等于可以上传任意私人语音训练。

## 原生调整不满足时：可选原创声线

以下是需要另外确认服务与接入方式的选择，不是 Muse 已开放的声音设计接口，也没有在本包中部署或试听验收。

[Qwen 官方仓库](https://github.com/QwenLM/Qwen3-TTS) 区分按描述生成音色的 VoiceDesign、固定声线的 CustomVoice 与基于参考音频的 Base 模型。需要稳定复用同一角色声音时，不要每轮重新设计：

| 路线 | 保持声线一致的方法 | 契约边界 |
| --- | --- | --- |
| 本地 Qwen VoiceDesign + Base | 先设计一段原创合成参考音频，再建立可复用的 `voice_clone_prompt`，后续台词沿用 | VoiceDesign 返回音频；不是云端 voice ID，需要本地模型与推理资源 |
| 阿里云声音设计 | 先试听预览音频，再保存并复用返回的 voice ID | 设计和合成按服务要求使用匹配的模型与地域；需已有授权、凭据和费用安排 |

本地流程见官方 [Voice Design then Clone 例程](https://github.com/QwenLM/Qwen3-TTS#voice-design-then-clone)，复用的是自行设计的合成声音，无需寻找真人配音样本。[阿里云文档](https://help.aliyun.com/zh/model-studio/voice-design-user-guide) 说明相同描述可能生成不同音色，应选定后复用，而不是把描述文本当成唯一声线标识。

合成成功仍只证明得到音频。Qwen 的原生 SDK／API 不自动等于 OpenAI-compatible 语音接口，目标宿主能否调用、播放或替换实时声线，应分别核对。

## 能力与隐私

依次检查：TTS 可用与授权 → 当前声音存在 → 能生成受支持格式 → 能原生发语音 / 只能发音频附件 / 都不能。后两种要分别处理，不能把音频文件假称语音消息。

在线 TTS 会接收朗读文本。默认只考虑当前回复中适合朗读的短句，不读凭据、隐私资料、完整聊天或来源文档；敏感内容须遵守宿主的明确授权规则。生成与发送失败时，保留完整文字，不用「你听见了吗」掩盖失败。

失败时只报告已证实的阶段与现象；原因未明就保留未知，回退已有可用声音或文字，并保持宿主安全校验。

## 可选 Edge 脚本

只有确定需要这条路线时才安装 `requirements-tts.txt` 中的依赖，不影响文本或选图：

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-tts.txt
python3 skills/whale-tts/scripts/generate.py --text '已经核对好了，结果放在这里。' --output-dir /宿主允许的媒体目录
```

参数可用 `--voice`、`--pitch`、`--rate`、`--volume` 覆盖。默认值与本页参考参数一致。脚本确认非空与 MP3 标记，只是文件结构检查，不代表完整音频解码、主观试听或线上送达。

可用性与服务规则可能变化，不保证离线、永久免费或所有地区可达。
