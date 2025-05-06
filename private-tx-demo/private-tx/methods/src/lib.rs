// This file is intentionally left empty 

include!(concat!(env!("OUT_DIR"), "/methods.rs")); 

use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SpendInput {
    pub note_data: Vec<u8>,
    pub note_commitment: Vec<u8>,
    pub public_key: Vec<u8>,
    pub signature: Vec<u8>,
    pub amount: u64,
    pub spend_amount: u64,
}
