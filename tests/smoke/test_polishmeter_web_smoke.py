"""PolishMeter project smoke tests."""

from config.settings import settings

def test_open_mainpage_polishmeter(page):
    page.goto(settings.web_page)

    assert page.title() != ""
    assert page.title() == settings.app_name
    assert page.get_by_role("heading", name=settings.app_name).is_visible()

def test_open_subpage_polishmeter_about(page):
    page.goto(f"{settings.web_page}{settings.subpage_about}")
    assert page.get_by_role("heading", name="About").is_visible()

def test_open_subpage_polishmeter_contact(page):
    page.goto(f"{settings.web_page}{settings.subpage_contactt}")
    assert page.get_by_role("heading", name="Contact").is_visible()

def test_navigate_to_subpage_about(page):
    pass

def test_navigate_to_subpage_contact(page):
    pass
