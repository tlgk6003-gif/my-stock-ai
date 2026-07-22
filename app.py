import datetime
import hashlib
import json
import re
import time
import urllib.parse
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st

# =============================================================================
# 🔥 [수익화 설정 영역] 쿠팡, 구글 애드센스, 카카오 애드핏 설정
# =============================================================================
COUPANG_LINK = "https://link.coupang.com/a/fAS0LGAFK8"
GOOGLE_ADSENSE_CLIENT = "ca-pub-XXXXXXXXXXXXXXXX" 
GOOGLE_ADSENSE_SLOT = "1234567890"
KAKAO_ADFIT_UNIT = "DAN-W4CcfdCUtd8S6CN5"
FIREBASE_URL = "https://mystockcommunity-dd967-default-rtdb.firebaseio.com/"

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

st.set_page_config(page_title="AI주식분석", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .animated-ad-banner {
        background: linear-gradient(120deg, #131b2e 0%, #1e293b 50%, #131b2e 100%);
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-radius: 14px;
        padding: 20px 24px;
        text-align: center;
        margin: 24px 0;
    }
    .ad-badge {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white; font-size: 0.7rem; font-weight: 800; padding: 4px 10px; border-radius: 6px; margin-right: 8px;
    }
    .ad-link { color: #38bdf8 !important; font-weight: 700; text-decoration: none; font-size: 1.05rem; }
    .metric-card {
        background: linear-gradient(145deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #21262d; border-radius: 12px; padding: 18px; margin-bottom: 14px;
    }
    .metric-title { color: #8b949e; font-size: 0.75rem; font-weight: 700; margin-bottom: 8px; text-transform: uppercase; }
    .metric-value { color: #f0f6fc; font-size: 1.2rem; font-weight: 800; }
    .custom-card {
        background-color: #161b22; border-left: 4px solid #3b82f6; border-radius: 10px; padding: 20px; margin-bottom: 16px;
        border-top: 1px solid #21262d; border-right: 1px solid #21262d; border-bottom: 1px solid #21262d;
    }
    .disclaimer-box {
        background: linear-gradient(135deg, #161b22 0%, #0f141c 100%);
        border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 10px; padding: 16px 20px; margin: 16px 0 24px 0; font-size: 0.82rem; color: #c9d1d9;
    }
    .section-header { font-size: 1.2rem; font-weight: 800; color: #58a6ff; margin-top: 32px; margin-bottom: 14px; border-bottom: 2px solid #21262d; padding-bottom: 8px; }
    .post-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 16px; }
    </style>
""", unsafe_allow_html=True)

def render_kakao_adfit():
  adfit_html = f"""
    <div style="text-align:center; margin: 20px 0; background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d;">
        <ins class="kakao_ad_area" style="display:none;"
             data-ad-unit="{KAKAO_ADFIT_UNIT}"
             data-ad-width="300"
             data-ad-height="250"></ins>
        <script type="text/javascript" src="//t1.daumcdn.net/kas/static/ba.min.js" async></script>
    </div>
    """
  st.components.v1.html(adfit_html, height=290)

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "user_id" not in st.session_state: st.session_state["user_id"] = ""
if "nickname" not in st.session_state: st.session_state["nickname"] = ""

with st.sidebar:
  st.markdown("### 🔐 회원 인증 센터")
  if not st.session_state["logged_in"]:
    auth_mode = st.radio("모드 선택", ["로그인", "회원가입"], horizontal=True)
    if auth_mode == "로그인":
      with st.form("login_form"):
        login_id = st.text_input("아이디")
        login_pw = st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인", use_container_width=True, type="primary"):
          users_db = load_users()
          safe_key = login_id.replace(".", "_").replace("#", "_").replace("$", "_")
          if safe_key in users_db and users_db[safe_key]["password"] == hash_password(login_pw):
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = login_id
            st.session_state["nickname"] = users_db[safe_key].get("nickname", login_id)
            st.rerun()
          else:
            st.error("아이디 또는 비밀번호가 불일치합니다.")
    else:
      with st.form("signup_form"):
        new_id = st.text_input("사용할 아이디")
        new_nickname = st.text_input("커뮤니티 닉네임")
        new_pw = st.text_input("비밀번호", type="password")
        new_pw_check = st.text_input("비밀번호 확인", type="password")
        if st.form_submit_button("회원가입 완료", use_container_width=True, type="primary"):
          if new_pw != new_pw_check:
            st.error("비밀번호가 불일치합니다.")
          else:
            users_db = load_users()
            safe_key = new_id.replace(".", "_").replace("#", "_").replace("$", "_")
            if safe_key in users_db:
              st.error("이미 존재하는 아이디입니다.")
            else:
              user_data = {"user_id": new_id, "nickname": new_nickname, "password": hash_password(new_pw), "joined_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
              if save_user_to_firebase(new_id, user_data):
                st.success("회원가입 완료! 로그인하세요.")
  else:
    st.markdown(f"👤 <b>{st.session_state['nickname']}</b>님 접속중", unsafe_allow_html=True)
    if st.button("로그아웃", use_container_width=True):
      st.session_state["logged_in"] = False
      st.session_state["user_id"] = ""
      st.session_state["nickname"] = ""
      st.rerun()

st.markdown("""
    <div style="padding: 10px 0 20px 0;">
        <span style="font-size: 2rem; font-weight: 900; color: #58a6ff;">⚡ AI주식분석</span>
        <span style="color: #8b949e; font-size: 0.95rem; margin-left: 12px;">실시간 증권 데이터 분석 & 커뮤니티</span>
    </div>
""", unsafe_allow_html=True)

tab_analysis, tab_board, tab_mypage = st.tabs(["📊 AI 종목 기술적 진단", "💬 주주 오픈 토론방", "⚙️ 마이페이지"])

def get_stock_code(user_input):
  cleaned = user_input.strip()
  if cleaned.isdigit() and len(cleaned) == 6:
    return cleaned
  
  mapping = {
      "삼성전자": "005930",
      "카카오": "035720",
      "형지글로벌": "011080",
      "이에이트": "418620",
      "스타코링크": "060240",
      "SK하이닉스": "000660",
      "LG에너지솔루션": "373220",
      "현대차": "005380"
  }
  return mapping.get(cleaned, "005930")

@st.cache_data(ttl=1800)
def fetch_naver_chart_data(code):
  try:
    url = f"https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=day&count=250&type=json"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    res = requests.get(url, headers=headers, timeout=5)
    if res.status_code == 200:
      data = res.json()
      chart_data = data.get("itemData", [])
      if chart_data:
        rows = []
        for item in chart_data:
          # 형식: [날짜, 시가, 고가, 저가, 종가, 거래량]
          rows.append({
              "Date": pd.to_datetime(str(item[0]), format="%Y%m%d"),
              "Open": float(item[1]),
              "High": float(item[2]),
              "Low": float(item[3]),
              "Close": float(item[4]),
              "Volume": float(item[5])
          })
        df = pd.DataFrame(rows)
        df.set_index("Date", inplace=True)
        return df
  except Exception:
    pass
  return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_naver_financial_info(code):
  url = f"https://finance.naver.com/item/main.naver?code={code}"
  headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
  res_data = {"per": "15.4배", "pbr": "1.4배", "summary": "해당 기업은 안정적인 실적 흐름을 유지하며 시장에서 주목을 받고 있는 종목입니다."}
  try:
    resp = requests.get(url, headers=headers, timeout=3)
    if resp.status_code == 200:
      text = resp.text
      per_match = re.search(r'<em id="_per">([\d\.\-]+)</em>', text)
      if per_match and per_match.group(1) != "-": res_data["per"] = f"{per_match.group(1)}배"
      pbr_match = re.search(r'<em id="_pbr">([\d\.\-]+)</em>', text)
      if pbr_match and pbr_match.group(1) != "-": res_data["pbr"] = f"{pbr_match.group(1)}배"
  except Exception:
    pass
  return res_data

with tab_analysis:
  st.markdown("""
  <div class="disclaimer-box">
      <b style="color:#ef4444;">⚠️ 투자 리스크 고지 및 법적 면책 고지</b><br>
      본 플랫폼의 모든 데이터는 참고용이며 투자의 책임은 본인에게 있습니다.
  </div>
  """, unsafe_allow_html=True)

  stock_input = st.text_input("🔍 종목명 입력:", placeholder="예: 삼성전자, 카카오, 이에이트")

  if st.button("🚀 AI 기술적 진단 실행", type="primary", use_container_width=True):
    if not stock_input:
      st.warning("종목명을 입력해주세요.")
    else:
      code = get_stock_code(stock_input)
      
      st.markdown(f"""
      <div class="animated-ad-banner">
          <span class="ad-badge">SPONSORED</span>
          <a href="{COUPANG_LINK}" target="_blank" class="ad-link">🔥 [베스트 경제/재테크 도서 할인전] 바로가기 ➔</a>
      </div>
      """, unsafe_allow_html=True)

      with st.spinner("실시간 데이터 분석 중..."):
        df = fetch_naver_chart_data(code)
        fin_info = get_naver_financial_info(code)

      if df.empty or len(df) < 5:
        st.error("⚠️ 데이터를 불러오는 중 일시적인 지연이 발생했습니다. 잠시 후 다시 시도해 주세요.")
      else:
        current_price = int(df["Close"].iloc[-1])
        prev_price = int(df["Close"].iloc[-2])
        price_change = current_price - prev_price
        pct_change = (price_change / prev_price) * 100

        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA60"] = df["Close"].rolling(window=60).mean()
        
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        current_rsi = round(float(100 - (100 / (1 + (gain / loss).iloc[-1]))), 1)

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-title">실시간 주가</div><div class="metric-value">{current_price:,}원 ({pct_change:+.2f}%)</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-title">RSI</div><div class="metric-value">{current_rsi}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-title">PER</div><div class="metric-value">{fin_info["per"]}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-title">PBR</div><div class="metric-value">{fin_info["pbr"]}</div></div>', unsafe_allow_html=True)

        st.markdown("<div class='section-header'>테크니컬 차트</div>", unsafe_allow_html=True)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="주가"), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="거래량"), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<div class='section-header'>기업 개요</div>", unsafe_allow_html=True)
        st.markdown(f'<div class="custom-card"><p>{fin_info["summary"]}</p></div>', unsafe_allow_html=True)
        
        render_kakao_adfit()

with tab_board:
  st.subheader("💬 주주 오픈 토론방")
  if st.session_state["logged_in"]:
    with st.form("post_form", clear_on_submit=True):
      title = st.text_input("제목")
      content = st.text_area("내용")
      if st.form_submit_button("등록"):
        if title and content:
          posts = load_posts()
          new_id = (max([p.get("id", 0) for p in posts]) + 1) if posts else 1
          posts.insert(0, {"id": new_id, "author": st.session_state["nickname"], "title": title, "content": content, "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")})
          save_posts_to_firebase(posts)
          st.success("등록되었습니다!")
          st.rerun()
  else:
    st.info("로그인 후 글을 작성할 수 있습니다.")

  for p in load_posts():
    st.markdown(f"""<div class="post-card"><b>{p.get('title')}</b><p>{p.get('content')}</p><span style="font-size:0.8rem;color:#8b949e;">{p.get('author')} | {p.get('date')}</span></div>""", unsafe_allow_html=True)

with tab_mypage:
  st.subheader("⚙️ 마이페이지")
  if st.session_state["logged_in"]:
    st.markdown(f"현재 닉네임: **{st.session_state['nickname']}**")
  else:
    st.warning("로그인 필요")
