import logging
import os
import xml.etree.ElementTree as ET
from typing import List, Dict
import datetime
from collections import defaultdict
from sample_project.plugins import DEMO_COLLECTORS
from core.interface import BaseCollector
from core.context import TestContext
from core.status import CaseStatus

from core.utils import generate_case_id
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
        errors = sum(1 for r in self.case_results if r.get('status') == CaseStatus.ERROR)
        # 将 UNKNOWN 视为 Skipped
        skipped = sum(1 for r in self.case_results if r.get('status') == CaseStatus.UNKNOWN or r.get('status') == CaseStatus.PENDING)

        logger.info("\n" + "="*50)
        logger.info("PLAN EXECUTION REPORT")
        logger.info("="*50)

        for idx, result in enumerate(self.case_results):
            case_file = result.get('case_file')
            status = result.get('status')
            suite = result.get('suite_path', 'Unknown')

            # 自动生成 Case ID
            case_id = generate_case_id(case_file)

            # 单行显示：ID, Suite, File, Status
            logger.info(f"Case {idx+1}: ID={case_id} | Suite={suite} | File={case_file} | Status=[{status}]")



        logger.info("-" * 50)
        logger.info(f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors} | Skipped: {skipped}")
        logger.info("="*50 + "\n")

        # 导出 JUnit XML (如果配置了 junit_path)
        junit_path = getattr(self, 'junit_path', None)
        if junit_path:
            self.export_junit_xml(junit_path)

    def export_junit_xml(self, output_path):
        """生成 JUnit 格式的 XML 报告"""
        # Root element: testsuites
        plan_name = self.plan_config.get('plan_name', 'Plan Execution Results')
        testsuites = ET.Element("testsuites", name=plan_name)

        # Group results by suite_path
        results_by_suite = defaultdict(list)
        for result in self.case_results:
            suite_path = result.get('suite_path', 'Unknown')
            results_by_suite[suite_path].append(result)

        timestamp = datetime.datetime.now().isoformat()

        for suite_path, suite_results in results_by_suite.items():
            # Calculate stats for this suite
            suite_total = len(suite_results)
            suite_failed = sum(1 for r in suite_results if r.get('status') == CaseStatus.FAILED)
            suite_errors = sum(1 for r in suite_results if r.get('status') == CaseStatus.ERROR)
            suite_skipped = sum(1 for r in suite_results if r.get('status') == CaseStatus.UNKNOWN or r.get('status') == CaseStatus.PENDING)
            suite_duration = sum(r.get('duration', 0.0) for r in suite_results)

            # Suite name (use filename without extension or path)
            suite_name = os.path.basename(suite_path).replace('.py', '') if suite_path != 'Unknown' else 'Unknown Suite'

            testsuite = ET.SubElement(testsuites, "testsuite",
                                      name=suite_name,
                                      tests=str(suite_total),
                                      failures=str(suite_failed),
                                      errors=str(suite_errors),
                                      skipped=str(suite_skipped),
                                      time=f"{suite_duration:.4f}",
                                      timestamp=timestamp)

            for result in suite_results:
                case_file = result.get('case_file')
                status = result.get('status')
                metadata = result.get('metadata', {})
                duration = result.get('duration', 0.0)

                # Retrieve error info captured in runner
                error_msg = result.get('error_message')
                if error_msg is None:
                    error_msg = 'Case Failed'

                error_tb = result.get('error_traceback')
                if error_tb is None:
                    error_tb = ''

                # 自动生成 Case ID
                case_id = generate_case_id(case_file)
                case_name = metadata.get('name', case_file)

                # Classname should be the case file path in dot notation
                # e.g., test/cases/demo/pass_case_1.py -> test.cases.demo.pass_case_1
                if case_file:
                    norm_path = os.path.normpath(case_file)
                    # Remove extension
                    base_path = os.path.splitext(norm_path)[0]
                    classname = base_path.replace(os.sep, '.')
                else:
                    classname = "unknown.case"

                testcase = ET.SubElement(testsuite, "testcase",
                                         name=f"{case_id}: {case_name}",
                                         classname=classname,
                                         time=f"{duration:.4f}")

                if status == CaseStatus.FAILED:
                    failure = ET.SubElement(testcase, "failure", message=str(error_msg))
                    failure.text = f"Status: {status}\nFile: {case_file}\n\nTraceback:\n{error_tb}"
                elif status == CaseStatus.ERROR:
                    error = ET.SubElement(testcase, "error", message=str(error_msg))
                    error.text = f"Status: {status}\nFile: {case_file}\n\nTraceback:\n{error_tb}"
                elif status == CaseStatus.UNKNOWN or status == CaseStatus.PENDING:
                    skipped_elem = ET.SubElement(testcase, "skipped")
                    skipped_elem.text = "Case skipped or status unknown"

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