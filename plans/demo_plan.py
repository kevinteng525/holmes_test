
environment = dict(
    type='local',  # 简单起见，本地运行
)

global_config = dict(
    target_device='CPU',
    debug=True
)

suites = [
    'suites/demo_suite.py'
]
