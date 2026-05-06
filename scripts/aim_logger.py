"""
AimLoggerCallback и утилита tb_to_aim — мост между
TensorBoard-логами и Aim-трекером.

LLaMA-Factory нативно поддерживает только TensorBoard, Wandb,
MLflow и SwanLab. Этот модуль решает проблему двумя способами:

1. AimLoggerCallback — TrainerCallback, который пишет метрики
   напрямую в Aim при обучении из Jupyter.

2. tb_to_aim() — утилита для конвертации уже записанных
   TensorBoard event-файлов в Aim.

Зависимости (установить в Jupyter):
    pip install aim tensorboard

Использование (колбэк):
    from aim_logger import AimLoggerCallback
    trainer = Trainer(
        ...,
        callbacks=[AimLoggerCallback(repo="aim://aim:53800")],
    )

Использование (конвертация):
    from aim_logger import tb_to_aim
    tb_to_aim("/home/jovyan/logs/tb", repo="/home/jovyan/logs/aim")
"""

from transformers import TrainerCallback
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class AimLoggerCallback(TrainerCallback):
    """
    Логирует скалярные метрики (loss, lr, eval_*) напрямую в Aim.

    Параметры:
        repo: путь к Aim-репозиторию или URL tracking-сервера
              (например, "aim://aim:53800" для Docker-сети,
               или "/home/jovyan/logs/aim" для локального)
        experiment: имя эксперимента в Aim UI
        log_system_params: логировать ли системные параметры (GPU, RAM)
    """

    def __init__(
        self,
        repo: str = "/home/jovyan/logs/aim",
        experiment: str = "llama-factory",
        log_system_params: bool = True,
    ):
        self.repo = repo
        self.experiment = experiment
        self.log_system_params = log_system_params
        self._run = None

    def _get_run(self):
        if self._run is not None:
            return self._run

        try:
            from aim import Run

            self._run = Run(
                repo=self.repo,
                experiment=self.experiment,
                log_system_params=self.log_system_params,
            )
            logger.info("AimLoggerCallback: подключено к %s", self.repo)
        except ImportError:
            logger.error(
                "AimLoggerCallback: пакет 'aim' не установлен. "
                "Выполните: pip install aim"
            )
        except Exception as e:
            logger.error("AimLoggerCallback: ошибка подключения к Aim: %s", e)

        return self._run

    def on_train_begin(self, args, state, control, model=None, **kwargs):
        run = self._get_run()
        if run is None:
            return

        hparams = {
            k: v
            for k, v in vars(args).items()
            if isinstance(v, (int, float, str, bool))
        }
        for k, v in hparams.items():
            run[f"hparams/{k}"] = v

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return

        run = self._get_run()
        if run is None:
            return

        step = state.global_step
        for key, value in logs.items():
            if isinstance(value, (int, float)):
                run.track(value, name=key, step=step)

    def on_train_end(self, args, state, control, **kwargs):
        if self._run is not None:
            self._run.close()
            self._run = None
            logger.info("AimLoggerCallback: run закрыт")


def tb_to_aim(
    tb_log_dir: str,
    repo: str = "/home/jovyan/logs/aim",
    experiment: str = "imported-from-tb",
) -> int:
    """
    Конвертирует скалярные метрики из TensorBoard event-файлов в Aim.

    Параметры:
        tb_log_dir: путь к директории с TensorBoard-логами
        repo: путь к Aim-репозиторию
        experiment: имя эксперимента в Aim

    Возвращает:
        Количество импортированных метрик
    """
    try:
        from aim import Run
        from tensorboard.backend.event_processing.event_accumulator import (
            EventAccumulator,
        )
    except ImportError as e:
        raise ImportError(
            f"Нужны пакеты 'aim' и 'tensorboard': {e}. "
            "Установите: pip install aim tensorboard"
        )

    count = 0
    run = Run(repo=repo, experiment=experiment)

    for root, _dirs, files in os.walk(tb_log_dir):
        event_files = [f for f in files if f.startswith("events.out.tfevents")]
        if not event_files:
            continue

        ea = EventAccumulator(root)
        ea.Reload()

        for tag in ea.Tags().get("scalars", []):
            for event in ea.Scalars(tag):
                run.track(event.value, name=tag, step=event.step)
                count += 1

    run.close()
    logger.info(
        "tb_to_aim: импортировано %d метрик из %s в %s",
        count, tb_log_dir, repo,
    )
    return count
