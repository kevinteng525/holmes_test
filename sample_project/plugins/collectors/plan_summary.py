
import logging
from typing import List, Dict
from sample_project.plugins import DEMO_COLLECTORS
from core.interface import BaseCollector
from core.context import TestContext
from core.status import CaseStatus

logger = logging.getLogger(__name__)

@DEMO_COLLECTORS.register_module()
class PlanSummaryCollector(BaseCollector):
    """
    Plan 级别的结果收集器，用于汇总并打印所有 Case 的执行结果。
    """
    def collect(self, context: TestContext):
        case_results: List[Dict] = context.get('case_results', [])
        plan_config = context.get('plan_config', {})
        
        total = len(case_results)
        passed = sum(1 for r in case_results if r.get('status') == CaseStatus.SUCCESS)
        failed = sum(1 for r in case_results if r.get('status') == CaseStatus.FAILED)
        unknown = total - passed - failed
        
        logger.info("\n" + "="*50)
        logger.info("PLAN EXECUTION REPORT")
        logger.info("="*50)
        
        for idx, result in enumerate(case_results):
            case_file = result.get('case_file')
            status = result.get('status')
            suite = result.get('suite_path', 'Unknown')
            metadata = result.get('metadata', {})

            case_id = metadata.get('ID', 'N/A')

            # 单行显示：ID, Suite, File, Status
            logger.info(f"Case {idx+1}: ID={case_id} | Suite={suite} | File={case_file} | Status=[{status}]")
            
        logger.info("-" * 50)
        logger.info(f"Total: {total} | Passed: {passed} | Failed: {failed} | Unknown: {unknown}")
        logger.info("="*50 + "\n")
