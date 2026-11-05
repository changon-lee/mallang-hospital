from conftest import boot, js, tick, spawn_patient

# 토스트 기록용: toast()를 감싸서 window._T 에 쌓음
SPY = "window._T = []; { const o = toast; toast = (h, c) => { _T.push(h); o(h, c); }; } 0"


def pay_ready(page, fee=100, **o):
    """수납 대기 환자 하나 (팁 0, 빠른 수납 팁 없음)."""
    pid = spawn_patient(page, **o)
    js(page, f"(() => {{ const p = G.patients.find(x => x.id === {pid}); p.stage = 'pay'; p.fee = {fee}; p.pat = 0; toCash(p); p.cashT = -10; }})()")
    return pid


def do_pay(page, pid):
    js(page, f"pay(G.patients.find(x => x.id === {pid}))")


# ---------- Task 1: 상태 + 트로피 ----------

def test_new_state_has_endgame_fields(page_at):
    page = page_at(); boot(page)
    assert js(page, "[S.eq, S.res.cur, S.annex.lv, S.donated, S.life.heli, Object.keys(S.troph).length]") == [{}, None, 0, 0, 0, 0]


def test_old_save_loads_with_defaults(page_at):
    page = page_at()
    js(page, """(() => { newState(); S.tut = true; S.grade = 2; S.total = 250;
      Object.assign(S.depts, {ort:true, eye:true, den:true, skin:true, obgy:true});
      for (const k of ['eq','res','annex','donated','volLast','life','troph']) delete S[k];
      localStorage.setItem(SAVE_KEY, JSON.stringify(S)); showTitle(); })()""")
    js(page, SPY)
    page.click('#tCont')
    assert page.js_errors == []
    assert js(page, "S.res.done") == {} and js(page, "S.life.maxCombo") == 0
    got = js(page, "Object.keys(S.troph)")
    for t in ['first', 't100', 'grade1', 'grade2']:
        assert t in got
    assert not any('트로피' in h for h in js(page, "_T"))


def test_trophy_count_and_mul(page_at):
    page = page_at(); boot(page)
    assert js(page, "TROPHIES.length") == 28
    assert len(set(js(page, "TROPHIES.map(t => t.id)"))) == 28
    js(page, "S.troph = {a:1, b:2, c:3}")
    assert abs(js(page, "trophyMul()") - 1.03) < 1e-9


def test_pay_uses_trophy_mul(page_at):
    page = page_at(); boot(page, rep=30)
    js(page, "S.troph = {}; for (let i = 0; i < 10; i++) S.troph['x' + i] = 1")
    pid = pay_ready(page, vip=False, karen=False, multi=False)
    m0 = js(page, "S.money"); do_pay(page, pid)
    assert js(page, "S.money") - m0 == 110
    assert js(page, "G.stats.trophBonus") == 10 and js(page, "G.stats.repBonus") == 0


def test_combo_trophy_instant(page_at):
    page = page_at(); boot(page)
    js(page, SPY)
    js(page, "G.combo = 19")
    pid = pay_ready(page, vip=False, karen=False, multi=False)
    do_pay(page, pid)
    assert js(page, "!!S.troph.combo20") and js(page, "S.life.maxCombo") == 20
    assert any('🏆' in h for h in js(page, "_T"))


def test_trophy_hall_shows_locked_and_owned(page_at):
    page = page_at(); boot(page)
    pid = pay_ready(page, vip=False, karen=False, multi=False); do_pay(page, pid)
    js(page, "G.mode = 'prep'; showTrophies()")
    assert page.locator('.modal .troph.own').count() >= 1
    assert page.locator('.modal .troph.lock').count() >= 1
    assert '/' in page.locator('.modal').inner_text()


# ---------- Task 2: 장비 ----------

def treat_fee(page, room, sym):
    """환자를 room 에 넣고 진료를 바로 끝내서 붙은 진료비를 돌려줌."""
    pid = spawn_patient(page, sym=sym, urg=0, unknown=False, multi=False, karen=False, vip=False)
    return js(page, f"""(() => {{ const p = G.patients.find(x => x.id === {pid}); register(p); sendTo(p, '{room}'); update(.05);
      p.phase = 'treat'; svcStep('{room}', p.slot, p); return p.fee; }})()""")


