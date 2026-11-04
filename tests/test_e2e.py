from conftest import boot, js

AUTO = """(() => { for (let k=0;k<4000 && G.mode==='play';k++) {
    for (const p of G.patients.slice()) {
      if (p.tantrum) for (let i=0;i<4;i++) calmKaren(p);
      if (p.stage==='reg') sendTo(p, p.unknown && !p.revealed ? 'exam' : p.dept);
      else if (p.stage==='next') sendTo(p, p.dest);
      else if (p.stage==='pay') pay(p);
    }
    update(0.1);
} })()"""


def test_auto_play_three_days(page_at):
    page = page_at((390, 744))
    boot(page, grade=3, day=12, money=20000, rep=90,
         depts={'ort': True, 'eye': True, 'den': True, 'skin': True, 'obgy': True, 'ear': True, 'neu': True},
         rooms={'exam': True, 'inj': True, 'rest': True, 'surg': True},
         staff_js="for (const d of ['ort','eye','den','skin','obgy','ear','neu']) S.staff.push(mkStaff('doctor',{dept:d}));"
                  "S.staff.push(mkStaff('nurse')); S.staff.push(mkStaff('cashier')); S.staff.push(mkStaff('pharm')); S.staff.push(mkStaff('janitor'));"
                  "S.staff.push(mkStaff('pnurse',{spd:1,kind:1})); S.staff.push(mkStaff('inurse',{spd:5,kind:1}))")
    js(page, "G.mode='prep'; act('start'); setSpeed(0)")
    for _ in range(3):
        js(page, AUTO)
        assert js(page, "G.mode") == 'summary'
        js(page, "act('sumOk'); act('start'); setSpeed(0)")
    assert page.js_errors == []
    assert js(page, "S.day") == 15


def test_guide_mentions_new_features(page_at):
    page = page_at(); boot(page)
    js(page, "showGuide()")
    text = page.locator('.modal').inner_text()
    for word in ['수술실', '수납 간호사', '직원 명부', '홍보', '대학병원']:
        assert word in text
