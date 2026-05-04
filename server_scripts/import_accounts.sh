#!/bin/bash
# Finance Suite 账号批量导入脚本
# 在服务器 /home/ubuntu/finance-suite-web/ 目录下执行

set -e
cd /home/ubuntu/finance-suite-web

echo "===== 初始化账号数据库 ====="

# 内测账号
python3 server_scripts/manage_users.py add linzuxi    lzx123456    vip
python3 server_scripts/manage_users.py add danny      danny123456  vip
python3 server_scripts/manage_users.py add ivan       ivan123456   vip
python3 server_scripts/manage_users.py add shengwei   86869945     vip
python3 server_scripts/manage_users.py add vanilla    lemon123456  vip
python3 server_scripts/manage_users.py add nanjian    nj123456     vip
python3 server_scripts/manage_users.py add fengzhijie fzj123456    vip
python3 server_scripts/manage_users.py add lianghailin lhl123456   vip
python3 server_scripts/manage_users.py add demo       demo2026     free
python3 server_scripts/manage_users.py add zhuanz     zhuanz0405   admin

# 华福证券账号
python3 server_scripts/manage_users.py add hfzq      hf1234       vip

echo ""
echo "===== 当前用户列表 ====="
python3 server_scripts/manage_users.py list
