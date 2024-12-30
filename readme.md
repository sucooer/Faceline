# 局域网文件传输工具

一个简单易用的局域网文件传输工具，支持在同一网络下的设备之间快速传输文件。

## 功能特点

- 🚀 快速启动，无需复杂配置
- 📱 支持移动端访问，响应式设计
- 🔍 文件预览功能（支持图片和文本文件）
- 💻 系统托盘运行，便捷管理
- 🎯 拖拽上传文件
- 📂 文件管理（上传、下载、预览、删除）
- 🎨 美观的用户界面

## 安装要求

- Python 3.6+
- 依赖包：
  - Flask
  - Waitress
  - Pillow
  - pystray

## 安装步骤

1. 克隆项目或下载源码
2. 安装依赖：
```bash
pip install flask waitress pillow pystray
```

## 使用方法

1. 运行程序：
```bash
python web_file_server.py
```
2. 程序会自动：
   - 在系统托盘显示图标
   - 打开默认浏览器访问界面
   - 创建文件存储目录：`~/FileTransfer_uploads`

3. 访问方式：
   - 本机访问：`http://localhost:5000`
   - 局域网访问：`http://<本机IP>:5000`

## 文件说明

- `web_file_server.py`：主程序文件
- `templates/`：HTML模板目录
  - `index.html`：主页面模板
  - `preview.html`：文件预览模板

## 注意事项

- 默认端口为5000，如需修改请在源码中更改
- 上传的文件保存在用户主目录下的`FileTransfer_uploads`文件夹中
- 建议在可信任的局域网环境中使用

## 系统托盘功能

- 点击图标显示菜单
- 可以快速打开网页界面
- 支持一键退出程序