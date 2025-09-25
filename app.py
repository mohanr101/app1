import hashlib
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
import pandas as pd

# ------------------------
# Blockchain Class
# ------------------------
class Blockchain:
    def __init__(self, difficulty: int = 3):
        self.chain: List[Dict[str, Any]] = []
        self.current_transactions: List[Dict[str, Any]] = []
        self.difficulty = difficulty
        # Create Genesis Block
        self.new_block(proof=100, previous_hash='1', note="Genesis Block")

    def new_block(self, proof: int, previous_hash: Optional[str] = None, note: str = "") -> Dict[str, Any]:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions.copy(),
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'note': note
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: float) -> int:
        tx = {
            'sender': sender,
            'recipient': recipient,
            'amount': float(amount),
            'timestamp': time.time()
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

    def all_transactions(self) -> List[Dict[str, Any]]:
        """
        Return list of all transactions with metadata (which block index / pending).
        """
        txs = []
        for block in self.chain:
            for tx in block['transactions']:
                tx_copy = tx.copy()
                tx_copy.update({'block_index': block['index'], 'block_timestamp': block['timestamp'], 'status': 'confirmed'})
                txs.append(tx_copy)
        # pending transactions
        for tx in self.current_transactions:
            tx_copy = tx.copy()
            tx_copy.update({'block_index': None, 'block_timestamp': None, 'status': 'pending'})
            txs.append(tx_copy)
        return txs

# ------------------------
# Utility functions (for display & totals)
# ------------------------
def extract_addresses(tx_list: List[Dict[str, Any]]) -> List[str]:
    addrs = set()
    for tx in tx_list:
        addrs.add(tx.get('sender'))
        addrs.add(tx.get('recipient'))
    # remove None if present
    return [a for a in addrs if a is not None]

def address_summary(blockchain: Blockchain) -> pd.DataFrame:
    txs = blockchain.all_transactions()
    addresses = extract_addresses(txs)
    rows = []
    for addr in addresses:
        received = sum(t['amount'] for t in txs if t['recipient'] == addr)
        sent = sum(t['amount'] for t in txs if t['sender'] == addr)
        count_in = sum(1 for t in txs if t['recipient'] == addr)
        count_out = sum(1 for t in txs if t['sender'] == addr)
        balance = blockchain.compute_balance(addr)
        rows.append({
            'address': addr,
            'balance': balance,
            'received_total': received,
            'sent_total': sent,
            'tx_count_in': count_in,
            'tx_count_out': count_out,
            'tx_count_total': count_in + count_out
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # sort by balance desc
    return df.sort_values(by='balance', ascending=False).reset_index(drop=True)

def total_minted(blockchain: Blockchain) -> float:
    # coins created by mining rewards are transactions where sender == "0"
    txs = blockchain.all_transactions()
    return sum(t['amount'] for t in txs if t['sender'] == "0")

def total_in_circulation(blockchain: Blockchain) -> float:
    # safer: sum of balances across all known addresses
    df = address_summary(blockchain)
    if df.empty:
        return 0.0
    return float(df['balance'].sum())

# ------------------------
# Streamlit App
# ------------------------
st.set_page_config(page_title="Classroom Crypto (Extended)", layout="wide")

# Persist blockchain and node id
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain(difficulty=3)
if 'node_id' not in st.session_state:
    st.session_state.node_id = str(uuid.uuid4()).replace('-', '')

bc: Blockchain = st.session_state.blockchain
node_id: str = st.session_state.node_id

st.title("🎓 Classroom Cryptocurrency (Extended)")

st.markdown(
    f"*Node ID:* `{node_id}`  \n"
    f"*Blockchain Length:* {len(bc.chain)}  \n"
    f"*Pending Transactions:* {len(bc.current_transactions)}  \n"
    f"*Proof-of-Work Difficulty:* {bc.difficulty}"
)

col_left, col_right = st.columns([2.2, 1])

# ------------------------
# Left column - Blockchain & Transactions Display
# ------------------------
with col_left:
    st.header("Recent Blocks & Mining")
    for block in reversed(bc.chain[-6:]):
        with st.expander(f"Block {block['index']} — proof {block['proof']} — note: {block.get('note','')}"):
            st.write("⏰", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block['timestamp'])))
            st.write("🔗 Previous Hash:", block['previous_hash'])
            st.write("📝 Note:", block.get('note', ''))
            st.write("📦 Transactions:")
            st.json(block['transactions'])

    if st.button("Show Full Blockchain JSON"):
        st.json(bc.chain)

    st.markdown("---")
    st.header("All Transactions (Confirmed + Pending)")
    all_txs = bc.all_transactions()
    if all_txs:
        # present as table
        df_txs = pd.DataFrame(all_txs)
        # convert timestamps to readable strings where present
        df_txs['timestamp'] = df_txs['timestamp'].apply(lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) if pd.notnull(t) else "")
        df_txs['block_timestamp'] = df_txs['block_timestamp'].apply(lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) if pd.notnull(t) else "")
        # reorder columns
        cols = ['status','block_index','block_timestamp','timestamp','sender','recipient','amount']
        df_txs = df_txs[cols]
        st.dataframe(df_txs)
    else:
        st.info("No transactions yet.")

    st.markdown("---")
    st.header("Filter Transactions by Address")
    addr_filter = st.text_input("Enter address to filter (leave empty to skip)")
    if st.button("Filter"):
        txs = bc.all_transactions()
        if addr_filter:
            filtered = [t for t in txs if t.get('sender') == addr_filter or t.get('recipient') == addr_filter]
            if filtered:
                df_f = pd.DataFrame(filtered)
                df_f['timestamp'] = df_f['timestamp'].apply(lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) if pd.notnull(t) else "")
                df_f['block_timestamp'] = df_f['block_timestamp'].apply(lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) if pd.notnull(t) else "")
                df_f = df_f[['status','block_index','block_timestamp','timestamp','sender','recipient','amount']]
                st.dataframe(df_f)
                # summary
                total_received = sum(t['amount'] for t in filtered if t.get('recipient') == addr_filter)
                total_sent = sum(t['amount'] for t in filtered if t.get('sender') == addr_filter)
                count_in = sum(1 for t in filtered if t.get('recipient') == addr_filter)
                count_out = sum(1 for t in filtered if t.get('sender') == addr_filter)
                st.success(f"Address `{addr_filter}` — Received: {total_received}, Sent: {total_sent}, In: {count_in}, Out: {count_out}")
            else:
                st.warning("No transactions found for this address.")
        else:
            st.warning("Please enter an address to filter.")

