from conftest import boot, js


def test_roster_pauses_and_lists_staff(page_at):
    page = page_at(); boot(page, grade=1, staff_js="S.staff.push(mkStaff('nurse'))")
    js(page, "setSpeed(1)")
    page.click('#bStaff')
    assert js(page, "G.modal") is True
    assert page.locator('.modal .sname').count() == 2
    t0 = js(page, "G.t"); page.wait_for_timeout(300)
    assert js(page, "G.t") == t0
    page.click('[data-act=rosterClose]')
    assert js(page, "G.modal") is False


def test_roster_order_by_role(page_at):
    page = page_at(); boot(page, grade=1, staff_js="S.staff.push(mkStaff('janitor')); S.staff.push(mkStaff('nurse'))")
    page.click('#bStaff')
    tags = page.locator('.modal .stag').all_inner_texts()
    assert tags[0] == '의사' and tags[1] == '간호사' and tags[2] == '청소부'


def test_rename_via_ui(page_at):
    page = page_at(); boot(page)
    page.click('#bStaff'); page.click('.modal .rn')
    page.fill('.modal .rn-in', '<i>닥터곰</i>'); page.keyboard.press('Enter')
    assert page.locator('.modal .sname').first.inner_text().startswith('<i>닥터곰</i>')
    assert js(page, "S.staff[0].name") == '<i>닥터곰</i>'
    assert page.locator('.modal .sname i').count() == 0


def test_rename_escape_cancels_and_keys_ignored(page_at):
    page = page_at(); boot(page); js(page, "setSpeed(1)")
    page.click('#bStaff'); page.click('.modal .rn')
    page.fill('.modal .rn-in', 'a b'); page.keyboard.press('Space'); page.keyboard.press('2'); page.keyboard.press('Escape')
    assert js(page, "S.staff[0].name") is None
    assert js(page, "G.speed") == 1


def test_roster_from_prep_returns_to_prep(page_at):
    page = page_at(); boot(page)
    js(page, "prepDay()")
    page.click('.modal [data-act=roster]')
    page.click('[data-act=rosterClose]')
    assert page.locator('[data-act=start]').count() == 1
