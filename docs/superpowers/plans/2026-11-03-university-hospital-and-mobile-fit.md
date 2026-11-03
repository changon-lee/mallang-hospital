# 대학병원 · 모바일 화면 맞춤 · 직원 확장 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 말랑병원에 대학병원 등급·수술실·새 진료과·연수·홍보·다중 의사·수납 간호사·직원 명부를 추가하고, 폰 세로 화면에서 맵이 스크롤 없이 꽉 차게 하며, 대사 말풍선이 증상을 가리지 않게 한다.

**Architecture:** 게임은 `index.html` 한 파일에 그대로 둔다(스펙 비목표: 파일 분리 금지). 테스트는 Python + Playwright로 헤드리스 Chromium에서 `index.html`을 열고, 전역 함수·상태(`S`, `G`, `update()` 등)를 `page.evaluate`로 직접 호출해 검증한다. 시간은 `setSpeed(0)`으로 실시간 루프를 멈춘 뒤 `update(dt)`를 직접 불러 진행시킨다.

**Tech Stack:** Vanilla HTML/CSS/JS(기존), 테스트 전용: Python 3.9, pytest, playwright(chromium).

**Spec:** `docs/superpowers/specs/2026-11-03-university-hospital-and-mobile-fit-design.md`

## Global Constraints

- 단일 `index.html`, 외부 라이브러리·이미지 없음 (이모지와 CSS만). 테스트 도구는 `tests/`와 `requirements-dev.txt`에만 둔다.
- localStorage 키 `mallang-hospital-v1`, 세이브 `v` = 1 유지. 기존 세이브는 새 필드를 기본값으로 채워 이어할 수 있어야 한다.
- 기준 기기: 세로 폰 390×844 ~ 430×932 (보이는 높이 약 740px 이상), 이 크기에서 스크롤 없음 + `--pz ≥ 22px`. 360×640은 깨지지만 않으면 됨.
- 한국어 UI, 기존 말투(귀엽고 다정한 존댓말) 유지.
- 초반(동네의원) 플레이 감각·튜토리얼·지원자 구성은 바뀌면 안 된다.
- 사용자 입력(직원 이름)은 `innerHTML`에 넣기 전 반드시 HTML 이스케이프.
- 모든 커밋 메시지 끝: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
- 작업 브랜치: `feature/university-hospital` (main에 직접 커밋 금지).

## Review Focus

1. **업데이트 전 세이브로 이어하기** — `tr`/`name`/`ear`/`neu`/`surg` 키가 없는 세이브가 에러 없이 열리고 하루를 끝까지 플레이할 수 있어야 한다. → Task 1 `test_old_save_plays_full_day`.
2. **영업 중 화면 회전·크기 변경** — 진료 중 환자가 사라지거나 슬롯이 초기화되면 안 된다(맵 재구성 없이 크기만 재계산). → Task 10 `test_resize_midday_keeps_patients`.
3. **같은 과 의사 둘 중 하나만 쉬는 중 + 응급 환자 대기** — 쉬는 의사의 의자만 닫히고, 응급 환자가 그 과에 줄 서 있으면 아무도 새로 쉬러 가지 않는다. → Task 3 `test_emergency_blocks_rest_all_doctors`.
4. **이상한 이름 입력** — HTML 태그, 공백만, 11자 이상, 이모지. 태그는 글자로 보이고, 공백만이면 기본 이름, 10자 초과는 잘린다. → Task 2 `test_name_edge_cases`.
5. **수납 간호사와 플레이어가 같은 환자를 거의 동시에 수납** — 돈이 두 번 들어오면 안 된다. → Task 4 `test_no_double_pay`.

## 공통 테스트 헬퍼 (Task 0에서 만듦, 이후 모든 테스트가 사용)

`tests/conftest.py`:
- fixture `page_at` → **팩토리**: `page_at((w,h)=(430,932))`를 한 테스트에서 여러 번 불러도 매번 새 페이지(같은 브라우저, 새 context)를 돌려준다. `file://` 절대경로로 `index.html` 열기, `localStorage.clear()` 후 새로고침.
- `boot(page, *, grade=0, day=1, money=5000, rep=30, depts=None, rooms=None, staff_js='') -> None`
  JS로: `newState(); S.tut=true; S.day=day; S.grade=grade; S.money=money; S.rep=rep;` depts/rooms 병합, `staff_js` 실행(예: `S.staff.push(mkStaff('doctor',{dept:'int',spd:3,kind:3}))`), `save(); startGame(S); act('start'); setSpeed(0);`
- `tick(page, seconds, step=0.1)` → JS 루프로 `update(step)`를 `seconds/step`번 호출.
- `js(page, expr)` → `page.evaluate(expr)` 축약.
- `spawn_patient(page, **opts) -> int` → `spawn(true, opts).id`.

전역 `let`/`const`(예: `S`, `G`, `DEPTS`)는 스크립트 전역 렉시컬 스코프라 `page.evaluate("S.money")`로 접근된다.

---

### Task 0: 브랜치 · 테스트 하네스 · 스모크 테스트

**Files:**
- Create: `requirements-dev.txt`, `tests/conftest.py`, `tests/test_smoke.py`, `.gitignore`
- Commit: `docs/superpowers/specs/...design.md`, 이 계획 파일

**Interfaces:**
- Produces: 위 "공통 테스트 헬퍼"의 `page_at`, `boot`, `tick`, `js`, `spawn_patient`.

- [ ] **Step 1: 브랜치 생성** — `git checkout -b feature/university-hospital`
- [ ] **Step 2: 의존성** — `requirements-dev.txt`에 `pytest>=7`, `playwright>=1.40`. 실행: `py -m pip install -r requirements-dev.txt` 후 `py -m playwright install chromium`. `.gitignore`에 `__pycache__/`, `.pytest_cache/`.
- [ ] **Step 3: 헬퍼와 스모크 테스트 작성**

```python
def test_title_and_new_game(page_at):
    page = page_at()
    assert page.locator('#title h1').inner_text() == '말랑병원'
    boot(page)
    assert js(page, "G.mode") == 'play'
    assert js(page, "S.staff.length") == 1

def test_tick_advances_time(page_at):
    page = page_at(); boot(page)
    tick(page, 5)
    assert 4.9 < js(page, "G.t") < 5.1
```

