from mmengine.registry import Registry
from core.registry import STEPS, COLLECTORS

# 定义统一的 demo scope，父注册表指向全局 STEPS/COLLECTORS
# 这样在 Case 中可以使用 'demo.ClassName' 进行引用
DEMO_STEPS = Registry('demo_steps', scope='demo', parent=STEPS)
DEMO_COLLECTORS = Registry('demo_collectors', scope='demo', parent=COLLECTORS)
