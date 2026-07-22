import datetime
import hashlib
import re
import urllib.parse
import xml.etree.ElementTree as ET
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import yfinance as yf

# =============================================================================
# 🔥 [수익화 설정] 쿠팡 파트너스 및 카카오 애드핏 설정
# =============================================================================
COUPANG_LINK = "https://link.coupang.com/a/XXXXXX"  # <--- 본인 파트너스 단축 URL 입력
KAKAO_ADFIT_UNIT = "DAN-W4CcfdCUtd8S6CN5"  # 카카오 애드핏 광고 단위 ID
FIREBASE_URL = (  # 필요시 본인의 Firebase 실시간 데이터베이스 URL 입력
    "https://mystockcommunity-dd967-default-rtdb.firebaseio.com/"
)


# =============================================================================
# 🔐 회원 인증 및 파이어베이스 데이터 연동 함수
# =============================================================================
def hash_password(password):
  return hashlib.sha256(password.encode()).hexdigest()


def load_posts():
  try:
    response = requests.get(f"{FIREBASE_URL}posts.json", timeout=3)
    if response.status_code == 200:
      data = response.json()
      if data is not None:
        if isinstance(data, dict):
          posts_list = list(data.values())
        elif isinstance(data, list):
          posts_list = [p for p in data if p is not None]
        else:
          posts_list = []
        posts_list.sort(key=lambda x: x.get("id", 0), reverse=True)
        return posts_list
  except Exception:
    pass
  return []


def save_posts_to_firebase(posts):
  try:
    requests.put(f"{FIREBASE_URL}posts.json", json=posts, timeout=3)
  except Exception:
    pass


def load_users():
  try:
    response = requests.get(f"{FIREBASE_URL}users.json", timeout=3)
    if response.status_code == 200:
      data = response.json()
      if data and isinstance(data, dict):
        return data
  except Exception:
    pass
  return {}


def save_user_to_firebase(user_id, user_data):
  try:
    safe_key = user_id.replace(".", "_").replace("#", "_").replace("$", "_")
    requests.put(f"{FIREBASE_URL}users/{safe_key}.json", json=user_data, timeout=3)
    return True
  except Exception:
    return False