- [ ] **Step 4: 실행** — `py -m pytest tests -q` → 2 passed.
- [ ] **Step 5: 커밋** — `git add -A && git commit -m "test: add playwright harness; add design spec and plan"`

---

### Task 1: 세이브 깊은 병합 (스펙 5.10)

**Files:** Modify `index.html` (`load()` 651행, `#tCont` 클릭 1803행, `mkStaff` 658행), Test `tests/test_save.py`

**Interfaces:**
- Produces: `migrate(raw: object) -> object` — `newState()` 기본값 위에 `raw`를 깊게 병합한 새 상태. `depts`/`rooms`/`up`/`deco`는 키 단위 병합, `staff`/`cands`의 각 직원은 `{tr:0, name:null, ...직원}`. `#tCont`는 `startGame(migrate(s))`를 쓴다.
- Produces: `mkStaff`가 `tr:0, name:null`을 포함.

- [ ] **Step 1: 실패 테스트**

```python
OLD = {"v":1,"day":5,"money":900,"rep":40,"stars":3,"grade":0,"total":30,
  "depts":{"int":True},"rooms":{"exam":True,"inj":False,"rest":False},
  "up":{"clinic":1,"wait":0,"ward":0},"deco":{},
  "staff":[{"id":1,"role":"doctor","dept":"int","animal":"🐻","spd":2,"kind":2,"lvl":1,"xp":0,"fat":0,"rest":0,"t":0,"wage":40}],
  "cands":[],"candDay":5,"tut":True,"nextId":2}

def test_migrate_fills_new_fields(page_at):
    page = page_at()
    s = page.evaluate("o => migrate(o)", OLD)
    assert s["rooms"]["exam"] is True and s["rooms"]["surg"] is False
    assert s["staff"][0]["tr"] == 0 and s["staff"][0]["name"] is None
    assert s["day"] == 5 and s["money"] == 900

def test_old_save_plays_full_day(page_at):
    page = page_at()
    page.evaluate("o => localStorage.setItem('mallang-hospital-v1', JSON.stringify(o))", OLD)
    page.reload(); page.click('#tCont'); js(page, "act('start'); setSpeed(0)")
    tick(page, 200, 0.2)
    # 남은 환자를 치워 결산을 강제 (자동 플레이는 Task 11에서 검증)
    js(page, "G.patients.slice().forEach(p => removeP(p,'bye')); update(0.1)")
    assert js(page, "S.day") == 6
```

  (Task 1에서 `newState().rooms`에 `surg:false`를 미리 추가하므로 `surg` 단언도 이 Task에서 통과한다.)

- [ ] **Step 2: 실행해 실패 확인** — `py -m pytest tests/test_save.py -q` → `migrate is not defined`.
- [ ] **Step 3: 구현** — `migrate`, `mkStaff` 기본 필드, `newState().rooms`에 `surg:false`, `#tCont`에서 `migrate` 사용.
- [ ] **Step 4: 통과 확인** — 같은 명령 → passed.
- [ ] **Step 5: 커밋** — `feat: deep-merge saves so new fields default safely`

---

### Task 2: 직원 이름 커스텀 데이터 · 이스케이프 (스펙 5.9 데이터 부분)

**Files:** Modify `index.html` (`staffName` 664행, `jo` 592행 호출부), Test `tests/test_names.py`

**Interfaces:**
- Produces: `esc(str) -> string` (`& < > " '` 이스케이프).
- Produces: `staffNameRaw(s) -> string` — `s.name`이 있으면 그것, 없으면 `` `${ANAME[s.animal]} ${ROLE[s.role].t}` ``.
- Produces: `staffName(s) -> string` = `esc(staffNameRaw(s))`. 조사는 `jo(staffNameRaw(s), a, b)`로 판단 후 결과를 `esc`. 헬퍼 `staffNameJo(s, a, b) -> string`(이스케이프된 결과)로 묶고 기존 `jo(staffName(..),..)` 호출 3곳(1620, 1640, 1308행)을 교체.
- Produces: `setStaffName(id: number, input: string) -> void` — `trim()`, 빈 문자열이면 `name=null`, 최대 10자(`Array.from`으로 코드포인트 기준 자르기), 그 후 `save()`.

- [ ] **Step 1: 실패 테스트**

```python
def test_default_and_custom_name(page_at):
    page = page_at(); boot(page)
    assert js(page, "staffName(S.staff[0])") == '곰곰 선생님'
    js(page, "setStaffName(S.staff[0].id, '  김원장  ')")
    assert js(page, "staffName(S.staff[0])") == '김원장'
    assert js(page, "JSON.parse(localStorage.getItem('mallang-hospital-v1')).staff[0].name") == '김원장'

def test_name_edge_cases(page_at):
    page = page_at(); boot(page)
    js(page, "setStaffName(S.staff[0].id, '<b>x</b>')")
    assert js(page, "staffName(S.staff[0])") == '&lt;b&gt;x&lt;/b&gt;'
    js(page, "setStaffName(S.staff[0].id, '   ')")
    assert js(page, "S.staff[0].name") is None
    js(page, "setStaffName(S.staff[0].id, '가나다라마바사아자차카')")
    assert js(page, "S.staff[0].name") == '가나다라마바사아자차'
    js(page, "setStaffName(S.staff[0].id, '🐻🐻🐻🐻🐻🐻🐻🐻🐻🐻🐻')")
    assert js(page, "Array.from(S.staff[0].name).length") == 10

def test_josa_uses_raw_name(page_at):
    page = page_at(); boot(page)
    js(page, "setStaffName(S.staff[0].id, '곰')")   # 받침 있음
    assert js(page, "staffNameJo(S.staff[0],'이','가')") == '곰이'
```

- [ ] **Step 2: 실패 확인** — `py -m pytest tests/test_names.py -q`
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 확인 + 전체 회귀** — `py -m pytest tests -q`
- [ ] **Step 5: 커밋** — `feat: custom staff names with html escaping`

---

