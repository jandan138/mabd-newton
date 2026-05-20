from __future__ import annotations

import unittest

import numpy as np


class NewtonExplicitEulerSolverTests(unittest.TestCase):
    def test_solver_explicit_euler_is_public_newton_solver(self) -> None:
        import newton

        self.assertTrue(hasattr(newton.solvers, "SolverExplicitEuler"))

    def test_solver_explicit_euler_uses_old_velocity_for_first_gravity_pose_step(self) -> None:
        import newton
        import warp as wp

        builder = newton.ModelBuilder(up_axis="Y", gravity=-9.81)
        body = builder.add_body(
            xform=wp.transform(wp.vec3(0.0, 1.0, 0.0), wp.quat_identity()),
            label="explicit_euler_body",
        )
        builder.add_shape_box(
            body=body,
            hx=0.1,
            hy=0.1,
            hz=0.1,
            cfg=newton.ModelBuilder.ShapeConfig(density=1000.0),
        )
        model = builder.finalize(device="cpu")
        state_in = model.state()
        state_out = model.state()
        control = model.control()
        contacts = model.contacts()

        solver = newton.solvers.SolverExplicitEuler(model, angular_damping=0.0)
        solver.step(state_in, state_out, control, contacts, 0.1)

        body_q = np.asarray(state_out.body_q.numpy()[body], dtype=float)
        body_qd = np.asarray(state_out.body_qd.numpy()[body], dtype=float)

        self.assertAlmostEqual(body_q[1], 1.0, places=6)
        self.assertAlmostEqual(body_qd[1], -0.981, places=5)


if __name__ == "__main__":
    unittest.main()
