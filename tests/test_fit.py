import pathlib
import pytest
from conftest import boot, js, tick, spawn_patient

PHONES = [(390, 744), (430, 832)]          # 보이는 높이(브라우저 바 제외)
OTHER = [(844, 350), (1440, 900)]

FILL_JS = """
  for (const d of DEPT_ORDER) if (DEPTS[d].grade <= S.grade) S.depts[d] = true;
  S.rooms = { exam:true, inj:true, rest:S.grade>=1, surg:S.grade>=3 };
  S.up.wait = 3; S.up.ward = 3;
  for (const d of DEPT_ORDER) if (S.depts[d]) while (doctorsOf(d).length < docCap()) S.staff.push(mkStaff('doctor',{dept:d}));
  buildMap(); applyLayout();
"""

NO_SCROLL = "(() => { const w = document.querySelector('#mapWrap'); return w.scrollHeight <= w.clientHeight + 1 && document.documentElement.scrollHeight <= innerHeight + 1 && document.documentElement.scrollWidth <= innerWidth })()"
PZ = "parseFloat(getComputedStyle(document.querySelector('#map')).getPropertyValue('--pz'))"
CARDS_FIT = "[...document.querySelectorAll('#map .card')].every(c => c.scrollHeight <= c.clientHeight + 1)"


def full_hospital(page, grade):
    boot(page, grade=grade); js(page, FILL_JS); page.wait_for_timeout(150)


@pytest.mark.parametrize("w,h", PHONES + OTHER)
@pytest.mark.parametrize("grade", [0, 1, 2, 3])
def test_no_scroll_and_min_size(page_at, w, h, grade):
    page = page_at((w, h)); full_hospital(page, grade)
    assert js(page, NO_SCROLL)
    assert js(page, CARDS_FIT)
    # 세로 폰·PC는 22px 이상. 높이 500px 미만 가로 폰은 스크롤만 없으면 됨 (Ruling, ledger 참고)
    # 대학병원 세로 폰은 신관 줄(얇은 한 줄)이 더해져 20px 이상 (Ruling: endgame Task 5)
    assert js(page, PZ) >= ((20 if grade == 3 and w < h else 22) if h >= 500 else 16)
    shots = pathlib.Path(__file__).parent / '_shots'; shots.mkdir(exist_ok=True)
    page.screenshot(path=str(shots / f'g{grade}_{w}x{h}.png'))


def test_full_queues_do_not_grow_rooms(page_at):
    page = page_at((390, 744)); full_hospital(page, 2)
    h0 = js(page, "document.querySelector('.card[data-room=ent]').getBoundingClientRect().height")
    for _ in range(8):
        spawn_patient(page, sym='🤒')
    js(page, "for (let i=0;i<10;i++){ const p=spawn(true,{sym:'🤒'}); register(p); }")
    js(page, "for (let i=0;i<6;i++){ const p=spawn(true,{sym:'🤒'}); register(p); p.stage='pay'; toCash(p); }")
    page.wait_for_timeout(500)
    assert abs(js(page, "document.querySelector('.card[data-room=ent]').getBoundingClientRect().height") - h0) < 1
    assert js(page, NO_SCROLL)
    assert js(page, CARDS_FIT)


def test_resize_midday_keeps_patients(page_at):
    page = page_at((390, 744)); boot(page)
    pid = spawn_patient(page, sym='🤒', urg=0)
    js(page, f"const p=G.patients.find(x=>x.id==={pid}); register(p); sendTo(p,'int')"); tick(page, 0.3)
    page.set_viewport_size({"width": 744, "height": 390}); page.wait_for_timeout(400)
    assert js(page, "G.slots.int[0] && G.slots.int[0].id") == pid
    assert js(page, f"G.patients.find(x=>x.id==={pid}).el.isConnected") is True
    assert js(page, NO_SCROLL)


def test_small_phone_does_not_break(page_at):
    page = page_at((360, 560)); full_hospital(page, 3)
    tick(page, 20)
    assert js(page, "G.mode") == 'play'
    assert page.js_errors == []


# fitMap과 같은 판정: 장식(가구·잠금 안내·의사 배지)은 빼고, 대기열 환자는 포함
FIT_PRED = """(() => { const st = document.createElement('style'); st.textContent = '#map .furn,#map .lk,#map .c-dept .staffs{display:none!important}'; document.head.appendChild(st);
  const ok = [...document.querySelectorAll('#map .card')].every(c => {
  if (c.scrollHeight > c.clientHeight + 1 || c.scrollWidth > c.clientWidth + 1) return false;
  const cb = c.querySelector('.cb');
  return !cb || (cb.scrollHeight <= cb.clientHeight + 1 && cb.scrollWidth <= cb.clientWidth + 1); });
  st.remove(); return ok; })()"""
CLIPPED = """[...document.querySelectorAll('#map .pt')].filter(p => {
  const c = p.closest('.card').getBoundingClientRect(), r = p.getBoundingClientRect();
  return r.bottom > c.bottom + 2 || r.right > c.right + 2 || r.left < c.left - 2; }).length"""
FILL_QUEUES = """for (let i=0;i<9;i++) spawn(true,{sym:'🤒'});
  for (let i=0;i<8;i++){ const p=spawn(true,{sym:'🤒'}); p.stage='pay'; toCash(p); }
  for (let i=0;i<8;i++){ const p=spawn(true,{sym:'🤒'}); register(p); p.done=true; p.dest='pharm'; p.stage='next'; sendTo(p,'pharm'); }"""


@pytest.mark.parametrize("w,h", [(390, 744), (667, 375), (740, 360), (844, 350), (1440, 900)])
@pytest.mark.parametrize("grade", [2, 3])
def test_full_queues_never_clipped(page_at, w, h, grade):
    page = page_at((w, h)); full_hospital(page, grade)
    js(page, FILL_QUEUES); page.wait_for_timeout(1300)
    assert js(page, CLIPPED) == 0
    # 꽉 맞추기에 성공했으면 모든 방이 넘치지 않고, 못 맞추면 스크롤로 전부 보여야 함
    assert js(page, FIT_PRED) or js(page, "document.querySelector('#mapWrap').scrollHeight > document.querySelector('#mapWrap').clientHeight")


@pytest.mark.parametrize("w,h", [(667, 375), (740, 360)])
def test_small_landscape_uses_wide_layout(page_at, w, h):
    page = page_at((w, h)); boot(page)
    assert js(page, "layoutMode()") == 'wide'
