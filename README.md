# OpenNet Blockchain Node

Manual setup for OpenNet PoV blockchain.

## 🛠 Manual Setup (on each validator droplet)

```bash
apt update && apt install -y git docker.io docker-compose python3-pip
pip3 install flask requests ecdsa cryptography

git clone https://github.com/YOUR_USERNAME/opennet.git
cd opennet

# Create .env file
cat > .env <<EOF
NODE_ID=nodeX
NODE_ROLE=account
VALIDATORS=node1,node2,node3
PEERS=http://159.203.71.7:8000,http://167.172.244.82:8000,http://174.138.94.199:8000
EOF

docker compose up -d --build
```

## 🧪 Wallet CLI

```bash
python opennet_node_service.py gen-wallet
python opennet_node_service.py sign-tx ...
python opennet_node_service.py send-tx ...
```
