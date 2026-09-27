"""根据本地尺码表回答身高、体重相关问题。"""

import re
from pathlib import Path


SIZE_GUIDE = Path(__file__).resolve().parent / "data" / "尺码推荐.txt"
SIZE_ROW = re.compile(
    r"身高：(?P<height_min>\d+)(?:-(?P<height_max>\d+))?cm\+?，"
    r"体重：(?P<weight_min>\d+)(?:-(?P<weight_max>\d+))?\s*斤\+?，"
    r"建议尺码(?P<size>[A-Z0-9]+)。"
)
HEIGHT_CM = re.compile(r"(\d+(?:\.\d+)?)\s*(?:cm|厘米|公分)", re.IGNORECASE)
HEIGHT_M = re.compile(r"(\d(?:\.\d+)?)\s*米")
HEIGHT_WITHOUT_UNIT = re.compile(r"身高\s*(?:是|为|[:：])?\s*(\d{2,3}(?:\.\d+)?)", re.IGNORECASE)
WEIGHT = re.compile(r"(\d+(?:\.\d+)?)\s*(斤|公斤|千克|kg)", re.IGNORECASE)
BARE_NUMBER = re.compile(r"\s*(\d{2,3}(?:\.\d+)?)\s*")


def _measurements(text):
    height_match = HEIGHT_CM.search(text)
    if height_match:
        height = float(height_match.group(1))
    else:
        height_match = HEIGHT_M.search(text)
        if height_match:
            height = float(height_match.group(1)) * 100
        else:
            height_match = HEIGHT_WITHOUT_UNIT.search(text)
            height = float(height_match.group(1)) if height_match else None

    weight_match = WEIGHT.search(text)
    if weight_match:
        weight = float(weight_match.group(1))
        if weight_match.group(2).lower() in {"公斤", "千克", "kg"}:
            weight *= 2
    else:
        weight = None
    return height, weight


def recommend_size(question, previous_messages=()):
    """返回本地尺码建议；非尺码问题返回 None，交给原有 RAG 流程。"""
    last_assistant = next(
        (message["content"] for message in reversed(previous_messages) if message["role"] == "assistant"),
        "",
    )
    number_reply = BARE_NUMBER.fullmatch(question)
    requested_height = "请提供身高" in last_assistant
    requested_weight = "请提供体重" in last_assistant
    if not (
        "尺码" in question
        or HEIGHT_CM.search(question)
        or HEIGHT_M.search(question)
        or HEIGHT_WITHOUT_UNIT.search(question)
        or WEIGHT.search(question)
        or (number_reply and (requested_height or requested_weight))
    ):
        return None

    height, weight = _measurements(question)
    if number_reply and requested_height:
        height = float(number_reply.group(1))
    elif number_reply and requested_weight:
        weight = float(number_reply.group(1))
    for message in reversed(previous_messages):
        if message["role"] != "user":
            continue
        old_height, old_weight = _measurements(message["content"])
        height = height if height is not None else old_height
        weight = weight if weight is not None else old_weight
        if height is not None and weight is not None:
            break

    if height is None or weight is None:
        missing = "身高和体重" if height is None and weight is None else ("身高" if height is None else "体重")
        return f"请提供{missing}，我会根据《尺码推荐.txt》匹配尺码。"

    matches = []
    for line in SIZE_GUIDE.read_text(encoding="utf-8").splitlines():
        row = SIZE_ROW.fullmatch(line.strip())
        if row is None:
            raise ValueError(f"尺码表格式无法识别：{line}")
        height_max = float(row["height_max"]) if row["height_max"] else float("inf")
        weight_max = float(row["weight_max"]) if row["weight_max"] else float("inf")
        if float(row["height_min"]) <= height <= height_max and float(row["weight_min"]) <= weight <= weight_max:
            matches.append(row["size"])

    if not matches:
        return f"《尺码推荐.txt》中没有同时覆盖身高{height:g}cm、体重{weight:g}斤的尺码。"
    sizes = "、".join(matches)
    if len(matches) > 1:
        return f"根据《尺码推荐.txt》，身高{height:g}cm、体重{weight:g}斤同时符合{sizes}。表格区间有重叠，无法仅凭这份表格确定唯一尺码。"
    return f"根据《尺码推荐.txt》，身高{height:g}cm、体重{weight:g}斤建议尺码{sizes}。"
