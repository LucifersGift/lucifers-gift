import os
import qrcode
from io import BytesIO
import base64
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class CryptoWalletManager:
    def __init__(self):
        key = os.getenv("WALLET_ENCRYPTION_KEY")
        if key:
            self.fernet = Fernet(key.encode())
        else:
            self.fernet = Fernet(Fernet.generate_key())

    def generate_seed_phrase(self, words: int = 12) -> str:
        """Generate 12 or 24 word seed phrase"""
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(words)
        return str(mnemonic)

    def derive_wallet(self, seed_phrase: str, coin: str, account_index: int = 0):
        seed_bytes = Bip39SeedGenerator(seed_phrase).Generate()
        coin_upper = coin.upper()

        if coin_upper == "SOL":
            from solders.keypair import Keypair
            from solders.mnemonic import Mnemonic
            mnemonic = Mnemonic.from_string(seed_phrase)
            seed = mnemonic.to_seed()[:32]
            keypair = Keypair.from_seed(seed)
            return {
                "coin": "SOL",
                "account_index": account_index,
                "address": str(keypair.pubkey()),
                "private_key": str(keypair.secret_key()),
                "derivation_path": f"m/44'/501'/{account_index}'/0'"
            }

        coin_map = {
            "BTC": Bip44Coins.BITCOIN,
            "ETH": Bip44Coins.ETHEREUM,
            "LTC": Bip44Coins.LITECOIN,
            "DOGE": Bip44Coins.DOGECOIN,
        }
        if coin_upper not in coin_map:
            raise ValueError(f"Unsupported coin: {coin}")

        bip_ctx = Bip44.FromSeed(seed_bytes, coin_map[coin_upper])
        account = bip_ctx.Purpose().Coin().Account(account_index)
        change = account.Change(Bip44Changes.CHAIN_EXT)
        addr_ctx = change.AddressIndex(0)

        return {
            "coin": coin_upper,
            "account_index": account_index,
            "address": addr_ctx.PublicKey().ToAddress(),
            "derivation_path": addr_ctx.PublicKey().ToPath(),
            "private_key": addr_ctx.PrivateKey().Raw().ToHex(),
        }

    def generate_qr_code(self, address: str) -> str:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
