"""
키워드 종합 분석기 v7.10
====================
네이버 키워드 + 구글 트렌드 + 네이버 데이터랩 + 트렌드 발굴

[변경 이력]
- v7.10: (D-1029-1) 사장님 "추천·비추천만 말고 정확한 이유를 같이" — 카드마다 판정 알약 옆 뻔한 한 줄("글이 적어 쓰기 좋아요") 대신 이 키워드의 실제 이유를 한 줄로("왜: 검색 적당 · 글이 찾는 사람보다 적음 · 상위 글이 오래돼 틈"). judge_keyword가 판정 분기마다 짧은 이유(short)를 같이 만들어 계산과 설명이 어긋나지 않게. 판정 기준은 그대로.
- v7.9: (D-1028-2) 네이버 기준도 보이게 — 키워드 도구의 "경쟁 정도"(높음·중간·낮음)를 카드 숫자 줄·키워드 자세히·검증 표에 "네이버 광고 경쟁"으로 표시. 이미 받아 오던 값(compIdx)이라 호출 추가 없음. 판정 계산은 그대로(v6.27: 광고 경쟁은 블로그 순위 난이도가 아니라 상업성).
- v7.8: 운영실 숫자 칸 "최근 7일 / 30일"이 좁은 화면에서 "5 / 1…"로 잘림(실제 앱 확인) → "최근 7일 N편", 30일은 ? 도움말로. GitHub push를 클로드가 하는 첫 시험 버전.
- v7.7: (D-1027-2) 블로그 운영실에 "구글 블로그" — 글 목록 = Blogger 피드(키 불필요, 최대 500개) / 서치콘솔 연결(Secrets [gsc] site·key_json, 서비스 계정 읽기 전용) → ① 🔎 색인 상태: URL 검사 API(구글이 직접 알려 주는 색인 여부·마지막 크롤링, 하루 2,000회) + "검사 열기"로 서치콘솔에서 색인 요청 ② 📈 노출·클릭: 최근 28일 글별 노출·클릭·평균 순위·대표 검색어·직전 28일 대비 클릭 변화. 서비스 계정 로그인(RS256 서명)은 부품 없이 직접 — openssl 서명과 같은지 확인. 카테고리·겹치는 글은 네이버와 공통(구글은 라벨).
- v7.6: (D-1027-1) 🗂️ 블로그 운영실 메뉴 — 사장님 "릴스 속 운영실 같은 걸 내 블로그용으로". 블로그 아이디 → 네이버 블로그 RSS(키·로그인 불필요, 최근 50개)로 글 목록 → ① 검색 누락: 제목 그대로 블로그 검색(글당 검색 API 1콜, 동시 3개) 상위 30개 안에 내 글이 있나 ✅/❌/⏳(발행 2일 안) ② 카테고리별 글 수·마지막 글, 최근 7·30일 글 수·평균 간격·가장 오래 쉰 때 ③ 겹치는 글: 제목 낱말+태그 겹침(블로그 글 20% 넘게 붙은 공통 태그는 뺌). 방문자·유입 검색어는 네이버 API가 없어 안 함.
- v7.5: (D-1022-6) 세부 키워드 가져오는 곳 고르기 — 검색창 아래 "자동완성(사람들이 실제로 치는 말, 기본) / 연관 키워드(검색광고 도구, 더 넓게·키 필요)". 사장님 "연관검색어는 사라진 거야?" → 자동완성이 기본이 되면서 연관어는 실패할 때만 나왔음. 결과 제목 옆에 어디서 가져왔는지 표시. 키 없으면 연관 키워드는 자동완성으로 대신.
- v7.4: (D-1022-2) 화면 다듬기 — 사장님 "거북이버프 도구 수준 UI, 누구나 쓰는 도구 느낌". Pretendard 글꼴·파랑 한 색·흰 카드·알약 버튼. 결과 표(data_editor) → 카드 목록(체크 상자 + 키워드 + 숫자 한 줄 + 판정 알약 배지·한 줄 설명 + ⚖/💰/주인공 꼬리표). 숫자 줄에 "1위 시 하루 약 N명"(월 검색×20%÷30, 계산만). 이번 달 글감 버튼·데이터(MONTHLY_TOPICS) 삭제. 시험: AppTest 4종 오류 0(검증/apptest_v7·nokey는 카드 체크 상자로 고침).
- v7.3: (D-1020-1) 키워드 "주인공" 칸 — 웹문서 상위 10개 중 공식 기관 도메인 수(webkr display 1→10, 같은 1콜) + 뉴스 총 기사 수·최근 7일 기사(뉴스 1콜 추가)로 🏛 공식 / 📰 언론 / 📝 블로그 표시. 세부 키워드 표·여러 개 한꺼번에 표·자세히(근거 한 줄). 처음엔 표시만(판정 점수 그대로) — 노출 진단 키워드로 맞는지 확인 후 반영 결정.
- v7.2: (D-1019-5) 왼쪽 세로 메뉴 — 사장님 "시인성이 안 좋아, 키워드 찾기랑 다른 데서 글감 찾기 항목을 왼쪽에 정렬". 사이드바에 🔍 키워드 찾기 + 보도자료·분야별 뉴스·뜨는 키워드·여러 개 한꺼번에·구글 트렌드 6개를 세로로, 고른 화면만 오른쪽에(아래 접힌 상자·가로 버튼 삭제). 키워드 찾기 화면 내용은 그대로.
- v7.1: (D-1019-1, Muse AI 리뷰 반영) 구매의도 지원 — ① "씨앗+추천/가격/순위/후기" 자동완성 확장(대비 키워드와 같은 방식, 검색당 자동완성 +4회) ② 표에 💰 구매형 칸 + 구매형 키워드의 광고경쟁 '높음'은 "돈 되는 주제" 신호로 안내 ③ 보내기 박스에 ⚖/💰가 있으면 "제휴글 후보" 안내(제휴글쓰기는 상품을 직접 넣는 방식이라 자동 채움 안내는 안 함) ④ 죽은 코드 BLOG_PROFILES·CATEGORY_POOLS·analyze_demographics 삭제(BLOG_CHOICES는 이미 없음). ⚠ py_compile + 함수 단위 시험만.
- v7.0: (D-1014-8) 화면 전면 개편(A안 · 한 화면) — 사장님 "너무 복잡하고 조잡해". 왼쪽 메뉴 9개를 없애고 검색창 하나로: 키워드 → 세부·롱테일 키워드 판정 표(동시 3개씩 판정) → 쓸 것 체크 → 생성기로(첫째 = 메인, 나머지 = 서브 키워드). 막막할 땐 검색창 아래 이번 달 글감 버튼. '키워드 하나 자세히'(판정 이유·상위 글·추이·뉴스·더 파기)와 '다른 데서 글감 찾기'(보도자료·분야별 뉴스·뜨는 키워드·여러 개 한꺼번에·구글 트렌드)는 접어 둠. 옛 한 번에 보기·세부 글감 파기·키워드 검증·이번 달 글감 화면은 이 한 화면으로 합쳐 삭제(⭐담아두기는 표 CSV 저장으로).
- v6.41: (D-1014-7) 돈나나 "세부 + 대비로 쪼개기" 반영 — ① 대비 키워드: 자동완성을 "씨앗 + vs·차이·비교"로도 받아 세부 글감 파기·한 번에 보기 연관어·생성기 서브 키워드에 함께 실음(⚖ 표시). 검색광고 연관어·자음 확장엔 잘 안 잡히던 것(예: 아이폰17 → vs 에어 차이·vs 17e 비교). 대비가 없는 주제(제습기 등)는 빈손이라 그냥 지나감 ② 세부 글감 파기 결과에서 "🔍 한 번에 보기로 이어서 파기" — 1단계에서 끝나던 것을 한 번에 보기의 파고들기(경로 표시)로 이어 감. ⚠ 로컬 파이썬 없어 정적 검토만.
- v6.40: (D-1014-1) 세부 키워드 '자음 확장' — 자동완성을 "씨앗 + ㄱ~ㅎ"로 여러 번 받아 롱테일을 넓게 모음(예: '제습기'만 넣으면 8개 구매형뿐 → '제습기 ㅂ'에서 보관·버리는법·분해청소). 생성기 v12.13 '서브 키워드' 칸으로 보내기 시드에 실려 감.
- v6.39: (D-1007-3) ① 🤖 AI 키워드(제미나이) 탭·사이드바 키 입력 삭제 ② 🗓️ 이번 달 글감 탭 신설(월별 살림 글감 6분류 → 버튼 한 번에 한 번에 보기로 / 한꺼번에 판정 / 이어 쓰기 = 지난 글 자동완성) ③ 판정 재설계: 검색량 100 미만 불합격·300 미만 최대 보통·넓으면 감점 / 비율이 핵심(1 미만 황금 ~ 30 이상 과다) / 절대 문서수는 극단(신규 20만+)만 감점(이중 감점 제거) / 상위 글 평균 180일+면 가점 / 노출 점수(광고 경쟁·모바일 섞임)는 판정에서 제외 / 합격 3점+
- v6.4: AI 키워드 탭 추가 (클로드·제미나이 각각 발굴 → 네이버 실측, 모델별 따로 출력)
- v6.5: AI 키워드 탭 카테고리 선택을 드롭다운 → 버튼 그리드로 변경
- v6.6: AI 키워드 탭 카테고리 복수 선택(토글) 지원, 결과에 카테고리 칼럼 추가
- v6.7: AI 키 저장 시 공백 제거(strip), API 오류 메시지에 실제 응답 본문 표시
- v6.8: 클로드 제거(결제 부담), 제미나이 전용으로 정리 + 모델명 2.0(폐기)→2.5-flash 수정
- v6.9: 제미나이 프롬프트 수정 — 문장형 대신 2~4단어 짧은 키워드 강제(네이버 검색량 측정 가능하게)
- v6.10: 시드 텍스트 버그 수정 — 블로그(라디오) 변경이 복사 텍스트에 반영되도록 text_area key 제거
- v6.11: 키워드 검증 탭 순서 변경 — 블로그 선택을 키워드 입력 위로 올림(블로그 먼저 → 검증)
- v6.12: 시드 텍스트 버그 수정 — reviewheart 힌트의 '후기·추천'(카테고리를 에세이/리뷰로 오분류시키던 단어) 제거, CAT-D(육아)+INT-1(혜택·비용)+정보성 신호어로 교체. cat_hint 명사 나열을 문장으로 녹여 자막 꼬리말 어색함 제거. (정책글이 '신청'을 메인키워드·에세이로 잘못 잡던 문제 해결)
- v6.13: 시드 텍스트 의도 고정 버그 수정 — reviewheart의 cat_hint/intent_hint에 박힌 INT-1(지원금·혜택·금액·신청) 단어가 모든 시드에 들어가 검색의도가 늘 '가격확인'·성격이 늘 '정보성'으로 고정되던 문제. 프로필은 카테고리(CAT) 신호어만 담고, 검색의도·성격은 키워드 자신과 연관어가 정하게 함(정책 키워드는 연관어에 신청·금액이 들어와 자연히 INT-1 유지, 육아·교육·시기형 키워드는 제대로 분류됨).
- v6.14: 시드에 세부 키워드 주입 — 검증 탭 분석 시 자동완성 세부키워드(아동수당→신청·언제까지·계좌변경·지급일 등)를 함께 수집해 시드의 연관어 자리에 넣음. 맨 키워드엔 의도가 없어 검색의도가 늘 한 값으로 고정되던 문제 해결(세부어가 의도를 정함). ※ 넓은 키워드는 다의도라 여전히 흐릴 수 있음 → 합격한 '세부 키워드'로 글 쓰면 의도가 또렷해짐.
- v6.15: 검증 탭 UI 개편 — 블로그명(ioneteam/reviewheart) 라벨 제거(카테고리 키·뉴스쿼리 키에서). 기존 "어느 블로그?" 단일 라디오(블로그명에 카테고리+단계 묶여있던 것)를 **'① 카테고리 선택 + ② 블로그 단계(신규/기존)'** 공통 기준으로 분리. cat_hint는 카테고리에서 파생(`cat_hint_for`), 판정기준은 단계가 곧 VERDICT_RULES 키(신규/기존). (기타는 신규와 기준이 동일해 제거) 선택값은 `st.query_params`(cat/stage)로 저장돼 새로고침에도 유지. `build_seed_text(result, cat_hint, sub_keywords)`로 시그니처 변경(BLOG_PROFILES·BLOG_CHOICES 의존 제거).
- v6.16: v6.15 마감 정리 — API키 부트스트랩의 query_params.clear()를 '키 파라미터만 선택 삭제(del)'로 바꿔 cat/stage 선택 저장값이 새로고침에도 보존되게 함(전체 clear 시 날아가던 버그). 키워드 입력 라벨 중복(② 두 번 → ③ 분석할 키워드) 수정. ※ 이후 키워드 검색기도 수정 시마다 버전 +0.1.
- v6.17: 세부 글감 파기 탭 합격 집계 버그 수정 — `"합격" in 판정`이 '불합격'에도 매칭돼 불합격을 합격으로 세던 문제(예: 실제 합격 0개인데 "합격 8개" 표시). 🟢 이모지로만 카운트하도록 변경.
- v6.18: '틀린 탭 사용' 자동 안내 추가 — suggest_tab() 통일 배너로, 잘못된 탭에 키워드를 넣으면 더 맞는 탭을 추천. ①키워드 검증: 넓은 키워드(불합격+월검색≥3만)→세부 글감 파기 ②여러 개 검증: 전부 넓은 단어→세부 글감 파기 ③구글 트렌드: 1개만 입력→키워드 검증 ④누가 검색하나: 데이터 없음(검색량 적음)→키워드 검증 ⑤글감 찾기: 연관어≤1(좁은 단어)→세부 글감 파기 ⑥세부 글감 파기: 자동완성 0개→키워드 검증 / 합격 0개→씨앗 구체화 안내. (임계값은 조정 가능)
- v6.19: 세부 글감 파기 'muhankey 스타일' 강화 — ① 연관어 개수 선택(20/50/100) ② "🔗 공식 연관어로 넓게 뽑기" 옵션(자동완성 대신 검색광고 연관어로 한 번에 많이, collect_sub_keywords(prefer_related=True)) ③ 비율(=문서수÷월간검색) 칼럼 추가(낮을수록 경쟁 대비 수요 좋음). 개수 많으면 ⚡2단계 권장 안내.
- v6.20: 소재 캘린더 탭 카테고리별 분리 — 기존엔 돈/육아 정책이 한 덩어리로 섞여 나왔음. CAL_CATEGORIES 자료구조(육아·가정·돈·정보 4개)로 각 카테고리마다 월별 시즌 소재 + 상시 소재를 따로 관리. UI는 기준 월 선택 + 카테고리 멀티셀렉트(기본 전체) → 2×2 카드로 카테고리별 분리 표시(각 카드: 이번 달 시즌 2개 + 다음 달 1개 + 상시 2개 + 전체 보기 expander). 기존 돈 시즌/상시 데이터는 '💰 돈' 카테고리로 그대로 이전.
- v6.21: 세부 글감 파기에 '두딸파파 씨앗 풀' 드롭다운(SEED_POOL 32개 내장) — "뭘 넣지?" 결정 피로 제거. 풀에서 고르면 직접 입력 없이 바로 파기. (직접 입력)이 기본값이라 기존 동작 무변경.
- v6.22: 📰 '오늘의 소재' 탭 신설 — 정책브리핑(korea.kr) 부처별 보도자료 RSS 수집(표준 라이브러리 XML 파싱, feedparser 의존성 없음) → 신호어 필터(돈·행동·타겟 + 최근성 점수) → 제목에서 후보 키워드 추출 → 상위 N건 검색량·문서수·비율 자동 실측(quick_kw_check). Streamlit Cloud엔 백그라운드가 없어 "버튼 수집" 방식. ⚠ RSS 주소는 배포 후 실테스트로 검증 필요(부처별 성공/실패 화면 표시, RSS_FEEDS 딕셔너리에서 수정).
- v6.23: 오늘의 소재 수집원 교체 (RSS → 목록 페이지 파싱) — 실테스트에서 dept_*.xml 전부 404. 조사 결과 korea.kr RSS는 서비스 자체가 중단됨(살아있는 policy_*.xml 피드도 내용이 2018년 12월 화석). 보도자료 목록 페이지(briefing/pressReleaseList.do)가 서버렌더링(오늘 날짜 자료가 정적 HTML에 존재)임을 확인 → fetch_press_releases()로 직접 파싱(제목=<strong>, 날짜·부처=span.source, pageIndex 페이지네이션, 페이지당 ~20건). RSS_FEEDS·fetch_rss_items 삭제. 날짜 점수 파싱을 RFC822→"%Y.%m.%d"로. 실제 저장 HTML로 파싱 로직 검증(node 포팅, 20건 추출 확인). 추가 설계 수정 2건: ① 최근성 점수만으로 필터 통과되던 구멍 차단(신호어 최소 1개 필수 — 안 그러면 오늘 자료는 MOU·간담회까지 전부 통과) ② 신호어 통과 0건인 날(흔함)을 위해 기본 수집 5페이지(~100건) + 전체 제목 훑어보기 폴백 expander.
- v6.24: 오늘의 소재 실운영 튜닝 — 첫 라이브 실행 결과("청년 700명 파견"류 행정 홍보가 상위 점령) 반영. ① 필터를 "돈 또는 행동 신호 필수"로 강화(타겟 단어는 가점만 — 청년·자녀만으로는 통과 불가) ② 후보 키워드 잡음어 보강(보도·참고·점검·운영·모든·목소리 등) + 서술형(다로 끝남: 알린다·시작한다) 제외.
- v6.25: 씨앗 풀 정체성 확장 — SEED_POOL을 '자녀 중심 32개' → '가정·자녀 경제 55개'로 확장(2026-07-10 확정 라인업 반영, 네이버 초유딩파파 = 가족 앵글 있는 돈). 신규 카테고리: 출산·양육 신제도(신생아 특례대출·6+6 부모육아휴직제 등) / 연말정산·세금(인적공제·의료비·월세·신용카드·산후조리원) / 청약·주거(주택드림·특별공급·전세자금·디딤돌) / 청년·신혼 지원(청년도약계좌·청년월세) / 건강보험·의료(피부양자·환급·본인부담상한제·영유아 건강검진) / 연금·목돈(국민연금·연금저축·노란우산·IRP). ★ 투자·투기(주식·부동산·코인·펀드·ETF) 전면 제외 — 세액공제·제도·절약 앵글만. 코드 변경은 SEED_POOL 리스트·selectbox help·주석뿐(로직 무변경).
- v6.26: blog_ai_writer '보내기' 시드 개선 2건. ① 카테고리 드롭다운 기본값을 IT(CAT-A, 맨 앞)→ 'CAT-C·정보·생활정보'(힌트 없는 안전 카테고리)로. 기존엔 안 바꾸면 cat_hint_for가 "스마트폰 갤럭시 아이폰 노트북 IT" 신호어를 시드에 몰래 주입 → 최저시급 등 비IT 키워드가 blog_ai_writer에서 CAT-A로 오분류(이번 실사례). IT 힌트는 CAT-A 직접 선택 시만 나오게(IT 서브블로그용 유지). ② build_seed_text: 실제 연관어(sub_keywords) 없을 때 키워드를 가짜로 반복하던 걸 제거 — 연관어 있을 때만 "함께 많이 찾는 키워드로는 ~" 문장 삽입(없으면 생략). ⚠ 로컬 파이썬 없어 정적 검토만 — 배포 후 실테스트 필요.
- v6.38: '한 번에 보기' 3대 보강 (시중 도구 비교 결핍 메우기, 사장님 "뭔가 부족" 진단 → 1·2·3 순서대로). **#1 상위 노출 글(v6.36)**: 판정 카드 아래 '🏆 지금 상위에 뜬 글'(제목·블로거·발행일) — "될까 안될까"만 알던 판정에 "누굴 이겨야 하나" 증거 추가. analyze_keyword가 최근성 계산용으로 이미 부르던 blog.json items를 재활용(추가 호출 X, top_posts 반환). **#2 검색 추이(v6.37)**: 카드에 '📈상승세/📉하락세/➡️유지 (±%)' + 최근 3개월 주간 스파크라인(get_trend_direction에 series·arrow·word 추가, 데이터랩 1콜). '지금이 쓸 타이밍인지' 타이밍 정보. **#3 담아두기(v6.38)**: ⭐담아두기 버튼 → 화면 하단 '담아둔 키워드' 표(판정·검색량·문서수·비율) + CSV 내보내기 + 비우기. 검증하면 휘발되던 걸 발행 계획으로 모음. 헬퍼 one_search(analyze+trend 묶음)로 검색·파기 양쪽 배선. ⚠ py_compile만 · 배포 후 실동작 확인 필요.
- v6.35: '한 번에 보기' 파고들기(drill-down) 매끄럽게 — 사장님 "두 번 파고들면 더 좋은 키워드 나오지 않나?". [기존] 연관어에서 [이걸로 검색] 누르면 판정만 뜨고 연관어는 다시 눌러야 해서 깊이 파려면 클릭이 많았음. [수정] ① 검색·파고들면 **연관어가 자동으로 함께 펼쳐짐**(one_show_related=True) → 넓은키워드→세부→더세부를 한 클릭씩. ② 버튼 라벨 '이걸로 검색'→**'이걸로 파기'**. ③ **파고들기 경로 브레드크럼**(🧭 아이폰 › 아이폰17 › 아이폰17 사전예약 · N단계째) 추가로 깊이 인지. one_path 세션상태로 관리(검색 시 리셋·파기 시 append). ⚠ py_compile만.
- v6.34: '한 번에 보기' 추천 연관어 관련도 필터 적용 — [문제] '아이폰' 검색 시 검색광고 keywordstool이 씨앗을 포함하지 않는 광고연관어(갤럭시·중고폰·요금제 등)까지 줘서 상관없는 게 많이 섞임(사장님 발견). [수정] 이미 있던 `filter_related_keywords(strict=True)`(씨앗 포함어만·위치무관·관련도순)를 통합 화면 연관어에도 적용 + 씨앗 자기 자신 제외 + 넉넉히(limit 10→40) 받아 걸러 상위 12개. 자동완성 폴백은 어차피 씨앗 포함이라 그대로 통과. [효과] 아이폰케이스·아이폰17 등 관련어만 남고 갤럭시·중고폰 제거. ⚠ py_compile만(로컬 streamlit 없음).
- v6.33: '한 번에 보기' 추천 연관어 폴백 수정 — [버그] '아이폰18' 등 신제품·미래 키워드는 검색광고 keywordstool에 데이터가 아직 없어 빈 결과 → "연관 키워드 없음"으로 뜸(사장님 실사용 발견). [원인] 키가 있으면 keywordstool만 쓰고, 그게 비면 폴백이 없었음(자동완성엔 아이폰18프로·출시일·사전예약·가격 등 잘 나오는데도). [수정] keywordstool이 error거나 빈 결과면 **자동완성으로 폴백**(씨앗과 동일한 항목은 제외) → 신제품도 연관어가 나옴. 자동완성 폴백 시 검색량은 없지만 각 줄 '이걸로 검색'으로 정밀 판정 가능(안내 캡션 추가). ⚠ 로컬 파이썬 없어 py_compile만 · 자동완성 엔드포인트 실측으로 아이폰18 10개 확인.
- v6.32: '🔍 한 번에 보기' 통합 기본 화면 신설 (거북이버프 황금키워드 흐름 벤치마킹) — 키워드 하나 넣고 엔터 → ①판정 카드(추천/보통/비추천 + 월간검색 PC·모바일 분리 + 문서수·비율·노출점수 + 상위노출 틈새 한 줄 + '그래서 뭘 하면 되나' 실행 조언 + 근거 expander) → [🔗 추천 연관 키워드](연관어+빠른판정+'이걸로 검색'으로 파고들기) → [📰 뉴스·정보 수집]을 한 화면에서. 8개 탭 오가지 않아도 됨. 사이드바 메뉴 맨 위=기본 화면. **하이브리드 키(get_active_keys)**: 서버 Secrets[naver] 있으면 방문자 키 없이 공개형, 없으면 방문자 입력 — 혼자 쓸 때/공개할 때 코드 동일(상용화 문 열어둠). **키 없어도** 연관어(자동완성)·뉴스(구글뉴스 RSS, fetch_news_titles_free)는 작동. 재사용: analyze_keyword·judge_keyword·get_related_keywords_list·search_news. 시장조사 근거: 성별·연령·구글트렌드는 블로거 저효용(무료도구도 없음)이라 기존 탭에 유지(통합 화면 미포함). ⚠ 로컬 파이썬 없어 py_compile만 — 배포 후 실행 확인 필요.
- v6.31: 사이드바 전문가형 리디자인 — ① 상단 브랜드 블록(로고+이름) 추가 ② 라디오 메뉴를 CSS로 '세로 내비 메뉴'화(hover 강조 + 선택 항목 accent 배경, radiogroup label 스타일링·:has(input:checked)) ③ '⚙️ API 설정'을 사이드바 **하단으로 이동·고정**(stSidebarUserContent flexbox + .push-bottom margin-top:auto) — 흩어져 있던 네이버/Gemini 2개 expander를 하나로 통합, 상태 배지 순화 ④ '어떤 걸 골라야 하나요?' 도움말을 접이식 expander로 정리 ⑤ 메인 헤더/여백·상태 배지 CSS 정돈(accent 팔레트 도입). ⚠ 로직 무변경(UI/CSS만) · :has 미지원 옛 브라우저에선 선택강조·하단고정이 순서상 하단 배치로 폴백. 로컬 파이썬 없어 정적 검토만 — 배포 후 실제 렌더 확인 필요.
- v6.30: 세부 글감 파기 '연관어 범위' 선택 시인성·설명 개선 — 기존 '🔗 공식 연관어로 넓게 뽑기' 체크박스가 옆칸에 작게 끼어 있고 용어(자동완성/검색광고 API)가 초보에게 어려웠음. → **'어떤 연관어를 찾을까요?' 라디오 2택**으로 승격(실예시: 구강검진 → 구강검진 비용 vs 찾아가는 AI구강검진). captions로 각 선택 결과 한 줄 설명. 값은 기존 prefer_related(sub_wide)로 그대로 연결 — 로직 무변경, UI/문구만. 상단 안내의 '자동완성+검색광고 API' 표현도 '네이버 실제 검색 데이터'로 순화. 기본값은 여전히 '뒤에 붙는 말만'(빠름).
- v6.29: 메뉴 UI 개편 — 상단 가로 탭(st.tabs)을 **왼쪽 사이드바 세로 메뉴(st.radio, SELECTED_MENU)**로 이전. 8개 화면 라벨은 기존 탭과 동일 문자열 유지, 각 `with tabX:` 블록을 `if SELECTED_MENU == "라벨":` 가드로 치환(선택된 화면만 렌더 → 매 rerun마다 8탭 전부 그리던 부담도 감소). 사이드바 최상단에 '🧭 메뉴' 배치 → 그 아래 기존 'API 설정'. 라디오 key로 새로고침에도 선택 유지. ⚠ 로컬 파이썬 없어 정적 검토만 — 배포 후 실행 확인 필요.
- v6.28: 탭 정리 — ① 삭제: '🗓️ 소재캘린더'·'📊 누가 검색하나(연령·성별 데이터랩)' 탭 2개(뉴스/이슈 발굴 계열 과다·저활용, IT 검색 롱테일엔 불필요). tab_cal 전용 죽은 데이터 CAL_CATEGORIES(155줄)도 제거. ② 나머지 8탭 '용도별' 재정렬 — [실전]세부글감파기·키워드검증·여러개검증 → [발굴]홈·글감찾기·오늘의소재·AI키워드 → [참고]구글트렌드. st.tabs 언팩 8=8·with블록 8개·잔여참조0 정적검증. ⚠ 로컬 파이썬 없어 정적 검토만 — 배포 후 실행 확인 필요.
- v6.27: 세부 글감/키워드 검증 '판정' 기준 교정(judge_keyword). [문제] 판정이 화면의 '비율(문서수÷검색량)'을 무시하고 '경쟁강도(=검색광고 광고주 경쟁)'를 organic 랭킹 난이도처럼 감점 → 비율 좋은 키워드가 보통, 나쁜 키워드가 합격으로 뒤집혀 보였다(실사례: '아이폰 배터리 성능' 비율 15.4인데 합격 vs '절약' 비율 2.7인데 보통). [교정] ① 비율을 판정 핵심 축으로 반영(<3 +2 / <10 +1 / ≥10 −2) ② 문서수 과다 페널티 강화(≥doc_ok −3) ③ 광고 경쟁강도는 점수에서 제외(상업성 지표라 랭킹과 무관, 안내만). judge_keyword 한 곳 수정으로 '세부 글감 파기'·'키워드 검증' 두 탭 동시 반영. ⚠ 로컬 파이썬 없어 정적 검토만 — 배포 후 실테스트.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import time
import hmac
import hashlib
import re
import html
import base64
import math
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="키워드 찾기", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    /* v7.4 (D-1022-2): 화면 다듬기 — 사장님 "거북이버프 도구 수준의 UI". 기능·판정 그대로, 겉모습만.
       글꼴 Pretendard · 파랑 한 색 · 넓은 여백 · 흰 카드+옅은 그림자 · 알약 버튼 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    :root{
        --accent:#2f6bff; --accent-2:#5b8cff; --accent-strong:#1f4fd6;
        --accent-soft:#eef3ff; --ink:#0f172a; --muted:#64748b; --line:#e6e9ef;
        --bg:#f6f7f9; --card:#ffffff; --shadow:0 1px 2px rgba(15,23,42,.04),0 6px 20px rgba(15,23,42,.06);
    }
    html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select{
        font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif !important; }
    .stApp{ background:var(--bg); }
    /* ---------- 메인 영역 ---------- */
    .block-container{ padding-top:2.6rem; max-width:1100px; }
    .eyebrow{ color:var(--accent); font-weight:700; font-size:.85rem; letter-spacing:.02em; margin-bottom:.35rem; }
    .main-header{ font-size:2.35rem; font-weight:800; letter-spacing:-.03em; color:var(--ink);
        margin:0 0 .4rem; line-height:1.2; }
    .subtitle{ color:var(--muted); margin-bottom:1.8rem; font-size:1rem; }
    h3, h4{ letter-spacing:-.02em; color:var(--ink); }

    /* ---------- 카드: 찾기 폼 · 테두리 상자 · 펼침 ---------- */
    [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"]{
        background:var(--card); border:1px solid var(--line) !important; border-radius:16px !important;
        box-shadow:var(--shadow); padding:1.1rem 1.2rem !important; }
    [data-testid="stExpander"] details{ background:var(--card); border:1px solid var(--line); border-radius:14px; }
    [data-testid="stExpander"] summary{ font-weight:600; }

    /* ---------- 입력칸 ---------- */
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea{
        border-radius:12px !important; font-size:1rem !important; }
    [data-testid="stTextInput"] div[data-baseweb="input"]{ min-height:48px; border-radius:12px; border-color:var(--line); background:#fff; }
    div[data-baseweb="select"] > div{ min-height:48px; border-radius:12px; }

    /* ---------- 버튼 ---------- */
    .stButton>button, .stFormSubmitButton>button, .stDownloadButton>button{
        border-radius:12px !important; font-weight:600; border:1px solid var(--line); background:#fff; color:var(--ink);
        min-height:42px; line-height:1.35; padding:.45rem .8rem; transition:all .12s; }
    .stButton>button p{ font-size:.92rem; word-break:keep-all; }
    .stButton>button:hover, .stFormSubmitButton>button:hover{ border-color:var(--accent); color:var(--accent); background:var(--accent-soft); }
    button[kind="primary"], button[kind="primaryFormSubmit"], [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"]{
        background:var(--accent) !important; border-color:var(--accent) !important; color:#fff !important;
        min-height:48px; border-radius:999px !important; box-shadow:0 4px 12px rgba(47,107,255,.25); }
    button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover, [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stBaseButton-primaryFormSubmit"]:hover{ background:var(--accent-strong) !important; color:#fff !important; }

    /* ---------- 표 ---------- */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"]{ border-radius:14px; overflow:hidden; border:1px solid var(--line);
        box-shadow:var(--shadow); background:#fff; }
    [data-testid="stMetric"]{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:.8rem 1rem; box-shadow:var(--shadow); }
    [data-testid="stCaptionContainer"]{ color:var(--muted); }

    /* ---------- 결과 카드 목록 (v7.4) ---------- */
    .kw-name{ font-weight:700; font-size:1.02rem; color:var(--ink); line-height:1.4; }
    .kw-tag{ display:inline-block; margin-left:.4rem; padding:.05rem .45rem; border-radius:999px; font-size:.72rem; font-weight:600;
        background:#f1f5f9; color:#475569; vertical-align:middle; }
    .kw-meta{ color:var(--muted); font-size:.84rem; margin-top:.15rem; }
    .kw-meta b{ color:var(--ink); }
    .kw-judge{ text-align:right; }
    .pill{ display:inline-block; padding:.2rem .7rem; border-radius:999px; font-size:.8rem; font-weight:700; }
    .pill-ok{ background:#e8f7ee; color:#16803c; } .pill-mid{ background:#fff6e0; color:#a16207; } .pill-no{ background:#fdecec; color:#c62828; }
    .kw-hint{ color:var(--muted); font-size:.74rem; margin-top:.25rem; line-height:1.35; }
    .kw-why{ color:var(--ink); font-size:.8rem; margin-top:.2rem; line-height:1.45; }
    .kw-sep{ border-top:1px solid #eef0f4; margin:.15rem 0; }
    /* 체크 상자도 파랑(기본 빨강 대신) — 배포는 app.py 하나라 테마 파일 대신 CSS로 */
    [data-testid="stCheckbox"] label:has(input:checked) > span:first-child{ background-color:var(--accent) !important; border-color:var(--accent) !important; }

    /* ---------- 사이드바 뼈대 ---------- */
    section[data-testid="stSidebar"]{ background:#ffffff; border-right:1px solid var(--line); }
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{
        display:flex; flex-direction:column; min-height:calc(100vh - 3.5rem); padding-top:.4rem; }
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div:first-child{
        display:flex; flex-direction:column; flex:1 1 auto; }
    /* '설정' 묶음을 하단으로 밀어내는 스페이서 (:has 미지원 브라우저면 그냥 순서상 하단) */
    [data-testid="stElementContainer"]:has(.push-bottom),
    [data-testid="element-container"]:has(.push-bottom){ margin-top:auto; }
    .push-bottom{ height:1px; }

    /* ---------- 브랜드 / 섹션 라벨 ---------- */
    .brand{ display:flex; align-items:center; gap:.55rem; padding:.35rem .2rem 1rem;
        font-weight:800; font-size:1.15rem; color:var(--ink); }
    .brand .logo{ width:34px; height:34px; border-radius:9px; flex:0 0 auto;
        background:linear-gradient(135deg,var(--accent),var(--accent-2));
        display:flex; align-items:center; justify-content:center; color:#fff; font-size:1.05rem; }
    .side-label{ font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
        color:var(--muted); margin:.4rem .2rem .5rem; }

    /* ---------- 라디오 → 세로 내비 메뉴 ---------- */
    section[data-testid="stSidebar"] div[role="radiogroup"]{ gap:.25rem; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label{
        width:100%; margin:0; padding:.55rem .7rem; border-radius:10px; border:1px solid transparent;
        cursor:pointer; transition:background .12s,color .12s; color:#374151; font-weight:600; font-size:.94rem; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover{
        background:var(--accent-soft); color:var(--accent-strong); }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child{ display:none; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked){
        background:var(--accent); box-shadow:0 4px 12px rgba(47,107,255,.25); }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) *{ color:#fff !important; }

    /* ---------- 상태 배지 ---------- */
    .api-status-ok{ background:#ecfdf5; color:#047857; border:1px solid #a7f3d0;
        padding:.4rem .7rem; border-radius:8px; font-weight:600; font-size:.85rem; }
    .api-status-no{ background:#fef2f2; color:#b91c1c; border:1px solid #fecaca;
        padding:.4rem .7rem; border-radius:8px; font-weight:600; font-size:.85rem; }

    section[data-testid="stSidebar"] .stButton>button{ border-radius:8px; }
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
        # v6.15: 키 파라미터만 URL에서 제거(전체 clear 시 cat/stage 선택 저장값까지 날아감)
        for _k in expected:
            if _k in st.query_params:
                del st.query_params[_k]
    else:
        st.session_state.keys_loaded_from_browser = True
        components.html(load_keys_html, height=0)

st.markdown('<div class="eyebrow">네이버 실제 숫자로 판정</div><div class="main-header">키워드 찾기</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">키워드 하나 넣으면 → 세부 키워드와 판정 → 쓸 것만 골라 생성기로</div>', unsafe_allow_html=True)


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
    # ---- 브랜드 ----
    st.markdown(
        '<div class="brand"><span class="logo">🔍</span><span>키워드 찾기</span></div>',
        unsafe_allow_html=True,
    )

    # ---- v7.2 (D-1019-5): 왼쪽 세로 메뉴 — 사장님 "시인성이 안 좋아, 키워드 찾기랑 다른 데서 글감 찾기 항목을 왼쪽에"
    #      (v7.0은 메뉴 없이 한 화면 + 아래 접힌 상자였음 → 접힌 상자 안 가로 버튼이 잘 안 보임) ----
    MENU_MAIN = "🔍 키워드 찾기"
    SRC_OPTIONS = ["자동완성", "연관 키워드"]   # v7.5
    EXTRA_MENUS = ["🗂️ 블로그 운영실", "📰 보도자료", "🗞️ 분야별 뉴스", "🔥 뜨는 키워드", "📋 여러 개 한꺼번에", "📈 구글 트렌드"]
    st.markdown('<div class="side-label">메뉴</div>', unsafe_allow_html=True)
    SIDE_MENU = st.radio("메뉴", [MENU_MAIN] + EXTRA_MENUS, key="side_menu", label_visibility="collapsed")
    if SIDE_MENU == MENU_MAIN:
        st.caption("① 키워드 넣고 찾기 → ② 표에서 쓸 것 체크 → ③ 생성기로 보내기")

    # ---- 아래 '설정'을 사이드바 하단으로 고정 ----
    st.markdown('<div class="push-bottom"></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-label">설정</div>', unsafe_allow_html=True)

    if st.session_state.api_configured:
        st.markdown('<div class="api-status-ok">✅ 네이버 API 연결됨</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="api-status-no">⚠️ API 키 입력 필요</div>', unsafe_allow_html=True)

    with st.expander("⚙️ API 설정", expanded=not st.session_state.api_configured):
        if st.session_state.api_configured:
            st.caption("브라우저에 저장돼 있어요")
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
            st.markdown("---")
        else:
            st.caption("네이버 키를 넣으면 모든 기능이 열려요 (구글 탭은 키 없이 가능)")

        st.caption("**네이버 검색 / 데이터랩** · developers.naver.com")
        client_id = st.text_input("Client ID", value=st.session_state.api_keys.get("client_id", ""), type="password")
        client_secret = st.text_input("Client Secret", value=st.session_state.api_keys.get("client_secret", ""), type="password")

        st.caption("**네이버 검색광고** · searchad.naver.com")
        ad_api_key = st.text_input("Access License", value=st.session_state.api_keys.get("ad_api_key", ""), type="password")
        ad_secret_key = st.text_input("Secret Key", value=st.session_state.api_keys.get("ad_secret_key", ""), type="password")
        ad_customer_id = st.text_input("Customer ID", value=st.session_state.api_keys.get("ad_customer_id", ""))

        if st.button("💾 네이버 키 저장", type="primary", use_container_width=True):
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

# v7.3 (D-1020-1): 키워드 "주인공" 판정 — 그 검색어의 상위를 블로그가 차지하나, 공식 기관·언론이 차지하나.
#   근거: 노출진단_2026-10-20 — 같은 정보글인데 IT 설정·문제 해결(블로그가 주인공) 23/24 노출 vs 정책·지원금(공식 기관이 주인공) 0/20.
#   처음엔 표시만(판정 점수엔 안 넣음) — 실제 노출과 맞춰 본 뒤 반영 여부 결정.
GOV_SUFFIXES = (".go.kr", ".or.kr", ".re.kr", ".mil.kr", "korea.kr", "gov.kr")
OWNER_LABEL = {"gov": "🏛 공식", "news": "📰 언론", "blog": "📝 블로그", "mid": ""}
OWNER_TIP = {
    "gov": "🏛 정부·공공 사이트가 답하는 검색어 — 새 블로그는 어려워요. 새 제도·소문 확인·좁은 상황·직접 해 본 과정으로 좁혀 보세요.",
    "news": "📰 지금 뉴스로 뜨는 검색어 — 빨리 쓰면 기회, 시기가 지나면 끝나요.",
    "blog": "📝 블로그가 답하는 검색어 — 해 볼 만해요.",
    "mid": "",
}


def _host(url):
    try:
        from urllib.parse import urlparse
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def keyword_owner(gov_n, news_total, blog_total, news_recent):
    """검색어의 주인공: gov(공식 기관 3곳 이상) / news(뉴스가 블로그 절반 이상 + 최근 7일 3건 이상) / blog / mid."""
    news_ratio = (news_total / blog_total) if blog_total else (1.0 if news_total else 0.0)
    if gov_n >= 3:
        return "gov"
    if news_ratio >= 0.5 and news_recent >= 3:
        return "news"
    if gov_n <= 1 and news_ratio < 0.2:
        return "blog"
    return "mid"


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
    gov_hosts = []   # v7.3: 웹문서 상위 10개 중 공식 기관 도메인
    for section in ["blog", "cafearticle", "webkr"]:
        try:
            rr = requests.get(f"https://openapi.naver.com/v1/search/{section}.json",
                              headers=search_headers, params={"query": keyword, "display": 10 if section == "webkr" else 1}, timeout=10)
            rr.raise_for_status()
            _j = rr.json()
            counts[section] = _j.get("total", 0)
            if section == "webkr":
                for _it in _j.get("items", [])[:10]:
                    _hst = _host(_it.get("link", ""))
                    if _hst and _hst.endswith(GOV_SUFFIXES) and _hst not in gov_hosts:
                        gov_hosts.append(_hst)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return {"keyword": keyword, "error": "검색 API 인증 실패"}
            counts[section] = 0
        except Exception:
            counts[section] = 0
    
    avg_days, recent_30d, fresh = 999, 0, 0
    top_posts = []  # v6.36: 상위 노출 글(경쟁 상대) — 이미 부르는 blog.json을 재활용(추가 호출 X)
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
        for it in items[:8]:
            pd_str = it.get("postdate", "")
            date_fmt = f"{pd_str[:4]}.{pd_str[4:6]}.{pd_str[6:8]}" if len(pd_str) == 8 else ""
            top_posts.append({
                "title": _strip_tags(it.get("title", "")),
                "blogger": it.get("bloggername", ""),
                "postdate": date_fmt,
                "link": it.get("link", ""),
            })
        if days_list:
            avg_days = sum(days_list) / len(days_list)
            if avg_days <= 30: fresh = 1.0
            elif avg_days >= 365: fresh = 0.0
            else: fresh = max(0, 1 - (avg_days - 30) / 335)
    except Exception: pass
    
    # v7.3: 언론 비중·최신성 (뉴스 검색 1콜 — 총 기사 수 + 최신 10건 중 최근 7일)
    news_total, news_recent = 0, 0
    try:
        rr = requests.get("https://openapi.naver.com/v1/search/news.json",
                          headers=search_headers, params={"query": keyword, "display": 10, "sort": "date"}, timeout=10)
        _nj = rr.json()
        news_total = _nj.get("total", 0) or 0
        from email.utils import parsedate_to_datetime
        _now = datetime.now()
        for _it in _nj.get("items", []):
            try:
                _d = parsedate_to_datetime(_it.get("pubDate", "")).replace(tzinfo=None)
                if (_now - _d).days <= 7:
                    news_recent += 1
            except Exception:
                pass
    except Exception:
        pass
    owner = keyword_owner(len(gov_hosts), news_total, counts.get("blog", 0), news_recent)

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
        "top_posts": top_posts,
        "owner": owner, "gov_hosts": gov_hosts, "news_total": news_total, "news_recent": news_recent,   # v7.3
        "error": None,
    }


# ================================================
# blog_ai_writer 연결용 시드 텍스트 생성 (다리)
# ================================================
# blog_ai_writer의 자막칸(refText)은 100자 이상 텍스트를 받아야
# detectCategory/detectIntent가 작동한다. 분석 결과를 그 칸에 붙일
# 자연스러운 시드 문단으로 변환해준다. blog_ai_writer는 수정하지 않는다.

# v7.1 (D-1019-1): BLOG_PROFILES 삭제 — 정의만 있고 쓰는 곳 없음(Muse AI 리뷰 지적)

# ================================================
# 신규/기존 블로그별 키워드 합격 판정
# ================================================
# v6.27: 판정 축 = 비율(문서수÷검색량)·문서 수·검색량·노출 점수 (전부 organic 신호).
# 광고 경쟁강도는 '상업성'이라 판정 점수에서 뺐다(안내만). 블로그 상태(신규/기존)로 문서수 기준을 다르게 적용.
VERDICT_RULES = {
    # v6.39: 판정 재설계(D-1007-3). 문서 수는 '비율'에 이미 들어 있으므로 절대값은 극단만 본다(이중 감점 제거).
    "신규": {
        "search_min": 100, "search_soft": 300, "search_high": 30000,  # 100 미만 = 수요 없음 / 300 미만 = 롱테일(최대 보통) / 3만 초과 = 넓음
        "doc_huge": 200000,                                           # 문서 20만 이상 = 판이 너무 큼
    },
    "기존": {
        "search_min": 100, "search_soft": 300, "search_high": 100000,
        "doc_huge": 1000000,
    },
}

# v6.15: 블로그명(ioneteam/reviewheart) 분리 → '카테고리 + 단계'를 공통 기준으로 선택.
STAGE_OPTIONS = ["신규", "기존"]   # v6.15: 기타는 신규와 기준이 동일해 제거(블로그 단계는 신규/기존 둘뿐)

def cat_hint_for(category_label):
    """선택한 카테고리 → blog_ai_writer detectCategory용 신호어(시드에 삽입)."""
    code = (category_label or "").split(" ")[0]   # "CAT-D2 · ..." → "CAT-D2"
    if code.startswith("CAT-A"):
        return "스마트폰 갤럭시 아이폰 노트북 앱 컴퓨터 IT"
    if code.startswith("CAT-D"):
        return "육아 자녀 교육 부모"
    return ""

def judge_keyword(result, blog_stage="신규"):
    """키워드가 해당 블로그 단계에 적합한지 등급 + 이유로 판정.
    v6.39 재설계(D-1007-3) — 사장님 "판정 기준 다시 검토":
      [문제1] 검색량이 거의 없어도(예: 50회) 비율·문서수가 좋으면 '합격'이 떴다 → 아무도 안 찾는 글을 추천.
      [문제2] 문서 수를 '비율'과 '절대 문서수'로 두 번 감점 → 검색 5천·문서 4만 같은 쓸 만한 키워드가 불합격.
      [문제3] 노출 점수에 광고 경쟁(25%)·모바일 비중(15%)이 섞여 v6.27 원칙(광고 경쟁은 랭킹 난이도 아님)과 어긋났다.
    [새 기준] ① 수요(검색량): 100 미만 불합격 · 300 미만 최대 보통 · 너무 넓으면 감점
             ② 비율(문서수÷검색량) = 핵심: 1 미만 황금 ~ 30 이상 경쟁 과다
             ③ 절대 문서수는 극단(20만 이상)만 감점
             ④ 상위 글이 오래됐으면(평균 180일+) 새 글이 들어갈 틈 → 가점
             ⑤ 광고 경쟁은 안내만. 노출 점수는 화면 참고용으로만 남기고 판정엔 안 씀."""
    rule = VERDICT_RULES.get(blog_stage, VERDICT_RULES["신규"])
    doc = result.get("blog_count", 0) or 0
    comp = result.get("competition", "")
    search = result.get("monthly_search", 0) or 0
    avg_days = result.get("avg_days")
    ratio = round(doc / search, 1) if search else None  # 표의 '비율'과 동일 계산

    reasons = []
    short = []   # v7.10: 카드에 보일 짧은 이유(같은 분기에서 함께 만든다)
    points = 0
    cap = None  # 수요가 약하면 등급 상한

    # 1) 수요 — 찾는 사람이 있어야 쓴다
    if search < rule["search_min"]:
        cap = "불합격"; reasons.append(f"🔴 검색량 {search:,}회 — 찾는 사람이 거의 없어요")
        short.append((-1, "찾는 사람이 거의 없어요"))
    elif search < rule["search_soft"]:
        cap = "보통"; reasons.append(f"🟡 검색량 {search:,}회 — 작지만 확실한 롱테일 (최대 '보통')")
        short.append((-1, "검색이 적은 롱테일"))
    elif search <= rule["search_high"]:
        points += 1; reasons.append(f"✅ 검색량 {search:,}회 — 적당해요")
        short.append((1, "검색량 적당"))
    else:
        points -= 1; reasons.append(f"🟡 검색량 {search:,}회 — 넓은 키워드 (큰 블로그·언론이 선점) → 세부 키워드 추천")
        short.append((-1, "너무 넓은 키워드라 큰 블로그가 선점"))

    # 2) 비율(문서수÷검색량) — 판정의 핵심
    if ratio is not None:
        if ratio < 1:
            points += 3; reasons.append(f"✅ 비율 {ratio} — 황금 (찾는 사람보다 글이 적어요)")
            short.append((1, "찾는 사람보다 글이 적음"))
        elif ratio < 3:
            points += 2; reasons.append(f"✅ 비율 {ratio} — 수요 대비 경쟁이 적어요")
            short.append((1, "찾는 사람에 비해 글이 적은 편"))
        elif ratio < 10:
            points += 1; reasons.append(f"🟡 비율 {ratio} — 보통")
            short.append((0, "글 수는 보통"))
        elif ratio < 30:
            points -= 1; reasons.append(f"🔴 비율 {ratio} — 글이 검색량보다 10배 넘게 많아요")
            short.append((-1, "글이 검색량의 10배 넘게 많음"))
        else:
            points -= 3; reasons.append(f"🔴 비율 {ratio} — 경쟁 과다")
            short.append((-1, "글이 너무 많아 경쟁 과다"))

    # 3) 절대 문서수 — 극단만
    if doc >= rule["doc_huge"]:
        points -= 1; reasons.append(f"🔴 경쟁 글 {doc:,}개 — 판이 너무 커요")
        short.append((-1, "경쟁 글이 수십만 개"))
    else:
        reasons.append(f"ℹ️ 경쟁 글 {doc:,}개")

    # 4) 상위 글 신선도 — 오래된 글이 자리 차지하면 틈이 있다
    if avg_days is not None:
        if avg_days >= 180:
            points += 1; reasons.append(f"✅ 상위 글 평균 {int(avg_days)}일 전 — 오래된 글이 자리 차지 중, 새 글이 들어갈 틈")
            short.append((1, "상위 글이 오래돼 새 글이 들어갈 틈"))
        elif avg_days <= 30:
            reasons.append(f"ℹ️ 상위 글이 최근 글 위주 (평균 {int(avg_days)}일) — 시기성 키워드라 빨리 쓰는 게 유리")
            short.append((0, "요즘 뜨는 주제라 빨리 쓰면 유리"))

    # 5) 광고 경쟁 — 안내만 (랭킹 난이도가 아니라 상업성)
    #    v7.1: 구매형 키워드에선 '높음' = 돈 되는 주제라는 신호로 안내
    if comp == "높음":
        if is_buy_intent(result.get("keyword", "")):
            reasons.append("💰 광고 경쟁 높음 — 구매형 키워드라 '돈 되는 주제' 신호. 쇼핑커넥트 구매 가이드 후보 (랭킹 난이도와 무관)")
        else:
            reasons.append("ℹ️ 광고 경쟁 높음 — 상업성 있는 키워드 (랭킹 난이도와 무관, 광고 수익엔 +)")

    if points >= 3:
        grade, emoji = "합격", "🟢"
    elif points >= 1:
        grade, emoji = "보통", "🟡"
    else:
        grade, emoji = "불합격", "🔴"
    if cap == "불합격":
        grade, emoji = "불합격", "🔴"
    elif cap == "보통" and grade == "합격":
        grade, emoji = "보통", "🟡"

    return {"grade": grade, "emoji": emoji, "reasons": reasons, "points": points, "short": short}


def why_line(v):
    """v7.10: 카드에 보일 판정 이유 한 줄. 판정을 정한 쪽을 앞에, 반대쪽은 '좋은 점/아쉬운 점'으로."""
    sh = v.get("short") or []
    pos = [t for g, t in sh if g > 0]; neg = [t for g, t in sh if g < 0]; neu = [t for g, t in sh if g == 0]
    if v["grade"] == "불합격":
        out = " · ".join(neg[:2] or neu[:1]) + (f"  (좋은 점: {pos[0]})" if pos else "")
    elif v["grade"] == "합격":
        out = " · ".join(pos[:3]) + (f"  (아쉬운 점: {neg[0]})" if neg else "")
    else:
        lack = neg[:1] or [t for t in neu if t != "요즘 뜨는 주제라 빨리 쓰면 유리"][:1]
        parts = (pos[:1] and ["좋은 점: " + pos[0]]) + (lack and ["아쉬운 점: " + lack[0]])
        out = " · ".join(parts or neu[:2])
    if v["grade"] != "불합격" and "요즘 뜨는 주제라 빨리 쓰면 유리" in neu:
        out += " · 요즘 뜨는 주제라 빨리 쓰면 유리"
    return out


def build_seed_text(result, cat_hint="", sub_keywords=None):
    kw = result.get("keyword", "")

    # v6.14: 검색의도 신호는 '세부/연관 키워드'에서 온다(맨 키워드엔 의도가 없음).
    #   자동완성 세부키워드(신청·언제까지·계좌변경 등 의도어가 풍부)를 우선 쓰고,
    #   없으면 검색광고 연관어로 폴백. 이 키워드들이 시드의 검색의도를 정한다.
    #   (v6.13: 정적 의도 문구(신청·금액·기준·정리) 박던 방식 제거 → 키워드 자신+세부어가 정하게)
    words = [w for w in (sub_keywords or []) if w]
    if not words:
        rel = result.get("related_keywords", []) or []
        words = [r.get("키워드", "") for r in rel if r.get("키워드")]
    rel_words = words[:10]
    # v6.26: 실제 연관어가 있을 때만 그 문장을 넣는다 (없으면 키워드만 반복돼 잡음 + 검색의도 신호 0)
    rel_part = (
        f"{kw} 관련해서 함께 많이 찾는 키워드로는 {', '.join(rel_words)} 등이 있습니다. "
        if rel_words else ""
    )
    cat_part = f"{cat_hint} 분야의 {kw} 정보입니다. " if cat_hint else ""
    seed = (
        f"{kw}에 대해 검색하는 사람들이 많습니다. "
        f"{rel_part}"
        f"이 글에서는 {kw}의 핵심 내용과 궁금한 점을 짚어봅니다. "
        f"{cat_part}"
        f"{kw} 정보를 찾는 분께 도움이 됩니다."
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


# v7.1 (D-1019-1): analyze_demographics 삭제 — 정의만 있고 쓰는 곳 없음(Muse AI 리뷰 지적)


# v7.1 (D-1019-1): CATEGORY_POOLS 삭제 — 정의만 있고 쓰는 곳 없음(Muse AI 리뷰 지적)


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
    # ── IT : 신제품 + 활용·기능 ──
    "CAT-A · IT·스마트폰": [
        "스마트폰 신제품", "갤럭시 기능", "아이폰 업데이트", "스마트폰 활용", "앱 추천",
    ],
    # ── 육아 : 두 딸(유치원·초2) 아빠 컨셉 3개 카드 ──
    "CAT-D1 · 육아·교육": [
        "초등 저학년", "유치원", "받아쓰기", "어린이 영어", "학습지", "초등 입학",
    ],
    "CAT-D2 · 자녀 혜택·정책": [
        "아동수당", "자녀장려금", "교육급여", "아이행복카드", "초등 입학지원금", "다자녀 혜택",
    ],
    "CAT-D3 · 아이와 생활": [
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
# v6.22~23: 오늘의 소재 — 정책브리핑(korea.kr) 보도자료
# ================================================
# 보도자료 시점 = 검색 급증 직전 + 경쟁 글 거의 0인 골든타임.
# v6.23: korea.kr RSS는 2018년에 서비스 중단(피드 주소는 살아있지만 내용이 2018년 화석)
#   → 보도자료 목록 페이지(pressReleaseList.do)가 서버렌더링이라 직접 파싱으로 전환.
#   구조: <a href="/briefing/pressReleaseView..."> <strong>제목</strong>
#         ... <span class="source"><span>2026.07.10</span><span>부처명</span>
# ⚠ korea.kr 개편으로 구조가 바뀌면 아래 fetch_press_releases의 정규식을 수정.

# 제목 신호어 — 이게 없는 보도자료(간담회·행사·인사)는 거른다
RSS_MONEY  = ["지급", "지원금", "환급", "인상", "감면", "공제", "바우처", "수당", "장려금", "급여", "할인", "무료", "혜택"]
RSS_ACTION = ["신청", "접수", "시행", "마감", "확대", "개편", "모집", "도입", "완화", "연장", "시작"]
RSS_TARGET = ["육아", "출산", "아동", "어린이", "다자녀", "자녀", "청년", "주택", "전세", "초등", "유치원", "보육", "부모", "임신", "교육비", "가구"]


def fetch_press_releases(pages=3, timeout=12):
    """정책브리핑 보도자료 목록 크롤링. 페이지당 약 20건, 제목·부처·날짜·링크 추출."""
    import re as _re
    import html as _html
    items, errors = [], []
    for p in range(1, pages + 1):
        try:
            r = requests.get(
                "https://www.korea.kr/briefing/pressReleaseList.do",
                params={"pageIndex": p}, timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            page_html = r.text.replace("\n", " ").replace("\r", " ")
        except Exception as e:
            errors.append(f"{p}페이지 수집 실패: {str(e)[:80]}")
            continue
        blocks = page_html.split('<a href="/briefing/pressReleaseView.do')[1:]
        for b in blocks:
            m_href = _re.match(r'([^"]*)"', b)
            m_title = _re.search(r"<strong>\s*(.*?)\s*</strong>", b)
            m_src = _re.search(r'class="source">\s*<span>([\d.]+)</span>\s*<span>([^<]+)</span>', b)
            if not m_title:
                continue
            title = _html.unescape(_re.sub(r"<[^>]+>", "", m_title.group(1))).strip()
            link = ("https://www.korea.kr/briefing/pressReleaseView.do"
                    + _html.unescape(m_href.group(1))) if m_href else ""
            items.append({
                "부처": (m_src.group(2).strip() if m_src else ""),
                "title": title,
                "link": link,
                "pubDate": (m_src.group(1) if m_src else ""),
            })
        time.sleep(0.2)
    # 제목 기준 중복 제거
    seen, out = set(), []
    for it in items:
        if it["title"] and it["title"] not in seen:
            seen.add(it["title"])
            out.append(it)
    return {"items": out, "errors": errors}


def score_press_item(title, pub_date_str):
    """보도자료 제목 점수화: 돈 +2 / 행동 +1 / 타겟 +2 / 최근성(2일 내 +2, 7일 내 +1)."""
    score, hits = 0, []
    if any(w in title for w in RSS_MONEY):
        score += 2; hits.append("💰돈")
    if any(w in title for w in RSS_ACTION):
        score += 1; hits.append("⚡행동")
    if any(w in title for w in RSS_TARGET):
        score += 2; hits.append("🎯타겟")
    try:
        d = datetime.strptime(pub_date_str, "%Y.%m.%d")   # v6.23: 목록 페이지 날짜 형식
        days = (datetime.now() - d).days
        if days <= 2:
            score += 2
        elif days <= 7:
            score += 1
    except Exception:
        pass
    return score, hits


_RSS_TITLE_NOISE = ["보도자료", "브리핑", "발표", "방안", "계획", "추진", "관련", "개최", "실시", "안내", "위한", "대한", "및",
                    # v6.24: 실운영에서 후보 키워드를 어색하게 만들던 잡음어 보강
                    "보도", "참고", "점검", "운영", "본격", "함께", "모든", "목소리", "재능", "세계", "현장", "정부", "국민"]

def extract_candidate_keywords(title):
    """제목에서 검색해볼 후보 키워드 1~2개.
    기계 추출엔 한계가 있어 어디까지나 '후보' — 최종 선택·검증은 사람이 검증 탭에서."""
    import re as _re
    t = _re.sub(r"[\[\](){}<>‘’“”'\"·,…~]", " ", title)
    words = [w for w in t.split() if len(w) >= 2]

    def _strip_j(w):
        for j in ["으로", "에서", "까지", "부터", "에게", "의", "을", "를", "이", "가", "은", "는", "에", "와", "과", "도", "로"]:
            if len(w) > 2 and w.endswith(j):
                return w[: -len(j)]
        return w

    words = [_strip_j(w) for w in words]
    # v6.24: '알린다·시작한다' 같은 서술형(다로 끝남)은 검색어가 못 됨 → 제외
    words = [w for w in words if len(w) >= 2 and w not in _RSS_TITLE_NOISE and not w.endswith("다")]
    if not words:
        return []
    # 타겟·돈 신호어가 든 단어를 앞으로 (검색어가 될 확률이 높은 명사)
    sig = [w for w in words if any(s in w for s in RSS_TARGET + RSS_MONEY)]
    base = sig + [w for w in words if w not in sig]
    cands = []
    if len(base) >= 2:
        cands.append(base[0] + " " + base[1])
    cands.append(base[0])
    return cands[:2]


def quick_kw_check(kw, keys):
    """후보 키워드 가벼운 실측: 월간검색(광고 API 1콜) + 블로그 문서수(검색 API 1콜) + 비율."""
    out = {"키워드": kw, "월간검색": None, "경쟁": "", "문서수": None, "비율": None}
    rel = get_related_keywords_list(kw, keys, limit=1)
    if not rel.get("error") and rel["keywords"]:
        out["월간검색"] = rel["keywords"][0]["월간검색"]
        out["경쟁"] = rel["keywords"][0]["경쟁"]
    try:
        rr = requests.get(
            "https://openapi.naver.com/v1/search/blog.json",
            headers={"X-Naver-Client-Id": keys["client_id"],
                     "X-Naver-Client-Secret": keys["client_secret"]},
            params={"query": kw, "display": 1}, timeout=10)
        rr.raise_for_status()
        out["문서수"] = rr.json().get("total", 0)
    except Exception:
        pass
    if out["월간검색"] and out["문서수"] is not None:
        out["비율"] = round(out["문서수"] / out["월간검색"], 1)
    return out


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


# v6.40 (D-1014-1): 자음 확장 — "씨앗 + ㄱ~ㅎ"로 자동완성을 여러 번 받아 롱테일을 넓게 모은다.
#   예: "제습기"만 넣으면 8개(구매형)뿐이지만 "제습기 ㅂ"에서 보관·버리는법·분해청소가 나온다.
#   씨앗 자체 자동완성을 맨 앞에 두어(검색 의도가 가장 가까운 것) 시드 문장·생성기 서브 키워드에 먼저 실리게 한다.
AC_CONSONANTS = ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
# v6.41 (D-1014-7): 대비 키워드 — "씨앗 + vs·차이·비교" 자동완성. 대비가 있는 주제(아이폰17 vs 에어 등)에서만 나온다.
AC_CONTRAST = ["vs", "차이", "비교"]
CONTRAST_WORDS = ("vs", "차이", "비교", "장단점", "뭐가 나", "어떤 게")


def is_contrast(kw):
    k = (kw or "").lower()
    return any(w in k for w in CONTRAST_WORDS)


def get_contrast_keywords(seed):
    seed = (seed or "").strip()
    if not seed:
        return []
    head = seed.split()[0]
    out = []
    for suf in AC_CONTRAST:
        q = seed + " " + suf
        res = get_autocomplete_keywords(q)
        if res["error"]:
            continue
        for w in res["keywords"]:
            # 입력한 그대로 되돌아온 것("제습기 차이")은 빼고, 씨앗이 든 진짜 대비어만("차이"로 "차일드락"이 따라오는 것 제외)
            if w.replace(" ", "") == q.replace(" ", ""):
                continue
            if head in w.replace(" ", "") and is_contrast(w) and w not in out:
                out.append(w)
    return out


# v7.1 (D-1019-1): 구매형 키워드 — "씨앗 + 추천·가격·순위·후기" 자동완성. 대비 키워드(AC_CONTRAST)와 같은 방식.
#   용도: 쇼핑커넥트 구매 가이드 키워드 발굴. "비교"는 AC_CONTRAST에 이미 있어 자동완성 확장에선 뺐다(배지 판정에는 포함).
AC_BUY = ["추천", "가격", "순위", "후기"]
BUY_WORDS = ("추천", "가격", "최저가", "할인", "순위", "비교", "후기", "구매")


def is_buy_intent(kw):
    k = (kw or "").lower()
    return any(w in k for w in BUY_WORDS)


def get_buy_keywords(seed):
    seed = (seed or "").strip()
    if not seed:
        return []
    head = seed.split()[0]
    out = []
    for suf in AC_BUY:
        q = seed + " " + suf
        res = get_autocomplete_keywords(q)
        if res["error"]:
            continue
        for w in res["keywords"]:
            # 입력한 그대로 되돌아온 것("갤럭시탭 가격")은 빼고, 씨앗이 든 진짜 구매형만
            if w.replace(" ", "") == q.replace(" ", ""):
                continue
            if head in w.replace(" ", "") and is_buy_intent(w) and w not in out:
                out.append(w)
    return out


def get_autocomplete_expanded(seed, max_total=80):
    seed = (seed or "").strip()
    if not seed:
        return {"error": "빈 키워드", "keywords": []}
    words = []
    first = get_autocomplete_keywords(seed)
    if not first["error"]:
        for w in first["keywords"]:
            if w not in words:
                words.append(w)
    head = seed.split()[0]
    for w in get_contrast_keywords(seed)[:5]:   # v6.41: 대비 키워드를 자음 확장보다 먼저(개수 제한에 잘리지 않게) · 5개까지(세부 글감을 덮지 않게)
        if w not in words:
            words.append(w)
    for w in get_buy_keywords(seed)[:5]:   # v7.1: 구매형 키워드를 대비 다음 순서로 (구매 가이드용) · 5개까지
        if w not in words:
            words.append(w)
    for c in AC_CONSONANTS:
        if len(words) >= max_total:
            break
        res = get_autocomplete_keywords(seed + " " + c)
        if res["error"]:
            continue
        for w in res["keywords"]:
            if head in w.replace(" ", "") and w not in words:
                words.append(w)
    if not words:
        return {"error": "자동완성 결과 없음", "keywords": []}
    return {"error": None, "keywords": words[:max_total]}


def collect_sub_keywords(seed, keys, limit=20, prefer_related=False):
    """
    세부 키워드 수집. 기본은 자동완성(롱테일) 우선, 실패 시 공식 키워드도구 폴백.
    v6.19: prefer_related=True면 공식 연관어(검색광고 키워드도구)를 우선 — 더 많은 연관어(예: 100개)가 필요할 때.
    반환: {"source": ..., "keywords": [...], "error": None|str}
    """
    if not prefer_related:
        ac = get_autocomplete_expanded(seed, max_total=max(limit, 20))   # v6.40 자음 확장
        if not ac["error"] and ac["keywords"]:
            # 씨앗을 포함하는 세부 키워드 우선 (롱테일)
            return {"source": "자동완성(자음 확장)", "keywords": ac["keywords"][:limit], "error": None}

    # 공식 키워드도구 연관어 (prefer_related거나 자동완성 실패 시) — 수백 개까지 가능
    rel = get_related_keywords_list(seed, keys, limit=limit)
    if not rel.get("error"):
        kws = [k["키워드"] for k in rel["keywords"] if k.get("키워드")]
        return {"source": ("공식 연관어" if prefer_related else "공식 연관어(폴백)"), "keywords": kws, "error": None}

    # 공식도 실패: prefer_related였다면 자동완성으로 한 번 더 시도
    if prefer_related:
        ac = get_autocomplete_keywords(seed)
        if not ac["error"] and ac["keywords"]:
            return {"source": "자동완성(폴백)", "keywords": ac["keywords"][:limit], "error": None}
    return {"source": None, "keywords": [], "error": f"세부 키워드 수집 실패 ({rel['error']})"}


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

    if change_pct >= 20:
        arrow, word = "📈", "상승세"
    elif change_pct <= -20:
        arrow, word = "📉", "하락세"
    else:
        arrow, word = "➡️", "유지"
    return {
        "change_pct": change_pct,
        "recent_avg": round(avg_second, 1),
        "series": ratios,          # v6.37: 스파크라인용 최근 90일 주간 추이
        "arrow": arrow, "word": word,
    }



# ================================================
# 메인 영역 - 탭 5개
# ================================================
# ── v6.18: 잘못된 탭 사용이 감지되면 더 맞는 탭을 안내하는 통일 배너 ──
def suggest_tab(reason, target_tab, action=""):
    """reason(왜 이 탭이 안 맞나) + target_tab(추천 탭) + action(거기서 뭘 하면 되나)."""
    msg = f"💡 **{reason}**  \n👉 왼쪽 🔍 키워드 찾기의 검색창에서 찾아보세요"   # v7.0: 탭이 없어져 target_tab은 쓰지 않음
    if action:
        msg += f" — {action}"
    st.warning(msg)


# ================================================
# v6.32: '한 번에 보기' 통합 화면용 헬퍼
# ================================================
def get_active_keys():
    """활성 네이버 키. 우선순위 ① 서버 Secrets(공개형 — 방문자 키 불필요) ② 방문자 입력.
    반환: (keys_dict|None, source: 'server'|'user'|None). 하이브리드라 혼자 쓸 때나 공개할 때나 코드 동일."""
    need = ("client_id", "client_secret", "ad_api_key", "ad_secret_key", "ad_customer_id")
    try:
        sec = st.secrets.get("naver")  # .streamlit/secrets.toml 의 [naver] (없으면 예외/None)
        if sec and all(sec.get(k) for k in need):
            return {k: sec.get(k) for k in need}, "server"
    except Exception:
        pass
    if st.session_state.get("api_configured") and st.session_state.get("api_keys"):
        return st.session_state.api_keys, "user"
    return None, None


def fetch_news_titles_free(query, limit=10):
    """키 없이 뉴스 제목 수집 — 구글 뉴스 RSS(한국어). 반환은 search_news와 동일 형태."""
    import xml.etree.ElementTree as ET
    from urllib.parse import quote
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        return {"error": f"뉴스 수집 실패: {str(e)[:120]}", "news": []}
    out, seen = [], set()
    for item in root.iter("item"):
        t = (item.findtext("title") or "").strip()
        if t and t not in seen:
            seen.add(t)
            out.append({"title": t, "link": item.findtext("link") or "", "pubDate": item.findtext("pubDate") or ""})
        if len(out) >= limit:
            break
    if not out:
        return {"error": "뉴스 결과 없음", "news": []}
    return {"error": None, "news": out}


def quick_reco(monthly, comp):
    """연관어 빠른 추천 판정 (문서수 없이 검색량+광고경쟁만). 블로거 스위트스팟 기준. 정밀판정은 '이걸로 검색'."""
    if not monthly:
        return "·", ""
    if 1000 <= monthly <= 30000 and comp != "높음":
        return "🟢", "추천"
    if monthly > 100000:
        return "🔴", "너무 넓음"
    if monthly < 500:
        return "⚪", "검색량 적음"
    return "🟡", "보통"


def one_search(kw, keys):
    """'한 번에 보기' 검색 1회 = 판정(analyze) + 추이(datalab). 키 없으면 (None, None)."""
    if not keys:
        return None, None
    res = analyze_keyword(kw, keys)
    trend = None
    if res and not res.get("error"):
        try:
            trend = get_trend_direction(kw, keys)  # 데이터랩 1콜 (실패시 None)
        except Exception:
            trend = None
    return res, trend


def one_action_tip(res, grade):
    """판정 카드 아래 '그래서 뭘 하면 되나' 한 줄 (거북이버프식 실행 조언)."""
    search = res.get("monthly_search", 0) or 0
    if grade == "불합격":
        if search >= 30000:
            return "🔴 너무 넓은 키워드예요 — 이걸론 상위노출이 어려워요. 아래 **추천 연관 키워드**에서 세부 글감을 골라보세요."
        return "🔴 경쟁이 세요 — 더 구체적인 세부 키워드로 좁혀보세요 (표의 🟢 추천이나 '이 키워드로 더 파기')."
    if grade == "보통":
        return "🟡 쓸 수는 있어요 — 검색량이 받쳐주면 도전, 아니면 표에서 더 쉬운 걸 골라보세요."
    return "🟢 바로 쓰기 좋아요! 표에서 체크하고 생성기로 보내세요."


# ============ v7.0 화면: 🔍 키워드 찾기 (A안 · 한 화면, D-1014-8) ============
# 사장님 "너무 복잡하고 조잡해 — 사용자 친화적으로" → 메뉴 9개를 한 화면으로.
# 흐름: 키워드 하나 → 세부·롱테일 키워드 판정 표 → 쓸 것 체크 → 생성기로(첫째 = 메인, 나머지 = 서브).
# 옛 '한 번에 보기·세부 글감 파기·키워드 검증·이번 달 글감'이 여기 하나로 합쳐짐. 나머지는 맨 아래 '다른 데서 글감 찾기'.
GRADE_LABEL = {"합격": "🟢 추천", "보통": "🟡 보통", "불합격": "🔴 비추천"}
GRADE_RANK = {"합격": 2, "보통": 1, "불합격": 0}


def _start_search(kw, keep_path=False):
    """검색 시작 (버튼 on_click 콜백 — 위젯 그리기 전에 실행). keep_path=True면 파고들기 경로에 한 단계 추가."""
    kw = (kw or "").strip()
    if not kw:
        return
    st.session_state["main_kw_input"] = kw
    st.session_state["main_pending"] = kw
    path = st.session_state.get("main_path", []) if keep_path else []
    st.session_state["main_path"] = path + [kw]
    st.session_state["main_limit"] = 25


def _more_search(seed):
    """'더 많이 찾기' (콜백) — 같은 키워드를 60개까지 다시."""
    st.session_state["main_kw_input"] = seed
    st.session_state["main_pending"] = seed
    st.session_state["main_limit"] = 60


_jump_to_one = _start_search   # 옛 이름 — 남은 화면의 '🔍 글감' 버튼이 이 이름으로 부른다


def _analyze_retry(kw, keys):
    """판정 1개. 동시에 여러 개를 부르다 API가 잠깐 거절하면 1초 쉬고 한 번 더."""
    r = analyze_keyword(kw, keys)
    if r.get("error") and ("429" in r["error"] or "API 오류" in r["error"]):
        time.sleep(1.0)
        r = analyze_keyword(kw, keys)
    return r


def run_main_search(seed, keys, stage, limit, prefer_related=False):
    """씨앗 → 세부 키워드 수집(자동완성 자음 확장 + 대비, v7.5: 또는 검색광고 연관 키워드) → 판정 → 표 행."""
    sub = collect_sub_keywords(seed, keys, limit=limit, prefer_related=bool(prefer_related and keys))
    words, seen = [seed], {seed.replace(" ", "")}
    for w in (sub.get("keywords") or []):
        if w.replace(" ", "") not in seen:
            seen.add(w.replace(" ", ""))
            words.append(w)
    results = {}
    if keys:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        prog = st.progress(0.0, text=f"'{seed}' 세부 키워드 {len(words)}개 판정 중…")
        with ThreadPoolExecutor(max_workers=3) as ex:
            futs = {ex.submit(_analyze_retry, w, keys): w for w in words}
            for i, f in enumerate(as_completed(futs)):
                w = futs[f]
                try:
                    results[w] = f.result()
                except Exception as e:
                    results[w] = {"keyword": w, "error": str(e)[:80]}
                prog.progress((i + 1) / len(words), text=f"판정 중 ({i + 1}/{len(words)}) {w}")
        prog.empty()
    rows = []
    for w in words:
        r = results.get(w)
        row = {"선택": False, "판정": "—", "키워드": w, "월 검색": None, "경쟁 글": None, "비율": None, "주인공": "", "네이버 광고": "", "_순서": -999}
        if r and not r.get("error"):
            v = judge_keyword(r, stage)
            s = r.get("monthly_search") or 0
            row.update({"판정": GRADE_LABEL[v["grade"]], "월 검색": s, "경쟁 글": r.get("blog_count"),
                        "비율": round(r["blog_count"] / s, 1) if s else None,
                        "주인공": OWNER_LABEL.get(r.get("owner", "mid"), ""),
                        "네이버 광고": r.get("competition") if r.get("competition") in ("높음", "중간", "낮음") else "",   # v7.9
                        "_순서": GRADE_RANK[v["grade"]] * 100 + v["points"]})
        elif r:
            row["판정"] = "⚪ 자료 없음"
            row["_순서"] = -500
        rows.append(row)
    if keys:
        rows.sort(key=lambda x: x["_순서"], reverse=True)
    return {"seed": seed, "rows": rows, "results": results, "source": sub.get("source"), "error": sub.get("error")}


def render_detail(kw, res, keys, stage):
    """'키워드 하나 자세히' — 왜 이 판정인지 · 상위 글 · 검색 추이 · 뉴스 · 더 파기."""
    if res is None and keys:
        res = _analyze_retry(kw, keys)
    if res and not res.get("error"):
        v = judge_keyword(res, stage)
        search = res.get("monthly_search", 0) or 0
        ratio = round(res["blog_count"] / search, 1) if search else None
        st.markdown(f"**{kw}** &nbsp; {GRADE_LABEL[v['grade']]}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("월 검색", f"{search:,}")
        m1.caption(f"PC {res.get('monthly_pc', 0):,} · 모바일 {res.get('monthly_mobile', 0):,}")
        m2.metric("경쟁 글", f"{res.get('blog_count', 0):,}")
        if res.get("competition") in ("높음", "중간", "낮음"):   # v7.9
            m2.caption(f"네이버 광고 경쟁 {res['competition']} (키워드 도구 기준)")
        m3.metric("비율", ratio if ratio is not None else "—")
        m3.caption("경쟁 글 ÷ 월 검색 · 낮을수록 좋아요")
        m4.metric("상위 글 평균", f"{res['avg_days']}일 전" if res.get("avg_days") is not None else "—")
        m4.caption(f"최근 30일 글 {res.get('recent_30d', 0)}개")
        st.info(one_action_tip(res, v["grade"]))
        _ow = res.get("owner", "mid")   # v7.3
        if OWNER_TIP.get(_ow):
            _gh = res.get("gov_hosts") or []
            st.caption(OWNER_TIP[_ow] + f"  (웹문서 상위 10개 중 공식 기관 {len(_gh)}곳" + (": " + ", ".join(_gh[:4]) if _gh else "")
                       + f" · 뉴스 {res.get('news_total', 0):,}건, 최근 7일 {res.get('news_recent', 0)}건)")
        st.markdown("**왜 이 판정인가요?**")
        for rsn in v["reasons"]:
            st.markdown("- " + rsn)
        tops = res.get("top_posts") or []
        if tops:
            st.markdown("**지금 상위에 뜬 글** — 내가 이겨야 할 글")
            for p in tops:
                meta = " · ".join([x for x in [p.get("blogger", ""), p.get("postdate", "")] if x])
                head = f"[{p.get('title', '')}]({p['link']})" if p.get("link") else p.get("title", "")
                st.markdown(f"- {head} <span style='color:#9ca3af;font-size:.8rem;'>{meta}</span>", unsafe_allow_html=True)
            st.caption("상위 글이 오래됐거나 작은 블로그면 비집을 틈이 있어요. 네이버에서 직접 검색해 언론·지식인이 위를 차지했는지도 보세요.")
    elif res and res.get("error"):
        st.warning(f"판정 자료가 없어요 ({res['error']}). 검색량이 아주 적거나 너무 긴 키워드일 수 있어요.")
    elif not keys:
        st.caption("🔑 판정은 네이버 API 키가 있어야 나와요.")

    b1, b2, b3 = st.columns(3)
    b1.button("🪓 이 키워드로 더 파기", key=f"dt_dig_{kw}", on_click=_start_search, args=(kw, True), use_container_width=True)
    show_trend = b2.button("📈 검색 추이", key=f"dt_tr_{kw}", use_container_width=True, disabled=keys is None)
    show_news = b3.button("📰 관련 뉴스", key=f"dt_nw_{kw}", use_container_width=True)
    if show_trend:
        with st.spinner("데이터랩 추이 보는 중…"):
            tr = get_trend_direction(kw, keys)
        if tr:
            st.caption(f"{tr['arrow']} 최근 3개월: **{tr['word']}** ({tr['change_pct']:+.0f}%) — 상승세면 지금이 쓸 타이밍")
            if tr.get("series") and len(tr["series"]) >= 4:
                st.line_chart(pd.DataFrame({"검색 추이": tr["series"]}), height=120)
        else:
            st.caption("추이 자료가 없어요.")
    if show_news:
        with st.spinner("뉴스 모으는 중…"):
            nr = search_news(kw, keys, display=10, sort="date") if keys else {"error": "no-key", "news": []}
            if nr.get("error") or not nr.get("news"):
                nr = fetch_news_titles_free(kw, limit=10)
        if nr.get("error"):
            st.caption(nr["error"])
        for n in nr.get("news", []):
            st.markdown(f"- [{n['title']}]({n['link']})" if n.get("link") else f"- {n['title']}")


keys, key_src = get_active_keys()
if SIDE_MENU == MENU_MAIN:   # v7.2: 왼쪽 메뉴에서 "키워드 찾기"를 골랐을 때만
    if keys is None:
        st.info("🔑 판정(검색량·경쟁 글)은 네이버 API 키가 있어야 나와요 — 왼쪽 **⚙️ API 설정**. 키가 없어도 세부 키워드 목록과 생성기로 보내기는 돼요.")

    # ── ① 검색창 (엔터로도 찾기) ──
    _sv = st.query_params.get("stage", "")
    with st.form("main_search", clear_on_submit=False):
        fc1, fc2, fc3 = st.columns([5.2, 2.6, 1.3])
        in_kw = fc1.text_input("키워드", key="main_kw_input", placeholder="키워드 하나 — 예: 제습기", label_visibility="collapsed")
        in_stage = fc2.selectbox("내 블로그", STAGE_OPTIONS, index=(STAGE_OPTIONS.index(_sv) if _sv in STAGE_OPTIONS else 0),
                                 key="main_stage", label_visibility="collapsed", format_func=lambda s: f"{s} 블로그" if len(s) <= 2 else s,
                                 help="신규 = 아직 작은 블로그. '기존'이면 더 큰 키워드도 추천으로 나와요.")
        go = fc3.form_submit_button("찾기", type="primary", use_container_width=True)
        # v7.5 (D-1022-6): 세부 키워드를 어디서 가져올지
        in_src = st.radio("세부 키워드 가져오기", SRC_OPTIONS, horizontal=True, key="main_src",
                          help="자동완성 = 사람들이 검색창에 실제로 치는 긴 말(기본). 연관 키워드 = 네이버 검색광고 도구가 묶어 주는 말 — 더 넓게 나오고 API 키가 있어야 해요.")
    st.query_params["stage"] = in_stage
    if go and in_kw.strip():
        st.session_state["main_pending"] = in_kw.strip()
        st.session_state["main_path"] = [in_kw.strip()]
        st.session_state["main_limit"] = 25

    # ── ② 찾기 실행 ──
    _pending = st.session_state.pop("main_pending", None)
    if _pending:
        with st.spinner(f"'{_pending}' 세부 키워드 모으는 중…"):
            st.session_state["main_data"] = run_main_search(_pending, keys, in_stage, st.session_state.get("main_limit", 25),
                                                            prefer_related=(st.session_state.get("main_src") == "연관 키워드"))
        if st.session_state.get("main_src") == "연관 키워드" and not keys:
            st.caption("🔑 연관 키워드는 API 키가 있어야 해서 자동완성으로 가져왔어요.")

    # ── ③ 결과 표 → 체크 → 생성기로 ──
    _data = st.session_state.get("main_data")
    if _data:
        _rows = _data["rows"]
        _path = st.session_state.get("main_path") or [_data["seed"]]
        if len(_path) > 1:
            st.caption("🧭 " + "  ›  ".join(_path))
        _n_ok = sum(1 for r in _rows if r["판정"].startswith("🟢"))
        st.markdown(f"#### '{_data['seed']}' 세부 키워드 {len(_rows)}개" + (f" · 🟢 추천 {_n_ok}개" if keys else ""))
        if _data.get("source"):
            st.caption(f"가져온 곳: {_data['source']}")
        if len(_rows) <= 1 and _data.get("error"):
            st.warning("세부 키워드가 안 나와요. 띄어쓰기를 바꾸거나 한 단계 넓은 말로 찾아보세요.")
        _df = pd.DataFrame(_rows).drop(columns=["_순서"])
        _df.insert(3, "비교", _df["키워드"].apply(lambda k: "⚖" if is_contrast(k) else ""))
        _df.insert(4, "구매형", _df["키워드"].apply(lambda k: "💰" if is_buy_intent(k) else ""))   # v7.1
        if not keys:
            _df = _df[["선택", "키워드", "비교", "구매형"]]   # 키가 없으면 판정 칸 없이
        # v7.4 (D-1022-2): 표(data_editor) → 카드 목록. 사장님 "거북이버프 도구 수준 UI" — 판정 알약 배지 + 줄마다 한 줄 설명 + 숫자 한 줄.
        # "1위 시 하루 ~N명" = 월 검색 × 20% ÷ 30 (거북이 검색량 조회기와 같은 어림셈, 계산만이라 속도 영향 없음).
        _HINT = {"합격": "글이 적어 쓰기 좋아요",
                 "보통": "더 구체적으로 좁혀 보세요",
                 "불합격": "글이 많거나 찾는 사람이 적어요"}
        _CLS = {"합격": "ok", "보통": "mid", "불합격": "no"}
        _picked = []
        _sid = re.sub(r"\W", "", _data["seed"])[:20] + f"_{len(_rows)}"
        with st.container(border=True):
            for _i, _r in enumerate(_rows):
                _res = _data["results"].get(_r["키워드"]) or {}
                _g = None; _why = []
                if keys and _res and not _res.get("error"):
                    _v = judge_keyword(_res, in_stage); _g = _v["grade"]; _why = why_line(_v)   # v7.10
                _tags = []
                if is_contrast(_r["키워드"]): _tags.append("⚖ 비교")
                if is_buy_intent(_r["키워드"]): _tags.append("💰 구매형")
                if _r.get("주인공"): _tags.append(_r["주인공"])
                _meta = ""
                if _g:
                    _s = _r["월 검색"] or 0
                    _day = round(_s * 0.2 / 30)
                    _meta = (f"월 검색 <b>{_s:,}</b> · 경쟁 글 {(_r['경쟁 글'] or 0):,} · 비율 {_r['비율'] if _r['비율'] is not None else '—'}"
                             f" · 1위 시 하루 약 <b>{_day:,}명</b>"
                             + (f" · 네이버 광고 경쟁 {_r['네이버 광고']}" if _r.get("네이버 광고") else ""))   # v7.9
                elif keys:
                    _meta = "판정 자료가 없어요 (검색량이 아주 적거나 너무 긴 말)"
                _c1, _c2, _c3 = st.columns([0.45, 6.2, 2.2], vertical_alignment="center")
                if _c1.checkbox("쓸 것", key=f"pk_{_sid}_{_i}", label_visibility="collapsed"):
                    _picked.append(_r["키워드"])
                _c2.markdown(
                    f'<div class="kw-row"><div class="kw-name">{html.escape(_r["키워드"])}'
                    + "".join(f'<span class="kw-tag">{html.escape(t)}</span>' for t in _tags) + "</div>"
                    + (f'<div class="kw-meta">{_meta}</div>' if _meta else "")
                    + (f'<div class="kw-why">왜: {html.escape(_why)}</div>' if _why else "") + "</div>", unsafe_allow_html=True)   # v7.10
                if _g:
                    _c3.markdown(f'<div class="kw-judge"><span class="pill pill-{_CLS[_g]}">{GRADE_LABEL[_g][2:]}</span>'
                                 '</div>', unsafe_allow_html=True)   # v7.10: 뻔한 한 줄 대신 왼쪽에 "왜:" 이유
                if _i < len(_rows) - 1:
                    st.markdown('<div class="kw-sep"></div>', unsafe_allow_html=True)
        _edited = _df
        if keys:
            st.caption("추천부터 보세요. 비율이 낮을수록(1 안팎) 찾는 사람에 비해 글이 적어요. 「1위 시 하루」는 월 검색의 20%로 어림한 숫자예요. 「네이버 광고 경쟁」은 네이버 키워드 도구 값 — 광고주가 많이 붙는 키워드(돈 되는 주제)라는 뜻이고, 블로그 상위 노출 난이도와는 달라요.")

        with st.container(border=True):
            if not _picked:
                st.markdown("**✍️ 생성기로 보내기** — 위 목록에서 쓸 키워드를 체크하세요. 첫째 = 메인 키워드, 나머지 = 서브 키워드.")
            else:
                _main, _subs = _picked[0], _picked[1:]
                st.markdown(f"**✍️ 생성기로 보내기** — 메인 **{_main}**" + (f" · 서브 {', '.join(_subs)}" if _subs else ""))
                _cats = list(CATEGORY_NEWS_QUERIES.keys())
                _saved_cat = st.query_params.get("cat", "")
                _def_idx = _cats.index("CAT-C · 정보·생활정보·꿀팁") if "CAT-C · 정보·생활정보·꿀팁" in _cats else 0
                _cat = st.selectbox("분야 (생성기 카테고리)", _cats, index=(_cats.index(_saved_cat) if _saved_cat in _cats else _def_idx), key="main_cat")
                st.query_params["cat"] = _cat
                _base = _data["results"].get(_main) or {}
                if _base.get("error"):
                    _base = {}
                _seed_text = build_seed_text({**_base, "keyword": _main}, cat_hint_for(_cat), sub_keywords=_subs or None)
                st.code(_seed_text, language=None, wrap_lines=True)
                st.caption("오른쪽 위 📋 복사 → 생성기 '세부 설정 › 자막·참고 자료' 칸에 붙여넣기 → 키워드·서브 키워드·분야가 자동으로 채워져요.")
                if any(is_contrast(k) or is_buy_intent(k) for k in _picked):   # v7.1
                    st.caption("⚖/💰 키워드가 있어요 → 제휴글 후보예요. 상품이 정해져 있으면 생성기 **🛒 제휴글쓰기**에서 상품을 넣어 쓰면 비교표·가격·링크 구조로 나와요.")

        _dc1, _dc2 = st.columns(2)
        _csv = _edited.drop(columns=["선택"]).to_csv(index=False).encode("utf-8-sig")
        _dc1.download_button("📥 표를 CSV로 저장", _csv, file_name=f"키워드_{_data['seed']}_{datetime.now().strftime('%m%d')}.csv",
                             mime="text/csv", use_container_width=True)
        if st.session_state.get("main_limit", 25) < 60:
            _dc2.button("➕ 더 많이 찾기 (최대 60개)", on_click=_more_search, args=(_data["seed"],), use_container_width=True)

        with st.expander("🔎 키워드 하나 자세히 — 왜 이 판정인지 · 상위 글 · 검색 추이 · 뉴스 · 더 파기"):
            _opts = [r["키워드"] for r in _rows]
            _dk = st.selectbox("볼 키워드", _opts, index=(_opts.index(_picked[0]) if _picked and _picked[0] in _opts else 0), key="main_detail_kw")
            render_detail(_dk, _data["results"].get(_dk), keys, in_stage)

# ── ④ 다른 데서 글감 찾기 — v7.2: 왼쪽 메뉴에서 고른 화면을 바로 보여 줌(접힌 상자 없앰) ──
EXTRA_MENU = SIDE_MENU if SIDE_MENU != MENU_MAIN else None
EXTRA_BOX = st.container()

# ============ 탭: 트렌드 대시보드 (메인) ============
if EXTRA_MENU == "🗞️ 분야별 뉴스":
  with EXTRA_BOX:
      if not st.session_state.api_configured:
          st.warning("👈 왼쪽 사이드바에서 네이버 API 키를 먼저 입력해주세요")
      else:
          st.info("""🏠 카테고리별 **지금 뜨는 뉴스·이슈**를 보여줍니다. 카드에서 마음에 드는 이슈를 보면,  
        그 키워드를 왼쪽 🔍 키워드 찾기의 검색창에 넣어 세부 키워드로 쪼개 보세요.  
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
                      st.caption("💡 쓸 이슈의 키워드를 왼쪽 🔍 키워드 찾기의 검색창에")

              for row_start in range(0, len(chosen), 2):
                  pair = chosen[row_start:row_start + 2]
                  cols = st.columns(2)
                  for ci, cat in enumerate(pair):
                      with cols[ci]:
                          with st.container(border=True):
                              render_news_card(cat)

