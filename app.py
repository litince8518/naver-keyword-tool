"""
키워드 종합 분석기 v6.11
====================
네이버 키워드 + 구글 트렌드 + 네이버 데이터랩 + 트렌드 발굴 + AI 키워드 자동수집(제미나이)

[변경 이력]
- v6.4: AI 키워드 탭 추가 (클로드·제미나이 각각 발굴 → 네이버 실측, 모델별 따로 출력)
- v6.5: AI 키워드 탭 카테고리 선택을 드롭다운 → 버튼 그리드로 변경
- v6.6: AI 키워드 탭 카테고리 복수 선택(토글) 지원, 결과에 카테고리 칼럼 추가
- v6.7: AI 키 저장 시 공백 제거(strip), API 오류 메시지에 실제 응답 본문 표시
- v6.8: 클로드 제거(결제 부담), 제미나이 전용으로 정리 + 모델명 2.0(폐기)→2.5-flash 수정
- v6.9: 제미나이 프롬프트 수정 — 문장형 대신 2~4단어 짧은 키워드 강제(네이버 검색량 측정 가능하게)
- v6.10: 시드 텍스트 버그 수정 — 블로그(라디오) 변경이 복사 텍스트에 반영되도록 text_area key 제거
- v6.11: 키워드 검증 탭 순서 변경 — 블로그 선택을 키워드 입력 위로 올림(블로그 먼저 → 검증)
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import time
import hmac
import hashlib
import base64
import math
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="키워드 종합 분석기", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.3rem; }
    .subtitle { color: #6b7280; margin-bottom: 2rem; }
    .api-status-ok { background: #d1fae5; color: #065f46; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600; }
    .api-status-no { background: #fee2e2; color: #991b1b; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "api_configured" not in st.session_state:
    st.session_state.api_configured = False
    st.session_state.api_keys = {}
if "keys_loaded_from_browser" not in st.session_state:
    st.session_state.keys_loaded_from_browser = False
if "ai_keys" not in st.session_state:
    st.session_state.ai_keys = {}
if "ai_keys_loaded" not in st.session_state:
    st.session_state.ai_keys_loaded = False

load_keys_html = """
<script>
(function() {
    const keys = ['client_id', 'client_secret', 'ad_api_key', 'ad_secret_key', 'ad_customer_id', 'gemini_api_key'];
    const loaded = {};
    let hasAny = false;
    keys.forEach(k => {
        const v = localStorage.getItem('naver_kw_' + k);
        if (v) { loaded[k] = v; hasAny = true; }
    });
    if (hasAny) {
        const params = new URLSearchParams(window.parent.location.search);
        let needReload = false;
        keys.forEach(k => {
            if (loaded[k] && !params.get(k)) {
                params.set(k, loaded[k]);
                needReload = true;
            }
        });
        if (needReload) {
            const newUrl = window.parent.location.pathname + '?' + params.toString();
            window.parent.history.replaceState({}, '', newUrl);
            window.parent.location.reload();
        }
    }
})();
</script>
"""

query_params = st.query_params

# AI 키 (클로드/제미나이) 로드 — 네이버와 독립적으로 처리
if not st.session_state.ai_keys_loaded:
    ai_loaded = {}
    for k in ['gemini_api_key']:
        if k in query_params:
            ai_loaded[k] = query_params[k]
    if ai_loaded:
        st.session_state.ai_keys.update(ai_loaded)
    st.session_state.ai_keys_loaded = True

if not st.session_state.api_configured and not st.session_state.keys_loaded_from_browser:
    loaded_keys = {}
    expected = ['client_id', 'client_secret', 'ad_api_key', 'ad_secret_key', 'ad_customer_id']
    for k in expected:
        if k in query_params:
            loaded_keys[k] = query_params[k]
    
    if len(loaded_keys) == 5:
        st.session_state.api_keys = loaded_keys
        st.session_state.api_configured = True
        st.session_state.keys_loaded_from_browser = True
        st.query_params.clear()
    else:
        st.session_state.keys_loaded_from_browser = True
        components.html(load_keys_html, height=0)

st.markdown('<div class="main-header">🔍 키워드 종합 분석기</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">네이버 + 구글 + 데이터랩 + 실시간 트렌드까지</div>', unsafe_allow_html=True)


def save_to_localstorage(keys_dict):
    js_data = json.dumps(keys_dict)
    save_html = f"""
    <script>
    const data = {js_data};
    Object.keys(data).forEach(k => {{
        localStorage.setItem('naver_kw_' + k, data[k]);
    }});
    </script>
    """
    components.html(save_html, height=0)


def clear_localstorage():
    clear_html = """
    <script>
    ['client_id', 'client_secret', 'ad_api_key', 'ad_secret_key', 'ad_customer_id'].forEach(k => {
        localStorage.removeItem('naver_kw_' + k);
    });
    </script>
    """
    components.html(clear_html, height=0)


def save_ai_keys_to_localstorage(ai_dict):
    js_data = json.dumps(ai_dict)
    save_html = f"""
    <script>
    const data = {js_data};
    Object.keys(data).forEach(k => {{
        localStorage.setItem('naver_kw_' + k, data[k]);
    }});
    </script>
    """
    components.html(save_html, height=0)


def clear_ai_keys_localstorage():
    clear_html = """
    <script>
    ['claude_api_key', 'gemini_api_key'].forEach(k => {
        localStorage.removeItem('naver_kw_' + k);
    });
    </script>
    """
    components.html(clear_html, height=0)


# ================================================
# 사이드바
# ================================================
with st.sidebar:
    st.header("⚙️ API 설정")
    
    if st.session_state.api_configured:
        st.markdown('<div class="api-status-ok">✅ 네이버 API 로드 완료</div>', unsafe_allow_html=True)
        st.caption("브라우저에 저장됨")
        st.write("")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✏️ 수정", use_container_width=True):
                st.session_state.api_configured = False
                st.rerun()
        with col_b:
            if st.button("🗑️ 삭제", use_container_width=True):
                st.session_state.api_configured = False
                st.session_state.api_keys = {}
                clear_localstorage()
                st.success("삭제됨")
                time.sleep(1)
                st.rerun()
    else:
        st.markdown('<div class="api-status-no">⚠️ 네이버 API 키 입력 필요</div>', unsafe_allow_html=True)
        st.caption("구글 탭은 키 없이도 사용 가능")
    
    st.markdown("---")
    
    with st.expander("🔑 네이버 API 키 입력", expanded=not st.session_state.api_configured):
        st.caption("**검색/데이터랩 API** (developers.naver.com)")
        client_id = st.text_input("Client ID", value=st.session_state.api_keys.get("client_id", ""), type="password")
        client_secret = st.text_input("Client Secret", value=st.session_state.api_keys.get("client_secret", ""), type="password")
        
        st.caption("**검색광고 API** (searchad.naver.com)")
        ad_api_key = st.text_input("Access License", value=st.session_state.api_keys.get("ad_api_key", ""), type="password")
        ad_secret_key = st.text_input("Secret Key", value=st.session_state.api_keys.get("ad_secret_key", ""), type="password")
        ad_customer_id = st.text_input("Customer ID", value=st.session_state.api_keys.get("ad_customer_id", ""))
        
        if st.button("💾 저장 (브라우저에 보관)", type="primary", use_container_width=True):
            if all([client_id, client_secret, ad_api_key, ad_secret_key, ad_customer_id]):
                keys_dict = {
                    "client_id": client_id, "client_secret": client_secret,
                    "ad_api_key": ad_api_key, "ad_secret_key": ad_secret_key,
                    "ad_customer_id": ad_customer_id,
                }
                st.session_state.api_keys = keys_dict
                st.session_state.api_configured = True
                save_to_localstorage(keys_dict)
                st.success("✅ 저장 완료!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("⚠️ 5개 키 모두 입력하세요")
    
    with st.expander("🤖 Gemini API 키 (선택) — 키워드 자동수집용", expanded=False):
        st.caption("**Gemini** (aistudio.google.com) — 무료 발급")
        gemini_key = st.text_input("Gemini API Key", value=st.session_state.ai_keys.get("gemini_api_key", ""), type="password", key="gemini_key_input")
        
        c_ai1, c_ai2 = st.columns(2)
        with c_ai1:
            if st.button("💾 저장", use_container_width=True, key="save_ai_keys"):
                if gemini_key:
                    ai_dict = {"gemini_api_key": gemini_key.strip()}
                    st.session_state.ai_keys = ai_dict
                    save_ai_keys_to_localstorage(ai_dict)
                    st.success("✅ 저장됨")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("키를 입력하세요")
        with c_ai2:
            if st.button("🗑️ 삭제", use_container_width=True, key="clear_ai_keys"):
                st.session_state.ai_keys = {}
                clear_ai_keys_localstorage()
                st.success("삭제됨")
                time.sleep(1)
                st.rerun()
        
        if st.session_state.ai_keys.get("gemini_api_key"):
            st.caption("Gemini ✅")
    
    st.markdown("---")
    st.markdown("""**📋 이럴 때 어느 탭?**
