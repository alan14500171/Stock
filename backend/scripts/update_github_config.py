#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import argparse

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'check_github_updates.py')

def read_config_file():
    """读取配置文件内容"""
    if not os.path.exists(CONFIG_FILE):
        print(f"错误: 配置文件不存在: {CONFIG_FILE}")
        sys.exit(1)
        
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def write_config_file(content):
    """写入配置文件内容"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"配置已更新: {CONFIG_FILE}")

def update_config(content, key, value):
    """更新配置文件中的特定键值"""
    # 对于字符串值，添加引号
    if isinstance(value, str):
        value = f'"{value}"'
    elif isinstance(value, bool):
        value = str(value)
    
    # 使用正则表达式查找并替换配置项
    pattern = rf'(\s+{key}\s*=\s*).*'
    replacement = f"\\1{value}"
    
    updated_content = re.sub(pattern, replacement, content)
    
    # 检查是否成功替换
    if updated_content == content:
        print(f"警告: 未找到配置项 {key} 或无法更新")
        return content
        
    return updated_content

def update_command_list(content, commands):
    """更新POST_UPDATE_COMMANDS列表"""
    # 构建命令列表字符串
    commands_str = "[\n"
    for cmd in commands:
        commands_str += f'        "{cmd}",\n'
    commands_str += "    ]"
    
    # 使用正则表达式查找并替换命令列表
    pattern = r'(\s+POST_UPDATE_COMMANDS\s*=\s*)\[.*?\]'
    replacement = f"\\1{commands_str}"
    
    # 使用DOTALL模式匹配多行
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 检查是否成功替换
    if updated_content == content:
        print(f"警告: 未找到POST_UPDATE_COMMANDS配置或无法更新")
        return content
        
    return updated_content

def main():
    parser = argparse.ArgumentParser(description='配置GitHub自动更新工具')
    
    parser.add_argument('--owner', help='GitHub仓库所有者用户名')
    parser.add_argument('--repo', help='GitHub仓库名称')
    parser.add_argument('--branch', help='要监控的分支名称')
    parser.add_argument('--token', help='GitHub API访问令牌')
    parser.add_argument('--interval', type=int, help='检查间隔（秒）')
    parser.add_argument('--path', help='本地仓库路径')
    parser.add_argument('--auto-update', dest='auto_update', action='store_true', help='启用自动更新')
    parser.add_argument('--no-auto-update', dest='auto_update', action='store_false', help='禁用自动更新')
    parser.add_argument('--backup', dest='backup', action='store_true', help='启用更新前备份')
    parser.add_argument('--no-backup', dest='backup', action='store_false', help='禁用更新前备份')
    parser.add_argument('--backup-dir', help='备份目录路径')
    parser.add_argument('--add-command', action='append', help='添加更新后执行的命令')
    parser.add_argument('--clear-commands', action='store_true', help='清除所有更新后执行的命令')
    
    args = parser.parse_args()
    
    # 读取当前配置
    content = read_config_file()
    
    # 更新配置
    if args.owner:
        content = update_config(content, 'REPO_OWNER', args.owner)
    
    if args.repo:
        content = update_config(content, 'REPO_NAME', args.repo)
    
    if args.branch:
        content = update_config(content, 'BRANCH', args.branch)
    
    if args.token:
        content = update_config(content, 'GITHUB_TOKEN', args.token)
    
    if args.interval:
        content = update_config(content, 'CHECK_INTERVAL', args.interval)
    
    if args.path:
        content = update_config(content, 'LOCAL_REPO_PATH', args.path)
    
    if args.auto_update is not None:
        content = update_config(content, 'AUTO_UPDATE', args.auto_update)
    
    if args.backup is not None:
        content = update_config(content, 'BACKUP_BEFORE_UPDATE', args.backup)
    
    if args.backup_dir:
        content = update_config(content, 'BACKUP_DIR', args.backup_dir)
    
    # 处理命令列表
    if args.clear_commands:
        content = update_command_list(content, [])
    elif args.add_command:
        # 提取当前命令列表
        match = re.search(r'POST_UPDATE_COMMANDS\s*=\s*\[(.*?)\]', content, re.DOTALL)
        current_commands = []
        if match:
            # 提取命令字符串并清理
            cmd_block = match.group(1).strip()
            if cmd_block:
                for line in cmd_block.split('\n'):
                    line = line.strip()
                    if line.startswith('"') or line.startswith("'"):
                        # 提取引号中的命令并去除尾部逗号
                        cmd = re.search(r'["\'](.*?)["\'],?', line)
                        if cmd:
                            current_commands.append(cmd.group(1))
        
        # 添加新命令
        for cmd in args.add_command:
            if cmd not in current_commands:
                current_commands.append(cmd)
        
        # 更新命令列表
        content = update_command_list(content, current_commands)
    
    # 写入更新后的配置
    write_config_file(content)
    
    print("配置更新完成！")

if __name__ == "__main__":
    main() 