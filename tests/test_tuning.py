"""2차 플레이 피드백 반영: 화면 맞춤 · 방 배치 · 평판 · 입원실 · 지원자 · 안내 간호사 · 성장 · 톡톡 안내"""
import pytest
from conftest import boot, js, tick, spawn_patient

PZ = "parseFloat(getComputedStyle(mapEl).getPropertyValue('--pz'))"
SCROLLFIT = "document.querySelector('#mapWrap').classList.contains('scrollfit')"


# ---------- 1·2. 화면 맞춤 ----------
def test_fit_ignores_walking_and_arriving_patients(page_at):
    page = page_at((1440, 900)); boot(page)
    js(page, "for (let i=0;i<4;i++) spawn(true); for (let i=0;i<3;i++) register(spawn(true)); fitMap()")
    assert js(page, SCROLLFIT) is False
    assert js(page, PZ) >= 34


@pytest.mark.parametrize("grade", [1, 3])
def test_hired_staff_badges_do_not_break_fit(page_at, grade):
    page = page_at((390, 844)); boot(page, grade=grade, rooms={'inj': True, 'rest': True})
    js(page, """for (const r of ['nurse','nurse','cashier','cashier','pharm','janitor','janitor','pnurse','inurse']) S.staff.push(mkStaff(r));
      buildMap(); applyLayout()""")
    assert js(page, SCROLLFIT) is False
    assert js(page, PZ) >= 22


def test_big_screen_uses_bigger_rooms(page_at):
    page = page_at((1440, 900)); boot(page)
    page.wait_for_timeout(200)
    assert js(page, PZ) > 40


def test_rooms_do_not_overlap_waiting_room(page_at):
    page = page_at((390, 844)); boot(page, grade=3, day=12)
    js(page, """for (const d of DEPT_ORDER) S.depts[d] = true; S.rooms = {exam:true,inj:true,rest:true,surg:true};
      for (const d of DEPT_ORDER) while (doctorsOf(d).length < docCap()) S.staff.push(mkStaff('doctor',{dept:d}));
      buildMap(); applyLayout();
      for (let i=0;i<5;i++) spawn(true); for (let i=0;i<6;i++) register(spawn(true));
      for (let i=0;i<3;i++){ const p=register(spawn(true)) || G.patients[G.patients.length-1]; sendTo(p, p.dept); }
      for (let i=0;i<40;i++) update(.1); fitMap();""")
    page.wait_for_timeout(300)
    over = js(page, """(() => { const w = document.querySelector('.card[data-room=wait]').getBoundingClientRect();
      return [...document.querySelectorAll('#map .card:not([data-room=wait]) .slot')].filter(s => { const r = s.getBoundingClientRect();
        return !(r.right <= w.left || w.right <= r.left || r.bottom <= w.top || w.bottom <= r.top); }).length })()""")
    assert over == 0
    assert js(page, SCROLLFIT) is False


def test_walking_patient_is_visible_above_rooms(page_at):
    page = page_at((430, 932)); boot(page)
    pid = spawn_patient(page, sym='🤒', urg=0)
    page.wait_for_timeout(700)
    js(page, f"register(G.patients.find(p=>p.id==={pid}))")
    # 걷는 동안: 맵 밖 최상위 층에 보이는 환자가 있고, 방 안의 진짜 환자는 숨김
    w = page.locator('body > .pt.walker')
    assert w.count() == 1
    assert js(page, "getComputedStyle(document.querySelector('body > .pt.walker')).position") == 'fixed'
    assert js(page, f"G.patients.find(p=>p.id==={pid}).el.style.visibility") == 'hidden'
    assert page.locator(f'.pt[data-id="{pid}"]').count() == 1  # 복제본은 data-id 없음
    page.wait_for_timeout(1400)
    assert page.locator('.pt.walker').count() == 0
    assert js(page, f"G.patients.find(p=>p.id==={pid}).el.style.visibility") == ''


def test_walker_cleared_when_patient_leaves(page_at):
    page = page_at((430, 932)); boot(page)
    pid = spawn_patient(page, sym='🤒', urg=0)
    page.wait_for_timeout(700)
    js(page, f"const p=G.patients.find(x=>x.id==={pid}); register(p); p.stage='pay'; toCash(p); pay(p)")
    assert page.locator('.pt.walker').count() == 0


