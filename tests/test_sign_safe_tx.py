import pytest
import json
import binascii
from application_client.boilerplate_command_sender import BoilerplateCommandSender, Errors
from application_client.boilerplate_response_unpacker import unpack_get_public_key_response, unpack_sign_tx_response
from utils import check_signature_validity

def test_sign_safe_tx(backend, scenario_navigator, firmware):
    """Test signing a Safe transaction with manual approval on the emulator."""
    if firmware.device.startswith("nano"):
        pytest.skip("Skipping this test for Nano devices")
    
    # Use the app interface instead of raw interface
    client = BoilerplateCommandSender(backend)
    
    # The path used for signing
    path = "m/44'/60'/0'/0/0"
    
    # Test data
    chain_id = 1  # Ethereum mainnet
    safe_address = bytes.fromhex("88Ffb774b8583c1C9A2b71b7391861c0Be253993")
    
    # Example Safe transaction
    safe_tx = {
        "to": [int(x) for x in bytes.fromhex("de0b295669a9fd93d5f28d9ec85e40f4cb697bae")],
        "value": 123000000000000000,  # 0.123 ETH
        "data": "",
        "operation": 0,
        "safe_tx_gas": 0,
        "base_gas": 0,
        "gas_price": 0,
        "gas_token": "0000000000000000000000000000000000000000",
        "refund_receiver": "0000000000000000000000000000000000000000",
        "nonce": 1
    }

    # First get the public key
    rapdu = client.get_public_key(path=path)
    _, public_key, _, _ = unpack_get_public_key_response(rapdu.data)

    # Prepare transaction data
    transaction_data = bytearray()
    transaction_data.extend(chain_id.to_bytes(8, 'big'))
    transaction_data.extend(safe_address)
    tx_json = json.dumps(safe_tx, separators=(',', ':'))
    transaction_data.extend(tx_json.encode())

    print(f"Transaction data: {bytes(transaction_data)}")
    # Send the sign transaction instruction and wait for approval
    with client.sign_tx(path=path, transaction=bytes(transaction_data)):
        scenario_navigator.review_approve()

    # Get and verify the signature
    response = client.get_async_response().data
    _, der_sig, _ = unpack_sign_tx_response(response)
    
    # Verify the signature
    assert check_signature_validity(public_key, der_sig, bytes(transaction_data))

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--device", "stax", "--display"]) 