import streamlit as st
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any

# -----------------------
# Block & Blockchain
# -----------------------
@dataclass
class Block:
    index: int
    transaction: Dict[str, Any]
    previous_hash: str
    timestamp: float = field(default_factory=time.time)
    hash: str = field(init=False)

    def __post_init__(self):
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transaction": self.transaction,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def recalc(self, update_timestamp: bool = True):
        if update_timestamp:
            self.timestamp = time.time()
        self.hash = self.calculate_hash()
        return self.hash

class Blockchain:
    def __init__(self):
        self.chain: List[Block] = [self.create_genesis_block()]

    def create_genesis_block(self) -> Block:
        return Block(0, {"sender": "0", "recipient": "0", "amount": 0}, "0")

    def add_block(self, transaction: Dict[str, Any]) -> Block:
        prev = self.chain[-1]
        new_block = Block(len(self.chain), transaction, prev.hash)
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self) -> bool:
        # Validate both recalculated hashes and previous_hash links
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            # check stored hash matches calculated hash
            if curr.hash != curr.calculate_hash():
                return False
            # check link to previous
            if curr.previous_hash != prev.hash:
                return False
        return True

    def tamper_block(self, index: int, new_tx: Dict[str, Any], recompute: bool = False):
        """Tamper block at index. If recompute=True, recompute hash for this and following blocks updating previous_hash links."""
        if index <= 0 or index >= len(self.chain):
            raise IndexError("Index out of range or genesis block cannot be tampered via this method.")
        # Modify the block's transaction (simulate tamper)
        target = self.chain[index]
        target.transaction = new_tx
        # If not recomputing, simply recalc the hash of this block to reflect change
        if not recompute:
            # simulate naive tamper: change hash but do NOT update following blocks' previous_hash
            target.recalc(update_timestamp=False)
            return
        # If recompute True: attacker recomputes this and all following blocks (updates timestamps & hashes)
        target.recalc(update_timestamp=True)
        # propagate fixes forward
        for i in range(index + 1, len(self.chain)):
            self.chain[i].previous_hash = self.chain[i-1].hash
            self.chain[i].recalc(update_timestamp=True)

    def replace_chain(self, new_chain: List[Dict[str, Any]]):
        """Replace chain from external JSON (simple loader)"""
        loaded = []
        for blk in new_chain:
            b = Block(
                index=blk["index"],
                transaction=blk["transaction"],
                previous_hash=blk["previous_hash"],
                timestamp=blk.get("timestamp", time.time())
            )
            # override hash if provided (so loaded chain keeps its stored hashes)
            if "hash" in blk:
                b.hash = blk["hash"]
            else:
                b.hash = b.calculate_hash()
            loaded.append(b)
        self.chain = loaded

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Tamper Playground — Blockchain Demo", layout="wide")

if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()

bc: Blockchain = st.session_state.blockchain

st.title("🔒 Blockchain Tamper Playground")
st.write("Add transactions, then try tampering with a past block. See how the chain validity changes.")

# Left: Add blocks
left, right = st.columns([2, 1])
with left:
    st.header("➕ Add Transaction (creates a new block)")
    with st.form("add_tx", clear_on_submit=True):
        sender = st.text_input("Sender", value="Alice")
        recipient = st.text_input("Recipient", value="Bob")
        amount = st.number_input("Amount", min_value=0.0, step=0.01, value=10.0)
        submitted = st.form_submit_button("Add Transaction -> New Block")
        if submitted:
            if sender and recipient and amount > 0:
                tx = {"sender": sender, "recipient": recipient, "amount": amount}
                new_block = bc.add_block(tx)
                st.success(f"Block #{new_block.index} added. Hash: {new_block.hash[:16]}...")
            else:
                st.error("Enter valid sender/recipient/amount.")

    st.markdown("---")
    st.header("📜 Blockchain Explorer (latest first)")
    for block in reversed(bc.chain):
        with st.expander(f"Block #{block.index} — Hash: {block.hash[:16]}..."):
            st.write("Index:", block.index)
            st.write("Timestamp:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp)))
            st.write("Previous Hash:", block.previous_hash)
            st.json(block.transaction)
    st.markdown("---")
    if st.button("Reset / New Chain"):
        st.session_state.blockchain = Blockchain()
        st.experimental_rerun()

with right:
    st.header("🔧 Tamper with a Block")
    if len(bc.chain) <= 1:
        st.info("Add at least 1 block (beyond genesis) to experiment.")
    else:
        # Choose block to tamper (not genesis)
        tamper_idx = st.selectbox("Select Block Index to Tamper", options=list(range(1, len(bc.chain))))
        st.write("Selected Block Preview:")
        blk = bc.chain[tamper_idx]
        st.json({
            "index": blk.index,
            "timestamp": blk.timestamp,
            "previous_hash": blk.previous_hash,
            "hash": blk.hash,
            "transaction": blk.transaction
        })

        st.markdown("**Edit transaction values to tamper**")
        with st.form("tamper_form"):
            new_sender = st.text_input("New Sender", value=str(blk.transaction.get("sender", "")))
            new_recipient = st.text_input("New Recipient", value=str(blk.transaction.get("recipient", "")))
            new_amount = st.number_input("New Amount", min_value=0.0, step=0.01, value=float(blk.transaction.get("amount", 0.0)))
            tamper_no_recalc = st.form_submit_button("Tamper (no recompute)")
            tamper_recalc = st.form_submit_button("Tamper & Recompute (repair chain)")

            if tamper_no_recalc:
                try:
                    bc.tamper_block(tamper_idx, {"sender": new_sender, "recipient": new_recipient, "amount": new_amount}, recompute=False)
                    st.warning("Block modified WITHOUT repairing subsequent blocks. Chain structure is likely broken now.")
                except Exception as e:
                    st.error(f"Tamper failed: {e}")

            if tamper_recalc:
                try:
                    bc.tamper_block(tamper_idx, {"sender": new_sender, "recipient": new_recipient, "amount": new_amount}, recompute=True)
                    st.success("Block modified and subsequent blocks' hashes were recomputed (chain structure repaired).")
                except Exception as e:
                    st.error(f"Tamper & Recompute failed: {e}")

    st.markdown("---")
    st.header("🔍 Validation")
    valid = bc.is_chain_valid()
    if valid:
        st.success("✅ Blockchain is valid (no tampering detected by structure).")
    else:
        st.error("❌ Blockchain is INVALID — tampering detected!")

    st.markdown("**Notes for class demo:**")
    st.write("- `Tamper (no recompute)` shows how a simple change breaks the chain. The changed block's hash will not match what the next block expects.")
    st.write("- `Tamper & Recompute` simulates an attacker who recalculates hashes for this and all later blocks so the chain looks structurally valid again. Explain to students that in real blockchains an attacker must ALSO redo Proof-of-Work / gain majority consensus, which is extremely costly and usually infeasible.")
    st.write("- Use the Explorer on the left to inspect blocks before and after tampering.")
