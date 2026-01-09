import logging
from core.interface import BaseStep
from core.context import TestContext
from sample_project.plugins import DEMO_STEPS

logger = logging.getLogger(__name__)

# 重命名为 DummyCompiler 以避免冲突
@DEMO_STEPS.register_module(name='DummyCompiler')
class Compiler(BaseStep):
    def process(self, context: TestContext):
        logger.info("Dummy Compiler running...")
        dump_ir = getattr(self, 'dump_IR', 'unknown')
        model_path = context.get('model_path')
        model_attr = context.get('model_attr')
        logger.info(f"Compiling model: {model_path}, model_attr: {model_attr}, dump_ir: {dump_ir}")
        # 写入编译产物
        context.set('engine_path', model_path + '.engine')


# 重命名为 DummyRunner 以避免冲突
@DEMO_STEPS.register_module(name='DummyRunner')
class Runner(BaseStep):
    def process(self, context: TestContext):
        logger.info("Dummy Runner inferencing...")
        engine_path = context.get('engine_path')
        logger.info(f"Loading engine: {engine_path}")
        # 写入推理结果
        context.set('output_tensor', [0.1, 0.2, 0.3])