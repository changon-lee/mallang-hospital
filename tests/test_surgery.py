from conftest import boot, js, tick

MK = "(() => { const p = spawn(true,{sym:'%s',urg:0}); register(p); p.done=true; p.dest='surg'; p.stage='next'; p.fee=40; return p.id })()"


def test_surgery_flow(page_at):
    page = page_at(); boot(page, grade=3, day=10, rooms={'surg': True}, depts={'ort': True})
    js(page, "buildMap(); applyLayout()")
    pid = js(page, MK % '🦴')
    assert 'surg' in js(page, f"validRooms(G.patients.find(p=>p.id==={pid}))")
    js(page, f"sendTo(G.patients.find(p=>p.id==={pid}),'surg')")
    tick(page, 0.2)
    assert js(page, f"G.patients.find(p=>p.id==={pid}).stage") == 'svc'
    tick(page, 8.1)
    assert js(page, f"G.patients.find(p=>p.id==={pid}).stage") == 'pay'
    assert js(page, f"G.patients.find(p=>p.id==={pid}).fee") == 40 + 120 + 30


def test_wrong_room_for_surgery_patient(page_at):
    page = page_at(); boot(page, grade=3, rooms={'surg': True})
    js(page, "buildMap(); applyLayout()")
    pid = js(page, MK % '🤒')
    js(page, f"sendTo(G.patients.find(p=>p.id==={pid}),'pharm')")
    assert js(page, "G.stats.wrong") == 1


def test_roll_dest_includes_surgery_only_when_owned(page_at):
    page = page_at(); boot(page, grade=3, depts={'ort': True})
    js(page, "Math.random = () => 0.999")
    assert js(page, "rollDest('ort',{})") != 'surg'
    js(page, "S.rooms.surg = true")
    assert js(page, "rollDest('ort',{})") == 'surg'


def test_bubble_shows_surgery_icon(page_at):
    page = page_at(); boot(page, grade=3, rooms={'surg': True})
    pid = js(page, MK % '🤒')
    js(page, f"updBub(G.patients.find(p=>p.id==={pid}))")
    assert js(page, f"G.patients.find(p=>p.id==={pid}).bubEl.textContent") == '⚕️'
