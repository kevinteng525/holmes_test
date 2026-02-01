metadata = dict(
    name='Demo passed Test1',
    ID='CASE-003',
    creator='tengkang.tk@alibaba-inc.com'
)
labels = ['report_demo']

pipeline = [
    dict(type='demo.ModelLoader', uri='oss://bucket/resnet50.onnx'),
    dict(type='demo.DummyCompiler',
         dump_IR={
             'need_dump': True,
             'pass': ['FusePadConv', 'FuseConvConv']
         }),
    dict(type='demo.DummyRunner'),
    dict(type='demo.NumericsComparator', rtol=1e-3),
    dict(type='demo.ConsoleCollector'),
    dict(type='demo.JsonResultCollector', output_file='pass_case_1_result.json')
]

precision = 'fp32'

# Case 级别配置（会覆盖 Suite 和 Plan 级别配置）
environment = dict(
    # 覆盖 Suite 的 docker_image
    docker_image="case-level-docker-image:v2.0",
    # 新增 Case 级别的字段
    case_specific_field="case_value"
)

global_config = dict(
    # 覆盖 Suite 的 suite_level_setting
    suite_level_setting="overridden_by_case",
    # 新增 Case 级别的字段
    case_level_setting="from_case"
)

config_files = dict(
    # 覆盖 Suite 的 suite_config
    suite_config="environments/case_level/case_override.cfg",
    # 新增 Case 级别的配置文件
    case_config="environments/case_level/case.cfg"
)

# Case 级别的 env_file（会覆盖 Suite 和 Plan 级别）
env_file = "environments/case_level/case.env"

# Case 级别的 setup_script
setup_script = "environments/case_level/case_setup.sh"
