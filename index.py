from flask import Flask, jsonify, send_file, render_template, request, send_from_directory
from flask_cors import CORS
import os
import mimetypes
import json
from pathlib import Path

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')
CORS(app)  # 允许跨域请求

# 图片文件扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}

# 配置要扫描的根目录
BASE_DIRECTORY = r'C:\Users\admin\Desktop'  # 修改为你的实际路径


def is_image_file(filename):
    """判断文件是否为图片"""
    extension = os.path.splitext(filename)[1].lower()
    return extension in IMAGE_EXTENSIONS


def contains_images(directory_path):
    """检查目录是否包含至少一张图片"""
    for file in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file)
        if os.path.isfile(file_path) and is_image_file(file):
            return True
    return False


def scan_directories():
    """扫描包含图片的文件夹"""
    folders_with_images = []

    try:
        for item in os.listdir(BASE_DIRECTORY):
            item_path = os.path.join(BASE_DIRECTORY, item)

            if os.path.isdir(item_path) and contains_images(item_path):
                # 收集文件夹中的所有图片
                images = []
                for image_file in os.listdir(item_path):
                    image_path = os.path.join(item_path, image_file)
                    if os.path.isfile(image_path) and is_image_file(image_file):
                        # 直接使用完整的相对路径，避免使用对象
                        relative_path = os.path.join(item, image_file)
                        images.append({
                            'name': image_file,
                            'path': relative_path,
                            'url': f'/api/images/{relative_path}'  # 提供完整URL路径
                        })

                if images:  # 只添加有图片的文件夹
                    folders_with_images.append({
                        'name': item,
                        'path': item,
                        'images': images,
                        'count': len(images)
                    })
    except Exception as e:
        print(f"扫描目录时出错: {e}")

    return folders_with_images


@app.route('/', methods=['GET'])
def index():
    """渲染首页"""
    return render_template('index.html')


@app.route('/api/folders', methods=['GET'])
def get_folders():
    """获取所有包含图片的文件夹及其图片列表"""
    folders = scan_directories()
    return jsonify(folders)


@app.route('/api/images/<path:image_path>', methods=['GET'])
def get_image(image_path):
    """获取指定路径的图片文件"""
    try:
        # 拼接完整路径
        full_path = os.path.join(BASE_DIRECTORY, image_path)

        # 验证路径安全性，防止目录遍历攻击
        requested_path = Path(full_path).resolve()
        base_path = Path(BASE_DIRECTORY).resolve()

        if not str(requested_path).startswith(str(base_path)):
            return jsonify({'error': '无效的路径'}), 403

        # 判断文件是否存在
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return jsonify({'error': '文件不存在', 'path': full_path}), 404

        # 获取文件所在目录和文件名
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)

        # 获取图片的MIME类型
        mimetype, _ = mimetypes.guess_type(full_path)
        if not mimetype:
            mimetype = 'application/octet-stream'

        # 直接从文件所在目录发送文件
        return send_from_directory(directory, filename, mimetype=mimetype)

    except Exception as e:
        return jsonify({'error': str(e), 'path': image_path}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    # 注册MIME类型
    mimetypes.init()
    for ext in IMAGE_EXTENSIONS:
        if ext == '.jpg':
            mimetypes.add_type('image/jpeg', ext)
        elif ext == '.svg':
            mimetypes.add_type('image/svg+xml', ext)
        else:
            mimetypes.add_type(f'image/{ext[1:]}', ext)

    app.run(debug=True, host='0.0.0.0', port=5000)