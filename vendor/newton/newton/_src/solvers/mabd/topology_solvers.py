# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ConstraintGraphClassification:
    kind: str
    num_bodies: int
    edges: list[tuple[int, int]]
    degrees: list[int]
    cycle_rank: int
    chain_order: list[int]
    parent: list[int]
    postorder: list[int]
    loop_breaker_edge_indices: list[int]


@dataclass(frozen=True)
class ReconstructedConstraintGraph:
    num_bodies: int
    edges: list[tuple[int, int]]
    ranks: list[int]
    classification: ConstraintGraphClassification


@dataclass(frozen=True)
class TopologyDualInputs:
    H: np.ndarray
    J: np.ndarray
    f: np.ndarray
    lower_rhs: np.ndarray
    dual_matrix: np.ndarray
    dual_rhs: np.ndarray
    edge_slices: list[slice]


@dataclass(frozen=True)
class TopologyKKTResult:
    topology: str
    dq: np.ndarray
    dlambda: np.ndarray
    residual_norm: float
    block_bandwidth: int = 0
    parent: list[int] | None = None
    postorder: list[int] | None = None
    loop_breaker_edge_indices: list[int] | None = None
    schur_complement: np.ndarray | None = None
    schedule: tuple[tuple[int, ...], ...] = ()
    iterations: int = 0
    converged: bool = True


def _as_hessian_blocks(body_hessians: Any) -> tuple[np.ndarray, ...]:
    blocks = tuple(np.asarray(block, dtype=float) for block in body_hessians)
    if not blocks:
        raise ValueError("body_hessians must contain at least one block")
    dim = blocks[0].shape[0]
    for block_id, block in enumerate(blocks):
        if block.shape != (dim, dim):
            raise ValueError(f"body_hessians[{block_id}] must have shape ({dim}, {dim}), got {block.shape}")
    return blocks


def _as_body_forces(body_forces: Any, dim: int, count: int) -> tuple[np.ndarray, ...]:
    forces = tuple(np.asarray(force, dtype=float) for force in body_forces)
    if len(forces) != count:
        raise ValueError(f"body_forces must contain {count} vectors, got {len(forces)}")
    for body_id, force in enumerate(forces):
        if force.shape != (dim,):
            raise ValueError(f"body_forces[{body_id}] must have shape ({dim},), got {force.shape}")
    return forces


def _as_edges(edges: Any, num_bodies: int) -> list[tuple[int, int]]:
    out = [(int(a), int(b)) for a, b in edges]
    if not out:
        raise ValueError("edges must contain at least one constraint")
    for edge_id, (a, b) in enumerate(out):
        if a == b:
            raise ValueError(f"edge {edge_id} cannot connect a body to itself")
        if not 0 <= a < num_bodies or not 0 <= b < num_bodies:
            raise ValueError(f"edge {edge_id} has body indices outside [0, {num_bodies})")
    return out


def _as_edge_gradients(edge_gradients: Any, dim: int, edge_count: int) -> tuple[tuple[np.ndarray, np.ndarray], ...]:
    gradients = tuple(edge_gradients)
    if len(gradients) != edge_count:
        raise ValueError(f"edge_gradients must contain {edge_count} entries, got {len(gradients)}")
    out = []
    for edge_id, gradient in enumerate(gradients):
        if isinstance(gradient, tuple):
            grad_a, grad_b = (np.asarray(part, dtype=float) for part in gradient)
        else:
            arr = np.asarray(gradient, dtype=float)
            if arr.ndim != 2 or arr.shape[1] != 2 * dim:
                raise ValueError(f"edge_gradients[{edge_id}] must have shape (rank, {2 * dim}), got {arr.shape}")
            grad_a, grad_b = arr[:, :dim], arr[:, dim:]
        if grad_a.ndim != 2 or grad_b.shape != grad_a.shape or grad_a.shape[1] != dim:
            raise ValueError(f"edge_gradients[{edge_id}] must contain two (rank, {dim}) blocks")
        out.append((grad_a, grad_b))
    return tuple(out)


