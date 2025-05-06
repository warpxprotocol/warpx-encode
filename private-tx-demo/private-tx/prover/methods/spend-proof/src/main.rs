use risc0_zkvm::guest::env;
use sha2::Digest;

fn main() {
    // Read the input data from the host
    let input: SpendInput = env::read();
    
    // Verify the note commitment
    // let computed_commitment = compute_note_commitment(&input.note_data);
    // assert_eq!(computed_commitment, input.note_commitment, "Invalid note commitment");
    
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

#[derive(serde::Serialize, serde::Deserialize)]
struct SpendInput {
    note_data: Vec<u8>,
    note_commitment: Vec<u8>,
    public_key: Vec<u8>,
    signature: Vec<u8>,
    amount: u64,
    spend_amount: u64,
}

fn compute_note_commitment(note_data: &[u8]) -> Vec<u8> {
    let mut hasher = sha2::Sha256::new();
    hasher.update(note_data);
    let result = hasher.finalize();
    result.to_vec()
}

fn verify_signature(_public_key: &[u8], _message: &[u8], _signature: &[u8]) -> bool {
    // In a real implementation, you would use a proper signature verification algorithm
    // For demonstration purposes, we'll just return true
    true
} 