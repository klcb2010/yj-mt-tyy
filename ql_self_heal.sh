cat > ql_self_heal.sh << 'EOF'
#!/bin/sh

CONTAINER="qinglong"

echo "=============================="
echo " QingLong Self Heal System"
echo "=============================="

# 1️⃣ 检查容器是否存在
echo "[1/6] 检查容器状态..."
docker ps | grep $CONTAINER >/dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "❌ 容器未运行，尝试启动..."
  docker start $CONTAINER
  sleep 5
fi

# 2️⃣ pm2 清理
echo "[2/6] 清理 pm2..."
docker exec $CONTAINER pm2 kill >/dev/null 2>&1

# 3️⃣ 修复权限
echo "[3/6] 修复目录权限..."
docker exec $CONTAINER sh -c "chmod -R 777 /ql/data"

# 4️⃣ 修复依赖
echo "[4/6] 修复青龙基础服务..."
docker exec $CONTAINER ql update >/dev/null 2>&1

# 5️⃣ 重启服务
echo "[5/6] 重启青龙服务..."
docker exec $CONTAINER ql restart >/dev/null 2>&1

# 6️⃣ 等待检查
echo "[6/6] 等待服务恢复..."
sleep 5

docker exec $CONTAINER pm2 list

echo "=============================="
echo "✔ 自愈执行完成"
echo "访问：http://IP:5700"
echo "=============================="
EOF
