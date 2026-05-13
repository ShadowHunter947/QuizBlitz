"""
================================================================================
Toy Statevector Simulator for:
"Quantum neural network with privacy protection of input data and
 training parameters" — Cheng Fang & Yan Chang, Physica Scripta 99 (2024)
================================================================================

SCOPE / HONESTY DISCLAIMER
──────────────────────────
• This is a NOISELESS STATEVECTOR proof-of-concept only.
• It DOES NOT perform practical encrypted inference on raw classical images.
• It DOES NOT provide hardware-level or cryptographic security.
• The goal is to verify algebraic circuit equivalence in simulation.
• The Rx / Ry hidden-parameter constructions here are DECOMPOSITION-BASED TOY
  models. The paper's full MBQC construction is only sketched via placeholder
  functions below.

The important exact check is Part 2: hiding Rz(theta) by absorbing theta into
an updated decryption/key angle, so no visible server-side Rz(theta) is needed.
================================================================================
"""

from __future__ import annotations

import time
import warnings
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity
from scipy.optimize import minimize
from sklearn.datasets import load_iris
from sklearn.preprocessing import MinMaxScaler

warnings.filterwarnings("ignore")

MASTER_SEED = 42
rng = np.random.default_rng(MASTER_SEED)
FIDELITY_THRESHOLD = 1.0 - 1e-6
DIFF_THRESHOLD = 1e-6


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — Core encryption primitives and utilities
# ══════════════════════════════════════════════════════════════════════════════
# Paper notation:
#   En(|psi>, a, omega) = X^a Rz(omega)|psi>
#   Dn(|out>, a', omega') = Rz(omega') X^a' |out>
# The server sees encrypted quantum states, not raw |psi>. Keys stay client-side.


def apply_encrypt(qc: QuantumCircuit, q: int, a: int, omega: float) -> None:
    """Apply En(., a, omega) = X^a Rz(omega) to qubit q."""
    qc.rz(omega, q)
    if int(a) == 1:
        qc.x(q)


def apply_decrypt(qc: QuantumCircuit, q: int, a: int, omega_prime: float) -> None:
    """Apply Dn(., a, omega_prime) = Rz(omega_prime) X^a to qubit q."""
    if int(a) == 1:
        qc.x(q)
    qc.rz(omega_prime, q)


def random_single_qubit_state(seed: int | None = None) -> Statevector:
    """Return a Haar-random single-qubit statevector using a fixedable seed."""
    local_rng = np.random.default_rng(seed)
    theta = local_rng.uniform(0.0, np.pi)
    phi = local_rng.uniform(0.0, 2.0 * np.pi)
    amp0 = np.cos(theta / 2.0)
    amp1 = np.exp(1j * phi) * np.sin(theta / 2.0)
    return Statevector([amp0, amp1])


def state_fidelity_compare(state1: Statevector, state2: Statevector) -> float:
    """Return |<state1|state2>|^2 as a Python float."""
    return float(state_fidelity(state1, state2))


def max_abs_error(state1: Statevector, state2: Statevector) -> float:
    """Return max amplitude error after aligning any physically irrelevant global phase."""
    a = np.asarray(state1.data, dtype=complex)
    b = np.asarray(state2.data, dtype=complex)
    inner = np.vdot(a, b)
    if abs(inner) > 0.0:
        b = b / (inner / abs(inner))
    return float(np.max(np.abs(a - b)))


def _state_from_circuit(qc: QuantumCircuit) -> Statevector:
    return Statevector.from_instruction(qc)


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — Exact hidden-parameter Rz verification
# ══════════════════════════════════════════════════════════════════════════════
# Plaintext: Rz(theta)|psi>
# Hidden version: Rz(theta - omega) X^a X^a Rz(omega)|psi> = Rz(theta)|psi>
# The true Rz parameter theta is hidden by absorbing it into a decryption/key
# update angle. No server-visible Rz(theta) gate is required.


def plaintext_rz_state(psi: Statevector, theta: float) -> Statevector:
    qc = QuantumCircuit(1)
    qc.initialize(psi.data, 0)
    qc.rz(theta, 0)
    return _state_from_circuit(qc)


def hidden_rz_state(psi: Statevector, theta: float, a: int, omega: float) -> Statevector:
    qc = QuantumCircuit(1)
    qc.initialize(psi.data, 0)
    apply_encrypt(qc, 0, a, omega)
    apply_decrypt(qc, 0, a, theta - omega)
    return _state_from_circuit(qc)


