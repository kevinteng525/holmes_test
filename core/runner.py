
import logging
from typing import List, Dict
from mmengine.config import Config
from core.registry import STEPS
from core.context import TestContext

logger = logging.getLogger(__name__)

class CaseRunner:
    """
    负责执行单个 Case 的 Pipeline
    """
    def __init__(self, context: TestContext):
        self.context = context

    def run(self, pipeline_cfg: List[Dict]):
        logger.info(f"Starting Case Execution...")
        for step_cfg in pipeline_cfg:
            try:
                # 使用 Registry 构建 Step 实例
                # step_cfg 必须包含 'type' 字段
                step_type = step_cfg.get('type')
                logger.info(f"Running Step: {step_type}")
                
                step = STEPS.build(step_cfg)
                step.process(self.context)
            except Exception as e:
                logger.error(f"Step {step_cfg.get('type')} failed: {e}")
                self.context.status = "FAILED"
                raise e
        
        self.context.status = "SUCCESS"
        logger.info("Case Execution Completed Successfully.")

from core.loader import SuiteLoader

class PlanRunner:
    """
    负责执行整个 Test Plan
    """
    def __init__(self, plan_cfg: Config):
        self.plan_cfg = plan_cfg
        self.global_config = plan_cfg.get('global_config', {})
        self.suites = plan_cfg.get('suites', [])

    def run(self) -> bool:
        """
        执行 Plan
        :return: True if all cases passed, False otherwise
        """
        total_cases = 0
        failed_cases = 0

        logger.info(f"Starting Plan Execution with {len(self.suites)} suites...")

        for suite_path in self.suites:
            logger.info(f"Processing Suite: {suite_path}")
            # 使用 Loader 加载 Case 列表
            try:
                case_files = SuiteLoader.load_cases_from_suite(suite_path)
            except Exception as e:
                logger.error(f"Failed to load suite {suite_path}: {e}")
                continue

            for case_file in case_files:
                logger.info(f"  -> Running Case: {case_file}")
                try:
                    case_cfg = Config.fromfile(case_file)
                    # 注入 Global Config
                    ctx = TestContext(global_config=self.global_config, case_config=case_cfg)
                    runner = CaseRunner(ctx)
                    runner.run(case_cfg.pipeline)
                    total_cases += 1
                except Exception as e:
                    logger.error(f"  -> Case Failed: {case_file} | Error: {e}")
                    failed_cases += 1

        logger.info("="*30)
        logger.info(f"Plan Execution Summary: Total {total_cases}, Failed {failed_cases}")
        return failed_cases == 0
