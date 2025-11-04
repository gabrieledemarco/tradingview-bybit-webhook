# app.py
import json
from utils import parse_signal_string
from flask import Flask, request, jsonify
from bitget_client import BitgetClient
from db_connect import RequestLogServer
from Order import Order, process_order_request
import math
import os

app = Flask(__name__)
client = BitgetClient()


@app.route("/order", methods=["POST"])
def handle_order():
    order = process_order_request(request)

    if order.order_type == "OPEN":
        print("OPEN ORDER")
        print("ORDER RAW DATA: ", order.raw_data)
        place_order(order)
    elif order.order_type == "CLOSE":
        print("CLOSE ORDER")
        client.close_all_positions(symbol=order.ticker.replace(".P", ""))
        print(order.raw_data)
    else:
        return jsonify({"error": "Tipo di ordine non riconosciuto"}), 400

    return order.raw_data


# @app.route("/place-order", methods=["POST"])
def place_order(order: Order):
    db = RequestLogServer()
    id_request = db.insert_request(request.json, "null")

    symbol = order.ticker.replace(".P", "")  # ["symbol"]
    margin_coin = "USDT"
    side = order.action
    trade_side = order.order_type.lower()  # data["tradeSide"]
    leverage = "20"  # data["leverage"]

    msg_parse_text = parse_signal_string(order.message)
    print("parse_text: ", msg_parse_text)

    quantity = abs(order.size)  # Mantieni come numero

    tp1_price = msg_parse_text["tp1"]
    tp2_price = msg_parse_text["tp2"]
    tp3_price = msg_parse_text["tp3"]
    sl_price = msg_parse_text["stop_loss"]

    print("qty_distribution: ", msg_parse_text["qty_distribution"])

    tp1_qty = str(round(float(msg_parse_text["qty_distribution"]["TP1"]) / 100 * quantity))
    tp2_qty = str(round(float(msg_parse_text["qty_distribution"]["TP2"]) / 100 * quantity))
    tp3_qty = str(round(float(msg_parse_text["qty_distribution"]["TP3"]) / 100 * quantity))


    print("tp1_qty: ", tp1_qty)
    print("tp2_qty: ", tp2_qty)
    print("tp3_qty: ", tp3_qty)

    leverage_result = client.set_leverage(symbol, margin_coin, leverage, side)
    order_result = client.place_order(symbol, margin_coin, str(quantity), side, trade_side)

    tp1_result = client.place_tp_sl(symbol, margin_coin, tp1_qty, side, tp1_price, "profit_plan")
    tp2_result = client.place_tp_sl(symbol, margin_coin, tp2_qty, side, tp2_price, "profit_plan")
    tp3_result = client.place_tp_sl(symbol, margin_coin, tp3_qty, side, tp3_price, "profit_plan")

    sl_result = client.place_tp_sl(symbol, margin_coin, str(math.floor(quantity)), side, sl_price, "loss_plan")

    # Salva i dati nel database
    #
    result_string = {
        "leverage": leverage_result,
        "order": order_result,
        "takeProfit": {
            "tp1": tp1_result,
            "tp2": tp2_result,
            "tp3": tp3_result
        },
        "stopLoss": sl_result
    }
    db.update_response(id_request,result_string)

    # Restituisce la risposta Json
    result_json = jsonify(result_string)
    print(result_json)

    return result_json


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

