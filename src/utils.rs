use alloc::vec::Vec;

use crate::AppSW;

/// BIP32 path stored as an array of [`u32`].
#[derive(Default)]
pub struct Bip32Path(Vec<u32>);

impl AsRef<[u32]> for Bip32Path {
    fn as_ref(&self) -> &[u32] {
        &self.0
    }
}

impl TryFrom<&[u8]> for Bip32Path {
    type Error = AppSW;

    /// Constructs a [`Bip32Path`] from a given byte array.
    ///
    /// This method will return an error in the following cases:
    /// - the input array is empty,
    /// - the number of bytes in the input array is not a multiple of 4,
    ///
    /// # Arguments
    ///
    /// * `data` - Encoded BIP32 path. First byte is the length of the path, as encoded by ragger.
    fn try_from(data: &[u8]) -> Result<Self, Self::Error> {
        // Check data length
        if data.is_empty() // At least the length byte is required
            || (data[0] as usize * 4 != data.len() - 1)
        {
            return Err(AppSW::WrongApduLength);
        }

        Ok(Bip32Path(
            data[1..]
                .chunks(4)
                .map(|chunk| u32::from_be_bytes(chunk.try_into().unwrap()))
                .collect(),
        ))
    }
}

// Helper function to convert hex string to byte array
pub fn hex_to_bytes(hex: &str) -> [u8; 32] {
    let mut bytes = [0u8; 32];
    for (i, byte) in hex.as_bytes().chunks(2).enumerate() {
        bytes[i] = u8::from_str_radix(core::str::from_utf8(byte).unwrap_or("00"), 16).unwrap_or(0);
    }
    bytes
}

/// Pads a byte array to 32 bytes (right-aligned) as per Ethereum ABI encoding rules
pub fn pad_to_32_bytes(input: &[u8]) -> [u8; 32] {
    let mut padded = [0u8; 32];
    if input.len() <= 32 {
        // Copy the input bytes to the end of the padded array (right-aligned)
        padded[32 - input.len()..].copy_from_slice(input);
    } else {
        // If input is longer than 32 bytes (shouldn't happen), truncate
        padded.copy_from_slice(&input[0..32]);
    }
    padded
}

/// Encodes data according to Ethereum ABI encoding rules
pub fn abi_encode(elements: &[&[u8]]) -> Vec<u8> {
    let mut encoded = Vec::new();
    
    // Concatenate all elements, padding each to 32 bytes
    for element in elements {
        if element.len() == 32 {
            // Element is already 32 bytes, just add it
            encoded.extend_from_slice(element);
        } else {
            // Pad the element to 32 bytes
            encoded.extend_from_slice(&pad_to_32_bytes(element));
        }
    }
    
    encoded
}
