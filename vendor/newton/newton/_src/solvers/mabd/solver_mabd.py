# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import numpy as np
import warp as wp

from ...core.types import override
from ...sim import Contacts, Control, Model, ModelBuilder, State
from ..solver import SolverBase
from .affine_math import pack_q, tetra_volume
from .control_forces import actuation_specs_from_model
from .single_body import SingleBodyABDPrecompute
from .step_oracle import MABDCPUOracleBody, MABDCPUOracleConfig, MABDCPUOracleStepResult, solve_cpu_oracle_step


class SolverMABD(SolverBase):
    """Multi-Affine-Body Dynamics solver shell with configured CPU oracle stepping.

    This class registers M-ABD model/state storage and owns invalidation of dense
    single-body caches. Phase 4 adds a guarded CPU oracle step path for tests and
    records; full contacts, scenes, and Warp kernels are intentionally unclaimed.
    """

    MABD_BODY_FREQUENCY = "mabd:body"
    MABD_CONSTRAINT_FREQUENCY = "mabd:constraint"
    MABD_CONTROL_FREQUENCY = "mabd:control"

    def __init__(self, model: Model):
        super().__init__(model=model)
        self.model_version = 0
        self.hessian_caches = []
        self.cpu_oracle_config: MABDCPUOracleConfig | None = None
        self.model_cpu_oracle_config: MABDCPUOracleConfig | None = None
        self.model_cpu_oracle_version = -1
        self.last_step_result: MABDCPUOracleStepResult | None = None

    def configure_cpu_oracle(self, config: MABDCPUOracleConfig | None) -> None:
        self.cpu_oracle_config = config
        self.last_step_result = None

    @staticmethod
    def _rotation_mode_from_model(value: int) -> str:
        modes = {0: "none", 1: "polar", 2: "no_polar"}
        mode = modes.get(int(value))
        if mode is None:
            raise ValueError("mabd:polar_mode must be 0 (none), 1 (polar), or 2 (no_polar)")
        return mode

    def _body_precompute_from_model_row(self, row: int) -> MABDCPUOracleBody:
        namespace = self.model.mabd
        rest_points = np.asarray(
            [
                namespace.rest_point0.numpy()[row],
                namespace.rest_point1.numpy()[row],
                namespace.rest_point2.numpy()[row],
                namespace.rest_point3.numpy()[row],
            ],
            dtype=float,
        )
        volume_value = float(namespace.volume.numpy()[row])
        volume = tetra_volume(rest_points) if volume_value < 0.0 else volume_value
        if volume <= 0.0:
            raise ValueError("mabd:volume must be positive or negative for tetra-volume derivation")

        density = float(namespace.density.numpy()[row])
        point_masses = np.asarray(
            [
                namespace.point_mass0.numpy()[row],
                namespace.point_mass1.numpy()[row],
                namespace.point_mass2.numpy()[row],
                namespace.point_mass3.numpy()[row],
            ],
            dtype=float,
        )
        explicit_masses = point_masses >= 0.0
        if np.all(explicit_masses):
            masses = point_masses
        elif not np.any(explicit_masses):
            if density <= 0.0:
                raise ValueError("mabd:density must be positive when point masses are derived")
            masses = np.full(4, density * volume / 4.0, dtype=float)
        else:
            raise ValueError("mabd:point_mass0..3 must be all explicit or all derived")
        if np.any(masses <= 0.0):
            raise ValueError("mabd point masses must be positive")

        young_modulus = float(namespace.young_modulus.numpy()[row])
        poisson_ratio = float(namespace.poisson_ratio.numpy()[row])
        precompute = SingleBodyABDPrecompute.from_linear_elastic_points(
            rest_points,
            masses,
            young_modulus=young_modulus,
            poisson_ratio=poisson_ratio,
            volume=volume,
        )
        return MABDCPUOracleBody(
            precompute=precompute,
            rest_q=pack_q(np.eye(3), np.zeros(3)),
            rotation_mode=self._rotation_mode_from_model(int(namespace.polar_mode.numpy()[row])),
        )

    def _custom_frequency_count(self, frequency: str) -> int:
        try:
            return int(self.model.get_custom_frequency_count(frequency))
        except KeyError as exc:
            raise ValueError(
                "model-derived SolverMABD.step() requires SolverMABD.register_custom_attributes(...) "
                "and at least one mabd:body row"
            ) from exc

    def _cpu_oracle_config_from_model(self) -> MABDCPUOracleConfig:
        if (
            self.model_cpu_oracle_config is not None
            and self.model_cpu_oracle_version == self.model_version
        ):
            return self.model_cpu_oracle_config

        body_count = self._custom_frequency_count(self.MABD_BODY_FREQUENCY)
        if body_count <= 0:
            raise ValueError("model-derived SolverMABD.step() requires at least one mabd:body row")
        constraint_count = self._custom_frequency_count(self.MABD_CONSTRAINT_FREQUENCY)
        if constraint_count:
            raise NotImplementedError(
                "model-derived SolverMABD.step() does not support mabd:constraint rows yet; "
                "provide configure_cpu_oracle(...) with explicit MABDCPUOracleConstraint specs"
            )
        config = MABDCPUOracleConfig(
            bodies=tuple(self._body_precompute_from_model_row(row) for row in range(body_count)),
            actuations=actuation_specs_from_model(self.model),
        )
        self.model_cpu_oracle_config = config
        self.model_cpu_oracle_version = self.model_version
        return config

    @staticmethod
    def _read_mabd_state(state: State) -> tuple[tuple[np.ndarray, ...], tuple[np.ndarray, ...]]:
        q0 = state.mabd.q0.numpy().copy()
        q1 = state.mabd.q1.numpy().copy()
        q2 = state.mabd.q2.numpy().copy()
        t = state.mabd.t.numpy().copy()
        qd0 = state.mabd.qd0.numpy().copy()
        qd1 = state.mabd.qd1.numpy().copy()
        qd2 = state.mabd.qd2.numpy().copy()
        td = state.mabd.td.numpy().copy()
        count = q0.shape[0]
        q = tuple(np.concatenate((q0[i], q1[i], q2[i], t[i])).astype(float, copy=False) for i in range(count))
        qd = tuple(np.concatenate((qd0[i], qd1[i], qd2[i], td[i])).astype(float, copy=False) for i in range(count))
        return q, qd

    @staticmethod
    def _write_mabd_state(state: State, q: tuple[np.ndarray, ...], qd: tuple[np.ndarray, ...]) -> None:
        q_arr = np.asarray(q, dtype=np.float32)
        qd_arr = np.asarray(qd, dtype=np.float32)
        expected_shape = (state.mabd.q0.numpy().shape[0], 12)
        if q_arr.shape != expected_shape:
            raise ValueError(f"q output must have shape {expected_shape}, got {q_arr.shape}")
        if qd_arr.shape != expected_shape:
            raise ValueError(f"qd output must have shape {expected_shape}, got {qd_arr.shape}")
        state.mabd.q0.assign(q_arr[:, 0:3])
        state.mabd.q1.assign(q_arr[:, 3:6])
        state.mabd.q2.assign(q_arr[:, 6:9])
        state.mabd.t.assign(q_arr[:, 9:12])
        state.mabd.qd0.assign(qd_arr[:, 0:3])
        state.mabd.qd1.assign(qd_arr[:, 3:6])
        state.mabd.qd2.assign(qd_arr[:, 6:9])
        state.mabd.td.assign(qd_arr[:, 9:12])

    @override
    def step(
        self,
        state_in: State,
        state_out: State,
        control: Control | None,
        contacts: Contacts | None,
        dt: float,
    ) -> None:
        if control is not None:
            raise NotImplementedError("SolverMABD Phase 4 CPU oracle step does not support Control input")
        if contacts is not None:
            raise NotImplementedError("SolverMABD Phase 4 CPU oracle step does not support Contacts input")
        config = self.cpu_oracle_config if self.cpu_oracle_config is not None else self._cpu_oracle_config_from_model()
        q, qd = self._read_mabd_state(state_in)
        result = solve_cpu_oracle_step(q=q, qd=qd, dt=dt, config=config)
        if state_out is not state_in:
            state_out.assign(state_in)
        self._write_mabd_state(state_out, result.q, result.qd)
        self.last_step_result = result

    @override
    def notify_model_changed(self, flags: int) -> None:
        self.model_version += 1
        self.model_cpu_oracle_config = None
        self.model_cpu_oracle_version = -1
        for cache in self.hessian_caches:
            cache.clear()

    @classmethod
    @override
    def register_custom_attributes(cls, builder: ModelBuilder) -> None:
        builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="body", namespace="mabd"))
        builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="constraint", namespace="mabd"))
        builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="control", namespace="mabd"))

        model_attrs = (
            ModelBuilder.CustomAttribute(
                name="body_index",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=-1,
                namespace="mabd",
                references="body",
            ),
            ModelBuilder.CustomAttribute(
                name="young_modulus",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=1.0e6,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="poisson_ratio",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=0.3,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="density",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=1.0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="polar_mode",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="rest_point0",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="rest_point1",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(1.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="rest_point2",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 1.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="rest_point3",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 1.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="point_mass0",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=-1.0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="point_mass1",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=-1.0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="point_mass2",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=-1.0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="point_mass3",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=-1.0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="volume",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=-1.0,
                namespace="mabd",
            ),
        )

        state_attrs = (
            ModelBuilder.CustomAttribute(
                name="q0",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.STATE,
                dtype=wp.vec3,
                default=wp.vec3(1.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="q1",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.STATE,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 1.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="q2",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.STATE,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 1.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="t",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.STATE,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="qd0",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.STATE,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="qd1",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.STATE,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="qd2",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.STATE,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="td",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.STATE,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
        )

        constraint_attrs = (
            ModelBuilder.CustomAttribute(
                name="constraint_type",
                frequency=cls.MABD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="body_a",
                frequency=cls.MABD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=-1,
                namespace="mabd",
                references=cls.MABD_BODY_FREQUENCY,
            ),
            ModelBuilder.CustomAttribute(
                name="body_b",
                frequency=cls.MABD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=-1,
                namespace="mabd",
                references=cls.MABD_BODY_FREQUENCY,
            ),
            ModelBuilder.CustomAttribute(
                name="rank",
                frequency=cls.MABD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="gradient_mode",
                frequency=cls.MABD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="axis0",
                frequency=cls.MABD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 1.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="axis1",
                frequency=cls.MABD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 1.0),
                namespace="mabd",
            ),
        )

        control_attrs = (
            ModelBuilder.CustomAttribute(
                name="control_body",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=-1,
                namespace="mabd",
                references=cls.MABD_BODY_FREQUENCY,
            ),
            ModelBuilder.CustomAttribute(
                name="control_enabled",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_stiffness",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=0.0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_damping",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=0.0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_target_q0",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(1.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_target_q1",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 1.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_target_q2",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 1.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_target_t",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_target_qd0",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_target_qd1",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_target_qd2",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_target_td",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_feedforward_q0",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_feedforward_q1",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_feedforward_q2",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="control_feedforward_t",
                frequency=cls.MABD_CONTROL_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
        )

        for attr in (*model_attrs, *state_attrs, *constraint_attrs, *control_attrs):
            builder.add_custom_attribute(attr)


__all__ = ["SolverMABD"]
