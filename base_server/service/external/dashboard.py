import requests
import websocket
import json
import threading


class KoreaInvestSimpleWSClient:
    def __init__(self, appkey, appsecret, mode="prod"):
        self.appkey = appkey
        self.appsecret = appsecret
        self.access_token = None
        self.approval_key = None
        self.ws = None
        self.thread = None
        self.mode = mode
        self.tr_id = "H0STCNT0"
        self.subscribed_codes = []

    def get_access_token(self):
        url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
        data = {
            "grant_type": "client_credentials",
            "appkey": self.appkey,
            "appsecret": self.appsecret
        }
        response = requests.post(url, json=data)
        self.access_token = response.json()["access_token"]

    def get_approval_key(self):
        url = "https://openapi.koreainvestment.com:9443/oauth2/Approval"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
        }
        data = {
            "grant_type": "client_credentials",
            "appkey": self.appkey,
            "secretkey": self.appsecret
        }
        response = requests.post(url, headers=headers, json=data)
        self.approval_key = response.json()["approval_key"]

    def _on_open(self, ws):
        print("▶ 웹소켓 연결 성공! 구독 시작...")
        for code in self.subscribed_codes:
            self.subscribe_code(ws, code)

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            print("▶ 최초 JSON 응답:", data)
        except json.JSONDecodeError:
            self.handle_pipe_message(message)

    def handle_pipe_message(self, message):
        segments = message.split('|')
        if segments[0] == '0' and segments[1] == self.tr_id:
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

    def _on_error(self, ws, error):
        print("▶ 오류 발생:", error)

    def _on_close(self, ws, code, msg):
        print("▶ 웹소켓 연결 종료")

    def subscribe_code(self, ws, code):
        subscribe_data = {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": self.tr_id,
                    "tr_key": code
                }
            }
        }
        ws.send(json.dumps(subscribe_data))
        print(f"▶ 구독 요청 전송: {code}")

    def connect(self, codes):
        self.subscribed_codes = codes
        self.get_access_token()
        self.get_approval_key()
        ws_url = "ws://ops.koreainvestment.com:31000" if self.mode == "prod" else "ws://ops.koreainvestment.com:21000"

        self.ws = websocket.WebSocketApp(
            ws_url,
            header=[
                f"approval_key:{self.approval_key}",
                f"authorization:Bearer {self.access_token}",
                f"appkey:{self.appkey}",
                f"appsecret:{self.appsecret}"
            ],
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.start()

    def disconnect(self):
        if self.ws:
            self.ws.close()
            self.thread.join()
            print("🛑 웹소켓 연결 해제 완료")