# ============ 탭: 오늘의 소재 (정책 보도자료 RSS → 키워드 발굴) ============
if EXTRA_MENU == "📰 보도자료":
  with EXTRA_BOX:
      st.subheader("📰 오늘의 소재 — 부처 보도자료에서 키워드 발굴")
      st.info("""정책브리핑(korea.kr) **보도자료 목록(전 부처)**을 읽어 돈·행동·타겟 신호어로 거른 뒤,
제목에서 뽑은 **후보 키워드의 검색량·문서수·비율까지 자동 조회**합니다.
보도자료 시점 = 검색 급증 직전 + 경쟁 글 거의 0인 골든타임 · 보도자료 원문 링크는 글 쓸 때 팩트 출처로도 사용
🟢 후보 키워드는 왼쪽 🔍 키워드 찾기의 검색창에서 최종 판정을 확인하고 쓰세요.""")

      if not st.session_state.api_configured:
          st.warning("👈 네이버 API 키가 없으면 수집·필터까지만 하고, 검색량 실측은 건너뜁니다")

      col_r1, col_r2 = st.columns(2)
      with col_r1:
          # 보도자료 대부분은 행정 잡음이라 신호어에 걸리는 건 소수 — 넉넉히 가져온다
          rss_pages = st.selectbox("가져올 목록 페이지 수 (페이지당 약 20건)", [3, 5, 10], index=1, key="rss_pages")
      with col_r2:
          rss_topn = st.selectbox("검색량까지 실측할 상위 소재 수", [5, 8, 12], index=1, key="rss_topn")

      if st.button("📰 보도자료 수집·분석", type="primary", use_container_width=True, key="rss_btn"):
          with st.spinner(f"정책브리핑 보도자료 수집 중 ({rss_pages}페이지)..."):
              res = fetch_press_releases(pages=rss_pages)
          for e in res["errors"]:
              st.warning(f"⚠ {e}")
          all_items = res["items"]

          if not all_items:
              st.error("수집된 보도자료가 없습니다 — korea.kr 페이지 구조가 바뀌었을 수 있어요 (fetch_press_releases 정규식 수정 필요)")
          else:
              st.caption(f"✅ 보도자료 {len(all_items)}건 수집 (전 부처, 최신순)")
              scored = []
              for it in all_items:
                  s, hits = score_press_item(it["title"], it.get("pubDate", ""))
                  # v6.24: 돈 또는 행동 신호가 있어야 통과 — 타겟(청년·자녀 등)만으로는 부족.
                  # ("청년 700명 파견"·"청년의 목소리" 같은 행정 홍보가 타겟+최근성만으로
                  #  상위를 점령하던 문제. 타겟은 가점 역할만.)
                  if s >= 2 and any(h in ("💰돈", "⚡행동") for h in hits):
                      it2 = dict(it)
                      it2["점수"] = s
                      it2["신호"] = " ".join(hits)
                      it2["후보"] = extract_candidate_keywords(it["title"])
                      scored.append(it2)
              scored.sort(key=lambda x: x["점수"], reverse=True)
              st.session_state["rss_all"] = all_items   # 0건일 때 훑어보기 폴백용

              # 상위 N건은 후보 키워드 실측 (광고 API + 블로그 문서수)
              if st.session_state.api_configured and scored:
                  top = scored[:rss_topn]
                  prog2 = st.progress(0)
                  st2 = st.empty()
                  for i, it in enumerate(top):
                      st2.text(f"후보 키워드 실측 중 ({i+1}/{len(top)}): {it['후보'][0] if it['후보'] else '-'}")
                      checks = []
                      for c in it["후보"]:
                          checks.append(quick_kw_check(c, st.session_state.api_keys))
                          time.sleep(0.15)
                      it["실측"] = checks
                      prog2.progress((i + 1) / len(top))
                  st2.empty(); prog2.empty()

              st.session_state["rss_scored"] = scored
              st.caption(f"신호어 필터 통과 {len(scored)}건 / 전체 수집 {len(all_items)}건")

      # 결과 표시 (세션 유지 — 버튼 다시 안 눌러도 남아있음)
      _rss_scored = st.session_state.get("rss_scored", [])
      if _rss_scored:
          _show_n = st.session_state.get("rss_topn", 8)
          st.markdown(f"### 🏆 오늘의 소재 상위 {min(_show_n, len(_rss_scored))}건")
          for it in _rss_scored[:_show_n]:
              with st.container(border=True):
                  st.markdown(f"**[{it['title']}]({it['link']})**")
                  st.caption(f"{it['부처']} · {it.get('pubDate', '')[:16]} · 점수 {it['점수']} · {it['신호']}")
                  if it.get("실측"):
                      for c in it["실측"]:
                          vol, doc, ratio = c["월간검색"], c["문서수"], c["비율"]
                          good = (vol or 0) >= 500 and (doc or 0) < 30000 and c["경쟁"] != "높음"
                          emoji = "🟢" if good else "⚪"
                          vol_s = f"{vol:,}" if isinstance(vol, int) else "?"
                          doc_s = f"{doc:,}" if isinstance(doc, int) else "?"
                          ratio_s = ratio if ratio is not None else "—"
                          st.write(f"{emoji} **{c['키워드']}** — 월 {vol_s}회 · 문서 {doc_s}개 · 비율 {ratio_s} · 네이버 광고 경쟁 {c['경쟁'] or '—'}")
                  elif it.get("후보"):
                      st.write("후보 키워드: " + ", ".join(it["후보"]))

          if len(_rss_scored) > _show_n:
              with st.expander(f"필터 통과 나머지 {len(_rss_scored) - _show_n}건 보기"):
                  for it in _rss_scored[_show_n:]:
                      cand = (" → 후보: " + ", ".join(it["후보"])) if it.get("후보") else ""
                      st.markdown(f"- [{it['title']}]({it['link']}) ({it['부처']} · 점수 {it['점수']}){cand}")

          st.info("🟢 후보를 왼쪽 🔍 키워드 찾기의 검색창에 넣어 판정 확인 → 체크해서 생성기로. "
                  "후보 추출은 기계라 어색할 수 있어요 — 제목을 보고 직접 다듬는 게 더 정확합니다.")
      elif st.session_state.get("rss_all"):
          # 수집은 됐는데 신호어 필터 통과 0건 — 흔한 날 (보도자료 대부분은 행정 잡음)
          st.info("오늘은 돈·육아 신호어에 걸린 보도자료가 없어요. 아래 전체 제목을 훑어보거나, "
                  "왼쪽 🔍 키워드 찾기의 검색창 아래 이번 달 글감을 눌러 보세요.")
          with st.expander(f"수집한 보도자료 전체 제목 훑어보기 ({len(st.session_state['rss_all'])}건)"):
              for it in st.session_state["rss_all"]:
                  st.markdown(f"- [{it['title']}]({it['link']}) ({it['부처']} · {it.get('pubDate', '')})")

