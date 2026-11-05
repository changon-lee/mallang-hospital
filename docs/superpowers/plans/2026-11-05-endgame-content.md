# 후반 콘텐츠 (신관 · 장비 · 나눔 · 연구 · 트로피) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 대학병원 이후 10~20일을 채우는 돈 쓸 곳(신관 5단계, 장비 레벨, 기부·봉사 진료, 연구 트리, 트로피 홀)을 추가한다.

**Architecture:** 모두 `index.html` 단일 파일 안. 저장 상태 `S`에 새 필드(`eq`, `res`, `annex`, `donated`, `life`, `troph`, `volLast`)를 넣고, 효과는 기존 계산 지점(`treatDur`, `svcDur`, `navInt`, `pay`, `endDay`, `updPatience`)에 곱셈 헬퍼로 한 번만 끼운다. 신관은 지도에 `annex` 카드 하나 + 자체 대기열/슬롯 시뮬레이션(`G.ax`)으로 돌린다.

**Tech Stack:** 바닐라 HTML/CSS/JS, pytest + Playwright(Chromium).

**Spec:** `docs/superpowers/specs/2026-11-05-endgame-content-design.md`

## Global Constraints
- 단일 파일 `index.html`, 외부 라이브러리 없음.
- 세이브 키 `mallang-hospital-v2`, `S.v === 2` 유지. 새 최상위 필드는 `newState()`에 기본값. 중첩 객체는 `startGame`에서 기본값 보정.
- 기존 테스트 전부 통과 유지 (현재 113개). 새 테스트는 `tests/test_endgame.py`.
- 해금: 트로피 처음부터 · 장비 등급1(최대 Lv 3/6/10 for 등급 1/2/3) · 기부·봉사·연구 등급2 · 신관 등급3.
- 수치는 spec 표 그대로 (아래 태스크에 다시 적음).
- 1일차 튜토리얼 흐름 불변.
- 화면 맞춤: 대학병원에서 1440x900, 390x744 모두 `CARDS_FIT`(기존 test_tuning의 겹침/넘침 검사) 통과.

## Review Focus
1. 이어하기 세이브(새 필드 없음) 로드 → 오류 없이 기본값, 누적 트로피 조용히 지급. → Task 1 `test_old_save_loads_with_defaults`.
2. 신관 환자가 남은 채 영업 종료 → 처리될 때까지 하루가 안 끝나고, 특실 환자는 결산 퇴원. → Task 6 `test_day_waits_for_annex_and_suite_discharges`.
3. 아이 환자(🧸)를 진료과로 보냄 → 말풍선만, 벌점·콤보 끊김 없음. → Task 6 `test_child_to_dept_is_gentle`.
4. 장비·연구 효과 중복 적용(같은 곱이 두 번) → 정확한 배율. → Task 2 `test_eq_speed_and_fee_exact`, Task 4 `test_research_effects_exact`.
5. 봉사 진료의 날에 수납 0원이지만 콤보 보너스·평판 보너스도 0, 일급은 나감. → Task 3 `test_volunteer_day_zero_income_wages_paid`.

---

### Task 1: 상태 필드 + 수입 배율 + 🏆 트로피 홀

**Files:**
- Modify: `index.html` (newState, startGame, pay, endDay, showPrep, act, 새 TROPHY 블록)
- Test: `tests/test_endgame.py` (새 파일)

**Interfaces:**
- Produces:
  - `newState()` 새 필드: `eq:{}`, `res:{done:{},cur:null}`, `annex:{lv:0,build:null}` (`build` = `{stage, left}`), `donated:0`, `volLast:-99`, `life:{maxCombo:0,emergOk:0,karenCalm:0,vip:0,heli:0,bestDay:0,perfectDays:0,volDays:0}`, `troph:{}`.
  - `incomeMul(): number` = `repMul() * trophyMul() * resFeeMul()` — 이후 모든 수입 계산은 이것만 쓴다. `resFeeMul`은 Task 4 전까지 `() => 1`.
  - `trophyMul(): number` = `1 + 0.01 * trophyCount()`.
  - `TROPHIES: Array<{id, icon, name, desc, check:()=>bool, prog?:()=>[cur,max]}>` (spec 28개, 순서 그대로).
  - `checkTrophies(silent=false): string[]` — 새로 얻은 id 목록, `S.troph[id]=S.day` 기록, silent 아니면 토스트.
  - `showTrophies()`, act `'trophy'`, 준비 화면 버튼 `data-act="trophy"`.
  - `G.stats.trophBonus` 누적, 결산 줄 "🏆 트로피 보너스 (포함)".
  - `S.life` 갱신 지점: pay(vip), angry 아님/응급 구조(`emergOk`), calmKaren(`karenCalm`), 결산(`bestDay`=그날 income 최대, `perfectDays`), `maxCombo`.