def test_eq_locked_by_grade(page_at):
    page = page_at(); boot(page, grade=0, money=99999)
    assert js(page, "eqMax()") == 0
    js(page, "G.mode='prep'; buy('eq:int')")
    assert js(page, "S.eq.int || 0") == 0 and js(page, "S.money") == 99999
    page2 = page_at(); boot(page2, grade=1, money=99999)
    js(page2, "G.mode='prep'; buy('eq:int')")
    assert js(page2, "S.eq.int") == 1 and js(page2, "S.money") == 99999 - 250
    js(page2, "S.eq.int = 3; buy('eq:int')")
    assert js(page2, "S.eq.int") == 3


def test_eq_price_curve(page_at):
    page = page_at(); boot(page)
    assert js(page, "eqPrice('int', 0)") == 250
    assert js(page, "eqPrice('int', 9)") == round(250 * 1.45 ** 9 / 10) * 10
    assert js(page, "eqPrice('ort', 0)") == 290
    assert js(page, "eqPrice('exam', 0)") == 300 and js(page, "eqPrice('peds', 0)") == 600


def test_eq_speed_and_fee_exact(page_at):
    page = page_at(); boot(page, grade=3)
    js(page, "S.eq.int = 5; S.up.clinic = 0; doctorOf('int').spd = 2")
    assert abs(js(page, "treatDur('int')") - 7 / 1.0 / 1 / 1.3) < 1e-9
    assert abs(treat_fee(page, 'int', '🤒') - 30 * 1.15) < 1e-9


def test_eq_room_speed(page_at):
    page = page_at(); boot(page, grade=3, rooms={'exam': True, 'surg': True})
    js(page, "S.eq.exam = 4; S.eq.surg = 2")
    assert abs(js(page, "svcDur('exam')") - 3.5 / 1.24) < 1e-9
    fee = js(page, """(() => { const p = spawn(true, {sym:'🦴', urg:0, unknown:false, multi:false, karen:false, vip:false});
      p.done = true; p.dest = 'surg'; p.stage = 'next'; sendTo(p, 'surg'); update(.05); p.phase = 'treat'; svcStep('surg', p.slot, p); return p.fee; })()""")
    assert abs(fee - (120 + js(page, "S.day") * 3) * 1.06) < 1e-9


def test_eq_tab_shows_now_next(page_at):
    page = page_at(); boot(page, grade=2, rooms={'exam': True})
    js(page, "G.mode='prep'; showShop('eq')")
    txt = page.locator('.modal').inner_text()
    assert '→' in txt and 'X-ray' in txt and '내과' in txt


# ---------- Task 3: 기부 · 봉사 진료 ----------

def prep(page):
    js(page, "prepDay()")


def test_donate_once_per_day(page_at):
    page = page_at(); boot(page, grade=2, day=10, money=10000, rep=50)
    prep(page)
    js(page, "act('give:big')")
    assert js(page, "S.money") == 10000 - 2000 and js(page, "S.donated") == 2000
    assert js(page, "S.rep") > 50
    js(page, "act('give:small')")
    assert js(page, "S.money") == 8000
    page2 = page_at(); boot(page2, grade=1, day=10, money=10000)
    prep(page2); js(page2, "act('give:small')")
    assert js(page2, "S.money") == 10000 and js(page2, "S.donated") == 0


def test_give_box_in_prep(page_at):
    page = page_at(); boot(page, grade=2, day=10)
    js(page, "prepDay()")
    txt = page.locator('.modal').inner_text()
    assert '기부' in txt and '봉사 진료' in txt
    page2 = page_at(); boot(page2, grade=1, day=10)
    js(page2, "prepDay()")
    assert '봉사 진료' not in page2.locator('.modal').inner_text()


