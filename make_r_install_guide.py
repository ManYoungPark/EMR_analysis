from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
import time

OUT = Path("images")
OUT.mkdir(exist_ok=True)

VIEWPORT = {"width": 1440, "height": 1000}

def get_font(size=28):
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            pass
    return ImageFont.load_default()

def annotate(image_path, box, out_path=None):
    out_path = out_path or image_path
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    x = int(box["x"])
    y = int(box["y"])
    w = int(box["width"])
    h = int(box["height"])

    pad = 8
    left = max(0, x - pad)
    top = max(0, y - pad)
    right = min(img.width - 1, x + w + pad)
    bottom = min(img.height - 1, y + h + pad)

    # red rectangle (thick line)
    for i in range(4):
        draw.rectangle([left-i, top-i, right+i, bottom+i], outline="red")

    img.save(out_path)

def save_annotated(page, locator, filename, label=""):
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    box = locator.bounding_box()
    if not box:
        raise RuntimeError(f"요소 위치를 찾을 수 없습니다: {label}")

    raw = OUT / ("_raw_" + filename)
    final = OUT / filename
    page.screenshot(path=str(raw), full_page=False)
    annotate(raw, box, final)
    raw.unlink(missing_ok=True)

def first_visible(page, *loc_funcs):
    for f in page.frames:
        for fn in loc_funcs:
            try:
                loc = fn(f)
                cnt = loc.count()
                for i in range(cnt):
                    item = loc.nth(i)
                    if item.is_visible():
                        box = item.bounding_box()
                        if box and box.get("width", 0) > 0 and box.get("height", 0) > 0:
                            return item
            except Exception:
                pass
    raise RuntimeError("표시 가능한 대상 요소를 찾지 못했습니다.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)

    # 1. CRAN home
    page.goto("https://cran.r-project.org/", wait_until="networkidle")
    win_link = first_visible(
        page,
        lambda f: f.get_by_text("Download R for Windows", exact=False),
        lambda f: f.locator('a[href*="bin/windows"]')
    )
    save_annotated(
        page, win_link,
        "01_cran_windows.png",
        "Download R for Windows 클릭"
    )
    win_link.click()
    page.wait_for_load_state("networkidle")

    # 2. Windows page -> base
    base_link = first_visible(
        page,
        lambda f: f.get_by_text("base", exact=False),
        lambda f: f.locator('a[href*="bin/windows/base"]')
    )
    save_annotated(
        page, base_link,
        "02_cran_base.png",
        "base 클릭"
    )
    base_link.click()
    page.wait_for_load_state("networkidle")

    # 3. latest Windows installer
    download_link = first_visible(
        page,
        lambda f: f.locator('a[href$="-win.exe"]'),
        lambda f: f.locator('a[href*="R-"][href*="-win.exe"]'),
        lambda f: f.get_by_text("Download R", exact=False)
    )
    save_annotated(
        page, download_link,
        "03_cran_download.png",
        "최신 R 설치 파일 다운로드"
    )

    # 4. Posit downloads
    page.goto("https://posit.co/downloads/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    rstudio = first_visible(
        page,
        lambda f: f.get_by_text("RStudio Desktop", exact=False),
        lambda f: f.locator('text=RStudio Desktop')
    )
    save_annotated(
        page, rstudio,
        "04_posit_rstudio.png",
        "RStudio Desktop 찾기"
    )

    # 5. try to find download CTA near RStudio
    try:
        dl = first_visible(
            page,
            lambda f: f.get_by_text("Download RStudio", exact=False),
            lambda f: f.locator('a[href*="rstudio"]'),
            lambda f: f.locator('a[href*="download"]')
        )
        save_annotated(
            page, dl,
            "05_rstudio_download.png",
            "RStudio 다운로드"
        )
    except Exception:
        # fallback: annotate RStudio heading again
        save_annotated(
            page, rstudio,
            "05_rstudio_download.png",
            "RStudio Desktop 다운로드 영역"
        )

    browser.close()

print("완료: images 폴더에 빨간색 박스만 표시된 캡처 이미지가 생성되었습니다.")
