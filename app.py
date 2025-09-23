import hashlib
import json
import time
import uuid
from typing import List, Dict, Any, Optional
import streamlit as st
# ------------------------
# Blockchain for Loan Tracking
1
# ------------------------
class Blockchain:
 def __init__(self, difficulty: int = 4): # Constructor
 self.chain: List[Dict[str, Any]] = []
 self.current_transactions: List[Dict[str, Any]] = []
 self.difficulty = difficulty
 # Create genesis block
 self.new_block(proof=100, previous_hash='1')
 def new_block(self, proof: int, previous_hash: Optional[str] = None)->
 Dict[str, Any]:
 block = {
 'index': len(self.chain) + 1,
 'timestamp': time.time(),
 'transactions': self.current_transactions.copy(),
 'proof': proof,
 'previous_hash': previous_hash or self.hash(self.chain[-1])
 }
 self.current_transactions = []
 self.chain.append(block)
 return block
 def new_transaction(self, sender: str, recipient: str, amount: float, loan:
 bool = False)-> int:
 tx = {
 'sender': sender,
 'recipient': recipient,
 'amount': amount,
 'loan': loan
 }
 self.current_transactions.append(tx)
 return self.last_block['index'] + 1 if self.chain else 1
 @staticmethod
 def hash(block: Dict[str, Any])-> str:
 block_string = json.dumps(block, sort_keys=True).encode()
 return hashlib.sha256(block_string).hexdigest()
 @property
 def last_block(self)-> Dict[str, Any]:
 return self.chain[-1]
 def proof_of_work(self, last_proof: int)-> int:
 proof = 0
 while not self.valid_proof(last_proof, proof):
 proof += 1
 return proof
 2
def valid_proof(self, last_proof: int, proof: int)-> bool:
 guess = f'{last_proof}{proof}'.encode()
 guess_hash = hashlib.sha256(guess).hexdigest()
 return guess_hash[:self.difficulty] == '0' * self.difficulty
 def compute_balance(self, address: str)-> float:
 balance = 0.0
 for block in self.chain:
 for tx in block['transactions']:
 if tx['recipient'] == address:
 balance += tx['amount']
 if tx['sender'] == address:
 balance-= tx['amount']
 for tx in self.current_transactions:
 if tx['recipient'] == address:
 balance += tx['amount']
 if tx['sender'] == address:
 balance-= tx['amount']
 return balance
 # ------------------------
# Streamlit App
 # ------------------------
st.set_page_config(page_title="Loan Tracking Blockchain", layout="wide")
 # Persist blockchain and node id
 if 'blockchain' not in st.session_state:
 st.session_state.blockchain = Blockchain(difficulty=3)
 if 'node_id' not in st.session_state:
 st.session_state.node_id = str(uuid.uuid4()).replace('-', '')
 bc: Blockchain = st.session_state.blockchain
 node_id: str = st.session_state.node_id
 st.title("🏦 Loan Tracking System on Blockchain")
 st.markdown(
 f"*Node ID:* {node_id} \n"
 f"*Blockchain Length:* {len(bc.chain)} \n"
 f"*Pending Transactions:* {len(bc.current_transactions)} \n"
 f"*Proof-of-Work Difficulty:* {bc.difficulty}"
 )
 col1, col2 = st.columns([2, 1])
 # ------------------------
# Left column - Blockchain Display
 3
# ------------------------
with col1:
 st.header("Recent Blocks")
 for block in reversed(bc.chain[-10:]):
 with st.expander(f"Block {block['index']} — proof {block['proof']}"):
 st.write("Timestamp:", time.strftime('%Y-%m-%d %H:%M:%S',
 time.localtime(block['timestamp'])))
 st.write("Previous Hash:", block['previous_hash'])
 st.write("Transactions:")
 st.json(block['transactions'])
 st.markdown("---")
 if st.button("Show Full Chain JSON"):
 st.json(bc.chain)
 # ------------------------
# Right column - Operations
 # ------------------------
with col2:
 st.header("Mine a Block")
 if st.button("Mine"):
 last_proof = bc.last_block['proof']
 with st.spinner("Mining new block..."):
 proof = bc.proof_of_work(last_proof)
 # Mining reward: 1 unit
 bc.new_transaction(sender="0", recipient=node_id, amount=1)
 new_block = bc.new_block(proof)
 st.success(f"Block #{new_block['index']} mined successfully!")
 st.json(new_block)
 st.markdown("---")
 st.header("Issue Loan / Record Repayment")
 with st.form("loan_form", clear_on_submit=True):
 sender = st.text_input("Sender Address", value=node_id)
 recipient = st.text_input("Recipient Address")
 amount = st.number_input("Amount", min_value=0.0, step=0.01)
 loan_type = st.radio("Transaction Type", ["Loan Issued", "Repayment"])
 submitted = st.form_submit_button("Add Transaction")
 if submitted:
 is_loan = True if loan_type == "Loan Issued" else False
 index = bc.new_transaction(sender=sender, recipient=recipient,
 amount=amount, loan=is_loan)
 st.success(f"Transaction added and will be included in Block 
{index}")
 st.markdown("---")
 st.header("Check Balance")
 addr = st.text_input("Address to check balance", value=node_id,
 4
key="balance_input")
 if st.button("Get Balance"):
 bal = bc.compute_balance(addr)
 st.write(f"Balance for {addr}: *{bal}*")
 st.markdown("---")
 st.header("Export / Import Blockchain")
 chain_json = json.dumps(bc.chain, indent=2)
 st.download_button("Download Chain JSON", data=chain_json,
 file_name="loan_chain.json", mime="application/json")
 uploaded = st.file_uploader("Upload JSON to replace current chain",
 type=['json'])
 if uploaded:
 try:
 loaded = json.loads(uploaded.read())
 if isinstance(loaded, list):
 bc.chain = loaded
 st.success("Chain replaced successfully!")
 else:
 st.error("Uploaded JSON must be a list of blocks.")
 except Exception as e:
 st.error(f"Failed to load JSON: {e}"