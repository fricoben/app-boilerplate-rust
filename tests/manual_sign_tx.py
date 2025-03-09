import pytest
from application_client.boilerplate_command_sender import BoilerplateCommandSender, Errors
from ragger.navigator import NavInsID, NavIns
from application_client.boilerplate_transaction import Transaction
from application_client.boilerplate_response_unpacker import unpack_get_public_key_response, unpack_sign_tx_response
from utils import check_signature_validity

# Import the base conftest
pytest_plugins = ("ragger.conftest.base_conftest", )


def test_manual_regular_tx_review(backend, navigator, firmware):
    """Display a regular transaction on screen for manual review."""
    print("\n" + "="*80)
    print("REGULAR TRANSACTION REVIEW")
    print("="*80)
    
    # Use the app interface instead of raw interface
    client = BoilerplateCommandSender(backend)
    
    # The path used for this test
    path = "m/44'/1'/0'/0/0"
    print(f"Derivation path: {path}")

    # First get the public key
    print("\nGetting public key...")
    rapdu = client.get_public_key(path=path)
    _, public_key, _, _ = unpack_get_public_key_response(rapdu.data)
    print(f"Public key: {public_key.hex()}")

    # Create the transaction
    transaction = Transaction(
        nonce=1,
        coin="ETH",
        value=401346,
        to="de0b295669a9fd93d5f28d9ec85e40f4cb697bae",
        memo="<3 from Kim"
    )
    
    # Print transaction details for reference
    print("\nTRANSACTION DETAILS:")
    print(f"Nonce: {transaction.nonce}")
    print(f"Coin: {transaction.coin}")
    print(f"Value: {transaction.value}")
    print(f"To: 0x{transaction.to}")
    print(f"Memo: {transaction.memo}")
    
    # Enable display of transaction memo (NBGL devices only)
    if not firmware.device.startswith("nano"):
        print("\nConfiguring display settings to show memo...")
        navigator.navigate([NavInsID.USE_CASE_HOME_SETTINGS,
                          NavIns(NavInsID.TOUCH, (200, 113)),
                          NavInsID.USE_CASE_SUB_SETTINGS_EXIT],
                          screen_change_before_first_instruction=False,
                          screen_change_after_last_instruction=False)

    # Serialize and send the transaction
    serialized_tx = transaction.serialize()
    print(f"\nSerialized transaction: {serialized_tx}")
    
    print("\nSending transaction to device...")
    print("Please review the transaction details on your device and approve/reject.")
    print("Waiting for your response...")
    
    with client.sign_tx(path=path, transaction=serialized_tx):
        # Here we don't use scenario_navigator.review_approve()
        # Instead, we wait for manual user interaction
        input("\nPress Enter after you've approved/rejected the transaction on the device...")

    try:
        # Get and verify the signature
        response = client.get_async_response()
        if response:
            _, signature, _ = unpack_sign_tx_response(response.data)
            print("\nTransaction was approved!")
            print(f"Signature: {signature.hex()}")
            
            # Verify the signature
            if check_signature_validity(public_key, signature, serialized_tx):
                print("✅ Signature verification successful!")
            else:
                print("❌ Signature verification failed!")
        else:
            print("\n❌ No response received - transaction might have been rejected")
            
    except Exception as e:
        print(f"\n❌ Error processing response: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    # Run the test directly with pytest
    pytest.main([__file__, "-v", "-s", "--device", "stax"]) 