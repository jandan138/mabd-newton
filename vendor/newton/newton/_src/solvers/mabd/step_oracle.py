# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .affine_math import (
    apply_no_polar_increment_rotation,
    apply_no_polar_rhs_rotation,
    apply_polar_increment_rotation,
    apply_polar_rhs_rotation,
    gravity_generalized_force,
    pack_q,
    unpack_q,
)
from .control_forces import MABDActuationSpec, assemble_control_generalized_forces
from .dense_kkt import solve_dense_dual_kkt
from .joint_constraints import JointGradientMode, MABDJointSpec, evaluate_joint, joint_residual
from .single_body import SingleBodyABDPrecompute
from .topology_solvers import (
    assemble_topology_dual_inputs,
    classify_constraint_graph,
    solve_chain_block_tridiagonal_kkt,
    solve_graph_block_gauss_seidel_kkt,
    solve_loop_schur_complement_kkt,
    solve_tree_elimination_kkt,
)


@dataclass(frozen=True)
class MABDCPUOracleBody:
    precompute: SingleBodyABDPrecompute
    rest_q: np.ndarray | None = None
    rotation_mode: str = "none"


@dataclass(frozen=True)
class MABDCPUOracleConstraint:
    body_a: int
    body_b: int
    spec: MABDJointSpec
    gradient_mode: JointGradientMode | str = JointGradientMode.FINITE_DIFFERENCE_ORACLE


@dataclass(frozen=True)
class MABDCPUOracleConfig:
    bodies: tuple[MABDCPUOracleBody, ...] | list[MABDCPUOracleBody]
    constraints: tuple[MABDCPUOracleConstraint, ...] | list[MABDCPUOracleConstraint] = field(default_factory=tuple)
    external_forces: tuple[np.ndarray, ...] | list[np.ndarray] | None = None
    gravity: np.ndarray | None = None
    actuations: tuple[MABDActuationSpec, ...] | list[MABDActuationSpec] = field(default_factory=tuple)
    topology: str = "dense"
    graph_schedule: tuple[tuple[int, ...], ...] | None = None
    residual_correction: bool = True


@dataclass(frozen=True)
class MABDCPUOracleStepResult:
    q: tuple[np.ndarray, ...]
    qd: tuple[np.ndarray, ...]
    dq: np.ndarray
    dlambda: np.ndarray
    residual_norm: float
    constraint_residual_norm: float
    topology: str


def _as_q_blocks(values: Any, name: str) -> tuple[np.ndarray, ...]:
    blocks = tuple(np.asarray(value, dtype=float) for value in values)
    for body_id, block in enumerate(blocks):
        if block.shape != (12,):
            raise ValueError(f"{name}[{body_id}] must have shape (12,), got {block.shape}")
    return blocks


def _body_rest_q(body: MABDCPUOracleBody) -> np.ndarray:
    if body.rest_q is None:
        return pack_q(np.eye(3), np.zeros(3))
    rest_q = np.asarray(body.rest_q, dtype=float)
    if rest_q.shape != (12,):
        raise ValueError(f"body rest_q must have shape (12,), got {rest_q.shape}")
    return rest_q


def _as_external_forces(config: MABDCPUOracleConfig, count: int) -> tuple[np.ndarray, ...]:
    if config.external_forces is None:
        return tuple(np.zeros(12, dtype=float) for _ in range(count))
    forces = tuple(np.asarray(force, dtype=float) for force in config.external_forces)
    if len(forces) != count:
        raise ValueError(f"external_forces must contain {count} vectors, got {len(forces)}")
    for body_id, force in enumerate(forces):
        if force.shape != (12,):
            raise ValueError(f"external_forces[{body_id}] must have shape (12,), got {force.shape}")
    return forces


def _as_gravity_forces(
    config: MABDCPUOracleConfig,
    bodies: tuple[MABDCPUOracleBody, ...],
) -> tuple[np.ndarray, ...]:
    if config.gravity is None:
        return tuple(np.zeros(12, dtype=float) for _body in bodies)
    gravity = np.asarray(config.gravity, dtype=float)
    if gravity.shape != (3,):
        raise ValueError(f"gravity must have shape (3,), got {gravity.shape}")
    return tuple(
        gravity_generalized_force(body.precompute.rest_points, body.precompute.masses, gravity)
        for body in bodies
    )


