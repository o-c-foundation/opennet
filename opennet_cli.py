# opennet_cli.py
import json
import time
import requests
import hashlib
from ecdsa import SigningKey, SECP256k1

MENU = '''
10. View Latest Chain

 ░▒▓██████▓▒░░▒▓███████▓▒░░▒▓████████▓▒░▒▓███████▓▒░░▒▓███████▓▒░░▒▓████████▓▒░▒▓████████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓██████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓██████▓▒░    ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
 ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░  ░▒▓█▓▒░     

============================================================================
1. Generate Wallet
2. Sign Transaction
3. Send Transaction
4. Faucet Request
5. Deploy Contract
6. Call Contract
7. Check Balance
8. Network Status
9. Transaction Lookup
10. View Latest Chain
0. Exit
'''

def gen_wallet():
    key = SigningKey.generate(curve=SECP256k1)
    pubkey = key.get_verifying_key().to_string().hex()
    address = "open" + hashlib.sha256(pubkey.encode()).hexdigest()[:36]
    print("\n[+] Wallet Generated")
    print("Address: ", address)
    print("Public Key: ", pubkey)
    print("Private Key: ", key.to_string().hex())

def sign_tx():
    priv = input("Private Key: ")
    sender = input("Sender Address: ")
    receiver = input("Receiver Address: ")
    amount = float(input("Amount: "))
    key = SigningKey.from_string(bytes.fromhex(priv), curve=SECP256k1)
    pubkey = key.get_verifying_key().to_string().hex()
    timestamp = time.time()
    message = f"{sender}:{receiver}:{amount}:{timestamp}".encode()
    signature = key.sign(message).hex()
    tx = {
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "timestamp": timestamp,
        "signature": signature,
        "pubkey": pubkey
    }
    print("\n[+] Signed Transaction:")
    print(json.dumps(tx, indent=2))
    return tx

def send_tx():
    tx = sign_tx()
    node = input("Node URL: ")
    res = requests.post(f"{node}/tx", json=tx)
    print("\n[+] Node Response:", res.status_code, res.json())

def faucet():
    priv = input("Treasury Private Key: ")
    receiver = input("Receiver Address: ")
    amount = float(input("Amount: "))
    key = SigningKey.from_string(bytes.fromhex(priv), curve=SECP256k1)
    pubkey = key.get_verifying_key().to_string().hex()
    sender = "open_treasury_001"
    timestamp = time.time()
    message = f"{sender}:{receiver}:{amount}:{timestamp}".encode()
    signature = key.sign(message).hex()
    tx = {
        "address": receiver,
        "amount": amount,
        "timestamp": timestamp,
        "signature": signature,
        "pubkey": pubkey
    }
    node = input("Node URL: ")
    res = requests.post(f"{node}/faucet", json=tx)
    print("\n[+] Faucet Response:", res.status_code, res.json())

def deploy_contract():
    priv = input("Deployer Private Key: ")
    creator = input("Deployer Address: ")
    code = input("Contract Code (e.g. return input['x'] * 2): ")
    key = SigningKey.from_string(bytes.fromhex(priv), curve=SECP256k1)
    pubkey = key.get_verifying_key().to_string().hex()
    timestamp = time.time()
    message = f"{creator}::{5.0}:{timestamp}".encode()
    signature = key.sign(message).hex()
    payload = {
        "creator": creator,
        "code": code,
        "timestamp": timestamp,
        "signature": signature,
        "pubkey": pubkey
    }
    node = input("Node URL: ")
    res = requests.post(f"{node}/deploy_contract", json=payload)
    print("\n[+] Deploy Response:", res.status_code, res.json())

def call_contract():
    contract = input("Contract ID: ")
    key = input("Input as JSON (e.g. {\"x\": 5}): ")
    node = input("Node URL: ")
    try:
        input_data = json.loads(key)
        res = requests.post(f"{node}/call_contract", json={"contract": contract, "input": input_data})
        print("\n[+] Call Response:", res.status_code, res.json())
    except Exception as e:
        print("[!] Error:", e)

def check_balance():
    address = input("Address: ")
    node = input("Node URL: ")
    res = requests.get(f"{node}/balance/{address}")
    result = res.json()
    balance = result.get("balance", 0)
    status = "🟢" if balance > 0 else "🔴"
    print(f"\n[+] Balance: {status} {balance} | {result}")

def network_status():
    node = input("Node URL: ")
    res = requests.get(f"{node}/index")
    print("\n[+] Network Status:", res.status_code, res.json())

def tx_lookup():
    address = input("Address to search: ")
    node = input("Node URL: ")
    res = requests.get(f"{node}/index")
    data = res.json().get("data", [])
    results = [tx for tx in data if tx.get("sender") == address or tx.get("receiver") == address]
    print(f"\n[+] Found {len(results)} transactions:")
    for tx in results:
        print(json.dumps(tx, indent=2))

def view_chain():
    node = input("Node URL: ")
    res = requests.get(f"{node}/chain")
    chain = res.json()
    print(f"\n[+] Latest {min(5, len(chain))} blocks:")
    for block in chain[-5:]:
        print(json.dumps(block, indent=2))

def main():
    while True:
        print(MENU)
        choice = input("Choose: ")
        if choice == "1": gen_wallet()
        elif choice == "2": sign_tx()
        elif choice == "3": send_tx()
        elif choice == "4": faucet()
        elif choice == "5": deploy_contract()
        elif choice == "6": call_contract()
        elif choice == "7": check_balance()
        elif choice == "8": network_status()
        elif choice == "9": tx_lookup()
        elif choice == "10": view_chain()
        elif choice == "0": break
        else: print("Invalid choice")
        input("\n[Enter to continue] →")

if __name__ == '__main__':
    main()
