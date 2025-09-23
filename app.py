import hashlib
import json
import time
import uuid
import streamlit as st

# ---------------- Blockchain ----------------
class Blockchain:
    def __init__(self):
        # canonical attributes
        self.chain = []
        self.pending_tx = []                       # canonical name for pending transactions

        # backward-compatible aliases (point to the same list object)
        self.pending_transactions = self.pending_tx
        self.current_transactions = self.pending_tx

        # genesis block
        self.new_block(proof=100, previous_hash="1")

    def new_block(self, proof, previous_hash=None):
        prev = previous_hash or (self.hash(self.chain[-1]) if self.chain else "1")
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.pending_tx.copy(),
            "proof": proof,
            "previous_hash": prev,
        }
        # reset pending list (and keep aliases pointing to the same object)
        self.pending_tx = []
        self.pending_transactions = self.pending_tx
        self.current_transactions = self.pending_tx

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.pending_tx.append({"sender": sender, "recipient": recipient, "amount": amount})
        # return index of the block that will hold this tx (next block)
        return self.last_block["index"] + 1 if self.chain else 1

    @staticmethod
    def hash(block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof, difficulty_prefix="0000"):
        proof = 0
        while hashlib.sha256(f"{last_proof}{proof}".encode()).hexdigest()[: len(difficulty_prefix)] != difficulty_prefix:
            proof += 1
        return proof

    def get_balance(self, address):
        bal = 0.0
        for block in self.chain:
            for tx in block["transactions"]:
                if tx["recipient"] == address:
                    bal += tx["amount"]
                if tx["sender"] == address:
                    bal -= tx["amount"]
        # include pending txs (optional, shows pending net effect)
        for tx in self.pending_tx:
            if tx["recipient"] == address:
                bal += tx["amount"]
            if tx["sender"] == address:
                bal -= tx["amount"]
        return bal

# ---------------- Streamlit App ----------------
st.set_page_config(page_title="💰 Crypto Wallet Simulator (Fixed)", layout="wide")

# If a blockchain object already exists in session_state, normalize it for compatibility.
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()
else:
    # normalize an existing object that may come from older code versions
    bc_obj = st.session_state.blockchain
    if not hasattr(bc_obj, "pending_tx"):
        if hasattr(bc_obj, "pending_transactions"):
            bc_obj.pending_tx = bc_obj.pending_transactions
        elif hasattr(bc_obj, "current_transactions"):
            bc_obj.pending_tx = bc_obj.current_transactions
        else:
            bc_obj.pending_tx = []
    # ensure aliases point to the same list
    bc_obj.pending_transactions = bc_obj.pending_tx
    bc_obj.current_transactions = bc_obj.pending_tx
    # no need to reassign to session_state (same object), but for clarity:
    st.session_state.blockchain = bc_obj

if "wallet" not in st.session_state:
    st.session_state.wallet = str(uuid.uuid4())[:8]

bc = st.session_state.blockchain
wallet = st.session_state.wallet

# Header / Dashboard
st.title("💰 Mini Crypto Wallet — Fixed")
st.caption("Demo blockchain app (wallet + explorer). This version normalizes different session-state shapes to avoid attribute errors.")

col1, col2, col3 = st.columns(3)
col1.metric("Blocks", len(bc.chain))
col2.metric("Pending Tx", len(bc.pending_tx))
col3.metric("Your Balance", f"{bc.get_balance(wallet):.2f} tokens")

# Tabs
tab1, tab2, tab3 = st.tabs(["📤 Send Money", "⛏️ Mine Block", "🔍 Explorer"])

with tab1:
    st.subheader("Send Tokens")
    recipient = st.text_input("Recipient Wallet ID")
    amount = st.number_input("Amount", min_value=0.0, step=1.0)
    if st.button("Send"):
        if not recipient:
            st.error("Please provide a recipient wallet ID.")
        elif amount <= 0:
            st.error("Amount must be greater than 0.")
        else:
            bc.new_transaction(sender=wallet, recipient=recipient, amount=amount)
            st.success(f"Transaction queued: {amount} → {recipient}")

with tab2:
    st.subheader("Mine (confirm pending transactions)")
    if st.button("Mine Now"):
        last_proof = bc.last_block["proof"]
        proof = bc.proof_of_work(last_proof, difficulty_prefix="0000")
        # reward miner (you)
        bc.new_transaction(sender="SYSTEM", recipient=wallet, amount=10)
        new_block = bc.new_block(proof)
        st.success(f"Block #{new_block['index']} mined. Reward credited (+10).")
        st.json(new_block)

with tab3:
    st.subheader("Blockchain Explorer")
    for block in reversed(bc.chain):
        with st.expander(f"Block #{block['index']} — proof {block['proof']}"):
            st.write("Timestamp:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block["timestamp"])))
            st.write("Prev hash:", block["previous_hash"])
            st.json(block["transactions"])

# Sidebar: wallet info & import/export
st.sidebar.header("🔑 Wallet")
st.sidebar.write("ID:", wallet)
st.sidebar.write("Balance:", f"{bc.get_balance(wallet):.2f}")

st.sidebar.markdown("---")
st.sidebar.header("📂 Chain Export / Import")
chain_json = json.dumps(bc.chain, indent=2)
st.sidebar.download_button("Download Chain JSON", data=chain_json, file_name="chain.json", mime="application/json")
uploaded = st.sidebar.file_uploader("Upload Chain JSON (replace)", type=["json"])
if uploaded:
    try:
        raw = uploaded.read()
        # raw may be bytes; decode if necessary
        loaded = json.loads(raw.decode() if isinstance(raw, (bytes, bytearray)) else raw)
        if isinstance(loaded, list):
            bc.chain = loaded
            st.sidebar.success("Chain replaced successfully.")
        else:
            st.sidebar.error("Uploaded file must be a JSON list (chain = [blocks...]).")
    except Exception as e:
        st.sidebar.error(f"Failed to load JSON: {e}")
