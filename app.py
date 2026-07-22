import google.generativeai as genai
import streamlit as st

st.set_page_config(
    page_title="국내주식 5단계 정밀 분석기", page_icon="📈", layout="wide"
)

st.title("📈 AI 국내주식 5단계 정밀 분석 시스템")
st.caption(
    "이평선(5/20/60/112/224일) 기반 차트 지도, 3자 종합 토론, 실전 모의투자 세팅 제공"
)

# API 키 설정 (보안)
api_key = st.sidebar.text_input("Gemini API Key를 입력하세요:", type="password")
st.sidebar.markdown(
    "[API Key 무료 발급 링크](https://aistudio.google.com/app/apikey)"
)

stock_name = st.text_input(
    "분석할 종목명 또는 종목코드를 입력하세요:",
    placeholder="예: 삼성전자, 대원전선, 한화오션",
)

if st.button("🚀 실시간 정밀 분석 시작", type="primary"):
    if not api_key:
        st.error("좌측 사이드바에 Gemini API Key를 입력해주세요!")
    elif not stock_name:
        st.warning("분석할 종목명을 입력해주세요.")
    else:
        with st.spinner(f"'{stock_name}' 종목 정밀 분석 보고서 생성 중..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash-8b")

                prompt = f"""
                너는 KOSPI/KOSDAQ 분석 전문 트레이더이자 리서치 애널리스트야.
                '{stock_name}' 종목에 대해 아래 5단계 양식에 맞춰 완벽히 분석해줘.

                [분석 수행 필수 조건]
                1. 분석 요청 시점의 실시간 최신 데이터(당일 시가, 고가, 저가, 현재가, 거래량 등)를 반영할 것.
                2. 5일, 20일, 60일, 112일, 224일 이동평균선 배열 상태 및 이격도 분석을 기술적 분석에 필수 포함할 것.
                3. 직관적인 텍스트 차트 지도, 3자 토론 비교표, 모의투자 가이드를 포함할 것.

                ---
                [답변 출력 양식]
                1. 📈 실시간 주가 & 기술적 차트 지도 (5/20/60/112/224일 이평선 정밀 분석)
                2. 💡 핵심 펀더멘털 & 모멘텀 요약
                3. 🗣️ 3자 전문가 종합 토론 (증권사 애널리스트 / 수급 트레이더 / AI 전문가)
                4. 📊 관점별 분석 & 대응 전략 종합 비교표 (마크다운 표)
                5. 🎮 실전 모의투자 시뮬레이션 (이평선 기반 진입가/익절가/손절가/손익비)
                """

                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")
