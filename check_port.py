#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
端口检查脚本
用于检查服务器端口是否开放
"""

import socket
import sys
import time

def check_port(host, port, timeout=5):
    """检查指定主机的端口是否开放"""
    print(f"正在检查 {host}:{port} 是否开放...")
    
    # 创建socket对象
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    # 尝试连接
    start_time = time.time()
    result = sock.connect_ex((host, port))
    end_time = time.time()
    
    # 关闭socket
    sock.close()
    
    # 检查结果
    if result == 0:
        print(f"✅ 端口 {port} 开放！响应时间: {(end_time - start_time):.3f}秒")
        return True
    else:
        print(f"❌ 端口 {port} 关闭或被阻止。错误代码: {result}")
        return False

def check_common_ports(host, ports=None):
    """检查常用端口是否开放"""
    if ports is None:
        ports = [22, 80, 443, 3306, 5432, 6379, 27017]
    
    print(f"\n正在检查 {host} 的常用端口...\n")
    
    results = {}
    for port in ports:
        results[port] = check_port(host, port)
        print("")  # 添加空行分隔
    
    # 打印摘要
    print("\n=== 端口检查摘要 ===")
    for port, is_open in results.items():
        status = "开放" if is_open else "关闭"
        print(f"端口 {port}: {status}")
    
    return results

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python check_port.py <主机> [端口]")
        print("示例: python check_port.py 172.16.0.109 3306")
        print("如果不指定端口，将检查常用端口")
        return
    
    host = sys.argv[1]
    
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
            check_port(host, port)
        except ValueError:
            print(f"错误: 端口必须是数字")
    else:
        check_common_ports(host)

if __name__ == "__main__":
    main() 