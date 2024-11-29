r"""Fixed Depth Hamiltonian Simulation via Cartan Decomposition
===============================================================

We introduce the powerful Lie theoretic decomposition technique for Hamiltonians, :math:`H = K h K^\dagger`,
that lets you time-evolve by arbitrary times with fixed depth, :math:`e^{-i t H} = K e^{-i t h} K^\dagger`.
In particular, we follow the approach in [#Kökcü]_ that directly provides us with a (fixed depth) circuit
decomposition of the unitaries :math:`K` and :math:`e^{-i t h}`.

Sounds too good to be true? There are of course caveats, mostly of practical nature.
One of them is that the relevant Lie algebra becomes too large to handle. This is still an extremely
powerful mathematical result integral for quantum compilation, circuit optimization and Hamiltonian simulation.

Introduction
------------

The :doc:`KAK theorem </demos/tutorial_kak_theorem>` is an important result from Lie theory that states that any Lie group element :math:`U` can be decomposed
as :math:`U = K_1 A K_2`, where :math:`K_{1, 2}` and :math:`A` are elements of two special sub-groups
:math:`\mathcal{K}` and :math:`\mathcal{A}`, respectively. In special cases, the decomposition simplifies to :math:`U = K A K^\dagger`.

You can think of this KAK decomposition as a generalization of
the singular value decomposition to Lie groups. For that, recall that the singular value decomposition states that any
matrix :math:`M \in \mathbb{C}^{m \times n}` can be decomposed as :math:`M = U \Lambda V^\dagger`, where :math:`\Lambda`
are the diagonal singular values and :math:`U \in \mathbb{C}^{m \times \mu}` and :math:`V^\dagger \in \mathbb{C}^{\mu \times n}`
are left- and right-unitary with :math:`\mu = \min(m, n)`.

In the case of the KAK decomposition, :math:`\mathcal{A}` is an Abelian subgroup such that all its elements are commuting,
just as is the case for diagonal matrices.

We can use this general result from Lie theory as a powerful circuit decomposition technique.

.. note:: We recommend a basic understanding of Lie algebras, see e.g. our :doc:`intro for quantum practitioners </demos/tutorial_liealgebra>`.
    Otherwise this demo should be self-contained. For the mathematically inclined we further recommend our :doc:`demo on the KAK theorem </demos/tutorial_kak_theorem>`
    that dives into the mathematical depths of the theorem and provides more background info.

Goal
----

Unitary gates in quantum computing are described by the special unitary Lie group :math:`SU(2^n)`, so we can use the KAK
theorem to decompose quantum gates into :math:`U = K_1 A K_2`. While the mathematical statement is rather straight-forward,
actually finding this decomposition is not. We are going to follow the recipe prescribed in 
`Fixed Depth Hamiltonian Simulation via Cartan Decomposition <https://arxiv.org/abs/2104.00728>`__ [#Kökcü]_, 
that tackles this decomposition on the level of the associated Lie algebra via Cartan decomposition.

In particular, we are going to consider the problem of time-evolving a Hermitian operator :math:`H` the generates the time-evolution unitary :math:`U = e^{-i t H}`.
We are going to perform a special case of KAK decomposition, a "KhK decomposition" if you will, on the algebraic level in terms of

.. math:: H = K^\dagger h_0 K.

This then induces the KAK decomposition on the group level as

.. math:: e^{-i t H} = K^\dagger e^{-i t h_0} K.

Let us walk through an explicit example, doing theory and code side-by-side.

For that we are going to use the generators of the Heisenberg model Hamiltonian for :math:`n=4` qubits on a one dimensional chain,

.. math:: \{X_i X_{i+1}, Z_i Z_{i+1}, Z_i Z_{i+1}\}_{i=0}^{2}.

The foundation to a KAK decomposition is a Cartan decomposition of the associated Lie algebra :math:`\mathfrak{g}`.
For that, let us first construct it and import some libraries that we are going to use later.


"""
from datetime import datetime
import matplotlib.pyplot as plt

import numpy as np
import pennylane as qml
from pennylane import X, Y, Z

import jax
import jax.numpy as jnp
import optax
jax.config.update("jax_enable_x64", True)

