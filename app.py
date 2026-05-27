"""
네이버 키워드 분석기 v3
======================
브라우저 localStorage에 API 키를 저장하여, 새로고침해도 유지됩니다.
각 사용자의 브라우저에만 저장되므로 친구와 링크 공유도 가능 (각자 자기 키 입력).
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
from datetime import datetime

st.set_page_config(page_title="네이버 키워드 분석기", page_icon="🔍", layout="wide")

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

# ================================================
# localStorage에서 키 불러오기 (페이지 첫 로드 시)
# ================================================
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
        // URL 파라미터로 전달
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

# URL 파라미터에서 키 읽기 (localStorage → JS → URL → Python)
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
        # URL 파라미터 제거 (보안)
        st.query_params.clear()
    else:
        # localStorage 읽기 시도 (한 번만)
        st.session_state.keys_loaded_from_browser = True
        components.html(load_keys_html, height=0)

st.markdown('<div class="main-header">🔍 네이버 키워드 분석기</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">검색량 · 블로그 수 · 홈판 노출 확률을 한 번에 분석</div>', unsafe_allow_html=True)


# ================================================
# JS 함수: localStorage에 저장
# ================================================
def save_to_localstorage(keys_dict):
    """JS를 통해 brower localStorage에 저장"""
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
    """localStorage 키 삭제"""
    clear_html = """
    <script>
    ['client_id', 'client_secret', 'ad_api_key', 'ad_secret_key', 'ad_customer_id'].forEach(k => {
        localStorage.removeItem('naver_kw_' + k);
    });
    </script>
    """
    components.html(clear_html, height=0)


# ================================================
# 사이드바: API 설정
# ================================================
with st.sidebar:
    st.header("⚙️ API 설정")
    
    if st.session_state.api_configured:
        st.markdown('<div class="api-status-ok">✅ API 키 자동 로드 완료</div>', unsafe_allow_html=True)
        st.caption("브라우저에 저장되어 다음 방문 시에도 자동 로드됩니다")
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
                st.success("브라우저 저장소에서 삭제됨")
                time.sleep(1)
                st.rerun()
    else:
        st.markdown('<div class="api-status-no">⚠️ API 키를 입력하세요</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.expander("🔑 네이버 API 키 입력", expanded=not st.session_state.api_configured):
        st.caption("**검색 API** (developers.naver.com)")
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
                st.success("✅ 저장 완료! 다음부터는 자동으로 불러옵니다.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("⚠️ 5개 키 모두 입력하세요")
    
    st.markdown("---")
    st.markdown("""**🔒 보안 안내**
- 키는 **본인 브라우저에만** 저장됩니다 (서버 X)
- 다른 사람이 이 사이트 들어가도 본인 키 못 봄
- 친구와 링크 공유 시, 친구는 자기 키 따로 입력""")
    st.markdown("---")
    st.markdown("""**📊 점수 가이드**
- 🟢 매우쉬움 (75+)
- 🟢 쉬움 (55~74)
- 🟡 보통 (35~54)
- 🔴 어려움 (20~34)
- 🔴 매우어려움 (~19)""")


# ================================================
# 분석 함수들
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
            return {"keyword": keyword, "error": "검색광고 API 인증 실패 (401) - 키 확인"}
        elif code == 403:
            return {"keyword": keyword, "error": "검색광고 API 권한 거부 (403) - 비즈머니 잔액 또는 라이선스 확인"}
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
                return {"keyword": keyword, "error": "검색 API 인증 실패 - Client ID/Secret 확인"}
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
# 메인 영역
# ================================================
if not st.session_state.api_configured:
    st.warning("👈 왼쪽 사이드바에서 API 키를 먼저 입력해주세요")
    st.info("💡 한 번 저장하면 다음 방문 시 자동으로 불러옵니다!")
    st.markdown("---")
    st.markdown("### 🔑 API 키 발급 방법")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""**검색 API** (블로그 수 조회)
1. https://developers.naver.com 접속
2. 로그인 → Application 등록
3. 사용 API: **검색** 체크
4. **Client ID**, **Client Secret** 발급""")
    with col_b:
        st.markdown("""**검색광고 API** (검색량 조회)
1. https://searchad.naver.com 접속
2. 회원가입 (개인 광고주 가능)
3. 도구 → API 사용 관리
4. **Access License**, **Secret Key**, **Customer ID** 확인""")
else:
    tab1, tab2 = st.tabs(["🎯 단일 키워드", "📋 일괄 분석"])
    
    with tab1:
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
    
    with tab2:
        keywords_text = st.text_area("키워드들 (한 줄에 하나씩)", placeholder="다이어트\n홈트레이닝\n간헐적단식", height=150)
        
        if st.button("🔍 일괄 분석", type="primary", use_container_width=True, key="bulk_btn"):
            keywords = [k.strip() for k in keywords_text.split("\n") if k.strip()]
            if not keywords:
                st.error("키워드를 입력해주세요")
            else:
                progress = st.progress(0)
                status = st.empty()
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
                            "키워드": r["keyword"],
                            "월간검색": r["monthly_search"],
                            "주간검색": r["weekly_search"],
                            "일간검색": r["daily_search"],
                            "블로그수": r["blog_count"],
                            "경쟁": r["competition"],
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

st.markdown("---")
st.caption("💡 네이버 키워드 분석기 v3.0 | 키 자동 저장")
