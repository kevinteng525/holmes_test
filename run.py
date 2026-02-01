import sys
import os
import json
import csv
import logging
import click
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

from core.utils import parse_options
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

        # 3. 初始化 Context
        ctx = TestContext(case_config=cfg)

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

        logger.info(f"Found {len(suites)} suites in plan.")

        from core.loader import SuiteLoader

        total_cases = 0
        case_data_list = []

        for suite_path in suites:
            print(f"\nSuite: {suite_path}")
            try:
                # 使用新方法同时获取 case 列表和 suite 配置
                case_files, suite_cfg = SuiteLoader.load_cases_with_config(suite_path)
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

                            # 按优先级合并配置：Case > Suite > Plan
                            # 对于字典类型使用深度合并
                            merged_config_files = _merge_hierarchical_config(case_cfg, suite_cfg, plan_cfg, 'config_files', {})
                            merged_global_config = _merge_hierarchical_config(case_cfg, suite_cfg, plan_cfg, 'global_config', {})
                            merged_environment = _merge_hierarchical_config(case_cfg, suite_cfg, plan_cfg, 'environment', {})

                            # 对于字符串类型使用简单覆盖
                            merged_env_file = _merge_config_field(case_cfg, suite_cfg, plan_cfg, 'env_file', '')
                            merged_setup_script = _merge_config_field(case_cfg, suite_cfg, plan_cfg, 'setup_script',
                                                    _merge_config_field(case_cfg, suite_cfg, plan_cfg, 'setup_scripts', ''))

                            # 从合并后的 environment 中提取镜像信息
                            vm_image = merged_environment.get('vm_image', '') if isinstance(merged_environment, dict) else ''
                            docker_image = merged_environment.get('docker_image', '') if isinstance(merged_environment, dict) else ''

                            # 收集数据
                            case_data_list.append({
                                'case ID': metadata.get('ID', ''),
                                'name': metadata.get('name', ''),
                                'suite': suite_path,
                                'case path': case_file,
                                'labels': labels_str,
                                'cmd': cmd,
                                'config_files': json.dumps(merged_config_files, ensure_ascii=False),
                                'env_file': merged_env_file,
                                'setup_scripts': merged_setup_script,
                                'vm_image': vm_image,
                                'docker_image': docker_image,
                                'global config': json.dumps(merged_global_config, ensure_ascii=False)
                            })
                        except Exception as e:
                            logger.error(f"Failed to load details for case {case_file}: {e}")
                            # 即使加载失败也记录基本信息，使用 Plan 级别配置作为后备
                            plan_config_files = plan_cfg.get('config_files', {})
                            plan_env_file = plan_cfg.get('env_file', '')
                            plan_setup_scripts = plan_cfg.get('setup_script', plan_cfg.get('setup_scripts', ''))
                            plan_env_cfg = plan_cfg.get('environment', {})
                            plan_vm_image = plan_env_cfg.get('vm_image', '') if isinstance(plan_env_cfg, dict) else ''
                            plan_docker_image = plan_env_cfg.get('docker_image', '') if isinstance(plan_env_cfg, dict) else ''
                            plan_global_config = plan_cfg.get('global_config', {})

                            case_data_list.append({
                                'case ID': 'ERROR',
                                'name': 'ERROR',
                                'suite': suite_path,
                                'case path': case_file,
                                'labels': '',
                                'cmd': f"python run.py case {case_file}",
                                'config_files': json.dumps(plan_config_files, ensure_ascii=False),
                                'env_file': plan_env_file,
                                'setup_scripts': plan_setup_scripts,
                                'vm_image': plan_vm_image,
                                'docker_image': plan_docker_image,
                                'global config': json.dumps(plan_global_config, ensure_ascii=False)
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

                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['case ID', 'name', 'suite', 'case path', 'labels', 'cmd', 'config_files', 'env_file', 'setup_scripts', 'vm_image', 'docker_image', 'global config']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for row in case_data_list:
                        writer.writerow(row)

                logger.info(f"Successfully dumped cases to {csv_path}")
                print(f"CSV exported to: {csv_path}")
            except Exception as e:
                logger.error(f"Failed to write CSV file: {e}")

    except Exception as e:
        logger.error(f"Failed to list cases: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()