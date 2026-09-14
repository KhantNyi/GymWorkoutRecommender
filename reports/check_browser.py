from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    page.goto('http://127.0.0.1:8501',wait_until='networkidle')
    page.get_by_role('heading',name='A workout that fits your day.').wait_for()
    page.get_by_text('Content-based',exact=True).click()
    page.get_by_text('Matches your goal and muscle focus',exact=False).wait_for()
    page.screenshot(path=str(root/'reports/ui_builder.png'),full_page=True)
    page.get_by_text('Exercise library',exact=True).click()
    page.get_by_role('textbox',name='Search exercises',exact=True).fill('Pushups')
    page.get_by_role('textbox',name='Search exercises',exact=True).press('Enter')
    page.get_by_text('With demonstration photos only',exact=True).click()
    page.get_by_role('heading',name='Pushups',exact=True).wait_for()
    page.wait_for_function("Array.from(document.querySelectorAll('[data-testid=stImage] img')).some(i=>i.complete && i.naturalWidth>0)")
    page.screenshot(path=str(root/'reports/ui_library.png'),full_page=True)
    assert page.locator('[data-testid=stException]').count()==0
    page.set_viewport_size({'width':390,'height':844})
    page.get_by_text('Build workout',exact=True).click()
    page.get_by_role('heading',name='1. Set up your session').wait_for()
    page.screenshot(path=str(root/'reports/ui_mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 2')
    browser.close()
print('Desktop and mobile browser checks passed; local demonstration images loaded.')
