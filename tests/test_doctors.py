from conftest import boot, js, tick, spawn_patient

TWO_INT = "S.staff.push(mkStaff('doctor',{dept:'int',spd:2,kind:2}))"


def test_two_doctors_two_slots(page_at):
    page = page_at(); boot(page, grade=1, staff_js=TWO_INT)
    assert js(page, "G.slots.int.length") == 2
    a = spawn_patient(page, sym='🤒', urg=0); b = spawn_patient(page, sym='🤧', urg=0)
    js(page, f"[{a},{b}].forEach(id => {{ const p=G.patients.find(x=>x.id===id); register(p); sendTo(p,'int'); }})")
    tick(page, 0.3)
    assert js(page, "G.slots.int.filter(Boolean).length") == 2


def test_each_slot_uses_its_own_doctor(page_at):
    page = page_at(); boot(page, grade=1, staff_js="S.staff.push(mkStaff('doctor',{dept:'int',spd:5,kind:1}))")
    js(page, "doctorsOf('int')[0].spd = 1")
    assert js(page, "treatDur('int',1) < treatDur('int',0)")
    assert js(page, "slotDoctor('int',1).spd") == 5


def test_resting_doctor_closes_only_own_slot(page_at):
    page = page_at(); boot(page, grade=1, rooms={'rest': True}, staff_js=TWO_INT)
    js(page, "doctorsOf('int')[1].rest = 5; renderStaff()")
    assert js(page, "slotReady('int',0)") is True
    assert js(page, "slotReady('int',1)") is False
    assert js(page, "G.slotEls.int[1].classList.contains('closed')") is True
    assert js(page, "G.slotEls.int[0].classList.contains('closed')") is False


def test_emergency_blocks_rest_all_doctors(page_at):
    page = page_at(); boot(page, grade=1, day=5, rooms={'rest': True}, staff_js=TWO_INT)
    js(page, "doctorsOf('int').forEach(d => d.fat = 90)")
    js(page, "const p = spawn(true,{emerg:true, sym:'🤒'}); p.stage='queued'; p.target='int'")
    js(page, "updStaff(0.1)")
    assert js(page, "doctorsOf('int').every(d => !(d.rest > 0))") is True


def test_hire_replaces_at_clinic_adds_at_hospital(page_at):
    page = page_at(); boot(page, grade=0)
    js(page, "G.mode='prep'; S.cands=[mkStaff('doctor',{dept:'int',spd:5,kind:5})]; buy('hire:0')")
    assert js(page, "doctorsOf('int').length") == 1
    assert js(page, "doctorsOf('int')[0].spd") == 5

    page2 = page_at(); boot(page2, grade=1)
    js(page2, "G.mode='prep'; S.cands=[mkStaff('doctor',{dept:'int',spd:1,kind:1})]; buy('hire:0')")
    assert js(page2, "doctorsOf('int').length") == 2
    assert js(page2, "G.slots.int.length") == 2


def test_replace_targets_weakest(page_at):
    page = page_at(); boot(page, grade=1, staff_js="S.staff.push(mkStaff('doctor',{dept:'int',spd:1,kind:1}))")
    keep = js(page, "doctorsOf('int')[0].id")
    js(page, "G.mode='prep'; S.cands=[mkStaff('doctor',{dept:'int',spd:4,kind:4})]; buy('hire:0')")
    ids = js(page, "doctorsOf('int').map(d => d.id)")
    assert keep in ids and len(ids) == 2
    assert js(page, "doctorsOf('int').some(d => d.spd === 1 && d.kind === 1)") is False


def test_cannot_fire_last_doctor(page_at):
    page = page_at(); boot(page, grade=1, staff_js=TWO_INT)
    js(page, "G.mode='prep'; buy('fire:' + doctorsOf('int')[1].id)")
    assert js(page, "doctorsOf('int').length") == 1
    js(page, "buy('fire:' + doctorsOf('int')[0].id)")
    assert js(page, "doctorsOf('int').length") == 1


def test_doctor_candidate_prefers_open_seat(page_at):
    page = page_at(); boot(page, grade=1, depts={'ort': True}, staff_js="S.staff.push(mkStaff('doctor',{dept:'ort'})); S.staff.push(mkStaff('doctor',{dept:'ort'}))")
    for _ in range(20):
        js(page, "genCands()")
        assert js(page, "S.cands.filter(c => c.role==='doctor').every(c => c.dept === 'int')") is True