n_wires = 4
gens = [X(i) @ X(i+1) for i in range(n_wires-1)]
gens += [Y(i) @ Y(i+1) for i in range(n_wires-1)]
gens += [Z(i) @ Z(i+1) for i in range(n_wires-1)]

H = qml.sum(*gens)

g = qml.lie_closure(gens)
g = [op.pauli_rep for op in g]

##############################################################################
# 
# Cartan decomposition
# --------------------
# 
# A Cartan decomposition is a bipartition :math:`\mathfrak{g} = \mathfrak{k} \oplus \mathfrak{m}` into a vertical subspace
# :math:`\mathfrak{k}` and an orthogonal horizontal subspace :math:`\mathfrak{m}`. In practice, it can be induced by an
# involution function :math:`\Theta` that fulfils :math:`\Theta(\Theta(g)) = g \ \forall g \in \mathfrak{g}`. Different 
# involutions lead to different types of Cartan decompositions, which have been fully classified by Cartan 
# (see `Wikipedia <https://en.wikipedia.org/wiki/Symmetric_space#Classification_result>`__).
# 
# .. note::
#     Note that :math:`\mathfrak{k}` is the small letter k in
#     `Fraktur <https://en.wikipedia.org/wiki/Fraktur>`__ and a 
#     common - not our - choice for the vertical subspace in a Cartan decomposition.
#
# One common choice of involution is the so-called even-odd involution for Pauli words
# :math:`P = P_1 \otimes P_2 .. \otimes P_n` where :math:`P_j \in \{I, X, Y, Z\}`.
# It essentially counts whether the number of non-identity Pauli operators in the Pauli word is even or odd.

def even_odd_involution(op):
    """Generalization of EvenOdd to sums of Paulis"""
    [pw] = op.pauli_rep
    return len(pw) % 2

even_odd_involution(X(0)), even_odd_involution(X(0) @ Y(3))

##############################################################################
# 
# The vertical and horizontal subspaces are the two eigenspaces of the involution, corresponding to the :math:`\pm 1` eigenvalues.
# In particular, we have :math:`\Theta(\mathfrak{k}) = \mathfrak{k}` and :math:`\Theta(\mathfrak{m}) = - \mathfrak{m}`.
# So in order to perform the Cartan decomposition :math:`\mathfrak{g} = \mathfrak{k} \oplus \mathfrak{m}`, we simply
# sort the operators by whether or not they yield a plus or minus sign from the involution function.
# This is possible because the operators and involution nicely align with the eigenspace decomposition.

def cartan_decomposition(g, involution):
    """Cartan Decomposition g = k + m
    
    Args:
        g (List[PauliSentence]): the (dynamical) Lie algebra to decompose
        involution (callable): Involution function :math:`\Theta(\cdot)` to act on PauliSentence ops, should return ``0/1`` or ``True/False``.
    
    Returns:
        k (List[PauliSentence]): the vertical subspace :math:`\Theta(x) = x`
        m (List[PauliSentence]): the horizontal subspace :math:`\Theta(x) = -x` """
    m = []
    k = []

    for op in g:
        if involution(op): # vertical space when involution returns True
            k.append(op)
        else: # horizontal space when involution returns False
            m.append(op)
    return k, m

k, m = cartan_decomposition(g, even_odd_involution)
len(g), len(k), len(m)


