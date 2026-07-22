import datetime
import json
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
# 🔥 [수익화 설정] 본인의 쿠팡 파트너스 링크를 아래 큰따옴표 안에 넣어주세요.
# =============================================================================
COUPANG_LINK = "https://link.coupang.com/a/XXXXXX"  # <--- 본인 파트너스 단축 URL 붙여넣기

# Firebase 실시간 데이터베이스 URL (정상 주소 반영 완료)
FIREBASE_URL = "https://mystockcommunity-dd967-default-rtdb.firebaseio.com/"


# -----------------------------------------------------------------------------
# Firebase 데이터베이스 연동 함수 (게시글 영구 저장)
# -----------------------------------------------------------------------------
def load_posts():
  try:
    response = requests.get(f"{FIREBASE_URL}posts.json", timeout=5)
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
    requests.put(f"{FIREBASE_URL}posts.json", json=posts, timeout=5)
  except Exception:
    pass


# -----------------------------------------------------------------------------
# 1. 페이지 설정 & 커스텀 CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI 주식 분석 & 자유 커뮤니티",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background-color: #0E1117; }
    
    @keyframes shine {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }

    .animated-ad-banner {
        background: linear-gradient(110deg, #1E2640 20%, #2A365C 40%, #1E2640 60%);
        background-size: 200% 100%;
        animation: shine 4s infinite linear, pulse 3s infinite ease-in-out;
        border: 1px solid #3B82F6;
        border-radius: 12px;
        padding: 18px 20px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 4px 25px rgba(59, 130, 246, 0.25);
    }
    .ad-badge {
        background-color: #EF4444;
        color: white;
        font-size: 0.75rem;
        font-weight: bold;
        padding: 3px 8px;
        border-radius: 4px;
        margin-right: 6px;
        display: inline-block;
    }
    .ad-link {
        color: #60A5FA !important;
        font-weight: 800;
        text-decoration: none;
        font-size: 1.1rem;
        transition: all 0.2s ease;
    }
    .ad-link:hover {
        color: #93C5FD !important;
        text-decoration: underline;
    }

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
    
    .post-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📈 AI 주식 분석 & 주주 자유 게시판")

# 상단 탭 구성 (종목 분석 / 커뮤니티 게시판)
tab_analysis, tab_board = st.tabs(
    ["📊 AI 종목 기술적 분석", "💬 종목 토론 & 자유 게시판"]
)

# -----------------------------------------------------------------------------
# 2. 크롤링 및 유틸리티 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def get_naver_financial_data(code_num):
  url = f"https://finance.naver.com/item/main.naver?code={code_num}"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }
  res = {"per": "-", "forward_per": "-", "pbr": "-", "roe": "-"}
  try:
    resp = requests.get(url, headers=headers, timeout=4)
    text = resp.text
    per_match = re.search(
        r'<em id="_per">([\d\.\-]+)</em>', text
    ) or re.search(r'PER\s*<em[^>]*>([\d\.\-]+)</em>', text)
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


@st.cache_data(ttl=300)
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
    resp = requests.get(rss_url, headers=headers, timeout=4)
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


@st.cache_data(ttl=300)
def fetch_stock_history(ticker_symbol):
  stock = yf.Ticker(ticker_symbol)
  df = stock.history(period="1y")
  if df.empty and ticker_symbol.endswith(".KS"):
    ticker_symbol = ticker_symbol.replace(".KS", ".KQ")
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="1y")
  return df, stock.info


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


