# app/services/local_llm.py
from unsloth import FastLanguageModel

MAX_SEQ_LENGTH = 2048
SYSTEM_PROMPT = (
    "You are a cautious medical and mental health assistant. "
    "Provide general educational information only. "
    "Do not diagnose with certainty. "
    "Encourage professional care when needed. "
    "If symptoms seem severe or urgent, clearly recommend immediate medical attention."
)

model = None
tokenizer = None

def load_local_model():
    global model, tokenizer
    if model is not None and tokenizer is not None:
        return

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/llama-3.1-8b-instruct",
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
    )
    model.load_adapter("models/medical_lora_adapter")
    FastLanguageModel.for_inference(model)

def generate_response(user_message: str) -> str:
    if model is None or tokenizer is None:
        raise RuntimeError("Local model is not loaded.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
    ).to("cuda")

    outputs = model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_new_tokens=220,
        temperature=0.6,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "assistant" in text:
        text = text.split("assistant", 1)[-1].strip()
    return text