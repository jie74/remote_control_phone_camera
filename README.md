# 远程调用手机摄像头

通过 WebSocket 实现手机摄像头画面的实时传输，在电脑端进行查看。

## 项目架构

```
┌─────────────┐     WebSocket      ┌─────────────┐     WebSocket      ┌─────────────┐
│  📱 手机端   │ ──→ 视频帧 ──→    │  🔌 服务器    │ ──→ 视频帧 ──→    │  🖥️ 电脑端   │
│  camera.html│                    │    app.py    │                    │ viewer.html │
└─────────────┘                    └─────────────┘                    └─────────────┘
```

## 技术栈

- **后端**: Python 3 + Flask + Flask-SocketIO
- **前端**: HTML5 + CSS3 + JavaScript
- **通信**: WebSocket (Socket.IO)
- **视频采集**: MediaDevices API (`getUserMedia`)
- **安全**: 自签名 SSL 证书（浏览器要求 HTTPS 才能访问摄像头）

## 运行流程

### 1. 修改服务器 IP（重要）

在启动前，请确保 `app.py` 中的 IP 地址与你的服务器实际 IP 一致：

```python
# app.py 第 120 行和第 135 行
# 将 10.6.22.1 替换为你的本机 IP
```

查看本机 IP 地址：
- **Windows**: 打开命令提示符，运行 `ipconfig`，找到 `IPv4 地址`
- **macOS/Linux**: 打开终端，运行 `ifconfig` 或 `ip addr`

### 2. 启动服务器

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器
python app.py
```

服务器会自动生成 SSL 证书（首次运行时），然后在端口 5000 启动服务。

### 3. 手机端操作

1. 在手机浏览器中打开：`https://<服务器IP>:5000/camera`
2. 浏览器提示证书不安全时，点击「高级」→「继续访问」
3. 输入摄像头名称（默认为"我的手机"）
4. 点击 📷 按钮开始推流
5. 可选操作：
   - 🔄 切换前后摄像头
   - 💡 开启/关闭闪光灯（需设备支持）
   - 调整画质（标清/高清/超清）

### 4. 电脑端查看

1. 在电脑浏览器中打开：`https://<服务器IP>:5000/viewer`
2. 等待手机端开始推流后，画面会自动显示
3. 查看实时统计：FPS、延迟、帧大小
4. 点击 ⛶ 按钮进入全屏模式

## 核心流程说明

### 连接流程

```
手机端                    服务器                    电脑端
  │                          │                          │
  │── SocketIO connect ─────→│                          │
  │                          │                          │
  │←── connect 确认 ─────────│                          │
  │                          │                          │
  │── register_camera ──────→│                          │
  │                          │── broadcast camera_list →│
  │                          │                          │
  │                          │←── register_viewer ──────│
  │                          │── camera_list (当前列表)→│
  │                          │                          │
```

### 视频帧传输流程

```
手机端                    服务器                    电脑端
  │                          │                          │
  │  getUserMedia 获取流      │                          │
  │         ↓                │                          │
  │  Canvas 捕获帧           │                          │
  │         ↓                │                          │
  │  toDataURL 转 JPEG       │                          │
  │         ↓                │                          │
  │── video_frame ──────────→│                          │
  │                          │── emit video_frame ─────→│
  │                          │       (room: viewer_sid) │
  │                          │                          │
  │                          │                          │── img.src = data.image
```

## 文件结构

```
远程调用手机摄像头/
├── app.py              # Flask 服务器主文件
├── certs/              # SSL 证书目录（自动生成）
│   ├── cert.pem        # 证书文件
│   └── key.pem         # 私钥文件
└── templates/          # HTML 模板
    ├── index.html      # 首页 - 选择角色
    ├── camera.html     # 手机端 - 摄像头采集
    └── viewer.html     # 电脑端 - 画面查看
```

## 关键功能

| 功能 | 说明 |
|------|------|
| 实时视频传输 | 通过 WebSocket 实现低延迟传输 |
| 前后摄像头切换 | 支持 environment/user 两种模式 |
| 闪光灯控制 | 利用 MediaTrackCapabilities API |
| 画质调整 | 支持 0.6/0.75/0.9 三种质量 |
| 多摄像头支持 | 支持同时连接多个手机 |
| 全屏显示 | 电脑端支持全屏查看 |
| 实时统计 | FPS、延迟、帧大小实时显示 |

## 注意事项

1. **HTTPS 必须**: 现代浏览器要求 HTTPS 才能访问摄像头 API
2. **网络要求**: 手机和电脑需在同一局域网内
3. **证书警告**: 首次访问会提示证书不安全，需手动确认继续
4. **性能建议**: 在网络不稳定时建议使用标清画质
5. **浏览器兼容性**: 推荐使用 Chrome、Safari 或 Edge

## 安装依赖

```bash
pip install flask flask-socketio cryptography
```
