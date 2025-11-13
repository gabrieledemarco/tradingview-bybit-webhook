import json
import re


def extract_signals_from_text(text):
    # Trova tutti i blocchi LONG o SHORT SIGNAL
    signal_blocks = re.findall(r"(LONG|SHORT) SIGNAL \|.*?Qty % → TP1: \d+% \| TP2: \d+% \| TP3: \d+%", text)

    # Trova tutti i blocchi completi
    full_blocks = re.findall(
        r"(LONG|SHORT) SIGNAL \| Entry: ([\d.]+) \| Stop Loss: ([\d.]+) \| TP1: ([\d.]+) \| TP2: ([\d.]+) \| TP3: (["
        r"\d.]+) \| Size: ([\-\d.]+) \| Qty % → TP1: (\d+)% \| TP2: (\d+)% \| TP3: (\d+)%",
        text
    )

    # Trova parametri generali (una sola volta)
    symbol = re.search(r"Segnale su (\w+)", text)
    timestamp = re.search(r"Ora: ([\d\-T:Z]+)", text)
    close_price = re.search(r"Prezzo chiusura: ([\d.]+)", text)
    action = re.search(r"Azione: (\w+)", text)

    results = []
    for block in full_blocks:
        direction, entry, sl, tp1, tp2, tp3, size, tp1_qty, tp2_qty, tp3_qty = block
        results.append({
            "symbol": symbol.group(1) if symbol else None,
            "timestamp": timestamp.group(1) if timestamp else None,
            "close_price": close_price.group(1) if close_price else None,
            "action": action.group(1) if action else None,
            "direction": direction,
            "entry": entry,
            "stop_loss": sl,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "size": size,
            "tp1_qty": tp1_qty,
            "tp2_qty": tp2_qty,
            "tp3_qty": tp3_qty
        })

    return results



def estrai_commento(testo):
    # Cerca la riga che inizia con "Commento:"
    match = re.search(r"Commento:\s*(.*)", testo)
    if match:
        commento = match.group(1).strip()
        return commento
    return None

def parse_order_text(text):
    result = {}

    # Pattern per ciascun campo
    patterns = {
        "ticker": r"Segnale su (.+)",
        "time": r"Ora:\s*(.+)",
        "close_price": r"Prezzo chiusura:\s*(.+)",
        "action": r"Azione:\s*(.+)",
        "comment": r"Commento:\s*(.+)",
        "trade_id": r"id trade\s+(.+)",
        "size": r"size:\s+(.+)",
        "message": r"Message:\s+(.+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            result[key] = match.group(1).strip()

    return result


def parse_signal_string(text: str) -> dict:
    """
    Parsifica un messaggio di alert Pine Script.
    Supporta:
    - TP singolo o multipli
    - SL come "SL" o "Stop Loss"
    - Entry
    - Size
    - Percentuali TP opzionali
    """
    result = {}

    text_upper = text.upper()

    # Tipo di segnale (OPEN/CLOSE) e direzione (LONG/SHORT)
    signal_match = re.search(r"(OPEN|CLOSE)\s+(LONG|SHORT)", text_upper)
    if signal_match:
        result["signal_type"] = signal_match.group(1)
        result["direction"] = signal_match.group(2)

    # Entry
    entry_match = re.search(r"Entry:\s*([\d.]+)", text)
    if entry_match:
        result["entry"] = float(entry_match.group(1))

    # Stop Loss (SL o Stop Loss)
    sl_match = re.search(r"(Stop Loss|SL):\s*([\d.]+)", text, re.IGNORECASE)
    if sl_match:
        result["stop_loss"] = float(sl_match.group(2))

    # Take Profits multipli (TP1, TP2, TP3)
    tp_multi_matches = re.findall(r"TP(\d):\s*([\d.]+)", text, re.IGNORECASE)
    if tp_multi_matches:
        # TP multipli
        for tp_idx, tp_val in tp_multi_matches:
            result[f"tp{tp_idx}"] = float(tp_val)
        # Percentuali TP (qty_distribution)
        qty_matches = re.findall(r"TP(\d):\s*(\d+)%", text, re.IGNORECASE)
        if qty_matches:
            result["qty_distribution"] = {f"TP{tp}": int(percent) for tp, percent in qty_matches}
    else:
        # Se non ci sono TP1/2/3, cerchiamo TP singolo
        tp_single_match = re.search(r"TP:\s*([\d.]+)", text, re.IGNORECASE)
        if tp_single_match:
            result["tp"] = float(tp_single_match.group(1))

    # Size
    size_match = re.search(r"Size:\s*([\d.]+)", text, re.IGNORECASE)
    if size_match:
        result["size"] = float(size_match.group(1))

    # Debug
    print("Parsed Results:", json.dumps(result, indent=2))
    return result
