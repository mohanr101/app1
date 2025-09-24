import streamlit as st
import hashlib
import json
import time
from typing import List, Dict, Any

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        # Genesis block
        self.new_block(proof=100, previous_hash="1")

    def new_block(self, proof: int, previous_hash: str = None) -> Dict[str, Any]:
        # Deep copy transactions to prevent external mutation
        block_transactions = [tx.copy() for tx in self.pending_transactions]
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": block_transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.pending_transactions = []
        block["hash"] = self.hash(block)  # store hash inside block
        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: float):
        tx = {"sender": sender, "recipient": recipient, "amount": amount}
        self.pending_transactions.append(tx)
        return self.last_block["index"] + 1

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        block_copy = block.copy()
        block_copy.pop("hash", None)  # don’t include old hash
        block_string = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    # Simulate tampering without changing data
    def simulate_tamper(self, index: int):
        if 0 < index <= len(self.chain):
            return True
        return False

    # Validate chain
    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr["previous_hash"] != prev["hash"]:
                return False
            if curr["hash"] != self.hash(curr):
                return False
        return True


# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="Immutable Blockchain Demo", layout="wide")

# Initialize blockchain
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()

bc: Blockchain = st.session_state.blockchain

st.title("🔗 Immutable Blockchain Demo")

# Blockchain status
col1, col2 = st.columns(2)
col1.metric("Chain Length", len(bc.chain))
col2.metric("Is Chain Valid?", "✅ Yes" if bc.is_chain_valid() else "❌ No")

# --- Add Transaction ---
st.header("➕ Add Transaction & Mine")
with st.form("tx_form", clear_on_submit=True):
    sender = st.text_input("Sender")
    recipient = st.text_input("Recipient")
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Add & Mine Block")
    if submitted and sender and recipient and amount > 0:
        bc.new_transaction(sender, recipient, amount)
        block = bc.new_block(proof=123)
        st.success(f"✅ Block {block['index']} added to chain!")

# --- Tamper Block Simulation ---
st.header("⚠️ Simulate Tampering")
if len(bc.chain) > 1:
    tamper_index = st.number_input(
        "Select Block to 'Tamper' (Simulation Only)",
        min_value=2,
        max_value=len(bc.chain),
        step=1
    )
    if st.button("💥 Simulate Tamper"):
        if bc.simulate_tamper(tamper_index):
            st.error(
                f"Attempted to tamper Block {tamper_index}!\n"
                "✅ Transactions cannot actually be changed. Blockchain remains immutable.\n"
                "❌ But if someone tried to change it, it would break the chain."
            )
else:
    st.info("No blocks available for tampering yet (Genesis only).")

# --- Explorer ---
st.header("🔎 Blockchain Explorer")
if len(bc.chain) == 0:
    st.info("Blockchain is empty.")
else:
    for block in reversed(bc.chain):
        index = block.get("index", "N/A")
        with st.expander(f"Block {index}"):
            st.write("Previous Hash:", block.get("previous_hash", "N/A"))
            st.write("Hash:", block.get("hash", "N/A"))
            st.json(block.get("transactions", []))
