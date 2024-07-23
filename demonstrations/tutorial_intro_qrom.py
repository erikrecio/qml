r"""Intro to QROM
=============================================================

Managing data is a crucial task on any computer, and quantum computers are no exception. Efficient data management is vital in quantum machine learning, search algorithms, and state preparation.
In this demonstration, we will discuss the concept of a Quantum Read-Only Memory (QROM), a data structure designed to load classical data on a quantum computer.
You will also see how easy it is to use this operator in PennyLane through the :class:`~.pennylane.QROM` template.


.. figure:: ../_static/demonstration_assets/qrom/qrom_opengraph.png
    :align: center
    :width: 50%
    :target: javascript:void(0)

QROM
-----

The QROM is an operator that allows us to load classical data into a quantum computer. Data is represented as a collection of bitstrings (list of 0s and 1s) that we denote by :math:`b_0, b_2, \ldots, b_{N-1}`. The QROM operator is then defined as:

.. math::

    \text{QROM}|i\rangle|0^{\otimes m}\rangle = |i\rangle|b_i\rangle,

where :math:`|b_i\rangle` is the bitstring associated with the :math:`i`-th computational basis and :math:`m` is the length of the bitstrings. We have assumed all the bistrings are of equal length.

For example, suppose our data consists of eight bitstrings, each with two bits: :math:`[01, 11, 11, 00, 01, 11, 11, 00]`. Then, the index register will consist of three
qubits (:math:`3 = \log_2 8`) and the target register of two qubits (e.g., :math:`m = 2`). For instance, for the
first four indices, the QROM operator acts as:

.. math::
     \begin{align}
     \text{QROM}|000\rangle|00\rangle &= |000\rangle|01\rangle \\
     \text{QROM}|001\rangle|00\rangle &= |001\rangle|11\rangle \\
     \text{QROM}|010\rangle|00\rangle &= |010\rangle|11\rangle \\
     \text{QROM}|011\rangle|00\rangle &= |011\rangle|00\rangle
     \end{align}

We will now explain three different implementations of QROM: Select, SelectSwap, and an extension of SelectSwap.

Select
~~~~~~~

:class:`~.pennylane.Select` is an operator that prepares quantum states associated with indices. It is defined as:

.. math::

    \text{Select}|i\rangle|0\rangle = |i\rangle U_i|0\rangle =|i\rangle|\phi_i\rangle,

where :math:`|\phi_i\rangle` is the :math:`i`-th state we want to encode, generated by a known unitary :math:`U_i`.
QROM can be considered a special case of the Select operator where the encoded states are computational basis states.
Then the unitaries :math:`U_i` can be simply :math:`X` gates that determine whether each bit is a :math:`0` or a :math:`1` satisfying:

.. math::

    U_i|0\rangle =|b_i\rangle.

We use :class:`~.pennylane.BasisEmbedding` as a useful template for preparing bitstrings, it places the :math:`X` gates
in the right position. Let's see how it could be implemented:

"""

import pennylane as qml
from functools import partial
import matplotlib.pyplot as plt


bitstrings = ["01", "11", "11", "00", "01", "11", "11", "00"]

control_wires = [0,1,2]
target_wires = [3,4]

Ui = [qml.BasisEmbedding(int(bitstring, 2), target_wires) for bitstring in bitstrings]

dev = qml.device("default.qubit", shots = 1)

# This line is included for drawing purposes only.
@partial(qml.devices.preprocess.decompose,
         stopping_condition = lambda obj: False,
         max_expansion=1)

@qml.qnode(dev)
def circuit(index):
    qml.BasisEmbedding(index, wires=control_wires)
    qml.Select(Ui, control=control_wires)
    return qml.sample(wires=target_wires)

qml.draw_mpl(circuit, style = "pennylane")(3)
plt.show()

##############################################################################
# In this example we are applying Select to index :math:`3`, so we encode the state :math:`|3\rangle = |011\rangle`
# with two :math:`X` gates.
# Now we can check that all the outputs are as expected:

for i in range(8):
    print(f"The bitstring stored in index {i} is: {circuit(i)}")


##############################################################################
# Nice, the outputs match the elements of our initial data list: :math:`[01, 11, 11, 00, 01, 11, 11, 00]`.
#
# The :class:`~.pennylane.QROM` template can be used to implement the previous circuit using directly the bitstring
# without having to calculate the :math:`U_i` gates:

bitstrings = ["01", "11", "11", "00", "01", "11", "11", "00"]

control_wires = [0,1,2]
target_wires = [3,4]

