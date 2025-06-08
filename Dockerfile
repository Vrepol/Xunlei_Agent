# 使用适用于树莓派 ARM 架构的 Python 镜像
FROM docker.1ms.run/python:3.9-slim-bullseye

# 避免交互模式
ENV DEBIAN_FRONTEND=noninteractive

# ---- 1) 接收 build-arg 并赋给 ENV ----
ARG HTTP_PROXY
ARG HTTPS_PROXY
# 如果想要用 socks，就再加 ARG ALL_PROXY
ENV http_proxy=$HTTP_PROXY
ENV https_proxy=$HTTPS_PROXY
# ENV all_proxy=$ALL_PROXY   #若你确实要 socks5，pip 原生不支持，需要其他工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      chromium \
      chromium-driver \
      xvfb \
      fonts-liberation \
      && rm -rf /var/lib/apt/lists/*
# ---- 2) 拷贝代码并安装依赖 ----
COPY . /app
WORKDIR /app

# 这里要求你在 /app 下有一个 requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

EXPOSE 7862

CMD ["python", "./backend/app.py"]
