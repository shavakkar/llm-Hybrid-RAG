import re
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from ai.agents.base import BaseGenerator

class LocalDeepSeekGenerator(BaseGenerator):
    """
    Optimized Local Execution supporting CPU fallback and GPU precision.
    """
    def __init__(self, model_path: str):
        print(f"[Generator] Loading Local LLM from: {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Ensure pad_token_id is set on the tokenizer
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        # Auto-detect optimal float precision based on hardware
        if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
            selected_dtype = torch.bfloat16
        elif torch.cuda.is_available():
            selected_dtype = torch.float16
        else:
            selected_dtype = torch.float32  # CPU default

        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=selected_dtype,
            device_map="auto",
            low_cpu_mem_usage=True,
            attn_implementation="sdpa" if torch.cuda.is_available() else "eager"
        )

    def generate_answer(self, query: str, context_documents: List[str]) -> Dict[str, Any]:
        context = "\n---\n".join(context_documents)
        user_content = f"Use ONLY the provided context to answer.\n\nContext:\n{context}\n\nQuestion:\n{query}"

        messages = [{"role": "user", "content": user_content}]

        # Applies the model's native instruction chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=300,
            temperature=0.6,
            do_sample=True,
            use_cache=True,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id
        )

        # Slice generated tokens to exclude the prompt input tokens
        input_len = inputs.input_ids.shape[-1]
        generated_tokens = outputs[0][input_len:]
        raw_output = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        # Extract reasoning thoughts and isolate answer
        think_match = re.search(r'<think>(.*?)</think>', raw_output, flags=re.DOTALL)
        thoughts = think_match.group(1).strip() if think_match else "No explicit reasoning generated."
        clean_answer = re.sub(r'<think>.*?</think>', '', raw_output, flags=re.DOTALL).strip()

        return {
            "thoughts": thoughts,
            "answer": clean_answer
        }