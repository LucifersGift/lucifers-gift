from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Wallet
from wallet_manager import CryptoWalletManager
from transaction_service import TransactionService
from auth import router as auth_router, get_current_user

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lucifers Gift")

app.include_router(auth_router)

manager = CryptoWalletManager()
tx_service = TransactionService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/wallets/generate")
def generate_wallet(
    coin: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    seed = manager.generate_seed_phrase(12)
    wallet_data = manager.derive_wallet(seed, coin)
    
    wallet = Wallet(
        user_id=current_user.id,
        coin=coin.upper(),
        address=wallet_data["address"],
        account_index=wallet_data.get("account_index", 0),
        derivation_path=wallet_data.get("derivation_path")
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    
    return {
        "seed_phrase": seed,
        "wallet": wallet_data,
        "qr_code_base64": manager.generate_qr_code(wallet_data["address"]),
        "warning": "BACKUP YOUR SEED PHRASE IMMEDIATELY AND SECURELY!"
    }

@app.get("/wallets")
def get_user_wallets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Wallet).filter(Wallet.user_id == current_user.id).all()

@app.get("/")
def root():
    return {"message": "Lucifers Gift API is running. Register or login at /auth/register or /auth/login"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