- 뭐 쓸지 모를 때 → 🏠 홈 / 🔥 글감 찾기
- 키워드 정했는데 쓸까 고민 → 🎯 키워드 검증
- 여러 개 한꺼번에 → 📋 여러 개 검증
- 더 세부 글감으로 쪼개기 → 🪓 세부 글감 파기
- 부가: 📈 구글 비교 / 📊 누가 검색하나""")


# ================================================
# 네이버 분석 함수
# ================================================
def _sig(secret, ts, method, uri):
    msg = f"{ts}.{method}.{uri}"
    return base64.b64encode(hmac.new(bytes(secret, "utf-8"), msg.encode("utf-8"), hashlib.sha256).digest()).decode("utf-8")

def _ad_headers(keys, method, uri):
    ts = str(round(time.time() * 1000))
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": ts,
        "X-API-KEY": keys["ad_api_key"],
        "X-Customer": str(keys["ad_customer_id"]),
        "X-Signature": _sig(keys["ad_secret_key"], ts, method, uri),
    }

def _parse(v):
    if isinstance(v, int): return v
    if isinstance(v, str):
        if "<" in v: return 5
        try: return int(v.replace(",", ""))
        except ValueError: return 0
    return 0

def analyze_keyword(keyword, keys):
    keyword = keyword.strip()
    if not keyword:
        return {"error": "빈 키워드"}
    
    try:
        r = requests.get(
            "https://api.naver.com/keywordstool",
            params={"hintKeywords": keyword.replace(" ", ""), "showDetail": "1"},
            headers=_ad_headers(keys, "GET", "/keywordstool"), timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 401:
            return {"keyword": keyword, "error": "검색광고 API 인증 실패 (401)"}
        elif code == 403:
            return {"keyword": keyword, "error": "검색광고 API 권한 거부 (403) - 비즈머니 잔액 확인"}
        return {"keyword": keyword, "error": f"검색광고 API 오류 ({code})"}
    except Exception as e:
        return {"keyword": keyword, "error": f"검색광고 API 오류: {e}"}
    
    if not data.get("keywordList"):
        return {"keyword": keyword, "error": "검색 결과 없음"}
    
    main = data["keywordList"][0]
    pc = _parse(main.get("monthlyPcQcCnt", 0))
    mo = _parse(main.get("monthlyMobileQcCnt", 0))
    total = pc + mo
    comp = main.get("compIdx", "정보없음")
    
    related = []
    for item in data["keywordList"][1:11]:
        related.append({
            "키워드": item.get("relKeyword", ""),
            "월간검색": _parse(item.get("monthlyPcQcCnt", 0)) + _parse(item.get("monthlyMobileQcCnt", 0)),
            "경쟁": item.get("compIdx", ""),
        })
    
    search_headers = {
        "X-Naver-Client-Id": keys["client_id"],
        "X-Naver-Client-Secret": keys["client_secret"],
    }
    counts = {}
    for section in ["blog", "cafearticle", "webkr"]:
        try:
            rr = requests.get(f"https://openapi.naver.com/v1/search/{section}.json",
                              headers=search_headers, params={"query": keyword, "display": 1}, timeout=10)
            rr.raise_for_status()
            counts[section] = rr.json().get("total", 0)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return {"keyword": keyword, "error": "검색 API 인증 실패"}
            counts[section] = 0
        except Exception:
            counts[section] = 0
    
    avg_days, recent_30d, fresh = 999, 0, 0
    try:
        rr = requests.get("https://openapi.naver.com/v1/search/blog.json",
                          headers=search_headers, params={"query": keyword, "display": 10, "sort": "sim"}, timeout=10)
        items = rr.json().get("items", [])
        days_list = []
        now = datetime.now()
        for it in items:
            pd_str = it.get("postdate", "")
            if len(pd_str) == 8:
                try:
                    diff = (now - datetime.strptime(pd_str, "%Y%m%d")).days
                    days_list.append(diff)
                    if diff <= 30: recent_30d += 1
                except ValueError: pass
        if days_list:
            avg_days = sum(days_list) / len(days_list)
            if avg_days <= 30: fresh = 1.0
            elif avg_days >= 365: fresh = 0.0
            else: fresh = max(0, 1 - (avg_days - 30) / 335)
    except Exception: pass
    
    blog_n = counts.get("blog", 0)
    if blog_n == 0: ratio_s = 1.0
    else:
        r_val = total / blog_n
        if r_val >= 1: ratio_s = 1.0
        elif r_val <= 0.001: ratio_s = 0.0
        else: ratio_s = max(0, min(1, (math.log10(r_val) + 3) / 3))
    
    comp_s = {"낮음": 1.0, "중간": 0.5, "높음": 0.2}.get(comp, 0.5)
    fresh_adj = 0.5 if fresh > 0.8 else (1 - fresh)
    mobile_ratio = mo / total if total > 0 else 0
    score = (ratio_s * 0.4 + comp_s * 0.25 + fresh_adj * 0.2 + mobile_ratio * 0.15) * 100
    
    if score >= 75: grade, emoji = "매우쉬움", "🟢"
    elif score >= 55: grade, emoji = "쉬움", "🟢"
    elif score >= 35: grade, emoji = "보통", "🟡"
    elif score >= 20: grade, emoji = "어려움", "🔴"
    else: grade, emoji = "매우어려움", "🔴"
    
    return {
        "keyword": keyword,
        "monthly_search": total, "monthly_pc": pc, "monthly_mobile": mo,
        "weekly_search": round(total / 4.345), "daily_search": round(total / 30.4),
        "mobile_ratio": mobile_ratio,
        "blog_count": counts.get("blog", 0), "cafe_count": counts.get("cafearticle", 0), "webkr_count": counts.get("webkr", 0),
        "competition": comp,
        "recent_30d": recent_30d,
        "avg_days": round(avg_days, 1) if avg_days < 999 else None,
        "exposure_score": round(score, 1),
        "difficulty": grade, "difficulty_emoji": emoji,
        "score_breakdown": {
            "수요/공급 비율": round(ratio_s, 3),
            "경쟁 강도": round(comp_s, 3),
            "최근성 기회": round(fresh_adj, 3),
            "모바일 우위": round(mobile_ratio, 3),
        },
        "related_keywords": related,
        "error": None,
    }


# ================================================
# blog_ai_writer 연결용 시드 텍스트 생성 (다리)
# ================================================
# blog_ai_writer의 자막칸(refText)은 100자 이상 텍스트를 받아야
# detectCategory/detectIntent가 작동한다. 분석 결과를 그 칸에 붙일
# 자연스러운 시드 문단으로 변환해준다. blog_ai_writer는 수정하지 않는다.

# 블로그별 카테고리 신호 단어 (detectCategory 적중률을 높이기 위한 힌트)
BLOG_PROFILES = {
    "ioneteam (IT 문제해결)": {
        "cat_hint": "스마트폰 갤럭시 아이폰 노트북 앱 설정 오류 해결 방법",
        "intent_hint": "방법 해결 설정 오류 사용법",
    },
    "reviewheart (육아·정책·리뷰)": {
        "cat_hint": "육아 아이 정책 지원금 신청 혜택 후기 추천",
        "intent_hint": "신청 후기 비교 추천 방법",
    },
    "(자동 감지)": {"cat_hint": "", "intent_hint": ""},
}

# ================================================
# 신규/기존 블로그별 키워드 합격 판정
# ================================================
# 기준 4개(블로그 문서 수·경쟁 강도·월간 검색량·노출 점수)를
# 블로그 상태에 따라 다르게 적용해 등급 + 이유를 돌려준다.
VERDICT_RULES = {
    "신규 블로그 (ioneteam 등)": {
        "doc_good": 10000, "doc_ok": 30000,      # 문서 수: 1만 미만 좋음 / 3만 미만 보통
        "search_low": 1000, "search_high": 30000, # 검색량: 1천~3만이 적당
    },
    "기존 블로그 (reviewheart 등)": {
        "doc_good": 30000, "doc_ok": 80000,
        "search_low": 1000, "search_high": 100000,
    },
}

# 블로그를 한 번만 고르면 판정기준(stage) + 시드 프로필이 함께 정해진다.
BLOG_CHOICES = {
    "ioneteam (IT · 신규)": {
        "stage": "신규 블로그 (ioneteam 등)",
        "profile": "ioneteam (IT 문제해결)",
    },
    "reviewheart (육아·정책 · 기존)": {
        "stage": "기존 블로그 (reviewheart 등)",
        "profile": "reviewheart (육아·정책·리뷰)",
    },
    "(기타 · 자동 감지)": {
        "stage": "신규 블로그 (ioneteam 등)",
        "profile": "(자동 감지)",
    },
}

def judge_keyword(result, blog_stage="신규 블로그 (ioneteam 등)"):
    """키워드가 해당 블로그 단계에 적합한지 등급 + 이유로 판정."""
    rule = VERDICT_RULES.get(blog_stage, VERDICT_RULES["신규 블로그 (ioneteam 등)"])
    doc = result.get("blog_count", 0) or 0
    comp = result.get("competition", "")
    search = result.get("monthly_search", 0) or 0
    score = result.get("exposure_score", 0) or 0

    reasons = []
    points = 0  # 합격 점수 (높을수록 좋음)

    # 1) 블로그 문서 수 (경쟁자 수) — 가장 중요
    if doc < rule["doc_good"]:
        points += 2; reasons.append(f"✅ 경쟁 글 {doc:,}개로 적음")
    elif doc < rule["doc_ok"]:
        points += 1; reasons.append(f"🟡 경쟁 글 {doc:,}개로 보통")
    else:
        points -= 1; reasons.append(f"🔴 경쟁 글 {doc:,}개로 많음 (이기기 어려움)")

    # 2) 경쟁 강도
    if comp == "낮음":
        points += 1; reasons.append("✅ 경쟁 강도 낮음")
    elif comp == "높음":
        points -= 1; reasons.append("🔴 경쟁 강도 높음")
    else:
        reasons.append("🟡 경쟁 강도 중간")

    # 3) 검색량 적정 구간
    if search < rule["search_low"]:
        reasons.append(f"🟡 검색량 {search:,}회로 적음 (수요 약함)")
    elif search <= rule["search_high"]:
        points += 1; reasons.append(f"✅ 검색량 {search:,}회로 적당")
    else:
        reasons.append(f"🟡 검색량 {search:,}회로 큼 (넓은 키워드, 경쟁↑)")

    # 4) 노출 점수 참고
    if score >= 55:
        points += 1; reasons.append(f"✅ 노출 점수 {score}점 (쉬움)")
    elif score < 35:
        points -= 1; reasons.append(f"🔴 노출 점수 {score}점 (어려움)")

    # 등급 결정
    if points >= 4:
        grade, emoji = "합격", "🟢"
    elif points >= 1:
        grade, emoji = "보통", "🟡"
    else:
        grade, emoji = "불합격", "🔴"

    return {"grade": grade, "emoji": emoji, "reasons": reasons, "points": points}


def build_seed_text(result, blog_profile="(자동 감지)"):
    kw = result.get("keyword", "")
    rel = result.get("related_keywords", []) or []
    rel_words = [r.get("키워드", "") for r in rel[:6] if r.get("키워드")]
    prof = BLOG_PROFILES.get(blog_profile, BLOG_PROFILES["(자동 감지)"])

    rel_str = ", ".join(rel_words) if rel_words else kw
    seed = (
        f"{kw}에 대해 검색하는 사람들이 많습니다. "
        f"{kw} 관련해서 함께 많이 찾는 키워드로는 {rel_str} 등이 있습니다. "
        f"이 글에서는 {kw}의 핵심 내용을 정리하고, "
        f"{prof['intent_hint']}을 중심으로 자세히 다룹니다. "
        f"{prof['cat_hint']}"
    ).strip()
    return seed


# ================================================
# 구글 트렌드
# ================================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_google_trends(keywords_list, timeframe="today 12-m", geo="KR"):
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return {"error": "pytrends 라이브러리가 설치되지 않았습니다"}
    
    try:
        pytrends = TrendReq(hl="ko-KR", tz=540, timeout=(10, 25), retries=2, backoff_factor=0.5)
        kws = keywords_list[:5]
        pytrends.build_payload(kws, cat=0, timeframe=timeframe, geo=geo, gprop="")
        
        result = {"keywords": kws, "error": None}
        
        try:
            iot = pytrends.interest_over_time()
            if not iot.empty:
                if "isPartial" in iot.columns:
                    iot = iot.drop(columns=["isPartial"])
                result["interest_over_time"] = iot
        except Exception as e:
            result["interest_over_time_error"] = str(e)
        
        try:
            ibr = pytrends.interest_by_region(resolution="REGION", inc_low_vol=True, inc_geo_code=False)
            if not ibr.empty:
                result["interest_by_region"] = ibr.sort_values(by=kws[0], ascending=False).head(10)
        except Exception as e:
            result["interest_by_region_error"] = str(e)
        
        try:
            related = pytrends.related_queries()
            if related and kws[0] in related:
                top = related[kws[0]].get("top")
                rising = related[kws[0]].get("rising")
                if top is not None and not top.empty:
                    result["related_top"] = top.head(10)
                if rising is not None and not rising.empty:
                    result["related_rising"] = rising.head(10)
        except Exception as e:
            result["related_error"] = str(e)
        
        return result
    except Exception as e:
        return {"error": f"구글 트렌드 조회 실패: {str(e)[:200]}"}


# ================================================
# 네이버 데이터랩 (신규)
# ================================================
def get_datalab_trend(keywords_groups, start_date, end_date, time_unit, 
                      keys, device="", ages=None, gender=""):
    """
    네이버 데이터랩 검색어 트렌드 조회
    keywords_groups: [{"groupName": "다이어트", "keywords": ["다이어트"]}, ...]
    """
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": keys["client_id"],
        "X-Naver-Client-Secret": keys["client_secret"],
        "Content-Type": "application/json",
    }
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": keywords_groups,
    }
    if device:
        body["device"] = device
    if ages:
        body["ages"] = ages
    if gender:
        body["gender"] = gender
    
    try:
        r = requests.post(url, headers=headers, json=body, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 401:
            return {"error": "인증 실패 - Client ID/Secret 확인"}
        elif code == 403:
            return {"error": "권한 없음 - developers.naver.com에서 '데이터랩(검색어 트렌드)' API 권한을 추가하세요"}
        else:
            return {"error": f"데이터랩 API 오류 ({code}): {e.response.text[:200]}"}
    except Exception as e:
        return {"error": f"데이터랩 API 오류: {str(e)[:200]}"}


def analyze_demographics(keyword, keys):
    """키워드의 연령대/성별/기기별 분석"""
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")  # 최근 3개월
    
    groups = [{"groupName": keyword, "keywords": [keyword]}]
    result = {"keyword": keyword}
    
    # 1) 시간별 추이
    base = get_datalab_trend(groups, start_date, end_date, "date", keys)
    if "error" in base:
        return {"error": base["error"]}
    result["time_trend"] = base
    
    # 2) 연령대별 (10대~60대+)
    age_results = {}
    age_groups = {
        "10대": ["2"], "20대": ["3", "4"], "30대": ["5", "6"],
        "40대": ["7", "8"], "50대": ["9", "10"], "60대+": ["11"]
    }
    for age_label, age_codes in age_groups.items():
        r = get_datalab_trend(groups, start_date, end_date, "month", keys, ages=age_codes)
        if "error" not in r and r.get("results"):
            # 평균값 계산
            data_points = r["results"][0].get("data", [])
            if data_points:
                avg = sum(d["ratio"] for d in data_points) / len(data_points)
                age_results[age_label] = round(avg, 2)
            else:
                age_results[age_label] = 0
        else:
            age_results[age_label] = 0
        time.sleep(0.2)  # rate limit 회피
    result["by_age"] = age_results
    
    # 3) 성별
    gender_results = {}
    for g_label, g_code in [("남성", "m"), ("여성", "f")]:
        r = get_datalab_trend(groups, start_date, end_date, "month", keys, gender=g_code)
        if "error" not in r and r.get("results"):
            data_points = r["results"][0].get("data", [])
            if data_points:
                avg = sum(d["ratio"] for d in data_points) / len(data_points)
                gender_results[g_label] = round(avg, 2)
            else:
                gender_results[g_label] = 0
        else:
            gender_results[g_label] = 0
        time.sleep(0.2)
    result["by_gender"] = gender_results
    
    # 4) 기기별
    device_results = {}
    for d_label, d_code in [("PC", "pc"), ("모바일", "mo")]:
        r = get_datalab_trend(groups, start_date, end_date, "month", keys, device=d_code)
        if "error" not in r and r.get("results"):
            data_points = r["results"][0].get("data", [])
            if data_points:
                avg = sum(d["ratio"] for d in data_points) / len(data_points)
                device_results[d_label] = round(avg, 2)
            else:
                device_results[d_label] = 0
        else:
            device_results[d_label] = 0
        time.sleep(0.2)
    result["by_device"] = device_results
    
    return result


# ================================================
# 메인 대시보드용 카테고리별 키워드 풀
# ================================================
# blog_ai_writer 카테고리(CAT-A~L)와 일치. 각 카드의 '갱신' 버튼을 누르면
# 해당 풀의 키워드 추세를 데이터랩으로 훑어 급상승만 보여준다.
CATEGORY_POOLS = {
    "CAT-A · IT·컴퓨터·스마트폰": [
        "아이폰", "갤럭시", "갤럭시S26", "노트북", "윈도우", "맥북", "에어팟", "갤럭시워치",
        "아이패드", "태블릿", "무선이어폰", "모니터", "그래픽카드", "SSD", "공유기",
        "블루투스", "USB", "충전기", "키보드", "웹캠",
    ],
    "CAT-AB · IT + 경제·재테크": [
        "스마트폰 보조금", "통신비 절약", "알뜰폰", "휴대폰 성지", "자급제폰",
        "데이터 무제한", "인터넷 가입", "결합할인", "중고폰 시세", "리퍼폰",
    ],
    "CAT-B · 경제·재테크·절약": [
        "주식", "ETF", "배당주", "적금", "예금금리", "연금저축", "ISA", "청약통장",
        "환율", "금값", "비트코인", "퇴직연금", "절세", "신용점수", "대출금리",
    ],
    "CAT-C · 정보·생활정보·꿀팁": [
        "전기요금", "도시가스", "주민등록등본", "민원24", "정부24", "국세청 환급",
        "자동차세", "재산세", "건강보험료", "실업급여", "전입신고", "공동인증서",
        "여권 발급", "운전면허 갱신", "쓰레기 종량제",
    ],
    "CAT-D · 육아·교육": [
        "이유식", "어린이집", "유치원", "분유", "기저귀", "아기 수면교육",
        "돌잔치", "유아 영어", "학습지", "초등 입학", "받아쓰기", "구구단",
        "어린이 영양제", "예방접종", "아기 발달",
    ],
    "CAT-E · 건강·운동·다이어트": [
        "다이어트", "홈트레이닝", "단백질", "유산소", "헬스", "필라테스",
        "간헐적단식", "혈압", "콜레스테롤", "영양제", "비타민", "단식",
        "스트레칭", "체지방", "근력운동",
    ],
    "CAT-F · 뷰티·패션": [
        "선크림", "쿠션", "립밤", "여름 코디", "원피스", "운동화",
        "향수", "탈모 샴푸", "헤어스타일", "네일", "다운펌", "기초화장품",
    ],
    "CAT-G · 여행·맛집": [
        "제주도 여행", "강릉 여행", "부산 맛집", "캠핑", "글램핑", "호캉스",
        "당일치기", "국내여행", "여름 휴가지", "물놀이", "계곡", "워터파크",
        "드라이브 코스", "펜션", "야경 명소",
    ],
    "CAT-H · 일상·감성·에세이": [
        "오늘의 날씨", "주말 나들이", "취미", "독서", "홈카페", "반신욕",
        "미니멀라이프", "정리수납", "플랜테리어", "캘리그라피",
    ],
    "CAT-I · 문화·예술·영화·음악": [
        "넷플릭스 추천", "드라마 추천", "영화 추천", "OTT", "디즈니플러스",
        "웹툰", "전시회", "콘서트", "뮤지컬", "신곡",
    ],
    "CAT-S · 스포츠·경기·선수": [
        "손흥민", "이강인", "KBO", "프리미어리그", "챔피언스리그", "월드컵",
        "야구 순위", "축구 중계", "골프", "마라톤", "올림픽", "MLB",
    ],
    "CAT-J · 반려동물·펫": [
        "강아지 사료", "고양이 사료", "강아지 훈련", "반려동물 보험", "펫호텔",
        "강아지 예방접종", "고양이 화장실", "반려견 등록", "강아지 미용", "펫푸드",
    ],
    "CAT-K · AI·자동화·툴": [
        "챗GPT", "구글 제미나이", "AI 그림", "프롬프트", "AI 영상", "노션",
        "엑셀 함수", "구글 스프레드시트", "캔바", "미드저니", "클로드", "AI 글쓰기",
    ],
    "CAT-L · 부동산·청약·투자": [
        "아파트 청약", "전세 대출", "주택담보대출", "분양", "재건축", "부동산 세금",
        "전월세 신고", "임대차", "디딤돌대출", "보금자리론", "신생아 특례", "오피스텔",
    ],
}


def scan_category_trends(pool, keys, top_n=8):
    """
    카테고리 풀의 키워드들을 데이터랩으로 훑어 급상승 순으로 정렬.
    반환: [{"키워드","change_pct","recent_avg"}, ...] 상승률 높은 순.
    """
    results = []
    for kw in pool:
        try:
            d = get_trend_direction(kw, keys)
            if d:
                results.append({
                    "키워드": kw,
                    "change_pct": d["change_pct"],
                    "recent_avg": d["recent_avg"],
                })
        except Exception:
            pass
        time.sleep(0.15)
    # 상승률 높은 순
    results.sort(key=lambda x: x["change_pct"], reverse=True)
    return results[:top_n]


# ================================================
# 메인 대시보드용 카테고리별 뉴스 검색어
# ================================================
# blog_ai_writer 카테고리(CAT-A~L)와 일치. 각 카테고리의 뉴스 검색어로
# 네이버 뉴스 API를 호출해 최신 이슈 제목을 카드에 띄운다.
CATEGORY_NEWS_QUERIES = {
    # ── ioneteam (IT) : 신제품 + 활용·기능 둘 다 ──
    "CAT-A · IT·스마트폰 (ioneteam)": [
        "스마트폰 신제품", "갤럭시 기능", "아이폰 업데이트", "스마트폰 활용", "앱 추천",
    ],
    # ── reviewheart : 두 딸(유치원·초2) 아빠 컨셉 3개 카드 ──
    "CAT-D1 · 육아·교육 (reviewheart)": [
        "초등 저학년", "유치원", "받아쓰기", "어린이 영어", "학습지", "초등 입학",
    ],
    "CAT-D2 · 자녀 혜택·정책 (reviewheart)": [
        "아동수당", "자녀장려금", "교육급여", "아이행복카드", "초등 입학지원금", "다자녀 혜택",
    ],
    "CAT-D3 · 아이와 생활 (reviewheart)": [
        "아이랑 가볼만한곳", "키즈카페", "초등 준비물", "어린이 영양제", "가족 나들이", "어린이 안전",
    ],
    # ── 그 외 카테고리 (필요시 사용) ──
    "CAT-B · 경제·재테크·절약": ["재테크", "금리", "주식"],
    "CAT-C · 정보·생활정보·꿀팁": ["생활꿀팁", "정부지원금", "생활정보"],
    "CAT-E · 건강·운동·다이어트": ["건강", "다이어트", "운동"],
    "CAT-F · 뷰티·패션": ["패션", "뷰티", "화장품"],
    "CAT-G · 여행·맛집": ["여행", "맛집", "국내여행"],
    "CAT-H · 일상·감성·에세이": ["라이프스타일", "취미", "트렌드"],
    "CAT-I · 문화·예술·영화·음악": ["영화", "드라마", "넷플릭스"],
    "CAT-S · 스포츠·경기·선수": ["스포츠", "축구", "야구"],
    "CAT-J · 반려동물·펫": ["반려동물", "강아지", "고양이"],
    "CAT-K · AI·자동화·툴": ["인공지능", "챗GPT", "AI"],
    "CAT-L · 부동산·청약·투자": ["부동산", "청약", "아파트"],
}


def _strip_tags(text):
    """뉴스 제목의 <b> 태그, HTML 엔티티 제거"""
    import re, html
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def search_news(query, keys, display=10, sort="date"):
    """
    네이버 뉴스 검색 API. 키워드로 최신 뉴스 제목·링크를 가져온다.
    sort='date' 최신순, 'sim' 정확도순.
    반환: [{"title","link","pubDate"}, ...]
    """
    try:
        r = requests.get(
            "https://openapi.naver.com/v1/search/news.json",
            params={"query": query, "display": display, "sort": sort},
            headers={
                "X-Naver-Client-Id": keys["client_id"],
                "X-Naver-Client-Secret": keys["client_secret"],
            },
            timeout=10,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        out = []
        seen = set()
        for it in items:
            title = _strip_tags(it.get("title", ""))
            if title and title not in seen:
                seen.add(title)
                out.append({
                    "title": title,
                    "link": it.get("originallink") or it.get("link", ""),
                    "pubDate": it.get("pubDate", ""),
                })
        return {"error": None, "news": out}
    except Exception as e:
        return {"error": f"뉴스 API 오류: {str(e)[:120]}", "news": []}


def fetch_category_news(category, keys, per_query=6):
    """카테고리의 검색어들로 뉴스를 모아 중복 제거 후 반환."""
    queries = CATEGORY_NEWS_QUERIES.get(category, [])
    all_news = []
    seen = set()
    for q in queries:
        res = search_news(q, keys, display=per_query, sort="date")
        if res["error"]:
            continue
        for n in res["news"]:
            if n["title"] not in seen:
                seen.add(n["title"])
                all_news.append(n)
        time.sleep(0.15)
    return all_news


# ================================================
# 세부 키워드(롱테일) 수집 - 네이버 자동완성
# ================================================
# 검색창 자동완성에서 "씨앗 + 뒤에 붙는 말"을 수집한다.
# 비공식 엔드포인트라 막힐 수 있어, 실패 시 호출부에서 공식 연관어로 폴백한다.
def get_autocomplete_keywords(seed):
    seed = seed.strip()
    if not seed:
        return {"error": "빈 키워드", "keywords": []}
    try:
        r = requests.get(
            "https://ac.search.naver.com/nx/ac",
            params={"q": seed, "con": "1", "frm": "nv", "ans": "2",
                    "r_format": "json", "st": "100"},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.naver.com/"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"error": f"자동완성 접근 실패: {str(e)[:120]}", "keywords": []}

    words = []
    for grp in data.get("items", []):
        if not isinstance(grp, list):
            continue
        for it in grp:
            if isinstance(it, list) and it and it[0]:
                w = it[0].strip()
                if w and w not in words:
                    words.append(w)
    if not words:
        return {"error": "자동완성 결과 없음", "keywords": []}
    return {"error": None, "keywords": words}


def collect_sub_keywords(seed, keys, limit=20):
    """
    세부 키워드 수집. 자동완성 우선, 실패하면 공식 키워드도구 연관어로 폴백.
    반환: {"source": "자동완성"|"공식 연관어", "keywords": [...], "error": None|str}
    """
    ac = get_autocomplete_keywords(seed)
    if not ac["error"] and ac["keywords"]:
        # 씨앗을 포함하는 세부 키워드 우선 (롱테일)
        kws = ac["keywords"][:limit]
        return {"source": "자동완성", "keywords": kws, "error": None}

    # 폴백: 공식 키워드도구 연관어
    rel = get_related_keywords_list(seed, keys, limit=limit)
    if rel.get("error"):
        return {"source": None, "keywords": [],
                "error": f"자동완성·공식 모두 실패 ({rel['error']})"}
    kws = [k["키워드"] for k in rel["keywords"] if k.get("키워드")]
    return {"source": "공식 연관어(폴백)", "keywords": kws, "error": None}


# ================================================
# 트렌드 발굴 (신규) - 내 분야에서 뜨는 연관 키워드 찾기
# ================================================
def get_related_keywords_list(seed_keyword, keys, limit=20):
    """검색광고 API로 연관 키워드 목록 + 월간검색량 수집"""
    try:
        r = requests.get(
            "https://api.naver.com/keywordstool",
            params={"hintKeywords": seed_keyword.replace(" ", ""), "showDetail": "1"},
            headers=_ad_headers(keys, "GET", "/keywordstool"), timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 403:
            return {"error": "검색광고 API 권한 거부 (403) - 비즈머니 잔액 확인"}
        return {"error": f"검색광고 API 오류 ({code})"}
    except Exception as e:
        return {"error": f"검색광고 API 오류: {str(e)[:150]}"}

    if not data.get("keywordList"):
        return {"error": "연관 키워드를 찾을 수 없습니다"}

    kws = []
    for item in data["keywordList"][:limit]:
        total = _parse(item.get("monthlyPcQcCnt", 0)) + _parse(item.get("monthlyMobileQcCnt", 0))
        kws.append({
            "키워드": item.get("relKeyword", ""),
            "월간검색": total,
            "경쟁": item.get("compIdx", ""),
        })
    return {"keywords": kws, "error": None}


def _relevance_score(seed, kw):
    """씨앗과 연관어의 관련도 점수. 높을수록 관련 높음."""
    seed_clean = seed.replace(" ", "")
    kw_clean = kw.replace(" ", "")
    # 1) 씨앗 단어를 통째로 포함하면 가장 높은 점수
    if seed_clean and seed_clean in kw_clean:
        return 100 + len(seed_clean)
    # 2) 씨앗의 글자가 얼마나 겹치는지 (부분 관련)
    overlap = sum(1 for ch in set(seed_clean) if ch in kw_clean)
    return overlap


def filter_related_keywords(seed, keywords, strict=True):
    """
    strict=True  : 씨앗 단어를 포함하는 연관어만 남김 (옵션 1)
    strict=False : 안 자르고 관련도 순으로 정렬, 관련 낮은 건 표시 (옵션 2)
    """
    scored = []
    for kw_info in keywords:
        kw = kw_info.get("키워드", "")
        score = _relevance_score(seed, kw)
        item = dict(kw_info)
        item["_rel"] = score
        item["관련"] = "관련" if score >= 100 else "관련낮음"
        scored.append(item)

    if strict:
        kept = [x for x in scored if x["_rel"] >= 100]
        # 너무 적게 남으면(2개 미만) 안전하게 관련도 상위로 보강
        if len(kept) < 2:
            kept = sorted(scored, key=lambda x: x["_rel"], reverse=True)[:max(2, len(scored)//2)]
        return kept
    else:
        return sorted(scored, key=lambda x: x["_rel"], reverse=True)


def get_trend_direction(keyword, keys):
    """
    데이터랩으로 키워드의 트렌드 방향 분석.
    최근 3개월을 전반부/후반부로 나눠 비교 → 상승/하락률 계산.
    """
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")

    groups = [{"groupName": keyword, "keywords": [keyword]}]
    res = get_datalab_trend(groups, start_date, end_date, "week", keys)

    if "error" in res or not res.get("results"):
        return None

    data_points = res["results"][0].get("data", [])
    if len(data_points) < 4:
        return None

    ratios = [d["ratio"] for d in data_points]
    half = len(ratios) // 2
    first_half = ratios[:half]
    second_half = ratios[half:]

    avg_first = sum(first_half) / len(first_half) if first_half else 0
    avg_second = sum(second_half) / len(second_half) if second_half else 0

    if avg_first == 0:
        change_pct = 100 if avg_second > 0 else 0
    else:
        change_pct = round((avg_second - avg_first) / avg_first * 100, 1)

    return {
        "change_pct": change_pct,
        "recent_avg": round(avg_second, 1),
    }


# ================================================
# AI 키워드 자동수집 (클로드 / 제미나이)
# ================================================
def _build_ai_keyword_prompt(category_label, n=12):
    return f"""당신은 네이버 블로그 SEO 키워드 발굴 전문가입니다.
