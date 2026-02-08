# Holmes Test Framework

Holmes Test 是一个通用、配置驱动、插件化的自动化测试框架，支持各种测试场景，目前优先支持Holmes推理引擎测试。

## 目录结构


- `core/`: 核心框架 (Context, Runner, Registry)
- `sample_project/`: Sample Project测试插件
  - `plugins/`: 插件实现
    - `steps/`: 测试步骤 (Action)
    - `checkers/`: 结果检查 (Verification)
    - `collectors/`: 结果收集 (Logging/Reporting)
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

# 导出为 CSV 文件（同时生成 exec_config YAML 文件）
python run.py list-cases test/plans/demo_plan.py --csv output.csv
```

### CSV 导出说明

导出 CSV 时会自动在同目录下创建 `exec_config` 文件夹，并生成执行配置 YAML 文件：

- `exec_config/default.yaml`: Plan 级别的默认配置
- `exec_config/<suite_name>.yaml`: Suite 级别的配置（如果 Suite 定义了执行配置字段）

**CSV 列说明：**

| 列名 | 说明 |
|------|------|
| `case ID` | 自动生成的 Case ID |
| `name` | Case 名称 |
| `component` | 组件名称（来自 Plan 的 metadata.component） |
| `domain` | 领域名称（来自 Suite 的 metadata.domain） |
| `suite` | Suite 文件路径 |
| `case path` | Case 文件路径 |
| `labels` | Case 标签 |
| `cmd` | 执行命令 |
| `exec_config` | 执行配置 YAML 文件路径 |

**生成的 YAML 文件格式示例：**

```yaml
environment:
  run_at: vm+docker
  base_image: base_vm_image.qcow2
  docker_id: torch2.6-cuda12.3-ubuntu22.04-py312
  packages:
    - PPU_SDK_Torch_Holmes_CUDA12.9.0_Ubuntu2404_PyTorch2.9.0_py312.tar.gz
  dependencies:
    packages:
      - python3.12
      - python3.12-dev
    pypi_packages:
      - pip==23.1.2
      - setuptools==67.6.1
      - wheel==0.40.0
runtime:
  hw_type: ppu
  driver: umd
  setup_driver: true
  resource:
    cpu: 8
    memory: 16
    ppu: 1
    gpu: 0
  labels: OAM-810E
config_files:
  cmodel_cfg: environments/holmes/configs/cmodel/default.cfg
  settings_cfg: environments/holmes/configs/settings/default.cfg
env_file: environments/holmes/envs/default.env
setup_script: environments/holmes/setup_scripts/daily_setup.sh
```

### 2. Docker 运行

构建镜像：
```bash
docker build -t holmes-test:latest -f build/sample_project/Dockerfile .
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

# 4. 可选：Case 级别配置（会覆盖 Suite 和 Plan 级别配置）
environment = dict(
    docker_image="case-specific-image:v1.0"
)
global_config = dict(
    case_specific_setting="value"
)
config_files = dict(
    case_config="path/to/case/config.cfg"
)
env_file = "path/to/case/env.env"
setup_script = "path/to/case/setup.sh"
```

### Suite 定义
参考 `test/suites/demo_suite.py`。一个 Suite 定义了 Case 的筛选规则和可选的 Suite 级别配置。

**示例：**
```python
# 元数据
metadata = dict(
    name='demo_suite',
    domain='codegen'  # 用于 CSV 导出
)

# Case 文件所在的根目录
case_root = 'test/cases/demo'

# Case 筛选器
selector = dict(
    include_labels=['demo'],
    exclude_labels=['flaky']
)

# 可选：Suite 级别配置（会覆盖 Plan 级别配置，但会被 Case 级别配置覆盖）
environment = dict(
    type='vm+docker',
    docker_id="suite-level-docker-id",  # 或使用 docker_image
    dependencies=dict(
        pypi_packages=[
            "demo==67.6.1",
        ],
    )
)
runtime = dict(
    resources=dict(
        cpu=9,
        memory=32,
    ),
)
global_config = dict(
    suite_level_setting="value"
)
config_files = dict(
    settings_cfg="path/to/suite/settings.cfg"
)
env_file = "path/to/suite/env.env"
setup_script = "path/to/suite/setup.sh"
```

### Plan 定义
参考 `test/plans/demo_plan.py`。一个 Plan 定义了要执行的 Suite 列表和全局配置。

**示例：**
```python
# 元数据
metadata = dict(
    name='demo_plan',
    component='holmes'  # 用于 CSV 导出
)

# 运行环境配置
environment = dict(
    type='vm+docker',
    run_type='vm+docker',
    vm_image="base_vm_image.qcow2",
    docker_id="torch2.6-cuda12.3-ubuntu22.04-py312",  # 或使用 docker_image
    packages=[
        "PPU_SDK_Torch_Holmes_CUDA12.9.0_Ubuntu2404_PyTorch2.9.0_py312.tar.gz",
    ],
    dependencies=dict(
        packages=[
            "python3.12",
            "python3.12-dev",
        ],
        pypi_packages=[
            "pip==23.1.2",
            "setuptools==67.6.1",
            "wheel==0.40.0",
        ],
    )
)

# 运行时配置
runtime = dict(
    hw_type='ppu',
    driver='umd',
    setup_driver=True,
    resources=dict(
        cpu=8,
        memory=16,
        ppu=1,
        gpu=0,
    ),
    labels='OAM-810E'
)

# 全局配置
global_config = dict(
    target_device='CPU',
    debug=True
)

# 配置文件
config_files = dict(
    cmodel_cfg="path/to/cmodel.cfg",
    settings_cfg="path/to/settings.cfg"
)

