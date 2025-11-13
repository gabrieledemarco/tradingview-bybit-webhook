# app.py
import json
import uuid
import math
from flask import Flask, request, jsonify
from utils import parse_signal_string
from bitget_client import BitgetClient
from db_module import DatabaseService
from Order import Order, process_order_request
import os

app = Flask(__name__)
client = BitgetClient()
db = DatabaseService()


@app.route("/order", methods=["POST"])
def handle_order():
    """Gestisce una nuova richiesta di ordine (OPEN o CLOSE)."""
    order = process_order_request(request)
    signal_id = str(uuid.uuid4())

  
    print("***************************")
    print("richiesta ricevuta: ", request)
    try:
        data = request.get_json(force=False, silent=False)
        print("richiesta ricevuta:", json.dumps(data, indent=2))
    except Exception as e:
        print(f"❌ Errore nel parsing JSON: {e}")
        print("Corpo grezzo:", request.data.decode('utf-8', errors='ignore'))

    # ✅ Salva richiesta in ingresso nel DB
    request_id = db.log_incoming_request(
        signal_id=signal_id,
        request_text=request.get_json(),
        response_text="null",
    )

    if order.order_type == "OPEN":
        result_json = place_order(order, signal_id)
    elif order.order_type == "CLOSE":
        client.close_all_positions(symbol=order.ticker.replace(".P", ""))
        result_json = {"status": "closed", "signal_id": signal_id}
    else:
        return jsonify({"error": "Tipo di ordine non riconosciuto"}), 400

    # ✅ Aggiorna il record request_log con la risposta
    db.update_request_response(request_id, json.dumps(result_json))

    return jsonify(result_json)

@app.route("/ping", methods=["GET"])
def ping():
    """Verifica lo stato del server e restituisce l'ultimo signal_id nel DB."""
    result = db.get_last_request_info()

    if not result:
        return jsonify({
            "status": "ok",
            "message": "Nessuna richiesta trovata in request_log"
        }), 200

    return jsonify({
        "status": "ok",
        "signal_id": result["signal_id"],
        "received_at": result["request_time"].strftime("%Y-%m-%d %H:%M:%S")
    }), 200

def place_order(order: Order, signal_id: str):
    """
    Esegue tutte le chiamate Bitget e le logga con lo stesso signal_id.
    Supporta TP multipli con qty_distribution oppure TP singolo.
    """
    symbol = order.ticker.replace(".P", "")
    margin_coin = "USDT"
    side = order.action
    trade_side = order.order_type.lower()
    leverage = "20"

    msg = parse_signal_string(order.message)
    qty = abs(order.size)

    take_profit_orders = {}
    stop_loss_order = None

    # -----------------------------
    # TP multipli con qty_distribution
    # -----------------------------
    if "qty_distribution" in msg and all(k in msg for k in ["tp1", "tp2", "tp3", "stop_loss"]):
        tp1_price, tp2_price, tp3_price, sl_price = msg["tp1"], msg["tp2"], msg["tp3"], msg["stop_loss"]
        tp1_qty = max(1, round(msg["qty_distribution"]["TP1"] / 100 * qty))
        tp2_qty = max(1, round(msg["qty_distribution"]["TP2"] / 100 * qty))
        tp3_qty = max(1, round(msg["qty_distribution"]["TP3"] / 100 * qty))

        take_profit_orders = {
            "tp1": client.place_tp_sl(symbol, margin_coin, str(tp1_qty), side, tp1_price, "profit_plan", signal_id),
            "tp2": client.place_tp_sl(symbol, margin_coin, str(tp2_qty), side, tp2_price, "profit_plan", signal_id),
            "tp3": client.place_tp_sl(symbol, margin_coin, str(tp3_qty), side, tp3_price, "profit_plan", signal_id)
        }
        stop_loss_order = client.place_tp_sl(symbol, margin_coin, str(qty), side, sl_price, "loss_plan", signal_id)

    # -----------------------------
    # TP singolo
    # -----------------------------
    elif "tp" in msg and "stop_loss" in msg:
        tp_price = msg["tp"]
        sl_price = msg["stop_loss"]

        take_profit_orders = {
            "tp": client.place_tp_sl(symbol, margin_coin, str(qty), side, tp_price, "profit_plan", signal_id)
        }
        stop_loss_order = client.place_tp_sl(symbol, margin_coin, str(qty), side, sl_price, "loss_plan", signal_id)

    else:
        # Messaggio non valido
        raise ValueError("Il messaggio del segnale non contiene TP/SL validi")

    # -----------------------------
    # Set leva e piazza ordine principale
    # -----------------------------
    leverage_result = client.set_leverage(symbol, margin_coin, leverage, side, signal_id)
    order_result = client.place_order(symbol, margin_coin, str(qty), side, trade_side, signal_id)

    results = {
        "leverage": leverage_result,
        "order": order_result,
        "takeProfit": take_profit_orders,
        "stopLoss": stop_loss_order
    }

    return results




if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
