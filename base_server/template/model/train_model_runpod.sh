#!/bin/bash
echo "🔥 Starting model training on RunPod..."
cd /workspace
echo "📁 Current directory: $(pwd)"
echo "📊 Models will be saved to: /workspace/models/"
tmux new-session -d -s training 'cd /workspace && python train_model.py --epochs 50 --batch-size 64 --model-type lstm_attention'
echo "✅ Training started in tmux session 'training'"
echo "Use 'tmux attach -t training' to monitor progress"