### Task 3: 의사 여러 명 · 의사 수만큼 진료 의자 (스펙 5.7)

**Files:** Modify `index.html` (`doctorOf`/`doctorReady` 665-666, `capOf` 668, `cardHTML` 857-858, `renderStaff` 899, `treatDur` 1126, `roomReady`/`updRooms` 1140·1206, `svcStep` 1185, `isIdle` 1221, `genCands` 693, `hireCheck` 1552, `staffCard` 1561, `buy` hire/fire 1633-1641, `tapRoom` 1746), Test `tests/test_doctors.py`

**Interfaces:**
- Produces: `doctorsOf(d) -> Staff[]` (`S.staff` 순서). `doctorOf(d)`는 `doctorsOf(d)[0]`로 유지(호환).
- Produces: `docCap() -> number` = `[1,2,3,3][S.grade]`. `capOf('doctor')`는 이 값.
- Produces: `slotDoctor(r, i) -> Staff|undefined` = `doctorsOf(r)[i]`. `slotReady(r, i) -> boolean` — 진료과면 `slotDoctor`가 있고 `rest`가 0, 그 외 방은 `true`. `updRooms`는 `roomReady(r)` 대신 `slotReady(r, i)`.
- Produces: `treatDur(r, i)` — 해당 슬롯 의사 기준. `svcStep`의 `work(doctorOf(r),7)` → `work(slotDoctor(r,i),7)`.
- 진료과 카드의 슬롯 수 = `Math.max(1, doctorsOf(d).length)`. 슬롯 i의 `.slot`에 `data-doc="${staff.id}"`, 쉬는 의사의 슬롯에 `.closed`(카드 전체 `.closed` 대신 슬롯 단위; CSS `.card.closed .slot::after`를 `.slot.closed::after`로).
- `isIdle(s)` 의사: 자기 슬롯(`doctorsOf(s.dept).indexOf(s)`)이 비었고, 그 과에 응급 미처치 환자가 줄 서 있지 않음.
- 고용 규칙: `doctorsOf(c.dept).length < docCap()` → 추가 "💌 고용"; 아니면 "🔄 교체" — 그 과에서 `spd+kind`가 가장 작은 의사(동률이면 먼저 고용된 쪽)를 대체. 해고: 그 과 의사 2명 이상일 때만 "👋 보내기".
- 의사 후보의 과: `docCap()` 미만인 열린 과 중 무작위, 없으면 열린 과 중 무작위.

- [ ] **Step 1: 실패 테스트**

```python
TWO_INT = "S.staff.push(mkStaff('doctor',{dept:'int',spd:2,kind:2}))"

def test_two_doctors_two_slots(page_at):
    page = page_at(); boot(page, grade=1, staff_js=TWO_INT)
    assert js(page, "G.slots.int.length") == 2
    a = spawn_patient(page, sym='🤒', urg=0); b = spawn_patient(page, sym='🤧', urg=0)
    js(page, f"[{a},{b}].forEach(id => {{ const p=G.patients.find(x=>x.id===id); register(p); sendTo(p,'int'); }})")
    tick(page, 0.3)
    assert js(page, "G.slots.int.filter(Boolean).length") == 2

def test_resting_doctor_closes_only_own_slot(page_at):
    page = page_at(); boot(page, grade=1, rooms={'rest':True}, staff_js=TWO_INT)
    js(page, "doctorsOf('int')[1].rest = 5")
    assert js(page, "slotReady('int',0)") is True
    assert js(page, "slotReady('int',1)") is False

def test_emergency_blocks_rest_all_doctors(page_at):
    page = page_at(); boot(page, grade=1, day=5, rooms={'rest':True}, staff_js=TWO_INT)
    js(page, "doctorsOf('int').forEach(d => d.fat = 90)")
    js(page, "const p = spawn(true,{emerg:true, sym:'🤒'}); p.stage='queued'; p.target='int'")
    js(page, "updStaff(0.1)")   # 슬롯은 비어 있지만 응급 환자가 int 줄에 있음
    assert js(page, "doctorsOf('int').every(d => !(d.rest > 0))") is True

def test_hire_adds_then_replaces_weakest(page_at):
    page = page_at(); boot(page, grade=0)
    js(page, "G.mode='prep'; S.cands=[mkStaff('doctor',{dept:'int',spd:5,kind:5})]; buy('hire:0')")
    assert js(page, "doctorsOf('int').length") == 1
    assert js(page, "doctorsOf('int')[0].spd") == 5   # 동네의원 정원 1 → 교체

    page2 = page_at(); boot(page2, grade=1)
    js(page2, "G.mode='prep'; S.cands=[mkStaff('doctor',{dept:'int',spd:1,kind:1})]; buy('hire:0')")
    assert js(page2, "doctorsOf('int').length") == 2

def test_cannot_fire_last_doctor(page_at):
    page = page_at(); boot(page, grade=1, staff_js=TWO_INT)
    js(page, "G.mode='prep'; buy('fire:' + doctorsOf('int')[1].id)")
    assert js(page, "doctorsOf('int').length") == 1
    js(page, "buy('fire:' + doctorsOf('int')[0].id)")
    assert js(page, "doctorsOf('int').length") == 1
```

- [ ] **Step 2: 실패 확인** — `py -m pytest tests/test_doctors.py -q`
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 + 전체 회귀** — `py -m pytest tests -q`
- [ ] **Step 5: 커밋** — `feat: multiple doctors per department with one chair each`

---

### Task 4: 수납 간호사 (스펙 5.6)

**Files:** Modify `index.html` (`ROLE` 556, `capOf`, `staffHome` 890, `cardHTML` case `cash` 870, `updStaff` 1227, `pay` 1045, `genCands` 684, 상점 정원 문구 1604, `tapRoom` cash 1743), Test `tests/test_cashier.py`