def hidden_rz_on_circuit(qc: QuantumCircuit, q: int, theta: float, a: int, omega: float) -> None:
    """In-place hidden Rz module: encrypt, then decrypt with theta absorbed."""
    apply_encrypt(qc, q, a, omega)
    apply_decrypt(qc, q, a, theta - omega)


def run_part2(n_tests: int = 50) -> dict[str, Any]:
    print("\n" + "═" * 84)
    print("PART 2 — Exact Hidden-Parameter Rz Verification")
    print("═" * 84)
    print(f"{'Test No':>7} | {'a':>1} | {'theta':>9} | {'omega':>9} | {'fidelity':>12} | {'max_error':>10} | Status")
    print("─" * 84)

    fidels: list[float] = []
    errs: list[float] = []
    all_pass = True
    seeds = rng.integers(0, 1_000_000, size=n_tests)

    for i in range(n_tests):
        psi = random_single_qubit_state(int(seeds[i]))
        a = int(rng.integers(0, 2))
        theta = float(rng.uniform(0, 2 * np.pi))
        omega = float(rng.uniform(0, 2 * np.pi))
        plain = plaintext_rz_state(psi, theta)
        hidden = hidden_rz_state(psi, theta, a, omega)
        fid = state_fidelity_compare(plain, hidden)
        err = max_abs_error(plain, hidden)
        ok = fid >= FIDELITY_THRESHOLD
        all_pass = all_pass and ok
        fidels.append(fid)
        errs.append(err)
        print(f"{i + 1:7d} | {a:1d} | {theta:9.5f} | {omega:9.5f} | {fid:12.9f} | {err:10.2e} | {'PASS' if ok else 'FAILED'}")

    return {"mean_fidelity": float(np.mean(fidels)), "max_error": float(np.max(errs)), "all_pass": all_pass}


# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — Alternative paper-style Rz relation
# ══════════════════════════════════════════════════════════════════════════════
# This version includes an explicit Rz(theta) operation:
# (Rz(2a theta - omega) X^a) Rz(theta) (X^a Rz(omega)) |psi> = Rz(theta)|psi>
# It is useful to verify the paper-style homomorphic relation, but the fully
# hidden Part 2 version is better for demonstrating parameter hiding because it
# removes the visible Rz(theta) gate and absorbs theta into decryption.


def paper_style_rz_state(psi: Statevector, theta: float, a: int, omega: float) -> Statevector:
    qc = QuantumCircuit(1)
    qc.initialize(psi.data, 0)
    apply_encrypt(qc, 0, a, omega)
    qc.rz(theta, 0)  # explicit server-visible Rz(theta)
    apply_decrypt(qc, 0, a, 2 * a * theta - omega)
    return _state_from_circuit(qc)


def run_part3(n_tests: int = 50) -> dict[str, Any]:
    print("\n" + "═" * 84)
    print("PART 3 — Paper-Style Rz Relation")
    print("═" * 84)
    fidels: list[float] = []
    errs: list[float] = []
    all_pass = True
    seeds = rng.integers(0, 1_000_000, size=n_tests)

    for i in range(n_tests):
        psi = random_single_qubit_state(int(seeds[i]))
        a = int(rng.integers(0, 2))
        theta = float(rng.uniform(0, 2 * np.pi))
        omega = float(rng.uniform(0, 2 * np.pi))
        plain = plaintext_rz_state(psi, theta)
        paper = paper_style_rz_state(psi, theta, a, omega)
        fid = state_fidelity_compare(plain, paper)
        err = max_abs_error(plain, paper)
        ok = fid >= FIDELITY_THRESHOLD
        if not ok:
            print(f"FAILED paper-style Rz test {i + 1}: fidelity={fid:.9f}, max_error={err:.2e}")
        all_pass = all_pass and ok
        fidels.append(fid)
        errs.append(err)

    print(f"Summary: mean fidelity={np.mean(fidels):.9f}, max error={np.max(errs):.2e}, {'PASS' if all_pass else 'FAILED'}")
    return {"mean_fidelity": float(np.mean(fidels)), "max_error": float(np.max(errs)), "all_pass": all_pass}


