#!/bin/bash
# Finance Suite 后端代码部署脚本
# 在 ECS 8.138.2.55 上执行，更新 Wind API 和数据源修复

set -e

echo "===== Finance Suite 后端部署 ====="
echo "目标：修复 Wind API 连接稳定性 + 数据源降级 bug"
echo ""

# 检测部署路径
if [ -d "/home/admin/.openclaw/workspace-linmeimei/skills/finance-suite" ]; then
    DEPLOY_PATH="/home/admin/.openclaw/workspace-linmeimei/skills/finance-suite"
elif [ -d "/home/ubuntu/finance-suite" ]; then
    DEPLOY_PATH="/home/ubuntu/finance-suite"
else
    echo "❌ 未找到 finance-suite 部署路径"
    echo "请手动指定路径或检查目录结构"
    exit 1
fi

echo "✓ 检测到部署路径: $DEPLOY_PATH"
echo ""

cd "$DEPLOY_PATH"

echo "===== 1. 备份当前版本 ====="
BACKUP_DIR="$DEPLOY_PATH/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp scripts/stock_data.py "$BACKUP_DIR/" 2>/dev/null || true
cp scripts/wind_data.py "$BACKUP_DIR/" 2>/dev/null || true
echo "✓ 备份完成: $BACKUP_DIR"
echo ""

echo "===== 2. 拉取最新代码 ====="
git fetch origin
git status
echo ""
echo "当前分支状态 ↑"
echo ""
read -p "是否拉取最新代码？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git pull origin main
    echo "✓ 代码已更新"
else
    echo "⊘ 跳过拉取"
fi
echo ""

echo "===== 3. 检查修复内容 ====="
echo "本次修复的 3 个 bug："
echo "  A. stock_data.py:_is_realtime_stale() - 修复缓存时间判断"
echo "  B. wind_data.py:_wsd_to_dict/_wss_to_dict - 修复空指针保护"
echo "  C. stock_data.py:_load_stock_cache() - 添加 AkShare 超时保护"
echo ""
echo "额外优化："
echo "  - Wind 连接超时 15s→30s，添加 2 次重试"
echo "  - Wind 支持自动重连"
echo ""

echo "===== 4. 重启服务 ====="
echo "检测运行中的 Python 进程..."
ps aux | grep -E "mcp_server.py|finance-suite" | grep -v grep || echo "未检测到运行中的服务"
echo ""
read -p "是否需要重启服务？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "请手动重启服务（根据实际部署方式）："
    echo "  - systemd: sudo systemctl restart finance-suite"
    echo "  - supervisor: supervisorctl restart finance-suite"
    echo "  - 手动: pkill -f mcp_server.py && nohup python mcp_server.py &"
else
    echo "⊘ 跳过重启"
fi
echo ""

echo "===== 5. 验证部署 ====="
echo "测试 Wind 连接..."
python3 -c "
import sys
sys.path.insert(0, 'scripts')
import wind_data
result = wind_data.check_connection()
print('Wind 连接状态:', result)
" 2>&1 || echo "⚠ Wind 测试失败（可能是 Wind 终端未登录）"
echo ""

echo "===== 部署完成 ====="
echo "修复内容已部署到: $DEPLOY_PATH"
echo "备份位置: $BACKUP_DIR"
echo ""
echo "下一步："
echo "1. 如果服务未重启，请手动重启"
echo "2. 测试 Wind API 连接是否稳定"
echo "3. 观察日志确认数据源降级是否正常工作"
