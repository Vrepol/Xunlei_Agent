# backend/download.py
import time
import os
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from typing import List

def start_download(magnet_links: List[str], server_addr: str, headless: bool = True) -> str:
    """
    从一组磁力链接执行批量下载，返回操作日志字符串（每行一条）。
    参数：
      - magnet_links: ["magnet:?xt=...", "magnet:?xt=...", ...]
      - server_addr: 如 "http://IP:Port"
      - headless: 是否无头模式
    返回：
      - str: 多行日志
    """
    logs = []

    if not server_addr.startswith("http"):
        logs.append(f"[ERROR] 无效的服务器地址: {server_addr}")
        return "\n".join(logs)

    # Selenium 初始化
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
    # 禁用图片、样式、字体，加快加载速度
    chrome_options.add_experimental_option(
        "prefs",
        {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
        }
    )
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")

    # —— 关键一步：指定 Chromium 可执行文件路径 —— #
    # 在 Raspberry Pi OS 上，apt 安装的 Chromium 可执行通常是 /usr/bin/chromium
    # 如果你不确定路径，可以在终端里执行 `which chromium` 来查看。
    chrome_options.binary_location = "/usr/bin/chromium"
    # 或者：chrome_options.binary_location = "/usr/bin/chromium-browser"
    # --------------------------------------------------------- #

    # 指定 Chromedriver 路径
    service = Service("/usr/bin/chromedriver")
    # 让 Chromedriver 输出日志到 /tmp/chromedriver.log，方便排查
    service.log_path = "/tmp/chromedriver.log"
    service.verbose = True

    try:
        driver = webdriver.Chrome(options=chrome_options, service=service)
    except Exception as e:
        # 打印完整 Traceback 到控制台
        traceback.print_exc()
        logs.append(f"[ERROR] 无法启动 ChromeDriver: {repr(e)}")
        return "\n".join(logs)

    for idx, link in enumerate(magnet_links, start=1):
        link = link.strip()
        if not link:
            continue

        logs.append(f"[{idx}/{len(magnet_links)}] 开始处理: {link}")
        try:
            driver.get(server_addr)
            driver.implicitly_wait(2)

            # 点击“新建任务”按钮
            new_task_btn = driver.find_element(By.CSS_SELECTOR, ".create__task")
            new_task_btn.click()

            # 等待输入对话框出现
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".nas-task-dialog"))
            )

            # 填写磁力链接并确认
            input_box = driver.find_element(By.CSS_SELECTOR, ".el-textarea__inner")
            input_box.clear()
            input_box.send_keys(link)

            confirm_btn = driver.find_element(
                By.CSS_SELECTOR,
                ".el-dialog__footer .el-button.el-button--primary.task-parse-btn"
            )
            confirm_btn.click()

            # 等待解析完成
            time.sleep(1)

            download_btn = driver.find_element(
                By.CSS_SELECTOR,
                ".result-nas-task-dialog_footer .el-button.el-button--primary.task-parse-btn"
            )
            download_btn.click()
            logs.append(f"[{idx}] 已点击下载按钮")

            time.sleep(1)
        except Exception as e:
            logs.append(f"[{idx}] 处理失败: {repr(e)}")

    driver.quit()
    logs.append(f"已处理 {len(magnet_links)} 条磁力链接。")
    return "\n".join(logs)