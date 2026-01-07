# Holmes Test Framework

Holmes Test 是一个通用、配置驱动、插件化的自动化测试框架，支持各种测试场景，目前优先支持Holmes推理引擎测试。

## 目录结构


- `core/`: 核心框架 (Context, Runner, Registry)
- `holmes/`: Holmes测试插件
  - `plugins/`: 插件实现 (Steps, Engines)
- `cases/`: 测试用例定义 (Config files)
- `suites/`: 测试套件 (逻辑分组)
- `plans/`: 测试计划 (执行入口配置)
- `environments/`: 环境配置 (Dockerfile)
- `run.py`: 命令行入口

## 快速开始

### 1. 本地运行

安装依赖：
```bash
pip install -r requirements.txt
```

运行单个 Case：
```bash
python run.py case cases/demo/demo_case.py
```

运行 Test Plan：
```bash
python run.py plan plans/demo_plan.py
```

### 2. Docker 运行

构建镜像：
```bash
docker build -t holmes-test:latest -f environments/base/Dockerfile .
```

在 Docker 中运行 Sample Plan：
```bash
docker run -v $(pwd):/workspace holmes-test:latest plan plans/sample_plan.py
```

## 编写测试

### Case 定义
参考 `cases/demo/demo_case.py`。一个 Case 包含一组配置和一个 Pipeline（步骤列表）。

### Step 定义
参考 `holmes/plugins/steps/common.py`。继承 `BaseStep` 并注册到 `STEPS`。
