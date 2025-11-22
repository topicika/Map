import pytest
from playwright.sync_api import Page, expect


def wait_for_suggestions(page: Page, selector: str):
    """Wait until the <datalist> has at least one option."""
    page.wait_for_function(
        """selector => {
            const el = document.querySelector(selector);
            return el && el.options && el.options.length > 0;
        }""",
        arg=selector,
    )


def fill_input_with_debounce(page: Page, input_selector: str, value: str, suggestion_selector: str):
    input = page.locator(input_selector)
    input.fill(value)
    input.dispatch_event("input")
    page.wait_for_timeout(300)
    wait_for_suggestions(page, suggestion_selector)
    input.blur()


@pytest.mark.playwright
def test_fetch_suggestions(page: Page, live_server):
    page.goto(live_server.url)
    fill_input_with_debounce(page, "#sourceinput", "LÉ-1", "#suggestions1")

    option_count = page.locator("#suggestions1 option").count()
    assert option_count > 0, "The result is empty"
    first_value = page.locator("#suggestions1 option").first.get_attribute("value")
    assert first_value is not None, "The result is None"
    assert "LÉ-1" in first_value, "The result is incorrect"


@pytest.mark.playwright
def test_submit_button(page: Page, live_server):
    page.goto(live_server.url)

    fill_input_with_debounce(page, "#sourceinput", "LÉ-1-131-02-34", "#suggestions1")
    fill_input_with_debounce(page, "#goalinput", "LÉ-1-134A-05-77", "#suggestions2")

    page.locator("button[type='submit']").click()

    expect(page.locator("canvas#myCanvas")).to_be_visible()
    assert "map_result" in page.url, "map_result is not loaded"


@pytest.mark.playwright
def test_back_to_main_button(page: Page, live_server):
    page.goto(live_server.url)

    fill_input_with_debounce(page, "#sourceinput", "LÉ-1-131-02-34", "#suggestions1")
    fill_input_with_debounce(page, "#goalinput", "LÉ-1-134A-05-77", "#suggestions2")

    page.locator("button[type='submit']").click()
    expect(page.locator("canvas#myCanvas")).to_be_visible()

    page.locator("a.btn.btn-secondary").click()
    expect(page.locator("button[type='submit']")).to_be_visible()
    assert page.url.rstrip("/") == live_server.url.rstrip("/"), "The main page is not loaded"


@pytest.mark.playwright
def test_level_buttons_redraw_canvas(page: Page, live_server):
    page.goto(live_server.url)

    fill_input_with_debounce(page, "#sourceinput", "LÉ-1-131-02-34", "#suggestions1")
    fill_input_with_debounce(page, "#goalinput", "LÉ-1-134A-05-77", "#suggestions2")

    page.locator("button[type='submit']").click()
    canvas = page.locator("canvas#myCanvas")
    expect(canvas).to_be_visible()

    level_buttons = page.locator("button[id^='level-']")
    assert level_buttons.count() > 0, "There are no levels"
    before = canvas.screenshot()
    level_buttons.first.click(force=True)
    page.wait_for_timeout(300)
    after = canvas.screenshot()
    assert before != after, "Canvas did not redraw after clicking level button"
