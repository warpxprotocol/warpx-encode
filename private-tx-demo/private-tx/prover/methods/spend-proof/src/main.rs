use risc0_zkvm::guest::env;
use sha2::{Digest, Sha256};

fn compute_note_commitment(note_data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(note_data);
    let result = hasher.finalize();
    result.into()
}

fn verify_signature(public_key: &[u8], message: &[u8], signature: &[u8]) -> bool {
    // For demo purposes, we'll use a simple hash-based signature verification
    let mut hasher = Sha256::new();
    hasher.update(public_key);
    hasher.update(message);
    let expected_signature = hasher.finalize();
    signature == expected_signature.as_slice()
}

// TODO
// nullifiers, viewing_key
#[derive(serde::Serialize, serde::Deserialize)]
struct SpendInput {
    note_data: Vec<u8>,
    note_commitment: [u8; 32],
    public_key: Vec<u8>,
    signature: Vec<u8>,
    amount: u64,
    spend_amount: u64,
}

fn main() {
    // Read the input data from the host
    let input: SpendInput = env::read();
    
    // Read the valid commitments set from the host
    let valid_commitments: Vec<[u8; 32]> = env::read();
    
    // Verify the note commitment is in the valid set
    let found = valid_commitments.iter().any(|c| c == &input.note_commitment);
    assert!(found, "Note commitment not in valid set");
    
    // Verify the note commitment
    let computed_commitment = compute_note_commitment(&input.note_data);
    assert_eq!(computed_commitment, input.note_commitment, "Invalid note commitment");
    
    // Verify the signature
    let message = [input.note_commitment.as_slice(), input.amount.to_le_bytes().as_slice()].concat();
    assert!(verify_signature(&input.public_key, &message, &input.signature), "Invalid signature");
    
    // Verify the amount is sufficient
    assert!(input.amount >= input.spend_amount, "Insufficient balance");
    
    // Compute the new note commitment
    let new_note_data = [input.note_data.as_slice(), input.spend_amount.to_le_bytes().as_slice()].concat();
    let new_commitment = compute_note_commitment(&new_note_data);
    
    // Write the new commitment back to the host
    env::commit(&new_commitment);
} 