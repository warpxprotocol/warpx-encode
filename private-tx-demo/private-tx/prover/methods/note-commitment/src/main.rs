use risc0_zkvm::guest::env;
use sha2::Digest;

fn main() {
    // Read the note data from the host
    let note_data: Vec<u8> = env::read();
    
    // Compute the note commitment
    let commitment = compute_note_commitment(&note_data);
    
    // Write the commitment back to the host
    env::commit(&commitment);
}

fn compute_note_commitment(note_data: &[u8]) -> [u8; 32] {
    // Here we use a simple hash function for demonstration
    // In a real implementation, you would use a proper cryptographic hash function
    let mut hasher = sha2::Sha256::new();
    hasher.update(note_data);
    let result = hasher.finalize();
    result.into()
} 