- [ ] **Step 1: Write failing tests** in `tests/test_endgame.py`:
  - `test_new_state_has_endgame_fields`: `js("[S.eq, S.res.cur, S.annex.lv, S.donated, S.life.heli, Object.keys(S.troph).length]") == [{}, None, 0, 0, 0, 0]`.
  - `test_old_save_loads_with_defaults`: localStorage에 새 필드 없는 v2 세이브(`grade:2, total:250, depts 6개`) 저장 → `#tCont` 클릭 → 오류 없음, `S.res.done == {}`, `S.troph`에 `t100`(누적 100)·`grade1`·`grade2` 있음, `.toast`에 "트로피" 없음(silent).
  - `test_trophy_count_and_mul`: `TROPHIES.length == 28`; `S.troph={a:1,b:2,c:3}` → `trophyMul() == 1.03`.
  - `test_pay_uses_trophy_mul`: rep 30(티어 없음), 트로피 10개 강제 → `pay` 대상 환자 fee 100, pat 0, 비VIP → 받은 돈 `round(100*1.10)` = 110, `G.stats.trophBonus == 10`.
  - `test_combo_trophy_instant`: `G.combo=19` 후 pay 한 번 → `S.troph.combo20` 존재, 토스트 "🏆".
  - `test_trophy_hall_shows_locked_and_owned`: `showTrophies()` → `.troph.own` 1개 이상(첫 치료 후), `.troph.lock` 존재, 진행도 텍스트 "/".
- [ ] **Step 2:** `pytest tests/test_endgame.py -q` → 6 FAIL (`TROPHIES is not defined` 등).
- [ ] **Step 3:** 구현. trophy id는 `first,t100,t500,t1000,combo20,combo40,day5k,day10k,day20k,perfect,emerg10,emerg50,karen20,vip30,grade1,grade2,grade3,alldept,legend,donate10k,vol3,res6,resAll,eq10,annex1,annexAll,heli10,staff15`. `pay`와 `endDay`(자동 수납·입원 퇴원)의 `repMul()`를 `incomeMul()`로 바꾸고, 기존 `repBonus`는 rep 몫, `trophBonus`는 트로피 몫으로 분리 집계(`base*repMul` 대비 차이). `checkTrophies()`는 pay 직후(콤보·누적)와 `endDay` 끝, `startGame`에서 silent로 호출. 트로피 홀: `.modal.wide` 안 `.tgrid` 격자, 각 `.troph.own|.lock`.
- [ ] **Step 4:** `pytest -q` → 전체 통과 (113 + 6).
- [ ] **Step 5:** Commit `feat: trophy hall with permanent fee bonus`.

### Task 2: ⚙️ 장비 레벨

**Files:** Modify `index.html` (EQ 블록, treatDur, svcDur, pay/svcStep 수수료, showShop, buy). Test `tests/test_endgame.py`.

