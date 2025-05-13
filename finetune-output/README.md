---
library_name: peft
license: other
base_model: /home/tiancongcong/.cache/modelscope/hub/models/Qwen/qwen-7B-chat
tags:
- llama-factory
- lora
- generated_from_trainer
model-index:
- name: finetune-output
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# finetune-output

This model is a fine-tuned version of [/home/tiancongcong/.cache/modelscope/hub/models/Qwen/qwen-7B-chat](https://huggingface.co//home/tiancongcong/.cache/modelscope/hub/models/Qwen/qwen-7B-chat) on the alpaca_zh_demo.json dataset.
It achieves the following results on the evaluation set:
- Loss: 1.3803

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 5e-05
- train_batch_size: 4
- eval_batch_size: 1
- seed: 42
- gradient_accumulation_steps: 4
- total_train_batch_size: 16
- optimizer: Adam with betas=(0.9,0.999) and epsilon=1e-08
- lr_scheduler_type: cosine
- num_epochs: 3.0
- mixed_precision_training: Native AMP

### Training results

| Training Loss | Epoch  | Step | Validation Loss |
|:-------------:|:------:|:----:|:---------------:|
| No log        | 0.8696 | 5    | 1.3848          |
| 1.5157        | 1.9130 | 11   | 1.3809          |
| 1.5157        | 2.6087 | 15   | 1.3803          |


### Framework versions

- PEFT 0.15.1
- Transformers 4.45.2
- Pytorch 2.7.0+cu126
- Datasets 3.5.0
- Tokenizers 0.20.3