# ══════════════════════════════════════════════════════════════════════════════
# PART 4 — Rx and Ry handling
# ══════════════════════════════════════════════════════════════════════════════
# Rx and Ry are harder in the paper because the real hidden construction uses
# measurement-based quantum computation (MBQC) and masked measurement angles.
# Level A below is only a decomposition-based equivalence toy model, not the
# full MBQC hidden-parameter construction from the paper.


def plaintext_rx_state(psi: Statevector, theta: float) -> Statevector:
    qc = QuantumCircuit(1)
    qc.initialize(psi.data, 0)
    qc.rx(theta, 0)
    return _state_from_circuit(qc)


def plaintext_ry_state(psi: Statevector, theta: float) -> Statevector:
    qc = QuantumCircuit(1)
    qc.initialize(psi.data, 0)
    qc.ry(theta, 0)
    return _state_from_circuit(qc)


def toy_hidden_rx_on_circuit(qc: QuantumCircuit, q: int, theta: float, a: int, omega: float) -> None:
    """TOY: Rx(theta) = H Rz(theta) H with the inner Rz hidden."""
    qc.h(q)
    hidden_rz_on_circuit(qc, q, theta, a, omega)
    qc.h(q)


def toy_hidden_ry_on_circuit(qc: QuantumCircuit, q: int, theta: float, a: int, omega: float) -> None:
    """
    TOY: Ry(theta) from Rz/Rx decomposition with the inner Rz hidden.

    Matrix identity: Ry(theta) = Rz(pi/2) Rx(theta) Rz(-pi/2).
    Qiskit appends gates left-to-right, so the rightmost operator is appended
    first: Rz(-pi/2), then hidden Rx(theta), then Rz(pi/2).
    """
    qc.rz(-np.pi / 2, q)
    toy_hidden_rx_on_circuit(qc, q, theta, a, omega)
    qc.rz(np.pi / 2, q)


def toy_hidden_rx_state(psi: Statevector, theta: float, a: int, omega: float) -> Statevector:
    qc = QuantumCircuit(1)
    qc.initialize(psi.data, 0)
    toy_hidden_rx_on_circuit(qc, 0, theta, a, omega)
    return _state_from_circuit(qc)


def toy_hidden_ry_state(psi: Statevector, theta: float, a: int, omega: float) -> Statevector:
    qc = QuantumCircuit(1)
    qc.initialize(psi.data, 0)
    toy_hidden_ry_on_circuit(qc, 0, theta, a, omega)
    return _state_from_circuit(qc)


def mbqc_hidden_rx(*_args: Any, **_kwargs: Any) -> Statevector:
    """
    PLACEHOLDER ONLY — full MBQC hidden Rx is not implemented.

    In the paper, theta is hidden inside masked measurement angles (delta_1,
    delta_2*) sent by the client. A real implementation must build the cluster
    state, measure in rotated bases, consume measurement outcomes, and apply the
    feed-forward correction. This function deliberately raises instead of
    pretending the MBQC protocol is complete.
    """
    raise NotImplementedError("Full MBQC hidden Rx is not implemented in this toy simulator.")


def mbqc_hidden_ry(*_args: Any, **_kwargs: Any) -> Statevector:
    """
    PLACEHOLDER ONLY — full MBQC hidden Ry is not implemented.

    The paper hides theta by changing masked measurement angles. This skeleton
    is intentionally unfinished unless the exact measurement pattern and
    feed-forward logic are implemented.
    """
    raise NotImplementedError("Full MBQC hidden Ry is not implemented in this toy simulator.")


