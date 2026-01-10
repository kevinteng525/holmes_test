import os
import glob
import logging
from typing import List, Dict
from mmengine.config import Config

logger = logging.getLogger(__name__)

class SuiteLoader:
    """
    负责加载 Test Suite 并扫描包含的 Test Case
    """
    @staticmethod
    def load_cases_from_suite(suite_path: str) -> List[str]:
        """
        解析 Suite 配置文件，返回需要执行的 Case 文件路径列表
        """
        suite_cfg = Config.fromfile(suite_path)
        case_root = suite_cfg.get('case_root', '.')

        # 简单的 glob 扫描，实际可能需要递归
        # 假设 suite_path 是相对于运行目录的
        # 这里需要处理相对路径问题，暂且假设是相对于 case_root

        # 构造搜索模式
        search_pattern = os.path.join(case_root, '**', '*.py')
        all_case_files = glob.glob(search_pattern, recursive=True)

        # 过滤逻辑 (Label 过滤)
        # 这里为了演示，简单过滤掉非 case 文件 (比如 __init__.py)
        valid_cases = []
        selector = suite_cfg.get('selector', {})
        include_labels = set(selector.get('include_labels', []))
        exclude_labels = set(selector.get('exclude_labels', []))

        for case_file in all_case_files:
            if os.path.basename(case_file).startswith('__'):
                continue

            # 读取 Case 配置判断 Label
            try:
                case_cfg = Config.fromfile(case_file)
                case_labels = set(case_cfg.get('labels', []))
                
                # 排除逻辑
                if exclude_labels and not case_labels.isdisjoint(exclude_labels):
                    continue
                
                # 包含逻辑: 如果指定了 include，则必须包含至少一个
                if include_labels and case_labels.isdisjoint(include_labels):
                    continue
                
                valid_cases.append(case_file)
            except Exception as e:
                # 记录详细的加载错误
                logger.warning(f"Failed to load case file: {case_file}. Error: {e}")
                pass
                
        return valid_cases