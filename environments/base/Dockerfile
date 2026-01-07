
FROM python:3.9-slim

WORKDIR /workspace

# 安装基础依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY core/ core/
COPY holmes/ holmes/
COPY run.py .

# 设置 PYTHONPATH
ENV PYTHONPATH=/workspace

# 默认入口
ENTRYPOINT ["python", "run.py"]
CMD ["--help"]
