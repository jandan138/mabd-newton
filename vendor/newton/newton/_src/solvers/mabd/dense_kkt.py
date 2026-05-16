# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


class KKTLowerRHSMode(str, Enum):
    ZERO = "zero"
    RESIDUAL_CORRECTED = "residual_corrected"


@dataclass(frozen=True)
class DenseKKTResult:
    dq: np.ndarray
    dlambda: np.ndarray
    lower_rhs: np.ndarray
    primal_matrix: np.ndarray
    dual_matrix: np.ndarray


def _as_hessian(value: Any) -> np.ndarray:
    H = np.asarray(value, dtype=float)
    if H.ndim != 2 or H.shape[0] != H.shape[1]:
        raise ValueError(f"H must be square, got {H.shape}")
    return H


def _as_gradient(value: Any, primal_size: int) -> np.ndarray:
    J = np.asarray(value, dtype=float)
    if J.ndim != 2 or J.shape[1] != primal_size:
        raise ValueError(f"J must have shape (m, {primal_size}), got {J.shape}")
    return J


def _as_force(value: Any, primal_size: int) -> np.ndarray:
    f = np.asarray(value, dtype=float)
    if f.shape != (primal_size,):
        raise ValueError(f"f must have shape ({primal_size},), got {f.shape}")
    return f


def _as_lower_rhs(value: Any | None, rank: int) -> np.ndarray:
    if value is None:
        return np.zeros(rank, dtype=float)
    rhs = np.asarray(value, dtype=float)
    if rhs.shape != (rank,):
        raise ValueError(f"lower_rhs must have shape ({rank},), got {rhs.shape}")
    return rhs


def assemble_dense_primal_kkt(H: Any, J: Any) -> np.ndarray:
    H_arr = _as_hessian(H)
    J_arr = _as_gradient(J, H_arr.shape[0])
    top = np.hstack((H_arr, J_arr.T))
    bottom = np.hstack((J_arr, np.zeros((J_arr.shape[0], J_arr.shape[0]), dtype=float)))
    return np.vstack((top, bottom))


def assemble_dense_dual_kkt(H: Any, J: Any) -> np.ndarray:
    H_arr = _as_hessian(H)
    J_arr = _as_gradient(J, H_arr.shape[0])
    return J_arr @ np.linalg.solve(H_arr, J_arr.T)


def recover_primal_from_dual(H: Any, J: Any, f: Any, dlambda: Any) -> np.ndarray:
    H_arr = _as_hessian(H)
    J_arr = _as_gradient(J, H_arr.shape[0])
    f_arr = _as_force(f, H_arr.shape[0])
    lam = np.asarray(dlambda, dtype=float)
    if lam.shape != (J_arr.shape[0],):
        raise ValueError(f"dlambda must have shape ({J_arr.shape[0]},), got {lam.shape}")
    return np.linalg.solve(H_arr, f_arr - J_arr.T @ lam)


def solve_dense_primal_kkt(H: Any, J: Any, f: Any, lower_rhs: Any | None = None) -> DenseKKTResult:
    H_arr = _as_hessian(H)
    J_arr = _as_gradient(J, H_arr.shape[0])
    f_arr = _as_force(f, H_arr.shape[0])
    lower = _as_lower_rhs(lower_rhs, J_arr.shape[0])
    primal = assemble_dense_primal_kkt(H_arr, J_arr)
    solution = np.linalg.solve(primal, np.concatenate((f_arr, lower)))
    return DenseKKTResult(
        dq=solution[: H_arr.shape[0]],
        dlambda=solution[H_arr.shape[0] :],
        lower_rhs=lower,
        primal_matrix=primal,
        dual_matrix=assemble_dense_dual_kkt(H_arr, J_arr),
    )


def solve_dense_dual_kkt(H: Any, J: Any, f: Any, lower_rhs: Any | None = None) -> DenseKKTResult:
    H_arr = _as_hessian(H)
    J_arr = _as_gradient(J, H_arr.shape[0])
    f_arr = _as_force(f, H_arr.shape[0])
    lower = _as_lower_rhs(lower_rhs, J_arr.shape[0])
    dual = assemble_dense_dual_kkt(H_arr, J_arr)
    unconstrained = np.linalg.solve(H_arr, f_arr)
    rhs = J_arr @ unconstrained - lower
    dlambda = np.linalg.solve(dual, rhs)
    dq = recover_primal_from_dual(H_arr, J_arr, f_arr, dlambda)
    return DenseKKTResult(
        dq=dq,
        dlambda=dlambda,
        lower_rhs=lower,
        primal_matrix=assemble_dense_primal_kkt(H_arr, J_arr),
        dual_matrix=dual,
    )


__all__ = [
    "DenseKKTResult",
    "KKTLowerRHSMode",
    "assemble_dense_dual_kkt",
    "assemble_dense_primal_kkt",
    "recover_primal_from_dual",
    "solve_dense_dual_kkt",
    "solve_dense_primal_kkt",
]
