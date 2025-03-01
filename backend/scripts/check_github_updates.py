#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import logging
import requests
import subprocess
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('github_updater')

# 配置信息
class Config:
    # GitHub仓库信息
    REPO_OWNER = "your_username"  # 替换为你的GitHub用户名
    REPO_NAME = "your_repo_name"  # 替换为你的仓库名称
    BRANCH = "main"  # 要监控的分支
    
    # GitHub API访问令牌（如果是私有仓库则需要）
    # 可以在GitHub的Settings -> Developer settings -> Personal access tokens生成
    GITHUB_TOKEN = ""  # 如果是公开仓库，可以留空
    
    # 本地仓库路径
    LOCAL_REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # 更新检查间隔（秒）
    CHECK_INTERVAL = 3600  # 默认每小时检查一次
    
    # 上次检查的提交SHA记录文件
    LAST_COMMIT_FILE = os.path.join(os.path.dirname(__file__), '.last_commit')
    
    # 更新后要执行的命令（如重启服务等）
    POST_UPDATE_COMMANDS = [
        # "systemctl restart your_service",  # 取消注释并替换为你需要的命令
    ]
    
    # 是否自动更新
    AUTO_UPDATE = True
    
    # 是否在更新前备份
    BACKUP_BEFORE_UPDATE = True
    BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

class GitHubUpdater:
    def __init__(self, config):
        self.config = config
        self._ensure_dirs()
        
    def _ensure_dirs(self):
        """确保必要的目录存在"""
        if self.config.BACKUP_BEFORE_UPDATE and not os.path.exists(self.config.BACKUP_DIR):
            os.makedirs(self.config.BACKUP_DIR)
    
    def _get_headers(self):
        """获取API请求头"""
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.config.GITHUB_TOKEN:
            headers['Authorization'] = f'token {self.config.GITHUB_TOKEN}'
        return headers
    
    def _get_last_commit_sha(self):
        """获取上次记录的提交SHA"""
        if os.path.exists(self.config.LAST_COMMIT_FILE):
            with open(self.config.LAST_COMMIT_FILE, 'r') as f:
                return f.read().strip()
        return None
    
    def _save_last_commit_sha(self, sha):
        """保存最新的提交SHA"""
        with open(self.config.LAST_COMMIT_FILE, 'w') as f:
            f.write(sha)
    
    def _get_latest_commit(self):
        """获取GitHub仓库最新的提交"""
        url = f'https://api.github.com/repos/{self.config.REPO_OWNER}/{self.config.REPO_NAME}/commits/{self.config.BRANCH}'
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取最新提交失败: {e}")
            return None
    
    def _create_backup(self):
        """创建当前代码的备份"""
        if not self.config.BACKUP_BEFORE_UPDATE:
            return True
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.tar.gz"
        backup_path = os.path.join(self.config.BACKUP_DIR, backup_name)
        
        try:
            # 排除.git目录和node_modules等大型目录
            cmd = f"tar --exclude='.git' --exclude='node_modules' --exclude='.venv' -czf {backup_path} -C {os.path.dirname(self.config.LOCAL_REPO_PATH)} {os.path.basename(self.config.LOCAL_REPO_PATH)}"
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"备份创建成功: {backup_path}")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"创建备份失败: {e}")
            return False
    
    def _pull_updates(self):
        """从GitHub拉取最新代码"""
        try:
            # 切换到仓库目录
            os.chdir(self.config.LOCAL_REPO_PATH)
            
            # 获取当前分支
            current_branch = subprocess.check_output(
                "git rev-parse --abbrev-ref HEAD", 
                shell=True
            ).decode().strip()
            
            # 如果不在目标分支，切换到目标分支
            if current_branch != self.config.BRANCH:
                logger.info(f"切换分支从 {current_branch} 到 {self.config.BRANCH}")
                subprocess.run(f"git checkout {self.config.BRANCH}", shell=True, check=True)
            
            # 拉取最新代码
            logger.info("正在拉取最新代码...")
            subprocess.run("git pull", shell=True, check=True)
            
            logger.info("代码更新成功")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"拉取更新失败: {e}")
            return False
    
    def _run_post_update_commands(self):
        """运行更新后的命令"""
        if not self.config.POST_UPDATE_COMMANDS:
            return
            
        logger.info("执行更新后命令...")
        for cmd in self.config.POST_UPDATE_COMMANDS:
            try:
                logger.info(f"执行命令: {cmd}")
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.SubprocessError as e:
                logger.error(f"命令执行失败: {cmd}, 错误: {e}")
    
    def check_and_update(self):
        """检查并更新代码"""
        # 获取最新提交
        latest_commit = self._get_latest_commit()
        if not latest_commit:
            return False
            
        latest_sha = latest_commit['sha']
        last_sha = self._get_last_commit_sha()
        
        # 如果SHA相同，说明没有更新
        if last_sha and last_sha == latest_sha:
            logger.info("没有检测到新的更新")
            return False
        
        # 有新的提交
        commit_message = latest_commit['commit']['message']
        commit_date = latest_commit['commit']['author']['date']
        author = latest_commit['commit']['author']['name']
        
        logger.info(f"检测到新的更新:")
        logger.info(f"提交: {latest_sha[:8]}")
        logger.info(f"作者: {author}")
        logger.info(f"日期: {commit_date}")
        logger.info(f"消息: {commit_message}")
        
        # 如果配置为自动更新
        if self.config.AUTO_UPDATE:
            logger.info("开始自动更新...")
            
            # 创建备份
            if self.config.BACKUP_BEFORE_UPDATE:
                if not self._create_backup():
                    logger.error("备份失败，取消更新")
                    return False
            
            # 拉取更新
            if self._pull_updates():
                # 保存最新的SHA
                self._save_last_commit_sha(latest_sha)
                
                # 运行更新后命令
                self._run_post_update_commands()
                
                logger.info("更新完成")
                return True
        else:
            logger.info("检测到更新，但自动更新已禁用")
            
        return False

def main():
    """主函数"""
    updater = GitHubUpdater(Config)
    
    # 单次运行模式
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        return updater.check_and_update()
    
    # 循环检查模式
    logger.info(f"GitHub更新检查服务启动，检查间隔: {Config.CHECK_INTERVAL}秒")
    
    while True:
        try:
            updater.check_and_update()
        except Exception as e:
            logger.error(f"检查更新时发生错误: {e}")
        
        logger.info(f"等待 {Config.CHECK_INTERVAL} 秒后进行下一次检查...")
        time.sleep(Config.CHECK_INTERVAL)

if __name__ == "__main__":
    main() 