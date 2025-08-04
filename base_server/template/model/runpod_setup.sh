#!/bin/bash

# RunPod 환경 설정 스크립트
# GPU 환경에서 주식 예측 API 서버를 설정하고 실행

set -e

echo "🚀 Starting RunPod Setup for Stock Prediction API..."

# 시스템 업데이트
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# 필수 시스템 패키지 설치
echo "📦 Installing system dependencies..."
apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    tmux \
    screen \
    nano \
    vim

# Python 환경 확인 및 설정
echo "🐍 Checking Python environment..."

# 사용 가능한 Python 버전 확인
echo "🔍 Available Python versions:"
ls -la /usr/bin/python* 2>/dev/null || echo "No python in /usr/bin/"
which python3.11 2>/dev/null && echo "✅ python3.11 found: $(which python3.11)"
which python3 2>/dev/null && echo "✅ python3 found: $(which python3)"
which python 2>/dev/null && echo "✅ python found: $(which python)"

# Python 실행 가능한 명령어 찾기 (우선순위: python3.11 > python3 > python)
PYTHON_CMD=""
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✅ Using python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✅ Using python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✅ Using python"
else
    echo "❌ No Python found!"
    exit 1
fi

# python 명령어가 없으면 심볼릭 링크 생성 (로컬 bin 디렉토리 사용)
if ! command -v python &> /dev/null; then
    echo "🔗 Creating python symlink..."
    mkdir -p ~/bin
    ln -sf $(which $PYTHON_CMD) ~/bin/python
    export PATH="$HOME/bin:$PATH"
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    echo "✅ python symlink created in ~/bin/"
fi

# pip 명령어 확인 및 설정
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
    echo "✅ Using pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
    echo "✅ Using pip"
else
    echo "❌ No pip found!"
    exit 1
fi

# pip 명령어가 없으면 심볼릭 링크 생성
if ! command -v pip &> /dev/null; then
    echo "🔗 Creating pip symlink..."
    mkdir -p ~/bin
    ln -sf $(which $PIP_CMD) ~/bin/pip
    echo "✅ pip symlink created in ~/bin/"
fi

# Python 및 pip 버전 확인 (감지된 명령어 사용)
echo "📋 Python and pip versions:"
$PYTHON_CMD --version
$PYTHON_CMD -m pip --version

# python 명령어 최종 확인
if command -v python &> /dev/null; then
    echo "✅ 'python' command is now available"
    python --version
else
    echo "⚠️ 'python' command not available, using $PYTHON_CMD"
fi

# GPU 확인
echo "🎮 Checking GPU availability..."
nvidia-smi

# 프로젝트 의존성 설치
echo "📚 Installing Python dependencies..."
$PYTHON_CMD -m pip install --upgrade pip setuptools wheel
$PYTHON_CMD -m pip install -r requirements.txt