**Interfaces:**
- Produces: `ROLE.cashier = { t:'수납 간호사', b:'💳', n:'수납 간호사', desc:'수납 줄의 환자를 자동으로 계산해요' }`, `ROLE_TONE.cashier = 'peach'`.
- Produces: `pay(p, opt={}) ` — `opt.auto`가 참이면 빠른 수납 팁(+5) 없음. 나머지 동일.
- `capOf('cashier')` = 동네의원 0, 병원 1, 종합병원 이상 2. `hireCheck`는 cap 0이면 버튼 비활성 "🔒 병원 승급 후".
- `updStaff`: `cashier` 타이머 `s.t -= dt*tm`, 0 이하에서 `stage==='pay'` 중 `cashT`가 가장 작은 환자 `pay(p,{auto:true})`, `work(s,4)`, `s.t = 3.2 - s.spd*0.4`; 대상 없으면 `s.t = 0.3`.
- `genCands`: `S.grade >= 1`이고 수납 간호사가 없으면 `list`에 `'cashier'` 보장(간호사·청소부 보장 다음 순서). 무작위 풀 `roles`에는 `S.grade >= 1`일 때만 `'cashier'` 추가. 동네의원 후보 구성은 기존과 동일.
- 수납 카드에 `<span class="staffs" data-staff="cash"></span>`.

- [ ] **Step 1: 실패 테스트**

```python
CASHIER = "S.staff.push(mkStaff('cashier',{spd:3,kind:2}))"

def mk_payer(page):
    return js(page, "(() => { const p = spawn(true,{sym:'🤒',urg:0}); p.stage='pay'; p.fee=40; toCash(p); return p.id })()")

def test_cashier_auto_pays_without_fast_tip(page_at):
    page = page_at(); boot(page, grade=1, staff_js=CASHIER)
    mk_payer(page); m0 = js(page, "S.money")
    tick(page, 1)   # 수납 간호사 타이머는 0에서 시작 → 첫 updStaff에서 바로 수납
    assert js(page, "G.patients.length") == 0
    # fee 40 + tip round(40*.25*pat/100) (pat ≥ 95 → 10), 빠른 팁 5 없음
    assert js(page, "S.money") - m0 == 50

def test_no_double_pay(page_at):
    page = page_at(); boot(page, grade=1, staff_js=CASHIER)
    pid = mk_payer(page); m0 = js(page, "S.money")
    js(page, f"const p=G.patients.find(x=>x.id==={pid}); pay(p); pay(p,{{auto:true}}); S.staff.find(s=>s.role==='cashier').t=0; updStaff(0.1)")
    assert js(page, "S.money") - m0 == js(page, "G.stats.income")
    assert js(page, "G.stats.treated") == 1

def test_cashier_locked_at_clinic_and_not_in_cands(page_at):
    page = page_at(); boot(page, grade=0, day=4)
    for _ in range(30):
        js(page, "genCands()")
        assert js(page, "S.cands.every(c => c.role !== 'cashier')")
    assert js(page, "capOf('cashier')") == 0

def test_cashier_guaranteed_at_hospital(page_at):
    page = page_at(); boot(page, grade=1, day=4)
    js(page, "S.staff.push(mkStaff('nurse')); S.staff.push(mkStaff('janitor')); genCands()")
    assert js(page, "S.cands.some(c => c.role === 'cashier')")
```

- [ ] **Step 2: 실패 확인** — `py -m pytest tests/test_cashier.py -q`
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 + 전체 회귀**
- [ ] **Step 5: 커밋** — `feat: cashier nurse auto-handles payments from hospital grade`

---

### Task 5: 대학병원 등급 · 새 진료과 · 응급 보정 (스펙 5.1, 5.4)

**Files:** Modify `index.html` (`DEPTS` 521, `DEPT_ORDER` 529, `GRADES`/`GRADE_TH` 554-555, `LAYOUT` 569, `applyLayout` 최대 폭 827, `gradeProgress` 729, `checkPromo` 734, `moreHTML` 844, `capOf` 668 청소부, `prepDay` 응급 수 1409, `extraPay` 1044, `showGradeInfo`), Test `tests/test_grade.py`

**Interfaces:**
- Produces: `MAX_GRADE = GRADES.length - 1` (= 3). 최고 등급 판정은 모두 `S.grade >= MAX_GRADE`로 일반화(`gradeProgress`, `checkPromo`, `moreHTML`). 청소부 정원은 `S.grade >= 2 ? 2 : 1` 유지.
- Data: `GRADES = ['동네의원','병원','종합병원','대학병원']`, `GRADE_TH`에 `{rep:88,total:450}` 추가.
- Data: `DEPTS.ear = { name:'이비인후과', icon:'👂', fee:65, price:5200, grade:3, syms:[['👂',1,'귀 아픔'],['😮‍💨',1,'코막힘']] }`, `DEPTS.neu = { name:'신경과', icon:'🧠', fee:75, price:6500, grade:3, syms:[['🤕',1,'두통'],['😵‍💫',1,'어지럼']] }`. `DEPT_ORDER` 끝에 `'ear','neu'`.
- Data (임시 레이아웃, Task 10에서 다듬음):
  - `LAYOUT.wide[3] = ['ent wait wait wait cash rest','int ort eye den skin pharm','obgy ear neu exam inj pharm','surg ward ward ward ward pharm']`
  - `LAYOUT.narrow[3] = ['ent wait wait','cash wait wait','int ort eye','den skin obgy','ear neu exam','inj surg pharm','ward ward pharm','ward ward rest']`
  - `surg`는 Task 6 전까지 잠긴 방으로 그려지도록 `BUY_ROOMS.surg`를 이 Task에서 데이터만 먼저 추가: `{ price:3800, grade:3, desc:'진료 후 ⚕️ 수술이 필요한 환자를 받아요 (수술비가 커요)' }`, `ROOMS.surg = {name:'수술실', icon:'⚕️'}`.
  - `#map` 최대 폭 배열에 `'1600px'` 추가.
- 응급: `prepDay`의 `ne`에 `+ (S.grade >= 3 ? 1 : 0)` 추가(기존 `+S.grade`와 별개). `extraPay`의 응급 몫 `(50 + S.day*5)`에만 `S.grade >= 3 ? 1.5 : 1` 곱하고 `Math.round`.

- [ ] **Step 1: 실패 테스트**

