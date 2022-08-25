r"""Classical shadows in the Pauli basis
========================================

.. meta::
    :property="og:description": Classical shadows in the Pauli basis
    :property="og:image": https://pennylane.ai/qml/_images/diffable_mitigation_thumb.png

.. related::

    classical_shadows
    ml_classical_shadows

*Author: Korbinian Kottmann, Posted: 22 September 2022*

abstract

Classical shadow theory
-----------------------

A `classical shadow` is a classical description of a quantum state that is capable of reproducing expectation values of local Pauli observables, see [#Huang2020]_.
We provide two additional demos in :doc:`tutorial_classical_shadows` and :doc:`tutorial_ml_classical_shadows`.

We are here focussing on the case where measurements are performed in the Pauli basis. The idea of classical shadows is to measure each qubit in a random Pauli basis.
While doing so, one keeps track of the performed measurement (its ``recipes``) in form of bits ``[0, 1, 2]`` corresponding to the measurement bases ``[X, Y, Z]``, respectively.
At the same time, the measurement outcome (its ``bits``) are recorded, where ``[0, 1]`` corresponds to the eigenvalues ``[1, -1]``, respectrively.

We record :math:`T` of such measurements, and for the :math:`t`-th measurement, we can reconstruct the ``local_snapshots``

.. math:: \rho^{(t)} = \bigotimes_{i=1}^{n} 3 U^\dagger_i |b_i \rangle \langle b_i | U_i - \mathbb{I},

where :math:`U_i` is rotating the qubit :math:`i` into the corresponding Pauli basis (e.g. :math:`U_i=H` for measurement in :math:`X`) at snapshot :math:`t`.
:math:`|b_i\rangle = (1 - b_i, b_i)` is the corresponding computational basis state given by the output bit :math:`b_i`.

From these local snapshots, one can compute expectation values of q-local Pauli strings, where locality refers to the number of non-Identity operators.

We show how to efficiently compute such expectation values without reconstructing any local density matrices using algebraic properties of Pauli operators.
Let us start by looking at individual snapshot expectation values :math:`\braket{\bigotimes_i\tilde{P}_i}^{(t)} = \text{tr}\left(\rho^{(t)} \left(\bigotimes_i\tilde{P}_i \right)\right)`
with :math:`\tilde{P}_i \in \{X, Y, Z, \mathbb{1}\}`. First, we convince ourselves of the identity

.. math:: U_i^\dagger |b_i\rangle \langle b_i| U_i = \frac{1}{2}\left((1-2b_i) P_i + \mathbb{1}\right),

where :math:`P_i \in \{X, Y, Z\}` is the Pauli operator corresponding to :math:`U_i` (Note that in this case :math:`P_i` is never the identity). 
The snapshot expectation value then reduces to

.. math:: \braket{\bigotimes_i\tilde{P}_i}^{(t)} = \prod_{i=1}^n \left(\tr{\frac{3}{2}(1-2b_i)P_i \tilde{P}_i + \frac{1}{2}\tilde{P}_i}\right).

The cases where :math:`\tilde{P}_i=\mathbb{1}` yield a trivial factor :math:`1` to the product.
The full product is always zero if any of the non-trivial :math:`\tilde{P}_i```` do not match :math:`P_i`. So in total, in the case that all Pauli operators match, we find

.. math:: \braket{\bigotimes_i\tilde{P}_i}^{(t)} = 3^q \prod_{\text{i non-trivial}}(1-2b_i).

This implies that in order to compute the expectation value of a Pauli string

.. math:: \braket{\bigotimes_i\tilde{P}_i} = \frac{1}{\tilde{T}} \sum_{\tilde{t}} \braket{\bigotimes_i\tilde{P}_i}^{(t)}

we simply need to sum the result bits for those  :math:`\tilde{T}` snapshots where the measurement recipe matches the observable,
indicated by the special index :math:`\tilde{t}` for the matching measurements.

This implies that computing expectation values with classical shadows comes down to picking the specific subset of snapshots where those specific observables
were already measured and discarding the remaining. If the desired observables are known prior to the measurement, one is thus advised to directly perform those measurements.
This was referred to as `derandomization` by the authors in a follow-up paper [#Huang2021]_.
Error bounds given by the number of measurements :math:`T = \mathcal{O}\left( \log(M) 4^\ell/\epsilon^2 \right)` guarantee that sufficiently many correct measurements
were performed to estimate :math:`M` different observables up to additive error :math:`\varepsilon`.

We will later compare this to directly measuring the desired observables and making use of simultaneously measuring qubit-wise-commuting observables. Before that, let us
demonstrate how to perform classical shadow measurements in a differentiable manner in PennyLane.

PennyLane implementation
------------------------

There are two ways of computing expectation values with classical shadows in PennyLane. The first is to return :func:`~.pennylane.shadow_expval` directly from the qnode.
"""