'{category_label}' 분야에서 지금(2026년 6월) 한국 네이버 블로그에 쓰면 좋을 키워드를 {n}개 발굴하세요.

[중요] 가능하면 web_search로 현재 트렌드를 실제 확인하고 뽑으세요. 기억으로만 채우지 마세요.

[가장 중요한 규칙 — 키워드 길이]
- longtail은 반드시 사람이 네이버 검색창에 실제로 치는 **2~4단어, 15자 이내**의 짧은 검색어여야 합니다.
- 문장처럼 길게 쓰지 마세요. 네이버는 긴 문장의 검색량을 집계하지 않아 측정이 불가능합니다.
- 연도(2026), 조사(이/가/을/를), 서술어(~방법/~안내/~여부/~총정리), 수식어를 빼고 핵심 명사만 남기세요.

  나쁜 예(문장형, 측정 불가):
   "2026 여름방학 초등 돌봄교실 신청 방법" / "부모급여 어린이집 다니면 얼마"
  좋은 예(2~4단어, 검색량 잡힘):
   "초등 돌봄교실 신청" / "부모급여 어린이집" / "아동수당 소득기준" / "육아휴직 급여 인상"

[그 외 규칙]
- big에는 경쟁 센 대표 키워드, longtail에는 위 규칙대로 다듬은 짧은 공략 키워드.
- 기간 구분(period)은 '월간'(시즌·정책) / '주간'(상승 트렌드) / '전일'(실시간 시사) 중 하나.

