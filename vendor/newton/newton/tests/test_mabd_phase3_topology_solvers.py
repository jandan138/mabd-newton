from __future__ import annotations

import unittest
from dataclasses import dataclass

import numpy as np

from newton._src.solvers import mabd


@dataclass(frozen=True)
class TopologyFixture:
    body_hessians: tuple[np.ndarray, ...]
    body_forces: tuple[np.ndarray, ...]
    edges: tuple[tuple[int, int], ...]
    edge_gradients: tuple[tuple[np.ndarray, np.ndarray], ...]
    lower_rhs_blocks: tuple[np.ndarray, ...]
    H: np.ndarray
    J: np.ndarray
    f: np.ndarray
    lower_rhs: np.ndarray


def _edge_gradient(rank: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    g_a = 0.15 * rng.normal(size=(rank, 12))
    g_b = 0.15 * rng.normal(size=(rank, 12))
    for row in range(rank):
        g_a[row, row] += 1.0
        g_b[row, 6 + row] -= 0.7
    return g_a, g_b


def _fixture(edges: tuple[tuple[int, int], ...], ranks: tuple[int, ...]) -> TopologyFixture:
    num_bodies = max(max(edge) for edge in edges) + 1
    body_hessians = tuple((2.0 + 0.35 * body_id) * np.eye(12) for body_id in range(num_bodies))
    body_forces = tuple(np.linspace(-0.2, 0.35, 12) + 0.03 * body_id for body_id in range(num_bodies))
    edge_gradients = tuple(_edge_gradient(rank, 20 + edge_id) for edge_id, rank in enumerate(ranks))
    lower_rhs_blocks = tuple(np.linspace(-0.03, 0.02, rank) + 0.002 * edge_id for edge_id, rank in enumerate(ranks))
    H = np.zeros((12 * num_bodies, 12 * num_bodies), dtype=float)
    for body_id, block in enumerate(body_hessians):
        start = 12 * body_id
        H[start : start + 12, start : start + 12] = block
    rows = []
    for (body_a, body_b), (grad_a, grad_b) in zip(edges, edge_gradients, strict=True):
        rank = grad_a.shape[0]
        row = np.zeros((rank, 12 * num_bodies), dtype=float)
        row[:, 12 * body_a : 12 * body_a + 12] = grad_a
        row[:, 12 * body_b : 12 * body_b + 12] = grad_b
        rows.append(row)
    return TopologyFixture(
        body_hessians=body_hessians,
        body_forces=body_forces,
        edges=edges,
        edge_gradients=edge_gradients,
        lower_rhs_blocks=lower_rhs_blocks,
        H=H,
        J=np.vstack(rows),
        f=np.concatenate(body_forces),
        lower_rhs=np.concatenate(lower_rhs_blocks),
    )


class MABDPhase3InternalTests(unittest.TestCase):
    def test_chain_block_tridiagonal_matches_dense_dual_kkt(self) -> None:
        p = _fixture(((0, 1), (1, 2), (2, 3)), (2, 3, 2))
        dense = mabd.solve_dense_dual_kkt(p.H, p.J, p.f, lower_rhs=p.lower_rhs)

        result = mabd.solve_chain_block_tridiagonal_kkt(
            p.body_hessians,
            p.edges,
            p.edge_gradients,
            p.body_forces,
            p.lower_rhs_blocks,
        )

        self.assertTrue(np.allclose(result.dlambda, dense.dlambda, atol=1.0e-10))
        self.assertTrue(np.allclose(result.dq, dense.dq, atol=1.0e-10))

    def test_chain_solver_accepts_single_pass_iterables(self) -> None:
        p = _fixture(((0, 1), (1, 2), (2, 3)), (2, 3, 2))
        dense = mabd.solve_dense_dual_kkt(p.H, p.J, p.f, lower_rhs=p.lower_rhs)

        result = mabd.solve_chain_block_tridiagonal_kkt(
            iter(p.body_hessians),
            iter(p.edges),
            iter(p.edge_gradients),
            iter(p.body_forces),
            iter(p.lower_rhs_blocks),
        )

        self.assertTrue(np.allclose(result.dlambda, dense.dlambda, atol=1.0e-10))
        self.assertTrue(np.allclose(result.dq, dense.dq, atol=1.0e-10))

    def test_loop_schur_complement_matches_dense_dual(self) -> None:
        p = _fixture(((0, 1), (1, 2), (2, 3), (3, 0)), (2, 2, 2, 3))
        dense = mabd.solve_dense_dual_kkt(p.H, p.J, p.f, lower_rhs=p.lower_rhs)

        result = mabd.solve_loop_schur_complement_kkt(
            p.body_hessians,
            p.edges,
            p.edge_gradients,
            p.body_forces,
            p.lower_rhs_blocks,
            loop_breaker_edge_indices=[3],
        )

        self.assertTrue(np.allclose(result.dlambda, dense.dlambda, atol=1.0e-10))
        self.assertTrue(np.allclose(result.dq, dense.dq, atol=1.0e-10))

    def test_graph_block_gauss_seidel_converges_to_dense_dual(self) -> None:
        p = _fixture(((0, 1), (1, 2), (2, 3), (3, 0), (0, 2)), (1, 1, 1, 1, 1))
        dense = mabd.solve_dense_dual_kkt(p.H, p.J, p.f, lower_rhs=p.lower_rhs)

        result = mabd.solve_graph_block_gauss_seidel_kkt(
            p.body_hessians,
            p.edges,
            p.edge_gradients,
            p.body_forces,
            p.lower_rhs_blocks,
            schedule=((0, 1, 3), (4, 2), (3, 1, 0), (2, 4)),
            tolerance=1.0e-10,
            max_iterations=200,
        )

        self.assertTrue(result.converged)
        self.assertTrue(np.allclose(result.dlambda, dense.dlambda, atol=2.0e-8))

    def test_graph_block_gauss_seidel_requires_complete_explicit_schedule(self) -> None:
        p = _fixture(((0, 1), (1, 2), (2, 3), (3, 0), (0, 2)), (1, 1, 1, 1, 1))

        with self.assertRaisesRegex(ValueError, "schedule must explicitly cover"):
            mabd.solve_graph_block_gauss_seidel_kkt(
                p.body_hessians,
                p.edges,
                p.edge_gradients,
                p.body_forces,
                p.lower_rhs_blocks,
            )

        with self.assertRaisesRegex(ValueError, "missing=\\[4\\]"):
            mabd.solve_graph_block_gauss_seidel_kkt(
                p.body_hessians,
                p.edges,
                p.edge_gradients,
                p.body_forces,
                p.lower_rhs_blocks,
                schedule=((0, 1), (2, 3)),
            )

    def test_single_loop_classification_uses_cycle_edge_breaker(self) -> None:
        classification = mabd.classify_constraint_graph(5, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4)])

        self.assertEqual(classification.kind, "single_loop")
        self.assertIn(classification.loop_breaker_edge_indices[0], [0, 1, 2])
        self.assertNotIn(-2, classification.parent)


if __name__ == "__main__":
    unittest.main()
