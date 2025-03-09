/*****************************************************************************
 *   Ledger App Boilerplate Rust.
 *   (c) 2023 Ledger SAS.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *****************************************************************************/
use crate::AppSW;
use alloc::vec::Vec;
use ledger_device_sdk::hash::{sha3::Keccak256, HashInit};
use ledger_device_sdk::io::Comm;
use serde::Deserialize;
use serde_json_core::from_slice;
use crate::utils::{hex_to_bytes, abi_encode};
use hex;

#[derive(Deserialize)]
pub struct SafeTx {
    pub to: [u8; 20],
    pub value: u64,
    #[serde(with = "hex::serde")]
    pub data: Vec<u8>,
    pub operation: u8,
    pub safe_tx_gas: u64,
    pub base_gas: u64,
    pub gas_price: u64,
    #[serde(with = "hex::serde")]
    pub gas_token: [u8; 20],
    #[serde(with = "hex::serde")]
    pub refund_receiver: [u8; 20],
    pub nonce: u64,
}

pub struct SafeTxContext {
    raw_tx: Vec<u8>,
    chain_id: u64,
    safe_address: [u8; 20],
    review_finished: bool,
}

impl SafeTxContext {
    pub fn new() -> SafeTxContext {
        SafeTxContext {
            raw_tx: Vec::new(),
            chain_id: 0,
            safe_address: [0u8; 20],
            review_finished: false,
        }
    }

    fn reset(&mut self) {
        self.raw_tx.clear();
        self.chain_id = 0;
        self.safe_address = [0u8; 20];
        self.review_finished = false;
    }

    fn calculate_domain_hash(&self) -> [u8; 32] {
        let mut keccak = Keccak256::new();
        let mut domain_hash = [0u8; 32];
        
        let domain_separator_typehash = hex_to_bytes("47e79534a245952e8b16893a336b85a3d9ea9fa8c573f3d803afb92a79469218");
        
        // Convert chain_id to bytes
        let chain_id_bytes = self.chain_id.to_be_bytes();
        
        // ABI encode the domain data
        let domain_data = abi_encode(&[
            &domain_separator_typehash,
            &chain_id_bytes,
            &self.safe_address,
        ]);
        
        let _ = keccak.hash(&domain_data, &mut domain_hash);
        domain_hash
    }

    fn calculate_tx_hash(&self, tx: &SafeTx) -> Result<[u8; 32], AppSW> {
        let mut keccak = Keccak256::new();
        let mut tx_hash = [0u8; 32];
        let mut data_hash = [0u8; 32];

        // Hash the transaction data
        let _ = keccak.hash(&tx.data, &mut data_hash);
        
        let safe_tx_typehash = hex_to_bytes("bb8310d486368db6bd6f849402fdd73ad53d316b5a4b2644ad6efe0f941286d8");
        
        // Convert numeric values to bytes
        let value_bytes = tx.value.to_be_bytes();
        let operation_bytes = [tx.operation];
        let safe_tx_gas_bytes = tx.safe_tx_gas.to_be_bytes();
        let base_gas_bytes = tx.base_gas.to_be_bytes();
        let gas_price_bytes = tx.gas_price.to_be_bytes();
        let nonce_bytes = tx.nonce.to_be_bytes();
        
        // ABI encode the transaction data
        let tx_data = abi_encode(&[
            &safe_tx_typehash,
            &tx.to,
            &value_bytes,
            &data_hash,
            &operation_bytes,
            &safe_tx_gas_bytes,
            &base_gas_bytes,
            &gas_price_bytes,
            &tx.gas_token,
            &tx.refund_receiver,
            &nonce_bytes,
        ]);
        
        // Create a fresh Keccak256 instance for the tx_hash calculation
        let mut fresh_keccak = Keccak256::new();
        let _ = fresh_keccak.hash(&tx_data, &mut tx_hash);
        
        Ok(tx_hash)
    }

    fn calculate_safe_tx_hash(&self, tx: &SafeTx) -> Result<[u8; 32], AppSW> {
        let mut keccak = Keccak256::new();
        let mut safe_tx_hash = [0u8; 32];
        
        let domain_hash = self.calculate_domain_hash();
        let tx_hash = self.calculate_tx_hash(tx)?;
        
        // Prepare the data for the safe transaction hash
        let mut safe_tx_hash_data = Vec::new();
        safe_tx_hash_data.extend_from_slice(&[0x19, 0x01]);
        safe_tx_hash_data.extend_from_slice(&domain_hash);
        safe_tx_hash_data.extend_from_slice(&tx_hash);
        
        let _ = keccak.hash(&safe_tx_hash_data, &mut safe_tx_hash);
        
        Ok(safe_tx_hash)
    }
}

pub fn get_safe_tx_hash(
    comm: &mut Comm,
    chunk: u8,
    more: bool,
    ctx: &mut SafeTxContext,
) -> Result<(), AppSW> {
    let data = comm.get_data().map_err(|_| AppSW::WrongApduLength)?;
    
    if chunk == 0 {
        // First chunk contains chain_id and safe_address
        if data.len() != 28 { // 8 bytes for chain_id + 20 bytes for address
            return Err(AppSW::WrongApduLength);
        }
        ctx.reset();
        ctx.chain_id = u64::from_be_bytes(data[0..8].try_into().unwrap());
        ctx.safe_address.copy_from_slice(&data[8..28]);
        Ok(())
    } else {
        // Append transaction data
        ctx.raw_tx.extend_from_slice(data);

        if !more {
            // Parse and process the complete transaction
            let parse_result = from_slice::<SafeTx>(&ctx.raw_tx);
            match parse_result {
                Ok((tx, _)) => {
                    // Calculate the Safe transaction hash
                    match ctx.calculate_safe_tx_hash(&tx) {
                        Ok(safe_tx_hash) => {
                            // Return the hash
                            comm.append(&safe_tx_hash);
                            ctx.review_finished = true;
                            Ok(())
                        },
                        Err(_e) => {
                            // Convert the error to a string representation based on its value
                            let _error_str = match _e {
                                AppSW::Deny => "Deny",
                                AppSW::WrongP1P2 => "WrongP1P2",
                                AppSW::InsNotSupported => "InsNotSupported",
                                AppSW::ClaNotSupported => "ClaNotSupported",
                                AppSW::TxDisplayFail => "TxDisplayFail",
                                AppSW::AddrDisplayFail => "AddrDisplayFail",
                                AppSW::TxWrongLength => "TxWrongLength",
                                AppSW::TxParsingFail => "TxParsingFail",
                                AppSW::TxHashFail => "TxHashFail",
                                AppSW::TxSignFail => "TxSignFail",
                                AppSW::KeyDeriveFail => "KeyDeriveFail",
                                AppSW::VersionParsingFail => "VersionParsingFail",
                                AppSW::WrongApduLength => "WrongApduLength",
                                AppSW::Ok => "Ok",
                            };
                            Err(_e)
                        }
                    }
                },
                Err(_e) => {
                    Err(AppSW::TxParsingFail)
                }
            }
        } else {
            Ok(())
        }
    }
}