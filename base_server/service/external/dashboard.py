from html import parser
import requests
import websocket
import json
import argparse

# OAuth2 접근 토큰 발급
def get_access_token(appkey, appsecret):
    url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    data = {
        "grant_type": "client_credentials",
        "appkey": appkey,
        "appsecret": appsecret
    }
    response = requests.post(url, json=data)
    return response.json()["access_token"]

# 웹소켓 접속키 발급
def get_ws_approval_key(access_token, appkey, appsecret):
    url = "https://openapi.koreainvestment.com:9443/oauth2/Approval"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appkey": appkey,
        "appsecret": appsecret,
    }
    data = {
        "grant_type": "client_credentials",
        "appkey": appkey,
        "secretkey": appsecret
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["approval_key"]

# 웹소켓 콜백 함수
def on_message(ws, message):
    try:
        data = json.loads(message)
        print("▶ 최초 JSON 응답:", data)
    except json.JSONDecodeError:
        handle_pipe_message(message)

def handle_pipe_message(message):
    segments = message.split('|')
    if segments[0] == '0' and segments[1] == 'H0STCNT0':
        payload = segments[3].split('^')

        result = {
            "종목코드": payload[0],
            "체결시간": payload[1],
            "현재가": payload[2],
            "전일대비": payload[4],
            "등락률(%)": payload[5],
            "거래량": payload[12],
            "누적거래량": payload[13],
            "누적거래대금": payload[14],
            "시가": payload[7],
            "고가": payload[8],
            "저가": payload[9],
        }

        print("▶ 실시간 시세:", result)
    else:
        print("▶ 알 수 없는 메시지 형식:", message)


def on_error(ws, error):
    print("▶ 오류 발생:", error)

def on_close(ws, close_status_code, close_msg):
    print("▶ 웹소켓 연결 종료")

def on_open(ws, approval_key, code):
    print("▶ 웹소켓 연결 성공! 구독 시작...")
    subscribe_data = {
        "header": {
            "approval_key": approval_key,
            "custtype": "P",      # 개인(P), 법인(B)
            "tr_type": "1",       # 실시간 데이터 요청
            "content-type": "utf-8"
        },
        "body": {
            "input": {
                "tr_id": "H0STCNT0",   # 주식 현재가 실시간 조회
                "tr_key": code         # 주식 종목 코드
            }
        }
    }
    ws.send(json.dumps(subscribe_data))

# 메인 CLI 코드
def main():
    parser = argparse.ArgumentParser(description="한국투자증권 OpenAPI 웹소켓 실시간 시세 조회 CLI")
    parser.add_argument("--appkey", required=True, help="한국투자증권에서 받은 본인의 APP_KEY 입력")
    parser.add_argument("--appsecret", required=True, help="한국투자증권에서 받은 본인의 APP_SECRET 입력")

    parser.add_argument("--code", required=True, help="조회할 주식 종목 코드 (예: 삼성전자: 005930)")
    parser.add_argument("--mode", default="prod", choices=["prod", "test"], help="서비스 환경(prod/test)")

    args = parser.parse_args()

    access_token = get_access_token(args.appkey, args.appsecret)
    approval_key = get_ws_approval_key(access_token, args.appkey, args.appsecret)

    ws_url = "ws://ops.koreainvestment.com:31000" if args.mode == "prod" else "ws://ops.koreainvestment.com:21000"

    ws = websocket.WebSocketApp(
        ws_url,
        header=[
            f"approval_key:{approval_key}",
            f"authorization:Bearer {access_token}",
            f"appkey:{args.appkey}",
            f"appsecret:{args.appsecret}"
        ],
        on_open=lambda ws: on_open(ws, approval_key, args.code),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()

if __name__ == "__main__":
    main()