```python
def test_promote_to_university(page_at):
    page = page_at(); boot(page, grade=2, rep=90)
    js(page, "S.total = 450")
    assert js(page, "checkPromo()") is True and js(page, "S.grade") == 3
    assert js(page, "checkPromo()") is False

def test_new_depts_buyable_in_order(page_at):
    page = page_at()
    boot(page, grade=3, money=99999, depts={'ort':True,'eye':True,'den':True,'skin':True,'obgy':True})
    js(page, "G.mode='prep'; buy('dept:neu')")
    assert js(page, "!!S.depts.neu") is False          # 이비인후과 먼저
    js(page, "buy('dept:ear'); buy('dept:neu')")
    assert js(page, "!!S.depts.ear && !!S.depts.neu") is True
    assert js(page, "symDept('🤕')") == 'neu'

def test_grade3_map_has_all_rooms(page_at):
    page = page_at(); boot(page, grade=3)
    rooms = js(page, "[...document.querySelectorAll('#map .card')].map(c => c.dataset.room).sort()")
    assert rooms == sorted(['ent','wait','cash','rest','int','ort','eye','den','skin','obgy','ear','neu','exam','inj','pharm','ward','surg'])

def test_emergency_bonus_university(page_at):
    page = page_at(); boot(page, grade=3, day=10)
    assert js(page, "extraPay({emerg:true})") == 150   # round((50+50)*1.5)
    assert js(page, "extraPay({vip:true})") == 140      # 60+80, 배율 없음
```

- [ ] **Step 2: 실패 확인** — `py -m pytest tests/test_grade.py -q`
- [ ] **Step 3: 구현** (안내서·승급 안내 모달의 "열리는 것" 목록은 데이터에서 자동 생성되므로 확인만)
- [ ] **Step 4: 통과 + 전체 회귀**
- [ ] **Step 5: 커밋** — `feat: university hospital grade with ENT and neurology`

---

### Task 6: 수술실 (스펙 5.2)

**Files:** Modify `index.html` (`DEST` 562, `cardHTML` 새 case `surg`, `svcDur` 1133, `rollDest` 1155, `svcStep` 비진료과 분기 1199, `validRooms` 1068, `sendTo` 1109, 안내서 1660, 상점 방 탭 tones 1583), Test `tests/test_surgery.py`

**Interfaces:**
- Consumes: Task 5의 `BUY_ROOMS.surg`, `ROOMS.surg`.
- Produces: `DEST.surg = '⚕️'`. `cardHTML('surg')` = 헤더 ⚕️ 수술실 + 가구 + `slotHTML()` 1개.
- `svcDur('surg') = 8`.
- `rollDest(r, p)`: `S.rooms.surg`일 때 후보 `['surg', w]` 추가, `w = p.emerg ? 3 : (r==='ort'||r==='neu') ? 2 : 0.5`. 기존의 `if (p && p.emerg) r = 'obgy'` 트릭은 그대로 두되 응급 판정은 원래 `r`이 아니라 `p.emerg`로 계산한다(순서 주의: surg 가중치를 먼저 계산).
- 수술 완료: `p.fee += 120 + S.day*3`, `stage='pay'`, `toCash(p)`.
- `validRooms`: `p.done`이면 `S.rooms.surg`일 때 `'surg'` 포함. `sendTo`: `DEST[r]`이고 `r === p.dest`면 `queueTo`(ward 예외는 기존대로).
- 상점 방 탭 tones에 `surg:'pink'`.

- [ ] **Step 1: 실패 테스트**

```python
def test_surgery_flow(page_at):
    page = page_at(); boot(page, grade=3, day=10, rooms={'surg':True}, depts={'ort':True})
    pid = js(page, "(() => { const p = spawn(true,{sym:'🦴',urg:0}); register(p); p.done=true; p.dest='surg'; p.stage='next'; p.fee=40; return p.id })()")
    js(page, f"sendTo(G.patients.find(p=>p.id==={pid}),'surg')")
    tick(page, 8.3)
    assert js(page, f"G.patients.find(p=>p.id==={pid}).stage") == 'pay'
    assert js(page, f"G.patients.find(p=>p.id==={pid}).fee") == 40 + 120 + 30

def test_wrong_room_for_surgery_patient(page_at):
    page = page_at(); boot(page, grade=3, rooms={'surg':True})
    pid = js(page, "(() => { const p = spawn(true,{sym:'🤒',urg:0}); register(p); p.done=true; p.dest='surg'; p.stage='next'; return p.id })()")
    js(page, f"sendTo(G.patients.find(p=>p.id==={pid}),'pharm')")
    assert js(page, "G.stats.wrong") == 1

def test_roll_dest_includes_surgery_only_when_owned(page_at):
    page = page_at(); boot(page, grade=3, depts={'ort':True})
    js(page, "Math.random = () => 0.999")   # wpick이 마지막 후보 선택
    assert js(page, "rollDest('ort',{})") != 'surg'
    js(page, "S.rooms.surg = true")
    assert js(page, "rollDest('ort',{})") == 'surg'
```

  (`wpick`은 마지막 후보를 고르므로 `surg`를 `opts` 맨 끝에 push한다.)

- [ ] **Step 2: 실패 확인** — `py -m pytest tests/test_surgery.py -q`
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 + 전체 회귀**
- [ ] **Step 5: 커밋** — `feat: surgery room as a post-treatment destination`

---

### Task 7: 직원 연수 · 홍보 (스펙 5.3)

**Files:** Modify `index.html` (`staffCard` 1558, `buy` 1613, `spawnInterval` 714, `spawn` VIP 확률 978, `showPrep` 1414, `newG` 643), Test `tests/test_spend.py`

