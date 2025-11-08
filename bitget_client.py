import time
import hmac
import hashlib
import base64
import json
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from db_module import DatabaseService  # ✅ nuovo import

load_dotenv()

BASE_URL = "https://api.bitget.com"
PRODUCT_TYPE = "USDT-FUTURES"
MARGIN_MODE = "isolated"
ORDER_TYPE = "market"
ENVIRONMENT = os.getenv("ENVIRONMENT", "demo")


class BitgetClient:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("SECRET")
        self.passphrase = os.getenv("PASSPHRASE")
        self.db_service = DatabaseService()  # ✅ sostituisce RequestLogApiServer

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
        print("response json:", json.dumps(response_data, indent=2))
        print("response data:", data)
        print("response code:", code)
        print("response msg:", msg)
        if code != "00000":
            print(f"❌ Errore Bitget: code={code}, msg={msg}")
            return False

        if not data:
            print("⚠️ Nessun dato restituito, ordine forse non accettato")
            return False

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

    def _post(self, path, payload, signal_id=None):
        """Effettua una POST verso Bitget e salva log nel DB."""
        body = json.dumps(payload)
        headers = self._get_headers("POST", path, body)

        try:
            response = requests.post(BASE_URL + path, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            response_data = response.json()

            request_log = {
                "timestamp": str(datetime.now()),
                "endpoint": path,
                "body": body,
                "headers": headers,
                "payload": payload
            }

            response_log = {
                "response_status": response.status_code,
                "response_body": response.text,
                "response_json": response_data,
                "response_data": response_data.get("data"),
                "response_code": response_data.get("code"),
                "response_msg": response_data.get("msg")
            }

            # ✅ nuovo logging tramite DatabaseService
            self.db_service.log_outgoing_api(request_log, response_log, signal_id)

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
                "headers": headers,
                "payload": payload
            }

            self.db_service.log_outgoing_api(request_log, error_log, signal_id)
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
                "headers": headers,
                "payload": payload
            }

            self.db_service.log_outgoing_api(request_log, error_log, signal_id)
            return {"error": "UnexpectedError", "message": str(e)}

    # --- Metodi operativi (restano invariati tranne l'aggiunta di signal_id opzionale) ---

    def set_leverage(self, symbol, margin_coin, leverage, side, signal_id=None):
        path = "/api/v2/mix/account/set-leverage"
        payload = {
            "symbol": symbol,
            "marginCoin": margin_coin,
            "leverage": str(leverage),
            "holdSide": "long" if side == "buy" else "short",
            "productType": PRODUCT_TYPE
        }
        return self._post(path, payload, signal_id)

    def place_order(self, symbol, margin_coin, quantity, side, trade_side, signal_id=None):
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
        return self._post(path, payload, signal_id)

    def place_tp_sl(self, symbol, margin_coin, quantity, side, trigger_price, plan_type, signal_id=None):
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
        return self._post(path, payload, signal_id)

    
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
