# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import warp as wp

from ...core.types import override
from ...sim import Contacts, Control, Model, ModelBuilder, State
from ..solver import SolverBase
from .affine_math import pack_q, tetra_volume
from .control_forces import actuation_specs_from_model
from .joint_constraints import (
    JointGradientMode,
    ball_joint,
    evaluate_joint,
    hinge_joint,
    prismatic_joint,
    universal_joint,
)
from .single_body import SingleBodyABDPrecompute
from .step_oracle import (
    MABDCPUOracleBody,
    MABDCPUOracleConfig,
    MABDCPUOracleConstraint,
    MABDCPUOraclePlaneConstraint,
    MABDCPUOracleStepResult,
    MABDCPUOracleWorldConstraint,
    solve_cpu_oracle_step,
)


@dataclass(frozen=True)
class MABDContactsInputSummary:
    policy: str
    rigid_contact_count: int
    rigid_contact_capacity: int
    rigid_contact_overflow_count: int
    rigid_contact_rows_read: int
    generated_plane_constraint_count: int
    skipped_contact_count: int
    source: str
    scope: str


class SolverMABD(SolverBase):
    """Multi-Affine-Body Dynamics solver shell with configured CPU oracle stepping.

    This class registers M-ABD model/state storage and owns invalidation of dense
    single-body caches. Phase 4 adds a guarded CPU oracle step path for tests and
    records; full contacts, scenes, and Warp kernels are intentionally unclaimed.
    """

    MABD_BODY_FREQUENCY = "mabd:body"
    MABD_CONSTRAINT_FREQUENCY = "mabd:constraint"
    MABD_WORLD_CONSTRAINT_FREQUENCY = "mabd:world_constraint"
    MABD_PLANE_CONSTRAINT_FREQUENCY = "mabd:plane_constraint"
    MABD_GRAVITY_FREQUENCY = "mabd:gravity"
    MABD_CONTROL_FREQUENCY = "mabd:control"

    def __init__(self, model: Model):
        super().__init__(model=model)
        self.model_version = 0
        self.hessian_caches = []
        self.cpu_oracle_config: MABDCPUOracleConfig | None = None
        self.model_cpu_oracle_config: MABDCPUOracleConfig | None = None
        self.model_cpu_oracle_version = -1
        self.last_step_result: MABDCPUOracleStepResult | None = None
        self.last_contacts_input_summary: MABDContactsInputSummary | None = None

    def configure_cpu_oracle(self, config: MABDCPUOracleConfig | None) -> None:
        self.cpu_oracle_config = config
        self.last_step_result = None
        self.last_contacts_input_summary = None

    @staticmethod
    def _rotation_mode_from_model(value: int) -> str:
        modes = {0: "none", 1: "polar", 2: "no_polar"}
        mode = modes.get(int(value))
        if mode is None:
            raise ValueError("mabd:polar_mode must be 0 (none), 1 (polar), or 2 (no_polar)")
        return mode

    def _rest_points_from_model_body_row(self, row: int) -> np.ndarray:
        namespace = self.model.mabd
        return np.asarray(
            [
                namespace.rest_point0.numpy()[row],
                namespace.rest_point1.numpy()[row],
                namespace.rest_point2.numpy()[row],
                namespace.rest_point3.numpy()[row],
            ],
            dtype=float,
        )

    def _body_precompute_from_model_row(self, row: int) -> MABDCPUOracleBody:
        namespace = self.model.mabd
        rest_points = self._rest_points_from_model_body_row(row)
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
        if young_modulus == 0.0 and int(namespace.zero_stiffness_diagnostic.numpy()[row]) != 0:
            precompute = SingleBodyABDPrecompute.from_points(rest_points, masses)
        else:
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

    @staticmethod
    def _joint_gradient_mode_from_model(value: int) -> JointGradientMode:
        modes = {
            0: JointGradientMode.FINITE_DIFFERENCE_ORACLE,
            1: JointGradientMode.PAPER_FAITHFUL,
        }
        mode = modes.get(int(value))
        if mode is None:
            raise ValueError("mabd:gradient_mode must be 0 (finite_difference_oracle) or 1 (paper_faithful)")
        return mode

    @staticmethod
    def _joint_spec_rank(spec: object) -> int:
        evaluation = evaluate_joint(
            spec,
            np.zeros(12, dtype=float),
            np.zeros(12, dtype=float),
            gradient_mode=JointGradientMode.FINITE_DIFFERENCE_ORACLE,
        )
        return int(evaluation.rank)

    def _constraint_from_model_row(self, row: int, body_count: int) -> MABDCPUOracleConstraint:
        namespace = self.model.mabd
        body_a = int(namespace.body_a.numpy()[row])
        body_b = int(namespace.body_b.numpy()[row])
        if not 0 <= body_a < body_count or not 0 <= body_b < body_count:
            raise ValueError("mabd:constraint body indices must reference mabd:body rows")

        rank = int(namespace.rank.numpy()[row])
        constraint_type = int(namespace.constraint_type.numpy()[row])
        ct_a = self._rest_points_from_model_body_row(body_a)
        ct_b = self._rest_points_from_model_body_row(body_b)
        axis0 = namespace.axis0.numpy()[row]
        axis1 = namespace.axis1.numpy()[row]
        cp_index = int(namespace.cp_index.numpy()[row])

        if constraint_type in (0, 1):
            if rank == 3:
                spec = ball_joint(ct_a, ct_b, cp_index=cp_index)
            elif rank == 4:
                spec = universal_joint(ct_a, ct_b, axis0=axis0, axis1=axis1)
            elif rank == 5:
                spec = hinge_joint(ct_a, ct_b, axis=axis0)
            else:
                raise ValueError("mabd:rank must be 3, 4, or 5 for inferred mabd:constraint rows")
        elif constraint_type == 2:
            spec = ball_joint(ct_a, ct_b, cp_index=cp_index)
        elif constraint_type == 3:
            spec = hinge_joint(ct_a, ct_b, axis=axis0)
        elif constraint_type == 4:
            spec = universal_joint(ct_a, ct_b, axis0=axis0, axis1=axis1)
        elif constraint_type == 5:
            spec = prismatic_joint(ct_a, ct_b, axis=axis0)
        else:
            raise ValueError("mabd:constraint_type must be 0..5")

        spec_rank = self._joint_spec_rank(spec)
        if rank != spec_rank:
            raise ValueError(f"mabd:rank must be {spec_rank} for constraint_type={constraint_type}")

        return MABDCPUOracleConstraint(
            body_a=body_a,
            body_b=body_b,
            spec=spec,
            gradient_mode=self._joint_gradient_mode_from_model(int(namespace.gradient_mode.numpy()[row])),
        )

    def _world_constraint_from_model_row(self, row: int, body_count: int) -> MABDCPUOracleWorldConstraint:
        namespace = self.model.mabd
        body = int(namespace.world_body.numpy()[row])
        if not 0 <= body < body_count:
            raise ValueError("mabd:world_body must reference a mabd:body row")
        return MABDCPUOracleWorldConstraint(
            body=body,
            rest_point=np.asarray(namespace.world_rest_point.numpy()[row], dtype=float),
            world_point=np.asarray(namespace.world_point.numpy()[row], dtype=float),
        )

    def _plane_constraint_from_model_row(self, row: int, body_count: int) -> MABDCPUOraclePlaneConstraint:
        namespace = self.model.mabd
        body = int(namespace.plane_body.numpy()[row])
        if not 0 <= body < body_count:
            raise ValueError("mabd:plane_body must reference a mabd:body row")
        return MABDCPUOraclePlaneConstraint(
            body=body,
            rest_point=np.asarray(namespace.plane_rest_point.numpy()[row], dtype=float),
            plane_normal=np.asarray(namespace.plane_normal.numpy()[row], dtype=float),
            plane_offset=float(namespace.plane_offset.numpy()[row]),
            active=bool(int(namespace.plane_active.numpy()[row])),
        )

    def _gravity_from_model(self) -> np.ndarray | None:
        count = self._custom_frequency_count(self.MABD_GRAVITY_FREQUENCY)
        namespace = self.model.mabd
        enabled_rows = [
            row
            for row in range(count)
            if int(namespace.gravity_enabled.numpy()[row]) != 0
        ]
        if not enabled_rows:
            return None
        if len(enabled_rows) > 1:
            raise ValueError("mabd:gravity supports at most one enabled row")
        return np.asarray(namespace.gravity_vector.numpy()[enabled_rows[0]], dtype=float)

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
        world_constraint_count = self._custom_frequency_count(self.MABD_WORLD_CONSTRAINT_FREQUENCY)
        plane_constraint_count = self._custom_frequency_count(self.MABD_PLANE_CONSTRAINT_FREQUENCY)
        config = MABDCPUOracleConfig(
            bodies=tuple(self._body_precompute_from_model_row(row) for row in range(body_count)),
            constraints=tuple(self._constraint_from_model_row(row, body_count) for row in range(constraint_count)),
            world_constraints=tuple(
                self._world_constraint_from_model_row(row, body_count)
                for row in range(world_constraint_count)
            ),
            plane_constraints=tuple(
                self._plane_constraint_from_model_row(row, body_count)
                for row in range(plane_constraint_count)
            ),
            gravity=self._gravity_from_model(),
            actuations=actuation_specs_from_model(self.model),
        )
        self.model_cpu_oracle_config = config
        self.model_cpu_oracle_version = self.model_version
        return config

    def _mabd_body_row_by_newton_body(self) -> dict[int, int]:
        namespace = self.model.mabd
        body_indices = np.asarray(namespace.body_index.numpy(), dtype=int)
        mapping: dict[int, int] = {}
        for row, newton_body in enumerate(body_indices):
            body_id = int(newton_body)
            if body_id < 0:
                continue
            if body_id in mapping:
                raise ValueError("duplicate mabd:body_index mapping for Newton body")
            mapping[body_id] = row
        return mapping

    def _plane_constraints_from_contacts(self, contacts: Contacts) -> tuple[MABDCPUOraclePlaneConstraint, ...]:
        reported_count = max(0, int(contacts.rigid_contact_count.numpy()[0]))
        capacity = int(contacts.rigid_contact_max)
        rows_read = min(reported_count, capacity)
        overflow_count = max(0, reported_count - capacity)
        generated: list[MABDCPUOraclePlaneConstraint] = []
        skipped_count = overflow_count

        if rows_read > 0:
            if self.model.shape_body is None:
                raise ValueError("SolverMABD Contacts input requires model.shape_body")
            shape_body = np.asarray(self.model.shape_body.numpy(), dtype=int)
            body_rows = self._mabd_body_row_by_newton_body()
            shape0_values = np.asarray(contacts.rigid_contact_shape0.numpy()[:rows_read], dtype=int)
            shape1_values = np.asarray(contacts.rigid_contact_shape1.numpy()[:rows_read], dtype=int)
            point0_values = np.asarray(contacts.rigid_contact_point0.numpy()[:rows_read], dtype=float)
            point1_values = np.asarray(contacts.rigid_contact_point1.numpy()[:rows_read], dtype=float)
            normal_values = np.asarray(contacts.rigid_contact_normal.numpy()[:rows_read], dtype=float)

            for shape0, shape1, point0, point1, normal in zip(
                shape0_values,
                shape1_values,
                point0_values,
                point1_values,
                normal_values,
                strict=True,
            ):
                shape0_id = int(shape0)
                shape1_id = int(shape1)
                if not 0 <= shape0_id < len(shape_body) or not 0 <= shape1_id < len(shape_body):
                    skipped_count += 1
                    continue

                mabd_body0 = body_rows.get(int(shape_body[shape0_id]))
                mabd_body1 = body_rows.get(int(shape_body[shape1_id]))
                if (mabd_body0 is None) == (mabd_body1 is None):
                    skipped_count += 1
                    continue

                if mabd_body0 is not None:
                    body = mabd_body0
                    rest_point = point0
                    plane_normal = normal
                    plane_point = point1
                else:
                    body = int(mabd_body1)
                    rest_point = point1
                    plane_normal = -normal
                    plane_point = point0

                generated.append(
                    MABDCPUOraclePlaneConstraint(
                        body=int(body),
                        rest_point=np.asarray(rest_point, dtype=float),
                        plane_normal=np.asarray(plane_normal, dtype=float),
                        plane_offset=float(np.dot(plane_normal, plane_point)),
                    )
                )

        self.last_contacts_input_summary = MABDContactsInputSummary(
            policy="rigid_contacts_to_point_plane_constraints_diagnostic",
            rigid_contact_count=reported_count,
            rigid_contact_capacity=capacity,
            rigid_contact_overflow_count=overflow_count,
            rigid_contact_rows_read=rows_read,
            generated_plane_constraint_count=len(generated),
            skipped_contact_count=skipped_count,
            source="newton.Contacts.rigid_contact_*",
            scope="diagnostic_only_static_geometry_plane_constraints",
        )
        return tuple(generated)

    def _cpu_oracle_config_with_contacts(
        self,
        config: MABDCPUOracleConfig,
        contacts: Contacts | None,
    ) -> MABDCPUOracleConfig:
        if contacts is None:
            self.last_contacts_input_summary = None
            return config

        contact_plane_constraints = self._plane_constraints_from_contacts(contacts)
        if not contact_plane_constraints:
            return config
        return replace(
            config,
            plane_constraints=tuple(config.plane_constraints) + contact_plane_constraints,
        )

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
        config = self.cpu_oracle_config if self.cpu_oracle_config is not None else self._cpu_oracle_config_from_model()
        config = self._cpu_oracle_config_with_contacts(config, contacts)
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
        builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="world_constraint", namespace="mabd"))
        builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="plane_constraint", namespace="mabd"))
        builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="gravity", namespace="mabd"))
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
            ModelBuilder.CustomAttribute(
                name="zero_stiffness_diagnostic",
                frequency=cls.MABD_BODY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=0,
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
                name="cp_index",
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

        world_constraint_attrs = (
            ModelBuilder.CustomAttribute(
                name="world_body",
                frequency=cls.MABD_WORLD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=-1,
                namespace="mabd",
                references=cls.MABD_BODY_FREQUENCY,
            ),
            ModelBuilder.CustomAttribute(
                name="world_rest_point",
                frequency=cls.MABD_WORLD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="world_point",
                frequency=cls.MABD_WORLD_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
        )

        plane_constraint_attrs = (
            ModelBuilder.CustomAttribute(
                name="plane_body",
                frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=-1,
                namespace="mabd",
                references=cls.MABD_BODY_FREQUENCY,
            ),
            ModelBuilder.CustomAttribute(
                name="plane_rest_point",
                frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="plane_normal",
                frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 1.0, 0.0),
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="plane_offset",
                frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.float32,
                default=0.0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="plane_active",
                frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=1,
                namespace="mabd",
            ),
        )

        gravity_attrs = (
            ModelBuilder.CustomAttribute(
                name="gravity_enabled",
                frequency=cls.MABD_GRAVITY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.int32,
                default=0,
                namespace="mabd",
            ),
            ModelBuilder.CustomAttribute(
                name="gravity_vector",
                frequency=cls.MABD_GRAVITY_FREQUENCY,
                assignment=Model.AttributeAssignment.MODEL,
                dtype=wp.vec3,
                default=wp.vec3(0.0, 0.0, 0.0),
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

        for attr in (
            *model_attrs,
            *state_attrs,
            *constraint_attrs,
            *world_constraint_attrs,
            *plane_constraint_attrs,
            *gravity_attrs,
            *control_attrs,
        ):
            builder.add_custom_attribute(attr)


__all__ = ["SolverMABD"]
