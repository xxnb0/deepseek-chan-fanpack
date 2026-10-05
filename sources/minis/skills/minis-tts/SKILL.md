---
name: minis-tts
description: Generate playable Edge TTS audio for Minis. Trigger on explicit read-aloud/audio requests, and proactively for concise voice accents in many suitable casual chats, work updates, and completed tasks alongside whale-stickers. Never claim audio exists without generating it. Save under /var/minis/attachments and embed an inline playable player; avoid mechanical repetition or serious/sensitive situations.
version: 1.0.0
---
# Minis chat audio generation

Generate TTS as a **chat-deliverable media artifact**, not merely a workspace file or model configuration. User preference: in many appropriate everyday exchanges and completed-work handoffs, proactively make a brief (one or two sentences) playable character-voice accent, optionally paired with a semantically matching Q-style sticker. Deliver substantive text first; do not read lengthy answers verbatim, slow down urgent work, force audio every turn, or inject playful media into serious/sensitive topics. If generation fails, never imply that audio played.

## Environment

- Current runtime has `edge-tts` 7.2.8 installed. It calls Microsoft's online Edge speech service; it is not an offline model and availability/policies may change. Do not promise unlimited or permanently free use.
- The configured Minis model list currently has no `audio_output` model. Do not claim Edge TTS was added as a Minis LLM/model or that it works without network access.
- `/var/minis/attachments/` is the media directory used for inline audio delivery in this Minis chat. `android-player` is an optional device playback control, not a substitute for embedding the result in the reply.

## Workflow

1. Generate with the bundled script:
   ```sh
   python3 /var/minis/skills/minis-tts/scripts/generate.py --text '要朗读的文字'
   ```
   Optional: `--voice zh-CN-XiaoxiaoNeural`, `--rate '+0%'`, `--volume '+0%'`, `--pitch '+0Hz'`, `--name announcement`. Default voice is `zh-CN-XiaoyiNeural` (lively, standard Mandarin) at `+22Hz` pitch. Use `--file /path/to/text.txt` for longer text.

## Character voice profile

For the community-created whale-girl persona, aim for lively, warm, clear standard Mandarin with lightly playful delivery; avoid treating any voice as official canon. The user should choose from short same-text samples when uncertain. Candidate labels below are the provider's voice-list descriptions, not objective guarantees:

- `zh-CN-XiaoyiNeural` — `Lively`; recommended default for a bright, playful character without a regional accent.
- `zh-CN-XiaoxiaoNeural` — `Warm`; a softer, gentler alternative.
- `zh-CN-liaoning-XiaobeiNeural` — `Humorous`; a stronger Northeastern regional flavor, useful as a deliberately comic comparison but not neutral Mandarin.

Use `+22Hz` as the selected character default: the user prefers this level over higher settings because excessive pitch sounds unnatural, not more character-accurate. Keep the rate at `+0%`; do not keep raising pitch in pursuit of a more exact persona. The user can override pitch per request. This service does not offer a reliable custom voice-cloning control through this CLI; do not claim generated samples exactly recreate a particular person's voice.
2. Check the script's result. It verifies the output is non-empty and prints the actual attachment path and Minis URL. If generation fails, report the failure; do not invent a playable file.
3. In the same reply, embed the returned audio URL as an inline media item:
   ```markdown
   ![语音播放](minis://attachments/speech-....mp3)
   ```
   Use the actual returned filename. A plain workspace link, a path without an embed, or a claim that playback is ready is not sufficient.
4. Keep the text reply concise. State that generation uses the online Edge service when that context matters.

## Voice discovery

Run `edge-tts --list-voices` and filter for `zh-CN-` when asked to choose a voice. Pick a matching voice ID from the actual output; never invent voice IDs. If Edge TTS is missing, explain the dependency rather than silently claiming setup is complete.

## Optional device playback

Only when the user specifically asks to start playback on the Android device, first generate the attachment, then run `android-player play <session> <absolute-file-path>` and verify with `android-player status <session>`. For ordinary requests, prioritize the inline player in the current chat; do not start device audio unexpectedly.
