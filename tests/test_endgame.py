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
