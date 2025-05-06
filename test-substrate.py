from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException
from substrateinterface.utils.ss58 import ss58_encode
from substrateinterface.keypair import Keypair
import time
import argparse
from pycoingecko import CoinGeckoAPI
import threading
import random
from threading import Lock

def create_limit_orders(
    substrate: SubstrateInterface,
    account,
    base_asset: int,
    quote_asset: int,
    base_price: int,  # Already in integer format
    tick_count: int,
    tick_spacing: int,  # Already in integer format
    amount_per_order: int  # Already in integer format
):
    """
    Create multiple limit orders at different price levels
    
    Args:
        substrate: SubstrateInterface instance
        account: Account to submit transactions
        base_asset: Base asset ID
        quote_asset: Quote asset ID
        base_price: Base price (in integer format)
        tick_count: Number of ticks to create on each side
        tick_spacing: Price spacing between ticks (in integer format)
        amount_per_order: Amount for each order (in integer format)
    """
    try:
        # Format asset IDs for Substrate
        base_asset_obj = {'WithId': base_asset}
        quote_asset_obj = {'WithId': quote_asset}
        
        # Create ask orders (above base price)
        for i in range(tick_count):
            ask_price = base_price + ((i + 1) * tick_spacing)
            
            # Create ask (sell) order
            call = substrate.compose_call(
                call_module='HybridOrderbook',
                call_function='limit_order',
                call_params={
                    'base_asset': base_asset_obj,
                    'quote_asset': quote_asset_obj,
                    'is_bid': False,  # ask order
                    'price': str(ask_price),
                    'quantity': str(amount_per_order)
                }
            )
            
            # Create and submit extrinsic
            extrinsic = substrate.create_signed_extrinsic(
                call=call,
                keypair=account
            )
            receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
            print(f"Ask order placed at price {ask_price}: {receipt.extrinsic_hash}")
            
            # Small delay between transactions
            time.sleep(2)

        # Create bid orders (below base price)
        for i in range(tick_count):
            bid_price = base_price - ((i + 1) * tick_spacing)
            
            # Create bid (buy) order
            call = substrate.compose_call(
                call_module='HybridOrderbook',
                call_function='limit_order',
                call_params={
                    'base_asset': base_asset_obj,
                    'quote_asset': quote_asset_obj,
                    'is_bid': True,  # bid order
                    'price': str(bid_price),
                    'quantity': str(amount_per_order)
                }
            )
            
            # Create and submit extrinsic
            extrinsic = substrate.create_signed_extrinsic(
                call=call,
                keypair=account
            )
            receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
            print(f"Bid order placed at price {bid_price}: {receipt.extrinsic_hash}")
            
            # Small delay between transactions
            time.sleep(2)

    except SubstrateRequestException as e:
        print(f"Error creating orders: {e}")

def health_check():
    substrate = SubstrateInterface(
        url="http://172.16.1.151:9988"
    )
    chain_head = substrate.get_chain_head()
    print("\n1. Chain Head Information:")
    print(f"Chain Head Block Hash: {chain_head}")
    latest_block = substrate.get_block_number(chain_head)
    print(f"Latest Block Number: #{latest_block}")
    print("\nLast 5 blocks:")
    current_hash = chain_head
    for i in range(5):
        block = substrate.get_block(current_hash)
        block_number = substrate.get_block_number(current_hash)
        print(f"Block #{block_number}: {current_hash}")
        current_hash = block['header']['parentHash']

