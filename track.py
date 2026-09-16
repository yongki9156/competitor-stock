# -*- coding: utf-8 -*-
"""
깃허브 액션스에서 매일 자동 실행되는 재고 조회 스크립트
data/history.json  : 상품별 날짜별 재고 원본 기록
data/report.csv    : 날짜별 판매추정 누적 기록 (대시보드가 이 파일을 읽음)
data/latest.json   : 대시보드가 바로 읽기 쉬운 최신 요약 (스토어별 최근 추정치)
"""

import json
import os
import time
import csv
from datetime import date

import requests

# ---------------- 추적할 상품 목록 ----------------
PRODUCTS = [
    {"store": "새로고침", "channel": "2sXkKvcjUjDuEbb5ZyIyJ", "product": "8709132931"},
    # {"store": "경쟁사A", "channel": "여기에채널아이디", "product": "여기에상품번호"},
]

REQUEST_DELAY_SEC = 2

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
REPORT_FILE = os.path.join(DATA_DIR, "report.csv")
LATEST_FILE = os.path.join(DATA_DIR, "latest.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://smartstore.naver.com/",
}


def fetch_stock(channel_id: str, product_no: str):
    url = f"https://smartstore.naver.com/i/v2/channels/{channel_id}/products/{product_no}?withWindow=false"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"  [실패] {product_no} - {e}")
        return None

    total = 0
    found = False

    for group in (data.get("combinationOptions") or []):
        for opt in group.get("options", []):
            qty = opt.get("stockQuantity")
            if qty is not None:
                total += qty
                found = True

    if not found:
        for opt in (data.get("simpleOptions") or []):
            qty = opt.get("stockQuantity")
            if qty is not None:
                total += qty
                found = True

    if not found and data.get("stockQuantity") is not None:
        total = data["stockQuantity"]
        found = True

    return total if found else None


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def append_report(rows):
    file_exists = os.path.exists(REPORT_FILE)
    with open(REPORT_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["날짜", "스토어", "상품번호", "오늘재고", "어제재고", "판매추정"])
        writer.writerows(rows)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    today = date.today().isoformat()
    history = load_json(HISTORY_FILE, {})
    latest = load_json(LATEST_FILE, {})
    report_rows = []

    for item in PRODUCTS:
        store, channel, product = item["store"], item["channel"], item["product"]
        key = f"{channel}_{product}"

        stock = fetch_stock(channel, product)
        if stock is None:
            time.sleep(REQUEST_DELAY_SEC)
            continue

        product_history = history.setdefault(key, {})
        yesterday_stock = None
        for d in sorted(product_history.keys(), reverse=True):
            if d < today:
                yesterday_stock = product_history[d]
                break

        product_history[today] = stock

        if yesterday_stock is None:
            est_sold = ""
        else:
            diff = yesterday_stock - stock
            est_sold = diff if diff > 0 else 0

        report_rows.append([today, store, product, stock, yesterday_stock if yesterday_stock is not None else "", est_sold])
        latest[key] = {
            "store": store,
            "product": product,
            "date": today,
            "stock": stock,
            "estSold": est_sold,
        }
        time.sleep(REQUEST_DELAY_SEC)

    save_json(HISTORY_FILE, history)
    save_json(LATEST_FILE, latest)
    if report_rows:
        append_report(report_rows)


if __name__ == "__main__":
    main()
