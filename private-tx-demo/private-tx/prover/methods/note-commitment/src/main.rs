use risc0_zkvm::guest::env;
use sha2::Digest;
use bincode;

#[derive(serde::Serialize, serde::Deserialize)]
struct NoteData {
    amount: u64,
    // Add other note fields as needed
    data: Vec<u8>,
}

fn compute_note_commitment(note_data: &[u8]) -> [u8; 32] {
    // Ensure note_data is not empty
    assert!(!note_data.is_empty(), "Note data cannot be empty");
    
    // Ensure note_data is not too large (e.g., max 1MB)
    assert!(note_data.len() <= 1024 * 1024, "Note data is too large");
    
    // Compute SHA-256 hash of note_data
    let mut hasher = sha2::Sha256::new();
    hasher.update(note_data);
    let result = hasher.finalize();
    
    // Convert to fixed-size array
    let mut commitment = [0u8; 32];
    commitment.copy_from_slice(&result);
    
    commitment
}

fn main() {
    // Read the note data and burned amount from the host
    let note_data: Vec<u8> = env::read();
    let burned_amount: u64 = env::read();
    
    // Deserialize note data to get the amount
    let note: NoteData = bincode::deserialize(&note_data)
        .expect("Failed to deserialize note data");
    
    // Verify that the note amount matches the burned amount
    assert_eq!(
        note.amount, burned_amount,
        "Note amount {} does not match burned amount {}",
        note.amount, burned_amount
    );
    
    // Compute the note commitment with constraints
    let commitment = compute_note_commitment(&note_data);
    
    // Verify commitment is not all zeros
    assert!(!commitment.iter().all(|&x| x == 0), "Invalid commitment: all zeros");
    
    // Write the commitment back to the host
    env::commit(&commitment);
} 