import os
import shutil
import subprocess
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 设置日志记录
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(filename='logs/build.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

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

    # 复制 buildozer.spec 文件
    shutil.copy('buildozer.spec', project_dir)

    # 进入项目目录并运行 Docker 构建
    try:
        logging.info('Starting Docker build for APK...')
        result = subprocess.run(
            ['docker', 'build', '-t', 'apk-builder', project_dir],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info('Docker build completed successfully!')
        logging.info(result.stdout)  # 记录输出信息

        # APK 文件的预期路径
        apk_file = os.path.join(project_dir, 'bin', f"{file.filename.split('.')[0]}-0.1-debug.apk")
        if os.path.exists(apk_file):
            return jsonify({'success': 'APK built successfully!', 'apk_url': f'/download/{file.filename.split(".")[0]}-0.1-debug.apk'}), 200
        else:
            logging.error('APK file not found!')
            return jsonify({'error': 'APK file not found!'}), 500
    except subprocess.CalledProcessError as e:
        logging.error(f'Error during Docker build: {str(e)}')
        logging.error('STDOUT: ' + e.stdout)
        logging.error('STDERR: ' + e.stderr)  # 记录错误输出
        return jsonify({'error': 'Failed to build APK', 'details': e.stderr}), 500
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
