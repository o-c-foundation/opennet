# opennet_node_service.py
import hashlib
import json
import os
import time
import requests
from flask import Flask, request, jsonify
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
from pathlib import Path
from getpass import getpass
from cryptography.fernet import Fernet

app = Flask(__name__)

NODE_ID = os.getenv("NODE_ID", "node1")
VALIDATORS = os.getenv("VALIDATORS", "node1,node2,node3").split(',')
NODE_ROLE = os.getenv("NODE_ROLE", "account")
PEERS = os.getenv("PEERS", "").split(',')
TREASURY_ADDR = "open_treasury_001"
GENESIS_SUPPLY = 500_000_000
FEE_RATE = 0.002
LEDGER_FILE = f"ledger_{NODE_ID}.json"
KEYSTORE_DIR = Path("keystore")
KEYSTORE_DIR.mkdir(exist_ok=True)

ledger_data = {
    "chain": [],
    "ledger": [],
    "balances": {TREASURY_ADDR: GENESIS_SUPPLY}
}

if os.path.exists(LEDGER_FILE):
    with open(LEDGER_FILE, 'r') as f:
        ledger_data.update(json.load(f))

def verify_signature(tx):
    try:
        pubkey_hex = tx.get("pubkey")
        sender = tx.get("sender")
        receiver = tx.get("receiver")
        amount = float(tx.get("amount"))
        timestamp = tx.get("timestamp")
        signature = tx.get("signature")

        pubkey_bytes = bytes.fromhex(pubkey_hex)
        verifying_key = VerifyingKey.from_string(pubkey_bytes, curve=SECP256k1)
        message = f"{sender}:{receiver}:{amount}:{timestamp}".encode()
        verifying_key.verify(bytes.fromhex(signature), message)

        derived_addr = "open" + hashlib.sha256(pubkey_bytes).hexdigest()[:36]
        return derived_addr == sender

    except (ValueError, BadSignatureError, TypeError):
        return False

@app.route("/tx", methods=["POST"])
def submit_transaction():
    tx = request.json
    sender = tx.get("sender")
    receiver = tx.get("receiver")
    amount = float(tx.get("amount", 0))
    timestamp = tx.get("timestamp")
    signature = tx.get("signature")
    pubkey_hex = tx.get("pubkey")

    if not all([sender, receiver, amount > 0, timestamp, signature, pubkey_hex]):
        return jsonify({"error": "Invalid transaction fields"}), 400

    if not verify_signature(tx):
        return jsonify({"error": "Invalid signature or sender mismatch"}), 403

    sender_balance = ledger_data["balances"].get(sender, 0.0)
    if sender_balance < amount:
        return jsonify({"error": "Insufficient funds"}), 403

    fee = amount * FEE_RATE
    net_amount = amount - fee

    ledger_data["balances"][sender] -= amount
    ledger_data["balances"][receiver] = ledger_data["balances"].get(receiver, 0.0) + net_amount

    eligible_validators = [v for v in VALIDATORS if v != NODE_ID]
    if eligible_validators:
        fee_share = fee / len(eligible_validators)
        for v in eligible_validators:
            ledger_data["balances"][v] = ledger_data["balances"].get(v, 0.0) + fee_share

    ledger_data["ledger"].append(tx)
    with open(LEDGER_FILE, 'w') as f:
        json.dump(ledger_data, f)

    return jsonify({"status": "accepted", "tx": tx})

@app.route("/validate_tx", methods=["POST"])
def validate_transaction():
    tx = request.json
    valid = verify_signature(tx)
    return jsonify({"valid": valid})

