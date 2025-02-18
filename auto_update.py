#!/usr/bin/env python3
import os
import time
import subprocess
import logging
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/auto_update.log')),
        logging.StreamHandler()
    ]
)

def run_command(cmd, check=True, input_data=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True, input=input_data)
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"命令执行失败: {e.cmd}")
        logging.error(f"错误输出: {e.stderr}")
        if check:
            raise
        return e
    except Exception as e:
        logging.error(f"执行命令时发生错误: {str(e)}")
        if check:
            raise
        return None

def setup_git_credentials():
    """配置Git凭据"""
    try:
        # 配置git使用store凭据助手
        run_command(["sudo", "/volume1/@appstore/Git/bin/git", "config", "--global", "credential.helper", "store"])
        
        # 设置git URL，包含用户名和密码
        git_url = "http://alan:gogs-12345@192.168.0.109:3000"
        run_command(["sudo", "/volume1/@appstore/Git/bin/git", "remote", "set-url", "origin", f"{git_url}/alan/stock.git"])
        
        logging.info("Git凭据配置完成")
    except Exception as e:
        logging.error(f"配置Git凭据时出错: {str(e)}")
        raise

def check_and_update():
    """检查并更新代码"""
    try:
        repo_path = "/volume1/docker/stock-app"
        os.chdir(repo_path)
        
        # 获取当前提交的hash
        current_hash = run_command(["sudo", "/volume1/@appstore/Git/bin/git", "rev-parse", "HEAD"]).stdout.strip()
        
        # 获取远程最新状态
        logging.info("检查远程更新...")
        run_command(["sudo", "/volume1/@appstore/Git/bin/git", "fetch", "origin", "main"])
        
        # 获取远程提交的hash
        remote_hash = run_command(["sudo", "/volume1/@appstore/Git/bin/git", "rev-parse", "origin/main"]).stdout.strip()
        
        # 比较是否有更新
        if current_hash != remote_hash:
            logging.info("检测到新的更新！")
            
            # 清理本地修改
            run_command(["sudo", "/volume1/@appstore/Git/bin/git", "reset", "--hard"])
            run_command(["sudo", "/volume1/@appstore/Git/bin/git", "clean", "-fd"])
            
            # 拉取最新代码
            logging.info("拉取最新代码...")
            run_command(["sudo", "/volume1/@appstore/Git/bin/git", "pull", "origin", "main"])
            
            # 停止并删除现有容器
            logging.info("停止现有容器...")
            run_command(["sudo", "/usr/local/bin/docker", "stop", "stock-app"], check=False)
            run_command(["sudo", "/usr/local/bin/docker", "rm", "stock-app"], check=False)
            
            # 重新构建镜像
            logging.info("重新构建镜像...")
            run_command(["sudo", "/usr/local/bin/docker-compose", "build"])
            
            # 启动新容器
            logging.info("启动新容器...")
            run_command(["sudo", "/usr/local/bin/docker-compose", "up", "-d"])
            
            logging.info("更新完成！")
        else:
            logging.info("没有检测到更新")
            
    except Exception as e:
        logging.error(f"更新过程中出错: {str(e)}")
        # 不抛出异常，让脚本继续运行

def main():
    """主函数"""
    repo_path = "/volume1/docker/stock-app"
    
    # 确保目录存在
    os.makedirs(repo_path, exist_ok=True)
    
    # 配置Git凭据
    setup_git_credentials()
    
    # 确保目录是一个Git仓库
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logging.info("初始化Git仓库...")
        os.chdir(repo_path)
        run_command(["sudo", "/volume1/@appstore/Git/bin/git", "init"])
        run_command(["sudo", "/volume1/@appstore/Git/bin/git", "remote", "add", "origin", "http://192.168.0.109:3000/alan/stock.git"])
        run_command(["sudo", "/volume1/@appstore/Git/bin/git", "fetch"])
        run_command(["sudo", "/volume1/@appstore/Git/bin/git", "checkout", "main"])
    
    logging.info("启动自动更新检查...")
    
    while True:
        try:
            check_and_update()
            time.sleep(30)  # 每30秒检查一次
        except KeyboardInterrupt:
            logging.info("收到终止信号，停止检查...")
            sys.exit(0)
        except Exception as e:
            logging.error(f"发生错误: {str(e)}")
            time.sleep(30)  # 发生错误后等待30秒再继续

if __name__ == "__main__":
    main() 