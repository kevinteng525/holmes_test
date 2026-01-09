# Holmes Test Framework

Holmes Test 是一个通用、配置驱动、插件化的自动化测试框架，支持各种测试场景，目前优先支持Holmes推理引擎测试。

## 目录结构


- `core/`: 核心框架 (Context, Runner, Registry)
- `sample_project/`: Sample Project测试插件
  - `plugins/`: 插件实现 (Steps, Engines)
- `test/`: 具体测试
  - `cases/`: 测试用例 (Config files)
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
python run.py case test/cases/demo/demo_case.py
```

运行 Test Plan：
```bash
python run.py plan test/plans/demo_plan.py
```

列出 Plan 中的 Cases：
```bash
python run.py list-cases test/plans/demo_plan.py
```

### 2. Docker 运行

构建镜像：
```bash
docker build -t holmes-test:latest -f environments/base/Dockerfile .
```

在 Docker 中运行 Sample Plan：
```bash
docker run -v $(pwd):/workspace holmes-test:latest plan test/plans/sample_plan.py
```

## 编写测试

### Case 定义
参考 `test/cases/demo/demo_case.py`。一个 Case 包含一组配置（Metadata, Labels）和一个 Pipeline（步骤列表）。

**示例：**
```python
# 1. 定义元数据 (必需)
metadata = dict(
    name='Demo Test Case',
    ID='CASE-001',
    creator='YourName'
)

# 2. 定义标签 (用于过滤)
labels = ['demo', 'daily']

# 3. 定义执行流水线
pipeline = [
    dict(type='demo.ModelLoader', uri='oss://bucket/model.onnx'),
    dict(type='demo.MyEngineRunner'),
    dict(type='demo.NumericsComparator', rtol=1e-3)
]
```

## 插件开发指南

### 1. 普通 Step 开发

适用于通用的测试步骤。

**实现与注册：**
```python
import logging
from core.interface import BaseStep
from core.context import TestContext
from core.registry import STEPS

logger = logging.getLogger(__name__)

@STEPS.register_module()
class MyStep(BaseStep):
    """自定义步骤"""
    
    def process(self, context: TestContext):
        # 从配置获取参数，默认为 'default'
        param = getattr(self, 'param', 'default')
        
        # 读取/写入上下文数据
        data = context.get('key')
        logger.info(f"Processing data: {data} with param: {param}")
        
        context.set('result', 'done')
```

**Pipeline 引用：**
```python
dict(type='MyStep', param='value')
```

### 2. 带 Scope 的 Step 开发

适用于特定引擎或模块的插件（如 TensorRT, ONNXRuntime），通过 Scope（命名空间）隔离，避免命名冲突。

**定义 Child Registry (Scope):**
通常在插件包的 `__init__.py` 中定义。

```python
from mmengine.registry import Registry
from core.registry import STEPS  # 导入全局 STEPS 作为父注册表

# 定义属于 'demo' scope 的注册表，parent 指向 STEPS
DEMO_STEPS = Registry('demo_steps', scope='demo', parent=STEPS)
```

**注册插件:**
使用自定义的 Registry 进行注册。

```python
from sample_project.plugins import DEMO_STEPS

@DEMO_STEPS.register_module()
class Compiler(BaseStep):
    def process(self, context: TestContext):
        # ...
        pass
```

**Pipeline 引用:**
使用 `scope.ClassName` 的格式进行引用。

```python
# 引用 demo scope 下的 Compiler 类
dict(type='demo.Compiler', param='value')
```

**注意：** Scope 名称对大小写敏感，请确保 Config 中的 Scope 前缀与 `Registry(scope='...')` 定义的一致。