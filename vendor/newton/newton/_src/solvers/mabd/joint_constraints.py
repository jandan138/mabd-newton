# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

from .control_points import block_diag4, control_point_selection, control_point_transform


class MABDJointType(str, Enum):
    BALL = "ball"
    HINGE = "hinge"
    UNIVERSAL = "universal"
    PRISMATIC = "prismatic"


class JointGradientMode(str, Enum):
    PAPER_FAITHFUL = "paper_faithful"
    FINITE_DIFFERENCE_ORACLE = "finite_difference_oracle"


@dataclass(frozen=True)
class MABDJointSpec:
    joint_type: MABDJointType
    control_tetrahedron_a: np.ndarray
    control_tetrahedron_b: np.ndarray
    axis0: np.ndarray | None = None
    axis1: np.ndarray | None = None
    cp_index: int = 0


@dataclass(frozen=True)
class JointEvaluation:
    residual: np.ndarray
    gradient: np.ndarray
    rank: int
    spec: MABDJointSpec
    gradient_mode: JointGradientMode


@dataclass(frozen=True)
class JointLimitEvaluation:
    theta: float
    lower: float
    upper: float
    stiffness: float
    clamped_theta: float
    violation: float
    penalty_rhs: float
    active: bool


def _as_q(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (12,):
        raise ValueError(f"{name} must have shape (12,), got {arr.shape}")
    return arr


def _as_ct(value: Any, name: str) -> np.ndarray:
    # control_point_transform performs the non-degeneracy check.
    control_point_transform(value)
    return np.asarray(value, dtype=float).reshape(4, 3)


def _as_unit_vec3(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {arr.shape}")
    norm = float(np.linalg.norm(arr))
    if norm <= 1.0e-12:
        raise ValueError(f"{name} must be nonzero")
    return arr / norm


def _skew(value: np.ndarray) -> np.ndarray:
    x, y, z = value
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=float)


def _axis_to_local_y_rotation(axis: Any) -> np.ndarray:
    a = _as_unit_vec3(axis, "axis")
    e_y = np.array([0.0, 1.0, 0.0], dtype=float)
    dot = float(a @ e_y)
    if dot > 1.0 - 1.0e-12:
        return np.eye(3)
    if dot < -1.0 + 1.0e-12:
        return np.diag([1.0, -1.0, -1.0])
    v = np.cross(a, e_y)
    vx = _skew(v)
    return np.eye(3) + vx + vx @ vx / (1.0 + dot)


def _universal_axes_rotation(axis0: Any, axis1: Any) -> np.ndarray:
    a0 = _as_unit_vec3(axis0, "axis0")
    a1 = _as_unit_vec3(axis1, "axis1")
    if abs(float(a0 @ a1)) > 1.0e-8:
        raise ValueError("universal axes must be orthogonal")
    a2 = np.cross(a0, a1)
    a2 /= np.linalg.norm(a2)
    return np.vstack((a2, a0, a1))


def _selection_row(*terms: tuple[int, int] | tuple[int, int, float]) -> np.ndarray:
    row = np.zeros((1, 12), dtype=float)
    for term in terms:
        if len(term) == 2:
            cp_index, component = term
            weight = 1.0
        elif len(term) == 3:
            cp_index, component, weight = term
        else:
            raise ValueError("selection terms must be (cp_index, component[, weight])")
        if not 0 <= int(cp_index) < 4:
            raise ValueError(f"cp_index must be in [0, 3], got {cp_index}")
        if not 0 <= int(component) < 3:
            raise ValueError(f"component must be in [0, 2], got {component}")
        row[0, 3 * int(cp_index) + int(component)] += float(weight)
    return row


def _linear_maps(spec: MABDJointSpec) -> tuple[np.ndarray, np.ndarray]:
    T_a = control_point_transform(spec.control_tetrahedron_a)
    T_b = control_point_transform(spec.control_tetrahedron_b)
    zero = np.zeros((1, 12), dtype=float)

    if spec.joint_type is MABDJointType.BALL:
        cp = int(spec.cp_index)
        S = control_point_selection(((cp, 0), (cp, 1), (cp, 2)))
        return S @ T_a, -S @ T_b

    if spec.joint_type is MABDJointType.HINGE:
        if spec.axis0 is None:
            raise ValueError("hinge joint requires axis0")
        D = block_diag4(_axis_to_local_y_rotation(spec.axis0))
        S = control_point_selection(((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)))
        return S @ D @ T_a, -S @ D @ T_b

    if spec.joint_type is MABDJointType.UNIVERSAL:
        if spec.axis0 is None or spec.axis1 is None:
            raise ValueError("universal joint requires axis0 and axis1")
        D = block_diag4(_universal_axes_rotation(spec.axis0, spec.axis1))
        S_cp2 = control_point_selection(((1, 0), (1, 1), (1, 2)))
        S_beta_y = _selection_row((0, 1), (1, 1, -1.0))
        G_a = np.vstack((S_cp2 @ D @ T_a, zero))
        G_b = np.vstack((-S_cp2 @ D @ T_b, S_beta_y @ D @ T_b))
        return G_a, G_b

    if spec.joint_type is MABDJointType.PRISMATIC:
        if spec.axis0 is None:
            raise ValueError("prismatic joint requires axis0")
        D = block_diag4(_axis_to_local_y_rotation(spec.axis0))
        G_a = np.zeros((5, 12), dtype=float)
        G_b = np.zeros((5, 12), dtype=float)
        rows = [
            (_selection_row((1, 0)), _selection_row((0, 0)), -1.0),
            (_selection_row((1, 2)), _selection_row((0, 2)), -1.0),
            (zero, _selection_row((0, 0), (1, 0, -1.0)), 1.0),
            (zero, _selection_row((0, 2), (1, 2, -1.0)), 1.0),
            (_selection_row((2, 0)), _selection_row((2, 0)), -1.0),
        ]
        for row_id, (S_a, S_b, beta_sign) in enumerate(rows):
            if S_a.shape[0] == 1:
                G_a[row_id : row_id + 1, :] = S_a @ D @ T_a
            G_b[row_id : row_id + 1, :] = beta_sign * S_b @ D @ T_b
        return G_a, G_b

    raise ValueError(f"unsupported M-ABD joint type: {spec.joint_type}")


def _as_gradient_mode(value: JointGradientMode | str) -> JointGradientMode:
    if isinstance(value, JointGradientMode):
        return value
    return JointGradientMode(str(value))


def ball_joint(control_tetrahedron_a: Any, control_tetrahedron_b: Any, cp_index: int = 0) -> MABDJointSpec:
    if not 0 <= int(cp_index) < 4:
        raise ValueError("cp_index must be in [0, 3]")
    return MABDJointSpec(
        joint_type=MABDJointType.BALL,
        control_tetrahedron_a=_as_ct(control_tetrahedron_a, "control_tetrahedron_a"),
        control_tetrahedron_b=_as_ct(control_tetrahedron_b, "control_tetrahedron_b"),
        cp_index=int(cp_index),
    )


def hinge_joint(control_tetrahedron_a: Any, control_tetrahedron_b: Any, axis: Any) -> MABDJointSpec:
    return MABDJointSpec(
        joint_type=MABDJointType.HINGE,
        control_tetrahedron_a=_as_ct(control_tetrahedron_a, "control_tetrahedron_a"),
        control_tetrahedron_b=_as_ct(control_tetrahedron_b, "control_tetrahedron_b"),
        axis0=_as_unit_vec3(axis, "axis"),
    )


def universal_joint(control_tetrahedron_a: Any, control_tetrahedron_b: Any, axis0: Any, axis1: Any) -> MABDJointSpec:
    _universal_axes_rotation(axis0, axis1)
    return MABDJointSpec(
        joint_type=MABDJointType.UNIVERSAL,
        control_tetrahedron_a=_as_ct(control_tetrahedron_a, "control_tetrahedron_a"),
        control_tetrahedron_b=_as_ct(control_tetrahedron_b, "control_tetrahedron_b"),
        axis0=_as_unit_vec3(axis0, "axis0"),
        axis1=_as_unit_vec3(axis1, "axis1"),
    )


def prismatic_joint(control_tetrahedron_a: Any, control_tetrahedron_b: Any, axis: Any) -> MABDJointSpec:
    return MABDJointSpec(
        joint_type=MABDJointType.PRISMATIC,
        control_tetrahedron_a=_as_ct(control_tetrahedron_a, "control_tetrahedron_a"),
        control_tetrahedron_b=_as_ct(control_tetrahedron_b, "control_tetrahedron_b"),
        axis0=_as_unit_vec3(axis, "axis"),
    )


def joint_residual(spec: MABDJointSpec, q_a: Any, q_b: Any) -> np.ndarray:
    G_a, G_b = _linear_maps(spec)
    return G_a @ _as_q(q_a, "q_a") + G_b @ _as_q(q_b, "q_b")


def _finite_difference_gradient(spec: MABDJointSpec, q_a: np.ndarray, q_b: np.ndarray) -> np.ndarray:
    base = joint_residual(spec, q_a, q_b)
    grad = np.zeros((base.shape[0], 24), dtype=float)
    eps = 1.0e-6
    for col in range(24):
        dq_a = np.zeros(12, dtype=float)
        dq_b = np.zeros(12, dtype=float)
        if col < 12:
            dq_a[col] = eps
        else:
            dq_b[col - 12] = eps
        plus = joint_residual(spec, q_a + dq_a, q_b + dq_b)
        minus = joint_residual(spec, q_a - dq_a, q_b - dq_b)
        grad[:, col] = (plus - minus) / (2.0 * eps)
    return grad


def evaluate_joint(
    spec: MABDJointSpec,
    q_a: Any,
    q_b: Any,
    gradient_mode: JointGradientMode | str = JointGradientMode.FINITE_DIFFERENCE_ORACLE,
) -> JointEvaluation:
    mode = _as_gradient_mode(gradient_mode)
    q_a_arr = _as_q(q_a, "q_a")
    q_b_arr = _as_q(q_b, "q_b")
    residual = joint_residual(spec, q_a_arr, q_b_arr)
    if mode is JointGradientMode.FINITE_DIFFERENCE_ORACLE:
        gradient = _finite_difference_gradient(spec, q_a_arr, q_b_arr)
    else:
        if spec.joint_type is not MABDJointType.BALL:
            raise NotImplementedError(
                "paper_faithful joint gradients require the rotation-gradient and "
                "skew-symmetrized path, which is not implemented in Phase 2"
            )
        G_a, G_b = _linear_maps(spec)
        gradient = np.hstack((G_a, G_b))
    return JointEvaluation(
        residual=residual,
        gradient=gradient,
        rank=residual.shape[0],
        spec=spec,
        gradient_mode=mode,
    )


def evaluate_joint_limit(theta: float, lower: float, upper: float, stiffness: float) -> JointLimitEvaluation:
    theta_float = float(theta)
    lower_float = float(lower)
    upper_float = float(upper)
    stiffness_float = float(stiffness)
    if lower_float > upper_float:
        raise ValueError("joint limit lower must be <= upper")
    if stiffness_float < 0.0:
        raise ValueError("joint limit stiffness must be non-negative")
    clamped = min(max(theta_float, lower_float), upper_float)
    active = clamped != theta_float
    violation = theta_float - clamped
    penalty_rhs = stiffness_float * violation if active else 0.0
    return JointLimitEvaluation(
        theta=theta_float,
        lower=lower_float,
        upper=upper_float,
        stiffness=stiffness_float,
        clamped_theta=clamped,
        violation=violation,
        penalty_rhs=penalty_rhs,
        active=active,
    )


def apply_joint_limit_penalty_rhs(
    base_lower_rhs: Any,
    row_indices: Any,
    evaluations: Any,
) -> np.ndarray:
    out = np.asarray(base_lower_rhs, dtype=float).copy()
    if out.ndim != 1:
        raise ValueError(f"base_lower_rhs must be one-dimensional, got {out.shape}")
    rows = []
    for row in row_indices:
        if isinstance(row, bool) or not isinstance(row, (int, np.integer)):
            raise TypeError("joint limit row index must be an integer")
        rows.append(int(row))
    limit_evaluations = list(evaluations)
    if len(rows) != len(limit_evaluations):
        raise ValueError("row_indices and evaluations must have the same length")
    for row, evaluation in zip(rows, limit_evaluations, strict=True):
        if row < 0 or row >= out.shape[0]:
            raise ValueError(f"joint limit row index {row} is out of range for lower_rhs size {out.shape[0]}")
        if not isinstance(evaluation, JointLimitEvaluation):
            raise TypeError("evaluations must contain JointLimitEvaluation values")
        out[row] += evaluation.penalty_rhs
    return out


__all__ = [
    "JointEvaluation",
    "JointGradientMode",
    "JointLimitEvaluation",
    "MABDJointSpec",
    "MABDJointType",
    "apply_joint_limit_penalty_rhs",
    "ball_joint",
    "evaluate_joint",
    "evaluate_joint_limit",
    "hinge_joint",
    "joint_residual",
    "prismatic_joint",
    "universal_joint",
]