**Interfaces:**
- Consumes: Task 1 `incomeMul`.
- Produces:
  - `EQ_TARGETS(): string[]` — 열린 진료과 + 열린 `exam,inj,pharm,surg` + 완공된 신관 칸 id(`peds,er,rehab,suite,heli`; Task 5 전엔 없음).
  - `eqLv(id): number` (`S.eq[id]||0`), `eqMax(): number` = `[0,3,6,10][S.grade]`.
  - `eqPrice(id, lv): number` = `round(base*1.45**lv/10)*10`, base = 진료과 `250+DEPT_ORDER.indexOf(id)*40`, 방 300, 신관 600.
  - `eqSpd(id): number` = `1+0.06*eqLv(id)`, `eqFee(id): number` = `1+0.03*eqLv(id)`.
  - `eqName(id, lv)`: exam이면 Lv1~3 'X-ray', 4~6 'CT', 7~10 'MRI'; 그 외 `'★'+lv`.
  - buy key `eq:<id>`; 상점 탭 `'eq'` ("⚙️ 장비"), 진료과·방·설비 다음 순서.
  - `UPS.clinic.name` → `'진료실 기본 장비'`.
- [ ] **Step 1: Failing tests:**
  - `test_eq_locked_by_grade`: grade 0 → `eqMax()==0`, `buy('eq:int')` 무변화; grade 1 `S.eq.int=3` → 추가 구매 불가.
  - `test_eq_price_curve`: `eqPrice('int',0)==250`, `eqPrice('int',9)==round(250*1.45**9/10)*10`, `eqPrice('exam',0)==300`.
  - `test_eq_speed_and_fee_exact`: grade 3, `S.eq.int=5`, 의사 spd 2, clinic 0 → `treatDur('int') == 7/(0.5+0.5)/1/1.3` (±1e-9); 내과 진료 끝난 환자 `p.fee == round?` — 수수료는 `DEPTS.int.fee * eqFee('int')` = 30*1.15 = 34.5 (fee는 소수 허용, 기존과 동일하게 반올림 없이 누적) → `p.fee == 34.5`.
  - `test_eq_room_speed`: `S.eq.exam=4` → `svcDur('exam') == 3.5/1.24`; `S.eq.surg=2` 수술 수수료 `(120+S.day*3)*1.06`.
  - `test_eq_tab_shows_now_next`: `showShop('eq')` → 카드 텍스트에 "→", exam 카드에 "X-ray".
- [ ] **Step 2:** 실행 → FAIL.
- [ ] **Step 3:** 구현. `treatDur`: 마지막에 `/ eqSpd(r)`. `svcDur(r)`: 결과 `/ eqSpd(r)` (튜토리얼 값은 제외). `svcStep`: 진료과 수수료 `* eqFee(r)`, 수술 `* eqFee('surg')`. 상점 카드: tag `Lv.n/max`, desc "지금 → 다음" (진료과: 진료 시간 초·진료비, 방: 처리 시간), 잠김은 `priceState` 재사용(등급 1 미만이면 승급 안내, 최대치면 'MAX ✨').
- [ ] **Step 4:** `pytest -q` 통과.
- [ ] **Step 5:** Commit `feat: per-room equipment levels`.

### Task 3: 🤝 기부 · 봉사 진료의 날

**Files:** Modify `index.html` (GIVE 블록, showPrep, act, pay, breakCombo, spawnInterval, endDay, HUD). Test `tests/test_endgame.py`.

**Interfaces:**
- Consumes: Task 1 `S.donated`, `S.volLast`, `S.life.volDays`, `checkTrophies`.
- Produces:
  - `DONATE = { small:{icon:'💝',name:'작은 기부',base:500,per:20,rep:2}, big:{icon:'💐',name:'큰 기부',base:1500,per:50,rep:5}, fund:{icon:'🏛️',name:'장학 재단',base:4000,per:120,rep:10} }`, `donateCost(id) = base + S.day*per`.
  - `G.donated` (오늘 기부액, 하루 1회 판정), `G.vol: bool`.
  - `donate(id)`, `startVolunteer()`; act `give:<id>`, `vol`. 준비 화면 `giveBoxHTML()` (등급 2 미만이면 '').
  - `volReady(): bool` = `S.day - S.volLast >= 3`.
