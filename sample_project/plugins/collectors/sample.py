import json
import logging
from core.interface import BaseCollector
from core.context import TestContext
from sample_project.plugins import DEMO_STEPS, DEMO_COLLECTORS
from core.status import CaseStatus

logger = logging.getLogger(__name__)

@DEMO_STEPS.register_module()
@DEMO_COLLECTORS.register_module()
class ConsoleCollector(BaseCollector):
    """
    将测试结果输出到控制台的收集器
    """
    def load_context(self, context: TestContext):
        self.status = context.status
        self.data = getattr(context, 'data', {})

    def action(self, context: TestContext):
        logger.info("=" * 30)
        logger.info("Test Results Summary")
        logger.info("=" * 30)
        logger.info(f"Status: {self.status}")

        # 打印 context 中所有非私有属性的数据
        for k, v in self.data.items():
            if not k.startswith('_'):
                logger.info(f"{k}: {v}")

        logger.info("=" * 30)

@DEMO_STEPS.register_module()
@DEMO_COLLECTORS.register_module()
class JsonResultCollector(BaseCollector):
    """
    将测试结果保存为 JSON 文件的收集器
    """
    def load_context(self, context: TestContext):
        self.status = context.status
        self.data = getattr(context, 'data', {})

    def action(self, context: TestContext):
        output_file = getattr(self, 'output_file', 'result.json')
        logger.info(f"Collecting results to {output_file}...")

        # 确保 status 转换为字符串
        status_str = self.status.value if isinstance(self.status, CaseStatus) else str(self.status)

        result_data = {
            "status": status_str,
            "data": {k: str(v) for k, v in self.data.items() if not k.startswith('_')}
        }

        try:
            with open(output_file, 'w') as f:
                json.dump(result_data, f, indent=4)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results to {output_file}: {e}")