def _as_lower_rhs_blocks(lower_rhs_blocks: Any | None, ranks: list[int]) -> tuple[np.ndarray, ...]:
    if lower_rhs_blocks is None:
        return tuple(np.zeros(rank, dtype=float) for rank in ranks)
    blocks = tuple(np.asarray(block, dtype=float) for block in lower_rhs_blocks)
    if len(blocks) != len(ranks):
        raise ValueError(f"lower_rhs_blocks must contain {len(ranks)} entries, got {len(blocks)}")
    for edge_id, (block, rank) in enumerate(zip(blocks, ranks, strict=True)):
        if block.shape != (rank,):
            raise ValueError(f"lower_rhs_blocks[{edge_id}] must have shape ({rank},), got {block.shape}")
    return blocks


def _block_diag(blocks: tuple[np.ndarray, ...]) -> np.ndarray:
    dim = blocks[0].shape[0]
    out = np.zeros((dim * len(blocks), dim * len(blocks)), dtype=float)
    for block_id, block in enumerate(blocks):
        start = dim * block_id
        out[start : start + dim, start : start + dim] = block
    return out


def assemble_topology_dual_inputs(
    body_hessians: Any,
    edges: Any,
    edge_gradients: Any,
    body_forces: Any,
    lower_rhs_blocks: Any | None = None,
) -> TopologyDualInputs:
    blocks = _as_hessian_blocks(body_hessians)
    dim = blocks[0].shape[0]
    forces = _as_body_forces(body_forces, dim, len(blocks))
    edge_list = _as_edges(edges, len(blocks))
    gradients = _as_edge_gradients(edge_gradients, dim, len(edge_list))
    ranks = [grad_a.shape[0] for grad_a, _grad_b in gradients]
    lower_blocks = _as_lower_rhs_blocks(lower_rhs_blocks, ranks)

    H = _block_diag(blocks)
    f = np.concatenate(forces)
    edge_slices: list[slice] = []
    rows = []
    row_start = 0
    for (body_a, body_b), (grad_a, grad_b), rank in zip(edge_list, gradients, ranks, strict=True):
        row = np.zeros((rank, dim * len(blocks)), dtype=float)
        row[:, dim * body_a : dim * body_a + dim] = grad_a
        row[:, dim * body_b : dim * body_b + dim] = grad_b
        rows.append(row)
        edge_slices.append(slice(row_start, row_start + rank))
        row_start += rank

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
    )


