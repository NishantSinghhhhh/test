import time
import torch
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- CONFIGURATION ---
MODEL_NAME = "gpt2-medium" # The "Boss" Model
PORT = 5000

# --- SETUP ---
app = Flask(__name__)
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[INIT] Loading Cloud Model: {MODEL_NAME} on {device}...")
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(device)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
print(f"[INIT] Model Loaded. Ready to accept requests.")

@app.route('/verify', methods=['POST'])
def verify():
    """
    Endpoint called by the Edge Device.
    Receives: {"tokens": [123, 456, ...]}
    Returns:  {"status": "accepted"}
    """
    try:
        data = request.json
        if not data or 'tokens' not in data:
            return jsonify({"error": "No tokens provided"}), 400

        # 1. Receive Draft Tokens
        draft_tokens_list = data['tokens']
        input_ids = torch.tensor([draft_tokens_list]).to(device)

        # 2. Run the Heavy Verification (The "Boss" doing work)
        # We wrap this in no_grad because we are just predicting, not training
        start_time = time.time()
        with torch.no_grad():
            outputs = model(input_ids)
            logits = outputs.logits

        # (In a full implementation, we would compare logits here.
        # For benchmarking, running the model IS the workload.)
        
        process_time = time.time() - start_time
        print(f"[INFO] Verified {len(draft_tokens_list)} tokens in {process_time:.4f}s")

        return jsonify({
            "status": "success",
            "server_processing_time": process_time
        })

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # host='0.0.0.0' allows external connections (Crucial for DigitalOcean)
    app.run(host='0.0.0.0', port=PORT)
