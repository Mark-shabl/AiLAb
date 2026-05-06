"""
LayerStatsCallback — кастомный колбэк для логирования гистограмм
весов и градиентов по слоям в TensorBoard.

Стандартное логирование HuggingFace/LLaMA-Factory пишет только
loss, lr и eval-метрики. Этот колбэк добавляет:
  - gradients/<имя_слоя>  — распределение градиентов
  - weights/<имя_слоя>    — распределение весов
  - grad_norm/<имя_слоя>  — L2-норма градиента (скаляр)

Использование из Jupyter:
    from layer_histograms import LayerStatsCallback
    from transformers import Trainer

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        callbacks=[LayerStatsCallback(log_every_n_steps=50)],
    )
    trainer.train()

Использование из LLaMA-Factory CLI (если поддерживается):
    Положите файл в /app/scripts/ и укажите в YAML-конфиге:
        callbacks: ["scripts.layer_histograms.LayerStatsCallback"]
"""

from transformers import TrainerCallback
import torch
from torch.utils.tensorboard import SummaryWriter
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class LayerStatsCallback(TrainerCallback):
    """
    Логирует гистограммы весов и градиентов обучаемых параметров
    в TensorBoard каждые N шагов оптимизатора.

    Параметры:
        log_every_n_steps: как часто писать гистограммы (по умолчанию 50)
        log_grad_norm: писать ли L2-норму градиента как скаляр
        output_dir: путь к директории TensorBoard-логов (если None —
                    берётся из training_args.logging_dir)
        filter_patterns: список подстрок для фильтрации слоёв
                         (например, ["lora", "attention"]). Если пусто —
                         логируются все обучаемые параметры.
    """

    def __init__(
        self,
        log_every_n_steps: int = 50,
        log_grad_norm: bool = True,
        output_dir: Optional[str] = None,
        filter_patterns: Optional[list[str]] = None,
    ):
        self.log_every_n_steps = log_every_n_steps
        self.log_grad_norm = log_grad_norm
        self.output_dir = output_dir
        self.filter_patterns = filter_patterns or []
        self._writer: Optional[SummaryWriter] = None

    def _get_writer(self, args) -> Optional[SummaryWriter]:
        if self._writer is not None:
            return self._writer

        log_dir = self.output_dir or getattr(args, "logging_dir", None)
        if log_dir is None:
            log_dir = os.path.join(
                getattr(args, "output_dir", "/app/output"), "tensorboard"
            )

        os.makedirs(log_dir, exist_ok=True)
        self._writer = SummaryWriter(log_dir=log_dir)
        logger.info("LayerStatsCallback: TensorBoard writer -> %s", log_dir)
        return self._writer

    def _should_log_param(self, name: str) -> bool:
        if not self.filter_patterns:
            return True
        return any(p in name for p in self.filter_patterns)

    def on_log(self, args, state, control, model=None, **kwargs):
        if model is None:
            return

        step = state.global_step
        if step == 0 or step % self.log_every_n_steps != 0:
            return

        writer = self._get_writer(args)
        if writer is None:
            return

        for name, param in model.named_parameters():
            if not param.requires_grad:
                continue
            if not self._should_log_param(name):
                continue

            weight_data = param.detach().float().cpu()
            writer.add_histogram(f"weights/{name}", weight_data, step)

            if param.grad is not None:
                grad_data = param.grad.detach().float().cpu()
                writer.add_histogram(f"gradients/{name}", grad_data, step)

                if self.log_grad_norm:
                    grad_norm = grad_data.norm(2).item()
                    writer.add_scalar(f"grad_norm/{name}", grad_norm, step)

        writer.flush()

    def on_train_end(self, args, state, control, **kwargs):
        if self._writer is not None:
            self._writer.close()
            self._writer = None
            logger.info("LayerStatsCallback: writer закрыт")
