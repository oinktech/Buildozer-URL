import os
import shutil
import subprocess
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 设置日志记录
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(filename='logs/build.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def create_buildozer_spec(project_dir, filename):
    """生成 buildozer.spec 文件"""
    spec_content = f"""
[app]
title = {filename.split('.')[0]}
package.name = {filename.split('.')[0]}
package.domain = org.example
source.dir = .
version = 0.1
requirements = python3,kivy
# (其他配置项可以根据需要添加)

[buildozer]
log_level = 2
"""
    with open(os.path.join(project_dir, 'buildozer.spec'), 'w') as f:
        f.write(spec_content.strip())
    logging.info('Created buildozer.spec file.')

@app.route('/build', methods=['POST'])
def build_apk():
    if 'file' not in request.files:
        logging.error('No file part in the request')
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        logging.error('No selected file')
        return jsonify({'error': 'No selected file'}), 400

    # 创建临时项目目录
    project_dir = '/tmp/buildozer_project'
    os.makedirs(project_dir, exist_ok=True)

    # 保存上传的文件
    file_path = os.path.join(project_dir, file.filename)
    file.save(file_path)
    logging.info(f'Saved file {file.filename} to {project_dir}')

    # 创建并保存 buildozer.spec 文件
    create_buildozer_spec(project_dir, file.filename)

    # 进入项目目录并运行 Buildozer
    os.chdir(project_dir)
    try:
        logging.info('Starting Buildozer...')
        # 加上 --force 参数来避免需要交互式确认
        result = subprocess.run(['buildozer', 'android', 'debug', '--force'], check=True, capture_output=True, text=True)
        logging.info('Build completed successfully!')
        logging.info(result.stdout)  # 记录输出信息

        # 打包完成后返回 APK 文件路径
        apk_file = os.path.join(project_dir, 'bin', f"{file.filename.split('.')[0]}-0.1-debug.apk")
        if os.path.exists(apk_file):
            return jsonify({'success': 'APK built successfully!', 'apk_url': f'/download/{file.filename.split(".")[0]}-0.1-debug.apk'}), 200
        else:
            logging.error('APK file not found!')
            return jsonify({'error': 'APK file not found!'}), 500
    except subprocess.CalledProcessError as e:
        logging.error(f'Error during build: {str(e)}')
        logging.error('stdout: ' + e.stdout)  # 记录标准输出
        logging.error('stderr: ' + e.stderr)  # 记录标准错误
        return jsonify({'error': 'Failed to build APK', 'details': str(e), 'stdout': e.stdout, 'stderr': e.stderr}), 500
    finally:
        # 清理临时文件
        shutil.rmtree(project_dir)
        logging.info(f'Cleaned up temporary directory: {project_dir}')

@app.route('/download/<apk_filename>', methods=['GET'])
def download_apk(apk_filename):
    apk_path = os.path.join('/tmp/buildozer_project/bin', apk_filename)
    if os.path.exists(apk_path):
        return jsonify({'apk_url': f'http://your_render_service_url/downloads/{apk_filename}'}), 200
    else:
        return jsonify({'error': 'APK file not found!'}), 404

@app.route('/admin/logs', methods=['GET'])
def view_logs():
    """查看日志文件"""
    log_file_path = 'logs/build.log'
    if os.path.exists(log_file_path):
        return send_file(log_file_path, as_attachment=False, mimetype='text/plain')
    else:
        return jsonify({'error': 'Log file not found!'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