# ---------- 3. 방 배치 바꾸기 ----------
def test_swap_same_size_rooms_and_persist(page_at):
    page = page_at((390, 844)); boot(page, grade=1, depts={'ort': True})
    js(page, "prepDay(); act('layout')")
    assert js(page, "!!G.layEdit")
    page.click('.card[data-room=int]'); page.click('.card[data-room=ort]')
    lay = js(page, "curLayout('narrow')")
    assert lay[2].split()[:2] == ['ort', 'int']
    assert 'ort int' in js(page, "mapEl.style.gridTemplateAreas")
    js(page, "act('layDone')")
    assert js(page, "!!G.layEdit") is False
    assert js(page, "JSON.parse(localStorage.getItem(SAVE_KEY)).lay.narrow1")[2].startswith('ort int')


def test_swap_different_size_refused_and_reset(page_at):
    page = page_at((390, 844)); boot(page, grade=1)
    js(page, "prepDay(); act('layout')")
    before = js(page, "curLayout('narrow').join('|')")
    assert js(page, "swapRooms('int','pharm')") is False
    assert js(page, "curLayout('narrow').join('|')") == before
    assert js(page, "swapRooms('int','ort')") is True
    js(page, "act('layReset')")
    assert js(page, "curLayout('narrow').join('|')") == before


def test_swap_two_by_two_rooms(page_at):
    page = page_at((390, 844)); boot(page, grade=2)
    assert js(page, "swapRooms('wait','ward')") is True
    lay = js(page, "curLayout('narrow')")
    assert lay[0] == 'ent ward ward' and lay[5].startswith('wait wait')


# ---------- 4·5. 평판 ----------
def test_combo_break_costs_rep(page_at):
    page = page_at(); boot(page, rep=80)
    pid = spawn_patient(page, sym='🤒', urg=0)
    js(page, f"G.combo = 5; wrongMove(G.patients.find(p=>p.id==={pid}))")
    assert js(page, "S.rep") < 80
    assert js(page, "G.combo") == 0


def test_rep_gain_shrinks_near_top(page_at):
    page = page_at(); boot(page, rep=30)
    low = js(page, "(() => { S.rep = 30; addRep(1); return S.rep - 30 })()")
    high = js(page, "(() => { S.rep = 90; addRep(1); return S.rep - 90 })()")
    assert high < low * 0.7
    assert js(page, "(() => { S.rep = 90; addRep(-3); return S.rep })()") == 87


def test_high_rep_pays_more(page_at):
    def earn(rep):
        page = page_at(); boot(page, rep=rep)
        m0 = js(page, "S.money")
        js(page, "const p = spawn(true,{sym:'🤒',urg:0}); p.stage='pay'; p.fee=100; toCash(p); p.cashT = -99; pay(p)")
        return js(page, "S.money") - m0
    base, top = earn(40), earn(96)
    assert top >= base * 1.4
    assert earn(80) > base


def test_rep_tier_shown_in_prep(page_at):
    page = page_at(); boot(page, rep=85)
    js(page, "prepDay()")
    assert '+25%' in page.locator('.modal').inner_text()


# ---------- 6. 입원실 침대 ----------
def test_ward_beds_start_at_two_and_grow_by_two(page_at):
    page = page_at(); boot(page)
    assert js(page, "G.slots.ward.length") == 2
    for lv, n in [(1, 4), (2, 6), (3, 8)]:
        js(page, f"S.up.ward = {lv}; buildMap(); applyLayout()")
        assert js(page, "G.slots.ward.length") == n


# ---------- 7. 지원자 · 일급 ----------
def test_wage_grows_faster_than_stats(page_at):
    page = page_at(); boot(page)
    lo = js(page, "wageOf({spd:1,kind:1,lvl:1})"); mid = js(page, "wageOf({spd:3,kind:3,lvl:1})"); hi = js(page, "wageOf({spd:5,kind:5,lvl:1})")
    assert hi - mid > mid - lo
    assert hi >= lo * 6


def test_continue_recomputes_old_wages(page_at):
    page = page_at(); boot(page)
    js(page, "S.staff[0].spd = 5; S.staff[0].kind = 5; S.staff[0].wage = 82; save(); showTitle()")
    page.click('#tCont')
    assert js(page, "S.staff[0].wage") == js(page, "wageOf(S.staff[0])") > 82


