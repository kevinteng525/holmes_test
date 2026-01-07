import time
import logging
from core.interface import BaseStep
from core.context import TestContext
from core.registry import STEPS

logger = logging.getLogger(__name__)

@STEPS.register_module()
class ModelLoader(BaseStep):
    """
    模拟模型加载步骤
    """
    def process(self, context: TestContext):
        uri = getattr(self, 'uri', 'unknown')

        # 从 Context 配置中获取 target_device 和 precision
        target_device = context.config.get('target_device', 'unknown')
        precision = context.config.get('precision', 'unknown')

        logger.info(f"Loading model from {uri} (Target: {target_device}, Precision: {precision})...")
        # 模拟加载耗时
        time.sleep(0.5)
        # 将模型路径写入 Context
        context.set('model_path', '/tmp/mock_model.onnx')
        logger.info("Model loaded.")

@STEPS.register_module()
class NumericsComparator(BaseStep):
    """
    模拟数值对比步骤
    """
    def process(self, context: TestContext):
        rtol = getattr(self, 'rtol', 1e-5)
        logger.info(f"Comparing results with rtol={rtol}...")
        
        output = context.get('output_tensor')
        if output is None:
            raise ValueError("No output_tensor found in context!")
            
        # 模拟对比逻辑
        logger.info(f"Verification passed for output: {output}")

@STEPS.register_module()
class SleepStep(BaseStep):
    """
    调试用的休眠步骤
    """
    def process(self, context: TestContext):
        seconds = getattr(self, 'seconds', 1)
        logger.info(f"Sleeping for {seconds} seconds...")
        time.sleep(seconds)