[출력 형식] 아래 JSON만 출력하세요. 설명·마크다운·코드펜스 금지.
{{"keywords":[{{"period":"월간","big":"빅키워드","longtail":"2~4단어 짧은 키워드","tip":"포스팅 작성 팁 한 줄"}}]}}
"""


def _extract_json(text):
    """모델 응답에서 JSON 블록만 안전하게 추출"""
    if not text:
        return None
    t = text.strip()
    # 코드펜스 제거
    t = t.replace("```json", "").replace("```", "").strip()
    # 첫 { 부터 마지막 } 까지
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(t[start:end + 1])
    except Exception:
        return None


def generate_keywords_gemini(category_label, api_key, n=12):
    prompt = _build_ai_keyword_prompt(category_label, n)
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
            headers={"content-type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        text = ""
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                text += part.get("text", "")
        parsed = _extract_json(text)
        if not parsed or "keywords" not in parsed:
            return {"error": "응답 파싱 실패", "raw": text[:300]}
        return {"keywords": parsed["keywords"]}
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        try:
            body = e.response.json()
            detail = body.get("error", {}).get("message", "") or str(body)[:200]
        except Exception:
            detail = e.response.text[:200]
        return {"error": f"Gemini API 오류 ({code}): {detail}"}
    except Exception as e:
        return {"error": f"Gemini 호출 오류: {e}"}


def measure_ai_keywords(kw_list, keys):
    """AI가 뽑은 키워드 리스트를 네이버 실측에 투입 → DataFrame용 rows 반환"""
    rows = []
    for item in kw_list:
        longtail = (item.get("longtail") or item.get("big") or "").strip()
        if not longtail:
            continue
        res = analyze_keyword(longtail, keys)
        if res.get("error"):
            rows.append({
                "기간": item.get("period", ""),
                "추천 롱테일": longtail,
                "월간검색": "-",
                "블로그문서": "-",
                "난이도": res.get("error", "오류"),
                "작성 팁": item.get("tip", ""),
            })
        else:
            rows.append({
                "기간": item.get("period", ""),
                "추천 롱테일": longtail,
                "월간검색": res.get("monthly_search", 0),
                "블로그문서": res.get("blog_count", 0),
                "난이도": f"{res.get('difficulty_emoji','')} {res.get('difficulty','')}",
                "작성 팁": item.get("tip", ""),
            })
    return rows


# ================================================
# 메인 영역 - 탭 5개
# ================================================
tab_home, tab5, tab6, tab1, tab2, tab3, tab4, tab_cal, tab_ai = st.tabs([
    "🏠 홈 · 뭐 쓸지 둘러보기", "🔥 글감 찾기 · 뭐가 뜨나", "🪓 세부 글감 파기",
    "🎯 키워드 검증 · 쓸까 말까", "📋 여러 개 한번에 검증",
    "📈 구글 트렌드 비교", "📊 누가 검색하나 (연령·성별)",
    "🗓️ 소재캘린더 · 이번 주 뭐 쓰지",
    "🤖 AI 키워드 (모델별)"
])

# ============ 탭: 트렌드 대시보드 (메인) ============
with tab_home:
    if not st.session_state.api_configured:
        st.warning("👈 왼쪽 사이드바에서 네이버 API 키를 먼저 입력해주세요")
    else:
        st.info("""🏠 카테고리별 **지금 뜨는 뉴스·이슈**를 보여줍니다. 카드에서 마음에 드는 이슈를 보면,  
        그 키워드를 '🎯 키워드 검증'이나 '🪓 세부 글감 파기' 탭에 넣어 글감으로 발전시키세요.  
