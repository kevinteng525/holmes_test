# 设计文档

## 1. 设计目标
构建一套**通用、配置驱动、插件化**的自动化测试底座，通过加载不同的插件包（如“Holmes测试插件包”），实现对不同被测对象的自动化测试。

- **通用核心 (Common Core)**：仅负责调度、配置解析、插件管理和结果收集，不包含具体业务逻辑。
- **业务插件化 (Domain Plugins)**：推理引擎测试逻辑（如 Compile, Infer）全部封装为插件。
- **环境标准化 (Environment as Code)**：内置 Docker 环境管理，确保测试环境一致性。
- **分层管理 (Hierarchy)**：支持 Test Plan -> Test Suite -> Test Case 三级管理体系。

## 2. 整体架构设计

框架分为 **基础设施层**、**核心调度层** 和 **业务插件层**。

```mermaid
graph TD
    subgraph Infrastructure [基础设施层]
        Docker[Docker 环境管理]
        DB[结果数据库]
    end

    subgraph Core [通用核心层]
        PlanRunner[Test Plan Runner]
        SuiteLoader[Suite Loader]
        CaseRunner[Case Pipeline Runner]
        Context[动态 Context (配置+数据)]
        Registry[全局插件注册中心]
    end
    
    subgraph Plugins [业务插件层 (以推理引擎为例)]
        Prepare[数据准备插件]
        Compile[编译插件]
        Infer[推理插件]
        Compare[对比插件]
        Collect[结果收集插件]
    end

    Docker -->|提供运行时| PlanRunner
    PlanRunner -->|解析全局配置| SuiteLoader
    SuiteLoader -->|Label 过滤| CaseRunner
    CaseRunner -->|组装 Pipeline| Plugins
    Plugins -->|读写| Context
```

---

## 3. 核心概念与层级体系

框架引入三层管理结构来满足从 CI/CD 到日常开发的各类需求。

### 3.1 第一层：测试计划 (Test Plan)
**职责**：定义“在什么环境下，跑哪些套件，用什么全局配置”。
- **环境绑定**：指定使用的 Dockerfile 或镜像。
- **全局配置**：定义适用于该计划下所有 Case 的公共参数（如 `target_device='A100'`, `engine_version='v2.0'`）。
- **套件引用**：包含哪些 Test Suite。

### 3.2 第二层：测试套件 (Test Suite)
**职责**：用例的逻辑集合与过滤。
- **Label 机制**：通过 Label（如 `daily`, `smoke`, `ops`）动态筛选要执行的 Case。
- **Case 聚合**：引用具体的 Case 配置文件或目录。

### 3.3 第三层：测试用例 (Test Case)
**职责**：定义具体的执行流水线 (Pipeline)。
- **Step 组装**：通过 Config 编排具体步骤。
- **Context 交互**：步骤间通过 Context 传递数据。

---

## 4. 详细模块设计

### 4.1 增强的上下文 (Enhanced Context)
Context 不仅是数据黑板，更是配置中心。核心层会自动将 `Test Plan` 和 `Test Case` 中的配置合并注入 Context，供 Step 使用。

```python
class TestContext:
    def __init__(self, global_config, case_config):
        # 1. 配置视图 (只读建议)
        # 优先级：Case Config > Global Config
        self.config = merge_config(global_config, case_config)
        
        # 2. 数据黑板 (读写)
        # 用于步骤间传递中间产物，如 model_ir, output_tensor
        self.data = {} 
        
        # 3. 运行时状态
        self.status = "PENDING"
```

**Step 实现示例：**
```python
class MyEngineCompiler(BaseStep):
    def process(self, context: TestContext):
        # 从 Context 配置中灵活读取参数
        flags = context.config.get('compile_flags', '-O3') 
        dump_ir = context.config.get('dump_ir', False)
        
        # 执行逻辑
        model = context.data['model_path']
        # ... compile logic ...
```

### 4.2 环境管理 (Environment Management)
框架仓库根目录下统一管理 Dockerfile。

**目录结构建议：**
```text
/environments
    /holmes:torch2.6-cuda12.3-ubuntu22.04-py310
        Dockerfile
        requirements.txt
    /holmes:torch2.4-cuda12.3-ubuntu22.04-py310
        Dockerfile
```