##############################################################################
# We have successfully decomposed the :math:`60`-dimensional Lie algebra 
# into a :math:`24`-dimensional vertical subspace and a :math:`36`-dimensional subspace.
#
# Note that not every bipartition of a Lie algebra constitutes a Cartan decomposition.
# For that, the subspaces need to fulfil the following three commutation relations
#
# .. math::
#     \begin{align}
#     [\mathfrak{k}, \mathfrak{k}] \subseteq \mathfrak{k} & \text{ (subalgebra)}\\
#     [\mathfrak{k}, \mathfrak{m}] \subseteq \mathfrak{m} & \text{ (reductive property)}\\
#     [\mathfrak{m}, \mathfrak{m}] \subseteq \mathfrak{k} & \text{ (symmetric property)}
#     \end{align}
#
# In particular, :math:`\mathfrak{k}` is closed under commutation and is therefore a subalgebra, whereas :math:`\mathfrak{m}` is not.
# This also has the consequence that the associated Lie group :math:`\mathcal{K} := e^{i \mathfrak{k}}` is a subgroup
# of the associated Lie group :math:`\mathcal{G} := e^{i \mathfrak{g}}`.
#
# Cartan subalgebra
# -----------------
# 
# With this we have identified the first subgroup (:math:`\mathcal{K}`) of the KAK decomposition. The other subgroup
# is induced by the so-called (horizontal) Cartan subalgebra :math:`\mathfrak{h}`. This is a maximal Abelian subalgebra of :math:`\mathfrak{m}` and is not unique.
# For the case of Pauli words we can simply pick any element in :math:`\mathfrak{m}` and collect all other operators in :math:`\mathfrak{m}`
# that commute with it.
#
# We then obtain a further split of the vector space :math:`\mathfrak{m} = \tilde{\mathfrak{m}} \oplus \mathfrak{h}`,
# where :math:`\tilde{\mathfrak{m}}` is just the remainder of :math:`\mathfrak{m}`.

def _commutes_with_all(candidate, ops):
    r"""Check if ``candidate`` commutes with all ``ops``"""
    for op in ops:
        com = candidate.commutator(op)
        com.simplify()
        
        if not len(com) == 0:
            return False
    return True

def cartan_subalgebra(m, which=0):
    """Compute the Cartan subalgebra from the odd parity space :math:`\mathfrak{m}`
    of the Cartan decomposition

    This implementation is specific for cases of bases of m with pure Pauli words as
    detailed in Appendix C in `2104.00728 <https://arxiv.org/abs/2104.00728>`__.
    
    Args:
        m (List[PauliSentence]): the odd parity subspace :math:`\Theta(x) = -x
        which (int): Choice for initial element of m from which to construct 
            the maximal Abelian subalgebra
    
    Returns:
        mtilde (List): remaining elements of :math:`\mathfrak{m}`
            s.t. :math:`\mathfrak{m} = \tilde{\mathfrak{m}} \oplus \mathfrak{h}`.
        h (List): Cartan subalgebra :math:`\mathfrak{h}`.

    """

    h = [m[which]] # first candidate
    mtilde = m.copy()

    for m_i in m:
        if _commutes_with_all(m_i, h):
            if m_i not in h:
                h.append(m_i)
    
    for h_i in h:
        mtilde.remove(h_i)
    
    return mtilde, h

mtilde, h = cartan_subalgebra(m)
len(g), len(k), len(mtilde), len(h)

##############################################################################
# We now have the Cartan decomposition :math:`\mathfrak{g} = \mathfrak{k} \oplus \tilde{\mathfrak{m}} \oplus \mathfrak{h}``
# and with that all the necessary ingredients for the KAK decomposition.
# 
# Variational KhK
# ---------------
#
# Obtaining the actual decomposition is highly non-trivial and there is no canonical way to go about computing it in terms of linear algebra sub-routines.
# In [#Kökcü]_, the authors propose to find the a local extremum of the cost function
# 
# .. math:: f(\theta) = \langle K(\theta) v K(\theta)^\dagger, H\rangle
# 
# where :math:`\langle \cdot, \cdot \rangle` is some inner product (in our case the trace inner product :math:`\langle A, B \rangle = \text{tr}(A^\dagger B)`).
# This construction uses the operator :math:`v = \sum_j \pi^j h_j \in \mathfrak{h}`
# that is such that :math:`e^{i t v}` is dense in :math:`e^{i \mathcal{h}}`.
# The latter means that for any point in :math:`e^{i \mathcal{h}}` there is a :math:`t` such that :math:`e^{i t v}` approximates it.
# Let us construct it.

gammas = [np.pi**i % 2 for i in range(1, len(h)+1)]

v = qml.dot(gammas, h)
v_m = qml.matrix(v, wire_order=range(n_wires))
v_m = jnp.array(v_m)


