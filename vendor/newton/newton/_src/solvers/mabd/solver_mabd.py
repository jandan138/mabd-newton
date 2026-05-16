# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import warp as wp

from ...core.types import override
from ...sim import Contacts, Control, Model, ModelBuilder, State
from ..solver import SolverBase


class SolverMABD(SolverBase):
    """Phase 1 shell for Multi-Affine-Body Dynamics.

    This class registers M-ABD model/state storage and owns invalidation of dense
    single-body caches. Full time stepping, joints, and contact are added in later
    phases and are intentionally not claimed here.
    """

    MABD_BODY_FREQUENCY = "mabd:body"
    MABD_CONSTRAINT_FREQUENCY = "mabd:constraint"

    def __init__(self, model: Model):
        super().__init__(model=model)
        self.model_version = 0
        self.hessian_caches = []

    @override
    def step(
        self,
        state_in: State,
        state_out: State,
        control: Control | None,
        contacts: Contacts | None,
        dt: float,
    ) -> None:
        raise NotImplementedError(
            "SolverMABD Phase 1 exposes verified single-body ABD oracles; "
            "time stepping is implemented in later phases."
        )

    @override
    def notify_model_changed(self, flags: int) -> None:
        self.model_version += 1
        for cache in self.hessian_caches:
            cache.clear()

    @classmethod
    @override
    def register_custom_attributes(cls, builder: ModelBuilder) -> None:
        builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="body", namespace="mabd"))
        builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="constraint", namespace="mabd"))

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

        for attr in (*model_attrs, *state_attrs, *constraint_attrs):
            builder.add_custom_attribute(attr)


__all__ = ["SolverMABD"]