　🟢 네이버 데이터 (검색 API · 뉴스)""")

        if "news_cache" not in st.session_state:
            st.session_state["news_cache"] = {}

        cat_names = list(CATEGORY_NEWS_QUERIES.keys())
        chosen = st.multiselect(
            "볼 카테고리 선택 (2~3개 추천)",
            cat_names,
            default=cat_names[:1],
            key="news_chosen",
        )

        if st.button("🔄 선택한 카테고리 뉴스 가져오기", type="primary", use_container_width=True, key="news_refresh"):
            if not chosen:
                st.warning("카테고리를 하나 이상 선택해주세요")
            else:
                prog = st.progress(0)
                status = st.empty()
                for i, cat in enumerate(chosen):
                    status.text(f"뉴스 가져오는 중 ({i+1}/{len(chosen)}): {cat}")
                    news = fetch_category_news(cat, st.session_state.api_keys, per_query=6)
                    st.session_state["news_cache"][cat] = news
                    prog.progress((i + 1) / len(chosen))
                status.empty(); prog.empty()

        # 선택한 카테고리: 한 줄에 2개씩, 각 카드 안에서 뉴스를 다시 2칸으로
        if chosen:
            def render_news_card(cat):
                news = st.session_state["news_cache"].get(cat)
                count = len(news) if news else 0
                st.markdown(f"**{cat}**  ·  {count}건")
                if news is None:
                    st.caption("위 버튼을 누르면 이 분야 최신 뉴스가 표시됩니다")
                elif not news:
                    st.caption("가져온 뉴스가 없습니다")
                else:
                    show = news[:20]
                    half = (len(show) + 1) // 2
                    left, right = show[:half], show[half:]
                    cL, cR = st.columns(2)
                    for col, items, start in ((cL, left, 1), (cR, right, half + 1)):
                        with col:
                            for idx, n in enumerate(items, start=start):
                                if n["link"]:
                                    st.markdown(f"{idx}. [{n['title']}]({n['link']})")
                                else:
                                    st.write(f"{idx}. {n['title']}")
                    st.caption("💡 쓸 이슈의 키워드를 '🎯 키워드 검증'·'🪓 세부 글감 파기'에")

            for row_start in range(0, len(chosen), 2):
                pair = chosen[row_start:row_start + 2]
                cols = st.columns(2)
                for ci, cat in enumerate(pair):
                    with cols[ci]:
                        with st.container(border=True):
                            render_news_card(cat)

# ============ 탭1: 네이버 단일 ============
with tab1:
    if not st.session_state.api_configured:
        st.warning("👈 왼쪽 사이드바에서 네이버 API 키를 먼저 입력해주세요")
    else:
        st.info("🎯 **쓸 키워드를 이미 정했을 때** — 이 키워드로 글 쓰면 노출될지, 검색량·경쟁·문서수를 종합해 판정합니다.  \n　🟢 네이버 데이터 (검색 API + 검색광고 API)")

        blog_pick = st.radio(
            "① 어느 블로그에 쓸 글인가요?",
            list(BLOG_CHOICES.keys()),
            horizontal=True,
            key="unified_blog_pick",
        )
        cfg = BLOG_CHOICES[blog_pick]

        keyword = st.text_input("② 분석할 키워드", placeholder="예: 다이어트", key="single_kw")
        
        if st.button("🔍 분석 시작", type="primary", use_container_width=True, key="single_btn"):
            if not keyword.strip():
                st.error("키워드를 입력해주세요")
            else:
                with st.spinner(f"'{keyword}' 분석 중..."):
                    result = analyze_keyword(keyword, st.session_state.api_keys)
                
                if result.get("error"):
                    st.error(f"❌ {result['error']}")
                else:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("월간 검색량", f"{result['monthly_search']:,}")
                    c2.metric("주간 검색량", f"{result['weekly_search']:,}")
                    c3.metric("일간 검색량", f"{result['daily_search']:,}")
                    c4.metric("노출 확률", f"{result['exposure_score']}점", f"{result['difficulty_emoji']} {result['difficulty']}")
                    
                    st.markdown("---")
                    col_L, col_R = st.columns(2)
                    with col_L:
                        st.subheader("📊 검색량 상세")
                        st.write(f"- **PC 월간**: {result['monthly_pc']:,}회")
                        st.write(f"- **모바일 월간**: {result['monthly_mobile']:,}회")
                        st.write(f"- **모바일 비율**: {result['mobile_ratio']*100:.1f}%")
                        st.write(f"- **경쟁 강도**: {result['competition']}")
                        st.subheader("📄 문서 수")
                        st.write(f"- **블로그**: {result['blog_count']:,}개")
                        st.write(f"- **카페**: {result['cafe_count']:,}개")
                        st.write(f"- **웹문서**: {result['webkr_count']:,}개")
                        st.subheader("🕒 최근성")
                        st.write(f"- **최근 30일 내 글**: {result['recent_30d']}개")
                        if result['avg_days'] is not None:
                            st.write(f"- **상위 글 평균 경과일**: {result['avg_days']}일")
                    with col_R:
                        st.subheader("🎯 노출 확률 세부 점수")
                        bdf = pd.DataFrame({
                            "지표": list(result["score_breakdown"].keys()),
                            "점수": list(result["score_breakdown"].values()),
                            "가중치": ["40%", "25%", "20%", "15%"],
                        })
                        st.dataframe(bdf, hide_index=True, use_container_width=True)
                        st.caption(f"종합: {result['exposure_score']}점 / 100점")
                    
                    if result.get("related_keywords"):
                        st.markdown("---")
                        st.subheader("🔗 연관 키워드 TOP 10")
                        rdf = pd.DataFrame(result["related_keywords"])
                        rdf["월간검색"] = rdf["월간검색"].apply(lambda x: f"{x:,}")
                        st.dataframe(rdf, hide_index=True, use_container_width=True)

                    # 분석 결과를 세션에 저장 (다리 블록이 재실행돼도 유지)
                    st.session_state["last_result"] = result

        # ===== 다리: blog_ai_writer 연결 =====
        if st.session_state.get("last_result"):
            lr = st.session_state["last_result"]
            st.markdown("---")
            st.subheader(f"🎯 이 키워드, '{blog_pick}'에 쓸까?")
            verdict = judge_keyword(lr, cfg["stage"])
            if verdict["grade"] == "합격":
                st.success(f"{verdict['emoji']} **{verdict['grade']}** — 이 블로그에 쓰기 좋은 키워드예요")
            elif verdict["grade"] == "보통":
                st.warning(f"{verdict['emoji']} **{verdict['grade']}** — 써도 되지만 더 좋은 키워드가 있을 수 있어요")
            else:
                st.error(f"{verdict['emoji']} **{verdict['grade']}** — 이 블로그엔 추천하지 않아요 (더 구체적인 키워드로)")
            for r in verdict["reasons"]:
                st.write(f"- {r}")

            st.markdown("---")
            st.subheader("✍️ blog_ai_writer로 보내기")
            st.caption(
                f"'{lr['keyword']}' 분석 결과를 blog_ai_writer 자막칸에 붙일 텍스트로 만듭니다. "
                "복사 → blog_ai_writer 자막칸에 붙여넣으면 키워드·카테고리·검색의도가 자동 설정됩니다."
            )
            seed_text = build_seed_text(lr, cfg["profile"])
            st.text_area("📋 복사할 텍스트 (아래 내용을 자막칸에 붙여넣기)", seed_text, height=140)
            st.caption("💡 blog_ai_writer에서 카테고리·의도가 다르게 잡히면 그 칸만 직접 바꾸면 됩니다.")

# ============ 탭2: 네이버 일괄 ============
with tab2:
    if not st.session_state.api_configured:
        st.warning("👈 왼쪽 사이드바에서 네이버 API 키를 먼저 입력해주세요")
    else:
        st.info("📋 **후보 키워드가 여러 개일 때** — 한 줄에 하나씩 넣으면 한꺼번에 판정해 비교해줍니다.  \n　🟢 네이버 데이터 (검색 API + 검색광고 API)")
        keywords_text = st.text_area("키워드들 (한 줄에 하나씩)", placeholder="다이어트\n홈트레이닝\n간헐적단식", height=150)
        if st.button("🔍 일괄 분석", type="primary", use_container_width=True, key="bulk_btn"):
            keywords = [k.strip() for k in keywords_text.split("\n") if k.strip()]
            if not keywords:
                st.error("키워드를 입력해주세요")
            else:
                progress = st.progress(0); status = st.empty()
                results = []
                for i, kw in enumerate(keywords):
                    status.text(f"분석 중 ({i+1}/{len(keywords)}): {kw}")
                    results.append(analyze_keyword(kw, st.session_state.api_keys))
                    progress.progress((i + 1) / len(keywords))
                    time.sleep(0.3)
                status.empty(); progress.empty()
                
                df_data = []
                for r in results:
                    if r.get("error"):
                        df_data.append({"키워드": r.get("keyword", "?"), "에러": r["error"]})
                    else:
                        df_data.append({
                            "키워드": r["keyword"], "월간검색": r["monthly_search"],
                            "주간검색": r["weekly_search"], "일간검색": r["daily_search"],
                            "블로그수": r["blog_count"], "경쟁": r["competition"],
                            "모바일%": f"{r['mobile_ratio']*100:.0f}%",
                            "노출점수": r["exposure_score"],
                            "난이도": f"{r['difficulty_emoji']} {r['difficulty']}",
                        })
                df = pd.DataFrame(df_data)
                st.success(f"✅ {len(results)}개 분석 완료")
                st.dataframe(df, hide_index=True, use_container_width=True)
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("📥 CSV 다운로드", csv,
                    file_name=f"keyword_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv", use_container_width=True)

# ============ 탭3: 구글 트렌드 ============
with tab3:
    st.info("💡 구글 트렌드는 API 키가 필요 없습니다. 최대 5개 키워드 비교 가능.  \n　🔵 구글 데이터 (Google Trends)")
    
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        trend_keywords = st.text_input("키워드 (쉼표로 구분, 최대 5개)",
                                       placeholder="예: 다이어트, 홈트레이닝, 간헐적단식", key="trend_kw")
    with col_b:
        timeframe_label = st.selectbox("기간",
            ["지난 7일", "지난 1개월", "지난 3개월", "지난 12개월", "지난 5년"],
            index=3, key="trend_tf")
        timeframe_map = {
            "지난 7일": "now 7-d", "지난 1개월": "today 1-m",
            "지난 3개월": "today 3-m", "지난 12개월": "today 12-m",
            "지난 5년": "today 5-y",
        }
    with col_c:
        geo = st.selectbox("국가", ["한국", "전세계", "미국", "일본"], index=0, key="trend_geo")
        geo_map = {"한국": "KR", "전세계": "", "미국": "US", "일본": "JP"}
    
    if st.button("📈 트렌드 분석", type="primary", use_container_width=True, key="trend_btn"):
        kws = [k.strip() for k in trend_keywords.split(",") if k.strip()]
        if not kws:
            st.error("키워드를 입력해주세요")
        elif len(kws) > 5:
            st.error("최대 5개까지만 입력 가능합니다")
        else:
            with st.spinner(f"구글 트렌드 조회 중..."):
                result = get_google_trends(kws, timeframe_map[timeframe_label], geo_map[geo])
            
            if result.get("error"):
                st.error(f"❌ {result['error']}")
                st.caption("⚠️ 구글이 일시적으로 차단했을 수 있어요. 1~2분 후 재시도")
            else:
                st.success(f"✅ '{', '.join(result['keywords'])}' 분석 완료")
                
                if "interest_over_time" in result:
                    st.subheader("📈 시간별 관심도 (0~100)")
                    st.line_chart(result["interest_over_time"], height=300)
                    iot = result["interest_over_time"]
                    summary_data = []
                    for kw in result["keywords"]:
                        if kw in iot.columns:
                            summary_data.append({
                                "키워드": kw, "평균": round(iot[kw].mean(), 1),
                                "최댓값": int(iot[kw].max()), "최솟값": int(iot[kw].min()),
                                "현재": int(iot[kw].iloc[-1]) if len(iot) > 0 else 0,
                            })
                    if summary_data:
                        st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)
                
                if "interest_by_region" in result:
                    st.markdown("---")
                    st.subheader("🌏 지역별 관심도 TOP 10")
                    st.bar_chart(result["interest_by_region"], height=300)
                
                col_top, col_rise = st.columns(2)
                with col_top:
                    if "related_top" in result:
                        st.subheader(f"🔝 '{result['keywords'][0]}' 인기 연관어")
                        st.dataframe(result["related_top"], hide_index=True, use_container_width=True)
                with col_rise:
                    if "related_rising" in result:
                        st.subheader(f"🚀 '{result['keywords'][0]}' 급상승 연관어")
                        st.dataframe(result["related_rising"], hide_index=True, use_container_width=True)

# ============ 탭4: 네이버 데이터랩 (신규) ============
with tab4:
    if not st.session_state.api_configured:
        st.warning("👈 왼쪽 사이드바에서 네이버 API 키를 먼저 입력해주세요")
    else:
        st.info("""📊 **타겟 독자를 확인할 때** — 키워드를 검색하는 사람들의 **연령/성별/기기** 비율을 분석합니다.  
        ⚠️ 이 기능은 developers.naver.com에서 **'데이터랩(검색어 트렌드)' API 권한**이 추가되어 있어야 동작합니다.  
