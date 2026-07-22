import datetime
import hashlib
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import yfinance as yf
from requests import Session

# =============================================================================
# 🔥 [수익화 설정] 쿠팡 파트너스 링크
# =============================================================================
COUPANG_LINK = "https://link.coupang.com/a/fAS0LGAFK8"

# Firebase 실시간 데이터베이스 URL
FIREBASE_URL = "https://mystockcommunity-dd967-default-rtdb.firebaseio.com/"


# -----------------------------------------------------------------------------
# 비밀번호 암호화 함수 (SHA-256)
# -----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Firebase 데이터베이스 연동 함수 (게시글 및 회원 정보)
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


def load_users():
    try:
        response = requests.get(f"{FIREBASE_URL}users.json", timeout=5)
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
        requests.put(
            f"{FIREBASE_URL}users/{safe_key}.json", json=user_data, timeout=5
        )
        return True
    except Exception:
        return False


# -----------------------------------------------------------------------------
# 1. 페이지 설정 & 증권사 MTS/HTS 스타일 커스텀 CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI주식분석",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background-color: #0b0e14; }
    
    @keyframes shine {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes pulse-subtle {
        0% { transform: scale(1); }
        50% { transform: scale(1.01); }
        100% { transform: scale(1); }
    }

    .animated-ad-banner {
        background: linear-gradient(120deg, #131b2e 0%, #1e293b 50%, #131b2e 100%);
        background-size: 200% 100%;
        animation: shine 5s infinite linear, pulse-subtle 4s infinite ease-in-out;
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-radius: 14px;
        padding: 20px 24px;
        text-align: center;
        margin: 24px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    .ad-badge {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        font-size: 0.7rem;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 6px;
        letter-spacing: 0.5px;
        margin-right: 8px;
        text-transform: uppercase;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
    }
    .ad-link {
        color: #38bdf8 !important;
        font-weight: 700;
        text-decoration: none;
        font-size: 1.05rem;
        transition: color 0.2s ease;
    }
    .ad-link:hover {
        color: #7dd3fc !important;
        text-decoration: underline;
    }

    .metric-card {
        background: linear-gradient(145deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        margin-bottom: 14px;
        transition: border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: #38bdf8;
    }
    .metric-title {
        color: #8b949e;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 8px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    .metric-value {
        color: #f0f6fc;
        font-size: 1.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    .custom-card {
        background-color: #161b22;
        border-left: 4px solid #3b82f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 16px;
        border-top: 1px solid #21262d;
        border-right: 1px solid #21262d;
        border-bottom: 1px solid #21262d;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .custom-card.bull { border-left-color: #ef4444; }
    .custom-card.bear { border-left-color: #3b82f6; }
    .custom-card.quant { border-left-color: #10b981; }

    .disclaimer-box {
        background: linear-gradient(135deg, #161b22 0%, #0f141c 100%);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 10px;
        padding: 16px 20px;
        margin: 16px 0 24px 0;
        font-size: 0.82rem;
        color: #c9d1d9;
        line-height: 1.6;
    }

    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: 0.92em;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #30363d;
    }
    .styled-table thead tr {
        background-color: #1f242d;
        color: #f0f6fc;
        text-align: left;
        font-weight: 700;
    }
    .styled-table th, .styled-table td {
        padding: 14px 18px;
        border-bottom: 1px solid #30363d;
    }
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #161b22;
    }
    .styled-table tbody tr:hover {
        background-color: #1c2128;
    }
    
    .section-header {
        font-size: 1.2rem;
        font-weight: 800;
        color: #58a6ff;
        margin-top: 32px;
        margin-bottom: 14px;
        border-bottom: 2px solid #21262d;
        padding-bottom: 8px;
        letter-spacing: -0.3px;
    }
    
    .post-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .post-card:hover {
        border-color: #3b82f6;
        transform: translateY(-1px);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 세션 상태 초기화
# -----------------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""
if "nickname" not in st.session_state:
    st.session_state["nickname"] = ""

# 사이드바 인증 센터
with st.sidebar:
    st.markdown("### 🔐 회원 인증 센터")

    if not st.session_state["logged_in"]:
        auth_mode = st.radio("모드 선택", ["로그인", "회원가입"], horizontal=True)

        if auth_mode == "로그인":
            with st.form("login_form"):
                login_id = st.text_input("아이디")
                login_pw = st.text_input("비밀번호", type="password")
                login_btn = st.form_submit_button(
                    "로그인", use_container_width=True, type="primary"
                )

                if login_btn:
                    users_db = load_users()
                    safe_key = (
                        login_id.replace(".", "_").replace("#", "_").replace("$", "_")
                    )
                    if safe_key in users_db and users_db[safe_key]["password"] == hash_password(
                        login_pw
                    ):
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = login_id
                        st.session_state["nickname"] = users_db[safe_key].get(
                            "nickname", login_id
                        )
                        st.success(f"환영합니다, {st.session_state['nickname']}님!")
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

        else:
            with st.form("signup_form"):
                new_id = st.text_input("사용할 아이디")
                new_nickname = st.text_input("커뮤니티 닉네임 (표시 이름)")
                new_pw = st.text_input("비밀번호", type="password")
                new_pw_check = st.text_input("비밀번호 확인", type="password")
                signup_btn = st.form_submit_button(
                    "회원가입 완료", use_container_width=True, type="primary"
                )

                if signup_btn:
                    if not new_id or not new_nickname or not new_pw:
                        st.warning("아이디, 닉네임, 비밀번호를 모두 입력해 주세요.")
                    elif new_pw != new_pw_check:
                        st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        users_db = load_users()
                        safe_key = (
                            new_id.replace(".", "_").replace("#", "_").replace("$", "_")
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
                                st.success("회원가입 완료! 로그인해 주세요.")
                            else:
                                st.error("회원가입 중 오류가 발생했습니다.")
    else:
        st.markdown(
            f"👤 접속 닉네임: <b style='color:#38bdf8;'>{st.session_state['nickname']}</b><br><span style='font-size:0.75rem; color:#8b949e;'>ID: {st.session_state['user_id']}</span>",
            unsafe_allow_html=True,
        )
        if st.button("로그아웃", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user_id"] = ""
            st.session_state["nickname"] = ""
            st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.8rem; color:#8b949e;'>⚡ AI 주식분석 플랫폼 v3.1<br>© 2026 Stock Community</div>",
        unsafe_allow_html=True,
    )

# 메인 헤더
st.markdown(
    """
    <div style="padding: 10px 0 20px 0;">
        <span style="font-size: 2rem; font-weight: 900; background: linear-gradient(90deg, #58a6ff, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">⚡ AI주식분석</span>
        <span style="color: #8b949e; font-size: 0.95rem; margin-left: 12px; font-weight: 600;">실시간 증권 데이터 분석 & 하이엔드 주주 커뮤니티</span>
    </div>
""",
    unsafe_allow_html=True,
)

tab_analysis, tab_board, tab_mypage = st.tabs(
    ["📊 AI 종목 기술적 진단", "💬 주주 오픈 토론방", "⚙️ 마이페이지"]
)


# -----------------------------------------------------------------------------
# 2. KRX 전 종목 자동 연동 및 검색 엔진 (세션 차단 우회 기능 포함)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def get_krx_stock_master():
    try:
        url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"
        df = pd.read_html(url, header=0)[0]
        df["종목코드"] = df["종목코드"].astype(str).str.zfill(6)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def search_naver_stock_code(query):
    try:
        url = f"https://ac.finance.naver.com/ac?q={urllib.parse.quote(query)}&target=stock"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        }
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            items = data.get("items", [])
            if items and len(items[0]) > 0:
                return items[0][0]
    except Exception:
        pass
    return None


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
    # 야후 파이낸스 차단 우회를 위한 커스텀 세션 헤더 장착
    session = Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    stock = yf.Ticker(ticker_symbol, session=session)
    df = stock.history(period="1y")
    if df.empty:
        if ticker_symbol.endswith(".KS"):
            alt_symbol = ticker_symbol.replace(".KS", ".KQ")
            stock = yf.Ticker(alt_symbol, session=session)
            df = stock.history(period="1y")
        elif ticker_symbol.endswith(".KQ"):
            alt_symbol = ticker_symbol.replace(".KQ", ".KS")
            stock = yf.Ticker(alt_symbol, session=session)
            df = stock.history(period="1y")
    return df, stock.info


def get_ticker_symbol_and_code(user_input):
    cleaned_input = user_input.strip()

    if cleaned_input.isdigit() and len(cleaned_input) == 6:
        test_url = f"https://finance.naver.com/item/main.naver?code={cleaned_input}"
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
            }
            resp = requests.get(test_url, headers=headers, timeout=3)
            if "KOSDAQ" in resp.text:
                return f"{cleaned_input}.KQ", cleaned_input
            else:
                return f"{cleaned_input}.KS", cleaned_input
        except:
            return f"{cleaned_input}.KQ", cleaned_input

    krx_df = get_krx_stock_master()
    if not krx_df.empty:
        matched = krx_df[krx_df["회사명"].str.lower() == cleaned_input.lower()]
        if not matched.empty:
            code = matched.iloc[0]["종목코드"]
            test_url = f"https://finance.naver.com/item/main.naver?code={code}"
            try:
                resp = requests.get(
                    test_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3
                )
                if "KOSDAQ" in resp.text:
                    return f"{code}.KQ", code
                else:
                    return f"{code}.KS", code
            except:
                return f"{code}.KQ", code

    special_mapping = {
        "e8": ("418620.KQ", "418620"),
        "E8": ("418620.KQ", "418620"),
        "이에이트": ("418620.KQ", "418620"),
        "스타코링크": ("060240.KQ", "060240"),
    }
    if cleaned_input.lower() in special_mapping:
        return special_mapping[cleaned_input.lower()]

    found_code = search_naver_stock_code(cleaned_input)
    if found_code:
        test_url = f"https://finance.naver.com/item/main.naver?code={found_code}"
        try:
            resp = requests.get(
                test_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3
            )
            if "KOSDAQ" in resp.text:
                return f"{found_code}.KQ", found_code
            else:
                return f"{found_code}.KS", found_code
        except:
            return f"{found_code}.KQ", found_code

    return f"{cleaned_input}.KQ", cleaned_input


@st.cache_data(ttl=3600)
def translate_to_ko(text):
    if not text or text == "기업 비즈니스 개요":
        return "제공된 기업 요약 정보가 없습니다."
    try:
        translated = GoogleTranslator(source="auto", target="ko").translate(text)
        return translated
    except Exception:
        return text


def calculate_quant_score_and_diagnosis(
    info, df, current_rsi, final_per_val, final_pbr_val, final_roe_val
):
    score = 5.0
    factors = []

    if isinstance(final_per_val, (int, float)) and final_per_val > 0:
        if final_per_val < 15:
            score += 1.5
            factors.append("밸류에이션 매력도 우수 (PER 15배 미만)")
        elif final_per_val > 40:
            score -= 1.0
            factors.append("밸류에이션 부담 존재 (PER 40배 초과)")
    else:
        score += 0.5

    if isinstance(final_roe_val, (int, float)):
        if final_roe_val > 0.15:
            score += 1.5
            factors.append("자기자본 이익률(ROE) 우수 (15% 이상)")
        elif final_roe_val < 0.05:
            score -= 0.5
            factors.append("수익성 개선 모니터링 필요 (ROE 5% 미만)")

    if 40 <= current_rsi <= 65:
        score += 1.0
        factors.append("안정적인 수급 및 적정 모멘텀 유지 구간")
    elif current_rsi > 75:
        score -= 1.0
        factors.append("단기 과열권 진입 (가격 조정 주의)")
    elif current_rsi < 30:
        score += 0.5
        factors.append("기술적 과매도 침체 구간 (반발 매수세 관찰)")

    if not df.empty and len(df) >= 60:
        ma20_last = df["MA20"].iloc[-1]
        ma60_last = df["MA60"].iloc[-1]
        close_last = df["Close"].iloc[-1]
        if close_last > ma20_last > ma60_last:
            score += 1.0
            factors.append("정배열 상승 추세 형성 (중장기 우상향)")
        elif close_last < ma20_last < ma60_last:
            score -= 1.0
            factors.append("역배열 하락 추세 주의")

    final_score = round(max(1.0, min(10.0, score)), 1)

    if final_score >= 8.0:
        diagnosis = (
            "강력한 펀더멘털과 우상향 추세가 동반되는 높은 매력도의 구간입니다."
        )
    elif final_score >= 6.0:
        diagnosis = (
            "안정적인 재무 지표를 바탕으로 박스권 및 완만한 추세를 보이는 구간입니다."
        )
    elif final_score >= 4.0:
        diagnosis = "단기 변동성이 확대되거나 수급 점검이 필요한 중립 구간입니다."
    else:
        diagnosis = (
            "재무적 지표 또는 기술적 추세의 보수적인 접근 및 리스크 관리가 필요한"
            " 구간입니다."
        )

    return final_score, diagnosis, factors


# =============================================================================
# 🟢 TAB 1: AI 종목 기술적 분석 화면
# =============================================================================
with tab_analysis:
    st.markdown(
        """
    <div class="disclaimer-box">
        <b style="color:#ef4444;">⚠️ 투자 리스크 고지 및 법적 면책 고지 (Disclaimer)</b><br>
        본 플랫폼은 알고리즘에 기반한 기술적 참고 지표 및 오픈 커뮤니티 공간을 제공하며, 개별 종목에 대한 투자 권유나 투자자문 목적이 아닙니다.<br>
        모든 투자의 최종 판단과 책임은 투자자 본인에게 있으므로 신중한 의사결정을 권장합니다.
    </div>
    """,
        unsafe_allow_html=True,
    )

    stock_input = st.text_input(
        "🔍 분석 대상 종목명 또는 6자리 종목코드를 입력하세요 (국내 전종목 연동완료):",
        placeholder="예: 삼성전자, 스타코링크, E8, 에코프로, 005930",
    )

    if st.button(
        "🚀 하이엔드 AI 기술적 진단 실행", type="primary", use_container_width=True
    ):
        if not stock_input:
            st.warning("⚠️ 분석할 종목명이나 종목코드를 입력해주세요.")
        else:
            ticker_symbol, pure_code = get_ticker_symbol_and_code(stock_input)

            st.markdown(
                f"""
            <div class="animated-ad-banner">
                <div style="margin-bottom:6px;">
                    <span class="ad-badge">SPONSORED</span>
                    <span style="font-size:0.8rem; color:#9ca3af;">투자의 안목을 높여주는 프리미엄 북앤특가 콜렉션</span>
                </div>
                <a href="{COUPANG_LINK}" target="_blank" class="ad-link">
                    🔥 [금주의 베스트 재테크/경제 도서 특별 할인전] 바로가기 ➔
                </a>
                <div style="font-size:0.7rem; color:#6b7280; margin-top:6px;">
                    파트너스 활동을 통해 일정액의 수수료를 제공받을 수 있습니다.
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            try:
                with st.spinner(
                    "⚡ 실시간 증권 빅데이터 및 퀀트 지표를 정밀 산출 중입니다..."
                ):
                    df, info = fetch_stock_history(ticker_symbol)

                if df is None or df.empty:
                    st.error(
                        f"⚠️ [{stock_input}] (티커: {ticker_symbol}) 종목의 데이터를 불러오지 못했습니다.<br>"
                        "원인 안내:<br>"
                        "1. 야후 파이낸스(yfinance) 서버에서 일시적인 API 요청을 차단했거나 응답이 지연되었습니다.<br>"
                        "2. 정확한 국내 종목명(예: 삼성전자) 또는 6자리 종목코드(예: 005930)를 다시 확인해 주세요.",
                        icon="🚨"
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

                    sector = info.get("sector", "국내 상장 주식 / 금융 섹터")
                    raw_summary = info.get("longBusinessSummary", "기업 비즈니스 개요")
                    summary = translate_to_ko(raw_summary)

                    yf_per = info.get("trailingPE")
                    yf_pbr = info.get("priceToBook")
                    yf_roe = info.get("returnOnEquity")

                    raw_per_num = yf_per
                    if naver_data["per"] != "-":
                        try:
                            raw_per_num = float(
                                naver_data["per"].replace("배", "").strip()
                            )
                        except:
                            pass

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

                    quant_score, diagnosis_text, quant_factors = (
                        calculate_quant_score_and_diagnosis(
                            info, df, current_rsi, raw_per_num, yf_pbr, yf_roe
                        )
                    )

                    ref_buy_1 = current_price
                    ref_buy_2 = int(current_price * 0.96)
                    ref_target = int(current_price * 1.15)
                    ref_stop = int(current_price * 0.94)

                    c1, c2, c3, c4, c5 = st.columns(5)
                    color_style = (
                        "#ef4444"
                        if price_change > 0
                        else ("#3b82f6" if price_change < 0 else "#8b949e")
                    )
                    sign = "+" if price_change > 0 else ""

                    c1.markdown(
                        f"""<div class="metric-card"><div class="metric-title">실시간 주가</div>
                    <div class="metric-value" style="color:{color_style};">{current_price:,}원 <span style="font-size:0.7rem; font-weight:normal;">({sign}{pct_change:.2f}%)</span></div></div>""",
                        unsafe_allow_html=True,
                    )
                    c2.markdown(
                        f"""<div class="metric-card"><div class="metric-title">RSI (14일)</div>
                    <div class="metric-value">{current_rsi} <span style="font-size:0.7rem; color:#8b949e; font-weight:normal;">({"과열" if current_rsi>70 else ("중립" if current_rsi>30 else "침체")})</span></div></div>""",
                        unsafe_allow_html=True,
                    )
                    c3.markdown(
                        f"""<div class="metric-card"><div class="metric-title">PER (선행/확정)</div>
                    <div class="metric-value" style="font-size:1.05rem;">{per_display_text}</div></div>""",
                        unsafe_allow_html=True,
                    )
                    c4.markdown(
                        f"""<div class="metric-card"><div class="metric-title">PBR / ROE</div>
                    <div class="metric-value" style="font-size:1.05rem;">{final_pbr} / {final_roe}</div></div>""",
                        unsafe_allow_html=True,
                    )
                    c5.markdown(
                        f"""<div class="metric-card"><div class="metric-title">AI 퀀트 점수</div>
                    <div class="metric-value" style="color:#10b981;">{quant_score} <span style="font-size:0.7rem; font-weight:normal;">/ 10점</span></div></div>""",
                        unsafe_allow_html=True,
                    )

                    st.write("")

                    factors_html = "".join([f"<li>{f}</li>" for f in quant_factors])
                    st.markdown(
                        f"""
                    <div class="custom-card quant">
                        <h4 style="color:#10b981; margin-bottom:8px;">🤖 AI 알고리즘 정밀 퀀트 진단 결과 ({quant_score} / 10점)</h4>
                        <p style="color:#f0f6fc; font-size:1rem; font-weight:600; margin-bottom:10px;">{diagnosis_text}</p>
                        <ul style="color:#c9d1d9; font-size:0.9rem; margin:0; line-height:1.5;">
                            {factors_html}
                        </ul>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        "<div class='section-header'>1️⃣ 기업 비즈니스 프로필 및 사업 구조</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"""
                    <div class="custom-card">
                        <h4 style="color:#58a6ff; margin-bottom:8px;">🏢 [{stock_input}] 기업 개요</h4>
                        <ul style="color:#c9d1d9; line-height:1.6;">
                            <li><b>핵심 섹터:</b> {sector}</li>
                            <li><b>시장 지위:</b> 해당 산업군 내 주력 플레이어</li>
                        </ul>
                        <p style="color:#8b949e; font-size:0.9rem; margin-top:12px;"><b>주요 사업 요약:</b> {summary[:350]}...</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        "<div class='section-header'>2️⃣ 테크니컬 차트 & 이동평균선 분석</div>",
                        unsafe_allow_html=True,
                    )
                    fig = make_subplots(
                        rows=2,
                        cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.06,
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
                            increasing_line_color="#ef4444",
                            decreasing_line_color="#3b82f6",
                        ),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df["MA20"],
                            line=dict(color="#facc15", width=1.5),
                            name="MA 20",
                        ),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df["MA60"],
                            line=dict(color="#fb923c", width=1.5),
                            name="MA 60",
                        ),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df["MA120"],
                            line=dict(color="#2dd4bf", width=1.5),
                            name="MA 120",
                        ),
                        row=1,
                        col=1,
                    )

                    colors = [
                        "#ef4444" if c >= o else "#3b82f6"
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
                        height=480,
                        margin=dict(l=10, r=10, t=10, b=10),
                        xaxis_rangeslider_visible=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown(
                        "<div class='section-header'>3️⃣ 핵심 재무 밸류에이션 매트릭스</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"""
                    <table class="styled-table">
                        <thead>
                            <tr><th>재무 지표</th><th>산출 데이터</th><th>분석 가이드</th></tr>
                        </thead>
                        <tbody>
                            <tr><td><b>선행 PER</b></td><td><b style="color:#58a6ff;">{final_fper}</b></td><td>컨센서스 추정 이익 기준 수익성 지표</td></tr>
                            <tr><td><b>확정 PER</b></td><td><b style="color:#f0f6fc;">{final_per}</b></td><td>최근 실적 결산 기준 주가수익비율</td></tr>
                            <tr><td><b>PBR</b></td><td><b>{final_pbr}</b></td><td>주가순자산비율 (자산가치 대비 배율)</td></tr>
                            <tr><td><b>ROE</b></td><td><b>{final_roe}</b></td><td>자기자본이익률 (수익 창출 효율성)</td></tr>
                        </tbody>
                    </table>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        "<div class='section-header'>4️⃣ 알고리즘 기반 가격 시나리오 참고</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"""
                    <div class="custom-card bull">
                        <h4 style="color:#ef4444; margin-bottom:6px;">📈 상향 돌파 시나리오 (저항 참고선: {ref_target:,}원)</h4>
                        <p style="color:#c9d1d9; margin:0; font-size:0.95rem;">거래량 유입 동반 시 주요 매물대 상단 돌파 여부 관찰</p>
                    </div>
                    <div class="custom-card">
                        <h4 style="color:#8b949e; margin-bottom:6px;">📊 박스권 횡보 시나리오 (지지 참고선: {ref_buy_2:,}원 ~ {ref_buy_1:,}원)</h4>
                        <p style="color:#c9d1d9; margin:0; font-size:0.95rem;">단기 이동평균선 부근 수급 밀집 구간 매물 소화 과정</p>
                    </div>
                    <div class="custom-card bear">
                        <h4 style="color:#3b82f6; margin-bottom:6px;">📉 하향 이탈 시나리오 (지지선 이탈: {ref_stop:,}원)</h4>
                        <p style="color:#c9d1d9; margin:0; font-size:0.95rem;">시장 리스크 확대 시 하단 주요 지지 라인 방어력 체크</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"<div class='section-header'>5️⃣ [{stock_input}] 실시간 동향 및 뉴스</div>",
                        unsafe_allow_html=True,
                    )
                    realtime_news = fetch_realtime_news(stock_input)
                    if realtime_news:
                        for news in realtime_news:
                            st.markdown(
                                f"""
                            <div style="background-color:#161b22; border:1px solid #30363d; border-radius:10px; padding:16px; margin-bottom:12px;">
                                <div style="font-size:0.8rem; color:#8b949e; margin-bottom:4px;">📰 <b>{news['source']}</b> • {news['pub_date']}</div>
                                <div style="font-size:1.05rem; font-weight:bold; color:#f0f6fc; margin-bottom:8px;">{news['title']}</div>
                                <a href="{news['link']}" target="_blank" style="color:#38bdf8; font-size:0.85rem; text-decoration:none;">🔗 뉴스 원문 기사 전문 보기 ➔</a>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info("관련 실시간 뉴스가 없습니다.")

            except Exception as e:
                st.error(f"⚠️ 분석 실행 중 오류가 발생했습니다: {e}")

# =============================================================================
# 💬 TAB 2: 주주 오픈 토론방 (커뮤니티)
# =============================================================================
with tab_board:
    st.markdown("### 💬 하이엔드 주주 오픈 토론방")
    st.markdown("전국 주주님들과 자유롭게 투자 의견을 나누고 인사이트를 공유해보세요.")

    posts = load_posts()

    if st.session_state["logged_in"]:
        with st.form("write_post_form", clear_on_submit=True):
            st.markdown(f"**✍️ 글쓰기** (작성자: {st.session_state['nickname']})")
            post_title = st.text_input("제목", placeholder="예: [토론] 오늘 실적 발표 관련 의견 공유합니다.")
            post_content = st.text_area("내용을 입력하세요", placeholder="자유로운 투자 토론 및 의견을 남겨주세요.")
            submit_post = st.form_submit_button("게시물 등록", type="primary")

            if submit_post:
                if not post_title or not post_content:
                    st.warning("제목과 내용을 모두 입력해 주세요.")
                else:
                    new_post = {
                        "id": int(datetime.datetime.now().timestamp()),
                        "user_id": st.session_state["user_id"],
                        "nickname": st.session_state["nickname"],
                        "title": post_title,
                        "content": post_content,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "likes": 0,
                        "comments": [],
                    }
                    posts.insert(0, new_post)
                    save_posts_to_firebase(posts)
                    st.success("게시글이 성공적으로 등록되었습니다!")
                    st.rerun()
    else:
        st.info("💡 게시글을 작성하시려면 사이드바에서 로그인 또는 회원가입을 진행해 주세요.")

    st.markdown("---")
    st.markdown("#### 📋 실시간 주주 토론 피드")

    if not posts:
        st.info("등록된 게시글이 없습니다. 첫 번째 주주가 되어 의견을 남겨보세요!")
    else:
        for idx, post in enumerate(posts):
            with st.container():
                st.markdown(
                    f"""
                <div class="post-card">
                    <div style="font-size:0.8rem; color:#8b949e; margin-bottom:6px;">
                        👤 <b>{post.get('nickname', '익명')}</b> • {post.get('date', '')}
                    </div>
                    <div style="font-size:1.15rem; font-weight:bold; color:#f0f6fc; margin-bottom:8px;">
                        {post.get('title', '')}
                    </div>
                    <div style="color:#c9d1d9; font-size:0.95rem; white-space: pre-wrap; margin-bottom:12px;">
                        {post.get('content', '')}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

# =============================================================================
# ⚙️ TAB 3: 마이페이지
# =============================================================================
with tab_mypage:
    st.markdown("### ⚙️ 마이페이지 및 회원 정보")
    if st.session_state["logged_in"]:
        st.markdown(
            f"""
        <div class="custom-card">
            <h4>👤 회원 계정 정보</h4>
            <p><b>닉네임:</b> {st.session_state['nickname']}</p>
            <p><b>아이디:</b> {st.session_state['user_id']}</p>
            <p><b>계정 상태:</b> 정상 인증 완료</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("로그인 후 이용하실 수 있는 공간입니다. 사이드바에서 로그인해 주세요.")
