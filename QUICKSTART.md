# 快速开始指南

## 跨平台支持

✅ **Mac** - 完全支持  
✅ **Windows** - 完全支持（需要额外配置）  
✅ **Linux** - 完全支持

---

## 快速安装

### Windows

```batch
# 1. 安装依赖
install.bat

# 2. 配置 API Key
copy .env.example .env
# 编辑 .env 填入你的 DASHSCOPE_API_KEY

# 3. 启动
start.bat
```

### Mac / Linux

```bash
# 1. 安装依赖
chmod +x install.sh start.sh
./install.sh

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 DASHSCOPE_API_KEY

# 3. 启动
./start.sh
```

---

## Windows 额外依赖

如果安装过程中遇到问题，可能需要手动安装以下工具：

### 1. FFmpeg（pydub 需要）

**方法一：使用 winget**
```powershell
winget install Gyan.FFmpeg
```

**方法二：使用 chocolatey**
```powershell
choco install ffmpeg
```

**方法三：手动安装**
1. 下载：https://ffmpeg.org/download.html
2. 解压到 `C:\ffmpeg`
3. 添加 `C:\ffmpeg\bin` 到系统 PATH

### 2. PortAudio（sounddevice 需要）

通常 `sounddevice` 会自带 PortAudio。如果安装失败：

```powershell
pip install sounddevice --only-binary :all:
```

### 3. WebRTC VAD

Windows 上可能需要使用预编译版本：

```powershell
pip install webrtcvad-wheels
# 或
pip install webrtcvad --only-binary :all:
```

---

## 运行模式

| 模式 | 说明 | 需要硬件 |
|------|------|----------|
| **文本对话** | 纯文本输入输出 | 无 |
| **语音对话** | 麦克风输入 + 扬声器输出 | 麦克风、扬声器 |
| **测试脚本** | 单元测试 | 无 |
| **音频测试** | 音频输入测试 | 麦克风 |

---

## 常见问题

### Q: `webrtcvad` 安装失败
**A:** 使用预编译 wheel：
```bash
pip install webrtcvad-wheels
```

### Q: `sounddevice` 无法找到 PortAudio
**A:** 
- Windows: `pip install sounddevice --only-binary :all:`
- Mac: `brew install portaudio`
- Ubuntu: `sudo apt install portaudio19-dev`

### Q: `pydub` 提示找不到 ffmpeg
**A:** 安装 ffmpeg 并添加到 PATH（见上方 Windows 额外依赖）

### Q: 语音模式没有声音
**A:** 
1. 检查麦克风权限
2. 确认默认录音设备正确
3. 检查 `.env` 中的 API Key 是否正确

---

## 获取 API Key

1. 访问阿里云 DashScope：https://dashscope.console.aliyun.com/
2. 注册/登录账号
3. 创建 API Key
4. 复制到 `.env` 文件

---

## 下一步

- 查看 `README.md` 了解详细功能
- 查看 `examples/` 目录了解更多示例
- 修改 `system_prompt` 自定义你的人设
