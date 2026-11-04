from conftest import boot, js


def test_training_cost_and_effect(page_at):
    page = page_at(); boot(page, grade=2, money=10000)
    js(page, "S.staff[0].spd = 2; S.staff[0].kind = 2; S.staff[0].wage = wageOf(S.staff[0])")
    sid = js(page, "S.staff[0].id"); w0 = js(page, "S.staff[0].wage")
    js(page, f"G.mode='prep'; buy('train:{sid}:spd')")
    assert js(page, "S.money") == 10000 - 250
    assert js(page, "S.staff[0].spd") == 3 and js(page, "S.staff[0].wage") > w0
    js(page, f"buy('train:{sid}:kind')")
    assert js(page, "S.money") == 10000 - 250 - 400
    assert js(page, "S.staff[0].kind") == 3 and js(page, "S.staff[0].tr") == 2


def test_training_open_below_general(page_at):
    # 2차 피드백: 자연 성장이 느려진 대신 연수는 처음부터 가능
    page = page_at(); boot(page, grade=1, money=10000)
    js(page, "S.staff[0].spd = 2; G.mode='prep'; buy('train:' + S.staff[0].id + ':spd')")
    assert js(page, "S.money") == 10000 - 250


def test_training_caps_at_5_and_needs_money(page_at):
    page = page_at(); boot(page, grade=2, money=99999)
    js(page, "S.staff[0].spd = 5; G.mode='prep'; buy('train:' + S.staff[0].id + ':spd')")
    assert js(page, "S.money") == 99999
    js(page, "S.money = 100; S.staff[0].kind = 1; buy('train:' + S.staff[0].id + ':kind')")
    assert js(page, "S.staff[0].kind") == 1 and js(page, "S.money") == 100


def test_training_buttons_in_staff_tab(page_at):
    page = page_at(); boot(page, grade=2, money=10000)
    js(page, "G.mode='prep'; showShop('staff')")
    assert page.locator('[data-act^="buy:train:"]').count() == 2
    page2 = page_at(); boot(page2, grade=0)
    js(page2, "G.mode='prep'; showShop('staff')")
    assert page2.locator('[data-act^="buy:train:"]').count() == 2


def test_ad_once_per_day_and_faster_spawns(page_at):
    page = page_at(); boot(page, grade=2, day=10, money=10000)
    js(page, "G = newG(); G.mode='prep'; Math.random = () => 0.5")
    base = js(page, "spawnInterval()")
    js(page, "act('ad:radio')")
    assert js(page, "S.money") == 10000 - 800
    assert abs(js(page, "spawnInterval()") - base * 0.75) < 1e-9
    js(page, "act('ad:tv')")
    assert js(page, "G.ad") == 'radio' and js(page, "S.money") == 10000 - 800


def test_ad_locked_below_general_and_resets_next_day(page_at):
    page = page_at(); boot(page, grade=1, day=10, money=10000)
    js(page, "G.mode='prep'; act('ad:flyer')")
    assert js(page, "G.ad") is None and js(page, "S.money") == 10000
    page2 = page_at(); boot(page2, grade=2, day=10, money=10000)
    js(page2, "G = newG(); G.mode='prep'; act('ad:flyer')")
    assert js(page2, "G.ad") == 'flyer'
    js(page2, "prepDay()")
    assert js(page2, "G.ad") is None


def test_ad_cost_in_day_summary(page_at):
    page = page_at(); boot(page, grade=2, day=10, money=10000)
    js(page, "G = newG(); G.mode='prep'; act('ad:flyer'); act('start'); setSpeed(0); G.t = 181; update(0.1)")
    assert '홍보비' in page.locator('.modal').inner_text()
