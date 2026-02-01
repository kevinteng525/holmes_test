
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

# Suite 级别配置（会覆盖 Plan 级别配置）
environment = dict(
    # 覆盖 Plan 的 docker_image
    docker_image="suite-level-docker-image:v1.0",
    # 新增 Suite 级别的字段
    suite_specific_field="suite_value"
)

global_config = dict(
    # 覆盖 Plan 的 debug 配置
    debug=False,
    # 新增 Suite 级别的字段
    suite_level_setting="from_suite"
)

config_files = dict(
    # 覆盖 Plan 的 settings 配置
    settings="environments/suite_level/settings.cfg",
    # 新增 Suite 级别的配置文件
    suite_config="environments/suite_level/suite.cfg"
)

# Suite 级别的 env_file（会覆盖 Plan 级别）
env_file = "environments/suite_level/suite.env"

setup_script = "environments/holmes/setup_scripts/suite_setup.sh"
