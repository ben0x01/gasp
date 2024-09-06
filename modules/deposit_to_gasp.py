import asyncio
import random
import json

from web3 import AsyncWeb3
from web3.exceptions import TransactionNotFound, ContractLogicError

from helper import approve_deposit_abi
from config import MIN_DELAY, MAX_DELAY, AMOUNT_OF_GASP


class Deposit:
    def __init__(self, private_key, rpc):
        self.private_key = private_key
        self.rpc = rpc
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(self.rpc))
        self.wallet = self.w3.eth.account.from_key(self.private_key)
        self.approve_contract_address = AsyncWeb3.to_checksum_address("0x5620cDb94BaAaD10c20483bd8705DA711b2Bc0a3")
        self.deposit_contract_address = AsyncWeb3.to_checksum_address("0x93de6a193A839218BCA00c8D478256Ac78281cE3")
        with open(approve_deposit_abi) as file:
            self._deposit_abi = json.load(file)

        self.approve_contract = self.w3.eth.contract(address=self.approve_contract_address, abi=self._deposit_abi)
        self.deposit_contract = self.w3.eth.contract(address=self.deposit_contract_address, abi=self._deposit_abi)

        self.holesky_url = "https://holesky.etherscan.io/tx"

    async def get_random_amount(self):
        balance = await self.w3.eth.get_balance(self.wallet.address)
        balance_decimal = float(self.w3.from_wei(balance, "ether"))
        random_amount = random.uniform(0, balance_decimal / 4)
        return self.w3.to_wei(random_amount, 'ether')

    async def is_transaction_successful(self, tx_hash: hex) -> bool:
        await asyncio.sleep(30)
        try:
            receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
            return receipt['status'] == 1
        except TransactionNotFound:
            print(f"Transaction with hash {tx_hash} not found.")
            return False
        except Exception as e:
            print(f"Error checking transaction: {e}")
            return False

    async def prepare_tx(self, eip1559=True):
        nonce = await self.w3.eth.get_transaction_count(self.wallet.address)
        base_fee = await self.w3.eth.gas_price
        max_priority_fee_per_gas = await self.w3.eth.max_priority_fee

        if eip1559:
            tx = {
                "from": self.wallet.address,
                "to": self.deposit_contract_address,
                "value": await self.get_random_amount(),
                "maxPriorityFeePerGas": max_priority_fee_per_gas,
                "maxFeePerGas": base_fee + max_priority_fee_per_gas,
                "nonce": nonce,
                "data": "0x274b3df4",
                "chainId": 17000
            }
        else:
            tx = {
                "from": self.wallet.address,
                "to": self.deposit_contract_address,
                "value": await self.get_random_amount(),
                "gas": 210000,
                "data": "0x274b3df4",
                "nonce": nonce,
                "chainId": 17000
            }

        estimated_gas = await self.w3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        print("Transaction successfully signed")
        tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        if await self.is_transaction_successful(tx_hash):
            print(f'Transaction hash: {self.holesky_url}/0x{tx_hash.hex()}')

    async def approve_and_deposit(self):
        nonce = await self.w3.eth.get_transaction_count(self.wallet.address)
        base_fee = await self.w3.eth.gas_price
        max_priority_fee_per_gas = await self.w3.eth.max_priority_fee

        try:
            tx = await self.approve_contract.functions.approve(
                "0x93de6a193A839218BCA00c8D478256Ac78281cE3",
                AMOUNT_OF_GASP
            ).build_transaction({
                "from": self.wallet.address,
                "nonce": nonce,
                "value": 0,
                "maxPriorityFeePerGas": max_priority_fee_per_gas,
                "maxFeePerGas": base_fee + max_priority_fee_per_gas,
            })

            estimated_gas = await self.w3.eth.estimate_gas(tx)
            tx['gas'] = estimated_gas
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            print("Transaction successfully signed")
            tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            if await self.is_transaction_successful(tx_hash):
                print(f'Transaction hash: {self.holesky_url}/0x{tx_hash.hex()}')

            nonce += 1

            tx = await self.deposit_contract.functions.deposit(
                "0x5620cDb94BaAaD10c20483bd8705DA711b2Bc0a3",
                AMOUNT_OF_GASP
            ).build_transaction({
                "from": self.wallet.address,
                "nonce": nonce,
                "value": 0,
                "maxPriorityFeePerGas": max_priority_fee_per_gas,
                "maxFeePerGas": base_fee + max_priority_fee_per_gas,
            })

            estimated_gas = await self.w3.eth.estimate_gas(tx)
            tx['gas'] = estimated_gas
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            print("Transaction successfully signed")
            tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            if await self.is_transaction_successful(tx_hash):
                print(f'Transaction hash: {self.holesky_url}/0x{tx_hash.hex()}')

        except ContractLogicError as e:
            print(f"Contract logic error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")


async def start_deposit(private_key, rpc):
    deposit_instance = Deposit(private_key, rpc)
    await deposit_instance.prepare_tx()
    await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    await deposit_instance.approve_and_deposit()