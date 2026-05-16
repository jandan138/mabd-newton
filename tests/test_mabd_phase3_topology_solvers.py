from __future__ import annotations

from dataclasses import dataclass
import unittest

import numpy as np
import warp as wp

import newton
from newton.solvers import SolverMABD, mabd


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
    edge_ranks: tuple[int, ...]


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
    f = np.concatenate(body_forces)
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
    J = np.vstack(rows)
    lower_rhs = np.concatenate(lower_rhs_blocks)
    return TopologyFixture(
        body_hessians=body_hessians,
        body_forces=body_forces,
        edges=edges,
        edge_gradients=edge_gradients,
        lower_rhs_blocks=lower_rhs_blocks,
        H=H,
        J=J,
        f=f,
        lower_rhs=lower_rhs,
        edge_ranks=ranks,
    )


def _chain_problem() -> TopologyFixture:
    return _fixture(((0, 1), (1, 2), (2, 3)), (2, 3, 2))


def _tree_problem() -> TopologyFixture:
    return _fixture(((0, 1), (1, 2), (1, 3)), (2, 2, 3))


def _single_loop_problem() -> TopologyFixture:
    return _fixture(((0, 1), (1, 2), (2, 3), (3, 0)), (2, 2, 2, 3))


def _general_graph_problem() -> TopologyFixture:
    return _fixture(((0, 1), (1, 2), (2, 3), (3, 0), (0, 2)), (1, 1, 1, 1, 1))


def _loop_model_with_mabd_constraints() -> object:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    for body_id in range(4):
        newton_body = builder.add_body()
        builder.add_custom_values(
            **{
                "mabd:body_index": newton_body,
                "mabd:young_modulus": 100.0,
                "mabd:poisson_ratio": 0.25,
                "mabd:density": 1.0,
                "mabd:polar_mode": 0,
            }
        )
    for edge, rank in zip(((0, 1), (1, 2), (2, 3), (3, 0)), (3, 5, 4, 3), strict=True):
        builder.add_custom_values(
            **{
                "mabd:constraint_type": 1,
                "mabd:body_a": edge[0],
                "mabd:body_b": edge[1],
                "mabd:rank": rank,
                "mabd:gradient_mode": 1,
                "mabd:axis0": wp.vec3(0.0, 1.0, 0.0),
                "mabd:axis1": wp.vec3(0.0, 0.0, 1.0),
            }
        )
    return builder.finalize()


