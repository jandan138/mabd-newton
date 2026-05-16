# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

import numpy as np

from newton._src.solvers.mabd import (
    MABDActuationSpec,
    assemble_control_generalized_forces,
    evaluate_affine_pd_control,
)
from newton.tests.unittest_utils import get_test_devices, wp


class TestMABDControlForcesInternal(unittest.TestCase):
    def test_affine_pd_control_force_matches_formula(self) -> None:
        q = np.linspace(-0.3, 0.8, 12)
        qd = np.linspace(0.2, -0.1, 12)
        target_q = q + np.linspace(0.05, -0.02, 12)
        target_qd = qd + np.linspace(-0.03, 0.04, 12)
        feedforward = np.linspace(0.1, 1.2, 12)
        damping = np.linspace(0.5, 1.6, 12)

        evaluation = evaluate_affine_pd_control(
            q,
            qd,
            MABDActuationSpec(
                body_id=2,
                target_q=target_q,
                target_qd=target_qd,
                stiffness=3.0,
                damping=damping,
                feedforward_force=feedforward,
            ),
        )

        expected = 3.0 * (target_q - q) + damping * (target_qd - qd) + feedforward
        self.assertEqual(evaluation.body_id, 2)
        self.assertTrue(np.allclose(evaluation.position_error, target_q - q))
        self.assertTrue(np.allclose(evaluation.velocity_error, target_qd - qd))
        self.assertTrue(np.allclose(evaluation.generalized_force, expected))

    def test_assemble_control_generalized_forces_sums_by_body(self) -> None:
        q = [np.zeros(12), np.ones(12)]
        qd = [np.zeros(12), np.zeros(12)]
        base = [np.ones(12), np.full(12, 2.0)]
        observed = assemble_control_generalized_forces(
            q,
            qd,
            actuations=[
                MABDActuationSpec(body_id=1, target_q=np.full(12, 3.0), stiffness=0.5),
                MABDActuationSpec(
                    body_id=1,
                    target_qd=np.full(12, -2.0),
                    damping=0.25,
                    feedforward_force=np.arange(12, dtype=float),
                ),
                MABDActuationSpec(body_id=0, feedforward_force=np.full(12, -0.5)),
            ],
            base_external_forces=base,
        )

        expected_body_1 = (
            base[1]
            + 0.5 * (np.full(12, 3.0) - q[1])
            + 0.25 * np.full(12, -2.0)
            + np.arange(12)
        )
        self.assertTrue(np.allclose(observed[0], np.full(12, 0.5)))
        self.assertTrue(np.allclose(observed[1], expected_body_1))

    def test_control_force_validation_rejects_bad_ids_shapes_and_gains(self) -> None:
        with self.assertRaisesRegex(ValueError, "body_id"):
            assemble_control_generalized_forces(
                [np.zeros(12)],
                [np.zeros(12)],
                actuations=[MABDActuationSpec(body_id=3, feedforward_force=np.zeros(12))],
            )
        with self.assertRaisesRegex(ValueError, "target_q"):
            evaluate_affine_pd_control(
                np.zeros(12),
                np.zeros(12),
                MABDActuationSpec(body_id=0, target_q=np.zeros(11)),
            )
        with self.assertRaisesRegex(ValueError, "stiffness"):
            evaluate_affine_pd_control(
                np.zeros(12),
                np.zeros(12),
                MABDActuationSpec(body_id=0, stiffness=-1.0),
            )


devices = get_test_devices()


if __name__ == "__main__":
    wp.clear_kernel_cache()
    unittest.main(verbosity=2)
