from mmengine.registry import Registry
from core.registry import STEPS  # 导入全局 STEPS 作为父注册表

# 定义属于 'tensorrt' scope 的注册表，并将其父节点指向 STEPS
# 这样 STEPS.build() 也能找到 tensorrt 下的模块
DUMMY_STEPS = Registry('dummy_steps', scope='dummy', parent=STEPS)