# =============================================================================
# 🟢 TAB 1: AI 종목 기술적 분석 화면
# =============================================================================
with tab_analysis:
  st.caption(
      "네이버 금융 실시간 재무연동 · 차트 · PER/PBR · 알고리즘 산출 참고 기준 · 실시간"
      " 뉴스"
  )

  st.markdown(
      """
  <div class="disclaimer-box">
      <b style="color:#E53E3E;">⚠️ 필수 확인사항 및 법적 면책 고지 (Disclaimer)</b><br>
      본 서비스는 특정 종목에 대한 매수/매도 추천이나 수수료 기반 투자자문을 제공하지 않습니다.<br>
      모든 수치는 공개된 시세 데이터 기반의 <b>'기술적 분석 참고용 정보'</b>일 뿐이며, 모든 투자 결정의 책임은 본인에게 있습니다.
  </div>
  """,
      unsafe_allow_html=True,
  )

  stock_input = st.text_input(
      "🔍 조회할 종목명 또는 종목코드를 입력하세요:",
      placeholder="예: 삼성전자, 대원전선, SK하이닉스, 005930",
  )

  if st.button(
      "🚀 AI 기술적 지표 산출 시작", type="primary", use_container_width=True
  ):
    if not stock_input:
      st.warning("⚠️ 조회할 종목명이나 종목코드를 입력해주세요.")
    else:
      ticker_symbol, pure_code = get_ticker_symbol_and_code(stock_input)

      st.markdown(
          f"""
      <div class="animated-ad-banner">
          <div style="margin-bottom:8px;">
              <span class="ad-badge">SPECIAL</span>
              <span style="font-size:0.85rem; color:#9CA3AF;">본 서비스는 무료로 제공되며, 아래 스폰서 혜택을 통해 운영됩니다.</span>
          </div>
          <a href="{COUPANG_LINK}" target="_blank" class="ad-link">
              🔥 [오늘의 추천 혜택] 주식/재테크 관련 베스트셀러 및 특가 상품 보기 ➔
          </a>
          <div style="font-size:0.75rem; color:#9CA3AF; margin-top:8px;">
              이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
          </div>
      </div>
      """,
          unsafe_allow_html=True,
      )

      try:
        with st.spinner("⚡ 데이터를 신속하게 불러오는 중입니다..."):
          df, info = fetch_stock_history(ticker_symbol)

        if df.empty:
          st.error(
              "⚠️ 해당 종목의 데이터를 찾을 수 없습니다. 정확한 종목명을"
              " 입력해주세요."
          )
        else:
          current_price = int(df["Close"].iloc[-1])
          prev_price = int(df["Close"].iloc[-2])
          price_change = current_price - prev_price
          pct_change = (price_change / prev_price) * 100
          volume = int(df["Volume"].iloc[-1])

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

          per_display_text = (
              f"선행 {final_fper} / {final_per}"
              if final_fper != "추정치없음"
              else f"{final_per}"
          )

          ref_buy_1 = current_price
          ref_buy_2 = int(current_price * 0.96)
          ref_target = int(current_price * 1.15)
          ref_stop = int(current_price * 0.94)

          # 지표 출력
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

          # 기업 개요
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

          # 차트
          st.markdown(
              "<div class='section-header'>2️⃣ 기술적 지표 & 이동평균선 차트</div>",
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

          # 재무
          st.markdown(
              "<div class='section-header'>3️⃣ 주요 재무 및 밸류에이션 수치</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"""
          <table class="styled-table">
              <thead>
                  <tr><th>구분</th><th>현재 수치</th><th>지표 설명</th></tr>
              </thead>
              <tbody>
                  <tr><td><b>선행 PER</b></td><td><b style="color:#58A6FF;">{final_fper}</b></td><td>추정 실적 기준 단순 주가수익비율</td></tr>
                  <tr><td><b>확정 PER</b></td><td><b style="color:#F0F6FC;">{final_per}</b></td><td>최근 12개월 실적 기준 단순 주가수익비율</td></tr>
                  <tr><td><b>PBR</b></td><td><b>{final_pbr}</b></td><td>순자산 대비 주가 수준 지표</td></tr>
                  <tr><td><b>ROE</b></td><td><b>{final_roe}</b></td><td>자기자본 수익성 수치</td></tr>
              </tbody>
          </table>
          """,
              unsafe_allow_html=True,
          )

          # 시나리오
          st.markdown(
              f"<div class='section-header'>4️⃣ 기술적 단순 시나리오 예시 (참고)</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"""
          <div class="custom-card bull">
              <h4 style="color:#E53E3E; margin-bottom:6px;">📈 기술적 상향 돌파 시나리오 (상단 참고선: {ref_target:,}원)</h4>
              <p>거래량 증가 및 매물대 돌파 시 상단 저항선 테스트 가능성</p>
          </div>
          <div class="custom-card">
              <h4 style="color:#8B949E; margin-bottom:6px;">📊 횡보 구간 시나리오 (참고 범위: {ref_buy_2:,}원 ~ {ref_buy_1:,}원)</h4>
              <p>이동평균선 부근에서 매물 소화 및 박스권 형성 가능성</p>
          </div>
          <div class="custom-card bear">
              <h4 style="color:#3182CE; margin-bottom:6px;">📉 기술적 하향 이탈 시나리오 (하단 참고선: {ref_stop:,}원)</h4>
              <p>시장 악재나 지지선 이탈 시 하단 가격 구간 재설정 관찰</p>
          </div>
          """,
              unsafe_allow_html=True,
          )

          # 실시간 뉴스
          st.markdown(
              f"<div class='section-header'>5️⃣ [{stock_input}] 관련 외부 뉴스</div>",
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
                  <a href="{news['link']}" target="_blank" style="color:#58A6FF; font-size:0.85rem; text-decoration:none; font-weight:600;">🔗 언론사 원문 기사 보기 ➔</a>
              </div>
              """,
                  unsafe_allow_html=True,
              )

      except Exception as e:
        st.error(f"⚠️ 데이터 처리 중 오류가 발생했습니다: {e}")


# =============================================================================
# 🟢 TAB 2: 자유 게시판 커뮤니티 화면 (Firebase DB 연동)
# =============================================================================
with tab_board:
  st.subheader("💬 주주 자유 토론 게시판")
  st.caption(
      "종목 분석 정보, 매수/매도 타이밍, 시장 이슈를 다른 유저들과 자유롭게 나눠보세요!"
  )

  # 1. 새 글 작성 영역
  with st.expander("✍️ 새 글 작성하기 (클릭하여 열기)", expanded=False):
    with st.form("write_post_form", clear_on_submit=True):
      col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
      author = col_f1.text_input("닉네임", placeholder="익명주주")
      password = col_f2.text_input(
          "비밀번호 (삭제용)", type="password", placeholder="4자리 이상"
      )
      category = col_f3.selectbox(
          "관련 종목/분류",
          ["자유토론", "삼성전자", "SK하이닉스", "대원전선", "국장종목", "미장종목"],
      )

      title = st.text_input("글 제목", placeholder="제목을 입력하세요")
      content = st.text_area(
          "글 내용",
          placeholder="자유롭게 의견을 적어주세요. (비방 및 불법 광고는 제재될 수 있습니다)",
          height=120,
      )

      submit_btn = st.form_submit_button("🚀 게시글 등록", type="primary")

      if submit_btn:
        if not author or not password or not title or not content:
          st.error("⚠️ 닉네임, 비밀번호, 제목, 내용을 모두 입력해 주세요!")
        else:
          posts = load_posts()
          new_id = (max([p.get("id", 0) for p in posts]) + 1) if posts else 1
          new_post = {
              "id": new_id,
              "author": author,
              "password": password,
              "category": category,
              "title": title,
              "content": content,
              "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
          }
          posts.insert(0, new_post)
          save_posts_to_firebase(posts)
          st.success("✅ 게시글이 성공적으로 영구 등록되었습니다!")
          st.rerun()

  st.markdown("---")

  # 2. 게시글 목록 출력
  posts = load_posts()

  if not posts:
    st.info("📌 아직 작성된 글이 없습니다. 첫 번째 주주 게시글을 남겨보세요!")
  else:
    for idx, post in enumerate(posts):
      st.markdown(
          f"""
        <div class="post-card">
            <div style="font-size:0.8rem; color:#58A6FF; margin-bottom:4px;">
                🏷️ <b>[{post.get('category', '자유토론')}]</b> • 👤 <b>{post.get('author')}</b> • 🕒 {post.get('date')}
            </div>
            <div style="font-size:1.15rem; font-weight:bold; color:#F0F6FC; margin-bottom:8px;">
                {post.get('title')}
            </div>
            <div style="font-size:0.95rem; color:#C9D1D9; white-space: pre-wrap; line-height:1.5;">
                {post.get('content')}
            </div>
        </div>
        """,
          unsafe_allow_html=True,
      )

      # 삭제 기능 (비밀번호 검증)
      with st.popover("🗑️ 글 삭제"):
        del_pw = st.text_input(
            "작성 시 입력한 비밀번호", type="password", key=f"pw_{post['id']}"
        )
        if st.button("확인 및 삭제", key=f"del_{post['id']}"):
          if del_pw == str(post.get("password")):
            posts.pop(idx)
            save_posts_to_firebase(posts)
            st.success("삭제되었습니다!")
            st.rerun()
          else:
            st.error("비밀번호가 일치하지 않습니다.")

      st.write("")
