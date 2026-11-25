"""Local-only, text-only Qwen3.5-9B adapter recipe. No downloads or uploads."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ("You are a helpful assistant. Reply in the language and script used in the question. "
          "For Romanized Tamil, use natural Tanglish. Keep any dry humor brief.")


def examples():
    def load(filename):
        rows = []
        for line in (ROOT / filename).read_text(encoding='utf-8').splitlines():
            if line.strip():
                fields = line.split('\t')
                rows.append((fields[0],fields[-1]))
        return rows
    train, valid = load('tanglish_pairs.tsv'), load('tanglish_eval.tsv')
    questions = [q.strip().casefold() for q,_ in train+valid]
    if len(questions)!=len(set(questions)) or any(not a.strip() for _,a in train+valid):
        raise ValueError('Duplicate prompt or missing answer.')
    return train,valid


def encode(tokenizer, question, answer):
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':question}]
    prompt=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prefix=tokenizer.encode(prompt,add_special_tokens=False)
    target=tokenizer.encode(answer,add_special_tokens=False)
    end=tokenizer.convert_tokens_to_ids('<|im_end|>')
    if end is None or end==tokenizer.unk_token_id or not target:
        raise ValueError('Expected the Qwen chat tokenizer and a nonempty answer.')
    ids=prefix+target+[end]
    if len(ids)>512:
        raise ValueError('Sample exceeds the context budget; review it before training.')
    return {'input_ids':ids,'attention_mask':[1]*len(ids),'labels':[-100]*len(prefix)+target+[end]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['check','tokenize','train'])
    parser.add_argument('--base',type=Path,help='Local upstream Transformers checkpoint directory.')
    parser.add_argument('--out',type=Path,help='New directory for the adapter.')
    args=parser.parse_args()
    train,valid=examples()
    print(f'{len(train)} training pairs, {len(valid)} separate evaluation pairs.')
    if args.mode=='check':
        return
    if not args.base or not args.base.is_dir():
        parser.error('Provide --base with the local Qwen3.5-9B checkpoint.')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(args.base,local_files_only=True)
    train=[encode(tokenizer,*row) for row in train]
    valid=[encode(tokenizer,*row) for row in valid]
    print('Maximum tokens per example:',max(len(row['input_ids']) for row in train+valid))
    if args.mode=='tokenize':
        return
    if not args.out or args.out.exists():
        parser.error('Provide --out with a fresh output directory.')
    import torch
    from peft import LoraConfig,get_peft_model,prepare_model_for_kbit_training
    from transformers import (AutoModelForImageTextToText,BitsAndBytesConfig,DataCollatorForSeq2Seq,
                              Trainer,TrainingArguments,set_seed)
    if not torch.cuda.is_available():
        parser.error('This training recipe requires a CUDA training environment.')
    dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    set_seed(13)
    quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
                             bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=dtype)
    base=AutoModelForImageTextToText.from_pretrained(args.base,local_files_only=True,device_map={'':0},
                                                     quantization_config=quant,dtype=dtype)
    if base.config.model_type!='qwen3_5':
        raise ValueError('Expected the Qwen3.5 checkpoint.')
    base=prepare_model_for_kbit_training(base)
    targets=[n for n,_ in base.named_modules() if 'language_model.' in n and n.endswith(('.q_proj','.v_proj'))]
    if not targets:
        raise ValueError('No text attention projections matched this checkpoint.')
    model=get_peft_model(base,LoraConfig(r=8,lora_alpha=16,lora_dropout=.05,target_modules=targets,bias='none'))
    model.print_trainable_parameters()
    args.out.mkdir(parents=True,exist_ok=False)
    options=TrainingArguments(output_dir=str(args.out),learning_rate=5e-5,num_train_epochs=1,
        per_device_train_batch_size=1,per_device_eval_batch_size=1,gradient_accumulation_steps=4,
        gradient_checkpointing=True,bf16=dtype==torch.bfloat16,fp16=dtype==torch.float16,
        prediction_loss_only=True,report_to='none',push_to_hub=False,save_strategy='no',seed=13,
        remove_unused_columns=False)
    trainer=Trainer(model=model,args=options,train_dataset=train,eval_dataset=valid,
        data_collator=DataCollatorForSeq2Seq(tokenizer,label_pad_token_id=-100))
    baseline=trainer.evaluate()['eval_loss']
    trainer.train()
    final=trainer.evaluate()['eval_loss']
    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    (args.out/'evaluation.json').write_text(json.dumps({'baseline_loss':baseline,'adapter_loss':final,
        'base_checkpoint':str(args.base),'train_examples':len(train),'eval_examples':len(valid)},indent=2))


if __name__=='__main__':
    main()