def test_volunteer_cooldown(page_at):
    page = page_at(); boot(page, grade=2, day=10)
    prep(page); js(page, "act('vol')")
    assert js(page, "G.vol") is True and js(page, "S.volLast") == 10
    js(page, "S.day = 12")
    assert js(page, "volReady()") is False
    js(page, "S.day = 13")
    assert js(page, "volReady()") is True


def test_volunteer_day_zero_income_wages_paid(page_at):
    page = page_at(); boot(page, grade=2, day=10, money=5000)
    prep(page); js(page, "act('vol'); act('start'); setSpeed(0); G.goals = []; G.event = null")  # 위생 점검 벌금 같은 이벤트 제외
    m0 = js(page, "S.money")
    js(page, "G.combo = 4")
    pid = pay_ready(page, vip=True, karen=False, multi=False); do_pay(page, pid)
    assert js(page, "S.money") == m0 and js(page, "G.stats.income") == 0
    wages = js(page, "S.staff.reduce((a, s) => a + s.wage, 0)")
    js(page, "G.t = 181; update(.1)")
    assert js(page, "G.mode") == 'summary'
    assert js(page, "S.money") == m0 - wages
    assert '봉사 진료' in page.locator('.modal').inner_text()
    assert js(page, "S.life.volDays") == 1


def test_volunteer_rep_and_combo(page_at):
    page = page_at(); boot(page, grade=2, day=10, rep=50)
    prep(page); js(page, "act('vol'); act('start'); setSpeed(0); S.rep = 50")
    pid = pay_ready(page, vip=False, karen=False, multi=False); do_pay(page, pid)
    assert abs(js(page, "S.rep") - (50 + 1.0 * (1 - .55 * .25))) < 1e-9
    r0 = js(page, "S.rep"); js(page, "G.combo = 5; breakCombo()")
    assert abs(js(page, "S.rep") - (r0 - 0.75)) < 1e-9
    js(page, "Math.random = () => 0.5")
    base = js(page, "G.vol = false, spawnInterval()")
    assert abs(js(page, "G.vol = true, spawnInterval()") - base / 1.3) < 1e-9


# ---------- Task 4: 연구 ----------

def test_research_gating(page_at):
    page = page_at(); boot(page, grade=1, day=10, money=50000)
    js(page, "prepDay(); act('res:diag')")
    assert js(page, "S.res.cur") is None and js(page, "S.money") == 50000
    page2 = page_at(); boot(page2, grade=2, day=10, money=50000)
    js(page2, "prepDay(); act('res:exam2')")
    assert js(page2, "S.res.cur") is None
    js(page2, "act('res:diag')")
    assert js(page2, "S.res.cur") == {'id': 'diag', 'left': 1} and js(page2, "S.money") == 47000
    js(page2, "act('res:kind')")
    assert js(page2, "S.res.cur.id") == 'diag' and js(page2, "S.money") == 47000
    js(page2, "act('start'); act('res:kind')")
    assert js(page2, "S.money") == 47000


def test_research_completes_after_days(page_at):
    page = page_at(); boot(page, grade=2, day=10, money=50000)
    js(page, "prepDay(); act('res:diag'); act('start'); setSpeed(0); G.goals = []; G.t = 181; update(.1)")
    assert js(page, "G.mode") == 'summary' and js(page, "hasRes('diag')") is True
    assert '연구비' in page.locator('.modal').inner_text()
    js(page, SPY); js(page, "act('sumOk')")
    assert any('연구 완료' in h for h in js(page, "_T"))
    js(page, "act('res:exam2')")
    assert js(page, "S.res.cur.id") == 'exam2'


def test_research_effects_exact(page_at):
    page = page_at(); boot(page, grade=2, day=10, rooms={'exam': True})
    js(page, "S.troph = {}; S.res.done = {}")
    t0 = js(page, "treatDur('int')"); ph0 = js(page, "svcDur('pharm')")
    nav0 = js(page, "navInt({spd:3})"); em0 = js(page, "emergLimit()")
    js(page, "S.res.done = {diag:1, exam2:1, drug:1, smart:1, erp:1, mgmt:1}")
    assert abs(js(page, "treatDur('int')") - t0 * .9) < 1e-9
    assert abs(js(page, "svcDur('exam')") - 3.5 * .7) < 1e-9
    assert abs(js(page, "svcDur('pharm')") - ph0 * .75) < 1e-9
    assert abs(js(page, "navInt({spd:3})") - nav0 * .8) < 1e-9
    assert js(page, "emergLimit()") == em0 + 8
    js(page, "S.rep = 30")
    pid = pay_ready(page, vip=False, karen=False, multi=False)
    m0 = js(page, "S.money"); do_pay(page, pid)
    assert js(page, "S.money") - m0 == 110


