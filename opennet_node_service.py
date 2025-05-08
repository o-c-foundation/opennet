# opennet_node_service.py

import hashlib
import json
import os
import random
import time
import requests
from typing import List, Dict
from flask import Flask, request, jsonify
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
from collections import defaultdict
from pathlib import Path
from getpass import getpass
from cryptography.fernet import Fernet

app = Flask(__name__)

NODE_ID = os.getenv("NODE_ID", "node1")
VALIDATORS = os.getenv("VALIDATORS", "node1,node2,node3,node4").split(',')
NODE_ROLE = os.getenv("NODE_ROLE", "account")
LEDGER_FILE = f"ledger_{NODE_ID}.json"
PEERS = os.getenv("PEERS", "").split(',')
TREASURY_ADDR = "open_treasury_001"
GENESIS_SUPPLY = 500_000_000
FEE_RATE = 0.002

ledger_data = {
    "chain": [],
    "ledger": [],
    "balances": {TREASURY_ADDR: GENESIS_SUPPLY},
}

@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify(ledger_data["chain"])

@app.route("/tx", methods=["POST"])
def submit_transaction():
    tx = request.json
    ledger_data["ledger"].append(tx)
    return jsonify({"status": "accepted"})

@app.route("/index", methods=["GET"])
def get_indexed():
    return jsonify({"role": NODE_ROLE, "data": ledger_data["ledger"]})

@app.route("/balance/<address>", methods=["GET"])
def get_balance(address):
    return jsonify({"address": address, "balance": ledger_data["balances"].get(address, 0.0)})

@app.route("/sync", methods=["POST"])
def sync_chain():
    return jsonify({"status": "sync complete", "length": len(ledger_data["chain"])})

# CLI Tool: Wallet Gen, TX Sign, TX Send, Encrypted Keystore
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "gen-wallet":
        prefix = "open"
        attempt = 0
        while True:
            key = SigningKey.generate(curve=SECP256k1)
            pubkey = key.get_verifying_key().to_string().hex()
            addr_hash = hashlib.sha256(pubkey.encode()).hexdigest()
            address = "open" + addr_hash[:36]
            attempt += 1
            if address.startswith(prefix):
                print("Address:", address)
                print("Public Key:", pubkey)
                print("Private Key:", key.to_string().hex())
                pw = getpass("Encrypt and save key (y/N)? ").lower()
                if pw == 'y':
                    password = getpass("Set password: ").encode()
                    fkey = Fernet.generate_key()
                    f = Fernet(fkey)
                    encrypted = f.encrypt(key.to_string())
                    with open(KEYSTORE_DIR / f"{address}.key", "wb") as kf:
                        kf.write(encrypted)
                    with open(KEYSTORE_DIR / f"{address}.pw", "wb") as pf:
                        pf.write(fkey)
                    print(f"Wallet saved to keystore/{address}.key")
                break

    elif len(sys.argv) > 1 and sys.argv[1] == "sign-tx":
        if len(sys.argv) != 6:
            print("Usage: sign-tx <private_key> <sender> <receiver> <amount>")
            sys.exit(1)
        try:
            priv_hex, sender, receiver, amount = sys.argv[2:6]
            key = SigningKey.from_string(bytes.fromhex(priv_hex), curve=SECP256k1)
            pubkey = key.get_verifying_key().to_string().hex()
            timestamp = time.time()
            message = f"{sender}:{receiver}:{amount}:{timestamp}".encode()
            signature = key.sign(message).hex()
            tx = {
                "sender": sender,
                "receiver": receiver,
                "amount": float(amount),
                "timestamp": timestamp,
                "signature": signature,
                "pubkey": pubkey
            }
            print(json.dumps(tx, indent=2))
        except (ValueError, IndexError) as e:
            print("Error: Invalid arguments or formatting.")
            print("Usage: sign-tx <private_key> <sender> <receiver> <amount>")
            sys.exit(1)

    elif len(sys.argv) > 1 and sys.argv[1] == "send-tx":
        if len(sys.argv) != 7:
            print("Usage: send-tx <private_key> <sender> <receiver> <amount> <node_url>")
            sys.exit(1)
        try:
            priv_hex, sender, receiver, amount, node_url = sys.argv[2:7]
            key = SigningKey.from_string(bytes.fromhex(priv_hex), curve=SECP256k1)
            pubkey = key.get_verifying_key().to_string().hex()
            timestamp = time.time()
            message = f"{sender}:{receiver}:{amount}:{timestamp}".encode()
            signature = key.sign(message).hex()
            tx = {
                "sender": sender,
                "receiver": receiver,
                "amount": float(amount),
                "timestamp": timestamp,
                "signature": signature,
                "pubkey": pubkey
            }
            res = requests.post(f"{node_url}/tx", json=tx)
            print("Node Response:", res.status_code, res.json())
        except Exception as e:
            print("Failed to send transaction:", str(e))
            sys.exit(1)

    else:
        app.run(host="0.0.0.0", port=8000)