class MABDPhase3TopologySolverTests(unittest.TestCase):
    def test_chain_block_tridiagonal_matches_dense_dual_kkt(self) -> None:
        p = _chain_problem()
        dense = mabd.solve_dense_dual_kkt(p.H, p.J, p.f, lower_rhs=p.lower_rhs)

        self.assertTrue(
            hasattr(mabd, "solve_chain_block_tridiagonal_kkt"),
            "mabd.solve_chain_block_tridiagonal_kkt must be exposed",
        )
        result = mabd.solve_chain_block_tridiagonal_kkt(
            p.body_hessians,
            p.edges,
            p.edge_gradients,
            p.body_forces,
            p.lower_rhs_blocks,
        )

        self.assertEqual(result.topology, "chain")
        self.assertEqual(result.block_bandwidth, 1)
        self.assertTrue(np.allclose(result.dlambda, dense.dlambda, atol=1.0e-10))
        self.assertTrue(np.allclose(result.dq, dense.dq, atol=1.0e-10))
        self.assertTrue(np.allclose(p.H @ result.dq + p.J.T @ result.dlambda, p.f, atol=1.0e-10))
        self.assertTrue(np.allclose(p.J @ result.dq, p.lower_rhs, atol=1.0e-10))

    def test_chain_solver_accepts_single_pass_iterables(self) -> None:
        p = _chain_problem()
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

    def test_tree_elimination_matches_dense_dual_kkt_and_records_orders(self) -> None:
        p = _tree_problem()
        dense = mabd.solve_dense_dual_kkt(p.H, p.J, p.f, lower_rhs=p.lower_rhs)

        self.assertTrue(hasattr(mabd, "solve_tree_elimination_kkt"), "mabd.solve_tree_elimination_kkt must be exposed")
        result = mabd.solve_tree_elimination_kkt(
            p.body_hessians,
            p.edges,
            p.edge_gradients,
            p.body_forces,
            p.lower_rhs_blocks,
            root=0,
        )

        self.assertEqual(result.topology, "tree")
        self.assertEqual(result.parent, [-1, 0, 1, 1])
        self.assertEqual(result.postorder, [2, 3, 1, 0])
        self.assertTrue(np.allclose(result.dlambda, dense.dlambda, atol=1.0e-10))
        self.assertTrue(np.allclose(result.dq, dense.dq, atol=1.0e-10))
        self.assertTrue(np.allclose(p.J @ result.dq, p.lower_rhs, atol=1.0e-10))

    def test_loop_schur_complement_matches_dense_dual_and_uses_declared_breaker(self) -> None:
        p = _single_loop_problem()
        dense = mabd.solve_dense_dual_kkt(p.H, p.J, p.f, lower_rhs=p.lower_rhs)

        self.assertTrue(
            hasattr(mabd, "solve_loop_schur_complement_kkt"),
            "mabd.solve_loop_schur_complement_kkt must be exposed",
        )
        result = mabd.solve_loop_schur_complement_kkt(
            p.body_hessians,
            p.edges,
            p.edge_gradients,
            p.body_forces,
            p.lower_rhs_blocks,
            loop_breaker_edge_indices=[3],
        )

        self.assertEqual(result.topology, "single_loop")
        self.assertEqual(result.loop_breaker_edge_indices, [3])
        self.assertEqual(result.schur_complement.shape, (p.edge_ranks[3], p.edge_ranks[3]))
        self.assertTrue(np.allclose(result.dlambda, dense.dlambda, atol=1.0e-10))
        self.assertTrue(np.allclose(result.dq, dense.dq, atol=1.0e-10))

    def test_graph_block_gauss_seidel_converges_to_dense_dual_with_recorded_schedule(self) -> None:
        p = _general_graph_problem()
        dense = mabd.solve_dense_dual_kkt(p.H, p.J, p.f, lower_rhs=p.lower_rhs)
        schedule = ((0, 1, 3), (4, 2), (3, 1, 0), (2, 4))

        self.assertTrue(
            hasattr(mabd, "solve_graph_block_gauss_seidel_kkt"),
            "mabd.solve_graph_block_gauss_seidel_kkt must be exposed",
        )
        result = mabd.solve_graph_block_gauss_seidel_kkt(
            p.body_hessians,
            p.edges,
            p.edge_gradients,
            p.body_forces,
            p.lower_rhs_blocks,
            schedule=schedule,
            tolerance=1.0e-10,
            max_iterations=200,
        )

        self.assertEqual(result.topology, "general_graph")
        self.assertEqual(result.schedule, schedule)
        self.assertTrue(result.converged)
        self.assertLessEqual(result.iterations, 200)
        self.assertLess(result.residual_norm, 1.0e-9)
        self.assertTrue(np.allclose(result.dlambda, dense.dlambda, atol=2.0e-8))
        self.assertTrue(np.allclose(result.dq, dense.dq, atol=2.0e-8))

    def test_graph_block_gauss_seidel_requires_complete_explicit_schedule(self) -> None:
        p = _general_graph_problem()

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

    def test_graph_classification_and_model_reconstruction_are_deterministic(self) -> None:
        self.assertTrue(hasattr(mabd, "classify_constraint_graph"), "mabd.classify_constraint_graph must be exposed")
        self.assertTrue(
            hasattr(mabd, "reconstruct_constraint_graph_from_model"),
            "mabd.reconstruct_constraint_graph_from_model must be exposed",
        )

        chain = mabd.classify_constraint_graph(4, [(0, 1), (1, 2), (2, 3)])
        self.assertEqual(chain.kind, "chain")
        self.assertEqual(chain.chain_order, [0, 1, 2, 3])
        self.assertEqual(chain.cycle_rank, 0)
        self.assertEqual(chain.degrees, [1, 2, 2, 1])

        tree = mabd.classify_constraint_graph(4, [(0, 1), (1, 2), (1, 3)], root=0)
        self.assertEqual(tree.kind, "tree")
        self.assertEqual(tree.parent, [-1, 0, 1, 1])
        self.assertEqual(tree.postorder, [2, 3, 1, 0])

        loop = mabd.classify_constraint_graph(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
        self.assertEqual(loop.kind, "single_loop")
        self.assertEqual(loop.cycle_rank, 1)
        self.assertEqual(loop.loop_breaker_edge_indices, [3])

        branched_loop = mabd.classify_constraint_graph(5, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4)])
        self.assertEqual(branched_loop.kind, "single_loop")
        self.assertIn(branched_loop.loop_breaker_edge_indices[0], [0, 1, 2])
        breaker = branched_loop.loop_breaker_edge_indices[0]
        spanning_edges = [
            edge for edge_id, edge in enumerate(branched_loop.edges) if edge_id != breaker
        ]
        spanning_tree = mabd.classify_constraint_graph(5, spanning_edges)
        self.assertIn(spanning_tree.kind, {"chain", "tree"})
        self.assertNotIn(-2, branched_loop.parent)

        graph = mabd.reconstruct_constraint_graph_from_model(_loop_model_with_mabd_constraints())
        self.assertEqual(graph.num_bodies, 4)
        self.assertEqual(graph.edges, [(0, 1), (1, 2), (2, 3), (3, 0)])
        self.assertEqual(graph.ranks, [3, 5, 4, 3])
        self.assertEqual(graph.classification.kind, "single_loop")

    def test_solver_step_remains_unsupported_in_phase3(self) -> None:
        model = newton.ModelBuilder().finalize()
        solver = SolverMABD(model)

        with self.assertRaises(NotImplementedError):
            solver.step(model.state(), model.state(), None, None, 0.01)


if __name__ == "__main__":
    unittest.main()
