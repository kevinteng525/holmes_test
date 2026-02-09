import logging
from typing import List, Dict
from mmengine.config import Config
from core.registry import STEPS, COLLECTORS, CHECKERS
from core.interface import BaseCollector
from core.context import TestContext
from core.status import CaseStatus
from core.utils import generate_case_id
import traceback
import time

logger = logging.getLogger(__name__)

class CaseRunner:
    """
    负责执行单个 Case 的 Pipeline
    """
    def __init__(self, context: TestContext):
        self.context = context

    def run(self, pipeline_cfg: List[Dict]):
        logger.info(f"Starting Case Execution...")
        execution_failed = False
        exception_to_raise = None

        for step_cfg in pipeline_cfg:
            step_type = step_cfg.get('type')

            # 构建 Step
            try:
                # 遍历注册表列表查找并构建 Step
                step = None
                registries = [STEPS, CHECKERS, COLLECTORS]
                for registry in registries:
                    if step_type in registry:
                        step = registry.build(step_cfg)
                        break

                # 如果都找不到，尝试默认从 STEPS 构建以抛出明确错误
                if step is None:
                    step = STEPS.build(step_cfg)

            except Exception as e:
                logger.error(f"Failed to build step {step_type}: {e}")
                execution_failed = True
                exception_to_raise = e
                self.context.status = CaseStatus.ERROR # 构建失败视为 ERROR
                break # 构建都失败了，后续无法继续

            is_collector = isinstance(step, BaseCollector)

            # 如果之前的步骤失败了，且当前步骤不是 Collector，则跳过
            if execution_failed and not is_collector:
                logger.warning(f"Skipping Step: {step_type} due to previous failure.")
                continue

            # 如果尚未失败，或者当前是 Collector，则执行
            try:
                # 在执行 Collector 之前，更新 Status
                if is_collector:
                    if execution_failed:
                        self.context.status = CaseStatus.FAILED
                    elif self.context.status == CaseStatus.PENDING:
                         # 如果还没失败且状态仍为 PENDING，说明目前为止是成功的
                         pass

                logger.info(f"Running Step: {step_type}")
                step.process(self.context)

                # 如果 Step 执行后状态变为失败，且不是 Collector，则标记执行失败，以跳过后续步骤
                if not is_collector and self.context.status in [CaseStatus.FAILED, CaseStatus.ERROR]:
                    execution_failed = True
                    logger.error(f"Step {step_type} failed with status: {self.context.status}")

            except Exception as e:
                logger.error(f"Step {step_cfg.get('type')} failed: {e}")
                traceback.print_exception(type(e), e, e.__traceback__)
                # 如果是 Collector 失败，记录日志但不中断后续 Collector（通常 Collector 失败不应影响主流程状态，但需记录）
                # 如果是普通 Step 失败，标记失败
                if not is_collector:
                    execution_failed = True
                    exception_to_raise = e
                    self.context.status = CaseStatus.FAILED
                else:
                    logger.error(f"Collector {step_type} failed, but continuing...")

        if not execution_failed:
             # 如果状态仍然是 PENDING，说明没有步骤显式设置状态，默认为 SUCCESS
             if self.context.status == CaseStatus.PENDING:
                 self.context.status = CaseStatus.SUCCESS
             logger.info("Case Execution Completed Successfully.")
        else:
             logger.error("Case Execution Failed.")
             if exception_to_raise:
                 raise exception_to_raise

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
        results = [] # 收集所有 case 的结果

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

                # 预先定义 case_result，确保即使加载配置失败也能记录基本信息
                case_result = {
                    'case_file': case_file,
                    'suite_path': suite_path,
                    'metadata': {},
                    'status': CaseStatus.UNKNOWN,
                    'context': None,
                    'error_message': None,
                    'error_traceback': None
                }

                try:
                    case_cfg = Config.fromfile(case_file)

                    # 提取 Metadata (直接从配置字典中读取)
                    case_result['metadata'] = case_cfg.get('metadata', {})

                    # 注入 Global Config 和 Case ID
                    ctx = TestContext(global_config=self.global_config, case_config=case_cfg)
                    auto_case_id = generate_case_id(case_file)
                    ctx.set('case_id', auto_case_id)
                    ctx.set('case_file', case_file)
                    runner = CaseRunner(ctx)

                    start_time = time.time()
                    try:
                        runner.run(case_cfg.pipeline)
                    finally:
                        case_result['duration'] = time.time() - start_time

                    # 记录成功结果
                    case_result['status'] = ctx.status
                    case_result['context'] = ctx

                    # 如果状态是失败但没有抛出异常（例如 Checker 设置了 FAILED），补充错误信息
                    if ctx.status in [CaseStatus.FAILED, CaseStatus.ERROR]:
                        failed_cases += 1 # 确保失败计数正确
                        if case_result['error_message'] is None:
                            case_result['error_message'] = f"Case finished with status {ctx.status} but no exception was raised."
                            case_result['error_traceback'] = "No traceback available. The case status was set to FAILED/ERROR during execution."

                except Exception as e:
                    logger.error(f"  -> Case Failed: {case_file} | Error: {e}")
                    failed_cases += 1
                    # 记录失败结果
                    case_result['status'] = CaseStatus.FAILED
                    case_result['error_message'] = str(e)
                    case_result['error_traceback'] = traceback.format_exc()

                    # ctx 可能在 runner.run 中已经创建，尝试获取
                    # 注意：如果 Config.fromfile 失败，ctx 可能不存在
                    # 这里简单处理，如果 ctx 存在则记录
                    if 'ctx' in locals():
                         case_result['context'] = ctx
                finally:
                    if 'duration' not in case_result:
                        case_result['duration'] = 0.0
                    total_cases += 1
                    results.append(case_result)

        # 执行 Plan 级别的 Collectors
        self._run_plan_collectors(results)

        logger.info("="*30)
        logger.info(f"Plan Execution Summary: Total {total_cases}, Failed {failed_cases}")
        return failed_cases == 0

    def _run_plan_collectors(self, results: List[Dict]):
        """
        运行 Plan 级别的 Collectors
        """
        plan_collectors_cfg = self.plan_cfg.get('plan_collectors', [])
        if not plan_collectors_cfg:
            return

        logger.info("Running Plan Collectors...")
        # 创建一个临时的 Context 用于 Plan Collector，包含所有 Case 的结果
        plan_context = TestContext(global_config=self.global_config)
        plan_context.set('case_results', results)
        plan_context.set('plan_config', self.plan_cfg)

        for collector_cfg in plan_collectors_cfg:
            try:
                collector_type = collector_cfg.get('type')
                logger.info(f"Running Plan Collector: {collector_type}")

                # 遍历注册表列表查找并构建 Collector
                collector = None
                registries = [COLLECTORS, STEPS]
                for registry in registries:
                    if collector_type in registry:
                        collector = registry.build(collector_cfg)
                        break

                if collector is None:
                    collector = STEPS.build(collector_cfg)

                collector.process(plan_context)
            except Exception as e:
                logger.error(f"Plan Collector {collector_cfg.get('type')} failed: {e}")