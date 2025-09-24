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
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.pending_transactions.copy(),
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

    # Tamper a block
    def tamper_block(self, index: int, new_sender: str, new_recipient: str, new_amount: float):
        if 0 < index <= len(self.chain):  # don’t allow genesis
            block = self.chain[index - 1]
            if block["transactions"]:
                block["transactions"][0] = {
                    "sender": new_sender,
                    "recipient": new_recipient,
                    "amount": new_amount,
                }
            return True
        return False

    # Recompute hash after tampering
    def recompute_hash(self, index: int):
        if 0 < index <= len(self.chain):
            block = self.chain[index - 1]
            block["hash"] = self.hash(block)
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
st.set_page_config(page_title="Tamper Playground — Blockchain Demo", layout="wide")

# Reset blockchain if class was updated
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()

bc: Blockchain = st.session_state.blockchain

st.title("🔗 Blockchain Tamper Playground")

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

# --- Tamper Block ---
st.header("⚠️ Tamper with a Block")
tamper_index = st.number_input("Select Block to Tamper (except Genesis)", min_value=2, max_value=len(bc.chain), step=1)
new_sender = st.text_input("New Sender")
new_recipient = st.text_input("New Recipient")
new_amount = st.number_input("New Amount", min_value=0.0, step=0.01)
colA, colB = st.columns(2)

if colA.button("💥 Tamper Only"):
    if bc.tamper_block(tamper_index, new_sender, new_recipient, new_amount):
        st.error(f"Tampered Block {tamper_index}! (Hash NOT updated)")
    else:
        st.warning("Invalid block selected.")

if colB.button("♻️ Tamper & Recompute Hash"):
    if bc.tamper_block(tamper_index, new_sender, new_recipient, new_amount):
        bc.recompute_hash(tamper_index)
        st.error(f"Block {tamper_index} tampered & hash recomputed. Chain may still break!")
    else:
        st.warning("Invalid block selected.")

# --- Explorer ---
st.header("🔎 Blockchain Explorer")
for block in reversed(bc.chain):
    with st.expander(f"Block {block['index']}"):
        st.write("Previous Hash:", block["previous_hash"])
        st.write("Hash:", block["hash"])
        st.json(block["transactions"])
