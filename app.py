import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import streamlit.components.v1 as components

# =============================================================================
# 1. 페이지 기본 설정 및 디자인 (CSS)
# =============================================================================
st.set_page_config(
    page_title="AI 주식 분석 & 토론 커뮤니티",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    /* 메인 배경 및 폰트 설정 */
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* 애니메이션 쿠팡 배너 스타일 */
    .coupang-banner {
        position: relative;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin: 15px 0;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    .coupang-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(
            45deg,
            transparent,
            rgba(255, 255, 255, 0.1),
            transparent
        );
        transform: rotate(45deg);
        animation: loading-shine 3s infinite;
    }
    @keyframes loading-shine {
        0% { transform: translateX(-100%) rotate(45deg); }
        100% { transform: translateX(100%) rotate(45deg); }
    }
    .banner-title {
        color: #60a5fa;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 6px;
    }
    .banner-desc {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    .banner-btn {
        display: inline-block;
        background-color: #2563eb;
        color: white !important;
        padding: 8px 18px;
        border-radius: 20px;
        text-decoration: none;
        font-weight: bold;
        font-size: 0.88rem;
        transition: all 0.2s ease;
    }
    .banner-btn:hover {
        background-color: #1d4ed8;
        transform: scale(1.05);
    }
    
    /* 카드 스타일 */
    .metric-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. 파트너스 링크 및 데이터 캐싱
# =============================================================================
# 🔥 본인의 쿠팡 파트너스 단축 URL을 입력하세요.
COUPANG_LINK = "https://link.coupang.com/a/XXXXXX"

@st.cache_data(ttl=3600)  # 1시간 데이터 캐싱 (속도 극대화)
def fetch_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y")
        info = stock.info
        return df, info
    except Exception as e:
        return None, None

def render_coupang_banner(title_text, desc_text, btn_text):
    st.markdown(f"""
    <div class="coupang-banner">
        <div class="banner-title">⚡ {title_text}</div>
        <div class="banner-desc">{desc_text}</div>
        <a href="{COUPANG_LINK}" target="_blank" class="banner-btn">{btn_text} ➔</a>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 3. 메인 화면 구성
# =============================================================================
st.title("📈 AI 주식 분석 & 종목 토론 커뮤니티")
st.caption("실시간 주가 지표 분석부터 유저 간 자유로운 종목 토론까지 한눈에 확인해보세요.")

# 상단 쿠팡 배너
render_coupang_banner(
    "오늘의 추천 주식/재테크 베스트셀러",
    "투자 고수들의 실전 매매 전략과 지표 해석법을 지금 확인해보세요.",
    "추천 도서 보러가기"
)

# 검색창
col1, col2 = st.columns([3, 1])
with col1:
    search_input = st.text_input("종목코드 또는 티커를 입력하세요 (예: 005930.KS, AAPL, TSLA)", value="005930.KS")
with col2:
    st.write("")
    st.write("")
    search_btn = st.button("🔍 종목 분석하기", use_container_width=True)

# 종목 검색 실행
if search_input:
    df, info = fetch_stock_data(search_input)
    
    if df is not None and not df.empty:
        stock_name = info.get('shortName', search_input) if info else search_input
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        price_diff = current_price - prev_price
        diff_pct = (price_diff / prev_price) * 100
        
        st.subheader(f"📊 {stock_name} ({search_input}) 분석 리포트")
        
        # 지표 요약
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("현재가", f"{current_price:,.0f}원" if "KS" in search_input else f"${current_price:,.2f}", f"{diff_pct:+.2f}%")
        m2.metric("고가(52주)", f"{df['High'].max():,.0f}" if "KS" in search_input else f"${df['High'].max():,.2f}")
        m3.metric("저가(52주)", f"{df['Low'].min():,.0f}" if "KS" in search_input else f"${df['Low'].min():,.2f}")
        m4.metric("거래량", f"{df['Volume'].iloc[-1]:,}")
        
        # 차트 출력
        st.line_chart(df['Close'], use_container_width=True)
        
        st.divider()
        
        # 중간 배너
        render_coupang_banner(
            f"💡 {stock_name} 투자 관련 초보 탈출 가이드",
            "초보 투자자를 위한 기술적 분석 및 리스크 관리 노하우 모음",
            "쿠팡에서 관련 도서 검색"
        )
        
        # =====================================================================
        # 🔥 [핵심] 2단계: 실시간 종목 토론 & 댓글 시스템 (Disqus 연동)
        # =====================================================================
        st.subheader(f"💬 [{stock_name}] 자유 종목 토론방")
        st.caption("이 종목에 대한 매수/매도 의견이나 전망을 자유롭게 나누어보세요!")
        
        # Disqus 댓글창 스크립트 (종목별 개별 쓰레드 생성)
        clean_symbol = search_input.replace('.', '_')
        disqus_html = f"""
        <div id="disqus_thread"></div>
        <script>
            var disqus_config = function () {{
                this.page.url = "https://my-stock-app.streamlit.app/?symbol={clean_symbol}";
                this.page.identifier = "stock_{clean_symbol}";
            }};
            (function() {{
                var d = document, s = d.createElement('script');
                s.src = 'https://stock-community.disqus.com/embed.js';
                s.setAttribute('data-timestamp', +new Date());
                (d.head || d.body).appendChild(s);
            }})();
        </script>
        <noscript>댓글을 보려면 자바스크립트를 활성화하세요.</noscript>
        """
        
        # 댓글창 출력
        components.html(disqus_html, height=500, scrolling=True)
        
    else:
        st.error("올바른 종목 코드를 입력해주세요. (한국 주식은 코드 뒤에 .KS 또는 .KQ 첨부: 예 - 005930.KS)")

# =============================================================================
# 4. 하단 가이드 (SEO & 정보성 글 보완)
# =============================================================================
st.divider()
with st.expander("📚 [초보 가이드] 주식 지표 및 커뮤니티 이용 안내"):
    st.markdown("""
    * **RSI (상대강도지수):** 70 이상은 과매수(매도 검토), 30 이하점 과매수(매수 검토) 구간입니다.
    * **PER (주가수익비율):** 기업의 이익 대비 주가 수준을 나타내며, 동종 업계 대비 낮을수록 저평가 상태입니다.
    * **클린 커뮤니티 수칙:** 타인에 대한 비방이나 근거 없는 리딩방 홍보는 제재 대상이 될 수 있습니다.
    """)
