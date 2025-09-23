import hashlib, json, time, uuid
import streamlit as st

# ---------------- Blockchain ----------------
class Blockchain:
    def __init__(self):
        self.chain, self.pending_tx = [], []
        self.new_block(previous_hash="1", proof=100)  # Genesis block

    def new_block(self, proof, previous_hash=None):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.pending_tx,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1])
        }
        self.pending_tx = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.pending_tx.append({"sender": sender, "recipient": recipient, "amount": amount})
        return self.last_block["index"] + 1

    @staticmethod
    def hash(block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    @property
    def last_block(self): return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while hashlib.sha256(f"{last_proof}{proof}".encode()).hexdigest()[:4] != "0000":
            proof += 1
        return proof

    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for tx in block["transactions"]:
                if tx["recipient"] == address: balance += tx["amount"]
                if tx["sender"] == address: balance -= tx["amount"]
        return balance

# ---------------- Streamlit ----------------
st.set_page_config(page_title="💰 Crypto Wallet Simulator", layout="wide")

if "blockchain" not in st.session_state: st.session_state.blockchain = Blockchain()
if "wallet" not in st.session_state: st.session_state.wallet = str(uuid.uuid4())[:8]

bc, wallet = st.session_state.blockchain, st.session_state.wallet

st.title("💰 Mini Crypto Wallet on Blockchain")
st.caption("A simple blockchain project to simulate wallet transactions (FinTech Demo)")

# Dashboard
col1, col2, col3 = st.columns(3)
col1.metric("Blocks", len(bc.chain))
col2.metric("Pending Tx", len(bc.pending_tx))
col3.metric("Your Balance", f"{bc.get_balance(wallet)} 💵")

# Tabs
tab1, tab2, tab3 = st.tabs(["📤 Send Money", "⛏️ Mine Block", "🔍 Blockchain Explorer"])

with tab1:
    st.subheader("Send Money")
    recipient = st.text_input("Recipient Wallet ID")
    amount = st.number_input("Amount", min_value=0.0, step=1.0)
    if st.button("Send"):
        if recipient and amount > 0:
            bc.new_transaction(wallet, recipient, amount)
            st.success(f"✅ Transaction added to pending block!")
        else:
            st.error("Please enter recipient and amount")

with tab2:
    st.subheader("Mine Block")
    if st.button("⛏️ Mine Now"):
        proof = bc.proof_of_work(bc.last_block["proof"])
        bc.new_transaction("SYSTEM", wallet, 10)  # Mining reward
        block = bc.new_block(proof)
        st.success(f"Block #{block['index']} mined! You earned 10 💵")
        st.json(block)

with tab3:
    st.subheader("Blockchain Explorer")
    for block in reversed(bc.chain):
        with st.expander(f"Block #{block['index']}"):
            st.write("Timestamp:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block["timestamp"])))
            st.write("Proof:", block["proof"])
            st.write("Prev Hash:", block["previous_hash"])
            st.json(block["transactions"])

st.sidebar.header("🔑 Your Wallet")
st.sidebar.write("Wallet ID:", wallet)
st.sidebar.write("Balance:", bc.get_balance(wallet))