# CUDA 호환성 확인 및 PyTorch GPU 테스트
echo "🔍 Testing PyTorch GPU support..."
$PYTHON_CMD -c "
try:
    import torch
    print('✅ PyTorch version:', torch.__version__)
    print('✅ CUDA available:', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('✅ GPU device:', torch.cuda.get_device_name(0))
        print('✅ GPU count:', torch.cuda.device_count())
        print('✅ CUDA version:', torch.version.cuda)
    else:
        print('⚠️ CUDA not available (will use CPU)')
except ImportError:
    print('⚠️ PyTorch not installed yet (will be installed with requirements.txt)')
except Exception as e:
    print('⚠️ PyTorch test failed:', str(e))
"

# 작업 디렉토리를 /workspace로 이동
echo "📁 Setting up workspace directory..."
cd /workspace

# 디렉토리 구조 생성 (/workspace 하위에)
echo "📁 Creating directory structure in /workspace..."
mkdir -p /workspace/data /workspace/models /workspace/logs /workspace/outputs /workspace/temp

# 권한 설정
echo "🔐 Setting permissions..."
chmod +x *.py
chmod +x *.sh

# 환경 변수 설정
echo "⚙️ Setting up environment variables..."
export PYTHONPATH=/workspace:$PYTHONPATH
export CUDA_VISIBLE_DEVICES=0
export TF_FORCE_GPU_ALLOW_GROWTH=true
export TF_CPP_MIN_LOG_LEVEL=1

# .bashrc에 환경 변수 추가
echo "
# Stock Prediction API Environment
export PYTHONPATH=/workspace:\$PYTHONPATH
export CUDA_VISIBLE_DEVICES=0
export TF_FORCE_GPU_ALLOW_GROWTH=true
export TF_CPP_MIN_LOG_LEVEL=1
" >> ~/.bashrc

# 데이터 수집 테스트 (옵션)
echo "📊 Testing data collection (optional)..."
$PYTHON_CMD -c "
try:
    from data_collector import StockDataCollector
    collector = StockDataCollector()
    data = collector.get_recent_data('AAPL', 10)
    if data is not None:
        print('✅ Data collection test passed')
    else:
        print('⚠️ Data collection test failed - no data returned')
except Exception as e:
    print(f'⚠️ Data collection test failed: {e}')
"

# RunPod용 실행 스크립트 생성
echo "📝 Creating RunPod execution scripts..."

# 학습 스크립트 (동적 생성)
cat > train_model_runpod.sh << EOF
#!/bin/bash
echo "🔥 Starting model training on RunPod..."
cd /workspace
echo "📁 Current directory: \$(pwd)"
echo "📊 Models will be saved to: /workspace/models/"
echo "🐍 Using Python: $PYTHON_CMD"
tmux new-session -d -s training 'cd /workspace && $PYTHON_CMD train_model.py --epochs 50 --batch-size 64 --model-type lstm_attention'
echo "✅ Training started in tmux session 'training'"
echo "Use 'tmux attach -t training' to monitor progress"
EOF

# API 서버 실행 스크립트 (동적 생성)
cat > start_api_runpod.sh << EOF
#!/bin/bash
echo "🌐 Starting API server on RunPod..."
cd /workspace
echo "📁 Current directory: \$(pwd)"
echo "📊 Loading models from: /workspace/models/"
echo "🐍 Using Python: $PYTHON_CMD"
tmux new-session -d -s api 'cd /workspace && $PYTHON_CMD api_server.py'
echo "✅ API server started in tmux session 'api'"
echo "Server is running on http://0.0.0.0:8000"
echo "Use 'tmux attach -t api' to monitor server"
EOF

# 배치 추론 스크립트 (동적 생성)
cat > batch_inference_runpod.sh << EOF
#!/bin/bash
echo "🔮 Starting batch inference on RunPod..."
cd /workspace
echo "📁 Current directory: \$(pwd)"
echo "📊 Loading models from: /workspace/models/"
echo "🐍 Using Python: $PYTHON_CMD"
SYMBOLS="AAPL MSFT GOOGL AMZN NVDA TSLA META NFLX AMD INTC"
tmux new-session -d -s inference "cd /workspace && $PYTHON_CMD inference_pipeline.py --symbols \$SYMBOLS --batch-size 5 --output /workspace/outputs/batch_predictions.json"
echo "✅ Batch inference started in tmux session 'inference'"
echo "Use 'tmux attach -t inference' to monitor progress"
EOF

chmod +x *.sh

# RunPod 포트 설정 안내
echo "🌐 Port Configuration for RunPod:"
echo "   - API Server: 8000 (HTTP)"
echo "   - MongoDB: 27017 (if using)"
echo "   - Redis: 6379 (if using)"
echo ""
echo "Make sure to expose port 8000 in your RunPod configuration!"

# Jupyter 노트북 설정 (선택사항)
echo "📓 Setting up Jupyter notebook (optional)..."
$PYTHON_CMD -m pip install jupyter jupyterlab

# Jupyter 설정
cat > jupyter_config.py << 'EOF'
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
c.NotebookApp.token = ''
c.NotebookApp.password = ''
c.NotebookApp.allow_root = True
EOF

# 모니터링 스크립트
cat > monitor_system.sh << 'EOF'
#!/bin/bash
echo "🖥️ System Monitoring"
echo "===================="
echo "GPU Status:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits
echo ""
echo "Python Processes:"
ps aux | grep python
echo ""
echo "Disk Usage:"
df -h
echo ""
echo "Memory Usage:"
free -h
EOF

chmod +x monitor_system.sh

# 설정 완료 메시지
echo ""
echo "🎉 RunPod setup completed successfully!"
echo ""
echo "📁 Working directory: /workspace (persistent storage)"
echo "📊 Models will be saved to: /workspace/models/ (persistent)"
echo "📈 Data will be stored in: /workspace/data/ (persistent)"
echo "📋 Logs will be saved to: /workspace/logs/ (persistent)"
echo ""
echo "Available commands:"
echo "  🔥 ./train_model_runpod.sh     - Start model training (saves to /workspace/models/)"
echo "  🌐 ./start_api_runpod.sh       - Start API server (loads from /workspace/models/)"
echo "  🔮 ./batch_inference_runpod.sh - Run batch inference"
echo "  🖥️ ./monitor_system.sh         - Monitor system resources"
echo ""
echo "Tmux sessions management:"
echo "  - List sessions: tmux ls"
echo "  - Attach to session: tmux attach -t [session_name]"
echo "  - Detach from session: Ctrl+B then D"
echo ""
echo "API Endpoints (once server is running):"
echo "  - Health check: http://localhost:8000/health"
echo "  - Single prediction: POST http://localhost:8000/predict"
echo "  - Batch prediction: POST http://localhost:8000/predict/batch"
echo "  - Model info: http://localhost:8000/models/info"
echo ""
echo "📖 Check the README.md for detailed usage instructions"
echo "🚀 Happy trading with AI predictions!"