##############################################################################
# 
# This procedure has the advantage that we can use an already decomposed ansatz
# 
# .. math:: K(\theta) = \prod_j e^{-i \theta_j k_j}
# 
# for the vertical unitary.
# 
# Now we just have to define the cost function and find an extremum.
# In this case we are going to use gradient descent to minimize the cost function to a minimum.
# We are going to use ``jax`` and ``optax`` and write some boilerplate for the optimization procedure.

def run_opt(
    value_and_grad,
    theta,
    n_epochs=500,
    lr=0.1,
):
    """Boilerplate jax optimization"""
    value_and_grad = jax.jit(jax.value_and_grad(loss))
    optimizer = optax.lbfgs(learning_rate=lr, memory_size=100)
    opt_state = optimizer.init(theta)

    energy = []
    gradients = []
    thetas = []

    @jax.jit
    def step(opt_state, theta):
        val, grad_circuit = value_and_grad(theta)
        updates, opt_state = optimizer.update(
            grad_circuit, opt_state, theta, value=val, grad=grad_circuit, value_fn=loss
        )
        theta = optax.apply_updates(theta, updates)

        return opt_state, theta, val

    t0 = datetime.now()
    ## Optimization loop
    for _ in range(n_epochs):
        opt_state, theta, val = step(opt_state, theta)

        energy.append(val)
        thetas.append(theta)
        
    t1 = datetime.now()
    print(f"final loss: {val}; min loss: {np.min(energy)}; after {t1 - t0}")

    return thetas, energy, gradients


##############################################################################
# We can now implement the cost function and find a minimum via gradient descent.

H_m = qml.matrix(H, wire_order=range(n_wires))
H_m = jnp.array(H_m)

def K(theta, k):
    for th, k_j in zip(theta, k):
        qml.exp(-1j * th * k_j.operation())

@jax.jit
def loss(theta):
    K_m = qml.matrix(K, wire_order=range(n_wires))(theta, k)
    A = K_m @ v_m @ K_m.conj().T
    return jnp.trace(A.conj().T @ H_m).real

theta0 = jnp.ones(len(k), dtype=float)

thetas, energy, _ = run_opt(loss, theta0, n_epochs=600, lr=0.05)
plt.plot(energy - np.min(energy))
plt.xlabel("epochs")
plt.ylabel("cost")
plt.yscale("log")
plt.show()


##############################################################################
# This gives us the optimal values of the parameters :math:`\theta_\text{opt}` of :math:`K(\theta_\text{opt}) =: K_c`.

theta_opt = thetas[-1]
Kc_m = qml.matrix(K, wire_order=range(n_wires))(theta_opt, k)

##############################################################################
# The special element :math:`h_0` from the Cartan subalgebra :math:`\mathfrak{h}` is given by
# rotating the Hamiltonian by the critical :math:`K_c`.
# 
# .. math:: h_0 = K_c H K_c^\dagger.

h_0_m = Kc_m.conj().T @ H_m @ Kc_m
h_0 = qml.pauli_decompose(h_0_m)

print(len(h_0))

# assure that h_0 is in \mathfrak{h}
h_vspace = qml.pauli.PauliVSpace(h)
not h_vspace.is_independent(h_0.pauli_rep)

##############################################################################
#
# This gives us the KhK decomposition of :math:`H`,
# 
# .. math:: H = K_c^\dagger h_0 K_c
# 
# This trivially reproduces the original Hamiltonian.
#

H_re = Kc_m @ h_0_m @ Kc_m.conj().T
np.allclose(H_re, H_m)

##############################################################################
# We can now check if the Hamiltonian evolution is reproduced correctly.
#

t = 1.
U_exact = qml.exp(-1j * t * H)
U_exact_m = qml.matrix(U_exact, wire_order=range(n_wires))

def U_kak(theta_opt, t):
    qml.adjoint(K)(theta_opt, k)
    qml.exp(-1j * t * h_0)
    K(theta_opt, k)

U_kak_m = qml.matrix(U_kak, wire_order=range(n_wires))(theta_opt, t)

def trace_distance(A, B):
    return 1 - np.abs(np.trace(A.conj().T @ B))/len(A)

trace_distance(U_exact_m, U_kak_m)





