
metadata = dict(
    name='report_demo_plan',
    component='holmes'
)
# 全局配置：会注入到所有 Case 的 Context 中
global_config = dict(
    target_device='CPU',
    debug=True,
    project_name='Report Demo'
)

# 执行配置
environment = dict(
    type='vm+docker',
    run_type='vm+docker',
    vm_image="base_vm_image.qcow2",
    docker_id="torch2.6-cuda12.3-ubuntu22.04-py312",
    packages=[
        "PPU_SDK_Torch_Holmes_CUDA12.9.0_Ubuntu2404_PyTorch2.9.0_py312.tar.gz",
    ],
    dependencies=dict(
        packages=[
            "python3.12",
            "python3.12-dev",
        ],
        pypi_packages=[
            "pip==23.1.2",
            "setuptools==67.6.1",
            "wheel==0.40.0",
        ],
    )
)

runtime = dict(
    hw_type='ppu',
    driver='umd',
    setup_driver=True,
    resources=dict(
        cpu=8,
        memory=16,
        ppu=1,
        gpu=0,
    ),
    labels='OAM-810E'
)

config_files = dict(
    cmodel_cfg="environments/holmes/configs/cmodel/default.cfg",
    settings_cfg="environments/holmes/configs/settings/default.cfg",
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
