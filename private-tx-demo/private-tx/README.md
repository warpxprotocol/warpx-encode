# Private Transaction Demo

## Project Overview

The RISC Zero Rust Starter Template provides a foundation for building projects using the RISC Zero zkVM. This template includes the basic structure and configuration needed to implement Zero-Knowledge Proofs.

## Project Structure

```
project_name
├── Cargo.toml                # Main project configuration file
├── Cargo.lock                # Dependency lock file
├── rust-toolchain.toml       # Rust toolchain version management
├── src/                      # Source code directory
├── prover/                   # Proof generation code
│   ├── Cargo.toml           # Prover configuration
│   ├── host/                # Host code directory
│   │   └── src/            # Host implementation
│   └── methods/            # Guest code directory
│       ├── Cargo.toml      # Methods configuration
│       ├── build.rs        # Build configuration
│       ├── spend-proof/    # Spend proof guest program
│       │   └── src/       # Spend proof implementation
│       └── note-commitment/ # Note commitment guest program
│           └── src/       # Note commitment implementation
├── verifier/                 # Proof verification code
├── target/                   # Build output directory
├── LICENSE                   # License file
└── .gitignore               # Git ignore file list
```

## Key Components

### 1. Source Code (src/)

- Core project logic implementation
- Main application code

### 2. Proof Generation (prover/)

#### Host Code (prover/host/)

- Code that runs outside the zkVM
- Manages interaction with guest code
- Handles proof verification and results

#### Guest Code (prover/methods/)

The methods directory contains two separate guest programs:

1. Spend Proof (prover/methods/spend-proof/)

   - Implements the spend proof generation logic
   - Verifies transaction spending
   - Runs inside the zkVM

2. Note Commitment (prover/methods/note-commitment/)
   - Implements the note commitment proof generation
   - Handles note commitment verification
   - Runs inside the zkVM

Both guest programs:

- Execute in the constrained zkVM environment
- Are built using the build.rs configuration
- Generate zero-knowledge proofs for their respective operations

### 3. Proof Verification (verifier/)

- Code for verifying generated proofs
- Proof validity checking logic
- Verification result processing

## Getting Started

### Prerequisites

- Install [rustup](https://rustup.rs)
- Rust version specified in `rust-toolchain.toml`

### Build and Run

```bash
cargo run
```

### Running the Prover

The prover can be executed with different proof types:

1. Note Commitment Proof

```bash
cargo run -- --proof note-commitment --amount 100
```

- Generates a note commitment proof
- Requires an amount parameter
- Used for creating new notes

2. Spend Proof

```bash
cargo run -- --proof spend
```

- Generates a spend proof
- Verifies the spending of existing notes
- Used for transaction verification
