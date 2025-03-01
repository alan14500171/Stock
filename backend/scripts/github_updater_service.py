#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
import logging
import argparse
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
logger = logging.getLogger('github_updater_service')

# 脚本路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPDATER_SCRIPT = os.path.join(SCRIPT_DIR, 'check_github_updates.py')
PID_FILE = os.path.join(SCRIPT_DIR, '.github_updater.pid')
LOG_FILE = os.path.join(SCRIPT_DIR, 'github_updater.log')

def is_running():
    """检查服务是否正在运行"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            # 进程不存在，删除PID文件
            os.remove(PID_FILE)
    
    return False

def write_pid(pid):
    """写入PID文件"""
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))

def start_service():
    """启动服务"""
    if is_running():
        logger.error("服务已经在运行中")
        return False
    
    logger.info("启动GitHub更新器服务...")
    
    # 启动更新脚本作为后台进程
    log_file = open(LOG_FILE, 'a')
    process = subprocess.Popen(
        [sys.executable, UPDATER_SCRIPT],
        stdout=log_file,
        stderr=log_file,
        close_fds=True
    )
    
    # 写入PID文件
    write_pid(process.pid)
    
    logger.info(f"服务已启动，PID: {process.pid}")
    logger.info(f"日志文件: {LOG_FILE}")
    
    return True

def stop_service():
    """停止服务"""
    if not is_running():
        logger.error("服务未运行")
        return False
    
    # 读取PID
    with open(PID_FILE, 'r') as f:
        pid = int(f.read().strip())
    
    logger.info(f"正在停止服务 (PID: {pid})...")
    
    # 发送终止信号
    try:
        os.kill(pid, signal.SIGTERM)
        
        # 等待进程终止
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except OSError:
                # 进程已终止
                break
        else:
            # 如果进程仍在运行，发送SIGKILL
            logger.warning("服务未响应SIGTERM，发送SIGKILL...")
            os.kill(pid, signal.SIGKILL)
    
    except OSError as e:
        logger.error(f"停止服务时出错: {e}")
        return False
    
    # 删除PID文件
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    
    logger.info("服务已停止")
    return True

def restart_service():
    """重启服务"""
    stop_service()
    time.sleep(1)
    return start_service()

def check_status():
    """检查服务状态"""
    if not is_running():
        logger.info("服务状态: 未运行")
        return False
    
    # 读取PID
    with open(PID_FILE, 'r') as f:
        pid = int(f.read().strip())
    
    # 获取进程信息
    try:
        # 在Linux上获取进程启动时间
        if sys.platform.startswith('linux'):
            cmd = f"ps -p {pid} -o lstart="
            start_time = subprocess.check_output(cmd, shell=True).decode().strip()
            logger.info(f"服务状态: 运行中 (PID: {pid}, 启动时间: {start_time})")
        else:
            logger.info(f"服务状态: 运行中 (PID: {pid})")
        
        # 检查日志文件
        if os.path.exists(LOG_FILE):
            file_size = os.path.getsize(LOG_FILE)
            modified_time = datetime.fromtimestamp(os.path.getmtime(LOG_FILE))
            logger.info(f"日志文件: {LOG_FILE} (大小: {file_size} 字节, 最后修改: {modified_time})")
        
        return True
    except subprocess.SubprocessError:
        logger.error(f"无法获取进程信息")
        return False

def view_log(lines=50):
    """查看日志文件的最后几行"""
    if not os.path.exists(LOG_FILE):
        logger.error(f"日志文件不存在: {LOG_FILE}")
        return False
    
    try:
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            # 在Linux/macOS上使用tail命令
            subprocess.run(f"tail -n {lines} {LOG_FILE}", shell=True)
        else:
            # 在Windows上手动读取最后几行
            with open(LOG_FILE, 'r') as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    print(line.strip())
        
        return True
    except Exception as e:
        logger.error(f"查看日志时出错: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='GitHub更新器服务管理')
    
    # 创建互斥的命令组
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--start', action='store_true', help='启动服务')
    group.add_argument('--stop', action='store_true', help='停止服务')
    group.add_argument('--restart', action='store_true', help='重启服务')
    group.add_argument('--status', action='store_true', help='检查服务状态')
    group.add_argument('--log', action='store_true', help='查看日志')
    
    # 日志行数选项
    parser.add_argument('--lines', type=int, default=50, help='查看日志时显示的行数')
    
    args = parser.parse_args()
    
    if args.start:
        start_service()
    elif args.stop:
        stop_service()
    elif args.restart:
        restart_service()
    elif args.status:
        check_status()
    elif args.log:
        view_log(args.lines)

if __name__ == "__main__":
    main() 