import re
from dataclasses import dataclass, field
import json


@dataclass
class Order:
    ticker: str = None
    time: str = None
    close_price: float = None
    action: str = None
    comment: str = None
    trade_id: str = None
    size: float = None
    message: str = None
    order_type: str = None  # "OPEN", "CLOSE", or None
    raw_data: dict = field(default_factory=dict)


def parse_order_text(text: str) -> Order:
    patterns = {
        "ticker": r"Segnale su (.+)",
        "time": r"Ora:\s*(.+)",
        "close_price": r"Prezzo chiusura:\s*([\d.]+)",
        "action": r"Azione:\s*(.+)",
        "comment": r"Commento:\s*(.+)",
        "trade_id": r"id trade\s+(.+)",
        "size": r"size:\s*([\d.]+)",
        "message": r"Message:\s*(.+)"
    }

    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            extracted[key] = match.group(1).strip()

    # Determina il tipo di ordine
    comment = extracted.get("comment", "").upper()
    message = extracted.get("message", "").upper()
    if "CLOSE" in comment or "CLOSE" in message:
        order_type = "CLOSE"
    elif "OPEN" in comment or "OPEN" in message:
        order_type = "OPEN"
    else:
        order_type = None

    return Order(
        ticker=extracted.get("ticker") if "ticker" in extracted else None,
        time=extracted.get("time") if "time" in extracted else None,
        close_price=float(extracted["close_price"]) if "close_price" in extracted else None,
        action=extracted.get("action") if "action" in extracted else None,
        comment=extracted.get("comment") if "comment" in extracted else None,
        trade_id=extracted.get("trade_id") if "trade_id" in extracted else None,
        size=float(extracted["size"]) if "size" in extracted else None,
        message=extracted.get("message")if "size" in extracted else None,
        order_type=order_type,
        raw_data=extracted
    )


def process_order_request(request) -> Order:
    print("=======================================")
    print("Received Order Request")
    print("_______________________________________")
    # Estrai il corpo JSON dalla request
    data = request.get_json()
    print("json data: ", json.dumps(data, indent=2))

    # Esegui il parsing del campo "text"
    order = parse_order_text(data["text"])

    print("_______________________________________")
    print("ticker:", order.ticker)
    print("action:", order.action)
    print("comment:", order.comment)
    print("message:", order.message)
    print("size:", order.size)
    print("order_type:", order.order_type)
    print("=======================================")

    return order
