"""PolishMeter project web application smoke tests.

Verify that the web interface starts properly, serves core pages
(main page, about - project description, contact - contact details), and supports
navigation via UI buttons.
"""

import pytest
from playwright.sync_api import Page, expect
from config.settings import settings


def test_open_mainpage_polishmeter(page: Page):
    """Verify that the main page loads with the expected title and main heading."""
    page.goto(settings.web_page)

    assert page.title() != ""
    assert page.title() == settings.app_name
    expect (page.get_by_role("heading", name=settings.app_name)).to_be_visible()


def test_open_subpage_polishmeter_about(page: Page):
    """Verify that the about subpage opens directly and renders its heading."""
    page.goto(f"{settings.web_page}{settings.subpage_about}")

    assert page.title() != ""
    expect(page).to_have_title(settings.subpage_about_name)
    expect(page.get_by_test_id("about-heading")).to_be_visible()


def test_open_subpage_polishmeter_contact(page):
    """Verify that the contact subpage opens directly and renders its heading."""
    page.goto(f"{settings.web_page}{settings.subpage_contact}")

    assert page.title() != ""
    expect(page).to_have_title(settings.subpage_contact_name)
    expect(page.get_by_test_id("contact-heading")).to_be_visible()


def test_navigate_to_subpage_about(page):
    """Verify navigation from the main page to the About subpage in a new tab."""
    page.goto(settings.web_page)

    with page.expect_popup() as new_page_info:
        page.get_by_test_id("nav-about").click()

    about_page = new_page_info.value
    expect(about_page.get_by_test_id("about-heading")).to_be_visible()


def test_navigate_to_subpage_contact(page):
    """Verify navigation from the main page to the Contact subpage in a new tab."""
    page.goto(settings.web_page)

    with page.expect_popup() as new_page_info:
        page.get_by_test_id("nav-contact").click()

    contact_page = new_page_info.value
    expect(contact_page.get_by_test_id("contact-heading")).to_be_visible()


def test_representative_indicator_is_present(page: Page, test_resources):
    """Verify that one representative indicator per data source is rendered on the main page."""
    for indicator_key in test_resources["gus_test_data"]["equivalence_class_representatives"]:
        page.goto(settings.web_page)

        indicator_row = page.get_by_test_id(f"indicator-row-{indicator_key}")
        expect(indicator_row).to_be_visible()


def test_representative_chart_is_loaded(page: Page, test_resources):
    """Verify that the chart image for the representative indicator is visible and properly loaded."""
    for indicator_key in test_resources["gus_test_data"]["equivalence_class_representatives"]:
        page.goto(settings.web_page)

        chart_img = page.get_by_test_id(f"chart-{indicator_key}_chart")
        expect(chart_img).to_be_visible()
        expect(chart_img).not_to_have_js_property("naturalWidth", 0)
