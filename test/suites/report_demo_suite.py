
# 测试套件配置：筛选用于演示报告生成的 Case

# Case 文件所在的根目录
case_root = 'test/cases/demo'

# Case 筛选器
selector = dict(
    # 只包含带有 'report_demo' 标签的 Case
    include_labels=['report_demo'],
    
    # 可选：排除带有 'flaky' 标签的 Case
    exclude_labels=['flaky']
)
