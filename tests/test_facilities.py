from conftest import boot, js, tick, spawn_patient

ALLR = {'exam': True, 'inj': True, 'rest': True, 'surg': True}


def prep(page):
    js(page, "prepDay()")


# ---------- 방·설비 업그레이드 ----------

def test_new_upgrade_prices_scale_with_effect(page_at):
    page = page_at(); boot(page)
    assert js(page, "UPS.inj.prices") == [2500, 6000]
    assert js(page, "UPS.surg.prices") == [5000, 12000]
    assert js(page, "UPS.rest.prices") == [1500, 3500, 7000]


def test_inj_beds_add_slots(page_at):
    page = page_at(); boot(page, grade=1, money=99999, rooms={'inj': True})
    prep(page)
    assert page.locator('.card[data-room=inj] .slot').count() == 1
    js(page, "buy('up:inj')")
    assert js(page, "S.up.inj") == 1 and js(page, "S.money") == 99999 - 2500
    assert page.locator('.card[data-room=inj] .slot').count() == 2
    assert js(page, "G.slots.inj.length") == 2
    js(page, "buy('up:inj'); buy('up:inj')")
    assert js(page, "S.up.inj") == 2 and page.locator('.card[data-room=inj] .slot').count() == 3


def test_upgrade_needs_its_room(page_at):
    page = page_at(); boot(page, grade=3, money=99999)
    prep(page); js(page, "buy('up:surg'); buy('up:inj'); buy('up:rest')")
    assert js(page, "[S.up.surg, S.up.inj, S.up.rest]") == [0, 0, 0] and js(page, "S.money") == 99999
    js(page, "showShop('room')")
    assert '먼저' in page.locator('.modal').inner_text()


def test_surgery_tables_add_slots(page_at):
    page = page_at(); boot(page, grade=3, money=99999, rooms=ALLR)
    prep(page); js(page, "buy('up:surg')")
    assert js(page, "S.money") == 99999 - 5000 and js(page, "G.slots.surg.length") == 2


def test_two_inj_patients_at_once(page_at):
    page = page_at(); boot(page, grade=1, money=99999, rooms={'inj': True})
    js(page, "S.up.inj = 1; buildMap(); applyLayout()")
    ids = [spawn_patient(page, sym='🤒', urg=0, unknown=False, multi=False, karen=False, vip=False) for _ in range(2)]
    for pid in ids:
        js(page, f"(() => {{ const p = G.patients.find(x => x.id === {pid}); register(p); p.done = true; p.dest = 'inj'; p.stage = 'next'; sendTo(p, 'inj'); }})()")
    tick(page, .2)
    assert js(page, "G.slots.inj.filter(Boolean).length") == 2


def test_rest_upgrade_cap_and_speed(page_at):
    page = page_at(); boot(page, grade=1, rooms={'rest': True})
    assert js(page, "restCap()") == 2 and abs(js(page, "restDur()") - 9) < 1e-9
    js(page, "S.up.rest = 3")
    assert js(page, "restCap()") == 5 and abs(js(page, "restDur()") - 9 / 1.45) < 1e-9
    js(page, "for (let i = 0; i < 5; i++) S.staff.push(mkStaff('janitor')); S.staff.forEach(s => s.fat = 90)")
    tick(page, .1)
    assert js(page, "S.staff.filter(s => s.rest > 0).length") >= 3


def test_room_tab_shows_levels_per_item(page_at):
    page = page_at(); boot(page, grade=3, money=99999, rooms=ALLR)
    prep(page); js(page, "showShop('room')")
    txt = page.locator('.modal').inner_text()
    for w in ['주사실 침대', '수술대', '휴게실 확장']:
        assert w in txt


# ---------- 인테리어 ----------

def test_new_deco_prices(page_at):
    page = page_at(); boot(page)
    assert [js(page, f"DECOS.{k}.price") for k in ['purifier', 'speaker', 'painting', 'photo']] == [1800, 2500, 6000, 9000]
    assert [js(page, f"DECOS.{k}.grade") for k in ['purifier', 'speaker', 'painting', 'photo']] == [1, 1, 2, 2]


def test_purifier_slows_dirt(page_at):
    page = page_at(); boot(page, grade=1)
    js(page, "Math.random = () => 0; G.patients.forEach(p => removeP(p, 'bye')); G.dirtT = 0; updDirt(.01)")
    base = js(page, "G.dirtT")
    js(page, "S.deco.purifier = true; G.dirtT = 0; updDirt(.01)")
    assert abs(js(page, "G.dirtT") - base * 1.5) < 1e-9


def test_speaker_calms_karens(page_at):
    page = page_at(); boot(page, grade=1)
    js(page, "Math.random = () => 0")
    t0 = js(page, "spawn(true, {karen:true}).tantrumT")
    js(page, "S.deco.speaker = true")
    assert js(page, "spawn(true, {karen:true}).tantrumT") == t0 * 1.5


def test_painting_boosts_rep_gain(page_at):
    page = page_at(); boot(page, grade=2, rep=50)
    js(page, "addRep(2)"); a = js(page, "S.rep") - 50
    js(page, "S.rep = 50; S.deco.painting = true; addRep(2)"); b = js(page, "S.rep") - 50
    assert abs(b - a * 1.05) < 1e-9
    js(page, "S.rep = 50; addRep(-3)")
    assert js(page, "S.rep") == 47


def test_photo_zone_more_vips(page_at):
    page = page_at(); boot(page, grade=2, day=15, rep=30)
    js(page, "Math.random = () => .10; G.vipTimes = []")  # 기본 확률 .09 보다 크고, 포토존 .1125 보다 작음
    assert js(page, "spawn(true, {karen:false, emerg:false}).vip") is False
    js(page, "S.deco.photo = true")
    assert js(page, "spawn(true, {karen:false, emerg:false}).vip") is True


def test_deco_tab_describes_each_effect(page_at):
    page = page_at(); boot(page, grade=2, money=99999)
    prep(page); js(page, "showShop('deco')")
    txt = page.locator('.modal').inner_text()
    for w in ['쓰레기', '진상', '평판', 'VIP', '9,000']:
        assert w in txt
    js(page, "buy('deco:photo')")
    assert js(page, "S.deco.photo") is True and js(page, "S.money") == 99999 - 9000


def test_full_map_still_fits_with_upgrades(page_at):
    for size in [(390, 744), (1440, 900)]:
        page = page_at(size); boot(page, grade=3, rooms=ALLR,
                                   depts={'ort': True, 'eye': True, 'den': True, 'skin': True, 'obgy': True, 'ear': True, 'neu': True})
        js(page, "S.up.inj = 2; S.up.surg = 2; S.up.rest = 3; for (const k in DECOS) S.deco[k] = true; buildMap(); applyLayout()")
        assert js(page, "[...document.querySelectorAll('#map .card')].every(c => c.scrollHeight <= c.clientHeight + 1)")
        assert not js(page, "document.querySelector('#mapWrap').classList.contains('scrollfit')")
