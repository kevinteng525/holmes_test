
from typing import Dict, Any, Optional
from mmengine.config import Config
from core.status import CaseStatus

class TestContext:
    """
    测试上下文，用于在 Pipeline 步骤间传递配置和数据。
    """
    def __init__(self, global_config: Optional[Dict] = None, case_config: Optional[Dict] = None):
        # 1. 配置合并：Case 配置优先于 Global 配置
        # 注意：这里简单的字典合并可能不够，mmengine.Config 提供了更强大的合并功能
        self._raw_global_config = global_config or {}
        self._raw_case_config = case_config or {}
        
        # 将字典转换为 Config 对象以便于访问
        self.config = Config(self._merge_configs(self._raw_global_config, self._raw_case_config))
        
        # 2. 数据黑板：用于步骤间传递中间产物 (如 model_path, input_tensor, output_tensor)
        self.data: Dict[str, Any] = {}
        
        # 3. 运行时状态
        self.status = CaseStatus.PENDING

    def _merge_configs(self, global_cfg: Dict, case_cfg: Dict) -> Dict:
        """简单的配置合并逻辑，Case 覆盖 Global"""
        # 将 Config 对象转换为普通字典，避免类型不兼容问题
        merged = dict(global_cfg).copy()
        merged.update(dict(case_cfg))
        return merged

    def get(self, key: str, default: Any = None) -> Any:
        """从 data 中获取数据的快捷方法"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """向 data 中写入数据的快捷方法"""
        self.data[key] = value
