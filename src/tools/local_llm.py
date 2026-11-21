
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

_model = None
_tokenizer = None


def load_local_llm():
    global _model, _tokenizer

    if _model is None:
        print("[LLM] Loading original Qwen model...")

        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME
        )

        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=(
                torch.float16
                if torch.cuda.is_available()
                else torch.float32
            ),
            device_map="auto"
        )

        _model.eval()

        print("[LLM] Qwen model loaded successfully!")

    return _tokenizer, _model


def ask_local_llm(system_prompt: str, user_prompt: str) -> str:
    """Original Sprints Qwen generation workflow."""

    tokenizer, model = load_local_llm()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    ).to(model.device)

    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=200,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    new_tokens = output[0][
        inputs["input_ids"].shape[-1]:
    ]

    return tokenizer.decode(
        new_tokens,
        skip_special_tokens=True
    ).strip()