　🟢 네이버 데이터 (데이터랩)""")
        
        dl_keyword = st.text_input("분석할 키워드", placeholder="예: 다이어트", key="dl_kw")
        
        if st.button("📊 데이터랩 분석", type="primary", use_container_width=True, key="dl_btn"):
            if not dl_keyword.strip():
                st.error("키워드를 입력해주세요")
            else:
                with st.spinner("데이터랩 조회 중... (10~20초)"):
                    result = analyze_demographics(dl_keyword, st.session_state.api_keys)
                
                if result.get("error"):
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ '{dl_keyword}' 인구통계 분석 완료 (최근 3개월 기준)")
                    
                    # 1) 시간별 추이
                    if "time_trend" in result and result["time_trend"].get("results"):
                        st.subheader("📈 일별 검색 추이")
                        data_points = result["time_trend"]["results"][0].get("data", [])
                        if data_points:
                            trend_df = pd.DataFrame(data_points)
                            trend_df["period"] = pd.to_datetime(trend_df["period"])
                            trend_df = trend_df.set_index("period")
                            trend_df.columns = [dl_keyword]
                            st.line_chart(trend_df, height=250)
                    
                    st.markdown("---")
                    
                    # 2) 연령대별
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.subheader("👥 연령대별 관심도")
                        if result.get("by_age"):
                            age_df = pd.DataFrame({
                                "연령대": list(result["by_age"].keys()),
                                "평균 관심도": list(result["by_age"].values()),
                            })
                            st.bar_chart(age_df.set_index("연령대"), height=250)
                            
                            # TOP 연령대 찾기
                            top_age = max(result["by_age"], key=result["by_age"].get)
                            st.caption(f"🎯 가장 많이 검색하는 연령대: **{top_age}**")
                    
                    # 3) 성별
                    with col_b:
                        st.subheader("⚧ 성별 관심도")
                        if result.get("by_gender"):
                            g_df = pd.DataFrame({
                                "성별": list(result["by_gender"].keys()),
                                "평균 관심도": list(result["by_gender"].values()),
                            })
                            st.bar_chart(g_df.set_index("성별"), height=250)
                            top_g = max(result["by_gender"], key=result["by_gender"].get)
                            st.caption(f"🎯 더 많이 검색: **{top_g}**")
                    
                    # 4) 기기별
                    st.markdown("---")
                    st.subheader("📱 기기별 관심도")
                    if result.get("by_device"):
                        d_df = pd.DataFrame({
                            "기기": list(result["by_device"].keys()),
                            "평균 관심도": list(result["by_device"].values()),
                        })
                        col_d1, col_d2 = st.columns([1, 2])
                        with col_d1:
                            st.dataframe(d_df, hide_index=True, use_container_width=True)
                            top_d = max(result["by_device"], key=result["by_device"].get)
                            st.caption(f"🎯 주 검색 기기: **{top_d}**")
                        with col_d2:
                            st.bar_chart(d_df.set_index("기기"), height=200)

# ============ 탭5: 트렌드 발굴 (신규) ============
with tab5:
    if not st.session_state.api_configured:
        st.warning("👈 왼쪽 사이드바에서 네이버 API 키를 먼저 입력해주세요")
    else:
        st.info("""🔥 **뭘 쓸지 막막할 때** — 관심 분야 단어 하나를 씨앗으로 넣으면, **그 분야에서 요즘 뜨고 있는 연관 키워드**를 찾아드립니다.
        (예: '부모급여' 넣으면 그 주변 뜨는 키워드가 나옴) 최근 3개월 트렌드를 분석해 상승률 높은 순으로 보여줘요. (데이터랩 권한 필요)  