import pennylane as qml
import pennylane.numpy as np
from matplotlib import pyplot as plt
from pennylane import classical_shadow, shadow_expval, ClassicalShadow

H = qml.Hamiltonian([1., 1.], [qml.PauliZ(0) @ qml.PauliZ(1), qml.PauliX(0) @ qml.PauliX(1)])

dev = qml.device("default.qubit", wires=range(2), shots=10000)
@qml.qnode(dev)
def qnode(x, H):
    qml.Hadamard(0)
    qml.CNOT((0,1))
    qml.RX(x, wires=0)
    return shadow_expval(H)

x = np.array(0.5, requires_grad=True)

##############################################################################
# The big advantage of this way of computing expectation values is that it is differentiable.

print(qnode(x, H), qml.grad(qnode)(x, H))

##############################################################################
# Note that to avoid unnecessary device executions you can provide a list of observables to :func:`~.pennylane.shadow_expval`.

Hs = [H, qml.PauliX(0), qml.PauliY(0), qml.PauliZ(0)]
print(qnode(x, Hs))
print(qml.jacobian(qnode)(x, Hs))

##############################################################################
# Alternatively, you can compute expectation values by first performing the shadow measurement and then perform classical post-processing using the :class:`~.pennylane.ClassicalShadow`
# class methods.

dev = qml.device("default.qubit", wires=range(2), shots=1000)
@qml.qnode(dev)
def qnode(x):
    qml.Hadamard(0)
    qml.CNOT((0,1))
    qml.RX(x, wires=0)
    return classical_shadow(wires=range(2))

bits, recipes = qnode(0)
shadow = ClassicalShadow(bits, recipes)

##############################################################################
# After recording these ``T=1000`` quantum measurements, we can post-process the results to arbitrary local expectation values of Pauli strings.
# For example, we can compute the expectation value of a Pauli string

print(shadow.expval(qml.PauliX(0) @ qml.PauliX(1), k=1))

##############################################################################
# or of a Hamiltonian:

H = qml.Hamiltonian([1., 1.], [qml.PauliZ(0) @ qml.PauliZ(1), qml.PauliX(0) @ qml.PauliX(1)])
print(shadow.expval(H, k=1))



##############################################################################
# Comparing quantum resources with conventional measurement methods 
# -----------------------------------------------------------------
# 
# Simultaneously measuring qubit-wise-commuting observables

# 3 cases: extreme 1: one observable, intermediate: H2O Hamiltonian, extreme 3: all q-local operators.
# molecular Hamiltonian
symbols = ["H", "O", "H"]
coordinates = np.array([-0.0399, -0.0038, 0.0, 1.5780, 0.8540, 0.0, 2.7909, -0.5159, 0.0])
electrons = 10
orbitals = 7
core, active = qml.qchem.active_space(electrons, orbitals, active_electrons=4, active_orbitals=4)
multiplicity = 1
charge = 0
basis_set = "sto-3g"
H, n_wires = qml.qchem.molecular_hamiltonian(
    symbols,
    coordinates,
    charge=charge,
    mult=multiplicity,
    basis=basis_set,
    active_electrons=4,
    active_orbitals=4,
    mapping="bravyi_kitaev",
    method="pyscf"
)
coeffs, obs = H.coeffs, H.ops
H_qwc = qml.Hamiltonian(coeffs, obs, grouping_type="qwc")

