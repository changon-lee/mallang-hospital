from conftest import boot, js

OLD = {"v": 1, "day": 5, "money": 900, "rep": 40, "stars": 3, "grade": 0, "total": 30,
       "depts": {"int": True}, "rooms": {"exam": True, "inj": False, "rest": False},
       "up": {"clinic": 1, "wait": 0, "ward": 0}, "deco": {},
       "staff": [], "cands": [], "candDay": 5, "tut": True, "nextId": 2}


def test_old_v1_save_is_ignored(page_at):
    page = page_at()
    page.evaluate("o => localStorage.setItem('mallang-hospital-v1', JSON.stringify(o))", OLD)
    page.reload()
    assert js(page, "load()") is None
    assert page.locator('#tCont').is_hidden()


def test_save_roundtrip_v2(page_at):
    page = page_at(); boot(page, day=3)
    raw = js(page, "JSON.parse(localStorage.getItem('mallang-hospital-v2'))")
    assert raw["v"] == 2 and raw["day"] == 3
    page.reload()
    assert page.locator('#tCont').is_visible()


def test_new_staff_has_new_fields(page_at):
    page = page_at(); boot(page)
    s = js(page, "mkStaff('nurse')")
    assert s["tr"] == 0 and s["name"] is None
    assert js(page, "S.rooms.surg") is False
