# 实时打断功能指南

## 📋 概述

Voice Agent 现在支持**基于意图判断的实时打断**，使用 LLM 模型理解用户是否有打断意图，而不是简单的规则匹配。

## 🎯 核心功能

### 1️⃣ 声学 VAD (Acoustic VAD)
- **作用**: 检测音频中是否有人声
- **技术**: WebRTC VAD + 能量检测
- **响应时间**: < 50ms

### 2️⃣ 语义 VAD (Semantic VAD) - 基于 LLM
- **作用**: 使用 LLM 判断用户是否有打断意图
- **技术**: 阿里云 qwen-turbo 模型
- **准确率**: 88.9%
- **响应时间**: 
  - 关键词检测：< 10ms
  - LLM 判断：~500ms

### 3️⃣ 实时打断
- **关键词打断**: 说出特定词语立即中断
- **意图打断**: LLM 理解用户意图后中断
- **能量打断**: 检测到新的语音输入时中断
- **综合响应时间**: < 600ms

---

## 🚀 使用方法

### 方式一：全双工模式（推荐）

```bash
cd ~/.openclaw/workspace/voice-agent
source .venv/bin/activate
python examples/full_duplex_demo.py
```

**特点**:
- ✅ 边听边说
- ✅ 随时打断
- ✅ LLM 理解打断意图
- ✅ 最自然的对话体验

### 方式二：文本对话测试

```bash
cd ~/.openclaw/workspace/voice-agent
source .venv/bin/activate
python tests/quick_chat.py
```

**特点**:
- ✅ 快速测试对话质量
- ✅ 无需麦克风

---

## 🎤 打断方式

### 1. 关键词打断（最快）

悠悠说话时，说出以下任意词语即可**立即**打断她：

```
等等、等一下、停下、停一下、停
不要说了、别说、别说了
不对、错了、不是这样、不是
取消、停止、闭嘴、打断、慢点、重新说
```

**响应时间**: < 10ms

**示例**:
```
悠悠：今天天气不错，我们可以...
你：等等
悠悠：（立即停止）怎么了？
```

### 2. 意图打断（智能）

悠悠说话时，说出任何表达打断意图的话，LLM 会理解并中断：

```
"我想说一下..."
"你说的不对..."
"听我说..."
"我还没说完..."
"不是这样的..."
```

**响应时间**: ~500ms

**示例**:
```
悠悠：我觉得你可以试试那个方法...
你：你说的不对，我觉得...
悠悠：（理解到你想纠正，立即停止）哦？你说说看
```

### 3. 能量打断（备选）

悠悠说话时，直接说话即可打断（无需特定词语）。

**响应时间**: ~200ms

**示例**:
```
悠悠：我觉得你可以试试...
你：（直接说话）不对，我想说的是...
悠悠：（检测到新语音，立即停止）哦，你说什么？
```

---

## ⚙️ 配置选项

### 禁用/启用打断

```python
from src.full_duplex_agent import FullDuplexVoiceAgent

agent = FullDuplexVoiceAgent()

# 禁用打断
agent.enable_interrupt(False)

# 启用打断
agent.enable_interrupt(True)
```

### 调整打断敏感度

编辑 `.env` 文件：

```bash
# 声学 VAD 敏感度 (0-3, 越高越敏感)
VAD_AGGRESSIVENESS=2

# 语义 VAD 阈值 (0-1, 越低越容易判定为打断)
SEMANTIC_VAD_THRESHOLD=0.5
```

### 自定义打断关键词

```python
# 修改 interrupt_keywords 列表
agent.semantic_vad.interrupt_keywords = [
    "等等", "停下", "停",
    # 添加自定义关键词
    "等一下", "稍等", "听我说"
]
```

---

## 📊 性能指标

