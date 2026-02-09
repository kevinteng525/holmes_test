import sys
import os
import json
import csv
import logging
import click
import yaml
from mmengine.config import Config
from core.runner import CaseRunner
from core.context import TestContext
from core.env_manager import DockerEnvironment
from core.registry import STEPS

# 重要：注册插件 到 Registry 中，不能删
import sample_project.plugins

# Debug: 打印当前注册的所有步骤，确认 ModelLoader 是否存在
print(f"DEBUG: Registered STEPS keys: {list(STEPS.module_dict.keys())}")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
logger = logging.getLogger('HolmesCLI')

@click.group()
def cli():
    """Holmes - 通用自动化测试框架"""
    pass

from core.utils import parse_options, generate_case_id
from core.runner import PlanRunner  # Ensure PlanRunner is imported if not already

@cli.command()
@click.argument('case_path')
@click.option('--env', default=None, help='指定运行环境')
@click.option('--options', default=None, help='覆盖配置 (key=value, space separated)')
def case(case_path, env, options):
    """单例模式：运行单个 Test Case"""
    logger.info(f"Mode: Single Case | Path: {case_path}")

    try:
        # 1. 加载配置
        cfg = Config.fromfile(case_path)

        # 2. 解析 options 并覆盖配置
        if options:
            override_opts = parse_options(options)
            logger.info(f"Overriding options: {override_opts}")
            cfg.merge_from_dict(override_opts)

        # 3. 初始化 Context，注入 Case ID
        ctx = TestContext(case_config=cfg)
        auto_case_id = generate_case_id(case_path)
        ctx.set('case_id', auto_case_id)
        ctx.set('case_file', case_path)

        # 4. 执行
        runner = CaseRunner(ctx)
        runner.run(cfg.pipeline)
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

@cli.command()
@click.argument('plan_path')
def plan(plan_path):
    """计划模式：运行 Test Plan"""
    logger.info(f"Mode: Test Plan | Path: {plan_path}")
    
    try:
        # 1. 加载 Plan 配置
        plan_cfg = Config.fromfile(plan_path)

        # 注入 Plan Name (基于文件名)
        plan_name = os.path.splitext(os.path.basename(plan_path))[0]
        plan_cfg.setdefault('plan_name', plan_name)

        # 2. 检查环境配置 & Docker 启动逻辑
        env_cfg = plan_cfg.get('environment')
        in_docker = os.environ.get('IN_DOCKER') == '1'

        if env_cfg and env_cfg.get('type') == 'docker' and not in_docker:
            logger.info("Docker environment detected. Preparing to run in container...")
            workspace_root = os.getcwd()
            env_manager = DockerEnvironment(env_cfg, workspace_root)

            # 准备镜像
            env_manager.ensure_image()

            # 构建容器内命令：复用当前执行的参数
            # 注意：这里假设容器内的 python 路径和宿主机一致，或者在 PATH 中
            # 简单起见，我们重新构造命令
            cmd_args = ['python', 'run.py', 'plan', plan_path]
            # 如果有其他参数需要透传，这里可能需要更复杂的解析，目前只处理最基本的

            # 启动容器运行
            exit_code = env_manager.run(cmd_args)
            sys.exit(exit_code)

        # 3. 如果在容器内 或 没有配置 Docker 环境，则直接运行
        if in_docker:
            logger.info("Running INSIDE Docker container.")

        # 4. 初始化 Runner
        runner = PlanRunner(plan_cfg)

        # 5. 执行
        success = runner.run()

        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Plan execution failed: {e}")
        sys.exit(1)

def _merge_config_field(case_cfg, suite_cfg, plan_cfg, field_name: str, default=None):
    """
    按优先级合并配置字段：Case > Suite > Plan

    Args:
        case_cfg: Case 配置
        suite_cfg: Suite 配置
        plan_cfg: Plan 配置
        field_name: 字段名
        default: 默认值

    Returns:
        合并后的字段值
    """
    # 优先级：Case > Suite > Plan
    if case_cfg and field_name in case_cfg:
        return case_cfg.get(field_name)
    if suite_cfg and field_name in suite_cfg:
        return suite_cfg.get(field_name)
    if plan_cfg and field_name in plan_cfg:
        return plan_cfg.get(field_name)
    return default


