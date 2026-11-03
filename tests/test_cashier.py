from conftest import boot, js, tick

CASHIER = "S.staff.push(mkStaff('cashier',{spd:3,kind:2}))"


def mk_payer(page):
    return js(page, "(() => { const p = spawn(true,{sym:'🤒',urg:0}); p.stage='pay'; p.fee=40; toCash(p); return p.id })()")


def test_cashier_auto_pays_without_fast_tip(page_at):
    page = page_at(); boot(page, grade=1, staff_js=CASHIER)
    mk_payer(page); m0 = js(page, "S.money")
    tick(page, 1)
    assert js(page, "G.patients.length") == 0
    assert js(page, "S.money") - m0 == 50  # 40 + round(40*.25*pat/100)=10, no fast tip


def test_manual_pay_still_gets_fast_tip(page_at):
    page = page_at(); boot(page, grade=1)
    pid = mk_payer(page); m0 = js(page, "S.money")
    js(page, f"pay(G.patients.find(p=>p.id==={pid}))")
    assert js(page, "S.money") - m0 == 55


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
    assert js(page, "hireCheck(mkStaff('cashier')).ok") is False


def test_cashier_guaranteed_at_hospital(page_at):
    page = page_at(); boot(page, grade=1, day=4)
    js(page, "S.staff.push(mkStaff('nurse')); S.staff.push(mkStaff('janitor')); genCands()")
    assert js(page, "S.cands.some(c => c.role === 'cashier')")
    assert js(page, "capOf('cashier')") == 1
    js(page, "S.grade = 2")
    assert js(page, "capOf('cashier')") == 2


def test_cashier_badge_on_cash_card(page_at):
    page = page_at(); boot(page, grade=1, staff_js=CASHIER)
    js(page, "renderStaff()")
    assert page.locator('.card[data-room=cash] [data-staff=cash] .sb').count() == 1
