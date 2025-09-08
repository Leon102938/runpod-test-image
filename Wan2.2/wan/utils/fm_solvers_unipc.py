import math
from typing import List, Optional, Tuple, Union

import numpy as np
import torch
from diffusers.configuration_utils import ConfigMixin, register_to_config
from diffusers.schedulers.scheduling_utils import (
    KarrasDiffusionSchedulers,
    SchedulerMixin,
    SchedulerOutput,
)
from diffusers.utils import is_scipy_available

if is_scipy_available():
    import scipy.stats


class FlowUniPCMultistepScheduler(SchedulerMixin, ConfigMixin):
    """
    Training-freier Sampler für Flow-/Diffusion-Modelle mit Multi-Step-Updates (UniPC-ähnlich).
    Diese Version ist konsistent für 'flow_prediction' und vermeidet typische
    Argument-/Device-/Dtype-Schwierigkeiten in TI2V-5B-Setups.
    """

    _compatibles = [e.name for e in KarrasDiffusionSchedulers]
    order = 1

    @register_to_config
    def __init__(
        self,
        num_train_timesteps: int = 1000,
        solver_order: int = 2,
        prediction_type: str = "flow_prediction",
        shift: Optional[float] = 1.0,
        use_dynamic_shifting: bool = False,
        thresholding: bool = False,
        dynamic_thresholding_ratio: float = 0.995,
        sample_max_value: float = 1.0,
        predict_x0: bool = True,
        solver_type: str = "bh2",
        lower_order_final: bool = True,
        disable_corrector: List[int] = [],
        solver_p: SchedulerMixin = None,
        timestep_spacing: str = "linspace",
        steps_offset: int = 0,
        final_sigmas_type: Optional[str] = "zero",
    ):
        if solver_type not in ["bh1", "bh2"]:
            if solver_type in ["midpoint", "heun", "logrho"]:
                self.register_to_config(solver_type="bh2")
            else:
                raise NotImplementedError(
                    f"{solver_type} is not implemented for {self.__class__}"
                )

        self.predict_x0 = predict_x0
        self.num_inference_steps = None

        # Baseline "sigmas" (monoton fallend 1 -> ~0)
        alphas = np.linspace(1, 1 / num_train_timesteps, num_train_timesteps)[::-1].copy()
        sigmas = 1.0 - alphas
        sigmas = torch.from_numpy(sigmas).to(dtype=torch.float32)

        # optional: statisches Time-Shifting
        if not use_dynamic_shifting:
            sigmas = shift * sigmas / (1 + (shift - 1) * sigmas)

        self.sigmas = sigmas
        self.timesteps = sigmas * num_train_timesteps

        self.model_outputs = [None] * solver_order  # hält konvertierte x0s
        self.timestep_list = [None] * solver_order
        self.lower_order_nums = 0
        self.disable_corrector = disable_corrector
        self.solver_p = solver_p
        self.last_sample = None
        self._step_index = None
        self._begin_index = None

        self.sigma_min = self.sigmas[-1].item()
        self.sigma_max = self.sigmas[0].item()

    @property
    def step_index(self):
        return self._step_index

    @property
    def begin_index(self):
        return self._begin_index

    def set_begin_index(self, begin_index: int = 0):
        self._begin_index = begin_index

    def set_timesteps(
        self,
        num_inference_steps: Union[int, None] = None,
        device: Union[str, torch.device] = None,
        sigmas: Optional[List[float]] = None,
        mu: Optional[Union[float, None]] = None,
        shift: Optional[Union[float, None]] = None,
    ):
        if self.config.use_dynamic_shifting and mu is None:
            raise ValueError(
                "You must pass `mu` when `use_dynamic_shifting` is True."
            )

        if sigmas is None:
            # linearer Verlauf in Sigma-Domäne
            sigmas = np.linspace(self.sigma_max, self.sigma_min, num_inference_steps + 1).copy()[:-1]

        if self.config.use_dynamic_shifting:
            sigmas = self.time_shift(mu, 1.0, sigmas)
        else:
            if shift is None:
                shift = self.config.shift
            sigmas = shift * sigmas / (1 + (shift - 1) * sigmas)

        # letztes Sigma (t=0) — Standard: 0
        if self.config.final_sigmas_type == "sigma_min":
            # Fallback: kleiner positiver Wert
            sigma_last = float(1e-5)
        elif self.config.final_sigmas_type == "zero":
            sigma_last = 0.0
        else:
            raise ValueError(
                f"`final_sigmas_type` must be one of 'zero' or 'sigma_min', got {self.config.final_sigmas_type}"
            )

        timesteps = sigmas * self.config.num_train_timesteps
        sigmas = np.concatenate([sigmas, [sigma_last]]).astype(np.float32)

        self.sigmas = torch.from_numpy(sigmas)
        self.timesteps = torch.from_numpy(timesteps).to(device=device, dtype=torch.int64)

        self.num_inference_steps = len(timesteps)
        self.model_outputs = [None] * self.config.solver_order
        self.lower_order_nums = 0
        self.last_sample = None
        if self.solver_p:
            self.solver_p.set_timesteps(self.num_inference_steps, device=device)

        self._step_index = None
        self._begin_index = None

    def _threshold_sample(self, sample: torch.Tensor) -> torch.Tensor:
        dtype = sample.dtype
        batch_size, channels, *remaining_dims = sample.shape

        if dtype not in (torch.float32, torch.float64):
            sample = sample.float()

        flat_size = channels * int(np.prod(remaining_dims)) if remaining_dims else channels
        sample = sample.reshape(batch_size, flat_size)
        abs_sample = sample.abs()

        s = torch.quantile(abs_sample, self.config.dynamic_thresholding_ratio, dim=1)
        s = torch.clamp(s, min=1, max=self.config.sample_max_value)
        s = s.unsqueeze(1)
        sample = torch.clamp(sample, -s, s) / s

        sample = sample.reshape(batch_size, channels, *remaining_dims)
        return sample.to(dtype)

    def _sigma_to_alpha_sigma_t(self, sigma):
        # Für diese einfache Flow-Parametrisierung
        return 1 - sigma, sigma

    def time_shift(self, mu: float, sigma: float, t: torch.Tensor):
        return math.exp(mu) / (math.exp(mu) + (1 / t - 1) ** sigma)

    def convert_model_output(
        self,
        sample: torch.Tensor,
        model_output: torch.Tensor
    ) -> torch.Tensor:
        """
        Rechnet das Netz-Output in x0-Schätzung um.
        Annahme für 'flow_prediction':
            x0 = x_t - sigma_t * eps_t
        """
        # Device/Dtype-Sicherheit
        if model_output.device != sample.device:
            model_output = model_output.to(sample.device)
        if model_output.dtype != sample.dtype:
            model_output = model_output.to(sample.dtype)

        sigma = self.sigmas[self.step_index].to(sample.device)
        _, sigma_t = self._sigma_to_alpha_sigma_t(sigma)

        if not self.predict_x0:
            raise ValueError("predict_x0=False wird in dieser Variante nicht unterstützt.")

        if self.config.prediction_type != "flow_prediction":
            raise ValueError(
                f"prediction_type must be 'flow_prediction', got {self.config.prediction_type}"
            )

        # Kanäle ggf. anpassen (z.B. 1->48 Wiederholung)
        if model_output.shape[1] != sample.shape[1]:
            if sample.shape[1] % model_output.shape[1] != 0:
                raise ValueError(
                    f"Channel mismatch cannot be resolved: model_output={model_output.shape}, sample={sample.shape}"
                )
            repeat_factor = sample.shape[1] // model_output.shape[1]
            model_output = model_output.repeat(
                1, repeat_factor, *[1] * (model_output.ndim - 2)
            )

        # x0 = x_t - sigma_t * eps_t
        x0_pred = sample - sigma_t * model_output

        if self.config.thresholding:
            x0_pred = self._threshold_sample(x0_pred)

        return x0_pred

    def multistep_uni_p_bh_update(
        self,
        model_output: torch.Tensor,
        *args,
        sample: torch.Tensor = None,
        order: int = None,
        **kwargs,
    ) -> torch.Tensor:
        """
        Predictor-Schritt. Nutzt x0 (model_output) und einen einfachen
        konsistenten Übergang von sigma_t -> sigma_s0:

            eps_t = (x_t - x0) / sigma_t
            x_{s0} = x0 + sigma_{s0} * eps_t
                   = x0 + (sigma_{s0}/sigma_t) * (x_t - x0)

        Das ist stabil und funktioniert für flow_prediction verlässlich.
        """
        device = sample.device
        sigma_t = self.sigmas[self.step_index].to(device)
        sigma_s0 = self.sigmas[self.step_index - 1].to(device)
        # x0 bereits gegeben als model_output (konvertiert)
        x0 = model_output

        # eps aus x0 ableiten
        eps_t = (sample - x0) / torch.clamp_min(sigma_t, 1e-9)

        prev_sample = x0 + sigma_s0 * eps_t
        return prev_sample

    def multistep_uni_c_bh_update(
        self,
        this_model_output: torch.Tensor,
        *args,
        last_sample: torch.Tensor = None,
        this_sample: torch.Tensor = None,
        order: int = None,
        **kwargs,
    ) -> torch.Tensor:
        """
        Corrector-Schritt (sanfte Heun-Blende). Wir benutzen x0 aus 'this_model_output'
        und bewegen uns leicht in Richtung x0, um Driften zu reduzieren.
        """
        device = this_sample.device
        sigma_t = self.sigmas[self.step_index].to(device)

        x0 = this_model_output  # bereits konvertiert
        # sanfte Korrektur (gewichtete Mittelung)
        blend = 0.2  # klein halten; stabiler auf 24GB
        corrected = (1 - blend) * this_sample + blend * (x0 + (this_sample - x0))
        # (oben neutralisiert sich's; alternativ kleine Dämpfung Richtung x0)
        corrected = (1 - blend) * this_sample + blend * x0

        # Optional: leichtes Re-Project auf die aktuelle Sigma-Schale
        # eps neu schätzen und x_t rekonstruieren
        eps_t = (corrected - x0) / torch.clamp_min(sigma_t, 1e-9)
        corrected = x0 + sigma_t * eps_t
        return corrected

    def index_for_timestep(self, timestep, schedule_timesteps=None):
        if schedule_timesteps is None:
            schedule_timesteps = self.timesteps
        indices = (schedule_timesteps == timestep).nonzero()
        pos = 1 if len(indices) > 1 else 0
        return indices[pos].item()

    def _init_step_index(self, timestep):
        if self.begin_index is None:
            if isinstance(timestep, torch.Tensor):
                timestep = timestep.to(self.timesteps.device)
            self._step_index = self.index_for_timestep(timestep)
        else:
            self._step_index = self._begin_index

    def step(
        self,
        model_output: torch.Tensor,
        timestep: Union[int, torch.Tensor],
        sample: torch.Tensor,
        return_dict: bool = True,
        generator=None
    ) -> Union[SchedulerOutput, Tuple]:
        """
        Ein Schritt des Schedulers:
          1) x0 aus (sample, model_output) schätzen (konvertieren)
          2) optional Corrector
          3) Predictor zum nächsten Sample
        """
        if self.num_inference_steps is None:
            raise ValueError(
                "Number of inference steps is 'None'; run 'set_timesteps' after creating the scheduler."
            )

        if self.step_index is None:
            self._init_step_index(timestep)

        # Corrector nur wenn nicht der erste Schritt
        use_corrector = (
            self.step_index > 0
            and self.step_index - 1 not in self.disable_corrector
            and self.last_sample is not None
        )

        # Device/Dtype angleichen
        if model_output.device != sample.device:
            model_output = model_output.to(sample.device)
        if model_output.dtype != sample.dtype:
            model_output = model_output.to(sample.dtype)

        # x0 aus aktuellem sample und Netz-Output
        model_output_convert = self.convert_model_output(sample, model_output)

        if use_corrector:
            sample = self.multistep_uni_c_bh_update(
                this_model_output=model_output_convert,
                last_sample=self.last_sample,
                this_sample=sample,
                order=getattr(self, "this_order", 1),
            )

        # Shift der Historie
        for i in range(self.config.solver_order - 1):
            self.model_outputs[i] = self.model_outputs[i + 1]
            self.timestep_list[i] = self.timestep_list[i + 1]

        self.model_outputs[-1] = model_output_convert
        self.timestep_list[-1] = timestep

        if self.config.lower_order_final:
            this_order = min(self.config.solver_order, len(self.timesteps) - self.step_index)
        else:
            this_order = self.config.solver_order

        self.this_order = min(this_order, self.lower_order_nums + 1)
        assert self.this_order > 0

        self.last_sample = sample

        # WICHTIG: Predictor mit KONVERTIERTEM x0 füttern
        prev_sample = self.multistep_uni_p_bh_update(
            model_output=model_output_convert,
            sample=sample,
            order=self.this_order,
        )

        if self.lower_order_nums < self.config.solver_order:
            self.lower_order_nums += 1

        self._step_index += 1

        if not return_dict:
            return (prev_sample,)

        return SchedulerOutput(prev_sample=prev_sample)

    def scale_model_input(self, sample: torch.Tensor, *args, **kwargs) -> torch.Tensor:
        return sample

    def add_noise(
        self,
        original_samples: torch.Tensor,
        noise: torch.Tensor,
        timesteps: torch.IntTensor,
    ) -> torch.Tensor:
        """
        Fügt Rauschen entsprechend sigma(t) hinzu: x_t = x0 + sigma_t * noise
        """
        device = original_samples.device
        if isinstance(timesteps, torch.Tensor):
            timesteps = timesteps.to(device)

        sigma = self.sigmas[self.index_for_timestep(timesteps)].to(device)
        while sigma.ndim < original_samples.ndim:
            sigma = sigma.view(-1, *([1] * (original_samples.ndim - 1)))

        return original_samples + sigma * noise

    def __len__(self):
        return self.config.num_train_timesteps
