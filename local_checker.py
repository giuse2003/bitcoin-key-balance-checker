import os
import sys
import json
import socket
import signal
import time
import logging
import datetime
import hashlib
import argparse

import base58
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
CHECKPOINT_FILE = "checkpoint.json"
RESULTS_FILE = "risultati.json"

keep_running = True

def handle_sigint(signum, frame):
    global keep_running
    logging.info("Rilevato segnale di arresto (Ctrl+C). Arresto programmato dopo la chiave corrente...")
    keep_running = False

signal.signal(signal.SIGINT, handle_sigint)

# --- Bech32 Address Encoding for P2WPKH ---
def bech32_polymod(values):
    generators = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    checksum = 1
    for value in values:
        top = checksum >> 25
        checksum = (((checksum & 0x1ffffff) << 5) ^ value) & 0xffffffff
        for i in range(5):
            if (top >> i) & 1:
                checksum ^= generators[i]
    return checksum

def convert_bits(data, from_bits, to_bits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1
    for value in data:
        if value < 0 or (value >> from_bits):
            return None
        acc = ((acc << from_bits) | value) & max_acc
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (to_bits - bits)) & maxv)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & maxv):
        return None
    return ret

def segwit_address(program):
    converted = convert_bits(program, 8, 5)
    data = [0] + converted
    # Expanded HRP for 'bc' is [3, 3, 0, 2, 3]
    expanded = [3, 3, 0, 2, 3] + data + [0, 0, 0, 0, 0, 0]
    polymod = bech32_polymod(expanded) ^ 1
    checksum = []
    for i in range(6):
        checksum.append((polymod >> (5 * (5 - i))) & 31)
    
    return "bc1" + "".join(BECH32_CHARSET[v] for v in (data + checksum))

# --- Address and ScriptPubKey Derivation ---
def hash160(bytes_data):
    sha = hashlib.sha256(bytes_data).digest()
    h = hashlib.new('ripemd160')
    h.update(sha)
    return h.digest()

def derive_addresses_and_scripts(private_key_int):
    # Derive compressed public key
    priv_bytes = private_key_int.to_bytes(32, byteorder='big')
    priv_key_obj = ec.derive_private_key(private_key_int, ec.SECP256K1(), default_backend())
    pub_key_obj = priv_key_obj.public_key()
    compressed_pubkey = pub_key_obj.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint
    )
    
    # Generate WIF (compressed)
    payload = b'\x80' + priv_bytes + b'\x01'
    wif = base58.b58encode_check(payload).decode('ascii')
    
    # 1. Legacy P2PKH
    pubkey_hash = hash160(compressed_pubkey)
    legacy_addr = base58.b58encode_check(b'\x00' + pubkey_hash).decode('ascii')
    legacy_script = b'\x76\xa9\x14' + pubkey_hash + b'\x88\xac'
    
    # 2. Nested SegWit P2SH-P2WPKH
    redeem_script = b'\x00\x14' + pubkey_hash
    redeem_hash = hash160(redeem_script)
    nested_addr = base58.b58encode_check(b'\x05' + redeem_hash).decode('ascii')
    nested_script = b'\xa9\x14' + redeem_hash + b'\x87'
    
    # 3. Native SegWit P2WPKH
    native_addr = segwit_address(pubkey_hash)
    native_script = b'\x00\x14' + pubkey_hash
    
    # Convert scriptPubKeys to Electrum scripthashes
    scripthash_legacy = hashlib.sha256(legacy_script).digest()[::-1].hex()
    scripthash_nested = hashlib.sha256(nested_script).digest()[::-1].hex()
    scripthash_native = hashlib.sha256(native_script).digest()[::-1].hex()
    
    return {
        "wif": wif,
        "addresses": {
            "legacy": legacy_addr,
            "nested": nested_addr,
            "native": native_addr
        },
        "scripthashes": {
            "legacy": scripthash_legacy,
            "nested": scripthash_nested,
            "native": scripthash_native
        }
    }

# --- Fulcrum TCP Socket client ---
def query_fulcrum_batch(scripthashes_dict):
    host = "127.0.0.1"
    port = 50001
    
    # We will map standard names to scripthashes
    keys = ["legacy", "nested", "native"]
    reqs = []
    
    for i, key in enumerate(keys):
        sh = scripthashes_dict[key]
        reqs.append({
            "jsonrpc": "2.0",
            "method": "blockchain.scripthash.get_balance",
            "params": [sh],
            "id": i * 2 + 1
        })
        reqs.append({
            "jsonrpc": "2.0",
            "method": "blockchain.scripthash.get_history",
            "params": [sh],
            "id": i * 2 + 2
        })
        
    sock = socket.create_connection((host, port), timeout=10)
    sock.sendall((json.dumps(reqs) + "\n").encode('utf-8'))
    
    response_data = b""
    while b"\n" not in response_data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response_data += chunk
        
    sock.close()
    
    resps = json.loads(response_data.decode('utf-8'))
    resps.sort(key=lambda r: r.get("id", 0))
    
    results = {}
    for i, key in enumerate(keys):
        balance_resp = resps[i * 2]
        history_resp = resps[i * 2 + 1]
        
        if "error" in balance_resp:
            raise Exception(f"Errore Fulcrum get_balance per {key}: {balance_resp['error']}")
        if "error" in history_resp:
            raise Exception(f"Errore Fulcrum get_history per {key}: {history_resp['error']}")
            
        balance_res = balance_resp["result"]
        history_res = history_resp["result"]
        
        results[key] = {
            "confirmed": balance_res.get("confirmed", 0),
            "unconfirmed": balance_res.get("unconfirmed", 0),
            "history_count": len(history_res) if isinstance(history_res, list) else 0
        }
        
    return results

