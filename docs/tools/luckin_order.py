#!/usr/bin/env python3
"""Luckin order helper for the WeChat Claude Code workspace."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_LAT = os.getenv("LUCKIN_DEFAULT_LAT", "31.2304")
DEFAULT_LNG = os.getenv("LUCKIN_DEFAULT_LNG", "121.4737")
DEFAULT_PRODUCT = os.getenv("LUCKIN_DEFAULT_PRODUCT_KEYWORD", "咖啡")
ENV_PATH = Path.home() / ".luckin" / ".env"
LAST_ORDER_PATH = Path.home() / ".luckin" / "last_order.json"
DEFAULT_LUCKIN_BIN = str(Path.home() / ".local" / "bin" / "luckin")


@dataclass
class Intent:
    store_keyword: str
    product_keyword: str
    amount: int
    nearby: bool


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Luckin pending-payment order.")
    parser.add_argument("message", help="User coffee order message")
    parser.add_argument("--lat", default=DEFAULT_LAT)
    parser.add_argument("--lng", default=DEFAULT_LNG)
    parser.add_argument("--stores-only", action="store_true", help="Only search nearby Luckin stores.")
    parser.add_argument("--preview-only", action="store_true", help="Demo-safe mode: preview the order without creating a pending-payment order.")
    parser.add_argument("--order-detail", action="store_true", help="Show order detail by order id, or latest created order.")
    args = parser.parse_args()

    load_luckin_env()

    lat, lng = resolve_location(args.message, args.lat, args.lng)

    if args.order_detail or looks_like_order_lookup(args.message):
        try:
            print(format_order_detail(args.message))
            return 0
        except RuntimeError as exc:
            print(str(exc))
            return 1

    if args.stores_only or looks_like_store_lookup(args.message):
        try:
            print(format_stores(search_stores(args.message, lat, lng)))
            return 0
        except RuntimeError as exc:
            print(str(exc))
            return 1

    intent = parse_intent(args.message)
    if not intent:
        print("妹妹还没识别出具体咖啡点单。可以这样说：帮我来一杯冰美式、来两杯热拿铁，或找一下附近的瑞幸门店。")
        return 2

    try:
        result = create_order(intent, lat, lng, preview_only=args.preview_only)
    except RuntimeError as exc:
        print(str(exc))
        return 1

    print(result)
    return 0


def load_luckin_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def parse_intent(message: str) -> Intent | None:
    text = re.sub(r"\s+", "", message)
    if not text:
        return None

    coffee_words = ("瑞幸", "Luckin", "luckin", "咖啡", "美式", "拿铁", "生椰", "椰椰", "橙C", "橙c", "厚乳", "冰萃", "葡萄冰萃")
    order_words = ("点", "下单", "下一杯", "下杯", "来一杯", "来杯", "来两杯", "来三杯", "来", "买", "帮我叫", "帮我订", "使用优惠券")
    if not any(word in text for word in coffee_words) or not any(word in text for word in order_words):
        return None

    nearby = any(word in text for word in ("附近", "最近", "周边"))
    store_keyword = ""
    product_part = text

    store_match = re.search(r"在(.+?)(?:店|门店)?(?:点|下单|买|来|下)", text)
    if store_match:
        store_keyword = clean_store(store_match.group(1))
        nearby = nearby or store_keyword in {"附近", "最近", "周边"}
        product_part = text[store_match.end() :]
    else:
        product_part = strip_order_prefix(text)

    amount = parse_amount(product_part)
    product_keyword = clean_product(product_part) or DEFAULT_PRODUCT
    if product_keyword in {"咖啡", "一杯咖啡", "杯咖啡"}:
        product_keyword = DEFAULT_PRODUCT

    return Intent(
        store_keyword="" if nearby else store_keyword,
        product_keyword=product_keyword,
        amount=amount,
        nearby=nearby or not store_keyword,
    )


def looks_like_store_lookup(message: str) -> bool:
    text = re.sub(r"\s+", "", message)
    store_words = ("瑞幸门店", "Luckin门店", "门店", "附近", "周边", "最近")
    lookup_words = ("看看", "查", "找一下", "找", "有没有", "哪家", "附近有没有", "配送范围")
    return any(word in text for word in store_words) and any(word in text for word in lookup_words)


def looks_like_order_lookup(message: str) -> bool:
    text = re.sub(r"\s+", "", message)
    return "订单" in text and any(word in text for word in ("看", "查", "查看", "最近", "详情"))


def search_stores(message: str, lat: str, lng: str) -> list[dict[str, Any]]:
    text = re.sub(r"\s+", "", message)
    keyword = ""
    for candidate in ("曾厝垵", "人民广场", "厦门", "附近"):
        if candidate in text and candidate != "附近":
            keyword = candidate
            break

    args = ["store", lat, lng]
    if keyword:
        args.append(keyword)

    store_text = run_luckin(*args)
    try:
        payload = json.loads(store_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"妹妹查门店时没读懂返回结果：{store_text[:200]}") from exc

    data = payload.get("data") or []
    if isinstance(data, dict):
        for key in ("list", "stores", "shopList", "deptList"):
            if isinstance(data.get(key), list):
                data = data[key]
                break

    if not isinstance(data, list):
        data = []
    return [item for item in data if isinstance(item, dict)]


def create_order(intent: Intent, lat: str, lng: str, preview_only: bool = False) -> str:
    store_cmd = ["store", lat, lng]
    if intent.store_keyword:
        store_cmd.append(intent.store_keyword)

    store_text = run_luckin(*store_cmd)
    dept_id = first_id(store_text, ("deptId", "dept_id", "deptNo", "storeId", "id"))
    if not dept_id:
        raise RuntimeError("妹妹查不到合适门店。可以换个更明确的门店名，或先确认默认定位。")

    product_text = run_luckin("product", dept_id, intent.product_keyword)
    product_spec = product_spec_from(product_text, intent.amount)
    if not product_spec:
        raise RuntimeError("妹妹查到了门店，但没找到可下单商品。可以换个更具体的咖啡名，比如美式、拿铁、橙C美式。")

    preview_text = run_luckin("order", "preview", dept_id, "-p", product_spec)
    if preview_only:
        return format_preview_reply(intent, dept_id, product_spec, preview_text)

    create_text = run_luckin("order", "create", dept_id, "-p", product_spec, "--lat", lat, "--lng", lng)

    return format_reply(intent, dept_id, product_spec, preview_text, create_text)


def run_luckin(*args: str) -> str:
    luckin_bin = os.getenv("LUCKIN_BIN", DEFAULT_LUCKIN_BIN)
    if not Path(luckin_bin).exists():
        luckin_bin = "luckin"
    env = os.environ.copy()
    env["PATH"] = f"{Path.home() / '.local' / 'bin'}:{env.get('PATH', '')}"
    result = subprocess.run(
        [luckin_bin, *args],
        check=False,
        text=True,
        capture_output=True,
        timeout=90,
        env=env,
    )
    text = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    if result.returncode != 0:
        if "LUCKIN_MCP_ORDER_TOKEN" in text or "luckin login" in text:
            raise RuntimeError("妹妹还没拿到瑞幸登录态。请先在这台机器上完成 luckin login。")
        raise RuntimeError(text or "Luckin 命令执行失败。")
    return text


def clean_store(value: str) -> str:
    return re.sub(r"^(帮我|请|给我|替我|到)", "", value).strip("，。,. ")


def strip_order_prefix(value: str) -> str:
    value = re.sub(r"^(帮我|请|给我|替我)?使用优惠券[，,]?", "", value)
    value = re.sub(r"^(帮我|请|给我|替我)?(在)?(附近|最近|周边)?", "", value)
    return re.sub(r"^(点|下单|下一杯|下杯|买|来|帮我叫|帮我订)", "", value)


def clean_product(value: str) -> str:
    value = re.sub(r"^(一杯|1杯|两杯|二杯|2杯|三杯|3杯|杯|份|个|一份|来一杯|来杯|点杯|点一杯|下一杯|下杯)", "", value)
    value = re.split(r"(配送地址|送到|地址|用Luckin|用luckin|用瑞幸|，|,|。)", value, maxsplit=1)[0]
    value = re.sub(r"^(冰|热)", "", value)
    value = re.sub(r"(五分糖|五分甜|半糖|少少甜|少甜|少糖|微甜|无糖|正常糖|加冰|少冰|去冰)$", "", value)
    value = re.sub(r"(谢谢|哈|呀|吧|。|！|!)$", "", value)
    return value.strip("，。,. ")


def parse_amount(value: str) -> int:
    if re.search(r"(两杯|二杯|2杯|两份|二份|2份)", value):
        return 2
    if re.search(r"(三杯|3杯|三份|3份)", value):
        return 3
    return 1


def resolve_location(message: str, default_lat: str, default_lng: str) -> tuple[str, str]:
    text = re.sub(r"\s+", "", message)
    known_locations = {
        "曾厝垵": ("24.4356", "118.1317"),
        "厦门": ("24.4798", "118.0894"),
        "人民广场": ("31.2304", "121.4737"),
    }
    for keyword, coords in known_locations.items():
        if keyword in text:
            return coords
    return default_lat, default_lng


def first_id(text: str, keys: tuple[str, ...]) -> str | None:
    for item in iter_json_items(text):
        for key in keys:
            value = item.get(key)
            if value is not None:
                return str(value)

    for key in keys:
        match = re.search(rf'"?{re.escape(key)}"?\s*[:=：]\s*"?([A-Za-z0-9_-]+)"?', text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def product_spec_from(text: str, amount: int) -> str | None:
    product_id = first_id(text, ("productId", "product_id", "goodsId", "id"))
    sku_code = first_id(text, ("skuCode", "sku_code", "skuId", "sku"))
    if product_id and sku_code:
        return f"{product_id}:{sku_code}:{amount}"
    return None


def iter_json_items(text: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []

    items: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            items.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(parsed)
    return items


def format_reply(intent: Intent, dept_id: str, product_spec: str, preview_text: str, create_text: str) -> str:
    preview = json.loads(preview_text)
    created = json.loads(create_text)

    data = preview.get("data", {})
    order = created.get("data", {})
    shop = data.get("shopInfo", {})
    product = (data.get("productInfoList") or [{}])[0]

    lines = [
        "姐姐，妹妹已经帮你创建好瑞幸待支付订单了。",
        f"订单号：{order.get('orderIdStr') or order.get('orderId')}",
        f"门店：{shop.get('deptName', '附近门店')}",
        f"地址：{shop.get('address', '门店地址以瑞幸订单为准')}",
        f"商品：{product.get('name', intent.product_keyword)} x {intent.amount}",
    ]

    addition = product.get("additionDesc")
    if addition:
        lines.append(f"规格：{addition}")

    price = product.get("estimateTotalPrice") or product.get("estimatePrice") or data.get("discountPrice")
    if price is not None:
        lines.append(f"价格：{price} 元")

    pay_url = order.get("payOrderUrl")
    qr_url = order.get("payOrderQrCodeUrl")
    if pay_url:
        lines.append(f"微信支付链接：{pay_url}")
    if qr_url:
        lines.append(f"支付二维码：{qr_url}")

    lines.append("您确认门店和商品没问题后，点链接或扫码支付就好。")
    save_last_order(order, shop, product)
    return "\n".join(str(line) for line in lines if line)


def format_preview_reply(intent: Intent, dept_id: str, product_spec: str, preview_text: str) -> str:
    preview = json.loads(preview_text)
    data = preview.get("data", {})
    shop = data.get("shopInfo", {})
    product = (data.get("productInfoList") or [{}])[0]

    lines = [
        "姐姐，妹妹已经帮你跑通瑞幸下单预览了（演示模式，未创建订单、未支付）。",
        f"门店：{shop.get('deptName', '附近门店')}",
        f"地址：{shop.get('address', '门店地址以瑞幸订单为准')}",
        f"商品：{product.get('name', intent.product_keyword)} x {intent.amount}",
    ]

    addition = product.get("additionDesc")
    if addition:
        lines.append(f"规格：{addition}")

    price = product.get("estimateTotalPrice") or product.get("estimatePrice") or data.get("discountPrice")
    if price is not None:
        lines.append(f"预估价格：{price} 元")

    lines.append(f"门店ID：{dept_id}")
    lines.append(f"商品规格：{product_spec}")
    lines.append("Demo 结论：store → product → order preview 链路已通。真实下单时去掉 --preview-only。")
    return "\n".join(str(line) for line in lines if line)


def save_last_order(order: dict[str, Any], shop: dict[str, Any], product: dict[str, Any]) -> None:
    LAST_ORDER_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "orderId": order.get("orderIdStr") or order.get("orderId"),
        "payOrderUrl": order.get("payOrderUrl"),
        "payOrderQrCodeUrl": order.get("payOrderQrCodeUrl"),
        "shopName": shop.get("deptName"),
        "productName": product.get("name"),
    }
    LAST_ORDER_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def format_order_detail(message: str) -> str:
    order_id = extract_order_id(message)
    if not order_id:
        order_id = load_last_order_id()
    if not order_id:
        raise RuntimeError("妹妹现在还没有最近订单记录。您可以把订单号发我，我就能帮您查详情。")

    detail_text = run_luckin("order", "detail", order_id)
    try:
        payload = json.loads(detail_text)
    except json.JSONDecodeError:
        return f"姐姐，订单 {order_id} 的详情返回如下：\n{detail_text}"

    data = payload.get("data") or {}
    lines = [f"姐姐，妹妹查到订单 {order_id}："]
    for key, label in (
        ("orderStatus", "状态"),
        ("orderStatusName", "状态"),
        ("deptName", "门店"),
        ("discountPrice", "价格"),
        ("payOrderUrl", "微信支付链接"),
        ("payOrderQrCodeUrl", "支付二维码"),
    ):
        value = data.get(key)
        if value not in (None, ""):
            lines.append(f"{label}：{value}")
    if len(lines) == 1:
        lines.append(json.dumps(data or payload, ensure_ascii=False)[:1000])
    return "\n".join(lines)


def extract_order_id(message: str) -> str | None:
    match = re.search(r"\b(\d{10,})\b", message)
    return match.group(1) if match else None


def load_last_order_id() -> str | None:
    if not LAST_ORDER_PATH.exists():
        return None
    try:
        payload = json.loads(LAST_ORDER_PATH.read_text())
    except json.JSONDecodeError:
        return None
    value = payload.get("orderId")
    return str(value) if value else None


def format_stores(stores: list[dict[str, Any]]) -> str:
    if not stores:
        return "妹妹查了一下，当前定位附近暂时没有拿到可用的 Luckin 门店结果。可以换个更具体的位置，比如“厦门曾厝垵附近有没有门店”。"

    lines = ["姐姐，妹妹查到附近这些 Luckin 门店："]
    for idx, store in enumerate(stores[:5], start=1):
        name = store.get("deptName") or store.get("name") or store.get("storeName") or "Luckin 门店"
        address = store.get("address") or store.get("addr") or "地址以瑞幸订单为准"
        status = store.get("workStatus") or store.get("status") or ""
        distance = store.get("distance")
        distance_text = f"，距离 {distance}m" if distance not in (None, "", 0.0) else ""
        suffix = f"（{status}{distance_text}）" if status or distance_text else ""
        lines.append(f"{idx}. {name}{suffix}")
        lines.append(f"   {address}")
    lines.append("要下单的话，直接说“点一杯美式/拿铁/咖啡”，妹妹可以继续帮您创建待支付订单。")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
