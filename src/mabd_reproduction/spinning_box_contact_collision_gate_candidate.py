"""Fail-closed unilateral contact/collision gate candidate for spinning box."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from time import perf_counter

import numpy as np
from newton.solvers import SolverMABD

from .experiment_configs import SpinningBoxRunConfig
from .reporting import ClaimReport, EvidenceStatus, write_claim_report
from .single_body_reports import (
    _assign_solver_mabd_state,
    _elastic_energy,
    _kinetic_energy,
    _read_solver_mabd_state,
    _spinning_box_solver_mabd_static_plane_model,
)
from .spinning_box_affine_static_plane_contacts_rollout_candidate import (
    _initial_qd,
    _sample_indices,
    _state_sample,
    _step_count,
)
from .spinning_box_physics import mabd_momentum_diagnostics, spinning_box_contact_diagnostics


BASELINE_LANE = "spinning_box_contact_collision_gate_candidate"
SOLVER_MODE = "solver_mabd_unilateral_static_plane_contact_gate_candidate"
BACKEND = "cpu_newton_solver_mabd_unilateral_static_plane_contact_gate_candidate"
CONTACT_CONSTRAINT_POLICY = "free_predict_detect_static_plane_contacts_then_unilateral_constrained_step"
CONTACT_DETECTION_SOURCE = "SolverMABD.detect_static_plane_contacts"
UNILATERAL_CONTACT_POLICY = "dense_cpu_active_set_drop_tensile_plane_rows"
PHASE88_ROLLOUT_CANDIDATE_REPORT = (
    "reports/experiment_matrix/"
    "single_body_spinning_box_affine_static_plane_contacts_rollout_candidate.json"
)


@dataclass(frozen=True)
class SpinningBoxContactCollisionGateCandidateRollout:
    step_count: int
    time_step_s: float
    duration_s: float
    sample_count: int
    total_wall_time_ms: float
    initial_energy_j: float
    final_energy_j: float
    relative_total_energy_drift: float
    final_position_m: np.ndarray
    final_linear_momentum_kg_m_s: np.ndarray
    final_angular_momentum_kg_m2_s: np.ndarray
    max_free_predicted_contact_penetration_m: float
    max_constrained_contact_penetration_m: float
    max_constraint_residual_norm: float
    max_contacts_input_overflow_count: int
    max_contacts_input_generated_plane_constraint_count: int
    max_affine_static_plane_candidate_contact_count: int
    max_unilateral_plane_requested_count: int
    max_unilateral_plane_accepted_count: int
    max_unilateral_plane_rejected_count: int
    max_unilateral_plane_skipped_count: int
    contact_count_summary: dict[str, int]
    trajectory_samples: tuple[dict[str, object], ...]


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_spinning_box_contact_collision_gate_candidate(
    config: SpinningBoxRunConfig,
) -> SpinningBoxContactCollisionGateCandidateRollout:
    lane = config.contact_collision_gate_candidate
    step_count = _step_count(lane)
    sample_indices = _sample_indices(step_count, lane.sample_count)
    mass_matrix = np.diag(config.mass_diagonal)

    model, _box_shape, _plane_shape = _spinning_box_solver_mabd_static_plane_model(config)
    state = model.state()
    solver = SolverMABD(model)
    solver.configure_cpu_oracle(
        replace(
            solver._cpu_oracle_config_from_model(),
            contact_constraint_mode=lane.contact_constraint_mode,
            topology="dense",
        )
    )
    q = config.initial_q.copy()
    qd = _initial_qd(lane)
    _assign_solver_mabd_state(state, q, qd)

    initial_energy = _kinetic_energy(qd, mass_matrix) + _elastic_energy(config=config, q=q)
    trajectory_samples: list[dict[str, object]] = []
    contact_counts: list[int] = []
    max_free_penetration = 0.0
    max_constrained_penetration = 0.0
    max_constraint_residual = 0.0
    max_overflow = 0
    max_generated_plane_constraints = 0
    max_candidate_contacts = 0
    max_unilateral_requested = 0
    max_unilateral_accepted = 0
    max_unilateral_rejected = 0
    max_unilateral_skipped = 0

    start = perf_counter()
    for step_index in range(step_count + 1):
        q, qd = _read_solver_mabd_state(state)
        if step_index in sample_indices:
            trajectory_samples.append(
                _state_sample(
                    config=config,
                    q=q,
                    qd=qd,
                    step_index=step_index,
                    time_step_s=lane.time_step_s,
                    mass_matrix=mass_matrix,
                )
            )
        if step_index == step_count:
            break

        q_current = q.copy()
        qd_current = qd.copy()
        solver.step(state, state, control=None, contacts=None, dt=lane.time_step_s)
        free_q, free_qd = _read_solver_mabd_state(state)
        free_contact = spinning_box_contact_diagnostics(config, free_q, free_qd)
        max_free_penetration = max(
            max_free_penetration,
            float(free_contact.max_penetration_depth),
        )

        contacts = solver.detect_static_plane_contacts(state)
        collision_summary = solver.last_static_plane_collision_summary
        if collision_summary is None:
            raise RuntimeError("SolverMABD.detect_static_plane_contacts() did not record summary")
        contact_counts.append(int(collision_summary.candidate_contact_count))
        max_candidate_contacts = max(
            max_candidate_contacts,
            int(collision_summary.candidate_contact_count),
        )

        _assign_solver_mabd_state(state, q_current, qd_current)
        solver.step(state, state, control=None, contacts=contacts, dt=lane.time_step_s)
        q_next, qd_next = _read_solver_mabd_state(state)
        constrained_contact = spinning_box_contact_diagnostics(config, q_next, qd_next)
        max_constrained_penetration = max(
            max_constrained_penetration,
            float(constrained_contact.max_penetration_depth),
        )

        step_result = solver.last_step_result
        if step_result is None:
            raise RuntimeError("SolverMABD.step() did not record last_step_result")
        max_constraint_residual = max(
            max_constraint_residual,
            float(getattr(step_result, "constraint_residual_norm", 0.0)),
        )
        max_unilateral_requested = max(
            max_unilateral_requested,
            int(step_result.unilateral_plane_constraint_requested_count),
        )
        max_unilateral_accepted = max(
            max_unilateral_accepted,
            int(step_result.unilateral_plane_constraint_accepted_count),
        )
        max_unilateral_rejected = max(
            max_unilateral_rejected,
            int(step_result.unilateral_plane_constraint_rejected_count),
        )
        max_unilateral_skipped = max(
            max_unilateral_skipped,
            int(step_result.unilateral_plane_constraint_skipped_count),
        )
        contacts_summary = solver.last_contacts_input_summary
        if contacts_summary is not None:
            max_overflow = max(
                max_overflow,
                int(contacts_summary.rigid_contact_overflow_count),
            )
            max_generated_plane_constraints = max(
                max_generated_plane_constraints,
                int(contacts_summary.generated_plane_constraint_count),
            )

    total_wall_time_ms = (perf_counter() - start) * 1000.0
    q, qd = _read_solver_mabd_state(state)
    final_energy = _kinetic_energy(qd, mass_matrix) + _elastic_energy(config=config, q=q)
    momentum = mabd_momentum_diagnostics(config, q, qd)
    contact_count_summary = {
        "initial": int(contact_counts[0]) if contact_counts else 0,
        "final": int(contact_counts[-1]) if contact_counts else 0,
        "min": min(contact_counts) if contact_counts else 0,
        "max": max(contact_counts) if contact_counts else 0,
    }
    relative_energy_drift = (
        0.0 if initial_energy == 0.0 else abs(final_energy - initial_energy) / abs(initial_energy)
    )

    return SpinningBoxContactCollisionGateCandidateRollout(
        step_count=step_count,
        time_step_s=lane.time_step_s,
        duration_s=lane.duration_s,
        sample_count=lane.sample_count,
        total_wall_time_ms=total_wall_time_ms,
        initial_energy_j=initial_energy,
        final_energy_j=final_energy,
        relative_total_energy_drift=relative_energy_drift,
        final_position_m=q[9:12],
        final_linear_momentum_kg_m_s=momentum.linear_momentum_kg_m_s,
        final_angular_momentum_kg_m2_s=momentum.angular_momentum_kg_m2_s,
        max_free_predicted_contact_penetration_m=max_free_penetration,
        max_constrained_contact_penetration_m=max_constrained_penetration,
        max_constraint_residual_norm=max_constraint_residual,
        max_contacts_input_overflow_count=max_overflow,
        max_contacts_input_generated_plane_constraint_count=max_generated_plane_constraints,
        max_affine_static_plane_candidate_contact_count=max_candidate_contacts,
        max_unilateral_plane_requested_count=max_unilateral_requested,
        max_unilateral_plane_accepted_count=max_unilateral_accepted,
        max_unilateral_plane_rejected_count=max_unilateral_rejected,
        max_unilateral_plane_skipped_count=max_unilateral_skipped,
        contact_count_summary=contact_count_summary,
        trajectory_samples=tuple(trajectory_samples),
    )


def _threshold_violations(
    rollout: SpinningBoxContactCollisionGateCandidateRollout,
    thresholds: dict[str, float],
) -> list[str]:
    candidates = {
        "max_contacts_input_overflow_count": float(rollout.max_contacts_input_overflow_count),
        "max_constraint_residual_norm": rollout.max_constraint_residual_norm,
        "max_relative_total_energy_drift": rollout.relative_total_energy_drift,
        "max_runtime_wall_time_ms": rollout.total_wall_time_ms,
        "max_unilateral_plane_rejected_count": float(rollout.max_unilateral_plane_rejected_count),
    }
    return sorted(
        key
        for key, value in candidates.items()
        if key in thresholds and float(value) > float(thresholds[key])
    )


def write_spinning_box_contact_collision_gate_candidate_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    lane = config.contact_collision_gate_candidate
    rollout = run_spinning_box_contact_collision_gate_candidate(config)
    threshold_violations = _threshold_violations(rollout, lane.thresholds)
    blockers = [
        "unilateral_static_plane_contact_not_paper_faithful",
        "paper_faithful_affine_collision_missing",
        "finite_plane_clipping_missing",
        "body_body_affine_contact_missing",
        "friction_restitution_ccd_missing",
        "spinning_box_comparison_pass_gate_not_enabled",
        "paper_faithful_gate_not_evaluated",
    ]
    if threshold_violations:
        blockers.insert(1, "contact_collision_gate_candidate_thresholds_violated")

    repo_root = Path(__file__).resolve().parents[2]
    phase88_path = repo_root / PHASE88_ROLLOUT_CANDIDATE_REPORT
    phase88_sha256 = _sha256_file(phase88_path) if phase88_path.exists() else "missing"

    observed = {
        "candidate_status": "contact_collision_gate_candidate_recorded",
        "gate_scope": lane.gate_scope,
        "paper_faithful": lane.paper_faithful,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
        "comparison_pass_gate_enabled": False,
        "contact_constraint_policy": CONTACT_CONSTRAINT_POLICY,
        "unilateral_contact_policy": UNILATERAL_CONTACT_POLICY,
        "contact_detection_source": CONTACT_DETECTION_SOURCE,
        "contacts_input_summary_source": "last_contacts_input_summary",
        "static_plane_collision_summary_source": "last_static_plane_collision_summary",
        "newton_contacts_api": "newton.Contacts",
        "solver_step_api": "SolverMABD.step(..., contacts=...)",
        "contact_constraint_mode": lane.contact_constraint_mode,
        "phase88_rollout_candidate_report": PHASE88_ROLLOUT_CANDIDATE_REPORT,
        "phase88_rollout_candidate_sha256": phase88_sha256,
        "duration_s": rollout.duration_s,
        "time_step_s": rollout.time_step_s,
        "step_count": rollout.step_count,
        "sample_count": rollout.sample_count,
        "initial_energy_j": rollout.initial_energy_j,
        "final_energy_j": rollout.final_energy_j,
        "relative_total_energy_drift": rollout.relative_total_energy_drift,
        "final_position_m": rollout.final_position_m.tolist(),
        "final_linear_momentum_kg_m_s": rollout.final_linear_momentum_kg_m_s.tolist(),
        "final_angular_momentum_kg_m2_s": rollout.final_angular_momentum_kg_m2_s.tolist(),
        "max_free_predicted_contact_penetration_m": (
            rollout.max_free_predicted_contact_penetration_m
        ),
        "max_constrained_contact_penetration_m": (
            rollout.max_constrained_contact_penetration_m
        ),
        "max_constraint_residual_norm": rollout.max_constraint_residual_norm,
        "max_contacts_input_overflow_count": rollout.max_contacts_input_overflow_count,
        "max_contacts_input_generated_plane_constraint_count": (
            rollout.max_contacts_input_generated_plane_constraint_count
        ),
        "max_affine_static_plane_candidate_contact_count": (
            rollout.max_affine_static_plane_candidate_contact_count
        ),
        "max_unilateral_plane_requested_count": rollout.max_unilateral_plane_requested_count,
        "max_unilateral_plane_accepted_count": rollout.max_unilateral_plane_accepted_count,
        "max_unilateral_plane_rejected_count": rollout.max_unilateral_plane_rejected_count,
        "max_unilateral_plane_skipped_count": rollout.max_unilateral_plane_skipped_count,
        "contact_count_summary": rollout.contact_count_summary,
        "threshold_violations": threshold_violations,
        "trajectory_samples": list(rollout.trajectory_samples),
        "blocking_reasons": blockers,
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode=SOLVER_MODE,
        backend=BACKEND,
        baseline_lane=BASELINE_LANE,
        expected={
            "paper_claim_status": "contact/collision gate candidate only; no lane gate",
            "gate_scope": lane.gate_scope,
            "paper_faithful": False,
            "paper_comparable": False,
            "full_experiment_claim_passed": False,
            "comparison_pass_gate_enabled": False,
            "source_lines": list(config.source_lines),
        },
        observed=observed,
        threshold=lane.thresholds,
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "single-body contact/collision gate candidate recorded; this is not "
            "a paper-faithful affine collision solver, comparison pass, or timing claim"
        ),
        timing_distribution={
            "scope": "local_cpu_wall_clock_not_paper_comparable",
            "paper_comparable": False,
            "total_wall_time_ms": rollout.total_wall_time_ms,
        },
        raw_outputs={"trajectory": "embedded_compact_samples"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "write_spinning_box_contact_collision_gate_candidate_report",
    "run_spinning_box_contact_collision_gate_candidate",
]