def run_part4(n_tests: int = 50) -> dict[str, Any]:
    print("\n" + "═" * 84)
    print("PART 4 — Rx/Ry Level A Decomposition-Based Toy Equivalence")
    print("═" * 84)
    rx_fidels: list[float] = []
    ry_fidels: list[float] = []
    rx_errs: list[float] = []
    ry_errs: list[float] = []
    rx_all_pass = True
    ry_all_pass = True
    seeds = rng.integers(0, 1_000_000, size=n_tests)

    for i in range(n_tests):
        psi = random_single_qubit_state(int(seeds[i]))
        theta = float(rng.uniform(0, 2 * np.pi))
        omega = float(rng.uniform(0, 2 * np.pi))
        a = int(rng.integers(0, 2))

        rx_plain = plaintext_rx_state(psi, theta)
        rx_hidden = toy_hidden_rx_state(psi, theta, a, omega)
        rx_fid = state_fidelity_compare(rx_plain, rx_hidden)
        rx_err = max_abs_error(rx_plain, rx_hidden)
        rx_all_pass = rx_all_pass and rx_fid >= FIDELITY_THRESHOLD
        rx_fidels.append(rx_fid)
        rx_errs.append(rx_err)

        ry_plain = plaintext_ry_state(psi, theta)
        ry_hidden = toy_hidden_ry_state(psi, theta, a, omega)
        ry_fid = state_fidelity_compare(ry_plain, ry_hidden)
        ry_err = max_abs_error(ry_plain, ry_hidden)
        ry_all_pass = ry_all_pass and ry_fid >= FIDELITY_THRESHOLD
        ry_fidels.append(ry_fid)
        ry_errs.append(ry_err)

        if rx_fid < FIDELITY_THRESHOLD or ry_fid < FIDELITY_THRESHOLD:
            print(f"FAILED Part 4 test {i + 1}: Rx fid={rx_fid:.9f}, Ry fid={ry_fid:.9f}")

    print(f"Hidden Rx: mean fidelity={np.mean(rx_fidels):.9f}, max error={np.max(rx_errs):.2e}, {'PASS' if rx_all_pass else 'FAILED'}")
    print(f"Hidden Ry: mean fidelity={np.mean(ry_fidels):.9f}, max error={np.max(ry_errs):.2e}, {'PASS' if ry_all_pass else 'FAILED'}")
    return {
        "rx_mean_fidelity": float(np.mean(rx_fidels)),
        "rx_max_error": float(np.max(rx_errs)),
        "rx_all_pass": rx_all_pass,
        "ry_mean_fidelity": float(np.mean(ry_fidels)),
        "ry_max_error": float(np.max(ry_errs)),
        "ry_all_pass": ry_all_pass,
    }


# ══════════════════════════════════════════════════════════════════════════════
# PART 5 — Toy 2-qubit QNN
# ══════════════════════════════════════════════════════════════════════════════
# This protected QNN is a modular algebraic verifier: single-qubit gates are
# checked through hidden-Rz modules, and CZ is checked through the paper-style
# encrypted CZ relation. It is not production-ready encrypted quantum cloud
# training and is not classical fully homomorphic encryption on images.


def _expectation_z0(state: Statevector) -> float:
    probs = state.probabilities()  # Qiskit little-endian basis ordering: |q1 q0>
    return float(probs[0] - probs[1] + probs[2] - probs[3])


def _build_plaintext_qnn(x: np.ndarray, theta: np.ndarray) -> QuantumCircuit:
    qc = QuantumCircuit(2)
    qc.ry(float(x[0]), 0)
    qc.ry(float(x[1]), 1)
    qc.rx(float(theta[0]), 0)
    qc.ry(float(theta[1]), 1)
    qc.cz(0, 1)
    qc.rz(float(theta[2]), 0)
    qc.rx(float(theta[3]), 1)
    return qc


def plaintext_qnn_state(x: np.ndarray, theta: np.ndarray) -> Statevector:
    return _state_from_circuit(_build_plaintext_qnn(x, theta))


def plaintext_qnn_predict(x: np.ndarray, theta: np.ndarray) -> float:
    return _expectation_z0(plaintext_qnn_state(x, theta))


def hidden_cz_on_circuit(qc: QuantumCircuit, q0: int, q1: int, a0: int, w0: float, a1: int, w1: float) -> None:
    """Paper Eq. 11 encrypted CZ relation as a toy module."""
    apply_encrypt(qc, q0, a0, w0)
    apply_encrypt(qc, q1, a1, w1)
    qc.cz(q0, q1)
    apply_decrypt(qc, q0, a0, -w0 - a1 * np.pi)
    apply_decrypt(qc, q1, a1, -w1 - a0 * np.pi)


def _fresh_key() -> tuple[int, float]:
    return int(rng.integers(0, 2)), float(rng.uniform(0, 2 * np.pi))