def test_ax_branch_needs_annex(page_at):
    page = page_at(); boot(page, grade=3, day=15, money=99999)
    js(page, "prepDay(); act('res:play')")
    assert js(page, "S.res.cur") is None
    js(page, "S.annex.lv = 1; act('res:play')")
    assert js(page, "S.res.cur.id") == 'play'


def test_lab_window_lists_branches(page_at):
    page = page_at(); boot(page, grade=2, day=10)
    js(page, "prepDay(); showResearch()")
    txt = page.locator('.modal').inner_text()
    for w in ['진료', '운영', '신관', '→', '신속 진단']:
        assert w in txt


# ---------- Task 5: 신관 공사 ----------

ALLD = {'ort': True, 'eye': True, 'den': True, 'skin': True, 'obgy': True, 'ear': True, 'neu': True}
ALLR = {'exam': True, 'inj': True, 'rest': True, 'surg': True}
CARDS_FIT = "[...document.querySelectorAll('#map .card')].every(c => c.scrollHeight <= c.clientHeight + 1)"
PZ = "parseFloat(getComputedStyle(mapEl).getPropertyValue('--pz'))"


def end_day(page):
    js(page, "act('start'); setSpeed(0); G.goals = []; G.t = 181; update(.1)")
    assert js(page, "G.mode") == 'summary'


def test_annex_card_only_at_grade3(page_at):
    page = page_at(); boot(page, grade=2)
    assert page.locator('.card[data-room=annex]').count() == 0
    page2 = page_at(); boot(page2, grade=3)
    assert page2.locator('.card[data-room=annex]').count() == 1
    assert page2.locator('.card[data-room=annex] .axs.off').count() == 5


def test_build_and_rush(page_at):
    page = page_at(); boot(page, grade=3, money=100000)
    js(page, "prepDay(); act('axBuild')")
    assert js(page, "S.money") == 92000 and js(page, "S.annex.build") == {'stage': 0, 'left': 3}
    js(page, "act('axRush')")
    assert js(page, "S.money") == 92000 - 2800 and js(page, "S.annex.build.left") == 2
    js(page, "act('axRush'); act('axRush')")
    assert js(page, "S.annex.lv") == 1 and js(page, "S.annex.build") is None
    assert js(page, "S.money") == 92000 - 2800 * 3
    assert page.locator('.axs[data-ax=peds]:not(.off)').count() == 1


def test_build_progresses_daily_and_upkeep(page_at):
    page = page_at(); boot(page, grade=3, money=100000)
    js(page, "prepDay(); act('axBuild')")
    end_day(page)
    assert '공사비' in page.locator('.modal').inner_text()
    js(page, "act('sumOk')"); end_day(page); js(page, "act('sumOk')"); end_day(page)
    assert js(page, "S.annex.lv") == 1
    js(page, "act('sumOk')")
    assert '완공' in page.locator('.modal').inner_text()
    end_day(page)
    txt = page.locator('.modal').inner_text()
    assert '신관 운영비' in txt and '-💰200' in txt


def test_build_blocked_during_play(page_at):
    page = page_at(); boot(page, grade=3, money=100000)
    js(page, "act('axBuild')")
    assert js(page, "S.annex.build") is None and js(page, "S.money") == 100000


def test_annex_window(page_at):
    page = page_at(); boot(page, grade=3, money=100000)
    js(page, "prepDay(); showAnnex()")
    txt = page.locator('.modal').inner_text()
    for w in ['소아과', '응급실', '재활치료실', 'VIP 특실', '헬기장', '8,000']:
        assert w in txt