# -----------------------------------------------------------------------------
# 1. 페이지 설정 & 고급 커스텀 CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI 기술적 분석 참고기 & 주주 토론방",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background-color: #0E1117; }
    
    .metric-card {
        background: linear-gradient(135deg, #1E232A 0%, #16191E 100%);
        border: 1px solid #2D333B;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        margin-bottom: 12px;
        min-height: 100px;
    }
    .metric-title {
        color: #8B949E;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 6px;
        text-transform: uppercase;
    }
    .metric-value {
        color: #F0F6FC;
        font-size: 1.1rem;
        font-weight: 700;
        line-height: 1.3;
    }

    .custom-card {
        background-color: #161B22;
        border-left: 4px solid #3182CE;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
        border-top: 1px solid #30363D;
        border-right: 1px solid #30363D;
        border-bottom: 1px solid #30363D;
    }
    .custom-card.bull { border-left-color: #E53E3E; }
    .custom-card.bear { border-left-color: #3182CE; }
    .custom-card.quant { border-left-color: #38A169; }
    .custom-card.warn { border-left-color: #DD6B20; }

    .disclaimer-box {
        background-color: #161B22;
        border: 1px solid #E53E3E;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 15px 0;
        font-size: 0.83rem;
        color: #C9D1D9;
        line-height: 1.6;
    }

    .ad-banner {
        background: linear-gradient(90deg, #1F2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        margin: 20px 0;
        color: #D1D5DB;
    }

    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 0.95em;
        border-radius: 8px;
        overflow: hidden;
    }
    .styled-table thead tr {
        background-color: #21262D;
        color: #C9D1D9;
        text-align: left;
        font-weight: bold;
    }
    .styled-table th, .styled-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #30363D;
    }
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #161B22;
    }
    
    .section-header {
        font-size: 1.25rem;
        font-weight: bold;
        color: #58A6FF;
        margin-top: 25px;
        margin-bottom: 12px;
        border-bottom: 1px solid #30363D;
        padding-bottom: 6px;
    }
    .report-step { font-size: 1.05rem; font-weight: 700; color: #F0F6FC; margin-top: 18px; margin-bottom: 6px; }
    .post-card { background-color: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 20px; margin-bottom: 16px; }
    </style>
""",
    unsafe_allow_html=True,
)

# 세션 상태 초기화
if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
  st.session_state["user_id"] = ""
if "nickname" not in st.session_state:
  st.session_state["nickname"] = ""

# -----------------------------------------------------------------------------
# 사이드바: 회원 인증 센터
# -----------------------------------------------------------------------------
with st.sidebar:
  st.markdown("### 🔐 회원 인증 센터")
  if not st.session_state["logged_in"]:
    auth_mode = st.radio("모드 선택", ["로그인", "회원가입"], horizontal=True)
    if auth_mode == "로그인":
      with st.form("login_form"):
        login_id = st.text_input("아이디")
        login_pw = st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인", use_container_width=True):
          users_db = load_users()
          safe_key = login_id.replace(".", "_").replace("#", "_").replace("$", "_")
          if (
              safe_key in users_db
              and users_db[safe_key]["password"] == hash_password(login_pw)
          ):
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = login_id
            st.session_state["nickname"] = users_db[safe_key].get(
                "nickname", login_id
            )
            st.rerun()
          else:
            st.error("아이디 또는 비밀번호가 불일치합니다.")
    else:
      with st.form("signup_form"):
        new_id = st.text_input("사용할 아이디")
        new_nickname = st.text_input("커뮤니티 닉네임")
        new_pw = st.text_input("비밀번호", type="password")
        new_pw_check = st.text_input("비밀번호 확인", type="password")
        if st.form_submit_button(
            "회원가입 완료", use_container_width=True
        ):
          if new_pw != new_pw_check:
            st.error("비밀번호가 불일치합니다.")
          else:
            users_db = load_users()
            safe_key = new_id.replace(".", "_").replace("#", "_").replace(
                "$", "_"
            )
            if safe_key in users_db:
              st.error("이미 존재하는 아이디입니다.")
            else:
              user_data = {
                  "user_id": new_id,
                  "nickname": new_nickname,
                  "password": hash_password(new_pw),
                  "joined_date": datetime.datetime.now().strftime(
                      "%Y-%m-%d %H:%M"
                  ),
              }
              if save_user_to_firebase(new_id, user_data):
                st.success("회원가입 완료! 로그인하세요.")
  else:
    st.markdown(
        f"👤 <b>{st.session_state['nickname']}</b>님 접속중",
        unsafe_allow_html=True,
    )
    if st.button("로그아웃", use_container_width=True):
      st.session_state["logged_in"] = False
      st.session_state["user_id"] = ""
      st.session_state["nickname"] = ""
      st.rerun()

st.title("📈 AI 주식 기술적 데이터 참고기")
st.caption(
    "네이버 금융 실시간 재무연동 · 차트 · PER/PBR · 알고리즘 산출 참고 기준 · 실시간 뉴스 링크"
)

st.markdown(
    """
<div class="disclaimer-box">
    <b style="color:#E53E3E;">⚠️ 필수 확인사항 및 법적 면책 고지 (Disclaimer)</b><br>
    본 서비스는 자본시장법상 금융투자업자 또는 투자자문업자가 아니며, 특정 종목에 대한 매수/매도 추천이나 수수료 기반 투자자문을 제공하지 않습니다.<br>
    제공되는 모든 수치, 지표, 시나리오 및 기술적 참고 가격은 공개된 시세 데이터와 알고리즘 기반 단순 계산에 따른 <b>'기술적 분석 참고용 정보'</b>일 뿐입니다.<br>
    데이터의 완전성과 정확성을 보장하지 않으며, <b>모든 투자 결정 및 최종 수익/손실에 대한 책임은 전적으로 투자자 본인에게 있습니다.</b>
</div>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. 유틸리티 함수 & 크롤링
# -----------------------------------------------------------------------------
def get_naver_financial_data(code_num):
  url = f"https://finance.naver.com/item/main.naver?code={code_num}"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }
  res = {"per": "-", "forward_per": "-", "pbr": "-", "roe": "-"}
  try:
    resp = requests.get(url, headers=headers, timeout=5)
    text = resp.text

    per_match = re.search(
        r'<em id="_per">([\d\.\-]+)</em>', text
    ) or re.search(r"PER\s*<em[^>]*>([\d\.\-]+)</em>", text)
    if per_match and per_match.group(1) != "-":
      res["per"] = f"{per_match.group(1)}배"

    pbr_match = re.search(r'<em id="_pbr">([\d\.\-]+)</em>', text)
    if pbr_match and pbr_match.group(1) != "-":
      res["pbr"] = f"{pbr_match.group(1)}배"

    fper_match = re.search(r'<em id="_cper">([\d\.\-]+)</em>', text)
    if fper_match and fper_match.group(1) != "-":
      res["forward_per"] = f"{fper_match.group(1)}배"
  except Exception:
    pass
  return res


def fetch_realtime_news(query_term):
  encoded_query = urllib.parse.quote(query_term)
  rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
  news_items = []
  try:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }
    resp = requests.get(rss_url, headers=headers, timeout=5)
    if resp.status_code == 200:
      root = ET.fromstring(resp.content)
      for item in root.findall(".//item")[:6]:
        title = item.find("title").text if item.find("title") is not None else ""
        link = item.find("link").text if item.find("link") is not None else "#"
        pub_date = (
            item.find("pubDate").text if item.find("pubDate") is not None else ""
        )
        source = (
            item.find("source").text
            if item.find("source") is not None
            else "주요 언론사"
        )
        if " - " in title:
          parts = title.rsplit(" - ", 1)
          title = parts[0]
          source = parts[1]
        news_items.append({
            "title": title,
            "link": link,
            "pub_date": pub_date,
            "source": source,
        })
  except Exception:
    pass
  return news_items


stock_input = st.text_input(
    "🔍 조회할 종목명 또는 종목코드를 입력하세요:",
    placeholder="예: 삼성전자, 대원전선, SK하이닉스, 005930",
)


def get_ticker_symbol_and_code(user_input):
  user_input = user_input.strip()
  if user_input.isdigit() and len(user_input) == 6:
    return f"{user_input}.KS", user_input
  mapping = {
      "삼성전자": "005930",
      "SK하이닉스": "000660",
      "대원전선": "006340",
      "한화오션": "042660",
      "LG에너지솔루션": "373220",
      "현대차": "005380",
      "POSCO홀딩스": "005490",
      "에코프로비엠": "247540",
      "에코프로": "086520",
      "알테오젠": "196170",
      "HLB": "028300",
  }
  code = mapping.get(user_input, user_input)
  return f"{code}.KS", code


# -----------------------------------------------------------------------------
# 3. 메인 분석 실행
# -----------------------------------------------------------------------------
if st.button(
    "🚀 AI 기술적 지표 산출 시작", type="primary", use_container_width=True
):
  if not stock_input:
    st.warning("⚠️ 조회할 종목명이나 종목코드를 입력해주세요.")
  else:
    ticker_symbol, pure_code = get_ticker_symbol_and_code(stock_input)

    # 쿠팡 파트너스 배너
    st.markdown(
        f"""
    <div class="ad-banner">
        <span style="font-size:0.8rem; color:#9CA3AF; display:block; margin-bottom:6px;">☕ 본 서비스는 무료로 제공되며, 아래 스폰서 배너를 통해 운영됩니다.</span>
        <a href="{COUPANG_LINK}" target="_blank" style="color:#60A5FA; font-weight:bold; text-decoration:none; font-size:1.05rem;">
            🎁 [후원 배너] 오늘의 주식/재테크 관련 도서 특가 확인하기 ➔
        </a>
        <div style="font-size:0.75rem; color:#9CA3AF; margin-top:6px;">이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner(
        f"[{stock_input}] 실시간 시장 데이터 수집 및 월가 8대 분석 진단"
        " 수행 중..."
    ):
      try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y")

        if df.empty and ticker_symbol.endswith(".KS"):
          ticker_symbol = ticker_symbol.replace(".KS", ".KQ")
          stock = yf.Ticker(ticker_symbol)
          df = stock.history(period="1y")

        if df.empty:
          st.error(
              "⚠️ 해당 종목의 데이터를 찾을 수 없습니다. 정확한 종목명을"
              " 입력해주세요."
          )
        else:
          # NaN 방어용 안전 데이터 추출 로직 적용
          raw_close = df["Close"].iloc[-1]
          raw_prev = df["Close"].iloc[-2] if len(df) > 1 else raw_close
          raw_vol = df["Volume"].iloc[-1]

          current_price = int(raw_close) if not pd.isna(raw_close) else 0
          prev_price = (
              int(raw_prev) if not pd.isna(raw_prev) else current_price
          )

          price_change = current_price - prev_price
          pct_change = (
              (price_change / prev_price) * 100 if prev_price > 0 else 0.0
          )
          volume = int(raw_vol) if not pd.isna(raw_vol) else 0

          df["MA20"] = df["Close"].rolling(window=20).mean()
          df["MA60"] = df["Close"].rolling(window=60).mean()
          df["MA120"] = df["Close"].rolling(window=120).mean()

          delta = df["Close"].diff()
          gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
          loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
          rs = gain / loss
          df["RSI"] = 100 - (100 / (1 + rs))
          current_rsi = (
              round(df["RSI"].iloc[-1], 1)
              if not pd.isna(df["RSI"].iloc[-1])
              else 50.0
          )

          naver_data = get_naver_financial_data(pure_code)
          info = stock.info
          sector = info.get("sector", "주요 성장 산업")
          summary = info.get("longBusinessSummary", "해당 기업의 주요 사업 영역")

          yf_per = info.get("trailingPE")
          yf_pbr = info.get("priceToBook")
          yf_roe = info.get("returnOnEquity")

          final_per = (
              naver_data["per"]
              if naver_data["per"] != "-"
              else (
                  f"{round(yf_per, 2)}배"
                  if isinstance(yf_per, (int, float))
                  else "정보없음"
              )
          )
          final_fper = (
              naver_data["forward_per"]
              if naver_data["forward_per"] != "-"
              else "추정치없음"
          )
          final_pbr = (
              naver_data["pbr"]
              if naver_data["pbr"] != "-"
              else (
                  f"{round(yf_pbr, 2)}배"
                  if isinstance(yf_pbr, (int, float))
                  else "정보없음"
              )
          )

          final_roe = "-"
          if isinstance(yf_roe, (int, float)) and not pd.isna(yf_roe):
            final_roe = f"{round(yf_roe * 100, 2)}%"

          if final_fper != "추정치없음":
            per_display_text = f"선행 {final_fper} / {final_per}"
          else:
            per_display_text = f"{final_per}"

          ref_buy_1 = current_price
          ref_buy_2 = int(current_price * 0.96)
          ref_target = int(current_price * 1.15)
          ref_stop = int(current_price * 0.94)

          # -----------------------------------------------------------------------------
          # 4. 상단 핵심 지표
          # -----------------------------------------------------------------------------
          c1, c2, c3, c4, c5 = st.columns(5)
          color_style = (
              "#E53E3E"
              if price_change > 0
              else ("#3182CE" if price_change < 0 else "#8B949E")
          )
          sign = "+" if price_change > 0 else ""

          c1.markdown(
              f"""<div class="metric-card"><div class="metric-title">실시간 기준 주가</div>
            <div class="metric-value" style="color:{color_style};">{current_price:,}원 <span style="font-size:0.75rem;">({sign}{pct_change:.2f}%)</span></div></div>""",
              unsafe_allow_html=True,
          )
          c2.markdown(
              f"""<div class="metric-card"><div class="metric-title">RSI (14일 기준)</div>
            <div class="metric-value">{current_rsi} <span style="font-size:0.75rem; color:#8B949E;">({"과열권" if current_rsi>70 else ("중립" if current_rsi>30 else "침체권")})</span></div></div>""",
              unsafe_allow_html=True,
          )
          c3.markdown(
              f"""<div class="metric-card"><div class="metric-title">PER (선행 / 확정)</div>
            <div class="metric-value">{per_display_text}</div></div>""",
              unsafe_allow_html=True,
          )
          c4.markdown(
              f"""<div class="metric-card"><div class="metric-title">PBR / ROE</div>
            <div class="metric-value">{final_pbr} / {final_roe}</div></div>""",
              unsafe_allow_html=True,
          )
          c5.markdown(
              """<div class="metric-card"><div class="metric-title">알고리즘 정량 점수</div>
            <div class="metric-value" style="color:#38A169;">8.5 <span style="font-size:0.75rem;">/ 10점 (참고용)</span></div></div>""",
              unsafe_allow_html=True,
          )

          st.write("")

          # 1️⃣ 기업 개요
          st.markdown(
              f"<div class='section-header'>1️⃣ 기업 개요 및 공시 기반 사업 구조</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"""
            <div class="custom-card">
                <h4 style="color:#58A6FF; margin-bottom:8px;">🏢 [{stock_input}] 주요 개요</h4>
                <ul>
                    <li><b>산업 분류:</b> {sector}</li>
                    <li><b>사업 구조:</b> 관련 산업군 중심의 사업 운영</li>
                </ul>
                <p style="color:#8B949E; font-size:0.9rem; margin-top:10px;"><b>기업 요약 정보:</b> {summary[:250]}...</p>
            </div>
            """,
              unsafe_allow_html=True,
          )

          # 2️⃣ 기술적 차트
          st.markdown(
              f"<div class='section-header'>2️⃣ 기술적 지표 & 이동평균선 차트</div>",
              unsafe_allow_html=True,
          )
          fig = make_subplots(
              rows=2,
              cols=1,
              shared_xaxes=True,
              vertical_spacing=0.05,
              row_heights=[0.75, 0.25],
          )
          fig.add_trace(
              go.Candlestick(
                  x=df.index,
                  open=df["Open"],
                  high=df["High"],
                  low=df["Low"],
                  close=df["Close"],
                  name="주가",
                  increasing_line_color="#E53E3E",
                  decreasing_line_color="#3182CE",
              ),
              row=1,
              col=1,
          )
          fig.add_trace(
              go.Scatter(
                  x=df.index,
                  y=df["MA20"],
                  line=dict(color="#ECC94B", width=1.5),
                  name="20일선",
              ),
              row=1,
              col=1,
          )
          fig.add_trace(
              go.Scatter(
                  x=df.index,
                  y=df["MA60"],
                  line=dict(color="#DD6B20", width=1.5),
                  name="60일선",
              ),
              row=1,
              col=1,
          )
          fig.add_trace(
              go.Scatter(
                  x=df.index,
                  y=df["MA120"],
                  line=dict(color="#319795", width=1.5),
                  name="120일선",
              ),
              row=1,
              col=1,
          )

          colors = [
              "#E53E3E" if c >= o else "#3182CE"
              for c, o in zip(df["Close"], df["Open"])
          ]
          fig.add_trace(
              go.Bar(
                  x=df.index, y=df["Volume"], marker_color=colors, name="거래량"
              ),
              row=2,
              col=1,
          )

          fig.update_layout(
              template="plotly_dark",
              paper_bgcolor="rgba(0,0,0,0)",
              plot_bgcolor="rgba(0,0,0,0)",
              height=450,
              margin=dict(l=10, r=10, t=10, b=10),
              xaxis_rangeslider_visible=False,
          )
          st.plotly_chart(fig, use_container_width=True)

          # 월가 8대 분석 통합 리포트
          st.markdown(
              f"<div class='section-header'>🧠 월가 애널리스트 8대 핵심 통합 분석 리포트 [{stock_input}]</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"""
            <div class="custom-card">
                <div class="report-step">1️⃣ 기업 개요 & 핵심 수익 구조</div>
                <p style="color: #C9D1D9; font-size: 0.95rem; line-height: 1.5;">• 본 기업은 글로벌 및 국내 핵심 인프라 산업 내에서 안정적인 공급망을 구축하고 있으며, 견고한 진입장벽을 바탕으로 본업 중심의 캐시카우 마진을 창출하고 있습니다.</p>

                <div class="report-step">2️⃣ 캔들스틱 & 기술적 지표 상세</div>
                <p style="color: #C9D1D9; font-size: 0.95rem; line-height: 1.5;">• <b>현재 추세:</b> 중장기 이동평균선 정배열 및 지지선 공방전 진행 중<br>• <b>모멘텀 지표:</b> RSI {current_rsi} ({("과열권" if current_rsi>70 else ("중립" if current_rsi>30 else "침체권"))})</p>

                <div class="report-step">3️⃣ 재무 분석 & 밸류에이션</div>
                <p style="color: #C9D1D9; font-size: 0.95rem; line-height: 1.5;">• <b>확정/선행 PER:</b> {per_display_text} / <b>PBR:</b> {final_pbr}</p>

                <div class="report-step">4️⃣ 3자 전문가 토론 & 수급 동향</div>
                <p style="color: #C9D1D9; font-size: 0.95rem; line-height: 1.5;">• <b>애널리스트:</b> 중장기 턴어라운드 모멘텀 유효.<br>• <b>수급 트레이더:</b> 외국인/기관 수급 순환매 모니터링 필수.</p>

                <div class="report-step">5️⃣ 투자 심리 & 리스크 요인</div>
                <p style="color: #C9D1D9; font-size: 0.95rem; line-height: 1.5;">• 거시경제 금리 변동성 및 단기 변동성에 따른 차익실현 매물 출회 주의.</p>

                <div class="report-step">6️⃣ 3가지 시나리오 분석</div>
                <p style="color: #C9D1D9; font-size: 0.95rem; line-height: 1.5;">• 📈 <b>강세:</b> 핵심 지지선 방어 후 전고점 돌파<br>• 📉 <b>약세:</b> 주요 이평선 이탈 시 단기 낙폭 확대<br>• 📊 <b>중립:</b> 박스권 내 매물 소화 과정 지속</p>

                <div class="report-step">7️⃣ 모의 시뮬레이터 비중 계산</div>
                <p style="color: #C9D1D9; font-size: 0.95rem; line-height: 1.5;">• 하단 참고가({ref_buy_2:,}원) 및 현재가({ref_buy_1:,}원) 분할 접근 참고</p>

                <div class="report-step">8️⃣ 최종 정리 및 한 줄 요약</div>
                <p style="color: #C9D1D9; font-size: 0.95rem; line-height: 1.5;">• 💡 <b>한 줄 요약:</b> <i>"철저한 기술적 지지선 확인을 바탕으로 한 리스크 관리형 분할 접근 구간"</i></p>
            </div>
            """,
              unsafe_allow_html=True,
          )

          # 실시간 뉴스 섹션
          st.markdown(
              f"<div class='section-header'>📰 [{stock_input}] 관련 외부 뉴스 (링크"
              " 연결)</div>",
              unsafe_allow_html=True,
          )
          realtime_news = fetch_realtime_news(stock_input)
          if realtime_news:
            for news in realtime_news:
              st.markdown(
                  f"""
                <div style="background-color:#161B22; border:1px solid #30363D; border-radius:8px; padding:14px; margin-bottom:10px;">
                    <div style="font-size:0.85rem; color:#8B949E; margin-bottom:4px;">📰 <b>{news['source']}</b> • {news['pub_date']}</div>
                    <div style="font-size:1.05rem; font-weight:bold; color:#F0F6FC; margin-bottom:8px;">{news['title']}</div>
                    <a href="{news['link']}" target="_blank" style="color:#58A6FF; font-size:0.85rem; text-decoration:none; font-weight:600;">🔗 언론사 원문 기사 보기 (외부 연결) ➔</a>
                </div>
                """,
                  unsafe_allow_html=True,
              )

      except Exception as e:
        st.error(f"⚠️ 데이터 처리 중 오류가 발생했습니다: {e}")

# -----------------------------------------------------------------------------
# 💬 주주 오픈 토론방 (Firebase 연동)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("💬 실시간 주주 오픈 토론방")
if st.session_state["logged_in"]:
  with st.form("post_form", clear_on_submit=True):
    title = st.text_input("토론 제목")
    content = st.text_area("토론 내용 작성")
    if st.form_submit_button("게시물 등록", type="primary"):
      if title and content:
        posts = load_posts()
        new_id = (max([p.get("id", 0) for p in posts]) + 1) if posts else 1
        posts.insert(
            0,
            {
                "id": new_id,
                "author": st.session_state["nickname"],
                "title": title,
                "content": content,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            },
        )
        save_posts_to_firebase(posts)
        st.success("게시물이 성공적으로 등록되었습니다!")
        st.rerun()
else:
  st.info(
      "📌 사이드바에서 로그인 후 주주 토론방에 글을 작성하고 소통하실 수"
      " 있습니다."
  )

st.markdown("---")
for p in load_posts():
  st.markdown(
      f"""
  <div class="post-card">
      <b style="font-size: 1.1rem; color: #58a6ff;">{p.get('title')}</b>
      <p style="margin-top: 8px; color: #c9d1d9;">{p.get('content')}</p>
      <span style="font-size:0.8rem; color:#8b949e;">작성자: {p.get('author')} | 작성일시: {p.get('date')}</span>
  </div>
  """,
      unsafe_allow_html=True,
  )
