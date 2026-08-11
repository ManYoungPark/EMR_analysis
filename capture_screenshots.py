from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("images")
OUT.mkdir(exist_ok=True)

def shot(page, path, full_page=False):
    page.screenshot(path=str(OUT / path), full_page=full_page)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})

    # 1. CRAN 메인 화면
    page.goto("https://cran.r-project.org/", wait_until="networkidle")
    shot(page, "01_cran_home.png", full_page=False)

    # 2. Windows용 R 페이지
    page.goto("https://cran.r-project.org/bin/windows/", wait_until="networkidle")
    shot(page, "02_r_windows.png", full_page=False)

    # 3. 최신 Windows base 다운로드 페이지
    page.goto("https://cran.r-project.org/bin/windows/base/", wait_until="networkidle")
    shot(page, "03_r_download.png", full_page=False)

    # 4. Posit 다운로드 페이지
    page.goto("https://posit.co/downloads/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    shot(page, "07_posit_downloads.png", full_page=False)

    # 5. RStudio 섹션 근처로 스크롤 후 캡처
    try:
        rstudio = page.get_by_text("RStudio Desktop", exact=False).first
        rstudio.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        shot(page, "08_rstudio_download.png", full_page=False)
    except Exception:
        # 페이지 구조가 변경되었을 경우 전체 페이지를 대체 캡처
        shot(page, "08_rstudio_download.png", full_page=True)

    browser.close()

print("캡처 완료: images 폴더를 확인하세요.")