def test_annex_fits_screen(page_at):
    # 신관 카드가 들어와도 방이 많이 작아지지 않음 (추가 전 기준: 1440x900 39 · 390x744 22)
    for size, base in [((1440, 900), 39), ((390, 744), 22)]:
        page = page_at(size); boot(page, grade=3, depts=ALLD, rooms=ALLR)
        js(page, "S.annex.lv = 5; buildMap(); applyLayout()")
        assert js(page, CARDS_FIT), size
        assert js(page, PZ) >= base * .85, (size, js(page, PZ))


# ---------- Task 6: 신관 칸 운영 ----------

def annex_day(page, lv, **kw):
    boot(page, grade=3, day=15, money=50000, **kw)
    js(page, f"S.annex.lv = {lv}; prepDay(); act('start'); setSpeed(0); G.ambTimes = []; G.heliTimes = []; G.emergTimes = []; G.spawnT = 999")


def P(pid):
    return f"G.patients.find(x => x.id === {pid})"


def test_child_flow(page_at):
    page = page_at(); annex_day(page, 1)
    pid = spawn_patient(page, child=True)
    js(page, f"register({P(pid)})")
    assert '🧸' in js(page, f"{P(pid)}.bubEl.textContent")
    tick(page, 2.5)
    assert js(page, f"{P(pid)}.stage") == 'annex' and js(page, f"{P(pid)}.ax") == 'peds'
    tick(page, 6.5)
    assert js(page, f"{P(pid)}.stage") == 'pay' and abs(js(page, f"{P(pid)}.fee") - 70) < 1e-9


def test_child_to_dept_is_gentle(page_at):
    page = page_at(); annex_day(page, 1)
    pid = spawn_patient(page, child=True)
    js(page, f"register({P(pid)}); G.combo = 3; sendTo({P(pid)}, 'int')")
    assert js(page, f"{P(pid)}.stage") == 'reg' and js(page, "G.combo") == 3 and js(page, "G.stats.wrong") == 0
    assert js(page, f"validRooms({P(pid)})").count('annex') == 1


def test_ambulance_auto_to_er(page_at):
    page = page_at(); boot(page, grade=3, day=15)
    js(page, "S.annex.lv = 2; prepDay()")
    assert js(page, "G.ambTimes.length") == 2
    js(page, "act('start'); setSpeed(0); G.ambTimes = []; G.heliTimes = []; G.emergTimes = []; G.spawnT = 999")
    pid = js(page, "spawnAmb().id")
    tick(page, 1)
    assert js(page, f"{P(pid)}.stage") == 'annex' and js(page, f"{P(pid)}.ax") == 'er' and js(page, f"{P(pid)}.saved") is True
    tick(page, 8.5)
    assert js(page, f"{P(pid)}.stage") == 'pay' and js(page, f"{P(pid)}.fee") >= 90


def test_existing_emergency_to_er(page_at):
    page = page_at(); annex_day(page, 2)
    pid = js(page, "spawn(true, {emerg:true}).id")
    js(page, f"sendTo({P(pid)}, 'annex')")
    assert js(page, f"{P(pid)}.saved") is True and js(page, "G.stats.emergOk") == 1
    assert js(page, f"{P(pid)}.ax") == 'er'


def test_rehab_dest(page_at):
    page = page_at(); annex_day(page, 3)
    pid = spawn_patient(page, sym='🦴', urg=0, unknown=False, multi=False, karen=False, vip=False)
    assert js(page, f"(() => {{ const r = Math.random; Math.random = () => .999; const d = rollDest('ort', {P(pid)}); Math.random = r; return d; }})()") == 'rehab'
    js(page, f"register({P(pid)}); {P(pid)}.done = true; assignDest({P(pid)}, 'rehab')")
    assert js(page, f"{P(pid)}.bubEl.textContent") == '🦿'
    tick(page, 2.5)
    assert js(page, f"{P(pid)}.stage") == 'annex' and js(page, f"{P(pid)}.ax") == 'rehab'


