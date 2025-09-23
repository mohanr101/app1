import streamlit as st
import hashlib
import json
import time
import uuid
from typing import List, Dict, Any

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def __init__(self, difficulty: int = 3):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.difficulty = difficulty
        # Genesis block
        self.new_block(proof=100, previous_hash="1")

    def new_block(self, proof: int, previous_hash: str = None) -> Dict[str, Any]:
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.pending_transactions.copy(),
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: float):
        tx = {"sender": sender, "recipient": recipient, "amount": amount}
        self.pending_transactions.append(tx)
        return self.last_block["index"] + 1

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    def valid_proof(self, last_proof: int, proof: int) -> bool:
        guess = f"{last_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == "0" * self.difficulty

    def get_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block["transactions"]:
                if tx["recipient"] == address:
                    balance += tx["amount"]
                if tx["sender"] == address:
                    balance -= tx["amount"]
        for tx in self.pending_transactions:
            if tx["recipient"] == address:
                balance += tx["amount"]
            if tx["sender"] == address:
                balance -= tx["amount"]
        return balance


# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="Mini Blockchain Wallet", layout="wide")

# Persist blockchain and wallet ID
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain(difficulty=3)
if "wallet" not in st.session_state:
    st.session_state.wallet = str(uuid.uuid4()).replace("-", "")

bc: Blockchain = st.session_state.blockchain
wallet: str = st.session_state.wallet

st.title("💳 Mini Blockchain Wallet (FinTech Demo)")

# Stats
col1, col2, col3 = st.columns(3)
col1.metric("Blockchain Length", len(bc.chain))
col2.metric("Pending Tx", len(bc.pending_transactions))
col3.metric("Your Balance", f"{bc.get_balance(wallet):.2f} tokens")

st.markdown(f"**Wallet ID:** `{wallet}`")

# --- Add Transaction ---
st.header("➕ Send Tokens")
with st.form("tx_form", clear_on_submit=True):
    recipient = st.text_input("Recipient Address")
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Add Transaction")
    if submitted:
        if recipient and amount > 0:
            bc.new_transaction(sender=wallet, recipient=recipient, amount=amount)
            st.success("✅ Transaction added to pending pool")
        else:
            st.error("⚠️ Enter recipient and valid amount")

# --- Mining ---
st.header("⛏️ Mine Block")
if st.button("Mine"):
    last_proof = bc.last_block["proof"]
    with st.spinner("Mining in progress..."):
        proof = bc.proof_of_work(last_proof)
        # Reward
        bc.new_transaction(sender="0", recipient=wallet, amount=1)
        block = bc.new_block(proof)
    st.success(f"🎉 Block #{block['index']} mined!")
    st.json(block)

# --- Blockchain Explorer ---
st.header("🔎 Blockchain Explorer")
for block in reversed(bc.chain[-5:]):  # show last 5 blocks
    with st.expander(f"Block {block['index']}"):
        st.write("Proof:", block["proof"])
        st.write("Previous Hash:", block["previous_hash"])
        st.json(block["transactions"])