##############################################################################
# Indeed we find that the KAK decomposition that we found reproduces the unitary evolution operator.
# Note that this is valid for arbitrary :math:`t`, such that the Hamiltonian simulation operator has a fixed depth.

##############################################################################
# Time evolutions
# ---------------
# 
# We compute multiple time evolutions for different times and compare Suzuki-Trotter product with the KAK decomposition circuit.
#

ts = jnp.linspace(1., 5., 10)

Us_exact = jax.vmap(lambda t: qml.matrix(qml.exp(-1j * t * H), wire_order=range(n_wires)))(ts)

def Us_kak(t):
    return Kc_m @ jax.scipy.linalg.expm(-1j * t * h_0_m) @ Kc_m.conj().T

Us_kak = jax.vmap(Us_kak)(ts)
Us_trotter5 = jax.vmap(lambda t: qml.matrix(qml.TrotterProduct(H, time=-t, n=5, order=4), wire_order=range(n_wires)))(ts)
Us_trotter50 = jax.vmap(lambda t: qml.matrix(qml.TrotterProduct(H, time=-t, n=50, order=4), wire_order=range(n_wires)))(ts)

def compute_res(Us):
    # vectorized trace inner product
    res = jnp.abs(jnp.einsum("bij,bji->b", Us_exact.conj(), Us))
    res /= 2**n_wires
    return 1 - res

res_kak = compute_res(Us_kak)
res_trotter5 = compute_res(Us_trotter5)
res_trotter50 = compute_res(Us_trotter50)

plt.plot(ts, res_kak+1e-15, label="KAK") # displace by machine precision to see it still in plot
plt.plot(ts, res_trotter5, "x--", label="5 Trotter steps")
plt.plot(ts, res_trotter50, ".-", label="50 Trotter steps")
plt.ylabel("empirical error")
plt.xlabel("t")
plt.yscale("log")
plt.legend()
plt.show()


##############################################################################
# We see the expected behavior of Suzuki-Trotter product formulas getting worse with increase of time
# while the KAK error is constant zero.
#
# The KAK decomposition is particularly well-suited for smaller systems as the circuit depth is equal to the
# dimension of the subspaces, in particular :math:`2 |\mathfrak{k}| + |\mathfrak{h}|`. Note, however,
# that these dimensions typically scale exponentially in the system size.
#


##############################################################################
# 
# Conclusion
# ----------
# 
# The KAK theorem is a very general mathematical result with far-reaching consequences.
# While there is no canonical way of obtaining an actual decomposition in practice, we followed
# the approach of [#Kökcü]_ that uses a specifically designed loss function and variational
# optimization to find the decomposition.
# This approach has the advantage that the resulting decomposition is itself already decomposed in terms of rotation gates in the original Lie algebra,
# as opposed to other methods such as [#Chu]_ that find :math:`K` as a whole.
# We provided a flexible pipeline that lets users find KAK decompositions in PennyLane for systems with small 
# DLA and specifically decomposed the Heisenberg model Hamiltonian with :math:`n=4` qubits that has a DLA of dimension :math:`60` (:math:`\left(\mathfrak{s u}(2^{n-2})\right)^{\oplus 4}`).
#



##############################################################################
# 
# References
# ----------
#
# .. [#Kökcü]
#
#     Efekan Kökcü, Thomas Steckmann, Yan Wang, J. K. Freericks, Eugene F. Dumitrescu, Alexander F. Kemper
#     "Fixed Depth Hamiltonian Simulation via Cartan Decomposition"
#     `arXiv:2104.00728 <https://arxiv.org/abs/2104.00728>`__, 2021.
#
# .. [#Chu]
#
#     Moody T. Chu
#     "Lax dynamics for Cartan decomposition with applications to Hamiltonian simulation"
#     `doi:10.1093/imanum/drad018 <https://doi.org/10.1093/imanum/drad018>`__, `preprint PDF <https://mtchu.math.ncsu.edu/Research/Papers/Cartan_02.pdf>`__ 2024.
#
#

##############################################################################
# About the author
# ----------------
# .. include:: ../_static/authors/korbinian_kottmann.txt