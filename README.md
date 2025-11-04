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
