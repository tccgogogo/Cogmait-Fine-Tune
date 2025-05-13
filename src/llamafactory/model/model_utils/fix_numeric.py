"""
修复模型数值问题的工具
"""

import torch
import warnings
from ...utils.generation_fix import fix_generation_functions


def apply_numeric_fixes(model):
    """
    应用各种数值稳定性修复到模型
    
    Args:
        model: 需要修复的模型
    """
    # 修复generate函数
    model = fix_generation_functions(model)
    
    # 检查并清理无效权重
    with torch.no_grad():
        for name, param in model.named_parameters():
            if torch.isnan(param).any() or torch.isinf(param).any():
                warnings.warn(f"发现无效参数值在 {name}，尝试修复...")
                # 用小随机值替换无效值
                invalid_mask = torch.isnan(param) | torch.isinf(param)
                if invalid_mask.any():
                    # 使用参数的均值和标准差生成随机值
                    valid_values = param[~invalid_mask]
                    if len(valid_values) > 0:
                        mean_val = valid_values.mean().item()
                        std_val = valid_values.std().item() or 1e-5
                        param.data[invalid_mask] = torch.randn_like(
                            param.data[invalid_mask]) * std_val * 0.1 + mean_val
                    else:
                        # 如果没有有效值，使用小随机值
                        param.data[invalid_mask] = torch.randn_like(
                            param.data[invalid_mask]) * 1e-5
    
    # 添加梯度裁剪以防止梯度爆炸
    if hasattr(model, "gradient_checkpointing_enable"):
        original_grad_ckpt = model.gradient_checkpointing_enable
        
        def safe_grad_ckpt(*args, **kwargs):
            model.gradient_checkpointing = True
            # 设置梯度裁剪
            for p in model.parameters():
                if p.requires_grad:
                    p.register_hook(lambda grad: torch.nn.utils.clip_grad_norm_(
                        grad, max_norm=1.0, norm_type=2))
            if original_grad_ckpt is not None:
                return original_grad_ckpt(*args, **kwargs)
        
        model.gradient_checkpointing_enable = safe_grad_ckpt
    
    return model 