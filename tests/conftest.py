import json
import pathlib
import pytest
from playwright.sync_api import sync_playwright

INDEX = (pathlib.Path(__file__).resolve().parent.parent / 'index.html').as_uri()


@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page_at(browser):
    """Factory: page_at((w, h)) -> fresh page with empty localStorage, title shown."""
    ctxs = []

    def make(size=(430, 932)):
        ctx = browser.new_context(viewport={'width': size[0], 'height': size[1]})
        ctxs.append(ctx)
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.js_errors = errors
        page.goto(INDEX)
        page.evaluate('localStorage.clear()')
        page.reload()
        return page

    yield make
    for c in ctxs:
        c.close()


def js(page, expr):
    return page.evaluate(expr)


def boot(page, *, grade=0, day=1, money=5000, rep=30, depts=None, rooms=None, staff_js=''):
    """Start a new game straight into day play (tutorial done), real-time loop paused."""
    page.evaluate(
        """([o, staffJs]) => {
          newState(); S.tut = true; S.day = o.day; S.grade = o.grade; S.money = o.money; S.rep = o.rep;
          Object.assign(S.depts, o.depts || {}); Object.assign(S.rooms, o.rooms || {});
          (new Function(staffJs))();
          save(); startGame(S); act('start'); setSpeed(0);
        }""",
        [dict(grade=grade, day=day, money=money, rep=rep, depts=depts, rooms=rooms), staff_js],
    )


def tick(page, seconds, step=0.1):
    page.evaluate('([n, s]) => { for (let i = 0; i < n; i++) update(s); }', [round(seconds / step), step])


def spawn_patient(page, **opts):
    return page.evaluate('o => spawn(true, o).id', opts)