- [ ] **Step 1: Failing tests:**
  - `test_donate_once_per_day`: grade 2 day 10 money 1e4 rep 50 → `act('give:big')` → money `-= 1500+500`, rep 증가 > 0, `S.donated == 2000`; 두 번째 `act('give:small')` 무변화; grade 1에선 무변화.
  - `test_volunteer_cooldown`: `act('vol')` → `G.vol` true, `S.volLast == S.day`; 다음 날 prep에서 `volReady()` false, 3일 뒤 true.
  - `test_volunteer_day_zero_income_wages_paid`: 봉사의 날 시작, 환자 fee 100 pay(vip true, combo 4→5) → money 변화 0, `G.stats.income == 0`; 결산 후 money = 시작 - 일급합계, 결산 텍스트에 "봉사 진료".
  - `test_volunteer_rep_and_combo`: 봉사의 날 pay 1명 rep 증가량 == `addRep(1.0)` 해당값(테스트에서 같은 식으로 계산), `comboPenalty` 감점 절반; `spawnInterval` 기대값 `/1.3` (Math.random 고정).
- [ ] **Step 2:** FAIL 확인.
- [ ] **Step 3:** 구현. `pay`: `G.vol`이면 total 0, 콤보 보너스 0, 대신 `addRep(1.0)`(VIP/진상 1.5는 유지 max). `breakCombo`: `G.vol`이면 pen/2. `spawnInterval`: `G.vol`이면 `/1.3`. `endDay`: 봉사면 자동 수납·퇴원비 0, `addRep(5)`, `S.life.volDays++`, 결산 줄 "🤝 봉사 진료의 날 평판 +x"; 기부는 결산 줄 "🤝 기부 -💰n" (오늘 기부액, 순이익에 반영). HUD: `#hVol` 작은 칩 "🤝 봉사" (봉사의 날만).
- [ ] **Step 4:** `pytest -q` 통과.
- [ ] **Step 5:** Commit `feat: donations and volunteer day`.

### Task 4: 🧪 의학 연구

**Files:** Modify `index.html` (RESEARCH 블록, showPrep, act, endDay/prepDay, 효과 지점). Test `tests/test_endgame.py`.

**Interfaces:**
- Consumes: Task 1 `S.res`, `incomeMul`; Task 2 `treatDur/svcDur`.
- Produces:
  - `RESEARCH = [{id, br:'med'|'ops'|'ax', step:1..4, name, icon, cost, days, desc}]` — spec 표 12개. id: `diag, exam2, drug, surg2, kind, smart, fatigue, mgmt, play, erp, robot, concierge`.
  - `hasRes(id): bool`, `resAvail(r): bool` (등급 2 이상, 같은 갈래 이전 단계 완료, `ax` 갈래는 등급 3 + `S.annex.lv >= step`, 진행 중 없음, 돈 충분), `startRes(id)`, act `res:<id>`, `showResearch()` + act `lab`.
  - 결산: `S.res.cur.left--`, 0이면 `done[id]=S.day`, 다음 prep에서 토스트 "🧪 연구 완료!" (`S.res.justDone`).
  - 효과 헬퍼 (Task 1의 `resFeeMul` 교체): `resFeeMul()` = mgmt ? 1.10 : 1.
  - 효과 지점: `treatDur` ×0.9(diag); `svcDur('exam')` ×0.7(exam2); `svcStep` ❓ 도박 성공률 0.5→0.65(exam2); `svcDur('pharm')` ×0.75(drug); `svcDur('surg')` ×0.7 + 수술비 ×1.3(surg2); `updPatience` 감소 ×0.92(kind); `navInt` ×0.8(smart); `work()` 피로 ×0.75(fatigue); `emergLimit` +8(erp). `ax` 갈래 효과는 Task 6에서 읽음: `axCap(id)`/`axDur(id)`.
- [ ] **Step 1: Failing tests:**
  - `test_research_gating`: grade 1 → `startRes('diag')` 무변화; grade 2 → 시작, money -3000, `S.res.cur == {id:'diag', left:1}`; 진행 중 `startRes('kind')` 무변화; `exam2`는 diag 완료 전 불가.
  - `test_research_completes_after_days`: diag 시작 → 하루 자동 진행(AUTO 없이 `G.t=181; update(.1)` 패턴, test_spend 참조) → `hasRes('diag')`, 다음 prep 토스트 "연구 완료".
  - `test_research_effects_exact`: 각 효과 하나씩 강제(`S.res.done.X=1`) 후 수치 비교: treatDur ×0.9, svcDur exam 3.5*0.7, pharm ×0.75, navInt ×0.8, emergLimit +8, pay 수입 ×1.10 (mgmt).
  - `test_ax_branch_needs_annex`: grade 3, `S.annex.lv=0` → `play` 불가; `lv=1` → 가능.
  - `test_lab_window_lists_branches`: `showResearch()` 텍스트에 "진료", "운영", "신관", "→".