# --- Checkpoint Management ---
def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        initial = {
            "last_completed_private_key_number": "0",
            "next_private_key_number": "1",
            "checked_keys": "0",
            "updated_at": None
        }
        write_checkpoint(initial)
        return initial
        
    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Impossibile leggere il checkpoint: {e}. Ne creo uno nuovo.")
        initial = {
            "last_completed_private_key_number": "0",
            "next_private_key_number": "1",
            "checked_keys": "0",
            "updated_at": None
        }
        write_checkpoint(initial)
        return initial

def safe_write_json(file_path, data):
    tmp_file = file_path + ".tmp"
    for attempt in range(15):
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_file, file_path)
            return
        except (PermissionError, OSError) as e:
            if attempt == 14:
                raise e
            time.sleep(0.1)

def write_checkpoint(checkpoint):
    safe_write_json(CHECKPOINT_FILE, checkpoint)

# --- Results Management ---
def save_positive_match(private_key_int, wif, addresses, fulcrum_data):
    results = []
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception as e:
            logging.error(f"Errore nella lettura del file risultati: {e}. Verrà sovrascritto.")
            
    match_entry = {
        "private_key_number": str(private_key_int),
        "wif": wif,
        "addresses": addresses,
        "results": fulcrum_data,
        "found_at": datetime.datetime.now().isoformat()
    }
    results.append(match_entry)
    
    safe_write_json(RESULTS_FILE, results)
    logging.info(f"!!! TROVATO SALDO O STORICO !!! Salvato in {RESULTS_FILE}")

# --- Main Program Execution ---
def main():
    parser = argparse.ArgumentParser(description="Verificatore Bitcoin locale sequenziale con Fulcrum.")
    parser.add_argument("--test-derivation", action="store_true", help="Esegue un test di derivazione crittografica ed esce.")
    args = parser.parse_args()
    
    if args.test_derivation:
        logging.info("Avvio del test di derivazione per la chiave numerica 1...")
        derived = derive_addresses_and_scripts(1)
        expected_legacy = "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
        expected_nested = "3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN"
        expected_native = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
        
        logging.info(f"WIF derivato: {derived['wif']}")
        logging.info(f"Legacy: {derived['addresses']['legacy']} (Atteso: {expected_legacy})")
        logging.info(f"Nested: {derived['addresses']['nested']} (Atteso: {expected_nested})")
        logging.info(f"Native: {derived['addresses']['native']} (Atteso: {expected_native})")
        
        assert derived['addresses']['legacy'] == expected_legacy, "Errore Legacy!"
        assert derived['addresses']['nested'] == expected_nested, "Errore Nested!"
        assert derived['addresses']['native'] == expected_native, "Errore Native!"
        
        logging.info("Test di derivazione superato con successo!")
        sys.exit(0)
        
    logging.info("Avvio del Verificatore Bitcoin locale...")
    checkpoint = load_checkpoint()
    
    next_key = int(checkpoint["next_private_key_number"])
    checked_keys = int(checkpoint["checked_keys"])
    
    logging.info(f"Ripresa dal checkpoint: prossima chiave da verificare = {next_key}, chiavi già verificate = {checked_keys}")
    
    while keep_running:
        # Step 1: Derive addresses and scripts for the current key
        derived = derive_addresses_and_scripts(next_key)
        wif = derived["wif"]
        addresses = derived["addresses"]
        scripthashes = derived["scripthashes"]
        
        # Step 2: Query Fulcrum (with retry loop in case it's offline or indexing)
        fulcrum_results = None
        while keep_running and fulcrum_results is None:
            try:
                fulcrum_results = query_fulcrum_batch(scripthashes)
            except Exception as e:
                # Log error and wait before retrying (check keep_running during sleep)
                logging.warning(f"Errore di connessione a Fulcrum durante l'interrogazione della chiave {next_key}: {e}. Riprovo tra 10 secondi...")
                for _ in range(10):
                    if not keep_running:
                        break
                    time.sleep(1)
        
        # If we are stopping, do not save results or advance checkpoint
        if not keep_running:
            break
            
        # Step 3: Check balances and history
        has_balance = False
        has_history = False
        total_sats = 0
        
        for key, data in fulcrum_results.items():
            total_sats += data["confirmed"] + data["unconfirmed"]
            if data["confirmed"] > 0 or data["unconfirmed"] > 0:
                has_balance = True
            if data["history_count"] > 0:
                has_history = True
                
        # Ordinary log (no WIF, only public addresses and summary)
        logging.info(
            f"Verificata chiave #{next_key} | "
            f"Legacy: {addresses['legacy']} | "
            f"Nested: {addresses['nested']} | "
            f"Native: {addresses['native']} | "
            f"Saldo: {total_sats} sat | "
            f"Storico: {any(d['history_count'] > 0 for d in fulcrum_results.values())} tx"
        )
        
        # Step 4: Classify results
        if has_balance:
            save_positive_match(next_key, wif, addresses, fulcrum_results)
            
        # Step 5: Save checkpoint and advance key
        last_completed = next_key
        next_key += 1
        checked_keys += 1
        
        checkpoint_update = {
            "last_completed_private_key_number": str(last_completed),
            "next_private_key_number": str(next_key),
            "checked_keys": str(checked_keys),
            "updated_at": datetime.datetime.now().isoformat()
        }
        write_checkpoint(checkpoint_update)
        
    logging.info("Programma arrestato ordinatamente. Stato salvato.")

if __name__ == "__main__":
    main()
