# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class MABDActuationSpec:
    body_id: int
    target_q: Any | None = None
    target_qd: Any | None = None
    stiffness: Any = 0.0
    damping: Any = 0.0
    feedforward_force: Any | None = None


@dataclass(frozen=True)
class MABDControlEvaluation:
    body_id: int
    position_error: np.ndarray
    velocity_error: np.ndarray
    feedforward_force: np.ndarray
    generalized_force: np.ndarray


def _as_q12(value: Any, name: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (12,):
        raise ValueError(f"{name} must have shape (12,), got {vector.shape}")
    return vector.astype(float, copy=True)


def _as_optional_q12(value: Any | None, name: str) -> np.ndarray | None:
    if value is None:
        return None
    return _as_q12(value, name)


def _as_gain(value: Any, name: str) -> float | np.ndarray:
    gain = np.asarray(value, dtype=float)
    if gain.shape == ():
        scalar = float(gain)
        if scalar < 0.0:
            raise ValueError(f"{name} must be nonnegative")
        return scalar
    if gain.shape != (12,):
        raise ValueError(f"{name} must be a scalar or shape (12,), got {gain.shape}")
    if np.any(gain < 0.0):
        raise ValueError(f"{name} must be nonnegative")
    return gain.astype(float, copy=True)


def _as_q_blocks(values: Any, name: str) -> tuple[np.ndarray, ...]:
    blocks = tuple(np.asarray(value, dtype=float) for value in values)
    for body_id, block in enumerate(blocks):
        if block.shape != (12,):
            raise ValueError(f"{name}[{body_id}] must have shape (12,), got {block.shape}")
    return tuple(block.astype(float, copy=True) for block in blocks)


def _vec3_rows(value: Any, name: str, count: int) -> np.ndarray:
    rows = np.asarray(value.numpy(), dtype=float)
    if rows.shape != (count, 3):
        raise ValueError(f"{name} must have shape ({count}, 3), got {rows.shape}")
    return rows


def _scalar_rows(value: Any, name: str, count: int, dtype: Any) -> np.ndarray:
    rows = np.asarray(value.numpy(), dtype=dtype)
    if rows.shape != (count,):
        raise ValueError(f"{name} must have shape ({count},), got {rows.shape}")
    return rows


def _pack_rows(q0: np.ndarray, q1: np.ndarray, q2: np.ndarray, t: np.ndarray) -> tuple[np.ndarray, ...]:
    return tuple(np.concatenate((q0[row], q1[row], q2[row], t[row])).astype(float, copy=True) for row in range(len(t)))


def evaluate_affine_pd_control(
    q: Any,
    qd: Any,
    spec: MABDActuationSpec,
) -> MABDControlEvaluation:
    q_vec = _as_q12(q, "q")
    qd_vec = _as_q12(qd, "qd")
    target_q = _as_optional_q12(spec.target_q, "target_q")
    target_qd = _as_optional_q12(spec.target_qd, "target_qd")
    stiffness = _as_gain(spec.stiffness, "stiffness")
    damping = _as_gain(spec.damping, "damping")
    feedforward = _as_optional_q12(spec.feedforward_force, "feedforward_force")
    position_error = np.zeros(12, dtype=float) if target_q is None else target_q - q_vec
    velocity_error = np.zeros(12, dtype=float) if target_qd is None else target_qd - qd_vec
    feedforward_force = np.zeros(12, dtype=float) if feedforward is None else feedforward
    generalized_force = stiffness * position_error + damping * velocity_error + feedforward_force
    return MABDControlEvaluation(
        body_id=int(spec.body_id),
        position_error=position_error,
        velocity_error=velocity_error,
        feedforward_force=feedforward_force,
        generalized_force=np.asarray(generalized_force, dtype=float),
    )


def assemble_control_generalized_forces(
    q: Any,
    qd: Any,
    *,
    actuations: Any = (),
    base_external_forces: Any | None = None,
) -> tuple[np.ndarray, ...]:
    q_blocks = _as_q_blocks(q, "q")
    qd_blocks = _as_q_blocks(qd, "qd")
    if len(q_blocks) != len(qd_blocks):
        raise ValueError(f"q and qd must contain the same number of bodies, got {len(q_blocks)} and {len(qd_blocks)}")
    if base_external_forces is None:
        forces = [np.zeros(12, dtype=float) for _ in q_blocks]
    else:
        base_blocks = _as_q_blocks(base_external_forces, "base_external_forces")
        if len(base_blocks) != len(q_blocks):
            raise ValueError(
                "base_external_forces must contain "
                f"{len(q_blocks)} vectors, got {len(base_blocks)}"
            )
        forces = [block.copy() for block in base_blocks]

    for spec in tuple(actuations or ()):
        body_id = int(spec.body_id)
        if not 0 <= body_id < len(q_blocks):
            raise ValueError(f"actuation body_id {body_id} is outside [0, {len(q_blocks)})")
        evaluation = evaluate_affine_pd_control(q_blocks[body_id], qd_blocks[body_id], spec)
        forces[body_id] += evaluation.generalized_force
    return tuple(forces)


def actuation_specs_from_model(model: Any, *, enabled_only: bool = True) -> tuple[MABDActuationSpec, ...]:
    row_count = int(model.get_custom_frequency_count("mabd:control"))
    if row_count == 0:
        return ()
    body_count = int(model.get_custom_frequency_count("mabd:body"))
    namespace = model.mabd
    control_body = _scalar_rows(namespace.control_body, "control_body", row_count, int)
    control_enabled = _scalar_rows(namespace.control_enabled, "control_enabled", row_count, int)
    stiffness = _scalar_rows(namespace.control_stiffness, "control_stiffness", row_count, float)
    damping = _scalar_rows(namespace.control_damping, "control_damping", row_count, float)
    target_q = _pack_rows(
        _vec3_rows(namespace.control_target_q0, "control_target_q0", row_count),
        _vec3_rows(namespace.control_target_q1, "control_target_q1", row_count),
        _vec3_rows(namespace.control_target_q2, "control_target_q2", row_count),
        _vec3_rows(namespace.control_target_t, "control_target_t", row_count),
    )
    target_qd = _pack_rows(
        _vec3_rows(namespace.control_target_qd0, "control_target_qd0", row_count),
        _vec3_rows(namespace.control_target_qd1, "control_target_qd1", row_count),
        _vec3_rows(namespace.control_target_qd2, "control_target_qd2", row_count),
        _vec3_rows(namespace.control_target_td, "control_target_td", row_count),
    )
    feedforward = _pack_rows(
        _vec3_rows(namespace.control_feedforward_q0, "control_feedforward_q0", row_count),
        _vec3_rows(namespace.control_feedforward_q1, "control_feedforward_q1", row_count),
        _vec3_rows(namespace.control_feedforward_q2, "control_feedforward_q2", row_count),
        _vec3_rows(namespace.control_feedforward_t, "control_feedforward_t", row_count),
    )

    specs: list[MABDActuationSpec] = []
    for row in range(row_count):
        if enabled_only and int(control_enabled[row]) == 0:
            continue
        body_id = int(control_body[row])
        if not 0 <= body_id < body_count:
            raise ValueError(f"control row {row} body {body_id} is outside [0, {body_count})")
        specs.append(
            MABDActuationSpec(
                body_id=body_id,
                target_q=target_q[row],
                target_qd=target_qd[row],
                stiffness=float(stiffness[row]),
                damping=float(damping[row]),
                feedforward_force=feedforward[row],
            )
        )
    return tuple(specs)


__all__ = [
    "MABDActuationSpec",
    "MABDControlEvaluation",
    "actuation_specs_from_model",
    "assemble_control_generalized_forces",
    "evaluate_affine_pd_control",
]