　🟢 네이버 데이터 (검색광고 API + 데이터랩)""")

        col_a, col_b = st.columns([3, 1])
        with col_a:
            seed_kw = st.text_input("관심 분야 키워드", placeholder="예: 다이어트", key="trend_seed")
        with col_b:
            analyze_count = st.selectbox("분석 개수", [10, 15, 20], index=0, key="trend_count",
                                         help="많을수록 정확하지만 느려집니다")

        st.caption("⚠️ 연관 키워드마다 데이터랩을 조회하므로, 10개 기준 약 20~40초 걸립니다.")

        only_related = st.checkbox(
            "🔲 씨앗 관련 키워드만 보기 (체크 해제 시 전체를 관련도 순으로 표시)",
            value=True, key="trend_only_related",
            help="체크: 씨앗 단어를 포함한 연관어만 남깁니다 (세탁기 같은 잡음 제거). 해제: 다 보여주되 관련 높은 순으로 정렬합니다.",
        )

        if st.button("🔥 트렌드 발굴 시작", type="primary", use_container_width=True, key="trend_dig_btn"):
            if not seed_kw.strip():
                st.error("키워드를 입력해주세요")
            else:
                # 1) 연관 키워드 수집
                with st.spinner("연관 키워드 수집 중..."):
                    rel_result = get_related_keywords_list(seed_kw, st.session_state.api_keys, limit=analyze_count)

                if rel_result.get("error"):
                    st.error(f"❌ {rel_result['error']}")
                else:
                    keywords = rel_result["keywords"]
                    # 씨앗 관련도 필터 적용 (체크 시 엄격, 해제 시 관련도 순 정렬)
                    keywords = filter_related_keywords(seed_kw, keywords, strict=only_related)
                    if only_related:
                        st.caption(f"연관 키워드 {len(keywords)}개 (씨앗 '{seed_kw}' 관련만). 트렌드 분석 시작...")
                    else:
                        st.caption(f"연관 키워드 {len(keywords)}개 (관련도 순). 트렌드 분석 시작...")

                    # 2) 각 키워드의 트렌드 방향 분석
                    progress = st.progress(0)
                    status = st.empty()
                    trend_data = []

                    for i, kw_info in enumerate(keywords):
                        kw = kw_info["키워드"]
                        status.text(f"트렌드 분석 중 ({i+1}/{len(keywords)}): {kw}")
                        direction = get_trend_direction(kw, st.session_state.api_keys)
                        if direction:
                            trend_data.append({
                                "키워드": kw,
                                "월간검색": kw_info["월간검색"],
                                "경쟁": kw_info["경쟁"],
                                "관련": kw_info.get("관련", ""),
                                "트렌드변화": direction["change_pct"],
                                "최근관심도": direction["recent_avg"],
                            })
                        progress.progress((i + 1) / len(keywords))
                        time.sleep(0.3)

                    status.empty()
                    progress.empty()

                    if not trend_data:
                        st.warning("트렌드 데이터를 가져오지 못했습니다. 데이터랩 권한을 확인해주세요.")
                    else:
                        # 상승률 순 정렬
                        trend_data.sort(key=lambda x: x["트렌드변화"], reverse=True)

                        st.success(f"✅ '{seed_kw}' 분야 트렌드 분석 완료")

                        # 상승/하락 분류
                        rising = [t for t in trend_data if t["트렌드변화"] > 5]
                        falling = [t for t in trend_data if t["트렌드변화"] < -5]

                        col_r, col_f = st.columns(2)
                        with col_r:
                            st.subheader("🔥 뜨는 키워드")
                            if rising:
                                for t in rising[:10]:
                                    st.markdown(
                                        f"**{t['키워드']}** &nbsp; "
                                        f"📈 +{t['트렌드변화']}% &nbsp; "
                                        f"(월 {t['월간검색']:,}회, 경쟁:{t['경쟁']})"
                                    )
                            else:
                                st.caption("뚜렷하게 상승 중인 키워드가 없습니다")

                        with col_f:
                            st.subheader("❄️ 식는 키워드")
                            if falling:
                                for t in falling[:10]:
                                    st.markdown(
                                        f"**{t['키워드']}** &nbsp; "
                                        f"📉 {t['트렌드변화']}% &nbsp; "
                                        f"(월 {t['월간검색']:,}회)"
                                    )
                            else:
                                st.caption("뚜렷하게 하락 중인 키워드가 없습니다")

                        # 전체 테이블
                        st.markdown("---")
                        st.subheader("📋 전체 결과 (상승률 순)")
                        df = pd.DataFrame(trend_data)
                        df_display = df.copy()
                        df_display["월간검색"] = df_display["월간검색"].apply(lambda x: f"{x:,}")
                        df_display["트렌드변화"] = df_display["트렌드변화"].apply(
                            lambda x: f"📈 +{x}%" if x > 5 else (f"📉 {x}%" if x < -5 else f"➡️ {x}%")
                        )
                        df_display = df_display.rename(columns={"트렌드변화": "트렌드"})
                        # 보기 좋은 순서로 정렬 (관련 열이 있으면 포함)
                        col_order = [c for c in ["키워드", "관련", "월간검색", "경쟁", "트렌드", "최근관심도"] if c in df_display.columns]
                        df_display = df_display[col_order]
                        st.dataframe(df_display, hide_index=True, use_container_width=True)

                        # CSV 다운로드
                        csv = df.to_csv(index=False).encode("utf-8-sig")
                        st.download_button(
                            "📥 CSV 다운로드", csv,
                            file_name=f"trend_discovery_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv", use_container_width=True,
                        )

                        st.caption("💡 '뜨는 키워드'를 '🎯 키워드 검증' 탭에서 자세히 분석하면 블로그 주제로 딱!")

# ============ 탭6: 세부 키워드 발굴 ============
with tab6:
    if not st.session_state.api_configured:
        st.warning("👈 왼쪽 사이드바에서 네이버 API 키를 먼저 입력해주세요")
    else:
        st.info("""🪓 **큰 키워드를 글감으로 쪼갤 때** — 넓은 키워드(예: 갤럭시S26)를 넣으면, **그 뒤에 붙는 세부 키워드**(사전예약·출시일·케이스 등)를 찾아  
        각각 합격 판정까지 해줍니다. 넓은 키워드는 입구로만 쓰고, 합격한 세부 키워드로 글을 쓰세요.  
