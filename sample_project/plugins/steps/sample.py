import time
import logging
from core.interface import BaseStep
from core.context import TestContext
from sample_project.plugins import DEMO_STEPS
from core.status import CaseStatus

logger = logging.getLogger(__name__)

@DEMO_STEPS.register_module()
class ModelLoader(BaseStep):
    """
    模拟模型加载步骤
    """

    def load_context(self, context: TestContext):
        # 从 Context 配置中获取 target_device 和 precision
        self.target_device = context.config.get('target_device', 'unknown')
        self.precision = context.config.get('precision', 'unknown')

    def action(self, context: TestContext):
        uri = getattr(self, 'uri', 'unknown')
        logger.info(f"Loading model from {uri} (Target: {self.target_device}, Precision: {self.precision})...")
        # 模拟加载耗时
        time.sleep(0.5)
        logger.info("Model loaded.")

    def set_context(self, context: TestContext):
        # 将模型路径写入 Context
        context.set('model_path', '/tmp/mock_model.onnx')
        model_attr = dict(target_device=self.target_device, precision=self.precision)
        context.set('model_attr', model_attr)

@DEMO_STEPS.register_module()
class SleepStep(BaseStep):
    """
    调试用的休眠步骤
    """

    def action(self, context: TestContext):
        seconds = getattr(self, 'seconds', 1)
        logger.info(f"Sleeping for {seconds} seconds...")
        time.sleep(seconds)