# Voice Agent - 语音对话智能体

基于阿里云 **Qwen3-Omni-Flash** 多模态模型的语音对话智能体。

## 架构

```
音频输入 → 声学 VAD → Qwen3-Omni-Flash (多模态 LLM) → TTS → 音频输出
```

**✨ 优势：**
- **无需 ASR** - Qwen3-Omni-Flash 直接理解音频
- **低延迟** - 减少中间环节
- **更自然** - 模型直接处理语音韵律、语气

### 组件说明

| 组件 | 技术 | 说明 |
|------|------|------|
| **声学 VAD** | WebRTC VAD | 检测音频中是否有人声 |
| **LLM** | Qwen3-Omni-Flash | 多模态大模型，直接处理音频 + 文本 |
| **TTS** | DashScope | 阿里云智能语音合成 (sambert-zhichu-v1) |

## 快速开始

### 1. 安装依赖

```bash
cd voice-agent
pip3 install -r requirements.txt
```

### 2. 配置 API Key

编辑 `.env` 文件：

```bash
DASHSCOPE_API_KEY="sk-your-api-key"
LLM_MODEL="qwen3-omni-flash"
```

### 3. 运行示例

**文本对话模式：**

```bash
python3 examples/chat_demo.py
```

**语音对话模式（需要麦克风）：**

```bash
python3 examples/voice_demo.py
```

**测试脚本：**

```bash
python3 tests/test_agent.py        # 文本测试
python3 tests/test_audio_input.py  # 音频输入测试
```

## 项目结构

```
voice-agent/
├── src/
│   ├── agent.py              # 主智能体
│   ├── acoustic_vad.py       # 声学 VAD
│   ├── llm.py                # Qwen3-Omni-Flash LLM (多模态)
│   ├── tts.py                # TTS 封装
│   └── __init__.py
├── examples/
│   ├── chat_demo.py          # 文本对话
│   └── voice_demo.py         # 语音对话
├── tests/
│   ├── test_agent.py         # 文本测试
│   └── test_audio_input.py   # 音频测试
├── .env                       # 配置
├── requirements.txt
└── README.md
```

## 自定义人设

```python
from src.agent import VoiceAgent

agent = VoiceAgent(
    system_prompt="""你是 XXX，一个...
- 性格：...
- 说话风格：...
- 背景：..."""
)
```

## API 参考

### VoiceAgent

```python
# 创建智能体
agent = VoiceAgent(api_key="...", system_prompt="...")

# 文本对话
async for event_type, data in agent.chat("你好"):
    if event_type == "text":
        print(data)
    elif event_type == "audio":
        # 播放音频
        pass

# 音频对话
import numpy as np
audio_data = np.array([...], dtype=np.int16)
async for event_type, data in agent.process_audio(audio_data):
    pass

# 清空历史
agent.clear_history()
```

## 事件类型

| 事件 | 说明 | 数据 |
|------|------|------|
| `listening` | 正在听 | None |
| `thinking` | 思考中 | None |
| `text` | 文本输出 | 文本片段 |
| `speaking` | 正在说 | None |
| `audio` | 音频输出 | PCM 数据 |

## 依赖服务

- **阿里云 DashScope**
  - Qwen3-Omni-Flash (多模态 LLM) - 音频 + 文本理解
  - SpeechSynthesizer (TTS) - 语音合成

## 注意事项

1. **Qwen3-Omni-Flash** 支持直接音频输入，音频需要转为 data URI 格式
2. **WebRTC VAD** 需要 16kHz 单声道 16-bit PCM 音频
3. **TTS 输出** 为 PCM 格式，可直接播放

## 许可证

Apache 2.0
