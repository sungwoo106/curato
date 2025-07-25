import torch
import numpy as np
import qai_hub as hub
from transformers import AutoModelForCausalLM, AutoTokenizer

DEVICE_NAME = "Snapdragon X Elite CRD"


def _compile_model(model_name: str, input_length: int = 64):
    """Compile the given Hugging Face model for the target device."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    torch_model = AutoModelForCausalLM.from_pretrained(model_name)
    torch_model.eval()

    dummy_ids = torch.randint(0, torch_model.config.vocab_size, (1, input_length))
    traced_model = torch.jit.trace(torch_model, dummy_ids)

    compile_job = hub.submit_compile_job(
        model=traced_model,
        device=hub.Device(DEVICE_NAME),
        input_specs=dict(input_ids=dummy_ids.shape),
        options="--target_runtime onnx",
    )

    target_model = compile_job.get_target_model()

    # Profile the compiled model on the target device
    hub.submit_profile_job(
        model=target_model,
        device=hub.Device(DEVICE_NAME),
    )

    return target_model, tokenizer


def _run_inference(target_model, tokenizer, prompt: str):
    """Run inference on the compiled model using the provided prompt."""
    input_ids = tokenizer(prompt, return_tensors="np")["input_ids"]
    inference_job = hub.submit_inference_job(
        model=target_model,
        device=hub.Device(DEVICE_NAME),
        inputs=dict(input_ids=[input_ids]),
    )
    output = inference_job.download_output_data()
    output_name = list(output.keys())[0]
    tokens = np.array(output[output_name][0])
    return tokenizer.decode(tokens, skip_special_tokens=True)


def run_phi35_mini(prompt: str) -> str:
    """Compile and run the phi 3.5 mini model on QAI Hub."""
    model_name = "microsoft/phi-3.5-mini-instruct"
    target_model, tokenizer = _compile_model(model_name)
    return _run_inference(target_model, tokenizer, prompt)


def run_llama32_3b(prompt: str) -> str:
    """Compile and run the Llama 3.2-3B model on QAI Hub."""
    model_name = "meta-llama/Llama-3.2-3B-Instruct"
    target_model, tokenizer = _compile_model(model_name)
    return _run_inference(target_model, tokenizer, prompt)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python hub_runner.py [phi|llama] <prompt>")
        sys.exit(1)

    model_key = sys.argv[1].lower()
    prompt = " ".join(sys.argv[2:])

    if model_key == "phi":
        print(run_phi35_mini(prompt))
    elif model_key == "llama":
        print(run_llama32_3b(prompt))
    else:
        raise ValueError("Unknown model key: " + model_key)
    