**Interfaces:**
- Produces: `trainCost(s) -> number` = `Math.round(250 * 1.6 ** s.tr)`.
- `buy('train:<staffId>:spd' | 'train:<staffId>:kind')`: `S.grade >= 2`, 해당 능력치 < 5, 돈 충분 → 차감, 능력치 +1, `s.tr++`, `s.wage = wageOf(s)`. 상점 직원 탭 "우리 병원 식구들" 카드(의사 포함)에 두 버튼 `📚 ⚡ 💰비용` / `📚 😊 💰비용`; 종합병원 미만이면 버튼 대신 잠금 문구 `🔒 종합병원부터 연수`. `buy`가 `key.split(':')`로 3조각을 받도록 수정.
- Data: `ADS = { flyer:{icon:'📄',name:'전단지',base:200,per:10,mul:.87}, radio:{icon:'📻',name:'라디오',base:600,per:20,mul:.75}, tv:{icon:'📺',name:'TV 광고',base:1500,per:40,mul:.65,vip:1.5} }`.
- Produces: `adCost(id) -> number` = `ADS[id].base + S.day*ADS[id].per`.
- `G.ad` (`newG` 기본 `null`, 저장 안 함). `act('ad:<id>')`: `S.grade >= 2`, `G.mode==='prep'`, `!G.ad`, 돈 충분 → 차감, `G.ad = id`, `showPrep()`.
- `spawnInterval`: `G.ad`면 `iv *= ADS[G.ad].mul`. `spawn`의 무작위 VIP 확률에 `G.ad && ADS[G.ad].vip || 1` 곱.
- `showPrep`: 종합병원 이상이면 "📣 오늘의 홍보" 박스에 세 버튼(선택 후엔 선택된 것만 "✓ 진행 중", 나머지 비활성).
- `endDay` 결산 표에 홍보비 줄 `📣 홍보비 -💰n`, `net` 계산에 포함(`G.adCost` 저장).

- [ ] **Step 1: 실패 테스트**

```python
def test_training_cost_and_effect(page_at):
    page = page_at(); boot(page, grade=2, money=10000)
    sid = js(page, "S.staff[0].id"); spd0 = js(page, "S.staff[0].spd"); w0 = js(page, "S.staff[0].wage")
    js(page, f"G.mode='prep'; buy('train:{sid}:spd')")
    assert js(page, "S.money") == 10000 - 250
    assert js(page, "S.staff[0].spd") == spd0 + 1 and js(page, "S.staff[0].wage") > w0
    js(page, f"buy('train:{sid}:kind')")
    assert js(page, "S.money") == 10000 - 250 - 400

def test_training_locked_below_general(page_at):
    page = page_at(); boot(page, grade=1, money=10000)
    js(page, "G.mode='prep'; buy('train:' + S.staff[0].id + ':spd')")
    assert js(page, "S.money") == 10000

def test_training_caps_at_5(page_at):
    page = page_at(); boot(page, grade=2, money=99999)
    js(page, "S.staff[0].spd = 5; G.mode='prep'; buy('train:' + S.staff[0].id + ':spd')")
    assert js(page, "S.money") == 99999

def test_ad_once_per_day_and_faster_spawns(page_at):
    page = page_at(); boot(page, grade=2, day=10, money=10000)
    js(page, "G.mode='prep'; Math.random = () => 0.5")
    base = js(page, "spawnInterval()")
    js(page, "act('ad:radio')")
    assert js(page, "S.money") == 10000 - 800
    assert abs(js(page, "spawnInterval()") - base * 0.75) < 1e-9
    js(page, "act('ad:tv')")
    assert js(page, "G.ad") == 'radio' and js(page, "S.money") == 10000 - 800
```

- [ ] **Step 2: 실패 확인** — `py -m pytest tests/test_spend.py -q`
- [ ] **Step 3: 구현** (`boot`가 `act('start')`까지 하므로 `G.mode='prep'`로 되돌려 테스트; `act('ad:..')`는 `prep`에서만 동작)
- [ ] **Step 4: 통과 + 전체 회귀**
- [ ] **Step 5: 커밋** — `feat: staff training and daily advertising money sinks`

---

### Task 8: 직원 명부 모달 · 이름 바꾸기 UI (스펙 5.9 UI 부분)

**Files:** Modify `index.html` (HUD 버튼 493행 옆, `act`, 키보드 핸들러 1810, CSS 상점 섹션 근처), Test `tests/test_roster.py`

**Interfaces:**
- Consumes: Task 2 `setStaffName`, `staffName`.
- Produces: HUD 버튼 `<button id="bStaff" class="ibtn" title="직원 명부">👥</button>` (📖 앞).
- Produces: `showRoster() -> void` — `G.mode`가 `play`면 `G.modal = true`. 역할 순서 `['doctor','nurse','cashier','pharm','janitor']`. 카드는 `staffCard`와 같은 `.sitem` 스타일을 재사용하되 버튼 없음. 이름 줄: `<div class="sname" data-sid="${id}">${staffName(s)} <button class="rn" data-act="rename:${id}">✏️</button></div>`. 하단 `<button class="btn pri" data-act="rosterClose">닫기</button>`.
- `act('rename:<id>')`: 이름 줄을 `<input class="rn-in" maxlength="10">`으로 교체, 값은 `staffNameRaw`가 아닌 `s.name || ''`, 포커스. Enter/blur → `setStaffName(id, value)` 후 `showRoster()` 다시 그림. Esc → 저장 없이 `showRoster()`.
- `act('rosterClose')`: `G.mode==='prep'`면 `showPrep()`, 아니면 `closeModal(); G.modal=false`.
- 키보드 핸들러: `e.target`이 `input`이면 즉시 return.
- 버튼은 `G.mode`가 `play` 또는 `prep`일 때만 동작.

- [ ] **Step 1: 실패 테스트**

```python
def test_roster_pauses_and_lists_staff(page_at):
    page = page_at(); boot(page, grade=1, staff_js="S.staff.push(mkStaff('nurse'))")
    js(page, "setSpeed(1)")
    page.click('#bStaff')
    assert js(page, "G.modal") is True
    assert page.locator('.modal .sname').count() == 2
    t0 = js(page, "G.t"); page.wait_for_timeout(300)
    assert js(page, "G.t") == t0

def test_rename_via_ui(page_at):
    page = page_at(); boot(page)
    page.click('#bStaff'); page.click('.modal .rn')
    page.fill('.modal .rn-in', '<i>닥터곰</i>'); page.keyboard.press('Enter')
    assert page.locator('.modal .sname').first.inner_text().startswith('<i>닥터곰</i>')
    assert js(page, "S.staff[0].name") == '<i>닥터곰</i>'

def test_rename_escape_cancels_and_space_key_ignored(page_at):
    page = page_at(); boot(page); js(page, "setSpeed(1)")
    page.click('#bStaff'); page.click('.modal .rn')
    page.fill('.modal .rn-in', 'ab'); page.keyboard.press('Space'); page.keyboard.press('Escape')
    assert js(page, "S.staff[0].name") is None
    assert js(page, "G.speed") == 1
```

