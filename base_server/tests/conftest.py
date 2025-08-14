from __future__ import annotations

import sys
from pathlib import Path


# 테스트에서 프로젝트 모듈을 임포트할 수 있도록 `base_server`를 sys.path에 추가
BASE_SERVER_DIR = Path(__file__).resolve().parents[1]
base_server_path = str(BASE_SERVER_DIR)
if base_server_path not in sys.path:
    sys.path.insert(0, base_server_path)


