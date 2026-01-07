
from abc import ABC, abstractmethod
from core.context import TestContext

class BaseStep(ABC):
    """
    所有测试步骤的基类。
    """
    def __init__(self, **kwargs):
        # 允许步骤在初始化时接收特定参数
        for k, v in kwargs.items():
            setattr(self, k, v)

    @abstractmethod
    def process(self, context: TestContext):
        """
        核心处理逻辑，子类必须实现。
        :param context: 测试上下文，包含配置和中间数据
        """
        pass


class BaseCollector(BaseStep):
    """
    所有结果收集器的基类。
    继承自 BaseStep，使其可以直接作为 Pipeline 的一部分运行。
    """
    @abstractmethod
    def collect(self, context: TestContext):
        """
        收集结果的具体实现。
        """
        pass

    def process(self, context: TestContext):
        """
        统一实现 process 方法，调用 collect。
        """
        self.collect(context)