# 环境文件和设置脚本
env_file = "path/to/default.env"
setup_script = "path/to/setup.sh"

# 引用的测试套件列表
suites = [
    'test/suites/demo_suite.py'
]

# Plan 级别的收集器
plan_collectors = [
    dict(type='demo.PlanSummaryCollector', junit_path='report/junit.xml')
]
```

## 配置层次结构

框架支持在 **Case**、**Suite** 和 **Plan** 三个层级定义配置，按照 **Case > Suite > Plan** 的优先级进行合并。

### 支持的配置字段

| 字段 | 类型 | 合并方式 | 说明 |
|------|------|---------|------|
| `metadata` | 字典 | 不合并 | 元数据（name, component, domain 等） |
| `environment` | 字典 | 深度合并 | 运行环境配置（docker_id/docker_image, vm_image, packages, dependencies 等） |
| `runtime` | 字典 | 深度合并 | 运行时配置（hw_type, driver, resources, labels 等） |
| `global_config` | 字典 | 深度合并 | 全局配置，会注入到 TestContext |
| `config_files` | 字典 | 深度合并 | 配置文件路径映射 |
| `env_file` | 字符串 | 简单覆盖 | 环境变量文件路径 |
| `setup_script` | 字符串 | 简单覆盖 | 设置脚本路径 |

### environment 字段说明

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `type` / `run_type` | 字符串 | 运行类型（如 `vm+docker`） |
| `vm_image` | 字符串 | VM 镜像名称 |
| `docker_id` | 字符串 | Docker 镜像 ID（与 docker_image 二选一，优先使用） |
| `docker_image` | 字符串 | Docker 镜像完整路径 |
| `packages` | 数组 | 需要安装的软件包列表 |
| `dependencies` | 字典 | 依赖配置，包含 `packages` 和 `pypi_packages` |

### runtime 字段说明

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `hw_type` | 字符串 | 硬件类型（如 `ppu`） |
| `driver` | 字符串 | 驱动类型（如 `umd`） |
| `setup_driver` | 布尔值 | 是否设置驱动 |
| `resources` | 字典 | 资源配置（cpu, memory, ppu, gpu） |
| `labels` | 字符串 | 标签（如 `OAM-810E`） |

### 合并规则

- **字典类型**（`environment`, `global_config`, `config_files`）：采用深度合并，Plan → Suite → Case，后者覆盖前者的同名键
- **字符串类型**（`env_file`, `setup_script`）：采用简单覆盖，优先使用高优先级层级的值

### 示例

假设有以下配置：

**Plan 级别：**
```python
environment = dict(docker_image="plan-image:v1", vm_image="base.qcow2")
global_config = dict(debug=True, project_name="Demo")
```

**Suite 级别：**
```python
environment = dict(docker_image="suite-image:v2")
global_config = dict(debug=False, suite_setting="value")
```

**Case 级别：**
```python
environment = dict(case_field="case_value")
global_config = dict(case_setting="from_case")
```

**合并结果：**
```python
environment = dict(
    docker_image="suite-image:v2",  # Suite 覆盖 Plan
    vm_image="base.qcow2",          # 来自 Plan
    case_field="case_value"         # 来自 Case
)
global_config = dict(
    debug=False,                    # Suite 覆盖 Plan
    project_name="Demo",            # 来自 Plan
    suite_setting="value",          # 来自 Suite
    case_setting="from_case"        # 来自 Case
)
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
    
    def load_context(self, context: TestContext):
        # 可选：从 Context 读取数据
        self.data = context.get('key')

    def action(self, context: TestContext):
        # 必需：核心处理逻辑
        # 从配置获取参数，默认为 'default'
        param = getattr(self, 'param', 'default')
        logger.info(f"Processing data: {self.data} with param: {param}")
        self.result = 'done'

    def set_context(self, context: TestContext):
        # 可选：向 Context 写入结果
        context.set('result', self.result)
```

### 2. Checker 开发

适用于结果验证步骤，框架会自动将其状态重置为 PENDING 并在失败时标记 Case 为 FAILED。

```python
from core.interface import BaseChecker
from core.context import TestContext
from core.registry import CHECKERS

@CHECKERS.register_module()
class MyChecker(BaseChecker):
    def action(self, context: TestContext):
        # 验证逻辑
        # 注意：BaseChecker 会自动在 process 中重置状态为 PENDING
        if not context.get('result'):
            raise RuntimeError("Result check failed!")
```

### 3. 带 Scope 的 Step 开发

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
    def action(self, context: TestContext):
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

### 4. 多级 Scope 开发

框架支持任意深度的 Scope 层级（如 Root -> Parent -> Child）。

**定义多级 Registry:**

```python
# 1. Root Registry (Global)
from core.registry import STEPS

# 2. Parent Registry (Domain)
# scope='demo'
DEMO_STEPS = Registry('demo_steps', scope='demo', parent=STEPS)

# 3. Child Registry (Custom)
# scope='custom'
CUSTOM_STEPS = Registry('custom_steps', scope='custom', parent=DEMO_STEPS)
```

**注册与引用:**

```python
# 注册到 Child Registry
@CUSTOM_STEPS.register_module()
class SpecialRunner(BaseStep): ...
```

在 Case 配置中，支持自动向上查找或显式指定 Scope：

```python
pipeline = [
    # 方式 A: 显式指定 Scope (推荐)
    dict(type='custom.SpecialRunner'),
    
    # 方式 B: 自动向上查找 (如果 Child 中没有，会去 Parent 找)
    dict(type='demo.Compiler'),
]
```