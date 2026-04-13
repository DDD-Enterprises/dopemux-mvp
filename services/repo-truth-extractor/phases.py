from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Dict, List, Set


class PhaseId(StrEnum):
    A = "A"
    H = "H"
    D = "D"
    C = "C"
    E = "E"
    W = "W"
    B = "B"
    G = "G"
    X = "X"
    Q = "Q"
    R = "R"
    T = "T"
    Z = "Z"
    S = "S"
    SP = "SP"


@dataclass(frozen=True)
class PhaseDefinition:
    phase_id: PhaseId
    dir_name: str
    display_name: str
    purpose: str
    required_dependencies: tuple[str, ...]
    optional_dependencies: tuple[str, ...]


PHASES = [phase.value for phase in PhaseId]
PHASE_S_BASE_STEPS = tuple(f"S{i}" for i in range(13))
PHASE_S_BASE_STEP_SET = set(PHASE_S_BASE_STEPS)
PHASE_SP_BASE_STEPS = tuple(f"SP{i}" for i in range(13))
PHASE_SP_BASE_STEP_SET = set(PHASE_SP_BASE_STEPS)
VERIFY_PHASE_CHOICES = PHASES + ["ALL"]
CODE_HEAVY_PHASES = {"C", "E", "Q"}
R_REQUIRED_INPUT_PHASES = ["A", "H", "D", "C"]
R_OPTIONAL_INPUT_PHASES = ["B", "E", "G", "W", "Q", "X"]

PHASE_DEFINITIONS = (
    PhaseDefinition(
        phase_id=PhaseId.A,
        dir_name="A_repo_control_plane",
        display_name="Repo Plane",
        purpose="Scan repository instruction, router, hook, compose, and provider-control surfaces.",
        required_dependencies=(),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.H,
        dir_name="H_home_control_plane",
        display_name="Home Plane",
        purpose="Scan operator home-level configs, providers, tmux flows, and local control-plane state.",
        required_dependencies=(),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.D,
        dir_name="D_docs_pipeline",
        display_name="Docs Plane",
        purpose="Extract documentation contracts, drift, recency, and canonical doc boundaries.",
        required_dependencies=(),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.C,
        dir_name="C_code_surfaces",
        display_name="Code Plane",
        purpose="Extract code entrypoints, schemas, runtime writers, and implementation truth surfaces.",
        required_dependencies=(),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.E,
        dir_name="E_execution_plane",
        display_name="Execution Plane",
        purpose="Map execution/bootstrap surfaces such as scripts, installers, docker, and ops entrypoints.",
        required_dependencies=(),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.W,
        dir_name="W_workflow_plane",
        display_name="Workflow Plane",
        purpose="Map workflows, automation surfaces, and execution orchestration paths.",
        required_dependencies=(),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.B,
        dir_name="B_boundary_plane",
        display_name="Boundary Plane",
        purpose="Extract boundary enforcement, contracts, and cross-plane isolation surfaces.",
        required_dependencies=(),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.G,
        dir_name="G_governance_plane",
        display_name="Governance Plane",
        purpose="Extract governance rules, hygiene controls, and policy enforcement surfaces.",
        required_dependencies=(),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.X,
        dir_name="X_feature_index",
        display_name="Feature Index",
        purpose="Index repo feature surfaces directly from code, config, scripts, and docs.",
        required_dependencies=(),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.Q,
        dir_name="Q_quality_assurance",
        display_name="Quality Assurance",
        purpose="Cross-check prior phases for contract failures, gaps, and extractor QA signals.",
        required_dependencies=("A", "H", "D", "C", "E", "W", "B", "G", "X"),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.R,
        dir_name="R_arbitration",
        display_name="Arbitration",
        purpose="Arbitrate normalized truth across required upstream phases and optional enrichments.",
        required_dependencies=tuple(R_REQUIRED_INPUT_PHASES),
        optional_dependencies=tuple(R_OPTIONAL_INPUT_PHASES),
    ),
    PhaseDefinition(
        phase_id=PhaseId.T,
        dir_name="T_task_packets",
        display_name="Task Packets",
        purpose="Derive task packets from arbitration and feature-index outputs.",
        required_dependencies=("R", "X"),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.Z,
        dir_name="Z_handoff_freeze",
        display_name="Handoff Freeze",
        purpose="Freeze final handoff package from arbitration, feature index, and task packets.",
        required_dependencies=("R", "X", "T"),
        optional_dependencies=(),
    ),
    PhaseDefinition(
        phase_id=PhaseId.S,
        dir_name="S_synthesis",
        display_name="Synthesis",
        purpose="Synthesize the final truth pack from arbitration outputs plus downstream rollups.",
        required_dependencies=("R",),
        optional_dependencies=("X", "T", "Z", "MANUAL"),
    ),
    PhaseDefinition(
        phase_id=PhaseId.SP,
        dir_name="SP_synthesis_pipeline",
        display_name="Synthesis Pipeline",
        purpose="Post-processing pipeline: dedupe, drift check, promotion readiness, redaction, linting, stability.",
        required_dependencies=("R",),
        optional_dependencies=("X", "T", "Z"),
    ),
)

PHASE_DIR_NAMES: Dict[str, str] = {definition.phase_id.value: definition.dir_name for definition in PHASE_DEFINITIONS}
PHASE_DISPLAY_NAMES: Dict[str, str] = {
    definition.phase_id.value: definition.display_name for definition in PHASE_DEFINITIONS
}
PHASE_PURPOSES: Dict[str, str] = {
    definition.phase_id.value: definition.purpose for definition in PHASE_DEFINITIONS
}
PHASE_REQUIRED_DEPENDENCIES: Dict[str, List[str]] = {
    definition.phase_id.value: list(definition.required_dependencies) for definition in PHASE_DEFINITIONS
}
PHASE_OPTIONAL_DEPENDENCIES: Dict[str, List[str]] = {
    definition.phase_id.value: list(definition.optional_dependencies) for definition in PHASE_DEFINITIONS
}

REQUIRED_PROMPT_STEP_IDS: Dict[str, Set[str]] = {
    "A": {"A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11", "A12", "A13", "A99"},
    "H": {"H0", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H9"},
    "D": {"D0", "D1", "D2", "D3", "D4", "D5"},
    "C": {"C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20", "C21"},
    "E": {"E0", "E1", "E2", "E3", "E4", "E5", "E6", "E9"},
    "W": {"W0", "W1", "W2", "W3", "W4", "W5", "W9"},
    "B": {"B0", "B1", "B2", "B3", "B9"},
    "G": {"G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G9"},
    "Q": {"Q0", "Q1", "Q2", "Q3", "Q9", "Q11"},
    "R": {"R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11"},
    "X": {"X0", "X1", "X2", "X3", "X4", "X9"},
    "T": {"T0", "T1", "T2", "T3", "T4", "T5", "T9"},
    "Z": {"Z0", "Z1", "Z2", "Z9"},
    "S": set(PHASE_S_BASE_STEPS),
    "SP": set(PHASE_SP_BASE_STEPS),
    "M": {"M0", "M1", "M2", "M3", "M4", "M5", "M6"},
}

LEGACY_PHASE_DIR_ALIASES: Dict[str, str] = {
    "R2_synthesis": "R_arbitration",
}