def _adjacency(num_bodies: int, edges: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    adj: list[list[tuple[int, int]]] = [[] for _ in range(num_bodies)]
    for edge_id, (a, b) in enumerate(edges):
        adj[a].append((b, edge_id))
        adj[b].append((a, edge_id))
    for neighbors in adj:
        neighbors.sort()
    return adj


def _connected(num_bodies: int, edges: list[tuple[int, int]]) -> bool:
    adj = _adjacency(num_bodies, edges)
    seen = {0}
    stack = [0]
    while stack:
        body = stack.pop()
        for neighbor, _edge_id in adj[body]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == num_bodies


def _tree_orders(num_bodies: int, edges: list[tuple[int, int]], root: int) -> tuple[list[int], list[int]]:
    adj = _adjacency(num_bodies, edges)
    parent = [-2] * num_bodies
    parent[root] = -1
    postorder: list[int] = []

    def visit(body: int) -> None:
        for neighbor, _edge_id in adj[body]:
            if parent[neighbor] == -2:
                parent[neighbor] = body
                visit(neighbor)
        postorder.append(body)

    visit(root)
    return parent, postorder


def _spanning_tree_edges(num_bodies: int, edges: list[tuple[int, int]], root: int) -> list[tuple[int, int]]:
    adj = _adjacency(num_bodies, edges)
    seen = {root}
    stack = [root]
    tree_edges: list[tuple[int, int]] = []
    while stack:
        body = stack.pop()
        for neighbor, edge_id in reversed(adj[body]):
            if neighbor not in seen:
                seen.add(neighbor)
                tree_edges.append(edges[edge_id])
                stack.append(neighbor)
    if len(seen) != num_bodies:
        raise ValueError("constraint graph must be connected")
    return tree_edges


def _default_loop_breaker(num_bodies: int, edges: list[tuple[int, int]]) -> int:
    for edge_id in range(len(edges) - 1, -1, -1):
        reduced = [edge for candidate_id, edge in enumerate(edges) if candidate_id != edge_id]
        if _connected(num_bodies, reduced):
            return edge_id
    raise ValueError("single-loop graph has no removable cycle edge")


def _chain_order(num_bodies: int, edges: list[tuple[int, int]], degrees: list[int]) -> list[int]:
    endpoints = [body for body, degree in enumerate(degrees) if degree <= 1]
    start = min(endpoints)
    adj = _adjacency(num_bodies, edges)
    order = [start]
    previous = -1
    current = start
    while len(order) < num_bodies:
        candidates = [neighbor for neighbor, _edge_id in adj[current] if neighbor != previous]
        if not candidates:
            break
        previous, current = current, candidates[0]
        order.append(current)
    return order


def classify_constraint_graph(num_bodies: int, edges: Any, root: int = 0) -> ConstraintGraphClassification:
    if num_bodies <= 0:
        raise ValueError("num_bodies must be positive")
    if not 0 <= int(root) < num_bodies:
        raise ValueError(f"root must be in [0, {num_bodies})")
    edge_list = _as_edges(edges, num_bodies)
    if not _connected(num_bodies, edge_list):
        raise ValueError("constraint graph must be connected")

    degrees = [0] * num_bodies
    for a, b in edge_list:
        degrees[a] += 1
        degrees[b] += 1
    cycle_rank = len(edge_list) - num_bodies + 1

    if len(edge_list) == num_bodies - 1:
        parent, postorder = _tree_orders(num_bodies, edge_list, int(root))
        if max(degrees) <= 2:
            kind = "chain"
            chain = _chain_order(num_bodies, edge_list, degrees)
        else:
            kind = "tree"
            chain = []
        loop_breakers: list[int] = []
    elif cycle_rank == 1:
        kind = "single_loop"
        loop_breakers = [_default_loop_breaker(num_bodies, edge_list)]
        spanning_edges = [edge for edge_id, edge in enumerate(edge_list) if edge_id not in loop_breakers]
        parent, postorder = _tree_orders(num_bodies, spanning_edges, int(root))
        chain = []
    else:
        kind = "general_graph"
        parent, postorder = _tree_orders(num_bodies, _spanning_tree_edges(num_bodies, edge_list, int(root)), int(root))
        chain = []
        loop_breakers = []

    return ConstraintGraphClassification(
        kind=kind,
        num_bodies=num_bodies,
        edges=edge_list,
        degrees=degrees,
        cycle_rank=cycle_rank,
        chain_order=chain,
        parent=parent,
        postorder=postorder,
        loop_breaker_edge_indices=loop_breakers,
    )


def reconstruct_constraint_graph_from_model(model: Any, root: int = 0) -> ReconstructedConstraintGraph:
    num_bodies = int(model.get_custom_frequency_count("mabd:body"))
    body_a = [int(value) for value in model.mabd.body_a.numpy()]
    body_b = [int(value) for value in model.mabd.body_b.numpy()]
    ranks = [int(value) for value in model.mabd.rank.numpy()]
    edges = list(zip(body_a, body_b, strict=True))
    return ReconstructedConstraintGraph(
        num_bodies=num_bodies,
        edges=edges,
        ranks=ranks,
        classification=classify_constraint_graph(num_bodies, edges, root=root),
    )


def _edge_order_for_chain(classification: ConstraintGraphClassification) -> list[int]:
    edge_order = []
    for body_a, body_b in zip(classification.chain_order[:-1], classification.chain_order[1:], strict=True):
        wanted = {body_a, body_b}
        for edge_id, edge in enumerate(classification.edges):
            if set(edge) == wanted:
                edge_order.append(edge_id)
                break
        else:
            raise ValueError("chain classification is inconsistent with edges")
    return edge_order


def _rows_for_edges(edge_slices: list[slice], edge_order: list[int]) -> list[int]:
    rows: list[int] = []
    for edge_id in edge_order:
        edge_slice = edge_slices[edge_id]
        rows.extend(range(edge_slice.start, edge_slice.stop))
    return rows


def _recover_dq(inputs: TopologyDualInputs, dlambda: np.ndarray) -> np.ndarray:
    return np.linalg.solve(inputs.H, inputs.f - inputs.J.T @ dlambda)


def _result_from_dlambda(
    topology: str,
    inputs: TopologyDualInputs,
    dlambda: np.ndarray,
    **kwargs: Any,
) -> TopologyKKTResult:
    dq = _recover_dq(inputs, dlambda)
    residual_norm = float(kwargs.pop("residual_norm", np.linalg.norm(inputs.dual_matrix @ dlambda - inputs.dual_rhs)))
    return TopologyKKTResult(topology=topology, dq=dq, dlambda=dlambda, residual_norm=residual_norm, **kwargs)


def _block_thomas_solve(
    diagonal_blocks: list[np.ndarray],
    off_diagonal_blocks: list[np.ndarray],
    rhs_blocks: list[np.ndarray],
) -> list[np.ndarray]:
    count = len(diagonal_blocks)
    c_prime: list[np.ndarray] = []
    d_prime: list[np.ndarray] = []
    for block_id in range(count):
        diag = diagonal_blocks[block_id].copy()
        rhs = rhs_blocks[block_id].copy()
        if block_id > 0:
            lower = off_diagonal_blocks[block_id - 1].T
            diag -= lower @ c_prime[block_id - 1]
            rhs -= lower @ d_prime[block_id - 1]
        if block_id < count - 1:
            c_prime.append(np.linalg.solve(diag, off_diagonal_blocks[block_id]))
        d_prime.append(np.linalg.solve(diag, rhs))

    out = [np.zeros_like(block) for block in rhs_blocks]
    out[-1] = d_prime[-1]
    for block_id in range(count - 2, -1, -1):
        out[block_id] = d_prime[block_id] - c_prime[block_id] @ out[block_id + 1]
    return out


def solve_chain_block_tridiagonal_kkt(
    body_hessians: Any,
    edges: Any,
    edge_gradients: Any,
    body_forces: Any,
    lower_rhs_blocks: Any | None = None,
) -> TopologyKKTResult:
    body_hessians = tuple(body_hessians)
    edges = tuple(edges)
    edge_gradients = tuple(edge_gradients)
    body_forces = tuple(body_forces)
    lower_rhs_blocks = None if lower_rhs_blocks is None else tuple(lower_rhs_blocks)
    inputs = assemble_topology_dual_inputs(body_hessians, edges, edge_gradients, body_forces, lower_rhs_blocks)
    classification = classify_constraint_graph(len(body_hessians), edges)
    if classification.kind != "chain":
        raise ValueError("solve_chain_block_tridiagonal_kkt requires chain topology")

    edge_order = _edge_order_for_chain(classification)
    row_order = _rows_for_edges(inputs.edge_slices, edge_order)
    S = inputs.dual_matrix[np.ix_(row_order, row_order)]
    rhs = inputs.dual_rhs[row_order]
    ordered_slices = []
    start = 0
    for edge_id in edge_order:
        rank = inputs.edge_slices[edge_id].stop - inputs.edge_slices[edge_id].start
        ordered_slices.append(slice(start, start + rank))
        start += rank

    diagonal_blocks = [S[slc, slc] for slc in ordered_slices]
    off_diagonal_blocks = [S[ordered_slices[i], ordered_slices[i + 1]] for i in range(len(ordered_slices) - 1)]
    rhs_blocks = [rhs[slc] for slc in ordered_slices]
    ordered_lambda_blocks = _block_thomas_solve(diagonal_blocks, off_diagonal_blocks, rhs_blocks)

    dlambda = np.zeros(inputs.dual_rhs.shape, dtype=float)
    for edge_id, block in zip(edge_order, ordered_lambda_blocks, strict=True):
        dlambda[inputs.edge_slices[edge_id]] = block
    return _result_from_dlambda("chain", inputs, dlambda, block_bandwidth=1)


def solve_tree_elimination_kkt(
    body_hessians: Any,
    edges: Any,
    edge_gradients: Any,
    body_forces: Any,
    lower_rhs_blocks: Any | None = None,
    root: int = 0,
) -> TopologyKKTResult:
    body_hessians = tuple(body_hessians)
    edges = tuple(edges)
    edge_gradients = tuple(edge_gradients)
    body_forces = tuple(body_forces)
    lower_rhs_blocks = None if lower_rhs_blocks is None else tuple(lower_rhs_blocks)
    inputs = assemble_topology_dual_inputs(body_hessians, edges, edge_gradients, body_forces, lower_rhs_blocks)
    classification = classify_constraint_graph(len(body_hessians), edges, root=root)
    if classification.kind not in {"tree", "chain"}:
        raise ValueError("solve_tree_elimination_kkt requires tree topology")
    dlambda = np.linalg.solve(inputs.dual_matrix, inputs.dual_rhs)
    return _result_from_dlambda(
        "tree",
        inputs,
        dlambda,
        parent=classification.parent,
        postorder=classification.postorder,
    )


def solve_loop_schur_complement_kkt(
    body_hessians: Any,
    edges: Any,
    edge_gradients: Any,
    body_forces: Any,
    lower_rhs_blocks: Any | None = None,
    loop_breaker_edge_indices: Any | None = None,
) -> TopologyKKTResult:
    body_hessians = tuple(body_hessians)
    edges = tuple(edges)
    edge_gradients = tuple(edge_gradients)
    body_forces = tuple(body_forces)
    lower_rhs_blocks = None if lower_rhs_blocks is None else tuple(lower_rhs_blocks)
    inputs = assemble_topology_dual_inputs(body_hessians, edges, edge_gradients, body_forces, lower_rhs_blocks)
    classification = classify_constraint_graph(len(body_hessians), edges)
    if classification.kind != "single_loop":
        raise ValueError("solve_loop_schur_complement_kkt requires a single-loop topology")
    breakers = [int(edge_id) for edge_id in (loop_breaker_edge_indices or classification.loop_breaker_edge_indices)]
    if not breakers:
        raise ValueError("at least one loop breaker edge is required")

    breaker_rows = _rows_for_edges(inputs.edge_slices, breakers)
    rest_edges = [edge_id for edge_id in range(len(classification.edges)) if edge_id not in set(breakers)]
    rest_rows = _rows_for_edges(inputs.edge_slices, rest_edges)
    A = inputs.dual_matrix[np.ix_(rest_rows, rest_rows)]
    C = inputs.dual_matrix[np.ix_(breaker_rows, rest_rows)]
    D = inputs.dual_matrix[np.ix_(breaker_rows, breaker_rows)]
    b_a = inputs.dual_rhs[rest_rows]
    b_d = inputs.dual_rhs[breaker_rows]
    inv_a_c_t = np.linalg.solve(A, C.T)
    inv_a_b = np.linalg.solve(A, b_a)
    schur = D - C @ inv_a_c_t
    x_d = np.linalg.solve(schur, b_d - C @ inv_a_b)
    x_a = np.linalg.solve(A, b_a - C.T @ x_d)

    dlambda = np.zeros(inputs.dual_rhs.shape, dtype=float)
    dlambda[rest_rows] = x_a
    dlambda[breaker_rows] = x_d
    return _result_from_dlambda(
        "single_loop",
        inputs,
        dlambda,
        loop_breaker_edge_indices=breakers,
        schur_complement=schur,
    )


def solve_graph_block_gauss_seidel_kkt(
    body_hessians: Any,
    edges: Any,
    edge_gradients: Any,
    body_forces: Any,
    lower_rhs_blocks: Any | None = None,
    schedule: tuple[tuple[int, ...], ...] | None = None,
    tolerance: float = 1.0e-10,
    max_iterations: int = 200,
    relaxation: float = 1.0,
) -> TopologyKKTResult:
    body_hessians = tuple(body_hessians)
    edges = tuple(edges)
    edge_gradients = tuple(edge_gradients)
    body_forces = tuple(body_forces)
    lower_rhs_blocks = None if lower_rhs_blocks is None else tuple(lower_rhs_blocks)
    inputs = assemble_topology_dual_inputs(body_hessians, edges, edge_gradients, body_forces, lower_rhs_blocks)
    edge_count = len(_as_edges(edges, len(body_hessians)))
    classification = classify_constraint_graph(len(body_hessians), edges)
    if schedule is None:
        raise ValueError("schedule must explicitly cover every constraint edge")
    normalized_schedule = tuple(tuple(int(edge_id) for edge_id in group) for group in schedule)
    if not normalized_schedule or any(not group for group in normalized_schedule):
        raise ValueError("schedule must contain at least one non-empty update group")
    covered_edges: set[int] = set()
    for group in normalized_schedule:
        for edge_id in group:
            if not 0 <= edge_id < edge_count:
                raise ValueError(f"schedule contains invalid edge id {edge_id}")
            covered_edges.add(edge_id)
    expected_edges = set(range(edge_count))
    if covered_edges != expected_edges:
        missing = sorted(expected_edges - covered_edges)
        extra = sorted(covered_edges - expected_edges)
        raise ValueError(f"schedule must cover every edge id at least once; missing={missing}, extra={extra}")

    S = inputs.dual_matrix
    rhs = inputs.dual_rhs
    dlambda = np.zeros_like(rhs)
    residual_norm = float(np.linalg.norm(S @ dlambda - rhs))
    converged = residual_norm <= tolerance
    iterations = 0
    for iteration in range(1, int(max_iterations) + 1):
        for group in normalized_schedule:
            for edge_id in group:
                slc = inputs.edge_slices[edge_id]
                local_rhs = rhs[slc] - S[slc, :] @ dlambda + S[slc, slc] @ dlambda[slc]
                updated = np.linalg.solve(S[slc, slc], local_rhs)
                dlambda[slc] = (1.0 - float(relaxation)) * dlambda[slc] + float(relaxation) * updated
        residual_norm = float(np.linalg.norm(S @ dlambda - rhs))
        iterations = iteration
        if residual_norm <= tolerance:
            converged = True
            break

    return _result_from_dlambda(
        classification.kind,
        inputs,
        dlambda,
        schedule=normalized_schedule,
        iterations=iterations,
        converged=converged,
        residual_norm=residual_norm,
    )


__all__ = [
    "ConstraintGraphClassification",
    "ReconstructedConstraintGraph",
    "TopologyDualInputs",
    "TopologyKKTResult",
    "assemble_topology_dual_inputs",
    "classify_constraint_graph",
    "reconstruct_constraint_graph_from_model",
    "solve_chain_block_tridiagonal_kkt",
    "solve_graph_block_gauss_seidel_kkt",
    "solve_loop_schur_complement_kkt",
    "solve_tree_elimination_kkt",
]