def _validate_config(config: MABDCPUOracleConfig, body_count: int) -> tuple[MABDCPUOracleBody, ...]:
    bodies = tuple(config.bodies)
    if len(bodies) != body_count:
        raise ValueError(f"config.bodies must contain {body_count} entries, got {len(bodies)}")
    for body_id, body in enumerate(bodies):
        if not isinstance(body.precompute, SingleBodyABDPrecompute):
            raise TypeError(f"config.bodies[{body_id}].precompute must be SingleBodyABDPrecompute")
        if body.rotation_mode not in {"none", "polar", "no_polar"}:
            raise ValueError("rotation_mode must be one of 'none', 'polar', or 'no_polar'")
    constraints = tuple(config.constraints)
    for constraint_id, constraint in enumerate(constraints):
        if not 0 <= int(constraint.body_a) < body_count or not 0 <= int(constraint.body_b) < body_count:
            raise ValueError(f"constraint {constraint_id} references a body outside [0, {body_count})")
    return bodies


def _require_constrained_none_rotation(bodies: tuple[MABDCPUOracleBody, ...]) -> None:
    for body_id, body in enumerate(bodies):
        if body.rotation_mode != "none":
            raise NotImplementedError(
                "constrained CPU oracle steps require rotation_mode='none' "
                f"until rotated KKT assembly is implemented; body {body_id} "
                f"uses rotation_mode={body.rotation_mode!r}"
            )


def _affine_only_no_polar_rhs(A: np.ndarray, rhs: np.ndarray) -> np.ndarray:
    affine_rhs = np.zeros(12, dtype=float)
    affine_rhs[:9] = rhs[:9]
    rotated = rhs.copy()
    rotated[:9] = apply_no_polar_rhs_rotation(A, affine_rhs)[:9]
    return rotated


def _affine_only_no_polar_increment(A: np.ndarray, delta: np.ndarray) -> np.ndarray:
    affine_delta = np.zeros(12, dtype=float)
    affine_delta[:9] = delta[:9]
    rotated = delta.copy()
    rotated[:9] = apply_no_polar_increment_rotation(A, affine_delta)[:9]
    return rotated


def _step_body_systems(
    q: tuple[np.ndarray, ...],
    qd: tuple[np.ndarray, ...],
    dt: float,
    bodies: tuple[MABDCPUOracleBody, ...],
    external_forces: tuple[np.ndarray, ...],
) -> tuple[tuple[np.ndarray, ...], tuple[np.ndarray, ...]]:
    hessians = []
    rhs = []
    inv_dt = 1.0 / float(dt)
    for _body_q, body_qd, body, force in zip(q, qd, bodies, external_forces, strict=True):
        mass = body.precompute.mass_matrix
        hessians.append(body.precompute.hessian(dt))
        rhs.append(inv_dt * (mass @ body_qd) + force)
    return tuple(hessians), tuple(rhs)


def _world_material_rhs(body_q: np.ndarray, inertial_external_rhs: np.ndarray, body: MABDCPUOracleBody) -> np.ndarray:
    return inertial_external_rhs - body.precompute.stiffness_matrix @ (body_q - _body_rest_q(body))