- [ ] **Step 2:** FAIL 확인.
- [ ] **Step 3:** 구현. 결산 줄 "🧪 연구비 -💰n"(그날 시작한 연구 비용). 연구 창: 갈래 3열(좁은 화면 1열), 각 노드 상태(완료 ✅ / 진행 중 ⏳n일 / 가능 버튼 / 잠김 🔒).
- [ ] **Step 4:** `pytest -q` 통과.
- [ ] **Step 5:** Commit `feat: medical research tree`.

### Task 5: 🏗️ 신관 공사 + 지도 카드

**Files:** Modify `index.html` (ANNEX 블록, LAYOUT 등급3, cardHTML/cardClass, ROOMS, showPrep, act, endDay/prepDay, CSS). Test `tests/test_endgame.py`.

**Interfaces:**
- Consumes: Task 1 `S.annex`, `checkTrophies`.
- Produces:
  - `ANNEX = [{id:'peds',icon:'👧',name:'소아과',cost:8000,days:3,upkeep:200}, {id:'er',icon:'🚑',name:'응급실',cost:14000,days:3,upkeep:300}, {id:'rehab',icon:'🦿',name:'재활치료실',cost:20000,days:4,upkeep:350}, {id:'suite',icon:'💎',name:'VIP 특실',cost:28000,days:4,upkeep:450}, {id:'heli',icon:'🚁',name:'헬기장',cost:38000,days:5,upkeep:600}]`.
  - `axBuilt(id): bool` (= `ANNEX.findIndex(a=>a.id===id) < S.annex.lv`), `rushCost(): number` = `ceil(ANNEX[stage].cost*0.35)`.
  - `startBuild()`, `rushBuild()`; act `axBuild`, `axRush`, `annex` (창 열기). 착공·단축은 `G.mode==='prep'`일 때만.
  - `S.annex.build = {stage, left}`; 결산에서 `left--`; `left<=0`이면 다음 prep에 `S.annex.lv++`, `build=null`, 축하 모달(`showAnnexDone`) + `checkTrophies`. 단축으로 0이 되면 즉시 완공.
  - 결산 줄 "🏗️ 공사비 -💰n"(그날 낸 착공비+단축비), "🏥 신관 운영비 -💰n" (= 완공 칸 upkeep 합).
  - 지도: `ROOMS.annex = {name:'신관', icon:'🏥'}`; 등급 3 레이아웃 wide/narrow에 `annex` 추가(세로 3칸 또는 가로 1줄, 빌더 판단), `cardHTML('annex')` → `.axslots` 안에 칸 5개 `.axs[data-ax=id]` (미완공 `.off` 🏗️, 공사 중이면 `⏳n일`). 카드 톡 → `showAnnex()` (영업 중엔 `G.modal=true` 정보 전용).
  - 대학병원 레이아웃 변경으로 기존 `test_grade3_map_has_all_rooms`의 `ALL`에 `'annex'` 추가.
- [ ] **Step 1: Failing tests:**
  - `test_annex_card_only_at_grade3`: grade 2 → `.card[data-room=annex]` 없음; grade 3 → 있음, `.axs.off` 5개.
  - `test_build_and_rush`: grade 3 money 1e5 prep → `act('axBuild')` money -8000, `S.annex.build == {stage:0,left:3}`; `act('axRush')` money -2800, left 2; 두 번 더 → `S.annex.lv == 1`, build null, `.axs[data-ax=peds]:not(.off)`.
  - `test_build_progresses_daily_and_upkeep`: 착공 후 결산 3번(빈 하루) → lv 1; 그 다음 결산 텍스트 "신관 운영비" 와 "-💰200".
  - `test_annex_fits_screen`: grade 3 lv 5, 1440x900 과 390x744에서 기존 `CARDS_FIT` 헬퍼(test_tuning) 통과, `--pz` ≥ 대학병원 현재 값의 85% (먼저 main 기준값을 측정해 상수로 고정).
  - `test_build_blocked_during_play`: play 중 `act('axBuild')` 무변화.