@qml.qnode(dev)
def circuit(index):
    qml.BasisEmbedding(index, wires=control_wires)
    qml.QROM(bitstrings, control_wires, target_wires, work_wires = None)
    return qml.sample(wires=target_wires)

##############################################################################
# Although this approach works correctly, the number of multicontrol gates is high.
# The decomposition of these gates is expensive and there are numerous works that attempt to simplify this.
# We highlight reference [#unary]_ which introduces an efficient technique using measurements in the middle
# of the circuit. Another clever approach was introduced in [#selectSwap]_ , with a smart structure known as SelectSwap,
# which we describe below.
#
# SelectSwap
# ~~~~~~~~~~
# The goal of the SelectSwap construction is to trade depth for width. That is, using multiple auxiliary qubits,
# we reduce the circuit depth required to build the QROM. To apply it, we just have to add ``work_wires`` to
# the template and PennyLane will do all the work for you automatically:
#

bitstrings = ["01", "11", "11", "00", "01", "11", "11", "00"]

control_wires = [0,1,2]
target_wires = [3,4]
work_wires = [5,6]

@qml.qnode(dev)
def circuit(index):
    qml.BasisEmbedding(index, wires=control_wires)
    qml.QROM(bitstrings, control_wires, target_wires, work_wires, clean = False)
    return qml.sample(wires=control_wires + target_wires + work_wires)


##############################################################################
# Internally, the main idea of this approach is to organize the :math:`U_i` operators in two dimensions,
# whose positions will be determined by a column index :math:`c` and a row index :math:`r`.
#
# .. figure:: ../_static/demonstration_assets/qrom/select_swap.jpeg
#    :align: center
#    :width: 70%
#    :target: javascript:void(0)
#
# The circuit is divided into two fundamental parts:
#
# - **Select block**:  works the same as before, but now it loads more than one bitstring per column. The control wires associated to this operator encode the column :math:`c` to be applied.
# - **Swap block**:  swaps the :math:`r`-row to the target wires where the :math:`r` value is encoded in the control wires associated with this operator.
#
#
# Let's look at an example by assuming we want to load in the target wires the bitstring with
# the index :math:`5`, i.e. :math:`b_5 = 11`.
# For it, we put as input in the control wires the state :math:`|101\rangle` (5 in binary). Then, the initial state is :math:`|101\rangle|00\rangle|00\rangle`,
# where the first two qubits store the index :math:`|c\rangle = |10\rangle` and the third qubit store to the index :math:`|r\rangle = |1\rangle`.
#
# The first operator we have to apply is the Select block, which loads the column :math:`c`, generating the state  :math:`|101\rangle U_4|00\rangle U_5|00\rangle = |101\rangle |01\rangle |11\rangle`,
# where :math:`01` and :math:`11` are the bitstrings :math:`b_4` and :math:`b_5`, respectively.
# After that we have to apply the Swap block. Since the third
# control qubit is a :math:`|r\rangle = |1\rangle`, we swap the row :math:`1` with the target wires, getting the state :math:`|101\rangle U_5 |00\rangle U_4|00\rangle = |101\rangle|11\rangle|01\rangle`
# loading the bitstring :math:`b_5 = 11` in the target register.

index = 5
output = circuit(index)
print(f"control wires: {output[:3]}")
print(f"target wires: {output[3:5]}")
print(f"work wires: {output[5:7]}")


##############################################################################
#
# Note that with more auxiliary qubits we could make larger groupings of bitstrings reducing the depth of the
# Select operator. Below we show an example with two columns and four rows:
#
# .. figure:: ../_static/demonstration_assets/qrom/select_swap_4.jpeg
#    :align: center
#    :width: 70%
#    :target: javascript:void(0)
#
# The QROM template will put as many rows as possible using the ``work_wires`` we pass.
#
#
# Reusable qubits
# ~~~~~~~~~~~~~~~~ 
#
# The above approach has a drawback. The work wires have been altered, i.e., after applying the operator they have not
# been returned to state :math:`|00\rangle`. This can cause unwanted behaviors but in PennyLane can be easily solved
# by setting the parameter ``clean = True``.


bitstrings = ["01", "11", "11", "00", "01", "11", "11", "00"]

control_wires = [0, 1, 2]
target_wires = [3, 4]
work_wires = [5, 6]


@qml.qnode(dev)
def circuit(index):
    qml.BasisEmbedding(index, wires=control_wires)
    qml.QROM(bitstrings, control_wires, target_wires, work_wires, clean=True)
    return qml.sample(wires=target_wires + work_wires)

