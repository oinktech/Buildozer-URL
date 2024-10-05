# 使用 Ubuntu 作为基础镜像
FROM ubuntu:20.04

# 确保非交互式模式
ENV DEBIAN_FRONTEND=noninteractive

# 更新和安装所需的工具
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    python3-pip \
    python3-setuptools \
    python3-dev \
    openjdk-8-jdk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY app.py .
COPY buildozer.spec .
COPY logs/ ./logs/

# 安装 Buildozer 及其依赖项
RUN pip3 install --no-cache-dir buildozer

# 为 Buildozer 准备环境
RUN buildozer init && \
    buildozer android update && \
    buildozer android clean

# 设置环境变量
ENV PATH="/root/.local/bin:${PATH}"

# 运行服务
CMD ["python3", "app.py"]
