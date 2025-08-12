# ── 설정 ───────────────────────────────────────────────────────────────

import json
import time
import threading
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import websocket

# ── 설정 ───────────────────────────────────────────────────────────────

APP_KEY     = "PSsXlKpjtkBnvtb2P2gMtSo8uB7MnLPL2fmv"
APP_SECRET  = "MBD52Fyyi7iZ/ScazxbYaYrQC/PCbfN8go8Xl0Yxe//biMvAtORlQJIwI543WeoSJo/zUHYkDRucAMVJz+Y05aAu92W+dRWMYxP0y9/etrs/1INSzHoj3/NzOwwF1pyxu6UOg1tK/69qeQUJUIpc8Vz8Q+VXavtG8eYLBmaB+fhZyvr3BXg="

REST_URL    = "https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/dailyprice"
TR_ID_DAILY = "HHDFS76240000"

SYMBOLS = [
    "QQQ", "QQQM", "QQQJ", "ONEQ", "TQQQ", "SQQQ",
    "IBIT", "TSLL", "QYLD", "GLDI", "SLVO"
]

# ── 인증 및 기기 정보 ──────────────────────────────────────────────────

def get_access_token(appkey: str, appsecret: str) -> str:
    url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    headers = {"Content-Type": "application/json; utf-8"}
    body = {
        "grant_type": "client_credentials",
        "appkey":     appkey,
        "appsecret":  appsecret
    }
    resp = requests.post(url, json=body, headers=headers, timeout=5)
    resp.raise_for_status()
    return resp.json()["access_token"]

def get_mac_address() -> str:
    mac = uuid.getnode()
    return ":".join(format((mac >> (8 * i)) & 0xFF for i in reversed(range(6))))

ACCESS_TOKEN = get_access_token(APP_KEY, APP_SECRET)
MAC_ADDRESS  = get_mac_address()

# ── 종가 조회 (REST API) ───────────────────────────────────────────────

def get_closing_price(symbol: str, market_code: str, yyyymmdd: str) -> str:
    headers = {
        "content-type":  "application/json; charset=utf-8",
        "appkey":        APP_KEY,
        "appsecret":     APP_SECRET,
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_id":         TR_ID_DAILY,
        "custtype":      "P",
        "mac_address":   MAC_ADDRESS,
    }
    params = {
        "AUTH": "",
        "GUBN": "0",
        "BYMD": yyyymmdd,
        "MODP": "0",
        "EXCD": market_code,
        "SYMB": symbol
    }
    resp = requests.get(REST_URL, headers=headers, params=params, timeout=5)
    resp.raise_for_status()
    result = resp.json()
    try:
        return result["output2"][0]["clos"]
    except (KeyError, IndexError):
        return "(데이터 없음)"

# ── WebSocket 실시간 수신 ─────────────────────────────────────────────

received_data = {}
ws_obj = None

def on_message(ws, message):
    global received_data
    msg = json.loads(message)
    tr_key = msg.get("header", {}).get("tr_key")
    if tr_key:
        received_data[tr_key] = msg
        print(f"[WebSocket] {tr_key} 시세 수신됨")

def on_error(ws, error):
    print(f"[WebSocket 오류]: {error}")

def on_close(ws, code, reason):
    print("[WebSocket] 연결 종료")

def on_open(ws):
    print("[WebSocket] 연결 성공")
    for sym in SYMBOLS:
        req = {
            "header": {
                "tr_id": "HDFSCNT0",
                "tr_key": sym
            }
        }
        ws.send(json.dumps(req))
        time.sleep(0.1)  # 과도한 요청 방지

def start_websocket():
    global ws_obj
    url = "ws://ops.koreainvestment.com:21000"  # 실제 WebSocket 주소 필요
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws_obj = ws
    thread = threading.Thread(target=ws.run_forever, daemon=True)
    thread.start()
    return ws

def wait_for_websocket_data(timeout=10):
    for _ in range(timeout):
        if len(received_data) > 0:
            return True
        time.sleep(1)
    return False

# ── 메인 ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    today = datetime.now(tz=ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")

    print("▶ 실시간 WebSocket 시도 중...")
    start_websocket()

    if wait_for_websocket_data(timeout=10):
        print("✅ 실시간 시세 수신 성공 (WebSocket)")
        for sym, data in received_data.items():
            price = data.get("body", {}).get("stck_prpr", "N/A")
            print(f"{sym} 실시간 가격: {price}")
    else:
        print("❌ 실시간 수신 실패 → REST API로 전환")
        for sym in SYMBOLS:
            close = get_closing_price(sym, "NAS", today)
            print(f"{sym} ({today}) 종가: {close}")
            time.sleep(1)
