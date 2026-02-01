import re
import time
from collections import OrderedDict
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

LISTING_URL = (
    "https://suumo.jp/jj/bukken/ichiran/JJ012FC001/?ar=030&bs=011&ra=030013"
    "&rnek=000519120&rnek=000522350&rnek=000539120&rnek=000502060&rnek=000506000"
    "&rnek=000520550&rnek=000515330&rnek=000529160&rnek=000529650&rnek=030501820"
    "&rnek=030541160&rnek=030517470&rnek=030541280&rnek=030505600&rnek=030532110"
    "&rnek=030527280&rnek=030513930&rnek=030500640&rnek=030506640&rnek=030528500"
    "&rnek=030511640&rnek=030536880&rnek=057312220&rnek=001502060&rnek=001519160"
    "&rnek=001514430&rnek=001519680&rnek=001519690&rnek=001528860&rnek=001527320"
    "&rnek=001527360&rnek=001534900&rnek=001520030&rnek=001531910&rnek=004520460"
    "&rnek=004550050&rnek=004520870&rnek=004350015&rnek=004308710&rnek=007050020"
    "&rnek=007050025&rnek=007050030&rnek=007008030&rnek=007028870&cn=30&pc=30"
)

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_TIMEOUT = 20
SLEEP_SECONDS = 1.5
CSV_OUTPUT = "suumo_results.csv"

COLUMNS = [
    "url",
    "物件名",
    "価格",
    "所在地",
    "交通",
    "間取り",
    "専有面積",
    "バルコニー面積",
    "築年数（築年月）",
    "階数 / 所在階",
    "向き",
    "管理費",
    "修繕積立金",
    "その他費用",
    "引渡し時期",
    "取引態様",
    "情報更新日",
    "次回更新予定日（あれば）",
    "建物構造（RC / SRC 等）",
    "総戸数",
    "駐車場",
    "用途地域",
    "土地権利",
    "管理形態 / 管理会社",
    "リフォーム（有無・内容が取れれば）",
]

LABEL_MAP = {
    "物件名": "物件名",
    "価格": "価格",
    "販売価格": "価格",
    "所在地": "所在地",
    "交通": "交通",
    "間取り": "間取り",
    "専有面積": "専有面積",
    "バルコニー面積": "バルコニー面積",
    "バルコニー": "バルコニー面積",
    "築年数": "築年数（築年月）",
    "築年月": "築年数（築年月）",
    "向き": "向き",
    "管理費": "管理費",
    "修繕積立金": "修繕積立金",
    "その他費用": "その他費用",
    "引渡": "引渡し時期",
    "引渡し": "引渡し時期",
    "取引態様": "取引態様",
    "情報更新日": "情報更新日",
    "次回更新日": "次回更新予定日（あれば）",
    "次回更新予定日": "次回更新予定日（あれば）",
    "構造": "建物構造（RC / SRC 等）",
    "建物構造": "建物構造（RC / SRC 等）",
    "総戸数": "総戸数",
    "駐車場": "駐車場",
    "用途地域": "用途地域",
    "土地権利": "土地権利",
    "管理形態": "管理形態 / 管理会社",
    "管理会社": "管理形態 / 管理会社",
    "リフォーム": "リフォーム（有無・内容が取れれば）",
    "リノベーション": "リフォーム（有無・内容が取れれば）",
}


