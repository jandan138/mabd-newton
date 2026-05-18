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
    point_jacobian,
    polar_rotation,
    unpack_q,
)
from .control_forces import MABDActuationSpec, assemble_control_generalized_forces
from .dense_kkt import solve_dense_dual_kkt
from .joint_constraints import JointGradientMode, MABDJointSpec, evaluate_joint, joint_residual
from .single_body import SingleBodyABDPrecompute
from .topology_solvers import (
    TopologyDualInputs,
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
class MABDCPUOracleWorldConstraint:
    body: int
    rest_point: np.ndarray
    world_point: np.ndarray


@dataclass(frozen=True)
class MABDCPUOraclePlaneConstraint:
    body: int
    rest_point: np.ndarray
    plane_normal: np.ndarray
    plane_offset: float
    active: bool = True


@dataclass(frozen=True)
class MABDCPUOracleConfig:
    bodies: tuple[MABDCPUOracleBody, ...] | list[MABDCPUOracleBody]
    constraints: tuple[MABDCPUOracleConstraint, ...] | list[MABDCPUOracleConstraint] = field(default_factory=tuple)
    world_constraints: tuple[MABDCPUOracleWorldConstraint, ...] | list[MABDCPUOracleWorldConstraint] = field(default_factory=tuple)
    plane_constraints: tuple[MABDCPUOraclePlaneConstraint, ...] | list[MABDCPUOraclePlaneConstraint] = field(default_factory=tuple)
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
    plane_constraint_requested_count: int = 0
    plane_constraint_accepted_count: int = 0
    plane_constraint_skipped_count: int = 0


def _as_q_blocks(values: Any, name: str) -> tuple[np.ndarray, ...]:
    blocks = tuple(np.asarray(value, dtype=float) for value in values)
    for body_id, block in enumerate(blocks):
        if block.shape != (12,):
            raise ValueError(f"{name}[{body_id}] must have shape (12,), got {block.shape}")
    return blocks


def _as_vec3(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {arr.shape}")
    return arr


def _normalized_plane_constraint_values(
    constraint_id: int,
    constraint: MABDCPUOraclePlaneConstraint,
) -> tuple[int, np.ndarray, np.ndarray, float]:
    body = int(constraint.body)
    rest_point = _as_vec3(
        constraint.rest_point,
        f"plane_constraints[{constraint_id}].rest_point",
    )
    normal = _as_vec3(
        constraint.plane_normal,
        f"plane_constraints[{constraint_id}].plane_normal",
    )
    normal_norm = float(np.linalg.norm(normal))
    if normal_norm == 0.0:
        raise ValueError(f"plane_constraints[{constraint_id}].plane_normal must be nonzero")
    offset = float(constraint.plane_offset)
    if not np.isfinite(offset):
        raise ValueError(f"plane_constraints[{constraint_id}].plane_offset must be finite")
    return body, rest_point, normal / normal_norm, offset / normal_norm


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
    world_constraints = tuple(config.world_constraints)
    for constraint_id, constraint in enumerate(world_constraints):
        if not 0 <= int(constraint.body) < body_count:
            raise ValueError(f"world constraint {constraint_id} references a body outside [0, {body_count})")
    plane_constraints = tuple(config.plane_constraints)
    for constraint_id, constraint in enumerate(plane_constraints):
        body, _rest_point, _normal, _offset = _normalized_plane_constraint_values(constraint_id, constraint)
        if not 0 <= body < body_count:
            raise ValueError(f"plane_constraints[{constraint_id}] references a body outside [0, {body_count})")
    return bodies


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


def _polar_increment_map(A: np.ndarray) -> np.ndarray:
    return np.kron(np.eye(4), polar_rotation(A))


def _body_solve_system(
    body_q: np.ndarray,
    inertial_external_rhs: np.ndarray,
    body: MABDCPUOracleBody,
) -> tuple[np.ndarray, np.ndarray]:
    if body.rotation_mode == "none":
        return _world_material_rhs(body_q, inertial_external_rhs, body), np.eye(12)

    A, _t = unpack_q(body_q)
    if body.rotation_mode == "polar":
        local_q = apply_polar_rhs_rotation(A, body_q)
        local_rhs = apply_polar_rhs_rotation(A, inertial_external_rhs) - body.precompute.stiffness_matrix @ (
            local_q - _body_rest_q(body)
        )
        return local_rhs, _polar_increment_map(A)

    if body.rotation_mode == "no_polar":
        raise NotImplementedError(
            "constrained CPU oracle no_polar KKT is unsupported because the current "
            "no-polar normalization increment is nonlinear"
        )

    raise ValueError("rotation_mode must be one of 'none', 'polar', or 'no_polar'")


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


def _world_constraint_blocks(
    q: tuple[np.ndarray, ...],
    config: MABDCPUOracleConfig,
) -> tuple[list[int], list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    bodies: list[int] = []
    gradients: list[np.ndarray] = []
    lower_rhs_blocks: list[np.ndarray] = []
    residuals: list[np.ndarray] = []
    for constraint_id, constraint in enumerate(config.world_constraints):
        body = int(constraint.body)
        rest_point = _as_vec3(
            constraint.rest_point,
            f"world_constraints[{constraint_id}].rest_point",
        )
        world_point = _as_vec3(
            constraint.world_point,
            f"world_constraints[{constraint_id}].world_point",
        )
        gradient = point_jacobian(rest_point)
        residual = gradient @ q[body] - world_point
        bodies.append(body)
        gradients.append(gradient)
        lower_rhs_blocks.append(-residual if config.residual_correction else np.zeros_like(residual))
        residuals.append(residual)
    return bodies, gradients, lower_rhs_blocks, residuals


def _plane_constraint_blocks(
    q: tuple[np.ndarray, ...],
    config: MABDCPUOracleConfig,
) -> tuple[list[int], list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    bodies: list[int] = []
    gradients: list[np.ndarray] = []
    lower_rhs_blocks: list[np.ndarray] = []
    residuals: list[np.ndarray] = []
    for constraint_id, constraint in enumerate(config.plane_constraints):
        if not bool(constraint.active):
            continue
        body, rest_point, normal, offset = _normalized_plane_constraint_values(constraint_id, constraint)
        gradient = normal.reshape(1, 3) @ point_jacobian(rest_point)
        residual = gradient @ q[body] - np.array([offset], dtype=float)
        bodies.append(body)
        gradients.append(gradient)
        lower_rhs_blocks.append(-residual if config.residual_correction else np.zeros_like(residual))
        residuals.append(residual)
    return bodies, gradients, lower_rhs_blocks, residuals


def _block_diag_hessians(blocks: tuple[np.ndarray, ...]) -> np.ndarray:
    dim = blocks[0].shape[0]
    out = np.zeros((dim * len(blocks), dim * len(blocks)), dtype=float)
    for body_id, block in enumerate(blocks):
        start = dim * body_id
        out[start : start + dim, start : start + dim] = block
    return out


def _assemble_dense_dual_inputs_with_world_constraints(
    hessians: tuple[np.ndarray, ...],
    body_edges: list[tuple[int, int]],
    body_gradients: list[tuple[np.ndarray, np.ndarray]],
    body_forces: tuple[np.ndarray, ...],
    body_lower_rhs_blocks: list[np.ndarray],
    world_bodies: list[int],
    world_gradients: list[np.ndarray],
    world_lower_rhs_blocks: list[np.ndarray],
    plane_bodies: list[int],
    plane_gradients: list[np.ndarray],
    plane_lower_rhs_blocks: list[np.ndarray],
    increment_maps: tuple[np.ndarray, ...],
) -> tuple[TopologyDualInputs, int, int]:
    dim = hessians[0].shape[0]
    H = _block_diag_hessians(hessians)
    f = np.concatenate(body_forces)
    rows = []
    lower_blocks = []
    edge_slices: list[slice] = []
    row_start = 0
    for (body_a, body_b), (grad_a, grad_b), lower_rhs in zip(
        body_edges,
        body_gradients,
        body_lower_rhs_blocks,
        strict=True,
    ):
        rank = grad_a.shape[0]
        row = np.zeros((rank, dim * len(hessians)), dtype=float)
        row[:, dim * body_a : dim * body_a + dim] = grad_a @ increment_maps[body_a]
        row[:, dim * body_b : dim * body_b + dim] = grad_b @ increment_maps[body_b]
        rows.append(row)
        lower_blocks.append(lower_rhs)
        edge_slices.append(slice(row_start, row_start + rank))
        row_start += rank
    for body, gradient, lower_rhs in zip(
        world_bodies,
        world_gradients,
        world_lower_rhs_blocks,
        strict=True,
    ):
        rank = gradient.shape[0]
        row = np.zeros((rank, dim * len(hessians)), dtype=float)
        row[:, dim * body : dim * body + dim] = gradient @ increment_maps[body]
        rows.append(row)
        lower_blocks.append(lower_rhs)
        edge_slices.append(slice(row_start, row_start + rank))
        row_start += rank

    def plane_row_increases_rank(row: np.ndarray) -> bool:
        if not rows:
            return True
        before = np.linalg.matrix_rank(np.vstack(rows), tol=1.0e-10)
        after = np.linalg.matrix_rank(np.vstack([*rows, row]), tol=1.0e-10)
        return bool(after > before)

    accepted_plane_count = 0
    skipped_plane_count = 0
    for body, gradient, lower_rhs in zip(
        plane_bodies,
        plane_gradients,
        plane_lower_rhs_blocks,
        strict=True,
    ):
        rank = gradient.shape[0]
        row = np.zeros((rank, dim * len(hessians)), dtype=float)
        row[:, dim * body : dim * body + dim] = gradient @ increment_maps[body]
        if not plane_row_increases_rank(row):
            skipped_plane_count += 1
            continue
        rows.append(row)
        lower_blocks.append(lower_rhs)
        edge_slices.append(slice(row_start, row_start + rank))
        row_start += rank
        accepted_plane_count += 1
    J = np.vstack(rows)
    lower_rhs = np.concatenate(lower_blocks)
    inv_h_f = np.linalg.solve(H, f)
    dual_matrix = J @ np.linalg.solve(H, J.T)
    dual_rhs = J @ inv_h_f - lower_rhs
    return TopologyDualInputs(
        H=H,
        J=J,
        f=f,
        lower_rhs=lower_rhs,
        dual_matrix=dual_matrix,
        dual_rhs=dual_rhs,
        edge_slices=edge_slices,
    ), accepted_plane_count, skipped_plane_count


def _solve_constrained_step(
    q: tuple[np.ndarray, ...],
    dt: float,
    hessians: tuple[np.ndarray, ...],
    rhs: tuple[np.ndarray, ...],
    increment_maps: tuple[np.ndarray, ...],
    config: MABDCPUOracleConfig,
) -> MABDCPUOracleStepResult:
    edges, gradients, lower_rhs_blocks, _residuals = _constraint_blocks(q, config)
    world_bodies, world_gradients, world_lower_rhs_blocks, _world_residuals = _world_constraint_blocks(q, config)
    plane_bodies, plane_gradients, plane_lower_rhs_blocks, _plane_residuals = _plane_constraint_blocks(q, config)
    topology = str(config.topology)
    if (world_bodies or plane_bodies) and topology != "dense":
        raise ValueError("world and plane constraints currently require topology='dense'")

    if topology == "auto":
        classification = classify_constraint_graph(len(q), edges)
        topology = classification.kind
        if topology == "general_graph" and config.graph_schedule is None:
            raise ValueError(
                "topology='auto' requires graph_schedule for general_graph routing; "
                "use topology='dense' for dense CPU oracle fallback"
            )
    has_rotated_body = any(body.rotation_mode != "none" for body in config.bodies)
    if has_rotated_body and topology != "dense":
        raise NotImplementedError("constrained rotated CPU oracle steps require topology='dense'")

    if topology == "dense":
        accepted_plane_count = 0
        skipped_plane_count = 0
        if world_bodies:
            inputs, accepted_plane_count, skipped_plane_count = _assemble_dense_dual_inputs_with_world_constraints(
                hessians,
                edges,
                gradients,
                rhs,
                lower_rhs_blocks,
                world_bodies,
                world_gradients,
                world_lower_rhs_blocks,
                plane_bodies,
                plane_gradients,
                plane_lower_rhs_blocks,
                increment_maps,
            )
        elif plane_bodies:
            inputs, accepted_plane_count, skipped_plane_count = _assemble_dense_dual_inputs_with_world_constraints(
                hessians,
                edges,
                gradients,
                rhs,
                lower_rhs_blocks,
                world_bodies,
                world_gradients,
                world_lower_rhs_blocks,
                plane_bodies,
                plane_gradients,
                plane_lower_rhs_blocks,
                increment_maps,
            )
        else:
            local_gradients = tuple(
                (grad_a @ increment_maps[body_a], grad_b @ increment_maps[body_b])
                for (body_a, body_b), (grad_a, grad_b) in zip(edges, gradients, strict=True)
            )
            inputs = assemble_topology_dual_inputs(hessians, edges, local_gradients, rhs, lower_rhs_blocks)
        dense = solve_dense_dual_kkt(inputs.H, inputs.J, inputs.f, lower_rhs=inputs.lower_rhs)
        dq = dense.dq
        dlambda = dense.dlambda
        residual_norm = float(np.linalg.norm(inputs.dual_matrix @ dlambda - inputs.dual_rhs))
        result_topology = "dense"
    elif topology == "chain":
        accepted_plane_count = 0
        skipped_plane_count = 0
        topo = solve_chain_block_tridiagonal_kkt(hessians, edges, gradients, rhs, lower_rhs_blocks)
        dq, dlambda, residual_norm, result_topology = topo.dq, topo.dlambda, topo.residual_norm, topo.topology
    elif topology == "tree":
        accepted_plane_count = 0
        skipped_plane_count = 0
        topo = solve_tree_elimination_kkt(hessians, edges, gradients, rhs, lower_rhs_blocks)
        dq, dlambda, residual_norm, result_topology = topo.dq, topo.dlambda, topo.residual_norm, topo.topology
    elif topology == "single_loop":
        accepted_plane_count = 0
        skipped_plane_count = 0
        topo = solve_loop_schur_complement_kkt(hessians, edges, gradients, rhs, lower_rhs_blocks)
        dq, dlambda, residual_norm, result_topology = topo.dq, topo.dlambda, topo.residual_norm, topo.topology
    elif topology == "general_graph":
        accepted_plane_count = 0
        skipped_plane_count = 0
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

    local_dq_blocks = tuple(dq[12 * body_id : 12 * body_id + 12] for body_id in range(len(q)))
    dq_blocks = tuple(
        increment_map @ local_dq
        for increment_map, local_dq in zip(increment_maps, local_dq_blocks, strict=True)
    )
    world_dq = np.concatenate(dq_blocks) if dq_blocks else np.zeros(0, dtype=float)
    q_next = tuple(body_q + body_dq for body_q, body_dq in zip(q, dq_blocks, strict=True))
    qd_next = tuple(body_dq / float(dt) for body_dq in dq_blocks)
    residual_after = [joint_residual(constraint.spec, q_next[int(constraint.body_a)], q_next[int(constraint.body_b)]) for constraint in config.constraints]
    residual_after.extend(
        point_jacobian(_as_vec3(constraint.rest_point, "rest_point")) @ q_next[int(constraint.body)]
        - _as_vec3(constraint.world_point, "world_point")
        for constraint in config.world_constraints
    )
    _plane_bodies_after, _plane_gradients_after, _plane_lower_after, plane_residual_after = _plane_constraint_blocks(
        q_next,
        config,
    )
    residual_after.extend(plane_residual_after)
    constraint_norm = float(np.linalg.norm(np.concatenate(residual_after))) if residual_after else 0.0
    return MABDCPUOracleStepResult(
        q=q_next,
        qd=qd_next,
        dq=world_dq,
        dlambda=dlambda,
        residual_norm=float(residual_norm),
        constraint_residual_norm=constraint_norm,
        topology=result_topology,
        plane_constraint_requested_count=len(plane_bodies),
        plane_constraint_accepted_count=accepted_plane_count,
        plane_constraint_skipped_count=skipped_plane_count,
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
    has_active_plane_constraints = any(bool(constraint.active) for constraint in config.plane_constraints)
    if not tuple(config.constraints) and not tuple(config.world_constraints) and not has_active_plane_constraints:
        return _unconstrained_step(q_blocks, dt_float, hessians, rhs, bodies)
    body_systems = tuple(
        _body_solve_system(body_q, body_rhs, body)
        for body_q, body_rhs, body in zip(q_blocks, rhs, bodies, strict=True)
    )
    local_rhs = tuple(system[0] for system in body_systems)
    increment_maps = tuple(system[1] for system in body_systems)
    return _solve_constrained_step(q_blocks, dt_float, hessians, local_rhs, increment_maps, config)


__all__ = [
    "MABDCPUOracleBody",
    "MABDCPUOracleConfig",
    "MABDCPUOracleConstraint",
    "MABDCPUOraclePlaneConstraint",
    "MABDCPUOracleStepResult",
    "MABDCPUOracleWorldConstraint",
    "solve_cpu_oracle_step",
]