def protected_qnn_state(x: np.ndarray, theta: np.ndarray, keys: dict[str, float | int]) -> Statevector:
    """
    Return the protected toy QNN output state.

    Honesty note: this is a noiseless statevector proof-of-concept. The code
    encrypts encoded qubits and uses hidden modules to verify algebraic
    equivalence, but the Rx/Ry pieces are decomposition-based toy checks rather
    than the paper's full MBQC masked-measurement construction.
    """
    qc = QuantumCircuit(2)

    # Encode classical features as rotation angles. This is not encrypted raw
    # classical-image inference; it is a small toy angle-encoding demo.
    qc.ry(float(x[0]), 0)
    qc.ry(float(x[1]), 1)

    # Initial encrypted checkpoint for the encoded qubits, followed by client
    # decryption so the subsequent modular verifier starts in a known frame.
    a0, w0 = int(keys["a0"]), float(keys["omega0"])
    a1, w1 = int(keys["a1"]), float(keys["omega1"])
    apply_encrypt(qc, 0, a0, w0)
    apply_encrypt(qc, 1, a1, w1)
    apply_decrypt(qc, 0, a0, -w0)
    apply_decrypt(qc, 1, a1, -w1)

    # Ansatz gate 1: Rx(theta[0]) on q0 via decomposition-based hidden Rz.
    a, w = _fresh_key()
    toy_hidden_rx_on_circuit(qc, 0, float(theta[0]), a, w)

    # Ansatz gate 2: Ry(theta[1]) on q1 via decomposition-based hidden Rz.
    a, w = _fresh_key()
    toy_hidden_ry_on_circuit(qc, 1, float(theta[1]), a, w)

    # Ansatz gate 3: CZ(0, 1) via encrypted CZ relation.
    cz_a0, cz_w0 = _fresh_key()
    cz_a1, cz_w1 = _fresh_key()
    hidden_cz_on_circuit(qc, 0, 1, cz_a0, cz_w0, cz_a1, cz_w1)

    # Ansatz gate 4: Rz(theta[2]) on q0, exactly hidden in the decryption angle.
    a, w = _fresh_key()
    hidden_rz_on_circuit(qc, 0, float(theta[2]), a, w)

    # Ansatz gate 5: Rx(theta[3]) on q1 via decomposition-based hidden Rz.
    a, w = _fresh_key()
    toy_hidden_rx_on_circuit(qc, 1, float(theta[3]), a, w)

    # Final encrypt/decrypt checkpoint before measurement, making the decryption
    # step explicit before extracting <Z>.
    fa0, fw0 = _fresh_key()
    fa1, fw1 = _fresh_key()
    apply_encrypt(qc, 0, fa0, fw0)
    apply_encrypt(qc, 1, fa1, fw1)
    apply_decrypt(qc, 0, fa0, -fw0)
    apply_decrypt(qc, 1, fa1, -fw1)

    return _state_from_circuit(qc)


def protected_qnn_predict(x: np.ndarray, theta: np.ndarray, keys: dict[str, float | int]) -> float:
    return _expectation_z0(protected_qnn_state(x, theta, keys))


def run_part5(n_trials: int = 20) -> dict[str, Any]:
    print("\n" + "═" * 84)
    print("PART 5 — Toy 2-Qubit QNN Prediction Equivalence")
    print("═" * 84)
    print(f"{'Trial':>5} | {'Plain pred':>12} | {'Protected pred':>14} | {'abs diff':>10} | {'state fidelity':>14}")
    print("─" * 84)
    diffs: list[float] = []
    fidels: list[float] = []

    for i in range(n_trials):
        x = rng.uniform(0, np.pi, size=2)
        theta = rng.uniform(0, 2 * np.pi, size=4)
        keys = {"a0": int(rng.integers(0, 2)), "omega0": float(rng.uniform(0, 2 * np.pi)), "a1": int(rng.integers(0, 2)), "omega1": float(rng.uniform(0, 2 * np.pi))}
        plain_state = plaintext_qnn_state(x, theta)
        protected_state = protected_qnn_state(x, theta, keys)
        plain_pred = _expectation_z0(plain_state)
        protected_pred = _expectation_z0(protected_state)
        diff = abs(plain_pred - protected_pred)
        fid = state_fidelity_compare(plain_state, protected_state)
        diffs.append(diff)
        fidels.append(fid)
        print(f"{i + 1:5d} | {plain_pred:12.7f} | {protected_pred:14.7f} | {diff:10.2e} | {fid:14.9f}")

    mean_diff = float(np.mean(diffs))
    min_fid = float(np.min(fidels))
    all_pass = mean_diff < DIFF_THRESHOLD and min_fid >= FIDELITY_THRESHOLD
    if not all_pass:
        print(f"FAILED Part 5: mean diff={mean_diff:.2e}, min state fidelity={min_fid:.9f}")
    return {"mean_diff": mean_diff, "max_error": float(np.max(diffs)), "min_fidelity": min_fid, "all_pass": all_pass}