def fetch_html(session: requests.Session, url: str) -> Optional[str]:
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.text
        print(f"[WARN] status {response.status_code} for {url}")
    except requests.RequestException as exc:
        print(f"[WARN] request failed for {url}: {exc}")
    return None


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_detail_urls(listing_html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(listing_html, "html.parser")
    urls: List[str] = []
    seen = set()
    for anchor in soup.select("a[href]"):
        href = anchor.get("href")
        if not href:
            continue
        if "/jj/bukken/" not in href and "/ms/" not in href and "/bukken/" not in href:
            continue
        full_url = urljoin(base_url, href)
        if full_url in seen:
            continue
        seen.add(full_url)
        urls.append(full_url)
    return urls


def extract_next_page_url(listing_html: str, base_url: str) -> Optional[str]:
    soup = BeautifulSoup(listing_html, "html.parser")
    next_link = soup.select_one("a[rel='next']")
    if not next_link:
        for anchor in soup.find_all("a"):
            if normalize_text(anchor.get_text()) in {"次へ", "次の30件", "次のページ"}:
                next_link = anchor
                break
    if not next_link:
        return None
    href = next_link.get("href")
    if not href:
        return None
    return urljoin(base_url, href)


def extract_pairs(soup: BeautifulSoup) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []

    for dl in soup.select("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        if len(dts) != len(dds):
            continue
        for dt, dd in zip(dts, dds):
            label = normalize_text(dt.get_text(" ", strip=True))
            value = normalize_text(dd.get_text(" ", strip=True))
            if label and value:
                pairs.append((label, value))

    for table in soup.select("table"):
        for row in table.select("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            label = normalize_text(th.get_text(" ", strip=True))
            value = normalize_text(td.get_text(" ", strip=True))
            if label and value:
                pairs.append((label, value))

    return pairs


def pick_first_text(soup: BeautifulSoup, selectors: Iterable[str]) -> Optional[str]:
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = normalize_text(node.get_text(" ", strip=True))
            if text:
                return text
    return None


def update_combined_field(data: Dict[str, Optional[str]], key: str, value: str) -> None:
    if not value:
        return
    if data.get(key):
        data[key] = f"{data[key]} / {value}"
    else:
        data[key] = value


def parse_detail_page(html: str, url: str) -> Dict[str, Optional[str]]:
    soup = BeautifulSoup(html, "html.parser")
    data: Dict[str, Optional[str]] = OrderedDict((col, None) for col in COLUMNS)
    data["url"] = url

    name = pick_first_text(
        soup, ["h1", ".property_view h1", ".section_h1-title", ".suumo_h1"]
    )
    price = pick_first_text(
        soup, [".property_view .price", ".price", ".bukkenTitle", ".property_view b"]
    )
    if name:
        data["物件名"] = name
    if price:
        data["価格"] = price

    pairs = extract_pairs(soup)
    floor_value = None
    total_floors = None
    management_parts: List[str] = []

    for label, value in pairs:
        normalized_label = normalize_text(label)
        if normalized_label in ("所在階", "階数"):
            if normalized_label == "所在階":
                floor_value = value
            else:
                total_floors = value
            continue
        if normalized_label in ("管理形態", "管理会社"):
            management_parts.append(value)
            continue

        for key, mapped in LABEL_MAP.items():
            if key in normalized_label:
                data[mapped] = value
                break

    if floor_value or total_floors:
        combined_floor = " / ".join([v for v in [floor_value, total_floors] if v])
        data["階数 / 所在階"] = combined_floor

    if management_parts:
        data["管理形態 / 管理会社"] = " / ".join(OrderedDict.fromkeys(management_parts))

    return data


def scrape_suumo(listing_url: str) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    detail_urls: List[str] = []
    seen_detail_urls = set()
    page_url = listing_url
    while page_url:
        listing_html = fetch_html(session, page_url)
        if not listing_html:
            raise RuntimeError(f"Failed to fetch listing page: {page_url}")
        page_detail_urls = extract_detail_urls(listing_html, page_url)
        for url in page_detail_urls:
            if url not in seen_detail_urls:
                seen_detail_urls.add(url)
                detail_urls.append(url)
        page_url = extract_next_page_url(listing_html, page_url)
        if page_url:
            time.sleep(SLEEP_SECONDS)

    if not detail_urls:
        raise RuntimeError("No detail URLs found. The page structure may have changed.")

    records: List[Dict[str, Optional[str]]] = []
    for idx, detail_url in enumerate(detail_urls, start=1):
        html = fetch_html(session, detail_url)
        if not html:
            records.append(OrderedDict((col, None) for col in COLUMNS))
            records[-1]["url"] = detail_url
            continue
        try:
            record = parse_detail_page(html, detail_url)
        except Exception as exc:
            print(f"[WARN] failed to parse {detail_url}: {exc}")
            record = OrderedDict((col, None) for col in COLUMNS)
            record["url"] = detail_url
        records.append(record)
        if idx < len(detail_urls):
            time.sleep(SLEEP_SECONDS)

    return pd.DataFrame(records, columns=COLUMNS)


def main() -> None:
    df = scrape_suumo(LISTING_URL)
    df.to_csv(CSV_OUTPUT, index=False)
    print(df.head())


if __name__ == "__main__":
    main()
