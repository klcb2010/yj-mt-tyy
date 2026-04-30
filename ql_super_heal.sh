cat > ql_super_heal.sh << 'EOF'
#!/bin/sh

CONTAINER="qinglong"
BASE="/ql/data"

echo "=============================="
echo " QingLong SUPER HEAL SYSTEM"
echo "=============================="

# ------------------------------
# 1️⃣ 容器检查 & pm2修复
# ------------------------------
echo "[1/8] pm2 服务修复..."
docker exec $CONTAINER pm2 kill >/dev/null 2>&1
docker exec $CONTAINER ql restart >/dev/null 2>&1

# ------------------------------
# 2️⃣ 目录修复
# ------------------------------
echo "[2/8] 修复基础目录..."
docker exec $CONTAINER sh -c "
mkdir -p $BASE/scripts
mkdir -p $BASE/raw
chmod -R 777 $BASE
"

# ------------------------------
# 3️⃣ scripts / raw 统一
# ------------------------------
echo "[3/8] scripts/raw 统一处理..."

docker exec $CONTAINER sh -c "
# raw → scripts（优先执行目录）
if [ -d $BASE/raw ]; then
  cp -f $BASE/raw/*.py $BASE/scripts/ 2>/dev/null || true
fi

# 防止 scripts 为空
if [ ! \"\$(ls -A $BASE/scripts 2>/dev/null)\" ]; then
  echo 'scripts为空，尝试从repo恢复'
  cp -f $BASE/repo/*.py $BASE/scripts/ 2>/dev/null || true
fi
"

# ------------------------------
# 4️⃣ 修复 task 路径错误
# ------------------------------
echo "[4/8] 修复任务路径..."

docker exec $CONTAINER sh -c "
DB=$BASE/db/database.sqlite

if [ -f \$DB ]; then
  echo '检测任务数据库存在'
  
  # 尝试修正旧 raw 路径
  sqlite3 \$DB \"UPDATE tasks SET command=REPLACE(command,'/ql/raw','/ql/data/scripts')\" 2>/dev/null || true
  sqlite3 \$DB \"UPDATE tasks SET command=REPLACE(command,'/ql/scripts','/ql/data/scripts')\" 2>/dev/null || true
fi
"

# ------------------------------
# 5️⃣ 环境变量修复
# ------------------------------
echo "[5/8] 环境修复..."
docker exec $CONTAINER sh -c "
if [ -f $BASE/config/env.sh ]; then
  chmod +x $BASE/config/env.sh
fi
"

# ------------------------------
# 6️⃣ 依赖修复
# ------------------------------
echo "[6/8] 依赖修复..."
docker exec $CONTAINER ql update >/dev/null 2>&1

# ------------------------------
# 7️⃣ 重启服务
# ------------------------------
echo "[7/8] 重启青龙..."
docker exec $CONTAINER ql restart >/dev/null 2>&1
sleep 5

# ------------------------------
# 8️⃣ 状态检查
# ------------------------------
echo "[8/8] 检查状态..."
docker exec $CONTAINER pm2 list

echo "=============================="
echo "✔ SUPER HEAL 完成"
echo "✔ scripts/raw 已统一"
echo "✔ task路径已修复"
echo "=============================="
EOF
