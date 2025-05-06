use risc0_verifier::*;
use serde::{Deserialize, Serialize};
use std::fs::File;
use tracing_subscriber::{fmt, EnvFilter};

#[derive(Debug, Serialize, Deserialize)]
struct VerificationInput {
    receipt_path: String,
    journal: Vec<u8>,
    image_id: Vec<u8>,
}

fn main() {
    // Initialize tracing
    fmt().with_env_filter(EnvFilter::from_default_env()).init();

    // Get the absolute path to verification_input.json
    let current_dir = std::env::current_dir().expect("Failed to get current directory");
    let prover_host_dir = current_dir
        .parent()
        .expect("Failed to get parent directory")
        .join("prover/host");

    let input_path = prover_host_dir.join("verification_input.json");

    // Read verification input from file
    let input: VerificationInput = serde_json::from_reader(
        File::open(&input_path).expect("Failed to open verification input file")
    ).expect("Failed to parse verification input");


    // Read and deserialize the receipt from prover/host directory
    let receipt_path = prover_host_dir.join(input.receipt_path);
    
    let receipt_file = match File::open(&receipt_path) {
        Ok(file) => file,
        Err(e) => {
            println!("Error opening receipt file: {:?}", e);
            panic!("Failed to open receipt file");
        }
    };

    let proof: Proof = match ciborium::de::from_reader(receipt_file) {
        Ok(proof) => proof,
        Err(e) => {
            println!("Error parsing receipt: {:?}", e);
            panic!("Failed to parse receipt");
        }
    };    

    // Convert journal and image_id
    let journal = Journal { bytes: input.journal };
    let image_id: [u8; 32] = input.image_id.try_into().expect("Invalid image_id length");
    let vk = Digest::from(image_id);

    // Create verifier for RISC Zero 1.2
    let verifier = v2_0().boxed();

    // Verify the receipt using risc0-verifier
    match verifier.verify(vk, proof, journal) {
        Ok(_) => println!("Verification successful!"),
        Err(e) => println!("Verification failed: {:?}", e),
    }
} 