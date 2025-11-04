import time
import hmac
import hashlib
import base64
import json
import requests
import config
from db_connect import RequestLogApiServer
import uuid
from datetime import datetime

BASE_URL = "https://api.bitget.com"
PRODUCT_TYPE = "USDT-FUTURES"
MARGIN_MODE = "isolated"
ORDER_TYPE = "market"
ENVIRONMENT = "demo"


class BitgetClient:
    def __init__(self):
        self.api_key = config.API_KEY
        self.api_secret = config.SECRET
        self.passphrase = config.PASSPHRASE
        self.logger = RequestLogApiServer()

    def _get_signature(self, timestamp, method, path, body=""):
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()

    def _validate_response(self, response_data):
        if not isinstance(response_data, dict):
            print("❌ Risposta non valida (non è un dizionario)")
            return False

        code = response_data.get("code")
        msg = response_data.get("msg")
        data = response_data.get("data")
        print("=======================================")
        print("response json: ", json.dumps(response_data, indent=2))
        print("response data: ", data)
        print("response code: ", code)
        print("response msg: ", msg)
        if code != "00000":
            print(f"❌ Errore Bitget: code={code}, msg={msg}")
            return False

        if not data:
            print("⚠️ Nessun dato restituito, ordine forse non accettato")
            return False
        print("****************************************")
        print("✅ Accepted Request:", data)
        print("****************************************")
        return True

    def _get_headers(self, method, path, body):
        timestamp = str(int(time.time() * 1000))
        sign = self._get_signature(timestamp, method, path, body)
        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": sign,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US",
            "paptrading": "1"
        }
        if ENVIRONMENT == "demo":
            headers["X-CHANNEL-API-CODE"] = "default"
        return headers

    def _post(self, path, payload):
        body = json.dumps(payload)
        headers = self._get_headers("POST", path, body)

        try:
            response = requests.post(BASE_URL + path, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            response_data = response.json()

            # Costruisci i blocchi di log
            request_log = {
                "timestamp": str(datetime.now()),
                "endpoint": path,
                "body": body,
                "headers": json.dumps(headers),
                "payload": json.dumps(payload)
            }

            response_log = {
                "response_status": str(response.status_code),
                "response_body": response.text,
                "response_json": json.dumps(response_data),
                "response_data": json.dumps(response_data.get("data")),
                "response_code": response_data.get("code"),
                "response_msg": response_data.get("msg")
            }

            # Inserisci nel database tramite RequestLogApiServer
            self.logger.insert_request(request_log, response_log)

            self._validate_response(response_data)
            return response_data

        except requests.exceptions.RequestException as e:
            error_log = {
                "response_status": "RequestException",
                "response_body": str(e),
                "response_json": "",
                "response_data": "",
                "response_code": "ERROR",
                "response_msg": str(e)
            }

            request_log = {
                "timestamp": str(datetime.now()),
                "endpoint": path,
                "body": body,
                "headers": json.dumps(headers),
                "payload": json.dumps(payload)
            }

            self.logger.insert_request(request_log, error_log)
            return {"error": "RequestException", "message": str(e)}

        except Exception as e:
            error_log = {
                "response_status": "UnexpectedError",
                "response_body": str(e),
                "response_json": "",
                "response_data": "",
                "response_code": "ERROR",
                "response_msg": str(e)
            }

            request_log = {
                "timestamp": str(datetime.now()),
                "endpoint": path,
                "body": body,
                "headers": json.dumps(headers),
                "payload": json.dumps(payload)
            }

            self.logger.insert_request(request_log, error_log)
            return {"error": "UnexpectedError", "message": str(e)}

    def set_leverage(self, symbol, margin_coin, leverage, side):
        path = "/api/v2/mix/account/set-leverage"
        payload = {
            "symbol": symbol,
            "marginCoin": margin_coin,
            "leverage": str(leverage),
            "holdSide": "long" if side == "buy" else "short",
            "productType": PRODUCT_TYPE
        }

        return self._post(path, payload)

    def place_order(self, symbol, margin_coin, quantity, side, trade_side):
        path = "/api/v2/mix/order/place-order"
        payload = {
            "symbol": symbol,
            "productType": PRODUCT_TYPE,
            "marginMode": MARGIN_MODE,
            "marginCoin": margin_coin,
            "size": quantity,
            "side": side,
            "tradeside": trade_side,
            "orderType": ORDER_TYPE,
            "force": "gtc"
        }
        return self._post(path, payload)

    def place_tp_sl(self, symbol, margin_coin, quantity, side, trigger_price, plan_type):
        path = "/api/v2/mix/order/place-tpsl-order"
        payload = {
            "symbol": symbol,
            "productType": PRODUCT_TYPE,
            "marginCoin": margin_coin,
            "planType": plan_type,
            "triggerPrice": trigger_price,
            "holdSide": "long" if side == "buy" else "short",
            "size": quantity
        }
        return self._post(path, payload)

    def close_all_positions(self, symbol):
        # 1. Recupera tutte le posizioni aperte
        path = "/api/v2/mix/order/close-positions"
        payload = {
            "symbol": symbol,
            "productType": PRODUCT_TYPE
        }
        response = self._post(path, payload)

        if not response or "data" not in response:
            print("❌ Nessuna posizione trovata o errore nella richiesta")
            return

        positions = response["data"]
        if not positions:
            print("✅ Nessuna posizione aperta da chiudere")
            return




""" 
    def _post(self, path, payload):
        try:

            body = json.dumps(payload)
            headers = self._get_headers("POST", path, body)
            print("=======================================")
            print("base: ", BASE_URL)
            print("path: ", path)
            print("body: ", body)
            print("headers: ", headers)
            print("payload: ", payload)
            print("=======================================")
            response = requests.post(BASE_URL + path, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            print("response status:", response.status_code)
            print("response body:", json.dumps(response_data, indent=2))
            self.logger.insert_request(json.dumps(payload), json.dumps(response_data))
            # ✅ Valida la risposta
            self._validate_response(response_data)
            print("=======================================")
        except requests.exceptions.RequestException as e:
            return {"error": "RequestException", "message": str(e)}
        except Exception as e:
            return {"error": "UnexpectedError", "message": str(e)}"""
