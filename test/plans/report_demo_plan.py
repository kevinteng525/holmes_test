
# 测试计划配置：运行演示 Case 并生成报告

# 运行环境配置（可选）
# 如果需要在 Docker 中运行，取消注释以下部分
environment = dict(
    type='vm+docker',
    vm_image="base_vm_image.qcow2",
    docker_image="art.eng.t-head.cn/ptgai-docker_ai-tmp/holmes:torch2.6-cuda12.3-ubuntu22.04-py310",
)

# 全局配置：会注入到所有 Case 的 Context 中
global_config = dict(
    target_device='CPU',
    debug=True,
    project_name='Report Demo'
)
config_files = dict(
    cmodel="environments/holmes/configs/cmodel/default.cfg",
    settings="environments/holmes/configs/settings/default.cfg",
)
env_file = "environments/holmes/envs/default.env"
setup_script = "environments/holmes/setup_scripts/daily_setup.sh"
# 引用的测试套件列表
suites = [
    'test/suites/report_demo_suite.py',
    'test/suites/demo_suite.py'
]

# Plan 级别的收集器
plan_collectors = [
    dict(type='demo.PlanSummaryCollector', junit_path='report/junit.xml')
]