def _unconstrained_step(
    q: tuple[np.ndarray, ...],
    dt: float,
    hessians: tuple[np.ndarray, ...],
    rhs: tuple[np.ndarray, ...],
    bodies: tuple[MABDCPUOracleBody, ...],
) -> MABDCPUOracleStepResult:
    dq_blocks = []
    residual_blocks = []
    for body_q, H, f, body in zip(q, hessians, rhs, bodies, strict=True):
        if body.rotation_mode == "none":
            world_rhs = _world_material_rhs(body_q, f, body)
            body_dq = np.linalg.solve(H, world_rhs)
            dq_blocks.append(body_dq)
            residual_blocks.append(float(np.linalg.norm(H @ body_dq - world_rhs)))
        elif body.rotation_mode == "polar":
            A, _t = unpack_q(body_q)
            local_q = apply_polar_rhs_rotation(A, body_q)
            local_rhs = apply_polar_rhs_rotation(A, f) - body.precompute.stiffness_matrix @ (
                local_q - _body_rest_q(body)
            )
            local_delta = np.linalg.solve(H, local_rhs)
            dq_blocks.append(apply_polar_increment_rotation(A, local_delta))
            residual_blocks.append(float(np.linalg.norm(H @ local_delta - local_rhs)))
        elif body.rotation_mode == "no_polar":
            A, _t = unpack_q(body_q)
            local_rhs = _affine_only_no_polar_rhs(A, _world_material_rhs(body_q, f, body))
            local_delta = np.linalg.solve(H, local_rhs)
            dq_blocks.append(_affine_only_no_polar_increment(A, local_delta))
            residual_blocks.append(float(np.linalg.norm(H @ local_delta - local_rhs)))
        else:  # pragma: no cover - _validate_config owns this boundary.
            raise ValueError("rotation_mode must be one of 'none', 'polar', or 'no_polar'")
    dq_blocks = tuple(dq_blocks)
    dq = np.concatenate(dq_blocks) if dq_blocks else np.zeros(0, dtype=float)
    q_next = tuple(body_q + body_dq for body_q, body_dq in zip(q, dq_blocks, strict=True))
    qd_next = tuple(body_dq / float(dt) for body_dq in dq_blocks)
    residual = sum(residual_blocks)
    return MABDCPUOracleStepResult(
        q=q_next,
        qd=qd_next,
        dq=dq,
        dlambda=np.zeros(0, dtype=float),
        residual_norm=residual,
        constraint_residual_norm=0.0,
        topology="unconstrained",
    )


def _constraint_blocks(
    q: tuple[np.ndarray, ...],
    config: MABDCPUOracleConfig,
) -> tuple[list[tuple[int, int]], list[tuple[np.ndarray, np.ndarray]], list[np.ndarray], list[np.ndarray]]:
    edges: list[tuple[int, int]] = []
    gradients: list[tuple[np.ndarray, np.ndarray]] = []
    lower_rhs_blocks: list[np.ndarray] = []
    residuals: list[np.ndarray] = []
    for constraint in config.constraints:
        body_a = int(constraint.body_a)
        body_b = int(constraint.body_b)
        evaluation = evaluate_joint(
            constraint.spec,
            q[body_a],
            q[body_b],
            gradient_mode=constraint.gradient_mode,
        )
        edges.append((body_a, body_b))
        gradients.append((evaluation.gradient[:, :12], evaluation.gradient[:, 12:24]))
        lower_rhs_blocks.append(-evaluation.residual if config.residual_correction else np.zeros_like(evaluation.residual))
        residuals.append(evaluation.residual)
    return edges, gradients, lower_rhs_blocks, residuals