for i in range(8):
    print(f"The bitstring stored in index {i} is: {circuit(i)[:2]}")
    print(f"The work wires for that index are in the state: {circuit(i)[2:4]}\n")


##############################################################################
# Great! To achieve this, we have followed the technique shown in [#cleanQROM]_ where the proposed circuit is as follows:
#
# .. figure:: ../_static/demonstration_assets/qrom/clean_version_2.jpeg
#    :align: center
#    :width: 90%
#    :target: javascript:void(0)
#
# where :math:`R` the number of rows. To see how this circuit works, let's suppose we want to load the bitstring :math:`b_{cr}` in the target wires, where :math:`b_{cr}`
# is the bitstring whose operator :math:`U` is placed in the c-th column and r-th row in the two dimensional representation shown in the Select block.
#
# We can summarize the idea in a few simple steps:
#
# 1. **A uniform superposition is created in the r-th register of the work wires**. To do this, we put the Hadamards in the target wires and move it to the :math:`r` -row with the Swap block.
#
# .. math::
#       |c\rangle |r\rangle |0\rangle |0\rangle \dots |+\rangle_r \dots |0\rangle.
#
# 2. **Select block is applied.** Note that in the :math:`r`-th position, the Select has no effect since the state :math:`|+\rangle` is not modified by :math:`X` gates.
#
# .. math::
#       |c\rangle |r\rangle |b_{c0}\rangle |b_{c1}\rangle \dots |+\rangle_r \dots |b_{c(R-1)}\rangle.
#
#
# 3. **The Hadamard gate is applied to the r-th register of the work wires.** The two Swap blocks and the Hadamard gate applied to the target wires achieve this.
#
# .. math::
#       |c\rangle |r\rangle |b_{c0}\rangle |b_{c1}\rangle \dots |0\rangle_r \dots |b_{c(R-1)}\rangle.
#
# 4. **Select block is applied.** Note that loading the bitstring twice in the same register leaves the state as :math:`|0\rangle`. (:math:`X^2 = \mathbb{I}`)
#
# .. math::
#       |c\rangle |r\rangle |0\rangle |0\rangle \dots |b_{cr}\rangle_r \dots |0\rangle.
#
# 5. **Swap block is applied.** With this, we move :math:`b_{cr}` that is encoded in the :math:`r`-row to the target wires.
#
# .. math::
#       |c\rangle |r\rangle |b_{cr}\rangle |0\rangle \dots |0\rangle_r \dots |0\rangle.
#
#
# Conclusion
# ----------
#
# By implementing various versions of the QROM operator, such as Select and SelectSwap, we optimize quantum circuits
# for enhanced performance and scalability. These methods improve the efficiency of
# state preparation [#StatePrep]_ techniques by reducing the number of required gates, which we recommend you explore.
# As the availability of qubits increases, the relevance of these methods will grow making this operator an
# indispensable tool for developing new algorithms and an interesting field for further study.
#
# References
# ----------
#
# .. [#unary]
#
#       Ryan Babbush, Craig Gidney, Dominic W. Berry, Nathan Wiebe, Jarrod McClean, Alexandru Paler, Austin Fowler, and Hartmut Neven,
#       "Encoding Electronic Spectra in Quantum Circuits with Linear T Complexity,"
#       `Physical Review X, 8(4), 041015 (2018). <http://dx.doi.org/10.1103/PhysRevX.8.041015>`__, 2018
#
# .. [#selectSwap]
#
#       Guang Hao Low, Vadym Kliuchnikov, and Luke Schaeffer,
#       "Trading T-gates for dirty qubits in state preparation and unitary synthesis",
#       `arXiv:1812.00954 <https://arxiv.org/abs/1812.00954>`__, 2018
#
# .. [#cleanQROM]
#
#       Dominic W. Berry, Craig Gidney, Mario Motta, Jarrod R. McClean, and Ryan Babbush,
#       "Qubitization of Arbitrary Basis Quantum Chemistry Leveraging Sparsity and Low Rank Factorization",
#       `Quantum 3, 208 <http://dx.doi.org/10.22331/q-2019-12-02-208>`__, 2019
#
# .. [#StatePrep]
#
#       Lov Grover and Terry Rudolph,
#       "Creating superpositions that correspond to efficiently integrable probability distributions",
#       `arXiv:quant-ph/0208112 <https://arxiv.org/abs/quant-ph/0208112>`__, 2002
#
# About the author
# ----------------
