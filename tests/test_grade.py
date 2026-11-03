from conftest import boot, js

ALL = ['ent', 'wait', 'cash', 'rest', 'int', 'ort', 'eye', 'den', 'skin', 'obgy', 'ear', 'neu', 'exam', 'inj', 'pharm', 'ward', 'surg']


def test_promote_to_university(page_at):
    page = page_at(); boot(page, grade=2, rep=90)
    js(page, "S.total = 450")
    assert js(page, "checkPromo()") is True and js(page, "S.grade") == 3
    assert js(page, "checkPromo()") is False
    assert js(page, "GRADES[S.grade]") == '대학병원'
    assert '최고 등급' in js(page, "gradeProgress()")


def test_general_hospital_not_max_anymore(page_at):
    page = page_at(); boot(page, grade=2, rep=80)
    js(page, "S.total = 300")
    assert '대학병원' in js(page, "gradeProgress()")
    assert js(page, "checkPromo()") is False


def test_new_depts_buyable_in_order(page_at):
    page = page_at()
    boot(page, grade=3, money=99999, depts={'ort': True, 'eye': True, 'den': True, 'skin': True, 'obgy': True})
    js(page, "G.mode='prep'; buy('dept:neu')")
    assert js(page, "!!S.depts.neu") is False
    js(page, "buy('dept:ear'); buy('dept:neu')")
    assert js(page, "!!S.depts.ear && !!S.depts.neu") is True
    assert js(page, "symDept('🤕')") == 'neu'
    assert js(page, "symDept('😮‍💨')") == 'ear'


def test_new_depts_locked_below_university(page_at):
    page = page_at()
    boot(page, grade=2, money=99999, depts={'ort': True, 'eye': True, 'den': True, 'skin': True, 'obgy': True})
    js(page, "G.mode='prep'; buy('dept:ear')")
    assert js(page, "!!S.depts.ear") is False


def test_grade3_map_has_all_rooms(page_at):
    page = page_at(); boot(page, grade=3)
    rooms = js(page, "[...document.querySelectorAll('#map .card')].map(c => c.dataset.room).sort()")
    assert rooms == sorted(ALL)
    page2 = page_at((1440, 900)); boot(page2, grade=3)
    rooms2 = js(page2, "[...document.querySelectorAll('#map .card')].map(c => c.dataset.room).sort()")
    assert rooms2 == sorted(ALL)
    assert page.js_errors == [] and page2.js_errors == []


def test_emergency_bonus_university(page_at):
    page = page_at(); boot(page, grade=3, day=10)
    assert js(page, "extraPay({emerg:true})") == 150
    assert js(page, "extraPay({vip:true})") == 140
    page2 = page_at(); boot(page2, grade=2, day=10)
    assert js(page2, "extraPay({emerg:true})") == 100


def test_university_extra_emergency(page_at):
    page = page_at(); boot(page, grade=3, day=10)
    js(page, "prepDay()")
    assert js(page, "G.emergTimes.length") == 1 + 1 + 3 + 1
