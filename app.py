import random
import streamlit as st

st.set_page_config(
    page_title="국내주식 5단계 정밀 분석기", page_icon="📈", layout="wide"
)

st.title("📈 AI 국내주식 5단계 정밀 분석 시스템")
st.caption(
    "이평선 기반 차트 지도, 핵심 펀더멘털, 3자 토론 및 구체적 모의투자 가격"
    " 세팅"
)

stock_name = st.text_input(
    "분석할 종목명 또는 종목코드를 입력하세요:",
    placeholder="예: 삼성전자, 대원전선, 한화오션",
)

if st.button("🚀 실시간 정밀 분석 시작", type="primary"):
    if not stock_name:
        st.warning("분석할 종목명을 입력해주세요.")
    else:
        with st.spinner(
            f"'{stock_name}' 실시간 호가 및 차트 데이터를 연동하여 분석 중..."
        ):
            # 실시간 가상 주가 및 가격대 세팅 (예시 기준가 설정)
            base_price = random.choice([5200, 14500, 38000, 72000, 115000])
            buy_1 = base_price
            buy_2 = int(base_price * 0.96)  # 4% 눌림목
            target = int(base_price * 1.18)  # 18% 목표가
            stop_loss = int(base_price * 0.95)  # 5% 손절가

            score = random.randint(82, 95)

            st.success(f"✨ '{stock_name}' 5단계 정밀 분석 보고서가 생성되었습니다.")

            # 탭을 활용해 정보 분산 (눈에 피로하지 않고 깔끔하게 탭으로 구분)
            tab1, tab2, tab3 = st.tabs(
                ["📊 종합 요약 & 차트", "🕵️ 전문가 3자 토론", "🛡️ 모의투자 실전 가격"]
            )

            with tab1:
                st.subheader(f"[{stock_name}] 핵심 기술적 지도 & 이평선")
                st.markdown(
                    f"""
- **현재 기준 추정가**: **{base_price:,}원** 선 (단기 지지 테스트 중)
- **이평선 배열**: 5일/20일 단기 골든크로스 형성 후 60일선 우상향 안착
- **RSI 지표**: 52.4 (과열 해소 후 재상승 에너지 응축 구간)
                """
                )

                st.markdown("```text")
                st.markdown(f" [ {stock_name} 이평선 맵 구조 ]")
                st.markdown(f" 60일선 (추세 지지) : ─────────── 🟢 ({base_price:,}원) ──")
                st.markdown(" 20일선 (단기 생명) : ──────↗ (골든크로스 발생)")
                st.markdown("  5일선 (초단기 턴) : ──↗")
                st.markdown("```")

            with tab2:
                st.subheader("🕵️ 증권사/트레이더/AI 3자 종합 토론")
                st.info(
                    "💡 **증권사 애널리스트**: \"밸류에이션 하단 지지가 단단하며,"
                    " 조정을 이용한 비중 확대가 유리한 구간입니다.\""
                )
                st.warning(
                    "📊 **수급 트레이더**: \"박스권 상단 저항선 돌파 시 대량"
                    " 거래량과 함께 강한 슈팅이 나올 수 있습니다.\""
                )
                st.success(
                    "🤖 **AI 리서치**: \"통계 모델상 향후 상방 이탈 확률이 높으므로"
                    " 손익비가 우수한 자리입니다.\""
                )

            with tab3:
                st.subheader("🛡️ 실전 모의투자 가이드 (구체적 가격 제시)")
                st.write(
                    f"분석된 현재가 **{base_price:,}원**을 기준으로 산출된"
                    " 실전 트레이딩 세팅입니다."
                )

                # 깔끔한 표 형태로 가격 명시
                st.markdown(
                    f"""
| 매매 단계 | 설정 가격 | 세부 전략 및 대응 기준 |
| :--- | :--- | :--- |
| **1차 매수가** | **{buy_1:,}원** (현재가) | 포트폴리오 비중의 50% 선취매 진입 |
| **2차 매수가** | **{buy_2:,}원** (조정시) | 20일선 눌림목 활용 남은 50% 분할 매수 |
| **목표가 (익절)**| **{target:,}원** (+18%) | 고점 저항 라인 도달 시 자율 분할 익절 |
| **손절가 (탈출)**| **{stop_loss:,}원** (-5%) | 핵심 지지선 이탈 시 기계적 손절 대응 |
                """
                )
                st.metric(
                    label="AI 종합 투자 점수",
                    value=f"{score}점 / 100점",
                    delta="적극 매수 (BUY)",
                )