@app.route("/faucet", methods=["POST"])
def faucet():
    data = request.get_json()
    address = data.get("address")
    amount = float(data.get("amount", 0))
    timestamp = data.get("timestamp")
    signature = data.get("signature")
    pubkey_hex = data.get("pubkey")

    if not all([address, amount > 0, timestamp, signature, pubkey_hex]):
        return jsonify({"error": "Invalid request"}), 400

    faucet_tx = {
        "sender": TREASURY_ADDR,
        "receiver": address,
        "amount": amount,
        "timestamp": timestamp,
        "signature": signature,
        "pubkey": pubkey_hex
    }

    if not verify_signature(faucet_tx):
        return jsonify({"error": "Invalid faucet signature"}), 403

    treasury = ledger_data["balances"].get(TREASURY_ADDR, 0)
    if treasury < amount:
        return jsonify({"error": "Insufficient treasury funds"}), 403

    ledger_data["balances"][TREASURY_ADDR] -= amount
    ledger_data["balances"][address] = ledger_data["balances"].get(address, 0) + amount

    faucet_tx["type"] = "faucet"
    ledger_data["ledger"].append(faucet_tx)
    with open(LEDGER_FILE, 'w') as f:
        json.dump(ledger_data, f)
    return jsonify({"status": "faucet granted", "tx": faucet_tx})

@app.route("/mine", methods=["POST"])
def mine_block():
    if not ledger_data["ledger"]:
        return jsonify({"error": "No transactions to mine"}), 400

    block = {
        "index": len(ledger_data["chain"]),
        "timestamp": time.time(),
        "transactions": ledger_data["ledger"][:],
        "miner": NODE_ID,
    }
    block["hash"] = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
    ledger_data["chain"].append(block)
    ledger_data["ledger"] = []
    with open(LEDGER_FILE, 'w') as f:
        json.dump(ledger_data, f)

    for peer in PEERS:
        try:
            requests.post(f"{peer}/receive_block", json=block, timeout=3)
        except Exception:
            continue

    return jsonify({"status": "block mined", "block": block})

@app.route("/receive_block", methods=["POST"])
def receive_block():
    new_block = request.json
    if not new_block:
        return jsonify({"error": "No block data"}), 400

    if new_block["index"] == len(ledger_data["chain"]):
        expected_hash = hashlib.sha256(json.dumps({k: v for k, v in new_block.items() if k != "hash"}, sort_keys=True).encode()).hexdigest()
        if new_block["hash"] == expected_hash:
            ledger_data["chain"].append(new_block)
            ledger_data["ledger"] = []
            with open(LEDGER_FILE, 'w') as f:
                json.dump(ledger_data, f)
            return jsonify({"status": "block accepted"})

    return jsonify({"status": "ignored"})

@app.route("/fullsync", methods=["POST"])
def full_sync():
    longest = ledger_data["chain"]
    for peer in PEERS:
        try:
            remote_chain = requests.get(f"{peer}/chain").json()
            if len(remote_chain) > len(longest):
                longest = remote_chain
        except Exception:
            continue

    if len(longest) > len(ledger_data["chain"]):
        ledger_data["chain"] = longest
        ledger_data["ledger"] = []
        with open(LEDGER_FILE, 'w') as f:
            json.dump(ledger_data, f)

    return jsonify({"status": "synced", "length": len(ledger_data["chain"])})

@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify(ledger_data["chain"])

@app.route("/index", methods=["GET"])
def get_indexed():
    return jsonify({"role": NODE_ROLE, "data": ledger_data["ledger"][-20:]})

@app.route("/balance/<address>", methods=["GET"])
def get_balance(address):
    return jsonify({"address": address, "balance": ledger_data["balances"].get(address, 0.0)})

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "gen-wallet":
        key = SigningKey.generate(curve=SECP256k1)
        pubkey = key.get_verifying_key().to_string().hex()
        addr_hash = hashlib.sha256(pubkey.encode()).hexdigest()
        address = "open" + addr_hash[:36]
        print("Address:", address)
        print("Public Key:", pubkey)
        print("Private Key:", key.to_string().hex())
    elif len(sys.argv) > 1 and sys.argv[1] == "sign-tx":
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
    elif len(sys.argv) > 1 and sys.argv[1] == "send-tx":
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
    else:
        app.run(host="0.0.0.0", port=8000)
