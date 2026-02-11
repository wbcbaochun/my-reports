#!/usr/bin/env python3
import json
import base64
import sys
import subprocess

def audio_to_base64(file_path):
    with open(file_path, 'rb') as f:
        audio_bytes = f.read()
    return base64.b64encode(audio_bytes).decode('utf-8')

def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    # Convert audio to base64
    print(f"Encoding {audio_file} to base64...")
    audio_b64 = audio_to_base64(audio_file)
    
    # Create input JSON
    input_data = {
        "audio": audio_b64,
        "language": "auto",
        "task": "transcribe"
    }
    
    # Save to file
    input_file = "input.json"
    with open(input_file, 'w') as f:
        json.dump(input_data, f)
    
    print(f"Input JSON saved to {input_file}")
    
    # Run inference.sh
    print("Running inference.sh...")
    cmd = ["infsh", "app", "run", "infsh/fast-whisper-large-v3", "--input", input_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)

if __name__ == "__main__":
    main()