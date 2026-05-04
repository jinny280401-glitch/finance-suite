#!/bin/bash
# Finance Suite 账号批量导入脚本
# 在服务器 /home/ubuntu/finance-suite-web/ 目录下执行

set -e
cd /home/ubuntu/finance-suite-web

echo "===== 初始化账号数据库 ====="

# 内测账号
python3 server_scripts/manage_users.py add linzuxi    <REMOVED_SECRET>    vip
python3 server_scripts/manage_users.py add danny      ***REDACTED***  vip
python3 server_scripts/manage_users.py add ivan       ***REDACTED***   vip
python3 server_scripts/manage_users.py add shengwei   <REMOVED_SECRET>     vip
python3 server_scripts/manage_users.py add vanilla    ***REDACTED***  vip
python3 server_scripts/manage_users.py add nanjian    ***REDACTED***     vip
python3 server_scripts/manage_users.py add fengzhijie ***REDACTED***    vip
python3 server_scripts/manage_users.py add lianghailin ***REDACTED***   vip
python3 server_scripts/manage_users.py add demo       <REMOVED_SECRET>     free
python3 server_scripts/manage_users.py add zhuanz     <REMOVED_SECRET>   admin

# 华福证券账号
python3 server_scripts/manage_users.py add hfzq      <REMOVED_SECRET>       vip

echo ""
echo "===== 当前用户列表 ====="
python3 server_scripts/manage_users.py list
