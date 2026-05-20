# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import warp as wp

from ...core.types import override
from ...sim import BodyFlags, Contacts, Control, Model, State
from ..semi_implicit.kernels_body import eval_body_joint_forces
from ..semi_implicit.kernels_contact import (
    eval_body_contact_forces,
    eval_particle_body_contact_forces,
)
from ..solver import SolverBase


@wp.func
def integrate_rigid_body_explicit(
    q: wp.transform,
    qd: wp.spatial_vector,
    f: wp.spatial_vector,
    com: wp.vec3,
    inertia: wp.mat33,
    inv_mass: float,
    inv_inertia: wp.mat33,
    gravity: wp.vec3,
    angular_damping: float,
    dt: float,
):
    x0 = wp.transform_get_translation(q)
    r0 = wp.transform_get_rotation(q)

    w0 = wp.spatial_bottom(qd)
    v0 = wp.spatial_top(qd)

    t0 = wp.spatial_bottom(f)
    f0 = wp.spatial_top(f)

    x_com0 = x0 + wp.quat_rotate(r0, com)

    # Explicit Euler advances pose from the old velocity.
    x1 = x_com0 + v0 * dt
    r1 = wp.normalize(r0 + wp.quat(w0, 0.0) * r0 * 0.5 * dt)

    wb = wp.quat_rotate_inv(r0, w0)
    tb = wp.quat_rotate_inv(r0, t0) - wp.cross(wb, inertia * wb)

    v1 = v0 + (f0 * inv_mass + gravity * wp.nonzero(inv_mass)) * dt
    w1 = wp.quat_rotate(r0, wb + inv_inertia * tb * dt)
    w1 *= 1.0 - angular_damping * dt

    q_new = wp.transform(x1 - wp.quat_rotate(r1, com), r1)
    qd_new = wp.spatial_vector(v1, w1)
    return q_new, qd_new


@wp.kernel
def integrate_bodies_explicit(
    body_q: wp.array[wp.transform],
    body_qd: wp.array[wp.spatial_vector],
    body_f: wp.array[wp.spatial_vector],
    body_com: wp.array[wp.vec3],
    m: wp.array[float],
    I: wp.array[wp.mat33],
    inv_m: wp.array[float],
    inv_I: wp.array[wp.mat33],
    body_flags: wp.array[wp.int32],
    body_world: wp.array[wp.int32],
    gravity: wp.array[wp.vec3],
    angular_damping: float,
    dt: float,
    body_q_new: wp.array[wp.transform],
    body_qd_new: wp.array[wp.spatial_vector],
):
    tid = wp.tid()

    if (body_flags[tid] & BodyFlags.KINEMATIC) != 0:
        body_q_new[tid] = body_q[tid]
        body_qd_new[tid] = body_qd[tid]
        return

    world_idx = body_world[tid]
    q_new, qd_new = integrate_rigid_body_explicit(
        body_q[tid],
        body_qd[tid],
        body_f[tid],
        body_com[tid],
        I[tid],
        inv_m[tid],
        inv_I[tid],
        gravity[wp.max(world_idx, 0)],
        angular_damping,
        dt,
    )
    body_q_new[tid] = q_new
    body_qd_new[tid] = qd_new


class SolverExplicitEuler(SolverBase):
    """Rigid-body explicit Euler integrator for Newton development baselines.

    This local solver is intentionally small. It reuses Newton's current-state
    rigid-body force and contact force path, then advances pose from old
    velocity before updating velocity from the accumulated forces.
    """

    def __init__(
        self,
        model: Model,
        angular_damping: float = 0.05,
        friction_smoothing: float = 1.0,
        joint_attach_ke: float = 1.0e4,
        joint_attach_kd: float = 1.0e2,
    ):
        super().__init__(model=model)
        self.angular_damping = angular_damping
        self.friction_smoothing = friction_smoothing
        self.joint_attach_ke = joint_attach_ke
        self.joint_attach_kd = joint_attach_kd

    def integrate_bodies_explicit(
        self,
        model: Model,
        state_in: State,
        state_out: State,
        dt: float,
        angular_damping: float = 0.0,
    ) -> None:
        if model.body_count:
            wp.launch(
                kernel=integrate_bodies_explicit,
                dim=model.body_count,
                inputs=[
                    state_in.body_q,
                    state_in.body_qd,
                    state_in.body_f,
                    model.body_com,
                    model.body_mass,
                    model.body_inertia,
                    model.body_inv_mass,
                    model.body_inv_inertia,
                    model.body_flags,
                    model.body_world,
                    model.gravity,
                    angular_damping,
                    dt,
                ],
                outputs=[state_out.body_q, state_out.body_qd],
                device=model.device,
            )

    @override
    def step(
        self,
        state_in: State,
        state_out: State,
        control: Control | None,
        contacts: Contacts | None,
        dt: float,
    ) -> None:
        if state_in.particle_count:
            raise NotImplementedError("SolverExplicitEuler currently supports rigid bodies only")

        with wp.ScopedTimer("simulate", False):
            body_f = state_in.body_f if state_in.body_count else None
            model = self.model

            if control is None:
                control = model.control(clone_variables=False)

            body_f_work = body_f
            if body_f is not None and model.joint_count and control.joint_f is not None:
                body_f_work = wp.clone(body_f)

            eval_body_joint_forces(
                model,
                state_in,
                control,
                body_f_work,
                self.joint_attach_ke,
                self.joint_attach_kd,
            )
            eval_body_contact_forces(
                model,
                state_in,
                contacts,
                friction_smoothing=self.friction_smoothing,
                body_f_out=body_f_work,
            )
            eval_particle_body_contact_forces(
                model,
                state_in,
                contacts,
                None,
                body_f_work,
                body_f_in_world_frame=False,
            )

            if body_f_work is body_f:
                self.integrate_bodies_explicit(
                    model,
                    state_in,
                    state_out,
                    dt,
                    self.angular_damping,
                )
            else:
                body_f_prev = state_in.body_f
                state_in.body_f = body_f_work
                self.integrate_bodies_explicit(
                    model,
                    state_in,
                    state_out,
                    dt,
                    self.angular_damping,
                )
                state_in.body_f = body_f_prev
