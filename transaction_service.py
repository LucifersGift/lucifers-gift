import os
from web3 import Web3
from models import Transaction
from dotenv import load_dotenv

load_dotenv()

class TransactionService:
    FEE_PERCENT = 0.002  # 0.2%

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("INFURA_URL", "https://eth.llamarpc.com")))

    def calculate_fee(self, amount: float) -> float:
        return round(amount * self.FEE_PERCENT, 8)

    def record_transaction(self, db, user_id: int, from_addr: str, to_addr: str, 
                         coin: str, amount: float, tx_hash: str = None):
        fee = self.calculate_fee(amount)
        tx = Transaction(
            user_id=user_id,
            from_address=from_addr,
            to_address=to_addr,
            coin=coin,
            amount=amount - fee,
            fee=fee,
            tx_hash=tx_hash,
            status="completed" if tx_hash else "pending"
        )
        db.add(tx)
        db.commit()
        return tx
