import streamlit as st
import hashlib
import json
import time

# -----------------------
# Block Class
# -----------------------
class Block:
    def __init__(self, index, transaction, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.transaction = transaction
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transaction": self.transaction,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, {"sender": "0", "recipient": "0", "amount": 0}, "0")

    def add_block(self, transaction):
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), transaction, previous_block.hash)
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.hash != curr.calculate_hash():
                return False
            if curr.previous_hash != prev.hash:
                return False
        return True

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="Simple Blockchain Ledger", layout="wide")

if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()

bc = st.session_state.blockchain

st.title("🔗 Blockchain Ledger Demo")

# Add new transaction
st.header("➕ Add Transaction")
with st.form("tx_form", clear_on_submit=True):
    sender = st.text_input("Sender")
    recipient = st.text_input("Recipient")
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Add to Blockchain")

    if submitted:
        if sender and recipient and amount > 0:
            tx = {"sender": sender, "recipient": recipient, "amount": amount}
            block = bc.add_block(tx)
            st.success(f"✅ Block #{block.index} added with hash {block.hash[:10]}...")
        else:
            st.error("⚠️ Enter valid sender, recipient, and amount")

# Show blockchain
st.header("📜 Blockchain Explorer")
for block in reversed(bc.chain):
    with st.expander(f"Block {block.index} | Hash: {block.hash[:15]}..."):
        st.json({
            "index": block.index,
            "timestamp": block.timestamp,
            "transaction": block.transaction,
            "previous_hash": block.previous_hash,
            "hash": block.hash
        })

# Validate chain
st.header("✅ Validate Blockchain")
if bc.is_chain_valid():
    st.success("Blockchain is valid and tamper-proof ✅")
else:
    st.error("Blockchain has been tampered ❌")
