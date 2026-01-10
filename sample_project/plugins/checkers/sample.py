import logging
from core.interface import BaseChecker
from core.context import TestContext
from sample_project.plugins import DEMO_CHECKERS
from core.status import CaseStatus

logger = logging.getLogger(__name__)

@DEMO_CHECKERS.register_module()
class NumericsComparator(BaseChecker):
    """
    模拟数值对比步骤
    """

    def load_context(self, context: TestContext):
        self.output_tensor = context.get('output_tensor')

    def action(self, context: TestContext):
        rtol = getattr(self, 'rtol', 1e-5)
        logger.info(f"Comparing results with rtol={rtol}...")

        if self.output_tensor is None:
            error_msg = "output_tensor not found in context!"
            logger.error(error_msg)
            context.status = CaseStatus.FAILED
            raise RuntimeError(error_msg)

        # 模拟对比逻辑
        logger.info("Numerics comparison passed.")

        # 模拟对比逻辑
        logger.info(f"Verification passed for output: {self.output_tensor}")

    def set_context(self, context: TestContext):
        context.status = CaseStatus.SUCCESS
