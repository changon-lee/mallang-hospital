from conftest import boot, js, tick


def test_title_and_new_game(page_at):
    page = page_at()
    assert page.locator('#title h1').inner_text() == '말랑병원'
    boot(page)
    assert js(page, "G.mode") == 'play'
    assert js(page, "S.staff.length") == 1
    assert page.js_errors == []


def test_tick_advances_time(page_at):
    page = page_at(); boot(page)
    tick(page, 5)
    assert 4.9 < js(page, "G.t") < 5.1