def test_vip_suite_and_discharge(page_at):
    page = page_at(); annex_day(page, 4)
    pid = spawn_patient(page, sym='🤰', urg=0, unknown=False, multi=False, karen=False, vip=True)
    assert js(page, f"(() => {{ const r = Math.random; Math.random = () => 0; const d = rollDest('obgy', {P(pid)}); Math.random = r; return d; }})()") == 'suite'
    js(page, f"register({P(pid)}); {P(pid)}.done = true; assignDest({P(pid)}, 'suite')")
    tick(page, 2.5)
    assert js(page, f"{P(pid)}.stage") == 'ward' and js(page, f"{P(pid)}.ax") == 'suite'
    exp = js(page, f"(() => {{ const p = {P(pid)}; return Math.round((p.fee + 120 + S.day*6 + extraPay(p)) * 2 * incomeMul()); }})()")
    js(page, f"for (const p of G.patients.slice()) if (p.id !== {pid}) removeP(p, 'bye'); G.goals = []; G.t = 181; update(.1)")
    assert js(page, "G.mode") == 'summary'
    assert js(page, "G.stats.annexIncome") == exp
    assert '신관 수입' in page.locator('.modal').inner_text()


def test_suite_full_falls_back_to_ward(page_at):
    page = page_at(); annex_day(page, 4)
    ids = [spawn_patient(page, sym='🤰', urg=0, unknown=False, multi=False, karen=False, vip=True) for _ in range(3)]
    for pid in ids:
        js(page, f"register({P(pid)}); {P(pid)}.done = true; toAnnex({P(pid)}, 'suite')")
    assert js(page, "G.ax.suite.slots.filter(Boolean).length") == 2
    assert js(page, f"{P(ids[2])}.ax || null") is None


def test_heli_auto_pay(page_at):
    page = page_at(); boot(page, grade=3, day=15)
    js(page, "S.annex.lv = 5; prepDay()")
    assert js(page, "G.heliTimes.length") in (1, 2)
    js(page, "act('start'); setSpeed(0); G.ambTimes = []; G.heliTimes = []; G.emergTimes = []; G.spawnT = 999")
    exp = js(page, "Math.round((400 + S.day*10) * incomeMul())")
    m0 = js(page, "S.money"); js(page, "spawnHeli()")
    tick(page, 10.5)
    assert js(page, "S.money") - m0 == exp and js(page, "S.life.heli") == 1


def test_annex_backlog_badge(page_at):
    page = page_at(); annex_day(page, 1)
    for _ in range(4):
        pid = spawn_patient(page, child=True)
        js(page, f"register({P(pid)}); toAnnex({P(pid)}, 'peds')")
    js(page, "renderAnnex()")
    assert page.locator('.axs[data-ax=peds] .backlog').count() == 1


def test_day_waits_for_annex_and_suite_discharges(page_at):
    page = page_at(); annex_day(page, 4)
    c = spawn_patient(page, child=True)
    v = spawn_patient(page, sym='🤰', urg=0, unknown=False, multi=False, karen=False, vip=True)
    js(page, f"register({P(c)}); toAnnex({P(c)}, 'peds'); register({P(v)}); {P(v)}.done = true; toAnnex({P(v)}, 'suite'); G.goals = []; G.t = 181; update(.1)")
    assert js(page, "G.mode") == 'play'
    tick(page, 7)
    js(page, f"pay({P(c)}); update(.1)")
    assert js(page, "G.mode") == 'summary'


def test_auto_play_with_annex(page_at):
    from test_e2e import AUTO
    page = page_at((390, 744))
    boot(page, grade=3, day=15, money=50000, rep=90, depts=ALLD, rooms=ALLR,
         staff_js="S.staff.push(mkStaff('nurse')); S.staff.push(mkStaff('cashier')); S.staff.push(mkStaff('pharm'))")
    js(page, "S.annex.lv = 5; prepDay(); act('start'); setSpeed(0)")
    inc = 0
    for _ in range(3):
        js(page, AUTO)
        assert js(page, "G.mode") == 'summary'
        inc += js(page, "G.stats.annexIncome")
        js(page, "act('sumOk'); act('start'); setSpeed(0)")
    assert page.js_errors == [] and inc > 0
