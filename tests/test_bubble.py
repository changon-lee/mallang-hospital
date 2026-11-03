from conftest import boot, js, spawn_patient


def rects_overlap(a, b):
    return not (a['right'] <= b['left'] or b['right'] <= a['left'] or a['bottom'] <= b['top'] or b['bottom'] <= a['top'])


def say_rects(page, pid, text):
    return js(page, f"""(() => {{ const p=G.patients.find(x=>x.id==={pid}); say(p,'{text}');
        const b=p.bubEl.getBoundingClientRect(), s=p.sayEl.getBoundingClientRect();
        return [b.toJSON(), s.toJSON()] }})()""")


def test_say_does_not_cover_symptom_in_seat(page_at):
    page = page_at(); boot(page)
    pid = spawn_patient(page, sym='🤒', urg=0, unknown=True)
    js(page, f"register(G.patients.find(p=>p.id==={pid}))")
    page.wait_for_timeout(1300)
    b, s = say_rects(page, pid, '어디가 아픈지 모르겠어요…')
    assert not rects_overlap(b, s)


def test_say_does_not_cover_symptom_at_entrance(page_at):
    page = page_at(); boot(page)
    pid = spawn_patient(page, sym='🤒', urg=0)
    page.wait_for_timeout(700)
    b, s = say_rects(page, pid, '먼저 톡! 해서 접수해 주세요~')
    assert not rects_overlap(b, s)


def test_symptom_bubble_above_say_layer(page_at):
    page = page_at(); boot(page)
    pid = spawn_patient(page, sym='🤒')
    z = js(page, f"(() => {{ const p=G.patients.find(x=>x.id==={pid}); return [+getComputedStyle(p.bubEl).zIndex, +getComputedStyle(p.sayEl).zIndex] }})()")
    assert z[0] > z[1]
