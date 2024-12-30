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

app = Flask(__name__)

# HTML 模板
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

def human_size(size_in_bytes):
    """将字节数转换为人类可读的格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB"

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
    try:
        if 'file' not in request.files:
            return '没有文件', 400
        file = request.files['file']
        if file.filename == '':
            return '没有选择文件', 400
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
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

@app.route('/preview/<filename>')
def preview_file(filename):
    try:
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except Exception as e:
        print(f"Error in preview: {str(e)}")
        return str(e), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error in delete: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def create_icon():
    """创建一个文件传输图标"""
    # 创建 32x32 像素的图像，使用 RGBA 模式支持透明度
    width = 32
    height = 32
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # 创建绘图对象
    draw = ImageDraw.Draw(image)
    
    # 绘制圆形背景
    circle_color = (76, 175, 80)  # 绿色
    draw.ellipse([2, 2, width-2, height-2], fill=circle_color)
    
    # 绘制箭头
    arrow_color = (255, 255, 255)  # 白色
    
    # 上箭头
    draw.polygon([
        (16, 8),   # 顶点
        (10, 14),  # 左下
        (22, 14)   # 右下
    ], fill=arrow_color)
    
    # 下箭头
    draw.polygon([
        (16, 24),  # 底点
        (10, 18),  # 左上
        (22, 18)   # 右上
    ], fill=arrow_color)
    
    return image

def open_browser():
    webbrowser.open('http://localhost:5000')

def quit_window(icon):
    icon.stop()
    os._exit(0)

def run_server():
    try:
        print(f"服务已启动，请在浏览器中访问: http://localhost:5000")
        print(f"文件将保存在: {UPLOAD_FOLDER}")
        serve(app, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"启动服务时出错: {str(e)}")

if __name__ == '__main__':
    # 创建并启动服务器线程
    server_thread = threading.Thread(target=run_server, daemon=True)
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