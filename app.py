import hashlib
import json
import time
import uuid
from typing import List, Dict, Any, Optional
import streamlit as st

# ------------------------
# Blockchain Class
# ------------------------
class Blockchain:
    def __init__(self, difficulty: int = 3):
        self.chain: List[Dict[str, Any]] = []
        self.current_transactions: List[Dict[str, Any]] = []
        self.difficulty = difficulty
        # Create genesis block
        self.new_block(proof=100, previous_hash="1")

    def new_block(self, proof: int, previous_hash: Optional[str] = None) -> Dict[str, Any]:
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.current_transactions.copy(),
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []  # clear pending after adding
        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: float) -> int:
        tx = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
        }
        self.current_transactions.append(tx)
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

    def compute_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block["transactions"]:
                if tx["recipient"] == address:
                    balance += tx["amount"]
                if tx["sender"] == address:
                    balance -= tx["amount"]
        for tx in self.current_transactions:
            if tx["recipient"] == address:
                balance += tx["amount"]
            if tx["sender"] == address:
                balance -= tx["amount"]
        return balance

    def all_balances(self) -> Dict[str, float]:
        users = set()
        for block in self.chain:
            for tx in block["transactions"]:
                users.add(tx["sender"])
                users.add(tx["recipient"])
        for tx in self.current_transactions:
            users.add(tx["sender"])
            users.add(tx["recipient"])
        return {user: self.compute_balance(user) for user in users if user != "0"}


# ------------------------
# Streamlit App
# ------------------------
st.set_page_config(page_title="Classroom Crypto", layout="wide")

# Persist blockchain and node id
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain(difficulty=3)
if "node_id" not in st.session_state:
    st.session_state.node_id = str(uuid.uuid4()).replace("-", "")

bc: Blockchain = st.session_state.blockchain
node_id: str = st.session_state.node_id

# Title
st.title("🎓 Classroom Cryptocurrency")
st.caption("Reward and transfer coins in a tamper-proof blockchain system")

# Layout: left = transactions & mining, right = chain & balances
col1, col2 = st.columns([1.5, 1])

# ------------------------
# Left column - Add & Mine
# ------------------------
with col1:
    st.subheader("➕ Add a Transaction")
    with st.form("tx_form", clear_on_submit=True):
        sender = st.text_input("Sender", value=node_id)
        recipient = st.text_input("Recipient")
        amount = st.number_input("Amount", min_value=0.0, step=1.0)
        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            if sender and recipient and amount > 0:
                index = bc.new_transaction(sender=sender, recipient=recipient, amount=amount)
                st.success(f"✅ Transaction will be added in Block {index} after mining")
            else:
                st.error("Please enter valid sender, recipient and amount.")

    st.markdown("---")
    st.subheader("⛏️ Mine Transactions")
    if st.button("Mine New Block", type="primary"):
        last_proof = bc.last_block["proof"]
        with st.spinner("Mining new block..."):
            proof = bc.proof_of_work(last_proof)
            # Mining reward
            bc.new_transaction(sender="0", recipient=node_id, amount=1)
            new_block = bc.new_block(proof)
        st.success(f"🎉 Block #{new_block['index']} mined successfully!")
        st.json(new_block)

# ------------------------
# Right column - Chain & Balances
# ------------------------
with col2:
    st.subheader("📦 Recent Blocks")
    for block in reversed(bc.chain[-5:]):
        with st.expander(f"Block {block['index']}"):
            st.write("⏰", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block["timestamp"])))
            st.json(block["transactions"])

    st.markdown("---")
    st.subheader("💰 Balances")
    balances = bc.all_balances()
    if balances:
        for user, bal in balances.items():
            st.write(f"**{user}** → {bal} coins")
    else:
        st.info("No balances yet. Add and mine some transactions!")

    st.markdown("---")
    st.subheader("⬇️ Export / Import Blockchain")
    chain_json = json.dumps(bc.chain, indent=2)
    st.download_button("Download Blockchain", data=chain_json, file_name="classroom_chain.json", mime="application/json")
    uploaded = st.file_uploader("Upload JSON", type=["json"])
    if uploaded:
        try:
            loaded = json.loads(uploaded.read())
            if isinstance(loaded, list):
                bc.chain = loaded
                st.success("✅ Blockchain replaced successfully!")
            else:
                st.error("Uploaded JSON must be a list of blocks.")
        except Exception as e:
            st.error(f"Failed to load JSON: {e}")