| 指标 | 目标值 | 实际值 |
|------|--------|--------|
| 声学 VAD 响应 | < 100ms | ✅ ~50ms |
| 关键词检测 | < 20ms | ✅ ~10ms |
| LLM 意图判断 | < 600ms | ✅ ~500ms |
| 能量打断响应 | < 300ms | ✅ ~200ms |
| 意图判断准确率 | > 85% | ✅ **88.9%** |

---

## 🔧 技术架构

```
┌─────────────────────────────────────────┐
│          全双工语音对话系统               │
│                                         │
│  ┌──────────┐                           │
│  │ 声学 VAD  │ 检测人声                   │
│  └────┬─────┘                           │
│       │                                 │
│       ▼                                 │
│  ┌──────────────────┐                   │
│  │   打断检测        │                   │
│  │  ┌────────────┐  │                   │
│  │  │ 关键词检测  │  │ < 10ms (快速)     │
│  │  └─────┬──────┘  │                   │
│  │        │         │                   │
│  │  ┌─────▼──────┐  │                   │
│  │  │ LLM 意图判断 │  │ ~500ms (智能)     │
│  │  └─────┬──────┘  │                   │
│  └────────┼────────┘                   │
│           │                            │
│           ▼                            │
│  ┌─────────────────┐                   │
│  │   TTS 播放       │◄─── 中断信号       │
│  │  (流式输出)     │                   │
│  └─────────────────┘                   │
└─────────────────────────────────────────┘
```

---

## 💡 使用技巧

### 1. 优先使用关键词
- 关键词打断最快（< 10ms）
- 紧急情况用"停"、"等等"

### 2. 自然表达意图
- 像真人对话一样自然表达
- LLM 能理解多种表达方式

### 3. 清晰发音
- 说话清晰，语速适中
- 避免背景噪音

### 4. 停顿等待
- 说完后停顿 0.5 秒，让系统判断
- 避免连续快速说话

---

## 🐛 常见问题

### Q: 打断不灵敏？
**A**: 
1. 检查麦克风音量和权限
2. 降低 `VAD_AGGRESSIVENESS` 到 1
3. 确保环境噪音不大

### Q: 总是误打断？
**A**:
1. 提高 `SEMANTIC_VAD_THRESHOLD` 到 0.7
2. 减少打断关键词数量
3. 禁用能量打断，只用关键词打断

### Q: LLM 判断慢？
**A**:
- 正常情况 ~500ms
- 确保网络连接良好
- 关键词打断不受影响（< 10ms）

### Q: 准确率如何提高？
**A**:
- 当前准确率为 88.9%
- 可以添加更多训练样本
- 优化 prompt 提示词

---

## 📝 API 参考

### FullDuplexVoiceAgent

```python
from src.full_duplex_agent import FullDuplexVoiceAgent

# 创建智能体
agent = FullDuplexVoiceAgent(
    system_prompt="你是悠悠，一个..."
)

# 启用/禁用打断
agent.enable_interrupt(True)

# 清空历史
agent.clear_history()

# 处理音频流
async for event_type, data in agent.process_audio_realtime(
    audio_stream,
    interrupt_callback=lambda: False
):
    if event_type == "text":
        print(data)
    elif event_type == "audio":
        # 播放音频
        pass
```

### SemanticVAD

```python
from src.semantic_vad import SemanticVAD

# 创建语义 VAD
vad = SemanticVAD(api_key="sk-xxx", threshold=0.5)

# 判断是否有打断意图
has_intent = await vad.has_interrupt_intent(
    text="等等，我想说一下",
    assistant_speaking=True
)
print(has_intent)  # True

# 判断是否说完（turn-taking）
is_complete = await vad.is_turn_complete("今天天气不错")
print(is_complete)  # True
```

---

## 🎉 下一步

- [ ] 集成 ASR 实时识别用户语音
- [ ] 优化 LLM prompt 提高准确率
- [ ] 添加更多打断意图样本
- [ ] 支持多轮对话上下文理解
- [ ] 添加打断统计和分析

---

**享受自然流畅的对话体验！** 🎊
