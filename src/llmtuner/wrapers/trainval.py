import os
import json
def trval_main(args):
    model_name_or_path = args.model_name_or_path
    model_template = args.model_template
    dataset: str = args.dataset
    output_dir = args.output_dir
    val_ratio = args.val_ratio
    each_max_samples = args.each_max_samples
    finetuning_type = args.finetuning_type
    per_device_train_batch_size = args.per_device_train_batch_size
    learning_rate = args.learning_rate
    num_train_epochs = args.num_train_epochs
    max_seq_len = args.max_seq_len

    if not os.path.exists(model_name_or_path):
        raise ValueError(f"Model {model_name_or_path} not found")
    
    # dataset change
    data_dir = dataset.split(',')[0].rsplit("/", 1)[0]
    datasets = dataset.replace(data_dir + "/", "")
    dataset_info = {key: {"file_name": key} for key in datasets.split(',')}
    with open(os.path.join(data_dir, 'dataset_info.json'), "w") as f:
        f.write(json.dumps(dataset_info, indent=4))

    train_param_cmd = f'''
--stage sft \
--do_train True \
--finetuning_type {finetuning_type} \
--model_name_or_path {model_name_or_path} \
--template {model_template} \
--dataset {datasets} \
--dataset_dir {data_dir} \
--val_size {val_ratio} \
--output_dir {output_dir} \
--overwrite_output_dir True \
--cutoff_len {max_seq_len} \
--learning_rate {learning_rate} \
--per_device_train_batch_size {per_device_train_batch_size} \
--per_device_eval_batch_size 1 \
--gradient_accumulation_steps 4 \
--lr_scheduler_type cosine \
--num_train_epochs {num_train_epochs} \
--logging_steps 10 \
--save_strategy epoch \
--evaluation_strategy epoch \
--metric_for_best_model eval_loss \
--load_best_model_at_end True \
--save_total_limit 1 \
--fp16 True \
--plot_loss True \
    '''

    if each_max_samples is not None:
        if len(each_max_samples.split(",")) != len(datasets.split(",")):
            raise ValueError(f"each_max_samples must be the same length as dataset")
        train_param_cmd += f'''
        --each_max_samples {each_max_samples} \
        '''
    