# ══════════════════════════════════════════════════════════════════════════════
# PART 6 — Tiny Iris binary classification demo
# ══════════════════════════════════════════════════════════════════════════════


def load_iris_binary() -> tuple[np.ndarray, np.ndarray]:
    data = load_iris()
    mask = data.target < 2
    x = data.data[mask, :2].astype(float)
    y = data.target[mask].astype(int)
    scaler = MinMaxScaler(feature_range=(0.0, np.pi))
    return scaler.fit_transform(x), y


def qnn_loss(theta: np.ndarray, x_data: np.ndarray, y_data: np.ndarray) -> float:
    total = 0.0
    for x, y in zip(x_data, y_data):
        pred = plaintext_qnn_predict(x, theta)
        label = 1.0 if y == 1 else -1.0
        total += (1.0 - pred * label) / 2.0
    return float(total / len(y_data))


def qnn_classify(pred: float) -> int:
    return 1 if pred >= 0.0 else 0


def run_part6() -> dict[str, Any]:
    print("\n" + "═" * 84)
    print("PART 6 — Tiny Iris Binary Classification Demo")
    print("═" * 84)
    x_data, y_data = load_iris_binary()
    theta0 = rng.uniform(0, 2 * np.pi, size=4)

    start = time.time()
    result = minimize(
        qnn_loss,
        theta0,
        args=(x_data, y_data),
        method="Nelder-Mead",
        options={"maxiter": 120, "xatol": 1e-4, "fatol": 1e-4, "disp": False},
    )
    runtime = time.time() - start
    theta_opt = result.x

    plain_states = [plaintext_qnn_state(x, theta_opt) for x in x_data]
    plain_preds = [_expectation_z0(s) for s in plain_states]
    plain_labels = [qnn_classify(p) for p in plain_preds]
    plain_acc = float(np.mean(np.asarray(plain_labels) == y_data))

    protected_states: list[Statevector] = []
    protected_preds: list[float] = []
    pred_diffs: list[float] = []
    state_fidels: list[float] = []
    for x, plain_state, plain_pred in zip(x_data, plain_states, plain_preds):
        keys = {"a0": int(rng.integers(0, 2)), "omega0": float(rng.uniform(0, 2 * np.pi)), "a1": int(rng.integers(0, 2)), "omega1": float(rng.uniform(0, 2 * np.pi))}
        protected_state = protected_qnn_state(x, theta_opt, keys)
        protected_pred = _expectation_z0(protected_state)
        protected_states.append(protected_state)
        protected_preds.append(protected_pred)
        pred_diffs.append(abs(plain_pred - protected_pred))
        state_fidels.append(state_fidelity_compare(plain_state, protected_state))

    protected_labels = [qnn_classify(p) for p in protected_preds]
    protected_acc = float(np.mean(np.asarray(protected_labels) == y_data))
    avg_diff = float(np.mean(pred_diffs))
    avg_fidelity = float(np.mean(state_fidels))

    print(f"Dataset: {len(x_data)} samples, 2 features, 2 classes")
    print(f"Optimizer: Nelder-Mead, final loss={result.fun:.6f}, success={result.success}")
    print(f"Plaintext accuracy: {plain_acc * 100:.1f}%")
    print(f"Protected accuracy: {protected_acc * 100:.1f}%")
    print(f"Average prediction difference: {avg_diff:.2e}")
    print(f"Average state fidelity: {avg_fidelity:.9f}")
    print(f"Runtime: {runtime:.2f}s")

    return {
        "plain_acc": plain_acc,
        "protected_acc": protected_acc,
        "avg_diff": avg_diff,
        "avg_state_fidelity": avg_fidelity,
        "runtime": runtime,
        "plain_preds": plain_preds,
        "protected_preds": protected_preds,
        "y": y_data,
    }


# ══════════════════════════════════════════════════════════════════════════════
# PART 7 — Summary table and plot
# ══════════════════════════════════════════════════════════════════════════════


