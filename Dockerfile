# 使用官方 Python 镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY app.py .
COPY buildozer.spec .
COPY logs/ ./logs/

# 安装 Buildozer 及其依赖项
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    python3-pip \
    python3-setuptools \
    python3-dev \
    openjdk-8-jdk \
    && pip install --no-cache-dir buildozer

# 设置环境变量
ENV PATH="/root/.local/bin:${PATH}"

# 运行服务
CMD ["python", "app.py"]