- [ ] **Step 2:** FAIL 확인.
- [ ] **Step 3:** 구현 (위 Produces). 신관 창: 단계 5줄(완공 ✅ / 공사 중 진행 막대 + 하루 단축 버튼 💰 / 다음 착공 버튼 / 잠김), 칸별 정원·처리 시간(Task 6 이후 값)·오늘 수입.
- [ ] **Step 4:** `pytest -q` 통과.
- [ ] **Step 5:** Commit `feat: annex construction and map card`.

### Task 6: 신관 칸 운영 (새 환자 5종)

**Files:** Modify `index.html` (spawn, register, rollDest, sendTo, validRooms, update 루프, updPatience, endDay, ANNEX 런타임, CSS). Test `tests/test_endgame.py`.

**Interfaces:**
- Consumes: Task 5 `ANNEX`, `axBuilt`; Task 4 `hasRes` (`play, erp, robot, concierge`); Task 2 `eqSpd/eqFee` (신관 칸 id 사용); Task 1 `incomeMul`, `S.life.heli`.
- Produces:
  - `G.ax = { [id]: { q: Patient[], slots: (Patient|null)[] } }` (prepDay에서 생성), `G.stats.annexIncome`.
  - `axCap(id)`: peds `1+play`, er 1, rehab `1+robot`, suite `2+concierge`, heli 1.
  - `axDur(id)`: peds 6, er 8 ×(erp?0.7:1), rehab 7, heli 10 — 모두 `/ eqSpd(id)`.
  - `axFee(p, id)`: peds 70, er `90 + extraPay(p)`, rehab 60 — 모두 `* eqFee(id)`; heli `(400+S.day*10)*eqFee('heli')` 자동 수납(`*incomeMul()`); suite는 결산 때 `(입원 퇴원비)*2*(concierge?1.3:1)`.
  - `toAnnex(p, id)`: 환자를 신관 카드로 `place` 후 `.ax-in` 클래스로 숨김, `p.loc='annex'`, `p.stage='annex'`, 큐에 넣음. 끝나면 `p.fee += axFee`, `p.stage='pay'`, `toCash(p)` 다시 보이기 (heli는 즉시 수납·제거, suite는 `stage='ward'` 유지).
  - 환자 필드: `p.child` (🧸, 등급3·peds 완공 시 15%), `p.amb` (구급차, er 완공 시 하루 +2 `G.ambTimes`), `p.heli` (heli 완공 시 하루 1~2 `G.heliTimes`), `p.axWant` (자동 이동할 칸 id), `p.axT` (자동 이동 시각 = G.t+2).
  - `rollDest`: rehab 완공 시 `ort/neu/surg` 이후 `['rehab',2]` 추가; `DEST.rehab='🦿'`. VIP + suite 완공: dest가 ward면 suite, 아니면 30%로 suite.
  - 자동 이동: `updAnnex(dt)`에서 `p.axWant && G.t>=p.axT` → `toAnnex`. 원장님이 신관 카드로 보내면(`sendTo(p,'annex')`) 즉시. 기존 응급 환자(`p.emerg && !p.saved`)를 신관으로 보내면 er 완공 시 `p.saved=true` 처리 + 응급실 큐 맨 앞.
  - 하트: 신관 대기 중 ×0.5; 아이 ×1.3, `p.pat < (play?20:30)`이면 `p.cry=true` (😭 말풍선) → 다른 대기 환자 감소 ×1.2. 헬기 대기 중 화남 → 평판 -6.
  - 📥: 칸 대기 ≥ 정원+2면 `.axs` 안 `.backlog`.
  - 마감: `update`의 남은 환자 집계에 신관 환자 포함(suite 제외), `endDay`에서 suite 환자 퇴원 처리 → `annexIncome` 가산.
  - 결산 줄 "🏥 신관 수입 +💰n".