def print_summary_table(p2: dict[str, Any], p3: dict[str, Any], p4: dict[str, Any], p5: dict[str, Any], p6: dict[str, Any]) -> None:
    print("\n" + "═" * 92)
    print("FINAL SUMMARY TABLE")
    print("═" * 92)
    print(f"{'Module':<38} | {'Fidelity / Diff':>16} | {'Max Error':>12} | Status")
    print("─" * 92)

    def row(name: str, value: float, err: float, ok: bool) -> None:
        print(f"{name:<38} | {value:16.9f} | {err:12.2e} | {'PASS' if ok else 'FAILED'}")

    row("Exact hidden Rz", p2["mean_fidelity"], p2["max_error"], p2["all_pass"])
    row("Paper-style Rz relation", p3["mean_fidelity"], p3["max_error"], p3["all_pass"])
    row("Decomposition toy Rx", p4["rx_mean_fidelity"], p4["rx_max_error"], p4["rx_all_pass"])
    row("Decomposition toy Ry", p4["ry_mean_fidelity"], p4["ry_max_error"], p4["ry_all_pass"])
    row("Toy QNN prediction equivalence", p5["mean_diff"], p5["max_error"], p5["all_pass"])
    row("Iris plaintext accuracy", p6["plain_acc"], 0.0, p6["plain_acc"] >= 0.5)
    row("Iris protected accuracy", p6["protected_acc"], p6["avg_diff"], p6["protected_acc"] >= 0.5 and p6["avg_diff"] < DIFF_THRESHOLD)
    print("═" * 92)


def plot_predictions(p6: dict[str, Any], out_path: str = "outputs/qnn_privacy_results.png") -> str:
    plain = np.asarray(p6["plain_preds"], dtype=float)
    protected = np.asarray(p6["protected_preds"], dtype=float)
    labels = np.asarray(p6["y"], dtype=int)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    colors = ["royalblue" if label == 0 else "tomato" for label in labels]
    lim = max(float(np.max(np.abs(plain))), float(np.max(np.abs(protected))), 1e-9) * 1.05

    axes[0].scatter(plain, protected, c=colors, edgecolors="k", linewidths=0.4, alpha=0.8, s=55)
    axes[0].plot([-lim, lim], [-lim, lim], "k--", lw=0.8, label="y = x")
    axes[0].axhline(0, color="grey", lw=0.5)
    axes[0].axvline(0, color="grey", lw=0.5)
    axes[0].set_xlim(-lim, lim)
    axes[0].set_ylim(-lim, lim)
    axes[0].set_xlabel("Plaintext <Z> prediction")
    axes[0].set_ylabel("Protected <Z> prediction")
    axes[0].set_title("Plaintext vs Protected Predictions")
    axes[0].legend(fontsize=8)

    diff = np.abs(plain - protected)
    axes[1].bar(np.arange(len(diff)), diff, color="steelblue", alpha=0.75, edgecolor="k", linewidth=0.3)
    axes[1].set_xlabel("Sample index")
    axes[1].set_ylabel("|Plain - Protected|")
    axes[1].set_title("Per-Sample Absolute Difference")
    axes[1].set_yscale("log")

    plt.tight_layout()
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Plot saved to {path}")
    return str(path)


if __name__ == "__main__":
    print(
        """
╔══════════════════════════════════════════════════════════════════════════════╗
║ Quantum Neural Network Privacy-Protection Simulator                         ║
║ Noiseless statevector proof-of-concept only                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    )
    p2_results = run_part2(n_tests=50)
    p3_results = run_part3(n_tests=50)
    p4_results = run_part4(n_tests=50)
    p5_results = run_part5(n_trials=20)
    p6_results = run_part6()
    print_summary_table(p2_results, p3_results, p4_results, p5_results, p6_results)
    plot_predictions(p6_results)
    print(
        """
HONESTY NOTES
1. The server sees encrypted quantum states, not raw |psi>.
2. Rz(theta) can be hidden by absorbing theta into a decryption/key-update angle.
3. Rx and Ry are harder because the paper uses MBQC with masked measurement angles.
4. Rx/Ry here are toy decomposition-based equivalence checks unless full MBQC is implemented.
5. This is not classical fully homomorphic encryption on images.
6. This is not production-ready encrypted quantum cloud training.
7. All results are noiseless statevector simulation only. Failed fidelity checks are printed.
"""
    )
