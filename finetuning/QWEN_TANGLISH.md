# Qwen3.5-9B Tanglish adapter recipe

The desktop uses its installed GGUF and the trained language router. This separate experiment fine-tunes low-rank adapters on a local upstream Transformers checkpoint. Keep both the base checkpoint and the original GGUF for rollback. No private conversation export is used.

**Corpus.** The TSV training file has 36 original question/translation/reply triples. The separate evaluation file has eight unseen question/reply pairs. Expand and review them with fluent speakers before optimizing for release. Include formal and familiar registers, spelling variants, English technical terms and serious requests. Keep near-duplicates and paraphrases in the same split. Reserve additional blind English, Tamil-script and Tanglish prompts for regression testing.

**Preparation.** The local preflight validated the upstream tokenizer from Qwen checkpoint revision `bd2750eed1009cf6921b269adb0b27154ae5548f` with Transformers 5.24.1. The maximum combined example length was 95 tokens. The recipe uses the checkpoint's chat template with thinking disabled, preserves its vocabulary, masks the entire prompt from the training loss, and supervises the reply plus the end-of-turn token. It rejects examples exceeding 512 tokens. Personal-memory embeddings remain a separate retrieval component.

```powershell
..\.venv\Scripts\python.exe finetuning/scripts/qwen_tanglish_lora.py check
.\.runtime\lora-preflight\Scripts\python.exe finetuning/scripts/qwen_tanglish_lora.py tokenize --base .runtime/qwen-tokenizer
```

**GPU training procedure.** On a CUDA machine, create a separate Python environment, install the PyTorch build for that accelerator, Transformers with Qwen3.5 support, Accelerate, PEFT, Jinja2 and bitsandbytes with 4-bit CUDA support. Supply a locally available, matching upstream checkpoint directory containing config, tokenizer, template and safetensors weights. Record its revision, GPU/driver and package versions. Run the script from the repository root with a fresh output directory:

```sh
python finetuning/scripts/qwen_tanglish_lora.py tokenize --base /models/Qwen3.5-9B
python finetuning/scripts/qwen_tanglish_lora.py train --base /models/Qwen3.5-9B --out .runtime/tanglish-lora-trial-01
```

Initial trial uses 4-bit NF4 double quantization, one epoch and a learning rate of 5e-5. Rank-8 LoRA is attached to text attention query and value projections. The vision stack stays frozen. The script reports trainable parameters, evaluates before and after training, and writes adapter and tokenizer files plus evaluation metrics. The GPU training stage has not been run in this workspace. [Upstream Qwen model](https://huggingface.co/Qwen/Qwen3.5-9B) · [PEFT quantized training guide](https://huggingface.co/docs/peft/en/developer_guides/quantization)

**Acceptance.** Compare identical held-out prompts with the original and adapted checkpoints. Have a fluent reviewer score script choice, understanding, idiom, usefulness and tone. Include serious prompts, English switch requests and retrieval of a synthetic owner fact. Check for invented names and repeated jokes. A lower loss alone cannot establish dialogue quality. For a passing trial, test the adapter with its exact base in a separate compatible serving process. If converting to GGUF, verify conversion support for this architecture and compare its outputs before changing the desktop model identifier. Switching back to the original server/model preserves the canonical SQL memory.
