import logging
from core.interface import BaseStep
from core.context import TestContext
from sample_project.plugins import DEMO_STEPS

logger = logging.getLogger(__name__)

# 注册为 MyEngineCompiler 以匹配 Case 引用
@DEMO_STEPS.register_module(name='MyEngineCompiler')
class Compiler(BaseStep):
    def load_context(self, context: TestContext):
        self.model_path = context.get('model_path')

    def action(self, context: TestContext):
        logger.info("Dummy Compiler running...")
        logger.info(f"Compiling model: {self.model_path}")

    def set_context(self, context: TestContext):
        # 写入编译产物
        context.set('engine_path', self.model_path + '.engine')

# 注册为 MyEngineRunner 以匹配 Case 引用
@DEMO_STEPS.register_module(name='MyEngineRunner')
class Runner(BaseStep):
    def load_context(self, context: TestContext):
        self.engine_path = context.get('engine_path')

    def action(self, context: TestContext):
        logger.info("Dummy Runner inferencing...")
        logger.info(f"Loading engine: {self.engine_path}")

    def set_context(self, context: TestContext):
        # 写入推理结果
        context.set('output_tensor', [0.1, 0.2, 0.3])
