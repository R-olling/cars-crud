"""Tier 3: browser -> JavaScript -> real HTTP -> FastAPI -> real SQLite."""

import re

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def add_car(page, live_server, make="Toyota", model="Corolla"):
    page.goto(f"{live_server}/cars/new")
    page.get_by_label("Make", exact=True).fill(make)
    page.get_by_label("Model", exact=True).fill(model)
    page.get_by_label("Year", exact=True).fill("2024")
    page.get_by_label("Color", exact=False).fill("Silver")
    page.get_by_role("button", name="Create car", exact=True).click()
    expect(page).to_have_url(re.compile(r"/cars/\d+$"))
    expect(page.get_by_role("heading", name=f"{make} {model}", exact=True)).to_be_visible()


def test_complete_crud_workflow(page, live_server):
    page.goto(live_server)
    expect(page.get_by_role("heading", name="No cars yet")).to_be_visible()
    page.get_by_role("link", name="Add car", exact=True).click()
    page.get_by_label("Make", exact=True).fill("Toyota")
    page.get_by_label("Model", exact=True).fill("Corolla")
    page.get_by_label("Year", exact=True).fill("2024")
    page.get_by_label("Color", exact=False).fill("Silver")
    page.get_by_role("button", name="Create car").click()

    expect(page.get_by_role("heading", name="Toyota Corolla")).to_be_visible()
    expect(page.locator("#car-year")).to_have_text("2024")
    page.get_by_role("link", name="Back to cars").click()
    row = page.get_by_role("row").filter(has_text="Toyota")
    expect(row).to_contain_text("Corolla")
    row.get_by_role("link", name="View", exact=True).click()
    expect(page.get_by_role("heading", name="Toyota Corolla")).to_be_visible()
    page.get_by_role("link", name="Edit car").click()
    expect(page.get_by_label("Model", exact=True)).to_have_value("Corolla")
    page.get_by_label("Model", exact=True).fill("Camry")
    page.get_by_label("Year", exact=True).fill("2025")
    page.get_by_role("button", name="Save changes").click()
    expect(page.get_by_role("heading", name="Toyota Camry")).to_be_visible()
    page.reload()
    expect(page.locator("#car-year")).to_have_text("2025")
    expect(page.locator("#car-model")).to_have_text("Camry")

    page.get_by_role("link", name="Back to cars").click()
    row = page.get_by_role("row").filter(has_text="Camry")
    page.once("dialog", lambda dialog: dialog.accept())
    row.get_by_role("button", name="Delete", exact=True).click()
    expect(page.get_by_role("heading", name="No cars yet")).to_be_visible()
    page.reload()
    expect(page.get_by_role("heading", name="No cars yet")).to_be_visible()


def test_delete_can_be_cancelled_then_confirmed(page, live_server):
    add_car(page, live_server)
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("button", name="Delete car").click()
    expect(page.get_by_role("heading", name="Toyota Corolla")).to_be_visible()
    page.reload()
    expect(page.get_by_role("heading", name="Toyota Corolla")).to_be_visible()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Delete car").click()
    expect(page.get_by_role("heading", name="No cars yet")).to_be_visible()


def test_required_fields_and_server_validation(page, live_server):
    page.goto(f"{live_server}/cars/new")
    page.get_by_role("button", name="Create car").click()
    assert page.locator("#make").evaluate("el => el.validity.valueMissing")
    expect(page).to_have_url(f"{live_server}/cars/new")

    # Whitespace passes HTML's required check but must fail server validation.
    page.get_by_label("Make", exact=True).fill("   ")
    page.get_by_label("Model", exact=True).fill("Corolla")
    page.get_by_label("Year", exact=True).fill("2024")
    page.get_by_role("button", name="Create car").click()
    expect(page.get_by_role("alert")).to_contain_text("make:")
    expect(page.get_by_role("button", name="Create car")).to_be_enabled()
    page.get_by_role("link", name="Back to cars").click()
    expect(page.get_by_role("heading", name="No cars yet")).to_be_visible()


def test_html_like_values_are_displayed_as_text(page, live_server):
    make = "<img src=x onerror=alert(1)>"
    add_car(page, live_server, make=make)
    assert page.locator("main img").count() == 0
    page.get_by_role("link", name="Back to cars").click()
    expect(page.get_by_role("cell", name=make, exact=True)).to_be_visible()
    assert page.locator("main img").count() == 0


def test_cancel_edit_does_not_save(page, live_server):
    add_car(page, live_server)
    page.get_by_role("link", name="Edit car").click()
    expect(page.get_by_label("Model", exact=True)).to_have_value("Corolla")
    page.get_by_label("Model", exact=True).fill("Unsaved change")
    page.get_by_role("link", name="Cancel", exact=True).click()
    expect(page.get_by_role("heading", name="Toyota Corolla")).to_be_visible()
    page.reload()
    expect(page.locator("#car-model")).to_have_text("Corolla")
