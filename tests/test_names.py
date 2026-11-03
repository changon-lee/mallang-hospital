from conftest import boot, js


def test_default_and_custom_name(page_at):
    page = page_at(); boot(page)
    assert js(page, "staffName(S.staff[0])") == '곰곰 선생님'
    js(page, "setStaffName(S.staff[0].id, '  김원장  ')")
    assert js(page, "staffName(S.staff[0])") == '김원장'
    assert js(page, "JSON.parse(localStorage.getItem('mallang-hospital-v2')).staff[0].name") == '김원장'


def test_name_edge_cases(page_at):
    page = page_at(); boot(page)
    js(page, "setStaffName(S.staff[0].id, '<b>x</b>')")
    assert js(page, "staffName(S.staff[0])") == '&lt;b&gt;x&lt;/b&gt;'
    js(page, "setStaffName(S.staff[0].id, '   ')")
    assert js(page, "S.staff[0].name") is None
    js(page, "setStaffName(S.staff[0].id, '가나다라마바사아자차카')")
    assert js(page, "S.staff[0].name") == '가나다라마바사아자차'
    js(page, "setStaffName(S.staff[0].id, '🐻🐻🐻🐻🐻🐻🐻🐻🐻🐻🐻')")
    assert js(page, "Array.from(S.staff[0].name).length") == 10


def test_josa_uses_raw_name(page_at):
    page = page_at(); boot(page)
    js(page, "setStaffName(S.staff[0].id, '곰')")
    assert js(page, "staffNameJo(S.staff[0],'이','가')") == '곰이'
    js(page, "setStaffName(S.staff[0].id, '<a>')")
    assert js(page, "staffNameJo(S.staff[0],'이','가')") == '&lt;a&gt;가'


def test_escaped_name_in_toast(page_at):
    page = page_at(); boot(page)
    js(page, "setStaffName(S.staff[0].id, '<img src=x onerror=alert(1)>'); tapRoom('int', cardEl('int'))")
    assert page.locator('#toasts img').count() == 0
