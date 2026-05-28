"""
키워드 종합 분석기 v6
====================
네이버 키워드 + 구글 트렌드 + 네이버 데이터랩 + 트렌드 발굴
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

load_keys_html = """
<script>
(function() {
    const keys = ['client_id', 'client_secret', 'ad_api_key', 'ad_secret_key', 'ad_customer_id'];
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
    
    st.markdown("---")
    st.markdown("""**📋 탭 안내**
- 🎯 네이버 단일: 키워드 종합 분석
- 📋 네이버 일괄: 여러 개 한번에
- 📈 구글 트렌드: 키워드 트렌드 비교
- 📊 데이터랩: 연령/성별 분석
- 🔥 트렌드 발굴: 내 분야 뜨는 키워드""")


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
# 메인 영역 - 탭 5개
# ================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 네이버 단일", "📋 네이버 일괄", "📈 구글 트렌드",
    "📊 데이터랩 (인구통계)", "🔥 트렌드 발굴"
])

# ============ 탭1: 네이버 단일 ============
with tab1:
    if not st.session_state.api_configured:
        st.warning("👈 왼쪽 사이드바에서 네이버 API 키를 먼저 입력해주세요")
    else:
        keyword = st.text_input("분석할 키워드", placeholder="예: 다이어트", key="single_kw")
        
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

# ============ 탭2: 네이버 일괄 ============
with tab2:
    if not st.session_state.api_configured:
        st.warning("👈 왼쪽 사이드바에서 네이버 API 키를 먼저 입력해주세요")
    else:
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
    st.info("💡 구글 트렌드는 API 키가 필요 없습니다. 최대 5개 키워드 비교 가능.")
    
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
        st.info("""💡 키워드를 검색하는 사람들의 **연령/성별/기기** 비율을 분석합니다.  
        ⚠️ 이 기능은 developers.naver.com에서 **'데이터랩(검색어 트렌드)' API 권한**이 추가되어 있어야 동작합니다.""")
        
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
        st.info("""💡 관심 키워드를 입력하면, **그 분야에서 요즘 뜨고 있는 연관 키워드**를 찾아드립니다.  
        최근 3개월 트렌드를 분석해 상승률이 높은 순으로 보여줘요. (데이터랩 권한 필요)""")

        col_a, col_b = st.columns([3, 1])
        with col_a:
            seed_kw = st.text_input("관심 분야 키워드", placeholder="예: 다이어트", key="trend_seed")
        with col_b:
            analyze_count = st.selectbox("분석 개수", [10, 15, 20], index=0, key="trend_count",
                                         help="많을수록 정확하지만 느려집니다")

        st.caption("⚠️ 연관 키워드마다 데이터랩을 조회하므로, 10개 기준 약 20~40초 걸립니다.")

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
                    st.caption(f"연관 키워드 {len(keywords)}개 발견. 트렌드 분석 시작...")

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
                        df_display.columns = ["키워드", "월간검색", "경쟁", "트렌드", "최근관심도"]
                        st.dataframe(df_display, hide_index=True, use_container_width=True)

                        # CSV 다운로드
                        csv = df.to_csv(index=False).encode("utf-8-sig")
                        st.download_button(
                            "📥 CSV 다운로드", csv,
                            file_name=f"trend_discovery_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv", use_container_width=True,
                        )

                        st.caption("💡 '뜨는 키워드'를 '🎯 네이버 단일' 탭에서 자세히 분석하면 블로그 주제로 딱!")

st.markdown("---")
st.caption("💡 키워드 종합 분석기 v6.0 | 네이버 + 구글 + 데이터랩 + 트렌드 발굴")
