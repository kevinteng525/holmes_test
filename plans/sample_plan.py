
# 样例测试计划
# 指定了运行环境为 Docker

environment = dict(
    type='docker',
    dockerfile='environments/base/Dockerfile',
    image_tag='holmes-test:latest'
)

global_config = dict(
    target_device='CPU',
    debug=True
)

suites = [
    'suites/demo_suite.py'
]