def test_skilled_candidates_show_up(page_at):
    page = page_at(); boot(page, grade=1, day=6)
    sums = js(page, "(() => { const out = []; for (let k=0;k<40;k++) { genCands(); out.push(...S.cands.map(c => c.spd + c.kind)); } return out })()")
    assert max(sums) >= 8
    assert sum(1 for s in sums if s >= 7) >= 8


def test_every_day_from_three_has_a_good_candidate(page_at):
    page = page_at(); boot(page, grade=0, day=3)
    for _ in range(20):
        js(page, "genCands()")
        assert js(page, "S.cands.some(c => c.spd + c.kind >= 6)")


# ---------- 8. 약국 · 주사 안내 간호사 ----------
def mk_next(page, dest):
    return js(page, f"(() => {{ const p = spawn(true,{{sym:'🤒',urg:0}}); register(p); p.done=true; p.dest='{dest}'; p.stage='next'; p.nextT=G.t; updBub(p); return p.id }})()")


def test_pharm_guide_nurse_routes_after_general_hospital(page_at):
    page = page_at(); boot(page, grade=2, staff_js="S.staff.push(mkStaff('pnurse',{spd:5,kind:2}))")
    pid = mk_next(page, 'pharm')
    tick(page, 2)
    assert js(page, f"(G.patients.find(p=>p.id==={pid})||{{}}).target") == 'pharm'


def test_pharm_guide_nurse_locked_before_general(page_at):
    page = page_at(); boot(page, grade=1, day=6)
    assert js(page, "capOf('pnurse')") == 0
    for _ in range(20):
        js(page, "genCands()")
        assert js(page, "S.cands.every(c => c.role !== 'pnurse' && c.role !== 'inurse')")


def test_inj_guide_nurse_at_university(page_at):
    page = page_at(); boot(page, grade=2, rooms={'inj': True})
    assert js(page, "capOf('inurse')") == 0
    page2 = page_at(); boot(page2, grade=3, rooms={'inj': True}, staff_js="S.staff.push(mkStaff('inurse',{spd:5,kind:2}))")
    assert js(page2, "capOf('inurse')") >= 1
    pid = mk_next(page2, 'inj')
    tick(page2, 2)
    assert js(page2, f"(G.patients.find(p=>p.id==={pid})||{{}}).target") == 'inj'


def test_guide_nurse_candidates_offered(page_at):
    page = page_at(); boot(page, grade=3, day=6, rooms={'inj': True},
                           staff_js="S.staff.push(mkStaff('nurse')); S.staff.push(mkStaff('janitor')); S.staff.push(mkStaff('cashier'))")
    js(page, "genCands()")
    roles = js(page, "S.cands.map(c => c.role)")
    assert 'pnurse' in roles or 'inurse' in roles


# ---------- 9. 느린 간호사는 밀림 ----------
def test_slow_nurse_falls_behind(page_at):
    def registered(spd):
        page = page_at(); boot(page, staff_js=f"S.staff.push(mkStaff('nurse',{{spd:{spd},kind:2}}))")
        js(page, "G.spawnT = 999; for (let i=0;i<6;i++) spawn(true)")
        tick(page, 6)
        return js(page, "G.patients.filter(p => p.stage !== 'new').length"), page
    slow, page = registered(1)
    fast, _ = registered(5)
    assert fast >= slow + 2
    assert js(page, "navInt({spd:1}) > 5 && navInt({spd:5}) < 2")


def test_backlog_badge_when_nurse_is_behind(page_at):
    page = page_at(); boot(page, staff_js="S.staff.push(mkStaff('nurse',{spd:1,kind:2}))")
    js(page, "G.spawnT = 999; for (let i=0;i<5;i++) spawn(true); renderStaff()")
    badge = page.locator('.card[data-room=ent] .backlog')
    assert badge.count() == 1 and '5' in badge.inner_text()


# ---------- 10. 성장 속도 ----------
def test_natural_growth_is_slow(page_at):
    page = page_at(); boot(page)
    js(page, "window.T = mkStaff('nurse',{spd:2,kind:2}); for (let i=0;i<60;i++) work(T, 0)")
    assert js(page, "T.spd + T.kind") <= 5
    assert js(page, "T.lvl") <= 3


def test_training_available_from_clinic(page_at):
    page = page_at(); boot(page, grade=0, money=10000)
    js(page, "S.staff[0].spd = 2; G.mode='prep'; buy('train:' + S.staff[0].id + ':spd')")
    assert js(page, "S.staff[0].spd") == 3