- [ ] **Step 2: 실패 확인** — `py -m pytest tests/test_roster.py -q`
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 + 전체 회귀**
- [ ] **Step 5: 커밋** — `feat: staff roster with inline rename`

---

### Task 9: 대사 말풍선이 증상을 가리지 않게 (스펙 5.8)

**Files:** Modify `index.html` (`.pt-say` CSS 141-142, `spawn`의 환자 마크업 984, `say` 806), Test `tests/test_bubble.py`

**Interfaces:**
- 마크업: `.pt-say`를 `.pt-in` 안, `.pt-bub` 바로 앞으로 옮긴다(`.pt-in`은 아래 정렬 flex라 대사가 증상 말풍선 위에 쌓임). `.pt-say`는 `position:absolute; bottom:calc(100% + 2px)`를 `.pt-bub` 기준으로 하기 위해 `.pt-bub`에 `position:relative`가 이미 있으므로 `.pt-say`를 `.pt-bub` **내부**가 아닌 형제로 두고, `.pt-say`의 기준을 증상 말풍선 위쪽으로 잡는 방식은 구현자가 정하되 아래 테스트를 만족해야 한다.
- 스타일: `font-size:10px; background:#5b4a60d9;` `.pt-bub`의 `z-index`를 `.pt-say`보다 높게(예: bub 7, say 6).
- `say(p, text, ms=1500)` 기본값 1.9초 → 1.5초.
- 맨 위 줄 방에서 대사 상단이 방 카드(`.card`) 위로 잘리면 `.pt-say.side` 클래스로 환자 오른쪽(`left:100%; bottom:50%; transform:none`)에 표시. 판단은 `say()` 안에서 표시 직후 `getBoundingClientRect` 비교.

- [ ] **Step 1: 실패 테스트**

```python
def rects_overlap(a, b):
    return not (a['right'] <= b['left'] or b['right'] <= a['left'] or a['bottom'] <= b['top'] or b['bottom'] <= a['top'])

def test_say_does_not_cover_symptom(page_at):
    page = page_at(); boot(page)
    pid = spawn_patient(page, sym='🤒', urg=0, unknown=True)
    js(page, f"register(G.patients.find(p=>p.id==={pid}))")   # '어디가 아픈지 모르겠어요…' 대사
    page.wait_for_timeout(1300)  # 이동 애니메이션 종료 대기
    r = js(page, f"""(() => {{ const p=G.patients.find(x=>x.id==={pid}); say(p,'어디가 아픈지 모르겠어요…');
        const b=p.bubEl.getBoundingClientRect(), s=p.sayEl.getBoundingClientRect();
        return [b.toJSON(), s.toJSON()] }})()""")
    assert not rects_overlap(r[0], r[1])

def test_symptom_bubble_above_say_layer(page_at):
    page = page_at(); boot(page)
    pid = spawn_patient(page, sym='🤒')
    z = js(page, f"(() => {{ const p=G.patients.find(x=>x.id==={pid}); return [+getComputedStyle(p.bubEl).zIndex, +getComputedStyle(p.sayEl).zIndex] }})()")
    assert z[0] > z[1]
```

- [ ] **Step 2: 실패 확인** — `py -m pytest tests/test_bubble.py -q`
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 + 전체 회귀**
- [ ] **Step 5: 커밋** — `fix: speech bubble no longer hides patient symptoms`

---

### Task 10: 모바일 화면 맞춤 (스펙 5.5) — 마지막 (모든 방·의자 수가 확정된 뒤)

**Files:** Modify `index.html` (CSS `#mapWrap` 53·284, `#map` 55·285·422, `.queue`/`.seats`/`.slot`/`.pt`, `@media (max-width:600px)` HUD 404·468, `applyLayout` 821, `LAYOUT.narrow[0..3]` 575, resize 리스너 1820, `place` 905), Test `tests/test_fit.py`

**Interfaces:**
- Produces: `fitMap() -> void`:
  1. `#map` 높이를 `#mapWrap`의 `clientHeight - 세로 padding`으로 고정, `gridTemplateRows = repeat(n, minmax(0,1fr))`.
  2. `--pz`를 `#map`에 설정: 34px에서 시작해 1px씩 줄이며, 내용이 있는 모든 `.card .cb`가 넘치지 않을 때(`scrollHeight <= clientHeight+1 && scrollWidth <= clientWidth+1`) 멈춘다. 하한 16px(작은 폰 허용). 대기열 컨테이너(`.queue`)는 측정에서 제외(겹침으로 처리).
  3. 대기열 겹침: `.queue`마다 자식 수와 폭으로 음수 `margin-right` 계산(`overlapQueue(el)`), 한 줄 유지(`flex-wrap:nowrap`).
- `applyLayout()` 끝에서 `fitMap()` 호출. `ResizeObserver(#mapWrap)` → `requestAnimationFrame(fitMap)`; 기존 `resize` 디바운스도 유지. **맵 재구성(`buildMap`) 없이** 크기만 바꾼다.
- `place()`/`removeP()`/`spawn()`에서 대상이 `.queue`이면 `overlapQueue(container)` 호출.
- `#mapWrap{overflow:hidden}`, `.card{overflow:hidden; min-height:0}`. `.coachpad`의 하단 여백이 있으면 그만큼 맵 높이 감소.
- 폰(`max-width:600px`): HUD를 한 줄로 — 로고 텍스트·등급 칩 숨김, 칩 폰트 축소; 목표 바+알림 바 높이 ≤ 34px.
- 의자·환자 비율: 필요 시 `.slot` 높이 `pz*2.7 → pz*2.3`, `.pt` 높이 `pz*2.15 → pz*2.0` (증상 말풍선이 몸에 살짝 겹침). Task 9 말풍선 테스트가 계속 통과해야 함.
- `LAYOUT.narrow[0..3]` 재설계: 3열, 최대 8줄, 모든 영역은 직사각형. 진료과 3석은 flex-wrap으로 2+1.