　🟢 네이버 데이터 (자동완성 + 검색광고 API)""")

        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            sub_seed = st.text_input("넓은 키워드 (씨앗)", placeholder="예: 갤럭시S26", key="sub_seed")
        with col_s2:
            sub_stage = st.selectbox("블로그 상태", list(VERDICT_RULES.keys()), key="sub_stage")

        sub_two_step = st.checkbox(
            "⚡ 2단계로 빠르게 (먼저 수집만 → 고른 것만 정밀 분석)",
            value=False, key="sub_two_step",
            help="체크: 검색량만 빠르게 보고 직접 고른 키워드만 합격판정(빠름). 해제: 전체 자동 합격판정(느림).",
        )

        if st.button("🪓 세부 키워드 발굴", type="primary", use_container_width=True, key="sub_dig_btn"):
            if not sub_seed.strip():
                st.error("키워드를 입력해주세요")
            else:
                with st.spinner("세부 키워드 수집 중..."):
                    sub_res = collect_sub_keywords(sub_seed, st.session_state.api_keys, limit=20)

                if sub_res.get("error"):
                    st.error(f"❌ {sub_res['error']}")
                else:
                    st.session_state["sub_keywords"] = sub_res["keywords"]
                    st.session_state["sub_source"] = sub_res["source"]
                    st.caption(f"수집 완료 ({sub_res['source']}): 세부 키워드 {len(sub_res['keywords'])}개")

                    if not sub_two_step:
                        # 전체 자동 분석 + 합격 판정
                        progress = st.progress(0)
                        status = st.empty()
                        rows = []
                        kws = sub_res["keywords"]
                        for i, kw in enumerate(kws):
                            status.text(f"분석 중 ({i+1}/{len(kws)}): {kw}")
                            r = analyze_keyword(kw, st.session_state.api_keys)
                            if not r.get("error"):
                                v = judge_keyword(r, sub_stage)
                                rows.append({
                                    "키워드": kw,
                                    "판정": f"{v['emoji']} {v['grade']}",
                                    "_점수": v["points"],
                                    "월간검색": r["monthly_search"],
                                    "경쟁글": r["blog_count"],
                                    "경쟁강도": r["competition"],
                                    "노출점수": r["exposure_score"],
                                })
                            progress.progress((i + 1) / len(kws))
                            time.sleep(0.2)
                        status.empty(); progress.empty()
                        st.session_state["sub_rows"] = rows

        # 결과 표시 (전체 분석 결과)
        if st.session_state.get("sub_rows"):
            rows = st.session_state["sub_rows"]
            rows_sorted = sorted(rows, key=lambda x: x["_점수"], reverse=True)
            pass_n = sum(1 for r in rows if "합격" in r["판정"])
            st.success(f"✅ 분석 완료 — 합격 {pass_n}개 / 전체 {len(rows)}개")

            df = pd.DataFrame(rows_sorted)
            df_show = df.drop(columns=["_점수"]).copy()
            df_show["월간검색"] = df_show["월간검색"].apply(lambda x: f"{x:,}")
            df_show["경쟁글"] = df_show["경쟁글"].apply(lambda x: f"{x:,}")
            st.dataframe(df_show, hide_index=True, use_container_width=True)

            csv = df.drop(columns=["_점수"]).to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 합격 목록 CSV 다운로드 (주간 글감)", csv,
                file_name=f"sub_keywords_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True,
            )
            st.caption("💡 합격한 키워드를 '🎯 키워드 검증' 탭에 넣으면 blog_ai_writer로 바로 보낼 수 있어요.")

        # 2단계 모드: 수집된 키워드에서 직접 고르기
        elif st.session_state.get("sub_keywords") and st.session_state.get("sub_two_step"):
            st.markdown("---")
            st.subheader("⚡ 정밀 분석할 키워드 고르기")
            picked = st.multiselect(
                "합격 판정할 키워드를 고르세요 (적게 고를수록 빠름)",
                st.session_state["sub_keywords"],
                key="sub_picked",
            )
            if st.button("선택한 키워드 정밀 분석", key="sub_analyze_picked"):
                rows = []
                progress = st.progress(0)
                for i, kw in enumerate(picked):
                    r = analyze_keyword(kw, st.session_state.api_keys)
                    if not r.get("error"):
                        v = judge_keyword(r, st.session_state["sub_stage"])
                        rows.append({
                            "키워드": kw, "판정": f"{v['emoji']} {v['grade']}", "_점수": v["points"],
                            "월간검색": r["monthly_search"], "경쟁글": r["blog_count"],
                            "경쟁강도": r["competition"], "노출점수": r["exposure_score"],
                        })
                    progress.progress((i + 1) / max(1, len(picked)))
                    time.sleep(0.2)
                progress.empty()
                st.session_state["sub_rows"] = rows
                st.rerun()

# ============ 탭: 소재캘린더 (육아 가정 돈 정보) ============
with tab_cal:
    import datetime as _dt

    # 시즌 고정형: 그 달에 검색 폭증하는 돈 이슈 (시기 검증 2026-06)
    _SEASONAL = {
        1:  [("연말정산 자녀 세액공제 총정리", "1~2월 연말정산, 자녀 1명당 세액공제·교육비 공제"),
             ("연말정산 교육비 공제 (학원비·교복)", "초중고 교육비 세액공제, 취학아동 학원비 포함 여부")],
        2:  [("연말정산 환급 많이 받는 자녀 공제 팁", "맞벌이 부부 자녀공제 몰아주기 절세"),
             ("새학기 입학 지원금·교육급여 신청", "3월 개학 앞두고 저소득층 교육급여·입학지원")],
        3:  [("신학기 학원비 부담 줄이는 지원·공제", "개학 시즌, 예체능 학원비 세액공제 한도"),
             ("초등 방과후·돌봄교실 비용 지원", "신학기 돌봄 공백, 아이돌봄서비스 정부지원")],
        4:  [("5월 종합소득세 미리 준비 (자녀 인적공제)", "종소세 신고 앞두고 자녀 인적공제·부양가족 정리"),
             ("어린이날 다자녀 혜택 미리보기", "가정의달 앞두고 다자녀 KTX·놀이시설 할인")],
        5:  [("5월 종합소득세 자녀 인적공제 완벽정리", "★두딸파파 4위 검증 — 맞벌이 절세"),
             ("자녀장려금 5월 신청 시작 (조건·금액)", "★매년 5/1 신청, 18세 미만·부부합산 7천만원 미만"),
             ("가정의달 다자녀 나들이 할인 총정리", "어린이날·어버이날 휴양림·KTX·놀이공원 다자녀")],
        6:  [("여름방학 다자녀 휴양림·캠핑 할인 예약", "성수기 앞두고 국립자연휴양림 다자녀 면제/할인"),
             ("초등 여름방학 돌봄·교육비 지원", "방학 중 아이돌봄·방과후 비용 지원")],
        7:  [("여름휴가 다자녀 KTX·SRT·공항주차 할인", "성수기 이동비, 다자녀 철도 30%·공항주차 50%"),
             ("물놀이장·워터파크 다자녀 할인 정리", "여름 나들이 다자녀 입장 할인")],
        8:  [("자녀장려금 8~9월 지급 시기·금액 확인", "★정기신청자 8월말~9월 지급"),
             ("2학기 학원비·교육비 부담 줄이기", "개학 앞두고 교육비 공제·지원 점검")],
        9:  [("추석 다자녀 KTX·SRT 예매 할인", "명절 이동비, 다자녀 철도 할인 인증법"),
             ("추석 연휴 다자녀 나들이·휴양림", "연휴 다자녀 휴양림 예약·할인")],
        10: [("내년 육아 지원금 개편 미리보기", "정부 예산안 시즌, 내년 아동수당·부모급여 변경"),
             ("가을 다자녀 문화·체험 할인", "단풍철 다자녀 시설 할인")],
        11: [("연말정산 미리보기 자녀 공제 점검", "연말 앞두고 자녀 세액공제 미리 계산"),
             ("김장·난방비 다자녀 가구 지원", "겨울 앞두고 에너지바우처·다자녀 난방 지원")],
        12: [("내년 바뀌는 육아 지원금 총정리", "★연말 제도 개편 발표, 내년 변경점 정리"),
             ("연말정산 자녀 공제 막판 체크리스트", "1월 연말정산 대비 서류·공제항목 점검")],
    }
    # 상시형: 아무 때나 검색 꾸준, 두딸파파 주력 (영아~교육비~세금 전 범위)
    _EVERGREEN = [
        ("다자녀 지원금 2자녀 기준 총정리", "★두딸파파 1위 검증 — 2자녀 다자녀 혜택"),
        ("아동수당 신청·금액 (만 9세 미만)", "보편 수당, 소득무관 월 최대 10만원"),
        ("부모급여 (만 0~1세) 신청·금액", "영아 월 50~100만원, 출생 60일내 신청"),
        ("첫만남이용권 (첫째 200·둘째 300만원)", "출생 바우처, 국민행복카드"),
        ("자녀 세액공제 완벽정리", "자녀 수별 세액공제, 출산·입양 추가공제"),
        ("자녀장려금 조건·금액·신청법", "저소득 양육가구, 소득·재산 요건"),
        ("아이돌봄서비스 정부지원 등급", "맞벌이 돌봄, 중위소득별 지원율"),
        ("교육급여·교육비 지원 (저소득)", "초중고 교육급여, 입학·수업료"),
        ("다자녀 대학등록금·국가장학금 확대", "다자녀 기준 2자녀 완화, 등록금 지원"),
        ("가정양육수당 (24개월 이상 미취학)", "어린이집 미이용 가정, 월 10만원"),
    ]

    st.subheader("🗓️ 소재 캘린더 — 육아 가정 돈 정보")
    st.caption("두딸파파 전용 · '이번 주 뭐 쓰지?'를 시즌 2개 + 상시 3개로 제안 "
               "· 금액/요율/연령은 글 쓸 때 web_search로 반드시 재확인")

    _months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
    _cur = _dt.date.today().month
    _sel = st.selectbox("기준 월", _months, index=_cur - 1, key="cal_month")
    _m = _months.index(_sel) + 1
    _nxt = _m % 12 + 1

    st.markdown(f"### 📌 {_sel} 시즌 소재 (지금 터지는 돈 이슈)")
    for _t, _w in _SEASONAL.get(_m, [])[:2]:
        st.markdown(f"- **{_t}**  \n  └ {_w}")

    st.markdown("### ⏭️ 다음 달 미리 써두기")
    for _t, _w in _SEASONAL.get(_nxt, [])[:1]:
        st.markdown(f"- **{_t}**  \n  └ {_w}")

    st.markdown("### ♻️ 상시 소재 (아무 때나 꾸준한 검색)")
    for _t, _w in _EVERGREEN[:3]:
        st.markdown(f"- **{_t}**  \n  └ {_w}")

    with st.expander("상시 소재 전체 보기"):
        for _t, _w in _EVERGREEN:
            st.markdown(f"- **{_t}**  \n  └ {_w}")

    st.info("고른 소재를 '🎯 키워드 검증' 탭에 넣어 검색량·경쟁도 확인 후 "
            "blog_ai_writer 프롬프트로 넘기세요. (발행은 항상 수동 — 자동발행 금지)")


# ============ 탭: AI 키워드 (모델별) ============
with tab_ai:
    st.info("""🤖 **제미나이가 키워드를 발굴** → 네이버 실측(검색량·문서수·난이도)으로 검증합니다.  
    🟢 AI는 '후보 발상'만 — 최종 판정은 네이버 실측입니다 (AI 추정 등급은 믿지 않음).  
    무료 한도(분당 호출 수)가 있어, 카테고리를 너무 많이 한꺼번에 돌리면 429가 날 수 있어요.""")

    if not st.session_state.api_configured:
        st.warning("👈 먼저 네이버 API 키를 입력하세요 (실측에 필요)")
    elif not st.session_state.ai_keys.get("gemini_api_key"):
        st.warning("👈 사이드바 '🤖 Gemini API 키'에서 키를 입력하세요 (무료 발급)")
    else:
        _ai_cats = list(CATEGORY_NEWS_QUERIES.keys())
        if "ai_cat_selected" not in st.session_state:
            st.session_state.ai_cat_selected = [_ai_cats[0]]
        # 구버전(문자열) 호환 — 리스트로 승격
        if isinstance(st.session_state.ai_cat_selected, str):
            st.session_state.ai_cat_selected = [st.session_state.ai_cat_selected]

        st.markdown("**카테고리 선택** (여러 개 클릭 가능 · 다시 클릭하면 해제)")
        _per_row = 3
        for _i in range(0, len(_ai_cats), _per_row):
            _cols = st.columns(_per_row)
            for _j, _cat in enumerate(_ai_cats[_i:_i + _per_row]):
                with _cols[_j]:
                    _is_sel = (_cat in st.session_state.ai_cat_selected)
                    if st.button(
                        ("✅ " if _is_sel else "") + _cat,
                        key=f"ai_cat_btn_{_i + _j}",
                        use_container_width=True,
                        type=("primary" if _is_sel else "secondary"),
                    ):
                        if _is_sel:
                            st.session_state.ai_cat_selected.remove(_cat)
                        else:
                            st.session_state.ai_cat_selected.append(_cat)
                        st.rerun()

        ai_cats_sel = st.session_state.ai_cat_selected
        if ai_cats_sel:
            st.caption(f"선택됨 ({len(ai_cats_sel)}개): **{', '.join(ai_cats_sel)}**")
        else:
            st.caption("⚠️ 카테고리를 하나 이상 선택하세요")
        ai_n = st.slider("모델당·카테고리당 키워드 개수", 6, 20, 12, key="ai_n_slider")

        has_gemini = bool(st.session_state.ai_keys.get("gemini_api_key"))

        if st.button("🚀 AI 키워드 생성 + 네이버 실측", type="primary", use_container_width=True, key="run_ai_kw"):
            if not ai_cats_sel:
                st.warning("카테고리를 하나 이상 선택하세요")
            elif not has_gemini:
                st.warning("사이드바에서 Gemini API 키를 먼저 입력하세요")
            else:
                st.session_state["ai_kw_gemini"] = None
                _total = len(ai_cats_sel)
                _g_rows, _g_err = [], None
                for _gi, _cat in enumerate(ai_cats_sel):
                    with st.spinner(f"🔵 제미나이 키워드 발굴+실측 ({_gi+1}/{_total}): {_cat}"):
                        g_res = generate_keywords_gemini(_cat, st.session_state.ai_keys["gemini_api_key"], ai_n)
                        if g_res.get("error"):
                            _g_err = g_res["error"]
                            continue
                        for _row in measure_ai_keywords(g_res["keywords"], st.session_state.api_keys):
                            _row = {"카테고리": _cat, **_row}
                            _g_rows.append(_row)
                if _g_rows:
                    st.session_state["ai_kw_gemini"] = {"rows": _g_rows}
                elif _g_err:
                    st.session_state["ai_kw_gemini"] = {"error": _g_err}

        st.markdown("### 🔵 제미나이 결과")
        gdata = st.session_state.get("ai_kw_gemini")
        if gdata is None:
            st.caption("아직 생성 안 함" if has_gemini else "Gemini 키 없음")
        elif gdata.get("error"):
            st.error(gdata["error"])
            if "429" in str(gdata["error"]):
                st.info("⏳ 429 = 무료 한도 초과(분당 호출 수). 1~2분 기다렸다가 다시 시도하거나, 카테고리를 줄여보세요.")
        elif gdata.get("rows"):
            df_g = pd.DataFrame(gdata["rows"])
            st.dataframe(df_g, use_container_width=True, hide_index=True)
            st.download_button("⬇️ 제미나이 CSV", df_g.to_csv(index=False).encode("utf-8-sig"),
                               "gemini_keywords.csv", "text/csv", key="dl_gemini")
        else:
            st.caption("결과 없음")

        st.caption("💡 월간검색 높고 난이도 🟢인 키워드가 발행 1순위. 고른 키워드는 '🎯 키워드 검증' 탭에서 한 번 더 정밀 확인 → blog_ai_writer로.")

st.markdown("---")
st.caption("💡 키워드 종합 분석기 v6.11 | 네이버 + 구글 + 데이터랩 + 트렌드 + AI 키워드(제미나이)")
