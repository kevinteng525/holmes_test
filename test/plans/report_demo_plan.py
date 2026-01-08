
# 测试计划配置：运行演示 Case 并生成报告

# 运行环境配置（可选）
# 如果需要在 Docker 中运行，取消注释以下部分
# environment = dict(
#     type='docker',
#     dockerfile='environments/base/Dockerfile',
#     image_tag='holmes-test:latest'
# )

# 全局配置：会注入到所有 Case 的 Context 中
global_config = dict(
    target_device='CPU',
    debug=True,
    project_name='Report Demo'
)

# 引用的测试套件列表
suites = [
    'test/suites/report_demo_suite.py',
    'test/suites/demo_suite.py'
]

# Plan 级别的收集器
plan_collectors = [
    dict(type='PlanSummaryCollector')
]