def _solve_constrained_step(
    q: tuple[np.ndarray, ...],
    dt: float,
    hessians: tuple[np.ndarray, ...],
    rhs: tuple[np.ndarray, ...],
    config: MABDCPUOracleConfig,
) -> MABDCPUOracleStepResult:
    edges, gradients, lower_rhs_blocks, _residuals = _constraint_blocks(q, config)
    topology = str(config.topology)

    if topology == "auto":
        classification = classify_constraint_graph(len(q), edges)
        topology = classification.kind
        if topology == "general_graph" and config.graph_schedule is None:
            raise ValueError(
                "topology='auto' requires graph_schedule for general_graph routing; "
                "use topology='dense' for dense CPU oracle fallback"
            )

    if topology == "dense":
        inputs = assemble_topology_dual_inputs(hessians, edges, gradients, rhs, lower_rhs_blocks)
        dense = solve_dense_dual_kkt(inputs.H, inputs.J, inputs.f, lower_rhs=inputs.lower_rhs)
        dq = dense.dq
        dlambda = dense.dlambda
        residual_norm = float(np.linalg.norm(inputs.dual_matrix @ dlambda - inputs.dual_rhs))
        result_topology = "dense"
    elif topology == "chain":
        topo = solve_chain_block_tridiagonal_kkt(hessians, edges, gradients, rhs, lower_rhs_blocks)
        dq, dlambda, residual_norm, result_topology = topo.dq, topo.dlambda, topo.residual_norm, topo.topology
    elif topology == "tree":
        topo = solve_tree_elimination_kkt(hessians, edges, gradients, rhs, lower_rhs_blocks)
        dq, dlambda, residual_norm, result_topology = topo.dq, topo.dlambda, topo.residual_norm, topo.topology
    elif topology == "single_loop":
        topo = solve_loop_schur_complement_kkt(hessians, edges, gradients, rhs, lower_rhs_blocks)
        dq, dlambda, residual_norm, result_topology = topo.dq, topo.dlambda, topo.residual_norm, topo.topology
    elif topology == "general_graph":
        topo = solve_graph_block_gauss_seidel_kkt(
            hessians,
            edges,
            gradients,
            rhs,
            lower_rhs_blocks,
            schedule=config.graph_schedule,
        )
        dq, dlambda, residual_norm, result_topology = topo.dq, topo.dlambda, topo.residual_norm, topo.topology
    else:
        raise ValueError("topology must be one of dense, auto, chain, tree, single_loop, or general_graph")

    dq_blocks = tuple(dq[12 * body_id : 12 * body_id + 12] for body_id in range(len(q)))
    q_next = tuple(body_q + body_dq for body_q, body_dq in zip(q, dq_blocks, strict=True))
    qd_next = tuple(body_dq / float(dt) for body_dq in dq_blocks)
    residual_after = [joint_residual(constraint.spec, q_next[int(constraint.body_a)], q_next[int(constraint.body_b)]) for constraint in config.constraints]
    constraint_norm = float(np.linalg.norm(np.concatenate(residual_after))) if residual_after else 0.0
    return MABDCPUOracleStepResult(
        q=q_next,
        qd=qd_next,
        dq=dq,
        dlambda=dlambda,
        residual_norm=float(residual_norm),
        constraint_residual_norm=constraint_norm,
        topology=result_topology,
    )


def solve_cpu_oracle_step(
    q: Any,
    qd: Any,
    dt: float,
    config: MABDCPUOracleConfig,
) -> MABDCPUOracleStepResult:
    dt_float = float(dt)
    if dt_float <= 0.0:
        raise ValueError("dt must be positive")
    q_blocks = _as_q_blocks(q, "q")
    qd_blocks = _as_q_blocks(qd, "qd")
    if len(q_blocks) != len(qd_blocks):
        raise ValueError(f"q and qd must contain the same number of bodies, got {len(q_blocks)} and {len(qd_blocks)}")
    bodies = _validate_config(config, len(q_blocks))
    base_external_forces = _as_external_forces(config, len(q_blocks))
    gravity_forces = _as_gravity_forces(config, bodies)
    external_forces = assemble_control_generalized_forces(
        q_blocks,
        qd_blocks,
        actuations=config.actuations,
        base_external_forces=tuple(
            base_force + gravity_force
            for base_force, gravity_force in zip(
                base_external_forces,
                gravity_forces,
                strict=True,
            )
        ),
    )
    hessians, rhs = _step_body_systems(q_blocks, qd_blocks, dt_float, bodies, external_forces)
    if not tuple(config.constraints):
        return _unconstrained_step(q_blocks, dt_float, hessians, rhs, bodies)
    _require_constrained_none_rotation(bodies)
    world_rhs = tuple(
        _world_material_rhs(body_q, body_rhs, body)
        for body_q, body_rhs, body in zip(q_blocks, rhs, bodies, strict=True)
    )
    return _solve_constrained_step(q_blocks, dt_float, hessians, world_rhs, config)


__all__ = [
    "MABDCPUOracleBody",
    "MABDCPUOracleConfig",
    "MABDCPUOracleConstraint",
    "MABDCPUOracleStepResult",
    "solve_cpu_oracle_step",
]
