import asyncio
import json
from playwright.async_api import async_playwright


async def scrape_bilibili_videos():
    url = "https://space.bilibili.com/24647191/search?keyword=%E7%9B%B4%E6%92%AD"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        page = await context.new_page()
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        )

        print(f"正在访问: {url}")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(5000)

        # 滚动加载更多内容
        print("滚动页面加载更多视频...")
        for i in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

        print("查找视频元素...")

        # 使用JavaScript提取视频信息
        videos_data = await page.evaluate(
            """() => {
            const videos = [];
            const links = document.querySelectorAll('a[href*="/video/"]');

            links.forEach(link => {
                const href = link.href;
                if (!href || videos.some(v => v.url === href)) return;

                // 尝试获取标题
                let title = "";

                // 从最近的card元素获取
                const card = link.closest('[class*="video-card"]');
                if (card) {
                    const titleEl = card.querySelector('.bili-video-card__info--tit, .video-title, [class*="title"]');
                    if (titleEl) {
                        title = titleEl.textContent || titleEl.getAttribute("title") || "";
                    }
                }

                // 从link的title属性
                if (!title) {
                    title = link.getAttribute("title") || "";
                }

                // 从link的文本内容（第一行）
                if (!title) {
                    const text = link.textContent.trim();
                    const lines = text.split('\\n');
                    if (lines.length > 0) {
                        title = lines[0].trim();
                    }
                }

                // 如果还是没有标题，获取link内第一个有意义的文本
                if (!title || title.length < 3) {
                    const parent = link.parentElement;
                    if (parent) {
                        const titleElements = parent.querySelectorAll('.title, [class*="title"], h3, h4');
                        titleElements.forEach(el => {
                            if (!title) {
                                title = el.textContent || el.getAttribute("title") || "";
                            }
                        });
                    }
                }

                title = title.trim();

                if (href && href.includes('bilibili.com/video/')) {
                    videos.push({
                        title: title || "N/A",
                        url: href
                    });
                }
            });

            return videos;
        }"""
        )

        print(f"找到 {len(videos_data)} 个视频")

        await browser.close()

        return videos_data


if __name__ == "__main__":
    result = asyncio.run(scrape_bilibili_videos())
    print(f"\n共找到 {len(result)} 个视频:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 保存到JSON文件
    with open("bilibili_videos.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n视频信息已保存到 bilibili_videos.json")
