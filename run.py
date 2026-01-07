import sys
import logging
import click
from mmengine.config import Config
from core.runner import CaseRunner
from core.context import TestContext
from core.loader import SuiteLoader

# 自动注册插件
# 实际项目中可能通过 entry_points 或 importlib 动态加载
import holmes.plugins.steps.common
import holmes.plugins.engines.dummy_engine
import holmes.plugins.collectors.common

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('HolmesCLI')

@click.group()
def cli():
    """Holmes - 通用自动化测试框架"""
    pass

from holmes.utils import parse_options
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

        # 2. 初始化 Runner
        runner = PlanRunner(plan_cfg)

        # 3. 执行
        success = runner.run()

        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Plan execution failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()