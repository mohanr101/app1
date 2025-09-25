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
        # Create Genesis Block
        self.new_block(proof=100, previous_hash='1')

    def new_block(self, proof: int, previous_hash: Optional[str] = None) -> Dict[str, Any]:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions.copy(),
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: float) -> int:
        tx = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }
        self.current_transactions.append(tx)
        return self.last_block['index'] + 1 if self.chain else 1

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
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == '0' * self.difficulty

    def compute_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block['transactions']:
                if tx['recipient'] == address:
                    balance += tx['amount']
                if tx['sender'] == address:
                    balance -= tx['amount']
        for tx in self.current_transactions:
            if tx['recipient'] == address:
                balance += tx['amount']
            if tx['sender'] == address:
                balance -= tx['amount']
        return balance

# ------------------------
# Streamlit App
# ------------------------
st.set_page_config(page_title="Classroom Crypto", layout="wide")

# Persist blockchain and node id
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain(difficulty=3)
if 'node_id' not in st.session_state:
    st.session_state.node_id = str(uuid.uuid4()).replace('-', '')

bc: Blockchain = st.session_state.blockchain
node_id: str = st.session_state.node_id

st.title("🎓 Classroom Cryptocurrency on Blockchain")

st.markdown(
    f"*Node ID:* `{node_id}` \n"
    f"*Blockchain Length:* {len(bc.chain)} \n"
    f"*Pending Transactions:* {len(bc.current_transactions)} \n"
    f"*Proof-of-Work Difficulty:* {bc.difficulty}"
)

col1, col2 = st.columns([2, 1])

# ------------------------
# Left column - Blockchain Display
# ------------------------
with col1:
    st.header("Recent Blocks")
    for block in reversed(bc.chain[-5:]):
        with st.expander(f"Block {block['index']} — proof {block['proof']}"):
            st.write("⏰", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block['timestamp'])))
            st.write("🔗 Previous Hash:", block['previous_hash'])
            st.write("📦 Transactions:")
            st.json(block['transactions'])
    if st.button("Show Full Blockchain"):
        st.json(bc.chain)

# ------------------------
# Right column - Operations
# ------------------------
with col2:
    # Mining
    st.header("⛏️ Mine a Block")
    if st.button("Mine New Block"):
        last_proof = bc.last_block['proof']
        with st.spinner("Mining in progress..."):
            proof = bc.proof_of_work(last_proof)
            # Mining reward
            bc.new_transaction(sender="0", recipient=node_id, amount=1)
            new_block = bc.new_block(proof)
        st.success(f"✅ Block #{new_block['index']} mined!")
        st.json(new_block)

    st.markdown("---")

    # Reward Coins (Teacher → Student)
    st.header("🎁 Reward Coins")
    with st.form("reward_form", clear_on_submit=True):
        student = st.text_input("Student Address")
        amount = st.number_input("Coins", min_value=1, step=1)
        reward_submit = st.form_submit_button("Reward")
        if reward_submit:
            index = bc.new_transaction(sender="Teacher", recipient=student, amount=amount)
            st.success(f"Transaction added — will be included in Block {index}")

    st.markdown("---")

    # Transfer Coins
    st.header("🔄 Transfer Coins")
    with st.form("transfer_form", clear_on_submit=True):
        sender = st.text_input("Sender Address", value=node_id)
        recipient = st.text_input("Recipient Address")
        amount = st.number_input("Amount", min_value=0.1, step=0.1)
        transfer_submit = st.form_submit_button("Transfer")
        if transfer_submit:
            if bc.compute_balance(sender) >= amount:
                index = bc.new_transaction(sender=sender, recipient=recipient, amount=amount)
                st.success(f"Transaction added — will be included in Block {index}")
            else:
                st.error("❌ Not enough balance!")

    st.markdown("---")

    # Check Balance
    st.header("💳 Check Balance")
    addr = st.text_input("Enter Address", value=node_id, key="balance_check")
    if st.button("Get Balance"):
        bal = bc.compute_balance(addr)
        st.info(f"Balance for `{addr}`: **{bal} coins**")
