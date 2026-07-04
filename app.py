"""
远程调用手机摄像头 - Flask + SocketIO 服务器 (固定IP版本)
手机打开摄像头页面采集画面，通过 WebSocket 传输到电脑端查看
使用固定IP 10.6.22.1，适用于皎月连等内网穿透环境
"""

import os
import ssl
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

LOCAL_IP = '10.6.22.1'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'camera-stream-secret-key'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading',
                    max_http_buffer_size=10 * 1024 * 1024)

cameras = {}
viewers = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/camera')
def camera():
    return render_template('camera.html')


@app.route('/viewer')
def viewer():
    return render_template('viewer.html')


@socketio.on('connect')
def handle_connect():
    print(f'[连接] 客户端已连接: {request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in cameras:
        cam_info = cameras.pop(sid)
        print(f'[断开] 摄像头断开: {cam_info.get("name", sid)}')
        emit('camera_disconnected', {'id': sid}, broadcast=True)
    if sid in viewers:
        viewers.pop(sid)
        print(f'[断开] 观看者断开: {sid}')


@socketio.on('register_camera')
def handle_register_camera(data):
    sid = request.sid
    cameras[sid] = {
        'name': data.get('name', '未命名摄像头'),
        'sid': sid
    }
    print(f'[注册] 摄像头已注册: {cameras[sid]["name"]}')
    emit('camera_list', {'cameras': [
        {'id': k, 'name': v['name']} for k, v in cameras.items()
    ]}, broadcast=True)


@socketio.on('register_viewer')
def handle_register_viewer():
    sid = request.sid
    viewers[sid] = {'sid': sid}
    print(f'[注册] 观看者已注册: {sid}')
    emit('camera_list', {'cameras': [
        {'id': k, 'name': v['name']} for k, v in cameras.items()
    ]})


@socketio.on('video_frame')
def handle_video_frame(data):
    for viewer_sid in viewers:
        emit('video_frame', data, room=viewer_sid)


def generate_ssl_cert():
    cert_dir = os.path.join(os.path.dirname(__file__), 'certs')
    cert_file = os.path.join(cert_dir, 'cert.pem')
    key_file = os.path.join(cert_dir, 'key.pem')

    if os.path.exists(cert_file) and os.path.exists(key_file):
        return cert_file, key_file

    os.makedirs(cert_dir, exist_ok=True)

    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import datetime
    import ipaddress

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, LOCAL_IP),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Camera Stream'),
    ])

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.IPAddress(ipaddress.IPv4Address(LOCAL_IP)),
                x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
                x509.DNSName('localhost'),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    with open(key_file, 'wb') as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(cert_file, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f'[SSL] 自签名证书已生成: {cert_dir}')
    return cert_file, key_file


@app.errorhandler(404)
def page_not_found(e):
    print(f'[404] 请求路径不存在: {request.path}')
    return f'''
    <html><body style="background:#0a0b14;color:#fff;font-family:sans-serif;
    display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;">
    <div>
        <h1 style="font-size:4rem;">📡</h1>
        <h2>页面不存在</h2>
        <p style="color:#999;">请求路径: {request.path}</p>
        <p style="margin-top:20px;">
            <a href="/camera" style="color:#7c5cff;margin:0 10px;">📱 手机端</a>
            <a href="/viewer" style="color:#00c8ff;margin:0 10px;">🖥️ 电脑端</a>
        </p>
    </div></body></html>
    ''', 404


if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 5000

    cert_file, key_file = generate_ssl_cert()

    print('=' * 60)
    print('  远程调用手机摄像头 (固定IP)')
    print('=' * 60)
    print(f'  固定IP: {LOCAL_IP}')
    print(f'  手机端打开: https://{LOCAL_IP}:{PORT}/camera')
    print(f'  电脑端打开: https://{LOCAL_IP}:{PORT}/viewer')
    print(f'  首页:       https://{LOCAL_IP}:{PORT}/')
    print('=' * 60)
    print('  注意: 首次访问时浏览器会提示证书不安全，')
    print('  请点击「高级」→「继续访问」即可。')
    print('=' * 60)

    socketio.run(app, host=HOST, port=PORT,
                 ssl_context=(cert_file, key_file),
                 allow_unsafe_werkzeug=True,
                 log_output=True)