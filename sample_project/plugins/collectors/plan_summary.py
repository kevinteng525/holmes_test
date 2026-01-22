import logging
import os
import xml.etree.ElementTree as ET
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
    def load_context(self, context: TestContext):
        self.case_results = context.get('case_results', [])
        self.plan_config = context.get('plan_config', {})

    def action(self, context: TestContext):
        total = len(self.case_results)
        passed = sum(1 for r in self.case_results if r.get('status') == CaseStatus.SUCCESS)
        failed = sum(1 for r in self.case_results if r.get('status') == CaseStatus.FAILED)
        unknown = total - passed - failed
        
        logger.info("\n" + "="*50)
        logger.info("PLAN EXECUTION REPORT")
        logger.info("="*50)
        
        for idx, result in enumerate(self.case_results):
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

        # 导出 JUnit XML (如果配置了 junit_path)
        junit_path = getattr(self, 'junit_path', None)
        if junit_path:
            self.export_junit_xml(junit_path, total, passed, failed, unknown)

    def export_junit_xml(self, output_path, total, passed, failed, unknown):
        """生成 JUnit 格式的 XML 报告"""
        testsuites = ET.Element("testsuites")
        # 统计 Errors (这里暂时将 Error 状态计入 failed 或者单独统计，CaseStatus.ERROR)
        errors = sum(1 for r in self.case_results if r.get('status') == CaseStatus.ERROR)

        testsuite = ET.SubElement(testsuites, "testsuite", name="PlanExecution",
                                  tests=str(total), failures=str(failed), errors=str(errors), skipped=str(unknown))

        total_duration = 0.0

        for result in self.case_results:
            case_file = result.get('case_file')
            status = result.get('status')
            suite = result.get('suite_path', 'Unknown')
            metadata = result.get('metadata', {})
            duration = result.get('duration', 0.0)
            total_duration += duration

            case_id = metadata.get('ID', 'N/A')
            case_name = metadata.get('name', case_file)

            # classname 通常对应包名/类名，这里使用 suite 路径代替
            classname = suite.replace('/', '.').replace('.py', '')

            testcase = ET.SubElement(testsuite, "testcase",
                                     name=f"{case_id}: {case_name}",
                                     classname=classname,
                                     time=f"{duration:.4f}")

            if status == CaseStatus.FAILED:
                failure = ET.SubElement(testcase, "failure", message="Case Failed")
                failure.text = f"Status: {status}\nFile: {case_file}"
            elif status == CaseStatus.ERROR:
                 error = ET.SubElement(testcase, "error", message="Case Error")
                 error.text = f"Status: {status}\nFile: {case_file}"

        testsuite.set('time', f"{total_duration:.4f}")

        tree = ET.ElementTree(testsuites)
        try:
            # 确保目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            logger.info(f"JUnit XML report generated at: {output_path}")
        except Exception as e:
            logger.error(f"Failed to generate JUnit XML report: {e}")