def _deep_merge_dicts(base: dict, override: dict) -> dict:
    """
    深度合并两个字典，override 中的值会覆盖 base 中的值
    """
    if base is None:
        base = {}
    if override is None:
        override = {}

    result = dict(base).copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def _merge_hierarchical_config(case_cfg, suite_cfg, plan_cfg, field_name: str, default=None):
    """
    按优先级深度合并配置字段（用于字典类型）：Plan -> Suite -> Case（后者覆盖前者）

    Args:
        case_cfg: Case 配置
        suite_cfg: Suite 配置
        plan_cfg: Plan 配置
        field_name: 字段名
        default: 默认值

    Returns:
        合并后的字段值
    """
    plan_value = plan_cfg.get(field_name, {}) if plan_cfg else {}
    suite_value = suite_cfg.get(field_name, {}) if suite_cfg else {}
    case_value = case_cfg.get(field_name, {}) if case_cfg else {}

    if not isinstance(plan_value, dict):
        plan_value = {}
    if not isinstance(suite_value, dict):
        suite_value = {}
    if not isinstance(case_value, dict):
        case_value = {}

    # 按优先级合并：Plan -> Suite -> Case
    result = _deep_merge_dicts(plan_value, suite_value)
    result = _deep_merge_dicts(result, case_value)

    return result if result else default


def _has_exec_config_fields(cfg) -> bool:
    """
    检查配置中是否定义了执行配置相关字段
    """
    exec_fields = ['environment', 'runtime', 'config_files', 'env_file', 'setup_script']
    if cfg is None:
        return False
    for field in exec_fields:
        if field in cfg and cfg.get(field):
            return True
    return False


