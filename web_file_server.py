from flask import Flask, request, render_template_string, send_file, jsonify
from waitress import serve
import os
import datetime
import io
import mimetypes
import sys
import webbrowser
import threading
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import win32gui
import win32con

app = Flask(__name__)

# HTML 模板中添加自动刷新的 JavaScript 代码
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>局域网文件传输</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            position: relative;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        }

        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }

        .window-container {
            width: 600px;
            margin: 20px auto;
            padding: 30px;
            border: 2px dashed #4CAF50;
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.9);
            transition: all 0.3s ease;
        }

        .window-container:hover {
            border-color: #45a049;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }

        .upload-form {
            text-align: center;
        }

        .file-input-wrapper {
            display: flex;
            gap: 15px;
            justify-content: center;
            align-items: center;
            margin: 20px auto;
            max-width: 400px;
        }

        .file-input {
            display: none;
        }

        .custom-file-upload,
        .submit-btn {
            width: 160px;
            padding: 12px 0;
            border-radius: 10px;
            font-size: 16px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }

        .custom-file-upload {
            background: #4CAF50;
            color: white;
        }

        .submit-btn {
            background: #2196F3;
            color: white;
        }

        .submit-btn:disabled {
            background: #cccccc;
            cursor: not-allowed;
        }

        .file-list {
            display: none;
        }

        .file-list.has-files {
            display: block;
        }

        .file-item {
            background: rgba(255, 255, 255, 0.95);
            margin: 10px 0;
            padding: 15px 20px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .file-info {
            display: flex;
            align-items: center;
        }

        .file-icon {
            font-size: 24px;
            margin-right: 15px;
        }

        .file-name {
            font-size: 16px;
            color: #333;
        }

        .file-meta {
            font-size: 14px;
            color: #666;
        }

        .file-actions {
            display: flex;
            gap: 8px;
        }

        .action-btn {
            padding: 8px 16px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        .preview-btn {
            background-color: #2196F3;
            color: white;
        }

        .download-btn {
            background-color: #4CAF50;
            color: white;
        }

        .delete-btn {
            background-color: #f44336;
            color: white;
        }

        @media (max-width: 768px) {
            .window-container {
                width: auto;
                margin: 20px 15px;
                padding: 20px;
            }

            .file-input-wrapper {
                flex-direction: column;
                gap: 10px;
            }

            .custom-file-upload,
            .submit-btn {
                width: 100%;
                max-width: 280px;
            }
        }

        .upload-icon {
            font-size: 64px;
            color: #4CAF50;
            margin: 20px 0;
            display: block;
            text-align: center;
            transition: transform 0.3s ease;
        }

        .upload-icon:hover {
            transform: scale(1.1);
        }

        .window-container h2 {
            text-align: center;
            color: #333;
            font-size: 24px;
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>局域网文件传输</h1>

        <div class="window-container upload-form" id="upload-area">
            <div class="upload-icon">📤</div>
            <h2>上传文件</h2>
            <form id="upload-form" enctype="multipart/form-data">
                <div class="file-input-wrapper">
                    <input type="file" name="file" id="file-input" class="file-input">
                    <label for="file-input" class="custom-file-upload">选择文件</label>
                    <button type="submit" class="submit-btn" disabled>上传</button>
                </div>
            </form>
            <div id="selected-file-name"></div>
        </div>

        {% if files %}
        <div class="window-container file-list has-files">
            <h2>文件列表</h2>
            {% for file in files %}
            <div class="file-item">
                <div class="file-info">
                    <span class="file-icon">
                        {% if file.type.startswith('image/') %}📷
                        {% elif file.type.startswith('video/') %}🎥
                        {% elif file.type.startswith('audio/') %}🎵
                        {% elif file.type.startswith('text/') %}📄
                        {% else %}📁
                        {% endif %}
                    </span>
                    <div class="file-details">
                        <span class="file-name">{{ file.name }}</span>
                        <span class="file-meta">{{ file.size }} | {{ file.modified }}</span>
                    </div>
                </div>
                <div class="file-actions">
                    {% if file.previewable %}
                    <a href="{{ url_for('preview_file', filename=file.name) }}" class="action-btn preview-btn">预览</a>
                    {% endif %}
                    <a href="{{ url_for('download_file', filename=file.name) }}" class="action-btn download-btn" download>下载</a>
                    <button class="action-btn delete-btn" onclick="deleteFile('{{ file.name }}')">删除</button>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <script>
        // 添加自动刷新功能
        let lastModified = Date.now();
        
        function checkForUpdates() {
            fetch('/check_updates?last_modified=' + lastModified)
                .then(response => response.json())
                .then(data => {
                    if (data.need_refresh) {
                        location.reload();
                    }
                    lastModified = Date.now();
                })
                .catch(error => console.error('Error:', error));
        }

        // 每 2 秒检查一次更新
        setInterval(checkForUpdates, 2000);

        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('upload-form');
            const fileInput = document.getElementById('file-input');
            const submitBtn = form.querySelector('.submit-btn');
            const fileNameDisplay = document.getElementById('selected-file-name');

            fileInput.addEventListener('change', function() {
                if (this.files.length > 0) {
                    submitBtn.disabled = false;
                    fileNameDisplay.textContent = '已选择: ' + this.files[0].name;
                } else {
                    submitBtn.disabled = true;
                    fileNameDisplay.textContent = '';
                }
            });

            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(form);
                
                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        location.reload();
                    } else {
                        alert('上传失败');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('上传失败');
                });
            });
        });

        function deleteFile(filename) {
            if (confirm(`确定要删除文件 "${filename}" 吗？`)) {
                fetch(`/delete/${filename}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('删除失败：' + data.error);
                    }
                })
                .catch(error => {
                    alert('删除失败：' + error);
                });
            }
        }
    </script>
</body>
</html>
'''

# 创建上传文件夹
UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'FileTransfer_uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 添加一个变量来跟踪最后修改时间
last_modified_time = datetime.datetime.now()

@app.route('/check_updates')
def check_updates():
    global last_modified_time
    client_last_modified = float(request.args.get('last_modified', 0)) / 1000.0
    client_last_modified = datetime.datetime.fromtimestamp(client_last_modified)
    need_refresh = last_modified_time > client_last_modified
    return jsonify({'need_refresh': need_refresh})

@app.route('/')
def index():
    try:
        files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            size = os.path.getsize(path)
            modified = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            
            mime_type, _ = mimetypes.guess_type(filename)
            mime_type = mime_type or 'application/octet-stream'
            
            files.append({
                'name': filename,
                'size': human_size(size),
                'modified': modified.strftime('%Y-%m-%d %H:%M:%S'),
                'type': mime_type,
                'previewable': mime_type and mime_type.startswith(('image/', 'text/'))
            })
        
        return render_template_string(HTML_TEMPLATE, files=files)
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/upload', methods=['POST'])
def upload_file():
    global last_modified_time
    try:
        if 'file' not in request.files:
            return '没有文件', 400
        file = request.files['file']
        if file.filename == '':
            return '没有选择文件', 400
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            last_modified_time = datetime.datetime.now()
            return '文件上传成功', 200
    except Exception as e:
        print(f"Error in upload: {str(e)}")
        return str(e), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except Exception as e:
        print(f"Error in download: {str(e)}")
        return str(e), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    global last_modified_time
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        last_modified_time = datetime.datetime.now()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error in delete: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/preview/<filename>')
def preview_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        size = os.path.getsize(file_path)
        modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or 'application/octet-stream'

        file_info = {
            'name': filename,
            'size': human_size(size),
            'modified': modified.strftime('%Y-%m-%d %H:%M:%S'),
            'type': mime_type
        }

        # 如果是文本文件，读取内容
        text_content = ''
        if mime_type and mime_type.startswith('text/'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            except:
                text_content = '无法读取文件内容'

        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>文件预览 - {{ file.name }}</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    .preview-container {
                        max-width: 1000px;
                        margin: 0 auto;
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    }
                    .preview-header {
                        margin-bottom: 20px;
                        padding-bottom: 20px;
                        border-bottom: 1px solid #eee;
                    }
                    .preview-content {
                        text-align: center;
                    }
                    img, video {
                        max-width: 100%;
                        height: auto;
                    }
                    audio {
                        width: 100%;
                    }
                    .text-content {
                        white-space: pre-wrap;
                        text-align: left;
                        background: #f8f8f8;
                        padding: 20px;
                        border-radius: 5px;
                    }
                    .back-btn {
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #4CAF50;
                        color: white;
                        text-decoration: none;
                        border-radius: 10px;
                        margin-top: 20px;
                    }
                    .back-btn:hover {
                        background-color: #45a049;
                    }
                </style>
            </head>
            <body>
                <div class="preview-container">
                    <div class="preview-header">
                        <h1>{{ file.name }}</h1>
                        <p>文件大小: {{ file.size }} | 修改时间: {{ file.modified }}</p>
                    </div>
                    <div class="preview-content">
                        {% if file.type.startswith('image/') %}
                            <img src="{{ url_for('download_file', filename=file.name) }}" alt="{{ file.name }}">
                        {% elif file.type.startswith('video/') %}
                            <video controls>
                                <source src="{{ url_for('download_file', filename=file.name) }}" type="{{ file.type }}">
                                您的浏览器不支持视频播放
                            </video>
                        {% elif file.type.startswith('audio/') %}
                            <audio controls>
                                <source src="{{ url_for('download_file', filename=file.name) }}" type="{{ file.type }}">
                                您的浏览器不支持音频播放
                            </audio>
                        {% elif file.type.startswith('text/') %}
                            <div class="text-content">
                                <pre>{{ text_content }}</pre>
                            </div>
                        {% else %}
                            <p>此文件类型不支持预览</p>
                        {% endif %}
                    </div>
                    <a href="/" class="back-btn">返回文件列表</a>
                </div>
            </body>
            </html>
        ''', file=file_info, text_content=text_content)
    except Exception as e:
        print(f"Error in preview: {str(e)}")
        return str(e), 500

def human_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB"

def create_icon():
    width = 32
    height = 32
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    circle_color = (76, 175, 80)
    draw.ellipse([2, 2, width-2, height-2], fill=circle_color)
    arrow_color = (255, 255, 255)
    draw.polygon([
        (16, 8),
        (10, 14),
        (22, 14)
    ], fill=arrow_color)
    draw.polygon([
        (16, 24),
        (10, 18),
        (22, 18)
    ], fill=arrow_color)
    return image

def open_browser():
    webbrowser.open('http://localhost:5000')

def quit_window(icon):
    icon.stop()
    os._exit(0)

def run_server():
    try:
        # 禁用 Flask 的开发服务器输出
        import logging
        log = logging.getLogger('werkzeug')
        log.disabled = True
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None

        print(f"服务已启动，请在浏览器中访问: http://localhost:5000")
        print(f"文件将保存在: {UPLOAD_FOLDER}")
        serve(app, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"启动服务时出错: {str(e)}")
        input("按回车键退出...")  # 添加这行以便在出错时看到错误信息

if __name__ == '__main__':
    try:
        # 使用 win32gui 隐藏控制台窗口
        if sys.platform.startswith('win'):
            the_program_to_hide = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(the_program_to_hide, win32con.SW_HIDE)

        # 创建并启动服务器线程
        server_thread = threading.Thread(target=run_server, daemon=False)  # 改为非守护线程
        server_thread.start()

        # 创建系统托盘图标
        icon = Icon(
            'File Transfer',
            create_icon(),
            menu=Menu(
                MenuItem('打开网页', open_browser),
                MenuItem('退出', quit_window)
            )
        )

        # 自动打开浏览器
        webbrowser.open('http://localhost:5000')

        # 运行系统托盘
        icon.run()
    except Exception as e:
        print(f"程序启动错误: {str(e)}")
        input("按回车键退出...") 