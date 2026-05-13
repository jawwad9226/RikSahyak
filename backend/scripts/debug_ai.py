import subprocess
import sys

MODEL_PATH = '/data/data/com.termux/files/home/models/qwen-0.5b.gguf'
sms_text = 'Mala railway station to hospital jaycha aahe'

system_prompt = 'You are a JSON extractor. Extract pickup and dropoff from ride messages. Reply ONLY with JSON.'
user_prompt = f'Extract locations: "{sms_text}". Reply: {{"pickup": "...", "dropoff": "..."}}'
full_prompt = f'<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n'

cmd = ['llama-completion', '-m', MODEL_PATH, '-p', full_prompt,
       '-n', '64', '--temp', '0.1', '-t', '4',
       '--ctx-size', '512', '--no-warmup',
       '--reverse-prompt', '<|im_end|>']

print("Running command...")
result = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
print('=== STDOUT ===')
print(repr(result.stdout))
print('=== STDERR TAIL ===')
print(repr(result.stderr[-300:]))
print('=== RETURN CODE ===', result.returncode)
