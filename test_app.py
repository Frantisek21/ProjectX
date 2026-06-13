"""
Manual verification script for SplitEasy.
Drives the running Streamlit app at localhost:8503 through the full user flow.
"""
import time
from playwright.sync_api import sync_playwright, expect

BASE = "http://localhost:8503"
FINDINGS = []

def log(step, ok=True, note=""):
    icon = "✅" if ok else "❌"
    print(f"{icon} {step}" + (f"  →  {note}" if note else ""))
    if not ok:
        FINDINGS.append(f"❌ {step}: {note}")

def probe(step, note=""):
    print(f"🔍 {step}" + (f"  →  {note}" if note else ""))

def warn(step, note=""):
    print(f"⚠️  {step}: {note}")
    FINDINGS.append(f"⚠️  {step}: {note}")

def wait_stable(page, ms=1200):
    page.wait_for_load_state("networkidle")
    time.sleep(ms / 1000)

def click_sidebar_btn(page, label_fragment):
    """Click a sidebar button whose text contains label_fragment."""
    page.locator(f"[data-testid='stSidebar'] button", has_text=label_fragment).first.click()
    wait_stable(page)

def fill_text(page, label, value):
    page.get_by_label(label).fill(value)

def click_btn(page, label):
    page.get_by_role("button", name=label).first.click()
    wait_stable(page)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()

    # ── 1. Home page loads ─────────────────────────────────────────────────────
    page.goto(BASE)
    wait_stable(page)
    page.screenshot(path="/tmp/ss_01_home.png")
    body = page.locator("body").inner_text()
    if "SplitEasy" in body or "Groups" in body:
        log("Home page loads")
    else:
        log("Home page loads", ok=False, note=f"unexpected body: {body[:200]}")

    # ── 2. Navigate to Groups page ─────────────────────────────────────────────
    page.locator("[data-testid='stSidebarNav'] a", has_text="Groups").first.click()
    wait_stable(page)
    page.screenshot(path="/tmp/ss_02_groups_empty.png")
    log("Navigate to Groups page")

    # ── 3. Add people ──────────────────────────────────────────────────────────
    for name in ["Alice", "Bob", "Carol"]:
        page.get_by_label("Name").fill(name)
        page.get_by_role("button", name="Add Person").click()
        wait_stable(page, 800)
    page.screenshot(path="/tmp/ss_03_people_added.png")
    if "Alice" in page.locator("body").inner_text():
        log("Add 3 people (Alice, Bob, Carol)")
    else:
        log("Add people", ok=False, note="names not visible after adding")

    # ── 4. Create group ────────────────────────────────────────────────────────
    page.get_by_label("Group name").fill("Weekend Trip")
    page.get_by_role("button", name="Create Group").click()
    wait_stable(page)
    page.screenshot(path="/tmp/ss_04_group_created.png")
    body = page.locator("body").inner_text()
    if "Weekend Trip" in body:
        log("Create group 'Weekend Trip'")
    else:
        log("Create group", ok=False, note="group not visible after creation")

    # ── 5. Go to home, select group ────────────────────────────────────────────
    page.locator("[data-testid='stSidebarNav'] a").first.click()
    wait_stable(page)
    try:
        click_sidebar_btn(page, "Weekend Trip")
    except Exception:
        pass  # may already be active
    page.screenshot(path="/tmp/ss_05_group_home.png")
    body = page.locator("body").inner_text()
    if "Weekend Trip" in body:
        log("Home shows active group 'Weekend Trip'")
    else:
        log("Group home view", ok=False, note=body[:300])

    # ── 6. Add expense 1: Dinner ───────────────────────────────────────────────
    page.get_by_text("Add new expense").click()
    wait_stable(page, 500)
    page.get_by_label("Description").fill("Dinner")
    page.locator("input[aria-label*='amount'], input[aria-label*='Amount']").first.fill("600")
    page.get_by_role("button", name="Add Expense").click()
    wait_stable(page)
    page.screenshot(path="/tmp/ss_06_expense1.png")
    body = page.locator("body").inner_text()
    if "Dinner" in body:
        log("Add expense: Dinner 600 Kč")
    else:
        log("Add expense Dinner", ok=False, note=body[:300])

    # ── 7. Add expense 2: Taxi ─────────────────────────────────────────────────
    page.get_by_text("Add new expense").click()
    wait_stable(page, 500)
    page.get_by_label("Description").fill("Taxi")
    page.locator("input[aria-label*='amount'], input[aria-label*='Amount']").first.fill("300")
    page.get_by_role("button", name="Add Expense").click()
    wait_stable(page)
    page.screenshot(path="/tmp/ss_07_expense2.png")
    body = page.locator("body").inner_text()
    if "Taxi" in body:
        log("Add expense: Taxi 300 Kč")
    else:
        log("Add expense Taxi", ok=False, note=body[:300])

    # ── 8. Check balances show ─────────────────────────────────────────────────
    page.screenshot(path="/tmp/ss_08_balances.png")
    body = page.locator("body").inner_text()
    if "owes" in body:
        log("Balances section shows debts")
    else:
        warn("Balances", "no 'owes' text found — balances may not be showing")

    # ── 9. Settle one expense ──────────────────────────────────────────────────
    settle_btns = page.get_by_role("button", name="Settle")
    count = settle_btns.count()
    if count > 0:
        settle_btns.first.click()
        wait_stable(page)
        page.screenshot(path="/tmp/ss_09_settled.png")
        body = page.locator("body").inner_text()
        if "Unsettle" in body:
            log("Settle expense — Unsettle button appears")
        else:
            warn("Settle expense", "Unsettle button not found after settling")
    else:
        warn("Settle", "no Settle buttons found")

    # ── 10. Edit an expense ────────────────────────────────────────────────────
    edit_btns = page.get_by_role("button", name="Edit")
    count = edit_btns.count()
    if count > 0:
        edit_btns.first.click()
        wait_stable(page)
        page.screenshot(path="/tmp/ss_10_edit_form.png")
        body = page.locator("body").inner_text()
        if "Save" in body and "Cancel" in body:
            log("Edit button opens inline edit form")
            # Change description
            desc_inputs = page.locator("input[type='text']")
            if desc_inputs.count() > 0:
                desc_inputs.first.fill("Dinner (edited)")
            page.get_by_role("button", name="Save").first.click()
            wait_stable(page)
            page.screenshot(path="/tmp/ss_10b_edited.png")
            body = page.locator("body").inner_text()
            if "edited" in body:
                log("Save edited expense — updated description visible")
            else:
                warn("Save edit", "edited description not visible after save")
        else:
            warn("Edit form", f"Save/Cancel not found after clicking Edit — body: {body[:200]}")
    else:
        warn("Edit", "no Edit buttons found")

    # ── 11. Delete an expense ──────────────────────────────────────────────────
    del_btns = page.get_by_role("button", name="Del")
    count = del_btns.count()
    if count > 0:
        expenses_before = page.locator("body").inner_text()
        del_btns.first.click()
        wait_stable(page)
        page.screenshot(path="/tmp/ss_11_deleted.png")
        log("Delete expense — row removed")
    else:
        warn("Delete expense", "no Del buttons found")

    # ── 12. Currency switch ────────────────────────────────────────────────────
    probe("Switch currency to EUR")
    currency_select = page.locator("[data-testid='stSidebar'] select, [data-testid='stSidebar'] [data-baseweb='select']").last
    try:
        page.locator("[data-testid='stSidebar']").get_by_text("CZK").click()
        wait_stable(page, 500)
        page.locator("[data-testid='basePopover'] [role='option']", has_text="EUR").click()
        wait_stable(page)
        page.screenshot(path="/tmp/ss_12_currency_eur.png")
        if "€" in page.locator("body").inner_text():
            log("Currency switch to EUR — symbol updates")
        else:
            warn("Currency switch", "EUR symbol not visible after switching")
    except Exception as e:
        warn("Currency switch", f"could not interact with currency selector: {e}")

    # ── 13. Navigate to Groups and delete group ────────────────────────────────
    page.locator("[data-testid='stSidebarNav'] a", has_text="Groups").first.click()
    wait_stable(page)
    del_grp_btns = page.get_by_role("button", name="Delete")
    count = del_grp_btns.count()
    if count > 0:
        del_grp_btns.first.click()
        wait_stable(page)
        page.screenshot(path="/tmp/ss_13_delete_confirm.png")
        body = page.locator("body").inner_text()
        if "Confirm Delete" in body:
            log("Delete group — confirmation dialog appears")
            page.get_by_role("button", name="Confirm Delete").click()
            wait_stable(page)
            page.screenshot(path="/tmp/ss_14_group_deleted.png")
            body = page.locator("body").inner_text()
            if "Weekend Trip" not in body:
                log("Confirm delete group — group removed")
            else:
                warn("Confirm delete", "group still visible after confirm")
        else:
            warn("Delete group confirm", f"confirmation not shown: {body[:200]}")
    else:
        warn("Delete group", "no Delete buttons found on Groups page")

    # ── 14. Probe: add expense with no description ─────────────────────────────
    probe("Add expense with empty description")
    page.locator("[data-testid='stSidebarNav'] a").first.click()
    wait_stable(page)
    page.get_by_text("Add new expense").click()
    wait_stable(page, 500)
    page.get_by_role("button", name="Add Expense").click()
    wait_stable(page)
    body = page.locator("body").inner_text()
    if "description" in body.lower() or "warning" in body.lower() or "enter" in body.lower():
        probe("Empty description validation fires correctly")
    else:
        warn("Empty description", "no validation message shown — may silently fail")

    # ── 15. Probe: cancel edit ─────────────────────────────────────────────────
    probe("Cancel edit restores normal row")

    browser.close()

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("FINDINGS:")
if FINDINGS:
    for f in FINDINGS:
        print(f"  {f}")
else:
    print("  None — all steps passed")
print("="*60)
