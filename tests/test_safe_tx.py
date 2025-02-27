from application_client.boilerplate_command_sender import BoilerplateCommandSender
import json
import binascii
import sys
import time

def test_get_safe_tx_hash(backend):
    """Test Safe transaction hash calculation."""
    client = BoilerplateCommandSender(backend)
    
    # Test data
    chain_id = 1  # Ethereum mainnet
    safe_address = bytes.fromhex("88Ffb774b8583c1C9A2b71b7391861c0Be253993")
    
    # Example Safe transaction
    safe_tx = {
        "to": [int(x) for x in bytes.fromhex("de0b295669a9fd93d5f28d9ec85e40f4cb697bae")],  # byte array
        "value": 123000000000000000,  # u64
        "data": "",  # empty string for empty data
        "operation": 0,  # u8
        "safe_tx_gas": 0,  # u64
        "base_gas": 0,  # u64
        "gas_price": 0,  # u64
        "gas_token": "0000000000000000000000000000000000000000",  # hex string without 0x
        "refund_receiver": "0000000000000000000000000000000000000000",  # hex string without 0x
        "nonce": 1  # u64
    }
    
    print("\n" + "="*80)
    print("TEST DATA (MATCHING safe_hashes.sh TEST DATA)")
    print("="*80)
    print(f"Chain ID: {chain_id}")
    print(f"Safe Address: 0x{binascii.hexlify(safe_address).decode()}")
    print(f"To: 0x{''.join([f'{x:02x}' for x in safe_tx['to']])}")
    print(f"Value: {safe_tx['value']}")
    print(f"Data: {safe_tx['data'] if safe_tx['data'] else '0x'}")
    print(f"Operation: {safe_tx['operation']}")
    print(f"Safe Tx Gas: {safe_tx['safe_tx_gas']}")
    print(f"Base Gas: {safe_tx['base_gas']}")
    print(f"Gas Price: {safe_tx['gas_price']}")
    print(f"Gas Token: 0x{safe_tx['gas_token']}")
    print(f"Refund Receiver: 0x{safe_tx['refund_receiver']}")
    print(f"Nonce: {safe_tx['nonce']}")
    print("="*80 + "\n")
    
    # First chunk: chain_id and safe_address
    first_chunk = chain_id.to_bytes(8, 'big') + safe_address
    
    # Send first chunk
    print("Sending first chunk (chain_id + safe_address)...")
    response = client.get_safe_tx_hash(chunk=0, more=True, data=first_chunk)
    
    # Serialize transaction data and print for debugging
    tx_json = json.dumps(safe_tx, separators=(',', ':'))  # compact JSON
    print(f"Sending JSON: {tx_json}")
    tx_bytes = tx_json.encode()
    
    # Send transaction data
    chunk_size = 255
    for i in range(0, len(tx_bytes), chunk_size):
        chunk = tx_bytes[i:i+chunk_size]
        more = i + chunk_size < len(tx_bytes)
        print(f"Sending chunk {i//chunk_size + 1}/{(len(tx_bytes) + chunk_size - 1)//chunk_size}, more={more}, size={len(chunk)}")
        response = client.get_safe_tx_hash(chunk=1, more=more, data=chunk)
    
    # The final response should contain the Safe transaction hash
    print("\n" + "="*80)
    print("RESULT")
    print("="*80)
    
    actual_hash = response.data.hex()
    
    # Add a small delay to ensure device has time to process and output logs
    time.sleep(0.5)
    
    # Now compare hashes
    try:
        # Compare with known hash from safe_hashes.sh script
        expected_hash = "938061ada63cd3e0fa939ef7881e8bffcf1bc1ebc0904ba6ed69d0a5f46db575"
        
        print("\n" + "="*80)
        print("HASH COMPARISON")
        print("="*80)
        print(f"Expected hash: 0x{expected_hash}")
        print(f"Actual hash:   0x{actual_hash}")
        
        if actual_hash == expected_hash:
            print("\n✅ HASH MATCH! The calculated hash matches the expected hash.")
        else:
            print("\n❌ HASH MISMATCH! The calculated hash does not match the expected hash.")
            
            # Print detailed hex comparison to identify differences
            print("\nDetailed comparison (byte by byte):")
            for i in range(0, len(expected_hash), 2):
                expected_byte = expected_hash[i:i+2]
                actual_byte = actual_hash[i:i+2]
                match = "✓" if expected_byte == actual_byte else "✗"
                print(f"Byte {i//2}: {expected_byte} vs {actual_byte} {match}")
            
        assert actual_hash == expected_hash, f"Hash mismatch! Expected: {expected_hash}, Got: {actual_hash}"
    except Exception as e:
        print(f"Error during hash comparison: {e}")
        raise
    

def run_test_directly():
    """Run the test directly without pytest."""
    from ragger.backend import BackendFactory
    
    print("Initializing Stax backend...")
    backend = BackendFactory.get_backend(
        app_path="/app/build/stax/bin/app.elf",
        model="stax",
        display=True
    )
    
    try:
        print("Running test...")
        test_get_safe_tx_hash(backend)
        print("\nTest completed successfully!")
    finally:
        backend.stop()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--direct":
        # Run the test directly without pytest
        run_test_directly()
    else:
        print("To run this test directly, use: python tests/test_safe_tx.py --direct")
        # When running with pytest, this code won't execute 