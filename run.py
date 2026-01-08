import sys
import os
import logging
import click
from mmengine.config import Config
from core.runner import CaseRunner
from core.context import TestContext
from core.env_manager import DockerEnvironment
from core.registry import STEPS

# 重要：注册插件 到 Registry 中，不能删
import holmes.plugins.steps.sample
import holmes.plugins.dummy.engine
import holmes.plugins.collectors.sample
import holmes.plugins.collectors.plan_summary

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

@cli.command()
@click.argument('plan_path')
def list_cases(plan_path):
    """列出 Plan 中包含的所有 Case"""
    logger.info(f"Listing cases for Plan: {plan_path}")

    try:
        # 1. 加载 Plan 配置
        plan_cfg = Config.fromfile(plan_path)
        suites = plan_cfg.get('suites', [])

        logger.info(f"Found {len(suites)} suites in plan.")

        from core.loader import SuiteLoader

        total_cases = 0
        for suite_path in suites:
            print(f"\nSuite: {suite_path}")
            try:
                case_files = SuiteLoader.load_cases_from_suite(suite_path)
                if not case_files:
                     print("  (No cases found)")
                for case_file in case_files:
                    print(f"  - {case_file}")
                    total_cases += 1
            except Exception as e:
                logger.error(f"Failed to load suite {suite_path}: {e}")

        print(f"\nTotal Cases: {total_cases}")

    except Exception as e:
        logger.error(f"Failed to list cases: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()