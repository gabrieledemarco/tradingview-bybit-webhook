# 📈 TradingView Bybit Webhook → Bitget Bot

Questo progetto è un sistema di automazione che riceve segnali da TradingView tramite webhook e li trasforma in ordini di trading su Bitget. È pensato per gestire strategie multi-target con stop loss, take profit e tracciamento delle richieste.

---

## 🚀 Funzionalità principali

- ✅ Ricezione webhook da TradingView
- 📤 Invio ordini a Bitget tramite API REST
- 🧠 Parsing intelligente dei segnali con distribuzione quantità su TP1, TP2, TP3
- 🛑 Gestione automatica di stop loss e take profit
- 🗃️ Logging dettagliato delle richieste in entrata (`request_log`) e in uscita (`api_requests`)
- 🔗 Collegamento tra segnali e chiamate API tramite `signal_id`

---

## 🧱 Struttura del progetto

| File / Modulo         | Descrizione |
|-----------------------|-------------|
| `app.py`              | Server Flask che riceve i webhook e gestisce il flusso |
| `Order.py`            | Classe per la costruzione e gestione degli ordini |
| `bitget_client.py`    | Wrapper per le API Bitget |
| `db_connect.py`       | Connessione al database MySQL |
| `utils.py`            | Funzioni di supporto (es. parsing, validazione) |
| `RequestLogDAO.py`    | DAO per la tabella `request_log` |
| `ApiRequestDAO.py`    | DAO per la tabella `api_requests` |

---

## 🛠️ Requisiti

- Python 3.10+
- MySQL Connector
- Flask

Installa le dipendenze:
```bash
pip install -r requirements.txt

# TradingView → Bybit Webhook Bot

Questo progetto consente di ricevere alert da TradingView via webhook e inviare ordini all’exchange Bybit mediante API.
Lo scopo è automatizzare strategie che generano segnali su TradingView e li traducono in operazioni reali su Bybit.

---# TradingView → Bybit Webhook Bot

Questo progetto consente di ricevere alert da TradingView via webhook e inviare ordini all’exchange Bybit mediante API.
Lo scopo è automatizzare strategie che generano segnali su TradingView e li traducono in operazioni reali su Bybit.

---

## Prerequisiti

* Account Bybit con **API key** e **Secret key** con permessi di trading.
* Server o VPS con endpoint pubblico (es. `/webhook`) accessibile via HTTPS.
* Account TradingView con piano che supporta **alert webhook**.
* Python 3.8+ installato e file `requirements.txt` configurato.

---

## Installazione

```bash
git clone https://github.com/gabrieledemarco/tradingview-bybit-webhook.git
cd tradingview-bybit-webhook
pip install -r requirements.txt
```

Configura il file `.env` o `config.py` con le tue credenziali Bybit:

```text
API_KEY = "la_tua_api_key"
API_SECRET = "la_tua_api_secret"
IS_TESTNET = True
ENDPOINT = "https://api-bitget.com"
```

Avvia il bot:

```bash
python main.py
```

---

## ⚙️ Configurazione di TradingView

### 1. Creazione della strategia

All’interno del tuo script Pine Script (versione 5 consigliata), devi generare un **messaggio di alert** che rispetti un formato predefinito.

Esempio LONG con tre Take Profit e uno Stop Loss:

```pinescript
//@version=5
strategy("Bybit Auto Trader", overlay=true)

// Esempio variabili
sl = close * 0.98
tp1 = close * 1.02
tp2 = close * 1.04
tp3 = close * 1.06
qty = 1
tp1_qty = 30
tp2_qty = 30
tp3_qty = 40

// Messaggio alert formattato
alert_msg_long = str.format(
    "🟢 LONG SIGNAL\nEntry: {0}\nStop Loss: {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSize: {5}\n\nQty % → TP1: {6}% | TP2: {7}% | TP3: {8}%",
    str.tostring(close, format.mintick),
    str.tostring(sl, format.mintick),
    str.tostring(tp1, format.mintick),
    str.tostring(tp2, format.mintick),
    str.tostring(tp3, format.mintick),
    str.tostring(qty),
    str.tostring(tp1_qty),
    str.tostring(tp2_qty),
    str.tostring(tp3_qty)
)

// Entrata long
strategy.entry("Long ", strategy.long, comment="Bullish Rejection Entry", qty=qty, alert_message=alert_msg_long)

// Uscite parziali
strategy.exit("Long TP1", from_entry="Long ", qty_percent=tp1_qty, limit=tp1, stop=sl, alert_message="CLOSE LONG SIGNAL")
strategy.exit("Long TP2", from_entry="Long ", qty_percent=tp2_qty, limit=tp2, stop=sl, alert_message="CLOSE LONG SIGNAL")
strategy.exit("Long TP3", from_entry="Long ", qty_percent=tp3_qty, limit=tp3, stop=sl, alert_message="CLOSE LONG SIGNAL")
```

> Il messaggio generato (`alert_message`) viene inviato al webhook Bybit e deve essere interpretato dal bot Python.

### 2. Creazione dell’alert su TradingView

1. Clicca sull’icona **⏰ Alert** o premi `Alt + A`.
2. In **Condizione**, scegli la tua strategia.
3. In **Webhook URL**, inserisci l’indirizzo pubblico del tuo server, es.: `https://tuo-dominio.com/webhook`
4. In **Messaggio**, incolla:

```json
{
  "symbol":"{{ticker}}",
  "side":"{{strategy.order.action}}",
  "price":{{close}},
  "message":"{{strategy.order.alert_message}}"
}
```

5. In **Ripeti alert**, seleziona *Ogni barra chiusa* o *Ogni segnale*.
6. Clicca su **Crea**.

### 3. Verifica del funzionamento

* Quando il segnale LONG scatta, TradingView invierà il messaggio al tuo endpoint.
* Il bot riceverà il payload e, leggendo i valori di `Entry`, `Stop Loss`, `TP1–TP3`, e `Size`, aprirà la posizione su Bybit e gestirà le uscite parziali.
* I segnali “CLOSE LONG SIGNAL” chiudono parzialmente la posizione secondo la strategia.

---

## ✅ Checklist finale

| Verifica | Descrizione                                                 |
| -------- | ----------------------------------------------------------- |
| 🔑       | Le API Key Bybit sono corrette e abilitate al trading       |
| 🌐       | L’endpoint webhook è pubblico e riceve POST JSON            |
| 🧩       | Il messaggio `alert_message` rispetta il tracciato definito |
| 🧪       | Test eseguito prima in **testnet**                          |
| 📜       | Log attivi per monitorare i messaggi ricevuti               |

---

## ⚠️ Disclaimer

Questo software è fornito **“as is”** e non garantisce profitti.
Usalo esclusivamente in ambiente di test prima di operare con capitale reale.

---

## 📄 Licenza

MIT License — consulta il file `LICENSE`.
