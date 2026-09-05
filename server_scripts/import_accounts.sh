#!/bin/bash
# Finance Suite 账号批量同步脚本
# 在服务器 /home/ubuntu/finance-suite-web/ 目录下执行
# 可重复执行：会补齐缺失账号，并重置默认账号密码/权限到标准值。

set -e
cd /home/ubuntu/finance-suite-web

echo "===== 同步账号数据库 ====="
python3 server_scripts/manage_users.py sync-defaults