def _convert_to_plain_dict(obj):
    """
    将 mmengine.Config 或其他类似字典的对象递归转换为普通 Python 字典
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _convert_to_plain_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_convert_to_plain_dict(item) for item in obj]
    return obj


def _merge_docker_field(base_env: dict, override_env: dict) -> tuple:
    """
    合并 docker_id 和 docker_image 字段，作为同一个概念处理。
    override 中定义的字段会覆盖 base 中的字段。

    Returns:
        tuple: (field_name, field_value) 或 (None, None)
    """
    # 检查 override 中是否定义了 docker_id 或 docker_image
    if override_env:
        if override_env.get('docker_id'):
            return ('docker_id', override_env.get('docker_id'))
        if override_env.get('docker_image'):
            return ('docker_image', override_env.get('docker_image'))

    # 如果 override 没有定义，使用 base 中的
    if base_env:
        if base_env.get('docker_id'):
            return ('docker_id', base_env.get('docker_id'))
        if base_env.get('docker_image'):
            return ('docker_image', base_env.get('docker_image'))

    return (None, None)


def _build_exec_config_dict(plan_environment, suite_environment, merged_runtime, merged_config_files, merged_env_file, merged_setup_script, plan_name: str = '', suite_name: str = '') -> dict:
    """
    根据合并后的配置构建 K8s CRD 格式的 exec_config 字典结构

    Args:
        plan_environment: Plan 级别的 environment 配置
        suite_environment: Suite 级别的 environment 配置（用于 docker_id/docker_image 的特殊合并）
        merged_runtime: 合并后的 runtime 配置
        merged_config_files: 合并后的 config_files 配置
        merged_env_file: 合并后的 env_file 配置
        merged_setup_script: 合并后的 setup_script 配置
        plan_name: Plan 名称，用于 metadata.namespace
        suite_name: Suite 名称，用于 metadata.name
    """
    # 构建 spec 部分
    spec = {}

    # 合并 environment（除了 docker_id/docker_image 之外的字段使用普通合并）
    merged_environment = _deep_merge_dicts(plan_environment or {}, suite_environment or {})

    # environment 部分
    if merged_environment or plan_environment or suite_environment:
        env_section = {}
        # run_at 来自 type 或 run_type
        run_at = merged_environment.get('run_type') or merged_environment.get('type')
        if run_at:
            env_section['run_at'] = run_at
        # base_image 来自 vm_image
        if merged_environment.get('vm_image'):
            env_section['base_image'] = merged_environment.get('vm_image')
        # docker_id 和 docker_image 作为同一个概念处理，Suite 覆盖 Plan
        docker_field, docker_value = _merge_docker_field(plan_environment or {}, suite_environment or {})
        if docker_field and docker_value:
            env_section[docker_field] = docker_value
        # packages 数组（兼容旧的 package 字段）
        if merged_environment.get('packages'):
            env_section['packages'] = _convert_to_plain_dict(merged_environment.get('packages'))
        elif merged_environment.get('package'):
            env_section['package'] = merged_environment.get('package')
        # dependencies 字段
        if merged_environment.get('dependencies'):
            env_section['dependencies'] = _convert_to_plain_dict(merged_environment.get('dependencies'))
        if env_section:
            spec['environment'] = env_section

    # runtime 部分
    if merged_runtime:
        runtime_section = {}
        if merged_runtime.get('hw_type'):
            runtime_section['hw_type'] = merged_runtime.get('hw_type')
        if merged_runtime.get('driver'):
            runtime_section['driver'] = merged_runtime.get('driver')
        if 'setup_driver' in merged_runtime:
            runtime_section['setup_driver'] = merged_runtime.get('setup_driver')
        if merged_runtime.get('resources'):
            # 将 resources 转换为普通字典，避免 mmengine.Config 序列化问题
            runtime_section['resource'] = _convert_to_plain_dict(merged_runtime.get('resources'))
        if merged_runtime.get('labels'):
            runtime_section['labels'] = merged_runtime.get('labels')
        if runtime_section:
            spec['runtime'] = runtime_section

    # config_files 部分：转换为普通字典
    if merged_config_files:
        spec['config_files'] = _convert_to_plain_dict(merged_config_files)

    # env_file 部分
    if merged_env_file:
        spec['env_file'] = merged_env_file

    # setup_script 部分
    if merged_setup_script:
        spec['setup_script'] = merged_setup_script

    # 构建完整的 K8s CRD 格式
    exec_config = {
        'apiVersion': 'test.eng.t-head.cn/v1',
        'kind': 'TestExecConfig',
        'metadata': {
            'name': suite_name or 'default',
            'namespace': plan_name or 'default'
        },
        'spec': spec
    }

    return exec_config


def _generate_exec_config_files(csv_path, plan_cfg, suite_configs: dict) -> dict:
    """
    生成 exec_config YAML 文件（K8s CRD 格式）

    Args:
        csv_path: CSV 文件路径，用于确定 exec_config 文件夹位置
        plan_cfg: Plan 配置
        suite_configs: Suite 配置字典 {suite_path: suite_cfg}

    Returns:
        dict: {suite_path 或 'default': yaml_file_path} 的映射
    """
    # 获取 Plan 名称（用于 metadata.namespace 和子文件夹名称）
    plan_metadata = plan_cfg.get('metadata', {})
    plan_name = plan_metadata.get('name') or 'default'

    # 创建 exec_config/<plan_name> 文件夹
    csv_dir = os.path.dirname(csv_path) if os.path.dirname(csv_path) else '.'
    exec_config_dir = os.path.join(csv_dir, 'exec_config', plan_name)
    if not os.path.exists(exec_config_dir):
        os.makedirs(exec_config_dir)

    exec_config_mapping = {}

    # 1. 生成 Plan 级别的 default.yaml
    plan_environment = plan_cfg.get('environment', {})
    plan_runtime = plan_cfg.get('runtime', {})
    plan_config_files = plan_cfg.get('config_files', {})
    plan_env_file = plan_cfg.get('env_file', '')
    plan_setup_script = plan_cfg.get('setup_script', '')

    default_exec_config = _build_exec_config_dict(
        plan_environment, None, plan_runtime, plan_config_files, plan_env_file, plan_setup_script,
        plan_name=plan_name, suite_name='default'
    )

    default_yaml_path = os.path.join(exec_config_dir, 'default.yaml')
    with open(default_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_exec_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    exec_config_mapping['default'] = default_yaml_path

    # 2. 为每个有执行配置的 Suite 生成 YAML 文件
    for suite_path, suite_cfg in suite_configs.items():
        # 获取 Suite 名称
        suite_metadata = suite_cfg.get('metadata', {}) if suite_cfg else {}
        suite_name = suite_metadata.get('name') or os.path.splitext(os.path.basename(suite_path))[0]

        if not _has_exec_config_fields(suite_cfg):
            # Suite 没有定义执行配置字段，使用 default
            exec_config_mapping[suite_path] = default_yaml_path
            continue

        # 合并 Plan 和 Suite 的配置
        plan_environment = plan_cfg.get('environment', {})
        suite_environment = suite_cfg.get('environment', {}) if suite_cfg else {}
        merged_runtime = _deep_merge_dicts(
            plan_cfg.get('runtime', {}),
            suite_cfg.get('runtime', {}) if suite_cfg else {}
        )
        merged_config_files = _deep_merge_dicts(
            plan_cfg.get('config_files', {}),
            suite_cfg.get('config_files', {}) if suite_cfg else {}
        )
        merged_env_file = suite_cfg.get('env_file') if suite_cfg and suite_cfg.get('env_file') else plan_cfg.get('env_file', '')
        merged_setup_script = suite_cfg.get('setup_script') if suite_cfg and suite_cfg.get('setup_script') else plan_cfg.get('setup_script', '')

        suite_exec_config = _build_exec_config_dict(
            plan_environment, suite_environment, merged_runtime, merged_config_files, merged_env_file, merged_setup_script,
            plan_name=plan_name, suite_name=suite_name
        )

        suite_yaml_path = os.path.join(exec_config_dir, f'{suite_name}.yaml')

        with open(suite_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(suite_exec_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        exec_config_mapping[suite_path] = suite_yaml_path

    return exec_config_mapping


@cli.command()
@click.argument('plan_path')
@click.option('--csv', 'csv_path', help='Dump result to CSV file')
def list_cases(plan_path, csv_path):
    """列出 Plan 中包含的所有 Case"""
    logger.info(f"Listing cases for Plan: {plan_path}")

    try:
        # 1. 加载 Plan 配置
        plan_cfg = Config.fromfile(plan_path)
        suites = plan_cfg.get('suites', [])

        # 获取 Plan 的 metadata 中的 component
        plan_metadata = plan_cfg.get('metadata', {})
        plan_component = plan_metadata.get('component', '')

        logger.info(f"Found {len(suites)} suites in plan.")

        from core.loader import SuiteLoader

        total_cases = 0
        case_data_list = []
        suite_configs = {}  # 用于存储所有 suite 配置，供生成 exec_config 使用

        for suite_path in suites:
            print(f"\nSuite: {suite_path}")
            try:
                # 使用新方法同时获取 case 列表和 suite 配置
                case_files, suite_cfg = SuiteLoader.load_cases_with_config(suite_path)
                suite_configs[suite_path] = suite_cfg  # 保存 suite 配置

                # 获取 Suite 的 metadata 中的 domain
                suite_metadata = suite_cfg.get('metadata', {}) if suite_cfg else {}
                suite_domain = suite_metadata.get('domain', '')

                if not case_files:
                     print("  (No cases found)")
                for case_file in case_files:
                    print(f"  - {case_file}")
                    total_cases += 1

                    if csv_path:
                        try:
                            # 加载 Case 详情用于导出
                            case_cfg = Config.fromfile(case_file)
                            metadata = case_cfg.get('metadata', {})

                            # Extract Case-level info
                            labels = case_cfg.get('labels', [])
                            labels_str = '|'.join(labels) if isinstance(labels, list) else str(labels)
                            cmd = f"python run.py case {case_file}"

                            # 自动生成 Case ID
                            auto_case_id = generate_case_id(case_file)

                            # 收集数据（去掉 config_files, env_file, setup_scripts, vm_image, docker_image, global config）
                            # 新增 component, domain, exec_config（exec_config 稍后填充）
                            case_data_list.append({
                                'case ID': auto_case_id,
                                'name': metadata.get('name', ''),
                                'component': plan_component,
                                'domain': suite_domain,
                                'suite': suite_path,
                                'case path': case_file,
                                'labels': labels_str,
                                'cmd': cmd,
                                'exec_config': ''  # 稍后填充
                            })
                        except Exception as e:
                            logger.error(f"Failed to load details for case {case_file}: {e}")
                            # 即使加载失败也生成 Case ID
                            auto_case_id = generate_case_id(case_file)

                            case_data_list.append({
                                'case ID': auto_case_id,
                                'name': 'ERROR',
                                'component': plan_component,
                                'domain': suite_domain,
                                'suite': suite_path,
                                'case path': case_file,
                                'labels': '',
                                'cmd': f"python run.py case {case_file}",
                                'exec_config': ''  # 稍后填充
                            })

            except Exception as e:
                logger.error(f"Failed to load suite {suite_path}: {e}")

        print(f"\nTotal Cases: {total_cases}")

        # 如果指定了 CSV 输出路径，则写入文件
        if csv_path and case_data_list:
            try:
                # 确保目录存在
                output_dir = os.path.dirname(csv_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                # 生成 exec_config YAML 文件
                exec_config_mapping = _generate_exec_config_files(csv_path, plan_cfg, suite_configs)

                # 填充每个 case 的 exec_config 路径
                for case_data in case_data_list:
                    suite_path = case_data['suite']
                    if suite_path in exec_config_mapping:
                        case_data['exec_config'] = exec_config_mapping[suite_path]
                    else:
                        case_data['exec_config'] = exec_config_mapping.get('default', '')

                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['case ID', 'name', 'component', 'domain', 'suite', 'case path', 'labels', 'cmd', 'exec_config']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for row in case_data_list:
                        writer.writerow(row)

                logger.info(f"Successfully dumped cases to {csv_path}")
                print(f"CSV exported to: {csv_path}")
                print(f"Exec config files generated in: {os.path.join(output_dir if output_dir else '.', 'exec_config')}")
            except Exception as e:
                logger.error(f"Failed to write CSV file: {e}")

    except Exception as e:
        logger.error(f"Failed to list cases: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()