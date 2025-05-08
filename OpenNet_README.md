# OpenNet Blockchain

OpenNet is a novel, experimental blockchain protocol designed around a new consensus mechanism called **Proof of Void (PoV)**. It focuses on maximizing decentralization and simplicity by having all nodes act as validators and contribute to consensus.

---

## 🧠 Concept: Proof of Void

Unlike traditional consensus algorithms, **Proof of Void** works like this:

- Every node is a validator.
- Every transaction is recorded by all nodes **except one**, randomly selected as the `void validator`.
- This one validator “voids” the transaction set for that block, asserting non-participation in that round.
- A block is considered **valid** if all validators agree except the one intentionally ignoring it.

This enforced disagreement creates a trustless proof pattern that ensures fault tolerance and eliminates centralized mining.

---

## 🏗 Architecture Overview

- Nodes: Dockerized Python Flask servers
- Consensus: PoV (1 void validator per block)
- Ledger: In-memory with persistent JSON file storage
- Frontend: React/Vite explorer UI with node sync status, tx and block views

---

## 💻 How to Run a Node

```bash
git clone https://github.com/o-c-foundation/opennet.git
cd opennet
```

Create a `.env` file:

```bash
NODE_ID=node1
NODE_ROLE=account
VALIDATORS=node1,node2,node3
PEERS=http://node1:8000,http://node2:8000,http://node3:8000
```

Build and launch:

```bash
docker-compose up -d --build
```

---

## 🧪 CLI Usage

### Generate Wallet

```bash
python opennet_node_service.py gen-wallet
```

### Sign Transaction

```bash
python opennet_node_service.py sign-tx <priv> <sender> <receiver> <amount>
```

### Send Transaction

```bash
python opennet_node_service.py send-tx <priv> <sender> <receiver> <amount> <node_url>
```

---

## 🔁 Network Operations

### Faucet

```bash
curl -X POST http://<node>:8000/faucet -d '{"address":"<your_wallet>","amount":1000}'
```

### Mine Block

```bash
curl -X POST http://<node>:8000/mine
```

### Sync with Peers

```bash
curl -X POST http://<node>:8000/fullsync
```

---

## 📦 Explorer

Live Vite/React explorer showing:

- 🔁 Latest transactions
- 📦 Latest blocks
- 🔍 Searchable by sender/receiver
- Hosted on Vercel (or run with `npm run dev`)

Repo: [OpenNet Explorer](https://github.com/o-c-foundation/opennet-explorer)

---

## 📖 How It Works Internally

- **Transactions**: Validated, fee deducted (0.2%), and added to memory
- **Mining**: `/mine` bundles txs into a block with hash and appends to chain
- **Persistence**: All chain + balances saved to `ledger_<node>.json`
- **Node Sync**: `/fullsync` fetches from all known peers and updates state

---

## 🧱 Future Improvements

- Smart contract support
- Consensus finality enforcement
- IPFS or decentralized state replication
- Frontend wallet + dapp interface

---

## ⚠️ Disclaimer

OpenNet is experimental and not intended for real financial use.

---

## 🛠 License

MIT