**运行逻辑：**
Runner 启动时，检查 Test Plan 指定的 environment 名称 -> 查找对应的 Dockerfile -> (构建/拉取)镜像 -> 在容器内启动测试进程。

---

## 5. 配置文件示例

### 5.1 Test Plan 配置 (daily_plan.py)
```python
# 指定运行环境 (对应 environments/cuda11/Dockerfile)
environment = dict(
    type='docker',
    path='environments/cuda11', 
    shm_size='8g'
)

# 全局配置 (将被注入到所有 Case 的 Context 中)
global_config = dict(
    target_device='T4',
    compiler_flags='--use_fast_math'
)

# 包含的套件
suites = [
    'test/suites/resnet_suite.py',
    'test/suites/bert_suite.py'
]
```

### 5.2 Test Suite 配置 (test/suites/resnet_suite.py)
```python
# 扫描路径
case_root = 'test/cases/resnet'

# 过滤策略：只运行带有 'daily' 标签 且 不带有 'flaky' 标签的 case
selector = dict(
    include_labels=['daily'],
    exclude_labels=['flaky']
)
```

### 5.3 Test Case 配置 (test/cases/resnet/resnet50_fp16.py)
```python
# Case 级别的标签定义
labels = ['daily', 'performance', 'vision']

# 具体的执行 Pipeline
pipeline = [
    # 步骤 1: 准备数据
    dict(type='ModelLoader', uri='oss://models/resnet50.onnx'),
    
    # 步骤 2: 编译 (使用 Context 中的 compile_flags)
    dict(type='MyEngineCompiler'), 
    
    # 步骤 3: 推理
    dict(type='MyEngineRunner'),
    
    # 步骤 4: 结果对比
    dict(type='NumericsComparator', rtol=1e-3),

    # 步骤 5: 结果收集 (Console, JSON)
    dict(type='ConsoleCollector'),
    dict(type='JsonResultCollector', output_file='result.json')
]
```

---

## 6. 执行模式与 CLI 设计 (Execution Modes)

框架提供统一的 CLI 入口 `run.py`，支持两种核心运行模式，满足 CI 批量运行和本地调试需求。

### 6.1 计划模式 (Plan Mode) - 用于 CI/CD
执行完整的 Test Plan，自动处理 Docker 环境构建与销毁。

```bash
# 运行 Daily 测试计划
python run.py plan test/plans/daily_plan.py

# 覆盖部分全局变量 (可选)
python run.py plan test/plans/daily_plan.py --options global_config.target_device=A100
```

### 6.2 单例模式 (Case Mode) - 用于本地开发调试
直接运行单个 Case 文件，支持快速验证。

```bash
# 默认在本地环境直接运行（不启动 Docker，适合快速调试逻辑）
python run.py case test/cases/resnet/resnet50_fp16.py

# 指定在 Docker 环境中运行（挂载当前代码）
python run.py case test/cases/resnet/resnet50_fp16.py --env holmes:torch2.6-cuda12.3-ubuntu22.04-py310

# 覆盖 Context 参数
python run.py case test/cases/resnet/resnet50_fp16.py --options compile_flags="-O0 -g"
```

---

## 7. 插件化系统 (Registry)

为了实现通用性，框架核心不包含任何具体业务逻辑，通过 Registry 动态加载。

```python
# 核心定义
STEPS = Registry('steps')
COLLECTORS = Registry('collectors')

# 扩展：推理引擎插件包 (holmes_inference_plugins)
@STEPS.register_module()
class MyEngineCompiler(BaseStep): ...

# 扩展：Web 测试插件包 (holmes_web_plugins)
@STEPS.register_module()
class HttpRequestStep(BaseStep): ...

# 扩展：结果收集插件
@STEPS.register_module() # 注册到 STEPS 以便在 Pipeline 中直接使用
@COLLECTORS.register_module()
class JsonResultCollector(BaseCollector): ...
```

## 8. 总结

本设计通过 **Test Plan -> Suite -> Case** 的三层模型解决了从环境定义到用例执行的完整管理问题，并通过 **Context 配置注入** 机制实现了步骤间的灵活参数传递。框架核心保持通用，配合 **Plugin** 机制，可完美支持推理引擎测试，同时也具备支持未来其他类型测试的能力。