# ------------------------
# Right column - Operations & Summaries
# ------------------------
with col_right:
    # Mining with custom note
    st.header("⛏️ Mine New Block (with optional note)")
    note = st.text_input("Block Note (optional)", value="")
    if st.button("Mine Block Now (include pending txs)"):
        last_proof = bc.last_block['proof']
        with st.spinner("Mining..."):
            proof = bc.proof_of_work(last_proof)
            # Reward miner with 1 coin minted (sender="0")
            bc.new_transaction(sender="0", recipient=node_id, amount=1)
            new_block = bc.new_block(proof, note=note)
        st.success(f"Block #{new_block['index']} mined and added!")
        st.json(new_block)

    st.markdown("---")
    # Custom transaction input (form + raw json option)
    st.header("➕ Create Transaction (add to pending)")
    st.write("You can add a transaction (Teacher -> Student, Student -> Student etc.). These will be pending until a block is mined.")
    with st.form("tx_form", clear_on_submit=True):
        t_sender = st.text_input("Sender Address", value="Teacher")
        t_recipient = st.text_input("Recipient Address", value="")
        t_amount = st.number_input("Amount", min_value=0.1, step=0.1, value=1.0)
        add_tx = st.form_submit_button("Add Transaction")
        if add_tx:
            idx = bc.new_transaction(sender=t_sender, recipient=t_recipient, amount=t_amount)
            st.success(f"Transaction added — will be included in Block {idx} (when mined)")

    st.markdown("or paste a raw transaction JSON (example: `{\"sender\":\"A\",\"recipient\":\"B\",\"amount\":2}`)")
    raw = st.text_area("Raw JSON (optional)")
    if st.button("Add Raw JSON Transaction"):
        if not raw.strip():
            st.error("Paste JSON first.")
        else:
            try:
                parsed = json.loads(raw)
                s = parsed.get('sender')
                r = parsed.get('recipient')
                a = float(parsed.get('amount'))
                idx = bc.new_transaction(sender=s, recipient=r, amount=a)
                st.success(f"Raw transaction added — will be included in Block {idx}")
            except Exception as e:
                st.error(f"Invalid JSON or fields missing: {e}")

    st.markdown("---")
    # Reward form as convenience (teacher)
    st.header("🎁 Quick Reward (Teacher -> Student)")
    with st.form("reward_quick", clear_on_submit=True):
        student_q = st.text_input("Student Address")
        amount_q = st.number_input("Coins", min_value=1, step=1, value=1)
        do_reward = st.form_submit_button("Reward Now")
        if do_reward:
            idx = bc.new_transaction(sender="Teacher", recipient=student_q, amount=amount_q)
            st.success(f"Reward transaction added — will be included in Block {idx}")

    st.markdown("---")
    # Balance check & totals
    st.header("💳 Check Balance / Totals")
    addr_check = st.text_input("Address to check balance", value=node_id, key="balance_check_right")
    if st.button("Get Balance & Summary"):
        bal = bc.compute_balance(addr_check)
        st.info(f"Balance for `{addr_check}`: **{bal} coins**")
        # quick transaction summary for address
        txs = bc.all_transactions()
        filtered = [t for t in txs if t.get('sender') == addr_check or t.get('recipient') == addr_check]
        total_received = sum(t['amount'] for t in filtered if t.get('recipient') == addr_check)
        total_sent = sum(t['amount'] for t in filtered if t.get('sender') == addr_check)
        st.write(f"Total received: {total_received} | Total sent: {total_sent} | Transaction count: {len(filtered)}")

    st.markdown("---")
    st.header("📊 System Totals & Per-Address Summary")
    minted = total_minted(bc)
    circ = total_in_circulation(bc)
    st.write(f"Total minted (from mining rewards, sender='0'): **{minted} coins**")
    st.write(f"Total in circulation (sum of balances across known addresses): **{circ} coins**")

    # Address summary table
    df_addr = address_summary(bc)
    if not df_addr.empty:
        st.subheader("Per-address summary (balances & counts)")
        st.dataframe(df_addr)
        if st.button("Download per-address CSV"):
            csv = df_addr.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", data=csv, file_name="address_summary.csv", mime="text/csv")
    else:
        st.info("No addresses / transactions yet — summary will appear once transactions exist.")

    st.markdown("---")
    st.header("Export / Import Blockchain")
    chain_json = json.dumps(bc.chain, indent=2)
    st.download_button("Download Chain JSON", data=chain_json, file_name="classroom_chain.json", mime="application/json")
    uploaded = st.file_uploader("Upload JSON to replace current chain", type=['json'])
    if uploaded:
        try:
            loaded = json.loads(uploaded.read())
            if isinstance(loaded, list):
                bc.chain = loaded
                # clear pending txs when replacing chain
                bc.current_transactions = []
                st.success("Chain replaced successfully!")
            else:
                st.error("Uploaded JSON must be a list of blocks.")
        except Exception as e:
            st.error(f"Failed to load JSON: {e}")