# ---------- 11. 톡톡 안내 ----------
def test_tap_patient_then_tap_room(page_at):
    page = page_at((430, 932)); boot(page)
    pid = spawn_patient(page, sym='🤒', urg=0)
    js(page, f"register(G.patients.find(p=>p.id==={pid})); setSpeed(1)")
    page.wait_for_timeout(900)
    page.click(f'.pt[data-id="{pid}"]')
    assert js(page, f"G.sel && G.sel.id") == pid
    page.click('.card[data-room=int] .ch')
    assert js(page, f"(G.patients.find(p=>p.id==={pid})||{{}}).target") == 'int' or js(page, f"G.slots.int[0] && G.slots.int[0].id") == pid


def drag_to(page, pid, room):
    a = page.locator(f'.pt[data-id="{pid}"]').bounding_box(); b = page.locator(f'.card[data-room={room}]').bounding_box()
    page.mouse.move(a['x'] + a['width'] / 2, a['y'] + a['height'] / 2); page.mouse.down()
    page.mouse.move(b['x'] + b['width'] / 2, b['y'] + b['height'] / 2, steps=8)
    ghost = page.locator('.pt.ghost').count()
    page.mouse.up()
    return ghost


def test_drag_and_drop_also_routes(page_at):
    page = page_at((430, 932)); boot(page)
    pid = spawn_patient(page, sym='🤒', urg=0)
    js(page, f"register(G.patients.find(p=>p.id==={pid})); setSpeed(1)")
    page.wait_for_timeout(900)
    assert drag_to(page, pid, 'int') == 1
    page.wait_for_timeout(100)
    assert js(page, f"(G.patients.find(p=>p.id==={pid})||{{}}).target") == 'int' or js(page, f"G.slots.int[0] && G.slots.int[0].id") == pid
    assert page.locator('.pt.ghost').count() == 0
    assert js(page, "G.sel") is None


def test_tap_then_drag_another_patient(page_at):
    # 하나를 톡으로 고른 상태에서 다른 환자를 끌어도 끈 환자가 가야 함
    page = page_at((430, 932)); boot(page)
    a = spawn_patient(page, sym='🤒', urg=0); b = spawn_patient(page, sym='🤒', urg=0)
    js(page, f"register(G.patients.find(p=>p.id==={a})); register(G.patients.find(p=>p.id==={b})); setSpeed(1)")
    page.wait_for_timeout(900)
    page.click(f'.pt[data-id="{a}"]')
    drag_to(page, b, 'int'); page.wait_for_timeout(100)
    assert js(page, f"G.patients.find(p=>p.id==={a}).stage") == 'reg'
    assert js(page, f"(G.patients.find(p=>p.id==={b})||{{}}).target") == 'int' or js(page, f"G.slots.int[0] && G.slots.int[0].id") == b


def test_reception_line_keeps_arrival_order_when_seats_full(page_at):
    # 의자가 꽉 차서 접수 끝난 환자가 입구에 서 있어도 줄 순서는 온 순서 그대로, 접수 끝난 사람은 🪑 대기 표시
    page = page_at(); boot(page, grade=1, staff_js="S.staff.push(mkStaff('nurse',{spd:1}))")
    js(page, "G.spawnT = 999; G.emergTimes = []; G.event = null")
    js(page, "for (let i = 0; i < G.seats.length; i++) { const p = spawn(true, {sym:'🤒', urg:0}); register(p); }")
    ids = []
    for _ in range(5):
        ids.append(js(page, "spawn(true, {sym:'🤒', urg:0}).id")); tick(page, 4)
    line = js(page, "[...G.entQ.children].map(e => +e.dataset.id)")
    assert line == sorted(line) == ids
    standing = js(page, "[...G.entQ.children].filter(e => e.classList.contains('standing')).map(e => +e.dataset.id)")
    reg = js(page, "G.patients.filter(p => p.loc === 'ent' && p.stage !== 'new').map(p => p.id)")
    assert standing == reg and len(reg) >= 2
    # 자리가 나면 먼저 온 사람부터 대기실로, 표시도 사라짐
    js(page, "const s = G.seats.find(Boolean); leave(s); removeP(s, 'bye'); update(.05)")
    assert js(page, f"G.patients.find(p => p.id === {ids[0]}).loc") == 'seat'
    assert js(page, f"G.patients.find(p => p.id === {ids[0]}).el.classList.contains('standing')") is False
