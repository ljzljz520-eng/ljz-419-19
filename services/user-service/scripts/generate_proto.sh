#!/bin/bash
# 从 .proto 文件生成 Python gRPC 代码
# 用法: bash scripts/generate_proto.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

PROTO_DIR="$PROJECT_DIR/protos"
OUTPUT_DIR="$PROJECT_DIR/app/protos"

echo "📦 生成 gRPC Python 代码..."
echo "  Proto 目录: $PROTO_DIR"
echo "  输出目录: $OUTPUT_DIR"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 生成 Python gRPC 代码
python -m grpc_tools.protoc \
    -I "$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR/user.proto"

# 创建 __init__.py
cat > "$OUTPUT_DIR/__init__.py" << 'EOF'
"""
gRPC 自动生成的 protobuf Python 代码
由 scripts/generate_proto.sh 脚本生成
"""
EOF

# 修复 import 路径 (grpc_tools 生成的 import 路径需要调整)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's/import user_pb2/from app.protos import user_pb2/' "$OUTPUT_DIR/user_pb2_grpc.py"
else
    # Linux
    sed -i 's/import user_pb2/from app.protos import user_pb2/' "$OUTPUT_DIR/user_pb2_grpc.py"
fi

echo "✅ gRPC 代码生成完成!"
echo "  - $OUTPUT_DIR/user_pb2.py"
echo "  - $OUTPUT_DIR/user_pb2_grpc.py"
