
metadata = dict(
    name='report_demo_suite',
    domain='native'
)
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

global_config = dict(
    # 覆盖 Plan 的 debug 配置
    debug=False,
    # 新增 Suite 级别的字段
    suite_level_setting="from_suite"
)

# 执行配置
# Suite 级别配置（会覆盖 Plan 级别配置）
environment = dict(
    # 覆盖 Plan 的 docker_image
    docker_image="art.eng.t-head.cn/ptgai-docker_ai-tmp/holmes:torch2.6-cuda12.3-ubuntu22.04-py310",
)


config_files = dict(
    # 覆盖 Plan 的 settings 配置
    settings_cfg="environments/suite_level/dynamo.cfg",
    # 新增 Suite 级别的配置文件
    suite_config_cfg="environments/suite_level/dynamo.cfg"
)

# Suite 级别的 env_file（会覆盖 Plan 级别）
env_file = "environments/suite_level/dynamo.env"

setup_script = "environments/holmes/setup_scripts/dynamo_setup.sh"
