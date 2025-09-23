import hashlib, json, time, uuid
from typing import List, Dict, Any, Optional
import streamlit as st

# ---------------- Blockchain ----------------
class Blockchain:
    def __init__(self, difficulty: int = 3):
        self.chain, self.current_transactions, self.difficulty = [], [], difficulty
        self.new_block(proof=100, previous_hash="1")

    def new_block(self, proof: int, previous_hash: Optional[str] = None):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.current_transactions.copy(),
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: float, loan: bool = False):
        self.current_transactions.append({"sender": sender, "recipient": recipient, "amount": amount, "loan": loan})
        return self.last_block["index"] + 1

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    @property
    def last_block(self): return self.chain[-1]

    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while not self.valid_proof(last_proof, proof): proof += 1
        return proof

    def valid_proof(self, last_proof: int, proof: int) -> bool:
        return hashlib.sha256(f"{last_proof}{proof}".encode()).hexdigest()[:self.difficulty] == "0" * self.difficulty

    def compute_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain + [{"transactions": self.current_transactions}]:
            for tx in block["transactions"]:
                if tx["recipient"] == address: balance += tx["amount"]
                if tx["sender"] == address: balance -= tx["amount"]
        return balance

# ---------------- Streamlit ----------------
st.set_page_config(page_title="Loan Tracking Blockchain", layout="wide")

if "blockchain" not in st.session_state: st.session_state.blockchain = Blockchain()
if "node_id" not in st.session_state: st.session_state.node_id = str(uuid.uuid4()).replace("-", "")
bc, node_id = st.session_state.blockchain, st.session_state.node_id

st.title("🏦 Loan Tracking Blockchain")
st.markdown(f"*Node ID:* {node_id}  \n*Blocks:* {len(bc.chain)} | *Pending Tx:* {len(bc.current_transactions)} | *Difficulty:* {bc.difficulty}")

col1, col2 = st.columns([2, 1])

# Left: Blockchain
with col1:
    st.header("Recent Blocks")
    for block in reversed(bc.chain[-10:]):
        with st.expander(f"Block {block['index']} (proof {block['proof']})"):
            st.write("⏱", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block['timestamp'])))
            st.write("Prev Hash:", block["previous_hash"])
            st.json(block["transactions"])
    if st.button("Show Full Chain JSON"): st.json(bc.chain)

# Right: Actions
with col2:
    st.header("Mine Block")
    if st.button("Mine"):
        with st.spinner("Mining..."):
            proof = bc.proof_of_work(bc.last_block["proof"])
            bc.new_transaction(sender="0", recipient=node_id, amount=1)
            st.success(f"Block #{bc.new_block(proof)['index']} mined!")

    st.header("Add Transaction")
    with st.form("tx_form", clear_on_submit=True):
        sender, recipient = st.text_input("Sender", value=node_id), st.text_input("Recipient")
        amount, tx_type = st.number_input("Amount", min_value=0.0, step=0.01), st.radio("Type", ["Loan", "Repayment"])
        if st.form_submit_button("Add"):
            bc.new_transaction(sender, recipient, amount, loan=(tx_type == "Loan"))
            st.success("Transaction added!")

    st.header("Check Balance")
    addr = st.text_input("Address", value=node_id, key="bal_inp")
    if st.button("Get Balance"): st.info(f"Balance: {bc.compute_balance(addr)}")

    st.header("Export / Import Chain")
    st.download_button("Download JSON", json.dumps(bc.chain, indent=2), "chain.json")
    uploaded = st.file_uploader("Upload Chain", type=["json"])
    if uploaded:
        try:
            bc.chain = json.loads(uploaded.read())
            st.success("Chain replaced!")
        except: st.error("Invalid JSON")
