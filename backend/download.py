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
from selenium.common.exceptions import TimeoutException
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

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式，可根据需要注释
    chrome_options.add_argument("--no-sandbox")  # 关键
    chrome_options.add_argument("--disable-dev-shm-usage")  # 关键
    prefs = {"profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2}
    service = Service("/usr/bin/chromedriver")
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=chrome_options,service=service)
    for idx, link in enumerate(magnet_links, start=1):
        link = link.strip()
        if not link:
            continue

        logs.append(f"[{idx}/{len(magnet_links)}] 开始处理: {link}")
        # 访问你的下载服务器页面
        driver.get(server_addr)
 
        driver.implicitly_wait(2)

        new_task_btn = driver.find_element(By.CSS_SELECTOR, ".create__task")
        new_task_btn.click()

        # 显式等待弹窗出现
        wait = WebDriverWait(driver, 2)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".nas-task-dialog")))

        # 找到输入框，输入磁力链接
        input_box = driver.find_element(By.CSS_SELECTOR, ".el-textarea__inner")
        input_box.send_keys(link)

        # 找到确认按钮
        confirm_btn = driver.find_element(By.CSS_SELECTOR, ".el-dialog__footer .el-button.el-button--primary.task-parse-btn")
        confirm_btn.click()

        # 等一下解析完（这里简单等待 1 秒，可根据页面加载情况调整）
        time.sleep(1)

        # 点击下载按钮
        download_btn = driver.find_element(By.CSS_SELECTOR, ".result-nas-task-dialog_footer .el-button.el-button--primary.task-parse-btn")
        download_btn.click()

        # 等待一些时间，或在此处做更多校验
        time.sleep(1)

    driver.quit()
    logs.append(f"已处理 {len(magnet_links)} 条磁力链接。")
    return "\n".join(logs)