# ============ 탭1: 네이버 단일 ============

# ============ 탭2: 네이버 일괄 ============
if EXTRA_MENU == "📋 여러 개 한꺼번에":
  with EXTRA_BOX:
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
                              "블로그수": r["blog_count"], "네이버 광고 경쟁": r["competition"],
                              "모바일%": f"{r['mobile_ratio']*100:.0f}%",
                              "노출점수": r["exposure_score"],
                              "난이도": f"{r['difficulty_emoji']} {r['difficulty']}",
                              "주인공": OWNER_LABEL.get(r.get("owner", "mid"), ""),   # v7.3
                              "공식기관": len(r.get("gov_hosts") or []), "뉴스": r.get("news_total", 0),
                          })
                  df = pd.DataFrame(df_data)
                  st.success(f"✅ {len(results)}개 분석 완료")
                  st.dataframe(df, hide_index=True, use_container_width=True)

                  # v6.18: 후보가 전부 넓은 키워드면 → 세부 글감 파기 추천
                  _ok = [r for r in results if not r.get("error")]
                  if _ok and all(r.get("monthly_search", 0) >= 30000 for r in _ok):
                      suggest_tab(
                          "넣은 키워드가 다 검색량 큰 넓은 단어예요 — 그대로는 경쟁이 세요",
                          "🪓 세부 글감 파기",
                          "각 단어를 거기에 넣어 세부 키워드로 쪼개면 이기기 쉬워져요",
                      )
                  csv = df.to_csv(index=False).encode("utf-8-sig")
                  st.download_button("📥 CSV 다운로드", csv,
                      file_name=f"keyword_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                      mime="text/csv", use_container_width=True)

# ============ 탭3: 구글 트렌드 ============
if EXTRA_MENU == "📈 구글 트렌드":
  with EXTRA_BOX:
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
              # v6.18: 비교 탭인데 1개만 넣었으면 → 단일 분석은 키워드 검증 추천
              if len(kws) == 1:
                  suggest_tab(
                      "구글 트렌드는 '여러 키워드 비교'용이에요 — 1개만 넣으면 비교가 안 돼요",
                      "🎯 키워드 검증 · 쓸까 말까",
                      "이 키워드 1개의 노출 가능성을 보려면 거기서 분석하세요 (아래는 단일 추이만)",
                  )
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

# ============ 탭5: 트렌드 발굴 (신규) ============
if EXTRA_MENU == "🔥 뜨는 키워드":
  with EXTRA_BOX:
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

                      # v6.18: 연관어가 씨앗 1개뿐이면(좁은 단어) → 세부 글감 파기 추천
                      if len(keywords) <= 1:
                          suggest_tab(
                              f"'{seed_kw}'는 연관 키워드가 거의 없는 좁은 단어예요 (검색광고 데이터가 얇음)",
                              "🪓 세부 글감 파기",
                              "이 단어를 넣으면 자동완성으로 세부 키워드(요금·사고·후기 등)가 나와요",
                          )

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
                          df_display = df_display.rename(columns={"트렌드변화": "트렌드", "경쟁": "네이버 광고 경쟁"})   # v7.9
                          # 보기 좋은 순서로 정렬 (관련 열이 있으면 포함)
                          col_order = [c for c in ["키워드", "관련", "월간검색", "네이버 광고 경쟁", "트렌드", "최근관심도"] if c in df_display.columns]
                          df_display = df_display[col_order]
                          st.dataframe(df_display, hide_index=True, use_container_width=True)

                          # CSV 다운로드
                          csv = df.to_csv(index=False).encode("utf-8-sig")
                          st.download_button(
                              "📥 CSV 다운로드", csv,
                              file_name=f"trend_discovery_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                              mime="text/csv", use_container_width=True,
                          )

                          st.caption("💡 '뜨는 키워드'를 왼쪽 🔍 키워드 찾기의 검색창에 넣으면 세부 키워드까지 판정해요.")

# ============ 탭6: 세부 키워드 발굴 ============
# v6.21: 두딸파파 씨앗 풀 — "뭘 넣지?" 결정 피로 제거용 내장 씨앗.
# 위에서부터 순서대로 돌려 쓰면 됨(고민 금지). 소진되면 🤖 AI 키워드 탭에서 리필.
# v6.25: 정체성 확장(자녀 중심 32 → 가정·자녀 경제 55) — 연말정산·청약·청년/신혼 지원·
#        건강보험·연금 카테고리 추가. 투자·투기(주식·코인·ETF·펀드)는 전면 제외,
#        세액공제·제도·절약 앵글만. (네이버 초유딩파파용 = 가족 앵글 있는 돈)
SEED_POOL = [
    "(직접 입력)",
    # ── 정책·수당 ──
    "아동수당", "부모급여", "자녀장려금", "근로장려금", "첫만남이용권", "국민행복카드",
    "양육수당", "교육급여", "아이돌봄서비스", "육아휴직급여", "배우자 출산휴가",
    # ── 출산·양육 신제도 ──
    "신생아 특례대출", "육아기 근로시간 단축급여", "6+6 부모육아휴직제",
    # ── 다자녀 ──
    "다자녀 혜택", "다자녀 국가장학금", "다자녀 자동차 감면", "다자녀 전기요금", "다자녀 KTX",
    # ── 교육·학교 ──
    "초등 입학준비금", "늘봄학교", "방과후학교", "초등 돌봄교실", "유아학비", "교육비 세액공제",
    # ── 연말정산·세금 ──
    "연말정산 자녀공제", "자녀 세액공제", "연말정산 인적공제", "의료비 세액공제",
    "월세 세액공제", "신용카드 소득공제", "산후조리원 세액공제",
    # ── 청약·주거 ──
    "자녀 청약통장", "청년 주택드림 청약통장", "신혼부부 특별공급", "생애최초 특별공급",
    "신혼부부 전세자금대출", "신생아 특례 디딤돌대출",
    # ── 청년·신혼 지원 ──
    "청년도약계좌", "청년월세 특별지원",
    # ── 건강보험·의료 ──
    "건강보험 피부양자", "건강보험료 환급", "본인부담상한제", "영유아 건강검진",
    "어린이 독감 예방접종", "아이 병원비 지원",
    # ── 연금·목돈 (세액공제·제도 앵글만, 투자·종목 제외) ──
    "국민연금 임의가입", "연금저축 세액공제", "노란우산공제", "IRP 세액공제",
    # ── 자녀 자산 ──
    "어린이 통장", "미성년 자녀 증여", "어린이 실비보험",
    # ── 생활 ──
    "지역화폐", "초등 준비물",
]


# ================================================
# v7.6 (D-1027-1): 🗂️ 블로그 운영실 — 내 네이버 블로그 최근 글(RSS) → ① 검색 누락 ② 카테고리·발행 간격 ③ 겹치는 글
#   네이버 블로그는 방문자·유입 통계 API가 없음 → "내 글이 검색에 보이나"까지만 자동. RSS는 최근 50개까지만 줌.
# ================================================
OPS_STOP = {"방법", "정리", "총정리", "사용법", "이유", "확인", "가이드", "해결", "설정", "기준", "신청", "신청방법",
            "정보", "비교", "추천", "후기", "차이", "대상", "조건", "금액", "자격", "한눈", "한눈에", "가지", "3가지",
            "5가지", "확인할", "있는", "하는", "위한", "진짜", "전부", "모음", "대처법", "시점", "경우", "제외", "기간", "방식"}


def _now_kst():
    return datetime.utcnow() + timedelta(hours=9)   # 서버(Streamlit Cloud)는 UTC — RSS 날짜는 한국 시간


def parse_blog_id(s):
    s = (s or "").strip()
    m = re.search(r"blog\.naver\.com/([A-Za-z0-9_-]+)", s)
    return m.group(1) if m else re.sub(r"[^A-Za-z0-9_-]", "", s)


@st.cache_data(ttl=600, show_spinner=False)
def fetch_blog_posts(blog_id):
    """네이버 블로그 RSS(로그인·키 불필요) → 최근 글 최대 50개. 반환: {"name", "posts"} 또는 {"error"}."""
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    try:
        r = requests.get(f"https://rss.blog.naver.com/{blog_id}.xml", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        ch = ET.fromstring(r.content).find("channel")
    except Exception:
        ch = None
    if ch is None:
        return {"error": f"'{blog_id}' 블로그 글 목록을 못 가져왔어요 — 아이디를 확인해 주세요."}
    posts = []
    for it in ch.findall("item"):
        link = (it.findtext("guid") or it.findtext("link") or "").split("?")[0]
        m = re.search(r"/(\d{6,})$", link)
        try:
            d = parsedate_to_datetime(it.findtext("pubDate") or "").replace(tzinfo=None)
        except Exception:
            d = None
        posts.append({
            "title": html.unescape((it.findtext("title") or "").strip()),
            "link": link, "log_no": m.group(1) if m else "", "date": d,
            "category": (it.findtext("category") or "").strip() or "(없음)",
            "tags": [t.strip() for t in (it.findtext("tag") or "").split(",") if t.strip()],
        })
    name = (ch.findtext("title") or "").strip()
    if not name and not posts:   # 없는 아이디도 200 + 빈 channel로 옴
        return {"error": f"'{blog_id}' 블로그를 찾지 못했어요 — 아이디를 확인해 주세요."}
    return {"name": name or blog_id, "posts": posts}


def check_in_search(post, blog_id, keys):
    """제목 그대로 블로그 검색(검색 API 1콜) → 상위 30개 안 내 글 순위. 0 = 안 보임, None = 확인 실패."""
    q = re.sub(r"\s+", " ", re.sub(r"[\"'“”‘’!?~]", " ", post["title"])).strip()
    try:
        rr = requests.get("https://openapi.naver.com/v1/search/blog.json",
                          headers={"X-Naver-Client-Id": keys["client_id"], "X-Naver-Client-Secret": keys["client_secret"]},
                          params={"query": q, "display": 30, "sort": "sim"}, timeout=10)
        rr.raise_for_status()
        items = rr.json().get("items", [])
    except Exception:
        return None
    for i, it in enumerate(items, 1):
        lk = it.get("link", "")
        if post["log_no"] and post["log_no"] in lk:
            return i
        if not post["log_no"] and f"/{blog_id}/".lower() in lk.lower() and _strip_tags(it.get("title", "")) == post["title"]:
            return i
    return 0


def search_status(rank, post):
    if rank is None:
        return "⚠ 확인 실패"
    if rank:
        return f"✅ 보임 ({rank}위)"
    if post["date"] and (_now_kst() - post["date"]).days < 2:
        return "⏳ 기다리는 중"
    return "❌ 안 보임"


def _ops_tokens(post):
    words = set()
    for w in re.findall(r"[0-9A-Za-z가-힣]+", post["title"].lower()):
        if len(w) > 2:
            w = re.sub(r"(으로|에서|에게|까지|부터|은|는|이|가|을|를|의|와|과|도|로|에)$", "", w)
        words.add(w)
    words |= {t.lower() for t in post["tags"]}
    return {w for w in words if len(w) >= 2 and w not in OPS_STOP and not w.isdigit()}


def find_overlaps(posts, limit=15):
    """제목 낱말 + 태그가 겹치는 글 쌍. 블로그 글 20% 넘게 붙은 공통 태그(꿀팁·생활정보 등)는 뺌."""
    toks = [_ops_tokens(p) for p in posts]
    df = {}
    for t in toks:
        for w in t:
            df[w] = df.get(w, 0) + 1
    common = {w for w, c in df.items() if len(posts) >= 10 and c / len(posts) > 0.2}
    out = []
    for i in range(len(posts)):
        for j in range(i + 1, len(posts)):
            a, b = toks[i] - common, toks[j] - common
            shared = a & b
            score = len(shared) / max(1, len(a | b))
            if len(shared) >= 2 and score >= 0.12:
                out.append((score, posts[i], posts[j], sorted(shared)))
    out.sort(key=lambda x: -x[0])
    return out[:limit]


def blog_rhythm(posts):
    """발행 간격 — 최근 7일·30일 글 수, 평균 간격, 가장 긴 공백, 마지막 글 며칠 전."""
    ds = sorted([p["date"] for p in posts if p["date"]], reverse=True)
    now = _now_kst()
    r = {"n7": sum(1 for d in ds if (now - d).days < 7), "n30": sum(1 for d in ds if (now - d).days < 30),
         "last_days": (now - ds[0]).days if ds else None, "avg_gap": None, "max_gap": None}
    if len(ds) >= 2:
        gaps = [((ds[i] - ds[i + 1]).total_seconds() / 86400, ds[i + 1], ds[i]) for i in range(len(ds) - 1)]
        r["avg_gap"] = sum(g[0] for g in gaps) / len(gaps)
        r["max_gap"] = max(gaps, key=lambda g: g[0])
    return r


# ── v7.7 (D-1027-2): 구글 블로그(서치콘솔) — 서비스 계정 열쇠는 Streamlit Secrets [gsc]에만. 부품(google-auth) 없이 RS256 서명 직접 ──
def _der_read(b, i):
    """DER 한 칸 읽기 → (태그, 내용, 다음 위치)."""
    tag, ln = b[i], b[i + 1]
    i += 2
    if ln & 0x80:
        nb = ln & 0x7F
        ln = int.from_bytes(b[i:i + nb], "big")
        i += nb
    return tag, b[i:i + ln], i + ln


def _rsa_key_from_pem(pem):
    """PKCS#8 'BEGIN PRIVATE KEY'(구글 서비스 계정 키 형식) → (n, d)."""
    body = "".join(l for l in pem.strip().splitlines() if "-----" not in l)
    der = base64.b64decode(body)
    _, seq, _ = _der_read(der, 0)                 # PrivateKeyInfo
    i = 0
    _, _, i = _der_read(seq, i)                   # version
    _, _, i = _der_read(seq, i)                   # 알고리즘(rsaEncryption)
    _, rsa, _ = _der_read(seq, i)                 # OCTET STRING → RSAPrivateKey
    _, rseq, _ = _der_read(rsa, 0)
    nums, j = [], 0
    while j < len(rseq) and len(nums) < 4:        # version, n, e, d
        _, v, j = _der_read(rseq, j)
        nums.append(int.from_bytes(v, "big"))
    return nums[1], nums[3]


def _rs256(msg, pem):
    n, d = _rsa_key_from_pem(pem)
    k = (n.bit_length() + 7) // 8
    t = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(msg).digest()
    em = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
    return pow(int.from_bytes(em, "big"), d, n).to_bytes(k, "big")


def _b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def gsc_config():
    """Secrets [gsc] → {"site", "key"} 또는 None."""
    try:
        sec = st.secrets.get("gsc")
        if sec and sec.get("site") and sec.get("key_json"):
            return {"site": sec["site"].strip(), "key": json.loads(sec["key_json"])}
    except Exception:
        pass
    return None


def gsc_token(cfg):
    """서비스 계정 → 구글 접근 토큰(1시간). 세션에 보관."""
    tk = st.session_state.get("gsc_token")
    if tk and tk[1] > time.time() + 60:
        return tk[0]
    key = cfg["key"]
    now = int(time.time())
    head = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = _b64url(json.dumps({"iss": key["client_email"], "scope": "https://www.googleapis.com/auth/webmasters.readonly",
                                "aud": key.get("token_uri", "https://oauth2.googleapis.com/token"),
                                "iat": now, "exp": now + 3600}).encode())
    sig = _b64url(_rs256(f"{head}.{claim}".encode(), key["private_key"]))
    r = requests.post(key.get("token_uri", "https://oauth2.googleapis.com/token"),
                      data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": f"{head}.{claim}.{sig}"}, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"구글 로그인 실패 ({r.status_code}): {r.text[:200]}")
    st.session_state["gsc_token"] = (r.json()["access_token"], now + int(r.json().get("expires_in", 3600)))
    return st.session_state["gsc_token"][0]


def _norm_url(u):
    u = (u or "").split("#")[0].split("?")[0].strip()
    return re.sub(r"^http://", "https://", u).lower()


@st.cache_data(ttl=600, show_spinner=False)
def fetch_blogger_posts(host):
    """구글 블로그(Blogger) 글 피드(키 불필요, 최대 500개) → 운영실 글 모양."""
    try:
        r = requests.get(f"https://{host}/feeds/posts/summary", params={"alt": "json", "max-results": 500},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        feed = r.json()["feed"]
    except Exception:
        return {"error": f"'{host}' 블로그 글 목록을 못 가져왔어요 — 주소를 확인해 주세요."}
    posts = []
    for e in feed.get("entry", []):
        link = next((l["href"] for l in e.get("link", []) if l.get("rel") == "alternate"), "")
        labels = [c.get("term", "") for c in e.get("category", []) if c.get("term")]
        try:
            d = datetime.strptime(e["published"]["$t"][:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            d = None
        posts.append({"title": html.unescape(e.get("title", {}).get("$t", "").strip()), "link": link, "log_no": "",
                      "date": d, "category": labels[0] if labels else "(없음)", "tags": labels})
    return {"name": feed.get("title", {}).get("$t", host), "posts": posts}


def gsc_page_stats(cfg, days=28):
    """서치콘솔 실적: 글(page)별 노출·클릭·평균 순위 + 대표 검색어, 직전 같은 기간 클릭. 데이터는 3일쯤 늦게 들어옴."""
    from urllib.parse import quote
    tok = gsc_token(cfg)
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{quote(cfg['site'], safe='')}/searchAnalytics/query"
    hdr = {"Authorization": f"Bearer {tok}"}
    end = (_now_kst() - timedelta(days=3)).date()
    start, pend = end - timedelta(days=days - 1), end - timedelta(days=days)
    pstart = pend - timedelta(days=days - 1)

    def q(s, e, dims, limit):
        r = requests.post(url, headers=hdr, json={"startDate": str(s), "endDate": str(e), "dimensions": dims, "rowLimit": limit}, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"서치콘솔 실적 오류 ({r.status_code}): {r.text[:200]}")
        return r.json().get("rows", [])

    out = {}
    for row in q(start, end, ["page"], 1000):
        u = _norm_url(row["keys"][0])
        o = out.setdefault(u, {"노출": 0, "클릭": 0, "_pos": 0.0, "전 클릭": 0, "검색어": ""})
        o["노출"] += row.get("impressions", 0)
        o["클릭"] += row.get("clicks", 0)
        o["_pos"] += row.get("position", 0) * row.get("impressions", 0)
    for row in q(pstart, pend, ["page"], 1000):
        u = _norm_url(row["keys"][0])
        out.setdefault(u, {"노출": 0, "클릭": 0, "_pos": 0.0, "전 클릭": 0, "검색어": ""})["전 클릭"] += row.get("clicks", 0)
    best = {}
    for row in q(start, end, ["page", "query"], 5000):
        u = _norm_url(row["keys"][0])
        if row.get("impressions", 0) > best.get(u, (0, ""))[0]:
            best[u] = (row["impressions"], row["keys"][1])
    for u, o in out.items():
        o["순위"] = round(o["_pos"] / o["노출"], 1) if o["노출"] else None
        o["검색어"] = best.get(u, (0, ""))[1]
    return {"rows": out, "range": f"{start.strftime('%m-%d')}~{end.strftime('%m-%d')}"}


def gsc_inspect(cfg, url):
    """URL 검사(구글이 직접 알려 주는 색인 상태). 하루 2,000회까지."""
    try:
        r = requests.post("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
                          headers={"Authorization": f"Bearer {gsc_token(cfg)}"},
                          json={"inspectionUrl": url, "siteUrl": cfg["site"], "languageCode": "ko-KR"}, timeout=20)
        if r.status_code != 200:
            return {"verdict": "ERR", "state": f"확인 실패 ({r.status_code})", "crawl": ""}
        ir = r.json().get("inspectionResult", {}).get("indexStatusResult", {})
        return {"verdict": ir.get("verdict", ""), "state": ir.get("coverageState", ""), "crawl": (ir.get("lastCrawlTime") or "")[:10]}
    except Exception:
        return {"verdict": "ERR", "state": "확인 실패", "crawl": ""}


def gsc_inspect_link(site, url):
    from urllib.parse import quote
    return f"https://search.google.com/search-console/inspect?resource_id={quote(site, safe='')}&id={quote(url, safe='')}"


def render_ops_common(ops_posts):
    """카테고리·발행 간격 / 겹치는 글 — 네이버·구글 공통."""
    _cats = {}
    for p in ops_posts:
        c = _cats.setdefault(p["category"], {"카테고리": p["category"], "글 수": 0, "_last": None})
        c["글 수"] += 1
        if p["date"] and (c["_last"] is None or p["date"] > c["_last"]):
            c["_last"] = p["date"]
    _now = _now_kst()
    return [{"카테고리": c["카테고리"], "글 수": c["글 수"],
             "마지막 글": c["_last"].strftime("%Y-%m-%d") if c["_last"] else "",
             "며칠 전": (_now - c["_last"]).days if c["_last"] else None}
            for c in sorted(_cats.values(), key=lambda c: -c["글 수"])]


if EXTRA_MENU == "🗂️ 블로그 운영실":
  with EXTRA_BOX:
      st.markdown("#### 🗂️ 블로그 운영실")
      OPS_PLATFORMS = ["네이버 블로그", "구글 블로그"]
      _pv = st.query_params.get("ops_pf", "")
      ops_pf = st.radio("블로그 종류", OPS_PLATFORMS, horizontal=True, key="ops_platform", label_visibility="collapsed",
                        index=OPS_PLATFORMS.index(_pv) if _pv in OPS_PLATFORMS else 0)
      st.query_params["ops_pf"] = ops_pf
      _naver = ops_pf == "네이버 블로그"
      if _naver:
          st.caption("내 네이버 블로그 최근 글(최대 50개)을 불러와 ① 검색에 잡혔는지 ② 카테고리·발행 간격 ③ 주제가 겹치는 글을 봐요. "
                     "글 목록은 키 없이 되고, ①만 네이버 키가 필요해요. 방문자·유입 검색어는 네이버가 API를 안 줘서 못 가져와요.")
      else:
          st.caption("구글 블로그 글 전체를 불러와 ① 구글 색인 상태 ② 노출·클릭·검색어 ③ 카테고리·발행 간격 ④ 겹치는 글을 봐요. "
                     "①②는 서치콘솔 연결(Secrets [gsc])이 필요해요.")
      _qk = "blog" if _naver else "gblog"
      with st.form("ops_form", clear_on_submit=False):
          oc1, oc2 = st.columns([5, 1.3])
          ops_in = oc1.text_input("블로그 주소", value=st.query_params.get(_qk, "" if _naver else "www.litince.kr"),
                                  key=f"ops_in_{_qk}", label_visibility="collapsed",
                                  placeholder=("블로그 아이디 — 예: blog.naver.com/ioneteam 이면 ioneteam" if _naver else "블로그 주소 — 예: www.litince.kr"))
          ops_go = oc2.form_submit_button("불러오기", type="primary", use_container_width=True)
      _sk = f"ops_sel_{_qk}"
      if ops_go:
          _bid = parse_blog_id(ops_in) if _naver else re.sub(r"^https?://|/.*$", "", ops_in.strip())
          if _bid:
              st.query_params[_qk] = _bid
              st.session_state[_sk] = _bid
              (fetch_blog_posts if _naver else fetch_blogger_posts).clear()
          else:
              st.warning("블로그 주소를 넣어 주세요")
      if _sk not in st.session_state and st.query_params.get(_qk):
          st.session_state[_sk] = st.query_params.get(_qk)

      ops_bid = st.session_state.get(_sk)
      if ops_bid:
          with st.spinner("글 목록 가져오는 중..."):
              ops_data = fetch_blog_posts(ops_bid) if _naver else fetch_blogger_posts(ops_bid)
          if ops_data.get("error"):
              st.error(ops_data["error"])
          elif not ops_data["posts"]:
              st.warning("가져온 글이 없어요 — 공개 글이 있는지 확인해 주세요.")
          else:
              ops_posts = ops_data["posts"]
              rh = blog_rhythm(ops_posts)
              st.markdown(f"**{ops_data['name']}** · " + (f"blog.naver.com/{ops_bid}" if _naver else ops_bid))
              m1, m2, m3, m4 = st.columns(4)
              m1.metric("불러온 글", f"{len(ops_posts)}개")
              m2.metric("최근 7일", f"{rh['n7']}편", help=f"최근 30일 {rh['n30']}편")
              m3.metric("평균 간격", f"{rh['avg_gap']:.1f}일" if rh["avg_gap"] is not None else "-")
              m4.metric("마지막 글", f"{rh['last_days']}일 전" if rh["last_days"] is not None else "-")

              if _naver:
                  ot1, ot2, ot3 = st.tabs(["🔎 검색 누락", "📂 카테고리·발행 간격", "🔁 겹치는 글"])
                  with ot1:
                      _keys, _ = get_active_keys()
                      _checked = st.session_state.get("ops_check", {}).get(ops_bid)
                      if _keys is None:
                          st.info("🔑 검색 확인은 네이버 키가 있어야 해요 — 왼쪽 **⚙️ API 설정**.")
                      else:
                          st.caption("글 제목 그대로 블로그 검색했을 때 상위 30개 안에 내 글이 있는지 봐요. "
                                     "❌가 며칠째 그대로면 검색 누락일 수 있어요(발행 2일 안 된 글은 ⏳).")
                          if st.button(f"🔎 검색 확인 (글 {len(ops_posts)}개 · 검색 {len(ops_posts)}회)", type="primary", key="ops_check_btn"):
                              from concurrent.futures import ThreadPoolExecutor
                              with st.spinner("검색해 보는 중..."):
                                  with ThreadPoolExecutor(max_workers=3) as ex:
                                      _ranks = list(ex.map(lambda p: check_in_search(p, ops_bid, _keys), ops_posts))
                              _checked = {p["link"]: rk for p, rk in zip(ops_posts, _ranks)}
                              st.session_state.setdefault("ops_check", {})[ops_bid] = _checked
                      _rows = []
                      for p in ops_posts:
                          row = {"날짜": p["date"].strftime("%m-%d") if p["date"] else "", "카테고리": p["category"],
                                 "제목": p["title"], "주소": p["link"]}
                          if _checked is not None:
                              row = {"검색": search_status(_checked.get(p["link"]), p), **row}
                          _rows.append(row)
                      if _checked is not None:
                          _cnt = {}
                          for r in _rows:
                              _cnt[r["검색"][0]] = _cnt.get(r["검색"][0], 0) + 1
                          st.markdown(f"✅ 보임 **{_cnt.get('✅', 0)}** · ❌ 안 보임 **{_cnt.get('❌', 0)}** · "
                                      f"⏳ 기다리는 중 **{_cnt.get('⏳', 0)}** · ⚠ 실패 **{_cnt.get('⚠', 0)}**")
                          _order = {"❌": 0, "⚠": 1, "⏳": 2, "✅": 3}
                          _rows.sort(key=lambda r: _order.get(r["검색"][0], 9))
                      st.dataframe(pd.DataFrame(_rows), hide_index=True, use_container_width=True,
                                   column_config={"주소": st.column_config.LinkColumn("주소", display_text="열기", width="small")})
              else:
                  ot1, ot1b, ot2, ot3 = st.tabs(["🔎 색인 상태", "📈 노출·클릭", "📂 카테고리·발행 간격", "🔁 겹치는 글"])
                  _cfg = gsc_config()
                  with ot1:
                      _ins = st.session_state.get("gsc_inspect", {}).get(ops_bid)
                      if _cfg is None:
                          st.info("🔑 서치콘솔 연결이 필요해요 — Streamlit Secrets에 [gsc] site·key_json을 넣어 주세요.")
                      else:
                          st.caption("구글이 직접 알려 주는 색인 상태예요(서치콘솔 URL 검사, 하루 2,000회까지). "
                                     "❌ 글은 '검사 열기' → 서치콘솔에서 **색인 생성 요청**을 누르세요(요청은 API로 못 해요).")
                          if st.button(f"🔎 색인 확인 (글 {len(ops_posts)}개)", type="primary", key="gsc_inspect_btn"):
                              from concurrent.futures import ThreadPoolExecutor
                              try:
                                  gsc_token(_cfg)
                                  with st.spinner("구글에 물어보는 중..."):
                                      with ThreadPoolExecutor(max_workers=3) as ex:
                                          _res = list(ex.map(lambda p: gsc_inspect(_cfg, p["link"]), ops_posts))
                                  _ins = {p["link"]: r for p, r in zip(ops_posts, _res)}
                                  st.session_state.setdefault("gsc_inspect", {})[ops_bid] = _ins
                              except Exception as e:
                                  st.error(str(e))
                      _rows = []
                      for p in ops_posts:
                          row = {"날짜": p["date"].strftime("%m-%d") if p["date"] else "", "카테고리": p["category"], "제목": p["title"]}
                          if _ins is not None:
                              r = _ins.get(p["link"], {})
                              _ic = {"PASS": "✅", "ERR": "⚠"}.get(r.get("verdict"), "❌")
                              row = {"색인": f"{_ic} {r.get('state', '')}", **row, "마지막 크롤링": r.get("crawl", ""),
                                     "검사": gsc_inspect_link(_cfg["site"], p["link"]) if _cfg else ""}
                          else:
                              row["주소"] = p["link"]
                          _rows.append(row)
                      if _ins is not None:
                          _cnt = {}
                          for r in _rows:
                              _cnt[r["색인"][0]] = _cnt.get(r["색인"][0], 0) + 1
                          st.markdown(f"✅ 색인됨 **{_cnt.get('✅', 0)}** · ❌ 안 됨 **{_cnt.get('❌', 0)}** · ⚠ 확인 실패 **{_cnt.get('⚠', 0)}**")
                          _order = {"❌": 0, "⚠": 1, "✅": 2}
                          _rows.sort(key=lambda r: _order.get(r["색인"][0], 9))
                      st.dataframe(pd.DataFrame(_rows), hide_index=True, use_container_width=True,
                                   column_config={"주소": st.column_config.LinkColumn("주소", display_text="열기", width="small"),
                                                  "검사": st.column_config.LinkColumn("검사", display_text="검사 열기", width="small")})
                  with ot1b:
                      _st = st.session_state.get("gsc_stats", {}).get(ops_bid)
                      if _cfg is None:
                          st.info("🔑 서치콘솔 연결이 필요해요 — Streamlit Secrets에 [gsc] site·key_json을 넣어 주세요.")
                      else:
                          if st.button("📈 최근 28일 실적 가져오기", type="primary", key="gsc_stats_btn"):
                              try:
                                  with st.spinner("서치콘솔에서 가져오는 중..."):
                                      _st = gsc_page_stats(_cfg)
                                  st.session_state.setdefault("gsc_stats", {})[ops_bid] = _st
                              except Exception as e:
                                  st.error(str(e))
                      if _st is not None:
                          _rows = []
                          for p in ops_posts:
                              s = _st["rows"].get(_norm_url(p["link"]), {})
                              _rows.append({"제목": p["title"], "노출": s.get("노출", 0), "클릭": s.get("클릭", 0),
                                            "평균 순위": s.get("순위"), "클릭 변화": s.get("클릭", 0) - s.get("전 클릭", 0),
                                            "대표 검색어": s.get("검색어", ""), "주소": p["link"]})
                          _rows.sort(key=lambda r: (-r["노출"], r["제목"]))
                          _tot_i, _tot_c = sum(r["노출"] for r in _rows), sum(r["클릭"] for r in _rows)
                          _zero = sum(1 for r in _rows if r["노출"] == 0)
                          st.markdown(f"**{_st['range']}** · 노출 **{_tot_i:,}** · 클릭 **{_tot_c:,}** · 노출 0인 글 **{_zero}개**")
                          st.caption("클릭 변화 = 직전 28일보다 늘거나 줄어든 클릭. 서치콘솔 데이터는 3일쯤 늦게 들어와요.")
                          st.dataframe(pd.DataFrame(_rows), hide_index=True, use_container_width=True,
                                       column_config={"주소": st.column_config.LinkColumn("주소", display_text="열기", width="small")})

              with ot2:
                  st.dataframe(pd.DataFrame(render_ops_common(ops_posts)), hide_index=True, use_container_width=True)
                  if rh["max_gap"]:
                      g, d0, d1 = rh["max_gap"]
                      st.caption(f"가장 오래 쉰 때: {d0.strftime('%m-%d')} → {d1.strftime('%m-%d')} ({g:.0f}일) · 불러온 {len(ops_posts)}편 기준"
                                 + ("(RSS는 최근 50개까지만 줘요)" if _naver else ""))

              with ot3:
                  _ov = find_overlaps(ops_posts)
                  if not _ov:
                      st.success("주제가 겹치는 글이 없어요")
                  else:
                      st.caption("제목 낱말·태그가 많이 겹치는 글이에요. 같은 키워드를 노렸다면 서로 순위를 나눠 먹을 수 있어요 — "
                                 "하나로 합치거나 각도를 다르게. 주제만 비슷하고 키워드가 다르면 괜찮아요.")
                      for score, a, b, shared in _ov:
                          with st.container(border=True):
                              st.markdown(f"[{a['title']}]({a['link']})  \n↔ [{b['title']}]({b['link']})")
                              st.caption("겹치는 말: " + " · ".join(shared))


st.markdown("---")
st.caption("💡 키워드 찾기 v7.10 | 네이버 + 구글 + 데이터랩 + 트렌드")
