from mmengine.registry import Registry
from core.registry import STEPS, COLLECTORS, CHECKERS

# 定义统一的 demo scope，父注册表指向全局 STEPS/COLLECTORS
# 这样在 Case 中可以使用 'demo.ClassName' 进行引用
DEMO_STEPS = Registry('demo_steps', scope='demo', parent=STEPS)
DEMO_CHECKERS = Registry('demo_checkers', scope='demo', parent=CHECKERS)
DEMO_COLLECTORS = Registry('demo_collectors', scope='demo', parent=COLLECTORS)

# 自动导入所有插件模块以触发注册
from .steps import sample, dummy, my_engine
from .checkers import sample
from .collectors import sample, plan_summary