- [ ] **Step 1: 실패 테스트**

```python
import pytest
PHONES = [(390, 844 - 100), (430, 932 - 100)]   # 보이는 높이(브라우저 바 제외)
OTHER = [(844, 390 - 40), (1440, 900)]
ALL_DEPTS = {'ort':True,'eye':True,'den':True,'skin':True,'obgy':True,'ear':True,'neu':True}

FILL_JS = """
  for (const d of DEPT_ORDER) if (DEPTS[d].grade <= S.grade) S.depts[d] = true;
  S.rooms = { exam:true, inj:true, rest:S.grade>=1, surg:S.grade>=3 };
  S.up.wait = 3; S.up.ward = 3;
  for (const d of DEPT_ORDER) if (S.depts[d]) while (doctorsOf(d).length < docCap()) S.staff.push(mkStaff('doctor',{dept:d}));
  buildMap(); applyLayout();
"""

def full_hospital(page, grade):
    """해당 등급에서 열 수 있는 모든 진료과·방, 과마다 의사 정원만큼, 의자·침대 최대."""
    boot(page, grade=grade); js(page, FILL_JS)

@pytest.mark.parametrize("w,h", PHONES + OTHER)
@pytest.mark.parametrize("grade", [0,1,2,3])
def test_no_scroll_and_min_size(page_at, w, h, grade):
    page = page_at((w, h)); full_hospital(page, grade)
    assert js(page, "document.querySelector('#mapWrap').scrollHeight <= document.querySelector('#mapWrap').clientHeight + 1")
    assert js(page, "document.documentElement.scrollWidth <= innerWidth")
    assert js(page, "parseFloat(getComputedStyle(document.querySelector('#map')).getPropertyValue('--pz'))") >= 22

def test_full_queues_do_not_grow_rooms(page_at):
    page = page_at((390, 744)); full_hospital(page, 2)
    h0 = js(page, "document.querySelector('.card[data-room=ent]').getBoundingClientRect().height")
    for _ in range(8): spawn_patient(page, sym='🤒')
    js(page, "for (let i=0;i<10;i++){ const p=spawn(true,{sym:'🤒'}); register(p); }")
    page.wait_for_timeout(400)
    assert abs(js(page, "document.querySelector('.card[data-room=ent]').getBoundingClientRect().height") - h0) < 1
    assert js(page, "document.querySelector('#mapWrap').scrollHeight <= document.querySelector('#mapWrap').clientHeight + 1")

def test_resize_midday_keeps_patients(page_at):
    page = page_at((390, 744)); boot(page)
    pid = spawn_patient(page, sym='🤒', urg=0)
    js(page, f"const p=G.patients.find(x=>x.id==={pid}); register(p); sendTo(p,'int')"); tick(page, 0.3)
    page.set_viewport_size({"width": 744, "height": 390}); page.wait_for_timeout(400)
    assert js(page, f"G.slots.int[0] && G.slots.int[0].id") == pid
    assert js(page, f"G.patients.find(x=>x.id==={pid}).el.isConnected") is True

def test_small_phone_does_not_break(page_at):
    page = page_at((360, 560)); full_hospital(page, 3)
    tick(page, 20)
    assert js(page, "G.mode") == 'play'
```


- [ ] **Step 2: 실패 확인** — `py -m pytest tests/test_fit.py -q` (현재 레이아웃은 폰에서 스크롤 발생으로 실패)
- [ ] **Step 3: 구현** — CSS 고정 높이 → `fitMap` → 대기열 겹침 → 폰 HUD 압축 → 레이아웃 재설계 순으로, 각 단계 후 테스트 재실행.
- [ ] **Step 4: 통과 + 전체 회귀** — `py -m pytest tests -q` (Task 9 말풍선 테스트 포함 전부)
- [ ] **Step 5: 수동 확인용 스크린샷** — 390×744 등급 0~3을 `tests/_shots/`(gitignore)에 저장해 사람이 눈으로 확인할 수 있게 한다.
- [ ] **Step 6: 커밋** — `fix: fit hospital map to phone screen without scrolling`

---

### Task 11: 마무리 — 안내서·문구 점검과 전체 플레이 회귀

**Files:** Modify `index.html` (안내서 `showGuide`, 상점 정원 안내 문구, README 기능 목록), `README.md`; Test `tests/test_e2e.py`

- [ ] **Step 1: 실패 테스트** — 한 판 자동 진행

```python
def test_auto_play_three_days(page_at):
    page = page_at(); boot(page, grade=3, day=12, money=20000, rooms={'exam':True,'inj':True,'rest':True,'surg':True},
                           staff_js="S.staff.push(mkStaff('nurse')); S.staff.push(mkStaff('cashier')); S.staff.push(mkStaff('pharm'))")
    errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
    for day in range(3):
        js(page, """(() => { for (let k=0;k<4000 && G.mode==='play';k++) {
            for (const p of G.patients) {
              if (p.stage==='reg') sendTo(p, p.unknown && !p.revealed ? 'exam' : p.dept);
              else if (p.stage==='next') sendTo(p, p.dest);
              else if (p.stage==='pay') pay(p);
              if (p.tantrum) for (let i=0;i<4;i++) calmKaren(p);
            }
            update(0.1);
        } })()""")
        assert js(page, "G.mode") == 'summary'
        js(page, "act('sumOk'); act('start'); setSpeed(0)")
    assert errors == []
    assert js(page, "S.day") == 15
```

  (대학병원은 최고 등급이라 승급 화면이 끼어들지 않는다.)

- [ ] **Step 2: 실행** — 실패 시 원인 수정.
- [ ] **Step 3: 안내서·README 갱신** — 안내서에 수술실·수납 간호사·의사 여러 명·직원 명부·홍보 한 줄씩, README 기능 목록과 성장 시스템에 대학병원.
- [ ] **Step 4: 전체 회귀** — `py -m pytest tests -q` → 전부 통과.
- [ ] **Step 5: 커밋** — `docs: update guide and README for university hospital update`
