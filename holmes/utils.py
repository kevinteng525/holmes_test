
from typing import Dict, List

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