- [ ] **Step 1: Failing tests:**
  - `test_child_flow`: lv 1, `spawn(true,{child:true})` → 말풍선 🧸 → register → `tick 2.5` → `p.stage=='annex'`, `G.ax.peds` 안 → `tick 7` → stage 'pay', fee == 70.
  - `test_child_to_dept_is_gentle`: 아이를 `sendTo(p,'int')` → stage 'reg' 유지, `G.combo` 그대로, `G.stats.wrong == 0`.
  - `test_ambulance_auto_to_er`: lv 2 prep → `G.ambTimes.length == 2`; 구급차 환자 spawn → 접수 없이 `tick 1` 안에 er 큐; 처리 후 fee ≥ 90.
  - `test_existing_emergency_to_er`: lv 2, 일반 응급 환자 `sendTo(p,'annex')` → `p.saved` true, `G.stats.emergOk == 1`.
  - `test_rehab_dest`: lv 3, `Math.random` 고정으로 rollDest('ort') 결과 집합에 'rehab' 포함; dest rehab 환자는 next 단계에서 2초 후 자동 신관.
  - `test_vip_suite_and_discharge`: lv 4, VIP 진료 끝 + rollDest가 ward → dest 'suite' → 자동 이동 → stage 'ward', 결산 `annexIncome == round(입원퇴원비*2*incomeMul)`.
  - `test_heli_auto_pay`: lv 5 prep → `G.heliTimes.length` in (1,2); 헬기 환자 → 10초 후 money 증가 `round((400+day*10)*incomeMul())`, `S.life.heli == 1`.
  - `test_annex_backlog_badge`: peds 정원 1, 아이 4명 신관 큐 → `.axs[data-ax=peds] .backlog`.
  - `test_day_waits_for_annex_and_suite_discharges`: `G.t=181`, 신관 처리 중 환자 1 + 특실 1 → `update(.1)` 후 mode 'play'; 처리 끝나고 수납 → 'summary'.
  - `test_auto_play_with_annex`: test_e2e AUTO 패턴(신관 보내기 추가 없이)으로 lv 5 3일 → js 오류 없음, 매일 summary 도달, `annexIncome > 0`.
- [ ] **Step 2:** FAIL 확인.
- [ ] **Step 3:** 구현 (위 Produces). `symDept('🧸')`는 진료과 없음 → `p.dept=null`; `validRooms`는 아이면 `['annex']`(+wait); `chooseSym`/복합/원인불명 대상 제외.
- [ ] **Step 4:** `pytest -q` 통과.
- [ ] **Step 5:** Commit `feat: annex rooms with new patient types`.

### Task 7: 마무리 — 안내서·README·첫 해금 안내·테스트 빌드

**Files:** Modify `index.html` (showGuide, prepDay 첫 해금 토스트), `README.md`, scratchpad `make_test.py`. Test `tests/test_endgame.py`, `tests/test_e2e.py`.

**Interfaces:**
- Consumes: 모든 이전 태스크.
- Produces: `S.seen = {}` 첫 해금 안내 1회 기록 (`eq`, `give`, `lab`, `annex`).
- [ ] **Step 1: Failing tests:**
  - `test_guide_mentions_endgame`: 안내서 텍스트에 '신관', '장비', '기부', '연구', '트로피'.
  - `test_unlock_hint_once`: grade 2 첫 prep → 토스트에 "연구"; 다음 prep 엔 없음.
- [ ] **Step 2:** FAIL 확인.
- [ ] **Step 3:** 구현. README 기능 목록에 5줄. scratchpad `make_test.py`의 테스트 빌드 newState 덮어쓰기에 `S.annex={lv:1,build:{stage:1,left:2}}`, `S.res={done:{diag:1},cur:{id:'exam2',left:1}}`, 돈 200000 추가 후 재생성.
- [ ] **Step 4:** `pytest -q` 전체 통과.
- [ ] **Step 5:** Commit `docs: guide and readme for endgame content`.
