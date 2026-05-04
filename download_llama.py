#!/usr/bin/env python3
"""
Script to download Llama model from Hugging Face for local use.
This downloads a quantized version for efficient local inference.
"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download
import sys

# Configuration
MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"  # Using smaller model for local deployment
LOCAL_MODEL_DIR = "./llama-models/llama-3.2-3b-instruct"

def download_llama_model():
    """
    Download Llama model from Hugging Face to local directory.
    Requires HF_TOKEN environment variable for gated models.
    """
    print("=" * 80)
    print("IASW - Llama Model Download Script")
    print("=" * 80)

    # Check for HuggingFace token
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("\n⚠️  WARNING: HF_TOKEN environment variable not set.")
        print("For gated models like Llama, you need to:")
        print("1. Create an account on huggingface.co")
        print("2. Request access to the Llama model")
        print("3. Generate a token at https://huggingface.co/settings/tokens")
        print("4. Set it: export HF_TOKEN='your_token_here'")
        print("\nAttempting download without token (may fail for gated models)...\n")

    # Create directory
    Path(LOCAL_MODEL_DIR).mkdir(parents=True, exist_ok=True)

    try:
        print(f"\n📥 Downloading model: {MODEL_NAME}")
        print(f"📁 Target directory: {LOCAL_MODEL_DIR}")
        print("\nThis may take several minutes depending on your connection...")
        print("-" * 80)

        # Download model
        snapshot_download(
            repo_id=MODEL_NAME,
            local_dir=LOCAL_MODEL_DIR,
            token=hf_token,
            ignore_patterns=["*.msgpack", "*.h5", "*.ot"],  # Skip unnecessary files
        )

        print("\n" + "=" * 80)
        print("✅ Model downloaded successfully!")
        print(f"📁 Location: {os.path.abspath(LOCAL_MODEL_DIR)}")
        print("=" * 80)

        # List downloaded files
        print("\n📋 Downloaded files:")
        for root, dirs, files in os.walk(LOCAL_MODEL_DIR):
            level = root.replace(LOCAL_MODEL_DIR, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # Show first 10 files
                print(f'{subindent}{file}')
            if len(files) > 10:
                print(f'{subindent}... and {len(files) - 10} more files')

        return True

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ Error downloading model: {str(e)}")
        print("=" * 80)

        if "gated" in str(e).lower() or "access" in str(e).lower():
            print("\n💡 This appears to be a gated model. Please:")
            print("1. Visit https://huggingface.co/" + MODEL_NAME)
            print("2. Accept the license agreement")
            print("3. Generate a token and set HF_TOKEN environment variable")
            print("4. Run this script again")

        return False

def verify_model():
    """Verify that the model was downloaded correctly."""
    required_files = ["config.json", "tokenizer.json", "tokenizer_config.json"]

    print("\n🔍 Verifying model files...")
    all_exist = True

    for file in required_files:
        file_path = os.path.join(LOCAL_MODEL_DIR, file)
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {file}")
        all_exist = all_exist and exists

    if all_exist:
        print("\n✅ All required files present!")
    else:
        print("\n⚠️  Some required files are missing. Download may be incomplete.")

    return all_exist

if __name__ == "__main__":
    print("\n")
    success = download_llama_model()

    if success:
        verify_model()
        print("\n🚀 Ready to use the local Llama model in IASW!")
    else:
        print("\n⚠️  Model download failed. Please check errors above.")
        sys.exit(1)
