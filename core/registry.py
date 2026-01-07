
from mmengine.registry import Registry

# 定义核心注册表
# STEPS: 用于注册各种 Pipeline 步骤 (如 ModelLoader, Compiler, Infer)
STEPS = Registry('steps')

# ENGINES: 用于注册推理引擎的特定实现 (如果有更高层的抽象，当前设计主要靠 Steps)
# 暂时保留，以备扩展
ENGINES = Registry('engines')
