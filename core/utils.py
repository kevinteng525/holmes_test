import os
import hashlib
from typing import Dict, List


def generate_case_id(case_file: str, case_roots: List[str] = None) -> str:
    """
    根据 Case 文件路径自动生成 Case ID

    Args:
        case_file: Case 文件路径，如 'test/cases/demo/pass_case_1.py'
        case_roots: Case 根目录列表，按优先级排序，默认为 ['v2/test/cases', 'test/cases']
                    优先匹配列表中靠前的根目录

    Returns:
        生成的 Case ID，格式为 '前缀-xxxxxxxxxxxxxxxx'，如 'demo-a1b2c3d4e5f6g7h8'
        前缀为目录路径（用 '-' 连接），后缀为文件名的 16 位哈希值
    """
    if not case_file:
        return 'unknown'

    if case_roots is None:
        case_roots = ['v2/test/cases', 'test/cases']

    # 规范化路径
    case_file = os.path.normpath(case_file)

    # 尝试匹配每个 case_root，优先匹配靠前的根目录
    relative_path = case_file
    for case_root in case_roots:
        normalized_root = os.path.normpath(case_root)
        if case_file.startswith(normalized_root):
            relative_path = case_file[len(normalized_root):].lstrip(os.sep)
            break

    # 分离目录和文件名
    dir_path = os.path.dirname(relative_path)
    file_name = os.path.basename(relative_path)

    # 移除 .py 扩展名
    if file_name.endswith('.py'):
        file_name = file_name[:-3]

    # 生成文件名的 8 位哈希值（使用 MD5）
    file_hash = hashlib.md5(file_name.encode('utf-8')).hexdigest()[:16]

    # 构建前缀（目录路径用 '-' 连接）
    if dir_path:
        prefix = dir_path.replace(os.sep, '-')
        case_id = f"{prefix}-{file_hash}"
    else:
        case_id = file_hash

    return case_id


def parse_options(options_str: str) -> Dict:
    """
    解析命令行传入的 options 字符串，格式为 "key1=value1 key2=value2"
    """
    if not options_str:
        return {}
    
    options = {}
    # 支持空格分隔的多个键值对
    # 注意：这里简单实现，不支持 value 中包含空格的情况
    pairs = options_str.split(' ')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            # 尝试转换数值类型
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass
            options[key] = value
    return options
