# pip install openai

import os
from openai import OpenAI, APIError

# 방법 1) 환경변수 OPENAI_API_KEY 사용 (권장)
# 방법 2) 아래 API_KEY 변수에 직접 붙여넣기
API_KEY = """sk-proj-bpTVKxPgjDa4BpMs8yf8DNigIWIvaGbd-317vAwRDdxuBEJcwFaY5vajuReRkev-uojgacb2lT3BlbkFJ0pwUjqzCmiUKmVeEOA1io60W5o_wuI8Pq8CKJKJfFFUIM8Bme-XXda9TIml6Z8aI8moEK_vDMA"""

MODEL = "gpt-4.1-mini"  # 가볍고 저렴한 일반 질의응답용 모델

# TODO: 여기에 물어볼 질문을 적으세요. (비워두면 실행 시 입력받습니다)
question = """나스닥에 상장된 기업 중에서 성장형이며, 나스닥 top 100이하, 500이상의 투자하기 좋은 주식의 티커를 10개주세요. 
최대한 많은 데이터를 가지고 추론해서 답을 하세요.
답은 티커만 주세요. 예시:["","","",""]"""

def main():
    key = API_KEY.strip()
    if not key:
        raise RuntimeError("API 키가 없습니다. 환경변수 OPENAI_API_KEY를 설정하거나 코드의 API_KEY에 붙여넣어 주세요.")

    client = OpenAI(api_key=key)

    q = question.strip() or input("질문을 입력하세요: ").strip()
    if not q:
        print("질문이 비어있습니다. 종료합니다.")
        return

    try:
        resp = client.responses.create(
            model=MODEL,
            input=q,
        )
        # 모델이 만들어준 최종 텍스트(편의 속성)
        print(resp.output_text)
    except APIError as e:
        print(f"[API 오류] {e}")
    except Exception as e:
        print(f"[오류] {e}")

if __name__ == "__main__":
    main()