len(qml.grouping.group_observables(obs))
singles, doubles = qml.qchem.excitations(electrons=4, orbitals=n_wires)
hf = qml.qchem.hf_state(4, n_wires)
theta = np.array([ 2.20700008e-02,  8.29716448e-02,  2.19227085e+00,
    3.19128513e+00, -1.35370403e+00,  6.61615333e-03,
    7.40317830e-01, -3.73367029e-01,  4.35206518e-02,
    -1.83668679e-03, -4.59312535e-03, -1.91103984e-02,
    8.21320961e-03, -1.48452294e-02, -1.88176061e-03,
    -1.66141213e-02, -8.94505652e-03,  6.92045656e-01,
    -4.54217610e-04, -8.22532179e-04,  5.27283799e-03,
    6.84640451e-03,  3.02313759e-01, -1.23117023e-03,
    4.42283398e-03,  6.02542038e-03])

# result on an ideal simulator
res_exact = -74.57076341
def circuit():
    qml.AllSinglesDoubles(weights = theta,
        wires = range(n_wires),
        hf_state = hf,
        singles = singles,
        doubles = doubles)
dev_exact = qml.device("default.qubit", wires=range(n_wires))
@qml.qnode(dev_exact)
def qnode_exact(obs):
    circuit()
    return qml.expval(obs)

res_exact = qnode_exact(H)
def rmsd(x, y):
    """root mean square difference"""
    return np.sqrt(np.mean((x - y)**2))
n_groups = len(qml.grouping.group_observables(obs))
d_qwc = []
d_sha = []

res_finites, res_shadows = [], []

n_wires = 8

shotss = np.arange(20, 220, 20)

for shots in shotss:
    for _ in range(10):

        
        dev_finite = qml.device("default.qubit", wires=range(n_wires), shots=int(shots))
        @qml.qnode(dev_finite)
        def qnode_finite(H):
            circuit()
            return qml.expval(H)

        with qml.Tracker(dev_finite) as tracker:
            res_finite = qnode_finite(H_qwc)

        dev_shadow = qml.device("default.qubit", wires=range(n_wires), shots=int(shots)*n_groups)

        @qml.qnode(dev_shadow)
        def qnode():
            circuit()
            return classical_shadow(wires=range(n_wires))
        
        bits, recipes = qnode()
        shadow = ClassicalShadow(bits, recipes)

        res_shadow = shadow.expval(H, k=1)

        assert tracker.totals["shots"] <=  int(shots)*n_groups
        if not _%25:
            print(tracker.totals["shots"], int(shots)*n_groups)

        res_finites.append(res_finite)
        res_shadows.append(res_shadow)

        d_qwc.append(rmsd(res_finite, res_exact))
        d_sha.append(rmsd(res_shadow, res_exact))
dq = np.array(d_qwc).reshape(len(shotss), 10)
dq, ddq = np.mean(dq, axis=1), np.var(dq, axis=1)
ds = np.array(d_sha).reshape(len(shotss), 10)
ds, dds = np.mean(ds, axis=1), np.var(ds, axis=1)
plt.errorbar(shotss*n_groups, ds, yerr=dds, fmt="x-", label="shadow")
plt.errorbar(shotss*n_groups, dq, yerr=ddq, fmt="x-", label="qwc")
plt.legend()



##############################################################################
#
# Conclusion
# ----------
# 
# conclusion
#
#
# References
# ----------
#
# .. [#Huang2020]
#
#     Hsin-Yuan Huang, Richard Kueng, John Preskill
#     "Predicting Many Properties of a Quantum System from Very Few Measurements."
#     `arXiv:2002.08953 <https://arxiv.org/abs/2002.08953>`__, 2020.
#
# .. [#Huang2021]
#
#     Hsin-Yuan Huang, Richard Kueng, John Preskill
#     "Efficient estimation of Pauli observables by derandomization."
#     `arXiv:2103.07510 <https://arxiv.org/abs/2103.07510>`__, 2021.

##############################################################################
# .. bio:: Korbinian Kottmann
#    :photo: ../_static/authors/qottmann.jpg
#
#    Korbinian is a summer resident at Xanadu, interested in (quantum) software development, quantum computing and (quantum) machine learning.