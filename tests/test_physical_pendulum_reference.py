from __future__ import annotations

import unittest

import numpy as np
from scipy import special


class PhysicalPendulumReferenceTests(unittest.TestCase):
    def test_elliptic_reference_matches_paper_reference_points(self) -> None:
        from mabd_reproduction.physical_pendulum_reference import (
            physical_pendulum_angle_reference,
        )

        kappa = np.sqrt(0.5)
        omega_lin = 2.0
        complete = special.ellipk(kappa * kappa)

        angles = physical_pendulum_angle_reference(
            np.array([0.0, complete / omega_lin, 2.0 * complete / omega_lin]),
            kappa=kappa,
            omega_lin=omega_lin,
        )

        np.testing.assert_allclose(angles, [0.0, np.pi / 2.0, np.pi], atol=1.0e-12)

    def test_elliptic_reference_rejects_invalid_inputs(self) -> None:
        from mabd_reproduction.physical_pendulum_reference import (
            physical_pendulum_angle_reference,
        )

        invalid_cases = (
            {"times": [0.0], "kappa": 0.0, "omega_lin": 1.0, "match": "kappa"},
            {"times": [0.0], "kappa": 1.0, "omega_lin": 1.0, "match": "kappa"},
            {"times": [0.0], "kappa": 0.5, "omega_lin": 0.0, "match": "omega_lin"},
            {"times": [-0.1], "kappa": 0.5, "omega_lin": 1.0, "match": "times"},
        )
        for case in invalid_cases:
            with self.subTest(case=case):
                with self.assertRaisesRegex(ValueError, str(case["match"])):
                    physical_pendulum_angle_reference(
                        case["times"],
                        kappa=float(case["kappa"]),
                        omega_lin=float(case["omega_lin"]),
                    )


if __name__ == "__main__":
    unittest.main()