def bootstrap_chain(substrate: SubstrateInterface, sudo_account: Keypair, test_account: Keypair):
    """
    Bootstrap the chain with initial setup:
    1. Transfer tokens from Alice to test account
    2. Create DOT and USDT assets
    3. Set asset metadata
    4. Mint initial tokens to both Alice and Bob
    5. Create WARP token
    6. Set WARP token metadata
    7. Mint WARP tokens to Alice, Bob, and Legend
    """
    try:
        print("\n=== Starting Bootstrap Process ===")
        
        # 1. Transfer tokens from Alice to test account
        print("\n1. Transferring initial tokens to test account...")
        transfer_call = substrate.compose_call(
            call_module='Balances',
            call_function='transfer_keep_alive',
            call_params={
                'dest': {'Id': test_account.ss58_address},
                'value': 10_000 * (10 ** 12)  # 10,000 tokens with 12 decimals
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=transfer_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"Transfer completed: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        # 2. Create assets
        print("\n2. Creating assets...")
        
        # Create DOT asset (ID: 1)
        create_dot_call = substrate.compose_call(
            call_module='Assets',
            call_function='create',
            call_params={
                'id': 1,
                'admin': sudo_account.ss58_address,
                'min_balance': 1
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=create_dot_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"DOT asset created: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        # Create USDT asset (ID: 2)
        create_usdt_call = substrate.compose_call(
            call_module='Assets',
            call_function='create',
            call_params={
                'id': 2,
                'admin': sudo_account.ss58_address,
                'min_balance': 1
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=create_usdt_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"USDT asset created: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        # 3. Set metadata for assets
        print("\n3. Setting asset metadata...")
        
        # Set DOT metadata (decimals: 9)
        set_dot_metadata_call = substrate.compose_call(
            call_module='Assets',
            call_function='set_metadata',
            call_params={
                'id': 1,
                'name': 'Polkadot',
                'symbol': 'DOT',
                'decimals': 9
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=set_dot_metadata_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"DOT metadata set: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        # Set USDT metadata (decimals: 6)
        set_usdt_metadata_call = substrate.compose_call(
            call_module='Assets',
            call_function='set_metadata',
            call_params={
                'id': 2,
                'name': 'Tether USD',
                'symbol': 'USDT',
                'decimals': 6
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=set_usdt_metadata_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"USDT metadata set: {receipt.extrinsic_hash}")
        
        print("Sleeping for 6 seconds")
        time.sleep(6)
        
        # 4. Mint tokens to both Alice and Bob
        print("\n4. Minting tokens to Alice, Bob, and Legend account...")
        
        # Create Bob's account
        bob_account = Keypair.create_from_uri("//Bob")
        
        # # Create Legend account from seed phrase
        legend_seed = "legend dad title ten sentence wealth script body grocery vivid vessel amazing"
        legend_account = Keypair.create_from_mnemonic(legend_seed)
        
        # Mint DOT tokens to Alice (100 million)
        mint_dot_alice_call = substrate.compose_call(
            call_module='Assets',
            call_function='mint',
            call_params={
                'id': 1,
                'beneficiary': sudo_account.ss58_address,
                'amount': 100_000_000 * (10 ** 9)  # 100 million DOT with 9 decimals
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=mint_dot_alice_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"DOT tokens minted to Alice: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        # Mint DOT tokens to Bob (100 million)
        mint_dot_bob_call = substrate.compose_call(
            call_module='Assets',
            call_function='mint',
            call_params={
                'id': 1,
                'beneficiary': bob_account.ss58_address,
                'amount': 100_000_000 * (10 ** 9)  # 100 million DOT with 9 decimals
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=mint_dot_bob_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"DOT tokens minted to Bob: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        # Mint DOT tokens to Legend account (100 million)
        mint_dot_legend_call = substrate.compose_call(
            call_module='Assets',
            call_function='mint',
            call_params={
                'id': 1,
                'beneficiary': legend_account.ss58_address,
                'amount': 100_000_000 * (10 ** 9)  # 100 million DOT with 9 decimals
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=mint_dot_legend_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"DOT tokens minted to Legend account: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        # Mint USDT tokens to Alice (100 million)
        mint_usdt_alice_call = substrate.compose_call(
            call_module='Assets',
            call_function='mint',
            call_params={
                'id': 2,
                'beneficiary': sudo_account.ss58_address,
                'amount': 100_000_000 * (10 ** 6)  # 100 million USDT with 6 decimals
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=mint_usdt_alice_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"USDT tokens minted to Alice: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        # Mint USDT tokens to Bob (100 million)
        mint_usdt_bob_call = substrate.compose_call(
            call_module='Assets',
            call_function='mint',
            call_params={
                'id': 2,
                'beneficiary': bob_account.ss58_address,
                'amount': 100_000_000 * (10 ** 6)  # 100 million USDT with 6 decimals
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=mint_usdt_bob_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"USDT tokens minted to Bob: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        # Mint USDT tokens to Legend account (100 million)
        mint_usdt_legend_call = substrate.compose_call(
            call_module='Assets',
            call_function='mint',
            call_params={
                'id': 2,
                'beneficiary': legend_account.ss58_address,
                'amount': 100_000_000 * (10 ** 6)  # 100 million USDT with 6 decimals
            }
        )
        
        extrinsic = substrate.create_signed_extrinsic(
            call=mint_usdt_legend_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"USDT tokens minted to Legend account: {receipt.extrinsic_hash}")
        
        print("\n=== Bootstrap Process Completed Successfully ===")
        
        # 5. Create WARP token (id=3)
        print("\n5. Creating WARP token...")
        create_warp_call = substrate.compose_call(
            call_module='Assets',
            call_function='create',
            call_params={
                'id': 3,
                'admin': sudo_account.ss58_address,
                'min_balance': 1
            }
        )
        extrinsic = substrate.create_signed_extrinsic(
            call=create_warp_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"WARP asset created: {receipt.extrinsic_hash}")
        time.sleep(2)

        # 6. Set WARP token metadata
        print("\n6. Setting WARP token metadata...")
        set_warp_metadata_call = substrate.compose_call(
            call_module='Assets',
            call_function='set_metadata',
            call_params={
                'id': 3,
                'name': 'Warp Token',
                'symbol': 'WARP',
                'decimals': 12
            }
        )
        extrinsic = substrate.create_signed_extrinsic(
            call=set_warp_metadata_call,
            keypair=sudo_account
        )
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"WARP metadata set: {receipt.extrinsic_hash}")
        time.sleep(2)

        # 7. Mint WARP tokens to Alice, Bob, and Legend
        print("\n7. Minting WARP tokens to Alice, Bob, and Legend account...")
        for acc, acc_name in [
            (sudo_account, 'Alice'),
            (bob_account, 'Bob'),
            (legend_account, 'Legend')
        ]:
            mint_warp_call = substrate.compose_call(
                call_module='Assets',
                call_function='mint',
                call_params={
                    'id': 3,
                    'beneficiary': acc.ss58_address,
                    'amount': 100_000_000 * (10 ** 12)  # 100 million WARP with 12 decimals
                }
            )
            extrinsic = substrate.create_signed_extrinsic(
                call=mint_warp_call,
                keypair=sudo_account
            )
            receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
            print(f"WARP tokens minted to {acc_name}: {receipt.extrinsic_hash}")
            time.sleep(2)
        
    except Exception as e:
        print(f"\nError during bootstrap: {e}")
        return False
    
    return True

def create_pool(
    substrate: SubstrateInterface,
    account: Keypair,
    base_asset_id: int,
    base_decimals: int,
    quote_asset_id: int,
    quote_decimals: int,
    taker_fee_rate: float,  # percentage (e.g., 0.03 for 0.03%)
    tick_size: int,
    lot_size: int,
    pool_decimals: int
):
    """
    Create a new pool in the HybridOrderbook pallet
    
    Args:
        substrate: SubstrateInterface instance
        account: Account to submit transaction
        base_asset_id: Base asset ID
        base_decimals: Base asset decimals
        quote_asset_id: Quote asset ID
        quote_decimals: Quote asset decimals
        taker_fee_rate: Taker fee rate in percentage (e.g., 0.03 for 0.03%)
        tick_size: Minimum price movement
        lot_size: Minimum trading amount
        pool_decimals: Pool token decimals
    """
    try:
        # Convert taker fee rate to Permill (percentage to parts per million)
        # e.g., 0.03% -> 300 Permill (0.03% = 0.0003 = 300/1,000,000)
        taker_fee_rate_permill = int(taker_fee_rate * 10000)
        
        print("\n=== Creating Pool ===")
        print(f"Base Asset ID: {base_asset_id}")
        print(f"Base Decimals: {base_decimals}")
        print(f"Quote Asset ID: {quote_asset_id}")
        print(f"Quote Decimals: {quote_decimals}")
        print(f"Taker Fee Rate: {taker_fee_rate}% ({taker_fee_rate_permill} Permill)")
        print(f"Tick Size: {tick_size}")
        print(f"Lot Size: {lot_size}")
        print(f"Pool Decimals: {pool_decimals}")

        base_asset_id = {'WithId': base_asset_id}
        quote_asset_id = {'WithId': quote_asset_id}
        
        # Compose the create_pool call
        call = substrate.compose_call(
            call_module='HybridOrderbook',
            call_function='create_pool',
            call_params={
                'base_asset': base_asset_id,
                'base_decimals': base_decimals,
                'quote_asset': quote_asset_id,
                'quote_decimals': quote_decimals,
                'taker_fee_rate': taker_fee_rate_permill,
                'tick_size': tick_size,
                'lot_size': lot_size,
                'pool_decimals': pool_decimals
            }
        )
        
        # Create and submit extrinsic
        extrinsic = substrate.create_signed_extrinsic(
            call=call,
            keypair=account
        )
        
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"\nPool creation submitted: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        return receipt.extrinsic_hash
        
    except Exception as e:
        print(f"Error creating pool: {e}")
        if hasattr(e, 'args') and len(e.args) > 0:
            print(f"Error details: {e.args[0]}")
        raise

def calculate_amounts(dot_amount: float, dot_price_in_usdt: float):
    """
    Calculate the proper amounts for liquidity provision considering decimals
    
    Args:
        dot_amount: Amount of DOT to provide
        dot_price_in_usdt: Current DOT price in USDT
    
    Returns:
        tuple: (base_amount, quote_amount) in their respective smallest units
    """
    DOT_DECIMALS = 9
    USDT_DECIMALS = 6
    
    # Convert DOT to smallest units
    dot_units = int(dot_amount * (10 ** DOT_DECIMALS))
    
    # Calculate USDT amount and convert to smallest units
    usdt_amount = dot_amount * dot_price_in_usdt
    usdt_units = int(usdt_amount * (10 ** USDT_DECIMALS))
    
    return dot_units, usdt_units

def get_dot_price():
    """
    Get current DOT price in USDT from CoinGecko API
    """
    try:
        cg = CoinGeckoAPI()
        # Get DOT price in USDT
        price = cg.get_price(ids='polkadot', vs_currencies='usd')
        return price['polkadot']['usd']
    except Exception as e:
        print(f"Error getting DOT price: {e}")
        return 4.0  # Fallback to default price

def add_liquidity(
    substrate: SubstrateInterface,
    account: Keypair,
    base_asset_id: int,
    quote_asset_id: int,
    base_amount: int,
    quote_amount: int,
    use_real_time_price: bool = False
):
    """
    Add liquidity to a pool in the HybridOrderbook pallet
    
    Args:
        substrate: SubstrateInterface instance
        account: Account to submit transaction
        base_asset_id: Base asset ID (DOT)
        quote_asset_id: Quote asset ID (USDT)
        base_amount: Amount of base asset to add (in smallest units)
        quote_amount: Amount of quote asset to add (in smallest units)
        use_real_time_price: Whether to use real-time price from CoinGecko
    """
    try:
        if use_real_time_price:
            # Get real-time DOT price
            dot_price = get_dot_price()
            print(f"\nCurrent DOT price from CoinGecko: ${dot_price}")
            
            # Recalculate quote amount based on real-time price
            dot_amount = base_amount / (10 ** 9)  # Convert to DOT
            quote_amount = int(dot_amount * dot_price * (10 ** 6))  # Convert to USDT smallest units
        
        # Calculate minimum amounts (99% of desired amounts to prevent slippage)
        base_amount_min = (base_amount * 99) // 100
        quote_amount_min = (quote_amount * 99) // 100
        
        print("\n=== Adding Liquidity ===")
        print(f"Base Asset (DOT) ID: {base_asset_id}")
        print(f"Quote Asset (USDT) ID: {quote_asset_id}")
        print(f"Base Amount: {base_amount} ({base_amount / (10 ** 9):.4f} DOT)")
        print(f"Quote Amount: {quote_amount} ({quote_amount / (10 ** 6):.4f} USDT)")
        print(f"Minimum Base Amount: {base_amount_min} ({base_amount_min / (10 ** 9):.4f} DOT)")
        print(f"Minimum Quote Amount: {quote_amount_min} ({quote_amount_min / (10 ** 6):.4f} USDT)")
        print(f"Effective Price: {(quote_amount / (10 ** 6)) / (base_amount / (10 ** 9)):.4f} USDT/DOT")
        
        # Format asset IDs for Substrate
        base_asset = {'WithId': base_asset_id}
        quote_asset = {'WithId': quote_asset_id}
        
        # Compose the add_liquidity call
        call = substrate.compose_call(
            call_module='HybridOrderbook',
            call_function='add_liquidity',
            call_params={
                'base_asset': base_asset,
                'quote_asset': quote_asset,
                'base_asset_desired': str(base_amount),
                'quote_asset_desired': str(quote_amount),
                'base_asset_min': str(base_amount_min),
                'quote_asset_min': str(quote_amount_min),
                'mint_to': account.ss58_address
            }
        )
        
        # Create and submit extrinsic
        extrinsic = substrate.create_signed_extrinsic(
            call=call,
            keypair=account
        )
        
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print(f"\nLiquidity addition submitted: {receipt.extrinsic_hash}")
        
        time.sleep(2)
        
        return receipt.extrinsic_hash
        
    except Exception as e:
        print(f"Error adding liquidity: {e}")
        if hasattr(e, 'args') and len(e.args) > 0:
            print(f"Error details: {e.args[0]}")
        raise

class NonceManager:
    def __init__(self, substrate: SubstrateInterface, account: Keypair):
        self.substrate = substrate
        self.account = account
        self.lock = Lock()
        self.current_nonce = None
        self._initialize_nonce()

    def _initialize_nonce(self):
        """Initialize the nonce from the chain"""
        with self.lock:
            self.current_nonce = self.substrate.get_account_nonce(self.account.ss58_address)

    def get_next_nonce(self):
        """Get the next nonce in a thread-safe way"""
        with self.lock:
            if self.current_nonce is None:
                self._initialize_nonce()
            nonce = self.current_nonce
            self.current_nonce += 1
            return nonce

def prefill_limit_orders(
    substrate: SubstrateInterface,
    bob: Keypair,
    base_asset: int,
    quote_asset: int,
    base_price: int,
    tick_spacing: int,
    amount_per_order: int,
    tick_range: int,
    total_orders: int
):
    """
    Bob이 미리 limit-order를 total_orders개 쌓는 함수 (양쪽 합산)
    """
    print(f"[Prefill] Bob이 limit-order {total_orders}개 미리 쌓는 중...")
    nonce_manager = NonceManager(substrate, bob)
    orders_placed = 0
    while orders_placed < total_orders:
        try:
            thread_base_price = base_price + random.randint(-tick_spacing, tick_spacing)
            nonce = nonce_manager.get_next_nonce()
            # Ask orders
            for i in range(tick_range):
                if orders_placed >= total_orders:
                    break
                ask_price = thread_base_price + ((i + 1) * tick_spacing)
                call = substrate.compose_call(
                    call_module='HybridOrderbook',
                    call_function='limit_order',
                    call_params={
                        'base_asset': {'WithId': base_asset},
                        'quote_asset': {'WithId': quote_asset},
                        'is_bid': False,
                        'price': str(ask_price),
                        'quantity': str(amount_per_order)
                    }
                )
                extrinsic = substrate.create_signed_extrinsic(
                    call=call,
                    keypair=bob,
                    nonce=nonce + i
                )
                try:
                    receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False)
                    print(f"[Prefill] Ask order submitted at price {ask_price}: {receipt.extrinsic_hash}")
                except Exception as e:
                    print(f"[Prefill] Failed to submit ask order: {e}")
                    continue
                orders_placed += 1
                time.sleep(0.2)
            # Bid orders
            for i in range(tick_range):
                if orders_placed >= total_orders:
                    break
                bid_price = thread_base_price - ((i + 1) * tick_spacing)
                call = substrate.compose_call(
                    call_module='HybridOrderbook',
                    call_function='limit_order',
                    call_params={
                        'base_asset': {'WithId': base_asset},
                        'quote_asset': {'WithId': quote_asset},
                        'is_bid': True,
                        'price': str(bid_price),
                        'quantity': str(amount_per_order)
                    }
                )
                extrinsic = substrate.create_signed_extrinsic(
                    call=call,
                    keypair=bob,
                    nonce=nonce + tick_range + i
                )
                try:
                    receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False)
                    print(f"[Prefill] Bid order submitted at price {bid_price}: {receipt.extrinsic_hash}")
                except Exception as e:
                    print(f"[Prefill] Failed to submit bid order: {e}")
                    continue
                orders_placed += 1
                time.sleep(0.2)
            time.sleep(0.5)
        except Exception as e:
            print(f"[Prefill] Error: {e}")
            time.sleep(1)
            nonce_manager._initialize_nonce()
    print(f"[Prefill] Bob이 limit-order {total_orders}개 미리 쌓기 완료!")


def stress_test(
    substrate: SubstrateInterface,
    alice: Keypair,
    bob: Keypair,
    base_asset: int,
    quote_asset: int,
    base_price: int,
    tick_spacing: int,
    amount_per_order: int,
    tick_range: int,
    num_limit_threads: int = 2,
    num_market_threads: int = 2,
    prefill_limit_orders_count: int = 100
):
    """
    Bob: limit_order(10개씩), Alice: market_order(1개씩), market-order는 limit-order가 충분히 쌓인 후 시작
    """
    # 1. Bob이 limit-order를 충분히 미리 쌓음
    prefill_limit_orders(
        substrate=substrate,
        bob=bob,
        base_asset=base_asset,
        quote_asset=quote_asset,
        base_price=base_price,
        tick_spacing=tick_spacing,
        amount_per_order=amount_per_order,
        tick_range=tick_range,
        total_orders=prefill_limit_orders_count
    )

    alice_nonce_manager = NonceManager(substrate, alice)
    bob_nonce_manager = NonceManager(substrate, bob)

    def bob_limit_worker(thread_id):
        print(f"[Bob-Limit] Starting worker thread {thread_id}")
        while True:
            try:
                thread_base_price = base_price + random.randint(-tick_spacing, tick_spacing)
                nonce = bob_nonce_manager.get_next_nonce()
                # Ask orders (10개)
                for i in range(10):
                    ask_price = thread_base_price + ((i + 1) * tick_spacing)
                    call = substrate.compose_call(
                        call_module='HybridOrderbook',
                        call_function='limit_order',
                        call_params={
                            'base_asset': {'WithId': base_asset},
                            'quote_asset': {'WithId': quote_asset},
                            'is_bid': False,
                            'price': str(ask_price),
                            'quantity': str(amount_per_order)
                        }
                    )
                    extrinsic = substrate.create_signed_extrinsic(
                        call=call,
                        keypair=bob,
                        nonce=nonce + i
                    )
                    try:
                        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False, timeout=10)
                        print(f"[Bob-Limit][{thread_id}] Ask order submitted at price {ask_price}: {receipt.extrinsic_hash}")
                    except Exception as e:
                        print(f"[Bob-Limit][{thread_id}] Failed to submit ask order: {e}")
                        continue
                    time.sleep(0.5)
                # Bid orders (10개)
                for i in range(10):
                    bid_price = thread_base_price - ((i + 1) * tick_spacing)
                    call = substrate.compose_call(
                        call_module='HybridOrderbook',
                        call_function='limit_order',
                        call_params={
                            'base_asset': {'WithId': base_asset},
                            'quote_asset': {'WithId': quote_asset},
                            'is_bid': True,
                            'price': str(bid_price),
                            'quantity': str(amount_per_order)
                        }
                    )
                    extrinsic = substrate.create_signed_extrinsic(
                        call=call,
                        keypair=bob,
                        nonce=nonce + 10 + i
                    )
                    try:
                        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False, timeout=10)
                        print(f"[Bob-Limit][{thread_id}] Bid order submitted at price {bid_price}: {receipt.extrinsic_hash}")
                    except Exception as e:
                        print(f"[Bob-Limit][{thread_id}] Failed to submit bid order: {e}")
                        continue
                    time.sleep(0.5)
                time.sleep(1.0)
            except Exception as e:
                print(f"[Bob-Limit][{thread_id}] Error: {e}")
                time.sleep(1)
                bob_nonce_manager._initialize_nonce()

    def alice_market_worker(thread_id):
        print(f"[Alice-Market] Starting worker thread {thread_id}")
        while True:
            try:
                nonce = alice_nonce_manager.get_next_nonce()
                is_bid = random.choice([True, False])
                call = substrate.compose_call(
                    call_module='HybridOrderbook',
                    call_function='market_order',
                    call_params={
                        'base_asset': {'WithId': base_asset},
                        'quote_asset': {'WithId': quote_asset},
                        'quantity': '1000000000',  # 항상 1개씩만 주문
                        'is_bid': True
                    }
                )
                extrinsic = substrate.create_signed_extrinsic(
                    call=call,
                    keypair=alice,
                    nonce=nonce
                )
                try:
                    receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False)
                    print(f"[Alice-Market][{thread_id}] Market order submitted (is_bid={is_bid}): {receipt.extrinsic_hash}")
                except Exception as e:
                    print(f"[Alice-Market][{thread_id}] Failed to submit market order: {e}")
                    continue
                time.sleep(1.0)
            except Exception as e:
                print(f"[Alice-Market][{thread_id}] Error: {e}")
                time.sleep(1)
                alice_nonce_manager._initialize_nonce()

    # Start Bob's limit-order threads
    for i in range(num_limit_threads):
        t = threading.Thread(target=bob_limit_worker, args=(i,), daemon=True)
        t.start()
        print(f"Started Bob limit-order thread {i}")
    # Start Alice's market-order threads
    for i in range(num_market_threads):
        t = threading.Thread(target=alice_market_worker, args=(i,), daemon=True)
        t.start()
        print(f"Started Alice market-order thread {i}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping stress test...")
        # Threads will automatically stop when main program exits

def main():
    parser = argparse.ArgumentParser(description='Substrate chain operations')
    
    parser.add_argument('--ws-url', type=str, default="ws://127.0.0.1:9944",
                        help='WebSocket URL of the node')
    parser.add_argument('--account-seed', type=str, default="//Alice",
                        help='Account seed or mnemonic (default: //Alice for dev account)')
    parser.add_argument('--base-asset', type=int,
                        help='Base asset ID')
    parser.add_argument('--quote-asset', type=int,
                        help='Quote asset ID')
    parser.add_argument('--base-price', type=int,
                        help='Base price (in integer format with decimals)')
    parser.add_argument('--tick-count', type=int, default=10,
                        help='Number of orders to create on each side')
    parser.add_argument('--tick-spacing', type=int,
                        help='Spacing between ticks (in integer format with decimals)')
    parser.add_argument('--amount', type=int,
                        help='Amount per order (in integer format with decimals)')
    parser.add_argument('--bootstrap', action='store_true',
                        help='Run bootstrap process')
    parser.add_argument('--test-account-seed', type=str,
                        help='Test account seed for bootstrap')
    parser.add_argument('--create-pool', action='store_true',
                        help='Create a new pool')
    parser.add_argument('--base-decimals', type=int,
                        help='Base asset decimals')
    parser.add_argument('--quote-decimals', type=int,
                        help='Quote asset decimals')
    parser.add_argument('--taker-fee-rate', type=float,
                        help='Taker fee rate in percentage (e.g., 0.03 for 0.03%%)')
    parser.add_argument('--tick-size', type=int,
                        help='Minimum price movement')
    parser.add_argument('--lot-size', type=int,
                        help='Minimum trading amount')
    parser.add_argument('--pool-decimals', type=int,
                        help='Pool token decimals')
    parser.add_argument('--add-liquidity', action='store_true',
                        help='Add liquidity to a pool')
    parser.add_argument('--dot-amount', type=float,
                        help='Amount of DOT to add as liquidity')
    parser.add_argument('--dot-price', type=float, default=4.0,
                        help='Current DOT price in USDT (default: 4.0)')
    parser.add_argument('--use-real-time-price', action='store_true',
                        help='Use real-time DOT price from CoinGecko')
    parser.add_argument('--stress-test', action='store_true',
                        help='Run stress test with multiple threads')
    parser.add_argument('--tick-range', type=int, default=10,
                        help='Number of ticks to create on each side for stress test')
    
    args = parser.parse_args()
    
    # Connect to node
    substrate = SubstrateInterface(
        url=args.ws_url
    )
    
    if args.stress_test:
        if not all([args.base_asset, args.quote_asset, args.base_price, args.tick_spacing, args.amount]):
            print("Error: All parameters (--base-asset, --quote-asset, --base-price, --tick-spacing, --amount) are required for stress test")
            return
        alice = Keypair.create_from_uri("//Alice")
        bob = Keypair.create_from_uri("//Bob")
        stress_test(
            substrate=substrate,
            alice=alice,
            bob=bob,
            base_asset=args.base_asset,
            quote_asset=args.quote_asset,
            base_price=args.base_price,
            tick_spacing=args.tick_spacing,
            amount_per_order=args.amount,
            tick_range=args.tick_range,
            num_limit_threads=2,  # 필요시 조정
            num_market_threads=2,  # 필요시 조정
            prefill_limit_orders_count=100  # 필요시 조정
        )
        return
    elif args.create_pool:
        if not all([args.base_asset, args.base_decimals, 
                   args.quote_asset, args.quote_decimals,
                   args.taker_fee_rate, args.tick_size,
                   args.lot_size, args.pool_decimals]):
            print("Error: All pool parameters are required for pool creation")
            return
            
        account = Keypair.create_from_uri(args.account_seed)
        create_pool(
            substrate=substrate,
            account=account,
            base_asset_id=args.base_asset,
            base_decimals=args.base_decimals,
            quote_asset_id=args.quote_asset,
            quote_decimals=args.quote_decimals,
            taker_fee_rate=args.taker_fee_rate,
            tick_size=args.tick_size,
            lot_size=args.lot_size,
            pool_decimals=args.pool_decimals
        )
    elif args.add_liquidity:
        if not all([args.base_asset, args.quote_asset, args.dot_amount]):
            print("Error: Required parameters: --base-asset, --quote-asset, --dot-amount")
            return
            
        # Calculate amounts based on DOT amount and price
        base_amount, quote_amount = calculate_amounts(args.dot_amount, args.dot_price)
            
        account = Keypair.create_from_uri(args.account_seed)
        add_liquidity(
            substrate=substrate,
            account=account,
            base_asset_id=args.base_asset,
            quote_asset_id=args.quote_asset,
            base_amount=base_amount,
            quote_amount=quote_amount,
            use_real_time_price=args.use_real_time_price
        )
    elif args.bootstrap:
        if not args.test_account_seed:
            print("Error: --test-account-seed is required for bootstrap")
            return
            
        sudo_account = Keypair.create_from_uri("//Alice")
        test_account = Keypair.create_from_uri(args.test_account_seed)
        bootstrap_chain(substrate, sudo_account, test_account)
    else:
        # Run limit order creation if all required parameters are provided
        if all([args.base_asset, args.quote_asset, args.base_price, args.tick_spacing, args.amount]):
            # Always use Alice's account for limit orders
            account = Keypair.create_from_uri("//Alice")
            create_limit_orders(
                substrate=substrate,
                account=account,
                base_asset=args.base_asset,
                quote_asset=args.quote_asset,
                base_price=args.base_price,
                tick_count=args.tick_count,
                tick_spacing=args.tick_spacing,
                amount_per_order=args.amount
            )
        else:
            print("Error: All parameters (--base-asset, --quote-asset, --base-price, --tick-spacing, --amount) are required for limit order creation")

if __name__ == "__main__":
    # health_check()
    main()