"""Ponte locale per verificare saldi tramite API pubbliche indicizzate.

Avvio:
    python bitcoin_api_bridge.py

Il servizio ascolta solo su 127.0.0.1:18766. La WIF viene elaborata localmente;
agli explorer vengono inviati esclusivamente gli indirizzi Bitcoin pubblici.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from bitcoin_crypto import derive_addresses


HOST = "127.0.0.1"
PORT = 18766
TIMEOUT_SECONDS = 15
USER_AGENT = "BitcoinEducationalBalanceChecker/1.0"

PROVIDERS = (
    {
        "name": "mempool.space",
        "address_url": "https://mempool.space/api/address/{address}",
        "status_url": "https://mempool.space/api/blocks/tip/height",
    },
    {
        "name": "Blockstream",
        "address_url": "https://blockstream.info/api/address/{address}",
        "status_url": "https://blockstream.info/api/blocks/tip/height",
    },
)


def request_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json, text/plain",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=TIMEOUT_SECONDS,
            context=ssl.create_default_context(),
        ) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise RuntimeError("Limite richieste raggiunto. Attendi e riprova.") from error
        raise RuntimeError(f"API HTTP {error.code}.") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Connessione API non riuscita: {error.reason}") from error


def request_json(url: str) -> dict[str, Any]:
    try:
        return json.loads(request_text(url))
    except json.JSONDecodeError as error:
        raise RuntimeError("L'API ha restituito una risposta non valida.") from error


def balance_from_address_data(data: dict[str, Any]) -> tuple[int, int]:
    chain_stats = data.get("chain_stats", {})
    mempool_stats = data.get("mempool_stats", {})
    funded = int(chain_stats.get("funded_txo_sum", 0)) + int(
        mempool_stats.get("funded_txo_sum", 0)
    )
    spent = int(chain_stats.get("spent_txo_sum", 0)) + int(
        mempool_stats.get("spent_txo_sum", 0)
    )
    transactions = int(chain_stats.get("tx_count", 0)) + int(
        mempool_stats.get("tx_count", 0)
    )
    return funded - spent, transactions


def check_provider(provider: dict[str, str], addresses: list[str]) -> dict[str, Any]:
    total_balance = 0
    total_transactions = 0
    details = []

    for address in addresses:
        data = request_json(provider["address_url"].format(address=address))
        balance, transactions = balance_from_address_data(data)
        total_balance += balance
        total_transactions += transactions
        details.append(
            {
                "address": address,
                "balance_sats": balance,
                "tx_count": transactions,
            }
        )

    return {
        "provider": provider["name"],
        "balance_sats": total_balance,
        "tx_count": total_transactions,
        "addresses": addresses,
        "details": details,
    }


def check_balance(wif: str) -> dict[str, Any]:
    addresses = derive_addresses(wif)
    errors = []

    for provider in PROVIDERS:
        try:
            return check_provider(provider, addresses)
        except Exception as error:
            errors.append(f"{provider['name']}: {error}")

    raise RuntimeError(" | ".join(errors))


def check_status() -> dict[str, Any]:
    errors = []

    for provider in PROVIDERS:
        try:
            height = int(request_text(provider["status_url"]).strip())
            return {
                "provider": provider["name"],
                "block_height": height,
            }
        except Exception as error:
            errors.append(f"{provider['name']}: {error}")

    raise RuntimeError(" | ".join(errors))


class ApiBridgeHandler(BaseHTTPRequestHandler):
    server_version = "BitcoinApiLocalBridge/1.0"

    def log_message(self, format_string: str, *arguments: Any) -> None:
        return

    def end_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin in (None, "null", "file://"):
            self.send_header("Access-Control-Allow-Origin", origin or "null")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(200, {"service": "online"})
            return

        if self.path == "/status":
            try:
                self.send_json(200, check_status())
            except Exception as error:
                self.send_json(503, {"error": str(error)})
            return

        self.send_json(404, {"error": "Endpoint non trovato."})

    def do_POST(self) -> None:
        if self.path != "/balance":
            self.send_json(404, {"error": "Endpoint non trovato."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 1 or content_length > 4096:
                raise ValueError("Richiesta non valida.")

            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            wif = payload.get("wif")
            if not isinstance(wif, str):
                raise ValueError("WIF mancante.")

            self.send_json(200, check_balance(wif))
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
        except Exception as error:
            self.send_json(503, {"error": str(error)})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ApiBridgeHandler)
    print(f"Servizio API locale attivo su http://{HOST}:{PORT}")
    print("La WIF resta locale; online vengono inviati solo gli indirizzi pubblici.")
    print("Lascia aperta questa finestra mentre usi bitcoin-api.html.")
    print("Premi Ctrl+C per arrestare il servizio.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
