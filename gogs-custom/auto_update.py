#!/usr/bin/env python3
import os
import time
import subprocess
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/auto_update.log')),
        logging.StreamHandler()
    ]
)

def setup_git_credentials():
    try:
        # 配置 Git 凭据存储
        subprocess.check_call(["sudo", "/volume1/@appstore/Git/bin/git", "config", "--global", "credential.helper", "store"])
        # 创建凭据文件
        credentials = "https://alan:gogs-12345@192.168.0.109:3000"
        home_dir = os.path.expanduser("~")
        with open(os.path.join(home_dir, ".git-credentials"), "w") as f:
            f.write(credentials)
        logging.info("Git 凭据配置完成")
    except Exception as e:
        logging.error(f"配置 Git 凭据时出错: {str(e)}")

def check_and_update():
    try:
        repo_path = "/volume1/docker/stock-app"
        os.chdir(repo_path)
        
        # 获取当前提交的 hash
        current_hash = subprocess.check_output(["sudo", "/volume1/@appstore/Git/bin/git", "rev-parse", "HEAD"]).decode().strip()
        
        # 获取远程最新状态
        logging.info("检查远程更新...")
        subprocess.check_call(["sudo", "/volume1/@appstore/Git/bin/git", "fetch", "origin", "main"])
        
        # 获取远程提交的 hash
        remote_hash = subprocess.check_output(["sudo", "/volume1/@appstore/Git/bin/git", "rev-parse", "origin/main"]).decode().strip()
        
        # 比较是否有更新
        if current_hash != remote_hash:
            logging.info("检测到新的更新！")
            
            # 拉取最新代码
            logging.info("拉取最新代码...")
            subprocess.check_call(["sudo", "/volume1/@appstore/Git/bin/git", "pull", "origin", "main"])
            
            # 停止并删除现有容器
            logging.info("停止现有容器...")
            subprocess.check_call(["sudo", "/usr/local/bin/docker", "stop", "stock-app"])
            subprocess.check_call(["sudo", "/usr/local/bin/docker", "rm", "stock-app"])
            
            # 重新构建镜像
            logging.info("重新构建镜像...")
            subprocess.check_call(["sudo", "/usr/local/bin/docker-compose", "build"])
            
            # 启动新容器
            logging.info("启动新容器...")
            subprocess.check_call(["sudo", "/usr/local/bin/docker-compose", "up", "-d"])
            
            logging.info("更新完成！")
        else:
            logging.info("没有检测到更新")
            
    except subprocess.CalledProcessError as e:
        logging.error(f"执行命令时出错: {e.output.decode() if hasattr(e, 'output') else str(e)}")
    except Exception as e:
        logging.error(f"发生错误: {str(e)}")

def main():
    repo_path = "/volume1/docker/stock-app"
    
    # 配置 Git 凭据
    setup_git_credentials()
    
    # 确保目录是一个 Git 仓库
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logging.info("初始化 Git 仓库...")
        os.chdir(repo_path)
        subprocess.check_call(["sudo", "/volume1/@appstore/Git/bin/git", "init"])
        subprocess.check_call(["sudo", "/volume1/@appstore/Git/bin/git", "remote", "add", "origin", "http://192.168.0.109:3000/alan/stock.git"])
        subprocess.check_call(["sudo", "/volume1/@appstore/Git/bin/git", "fetch"])
        subprocess.check_call(["sudo", "/volume1/@appstore/Git/bin/git", "checkout", "main"])
    
    logging.info("启动自动更新检查...")
    
    try:
        while True:
            check_and_update()
            time.sleep(30)  # 每30秒检查一次
    except KeyboardInterrupt:
        logging.info("收到终止信号，停止检查...")

if __name__ == "__main__":
    main() 