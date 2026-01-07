import docker
import os
import sys
import logging
from typing import Dict, List

logger = logging.getLogger('EnvManager')

class DockerEnvironment:
    def __init__(self, env_config: Dict, workspace_root: str):
        self.config = env_config
        self.workspace_root = workspace_root
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.warning(f"Failed to connect to Docker Daemon: {e}")
            self.client = None
            
        self.image_tag = env_config.get('image_tag', 'holmes-test:latest')
        self.dockerfile = env_config.get('dockerfile')

    def is_available(self):
        return self.client is not None

    def ensure_image(self):
        """确保镜像存在，如果不存在且指定了 Dockerfile 则构建"""
        if not self.is_available():
            raise RuntimeError("Docker is not available")

        try:
            self.client.images.get(self.image_tag)
            logger.info(f"Docker image '{self.image_tag}' found locally.")
        except docker.errors.ImageNotFound:
            logger.info(f"Image '{self.image_tag}' not found.")
            if self.dockerfile:
                logger.info(f"Building image from {self.dockerfile}...")
                try:
                    # 使用 workspace_root 作为构建上下文
                    self.client.images.build(
                        path=self.workspace_root,
                        dockerfile=self.dockerfile,
                        tag=self.image_tag,
                        rm=True
                    )
                    logger.info(f"Image '{self.image_tag}' built successfully.")
                except Exception as e:
                    logger.error(f"Failed to build image: {e}")
                    raise
            else:
                logger.info(f"Pulling image '{self.image_tag}'...")
                try:
                    self.client.images.pull(self.image_tag)
                    logger.info(f"Image '{self.image_tag}' pulled successfully.")
                except Exception as e:
                    logger.error(f"Failed to pull image: {e}")
                    raise

    def run(self, cmd_args: List[str]) -> int:
        """在容器内运行命令"""
        if not self.is_available():
            raise RuntimeError("Docker is not available")

        # 挂载当前工作目录
        volumes = {
            self.workspace_root: {'bind': '/workspace', 'mode': 'rw'}
        }

        # 设置环境变量，标记已经在 Docker 中，防止无限递归
        environment = {
            'IN_DOCKER': '1',
            'PYTHONPATH': '/workspace'
        }
        
        # 传递用户可能设置的特定环境变量
        if 'options' in self.config:
             # 这里可以扩展更多配置处理
             pass

        logger.info(f"Starting Docker container with image: {self.image_tag}")
        logger.info(f"Command: {' '.join(cmd_args)}")

        try:
            container = self.client.containers.run(
                self.image_tag,
                command=cmd_args,
                volumes=volumes,
                working_dir='/workspace',
                environment=environment,
                detach=True,
                # 使用 host 网络模式可能方便某些调试，但这里暂保持默认
            )
            
            # 流式输出日志
            try:
                for line in container.logs(stream=True, follow=True):
                    print(line.decode('utf-8', errors='replace'), end='')
            except Exception:
                pass

            # 等待容器结束
            result = container.wait()
            exit_code = result.get('StatusCode', 0)
            
            # 清理容器
            container.remove()
            
            return exit_code

        except Exception as e:
            logger.error(f"Failed to run container: {e}")
            return 1
