from abc import ABC, abstractmethod
from core.context import TestContext
from core.status import CaseStatus

class BaseStep(ABC):
    """
    所有测试步骤的基类。
    """
    def __init__(self, **kwargs):
        # 允许步骤在初始化时接收特定参数
        for k, v in kwargs.items():
            setattr(self, k, v)

    def process(self, context: TestContext):
        """
        模板方法：按顺序执行 load_context, action, set_context
        """
        self.load_context(context)
        self.action(context)
        self.set_context(context)

    def load_context(self, context: TestContext):
        """
        从上下文读取数据，子类可覆盖
        """
        pass

    def set_context(self, context: TestContext):
        """
        向上下文写入数据，子类可覆盖
        """
        pass

    @abstractmethod
    def action(self, context: TestContext):
        """
        核心处理逻辑，子类必须实现。
        :param context: 测试上下文，包含配置和中间数据
        """
        pass

class BaseChecker(BaseStep):
    """
    所有检查器的基类。
    强制将 Context 状态初始化为 PENDING。
    """
    def process(self, context: TestContext):
        # 强制设置初始状态为 PENDING
        context.status = CaseStatus.PENDING
        super().process(context)

class BaseCollector(BaseStep):
    """
    所有结果收集器的基类。
    继承自 BaseStep，使其可以直接作为 Pipeline 的一部分运行。
    """
    pass