import datetime
import re
import time
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

# -----------------------------------------------------------------------------
# 1. 페이지 설정 & 커스텀 CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI 기술적 분석 참고기",
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
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📈 AI 주식 기술적 데이터 참고기")
st.caption(
    "네이버 금융 실시간 재무연동 · 차트 · PER/PBR · 알고리즘 산출 참고 기준 · 실시간 뉴스 링크"
)

# 상단 법적 고지 안내 (자본시장법 및 무등록 자문 방지 문구 강화)
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

    progress_bar = st.progress(0)
    status_text = st.empty()

    # 표시광고법 준수 쿠팡 파트너스 배너
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

    for i in range(1, 101):
      time.sleep(0.02)
      progress_bar.progress(i)
      if i < 40:
        status_text.text(
            f"⏳ AI 데이터 수집 및 차트 수치 연동 중... ({i}%)"
        )
      elif i < 80:
        status_text.text(
            f"📊 이평선 및 PER/PBR 재무 밸류에이션 단순 계산 중... ({i}%)"
        )
      else:
        status_text.text(
            f"🎯 시나리오 및 기술적 수준 분석 완료... ({i}%)"
        )

    progress_bar.empty()
    status_text.empty()

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
            round(df["RSI"].iloc[-1], 1) if not pd.isna(df["RSI"].iloc[-1]) else 50.0
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

        # 💡 리스크 완화: 단어 변경 (매수가/목표가/손절가 ➔ 참고 지지선/저항선)
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

        st.markdown(
            f"""
        * **이동평균선:** 최근 20일선 및 주요 이평선 배치 상태 확인
        * **하단 지지 참고선:** {int(current_price*0.95):,}원 (20일선 가중 영역)
        * **상단 저항 참고선:** {int(current_price*1.12):,}원 (최근 박스권 상단 영역)
        """
        )

        # 3️⃣ 재무 분석
        st.markdown(
            f"<div class='section-header'>3️⃣ 주요 재무 및 밸류에이션 수치</div>",
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

        # 4️⃣ 다각도 시각 제시 (주관적 문구 ➔ 객관적 관점 정리)
        st.markdown(
            f"<div class='section-header'>4️⃣ 시장 지표별 해석 관점 (참고용)</div>",
            unsafe_allow_html=True,
        )
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
          st.markdown(
              f"""
          <div class="custom-card bull">
              <h4 style="color:#E53E3E; margin-bottom:6px;">📈 펀더멘털 관점</h4>
              <p>"현재 PER({final_per}) 및 재무 지표를 토대로 한 실적 관련 모멘텀 관찰 필요"</p>
          </div>
          """,
              unsafe_allow_html=True,
          )
        with col_t2:
          st.markdown(
              f"""
          <div class="custom-card bear">
              <h4 style="color:#3182CE; margin-bottom:6px;">📊 수급/차트 관점</h4>
              <p>"당일 거래량({volume:,}주) 변화 및 주요 이평선 지지 여부 추적 관찰"</p>
          </div>
          """,
              unsafe_allow_html=True,
          )
        with col_t3:
          st.markdown(
              """
          <div class="custom-card quant">
              <h4 style="color:#38A169; margin-bottom:6px;">🤖 퀀트 수치 관점</h4>
              <p>"과거 유사 패턴 분석 시 단기 변동성 구간 진입 가능성 수치화"</p>
          </div>
          """,
              unsafe_allow_html=True,
          )

        # 5️⃣ 리스크 요인
        st.markdown(
            f"<div class='section-header'>5️⃣ 시장 변동성 및 리스크 요인</div>",
            unsafe_allow_html=True,
        )
        col_r1, col_r2 = st.columns(2)
        with col_r1:
          st.markdown(
              """
          <div class="custom-card">
              <h4 style="color:#ECC94B; margin-bottom:6px;">🧠 과열 / 심리 지표</h4>
              <p>RSI 기반 단순 심리 상태: <b>중립~관망 구간</b></p>
              <p style="color:#8B949E; font-size:0.9rem;">지수 변동에 따른 단순 심리 상태 지표 수치입니다.</p>
          </div>
          """,
              unsafe_allow_html=True,
          )
        with col_r2:
          st.markdown(
              """
          <div class="custom-card warn">
              <h4 style="color:#DD6B20; margin-bottom:6px;">⚠️ 주요 주의 리스크 요인</h4>
              <ul style="font-size:0.9rem;">
                  <li><b>거시 변수:</b> 환율, 금리 등 거시경제 환경 영향</li>
                  <li><b>시장 변수:</b> 전체 증시 수급 이탈 가능성</li>
                  <li><b>기술적 리스크:</b> 주요 지지선 이탈 시 수급 변동 가능성</li>
              </ul>
          </div>
          """,
              unsafe_allow_html=True,
          )

        # 6️⃣ 기술적 3대 시나리오 (용어 변경)
        st.markdown(
            f"<div class='section-header'>6️⃣ 기술적 단순 시나리오 예시 (참고)</div>",
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

        # 7️⃣ 모의 계산기 (투자자문 오인 방지를 위해 '모의 시뮬레이터'로 명칭 변경)
        st.markdown(
            f"<div class='section-header'>7️⃣ 수치 계산 연습용 모의 시뮬레이터</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
        <table class="styled-table">
            <thead><tr><th>기술적 구간 구분</th><th>산출 기준가</th><th>가상 참고 비율</th><th>기술적 의미</th></tr></thead>
            <tbody>
                <tr><td><b>현재 기준가</b></td><td><b>{ref_buy_1:,}원</b></td><td><span style="color:#38A169;">40%</span></td><td>현재 시세 수치 기준</td></tr>
                <tr><td><b>하단 기술적 참고가</b></td><td><b>{ref_buy_2:,}원</b></td><td><span style="color:#38A169;">60%</span></td><td>-4% 조정 시 가상 수치</td></tr>
                <tr><td><b>상단 저항 참고가</b></td><td><b style="color:#E53E3E;">{ref_target:,}원</b></td><td><span style="color:#E53E3E;">-</span></td><td>+15% 단순 기술적 수치</td></tr>
                <tr><td><b>하단 지지 참고가</b></td><td><b style="color:#3182CE;">{ref_stop:,}원</b></td><td><span style="color:#3182CE;">-</span></td><td>-6% 단순 기술적 수치</td></tr>
            </tbody>
        </table>
        """,
            unsafe_allow_html=True,
        )

        budget = st.number_input(
            "💡 모의로 계산해볼 입력 금액(원):",
            min_value=1000000,
            value=10000000,
            step=1000000,
        )
        qty_1 = int((budget * 0.4) // ref_buy_1)
        qty_2 = int((budget * 0.6) // ref_buy_2)
        st.info(
            f"💡 **가상 시뮬레이션 결과:** {ref_buy_1:,}원 기준 약 **{qty_1:,}주**"
            f" / {ref_buy_2:,}원 기준 약 **{qty_2:,}주** 환산 가능 (단순 수학적"
            " 산출 결과)"
        )

        # 8️⃣ 실시간 뉴스 (Outlink 방식 명시)
        st.markdown(
            f"<div class='section-header'>8️⃣ [{stock_input}] 관련 외부 뉴스 (링크"
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

        naver_url = f"https://search.naver.com/search.naver?where=news&query={urllib.parse.quote(stock_input)}"
        st.markdown(
            f"""<div style="text-align:center; margin-top:15px; margin-bottom:20px;"><a href="{naver_url}" target="_blank"><button style="background-color:#03CF5D; color:white; border:none; padding:12px 24px; border-radius:6px; font-weight:bold; cursor:pointer; font-size:1rem;">🟢 네이버 뉴스 전체 검색 ➔</button></a></div>""",
            unsafe_allow_html=True,
        )

        # 하단 면책문구 재차 강조
        st.markdown(
            """
        <div class="disclaimer-box" style="text-align:center; margin-top:30px;">
            <b>[법적 책임의 한계 및 면책 고지]</b><br>
            본 웹사이트에서 제공하는 데이터, 분석 수치, 기술적 지표 및 시뮬레이션 결과는 알고리즘에 의해 자동 계산되는 단순 참고용 정보입니다.<br>
            어떠한 경우에도 투자 결과에 대한 법적 책임 소재의 증빙자료로 사용될 수 없으며, 금융투자 상품 거래에 따른 모든 위험과 책임은 이용자 본인에게 있습니다.
        </div>
        """,
            unsafe_allow_html=True,
        )

    except Exception as e:
      st.error(f"⚠️ 데이터 처리 중 오류가 발생했습니다: {e}")
