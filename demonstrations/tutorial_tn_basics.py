r"""Tutorial: ABC of tensor networks
=============================================================

Intro:
- introduce where are tensor networks used (physics, math, machine learning), why are they so widely spread, and mention how they are not just a data structure but also a diagrammatic language for formal reasoning and even proofs!
- Define the scope of this tutorial: basics of tensor networks, their relation to quantum circuits, and the importance of choosing the contraction paths.

From matrices to tensors
^^^^^^^^^^^^^^^^^^^^^^^^^^^

A common and intuitive way of thinking about tensors is as generalizations of vectors and matrices. That is, we can think of them as multi dimensional arrays - i.e., multi dimensional maps that are linear with respect to every parameter.
A tensor of dimensions :math:`d_1 \times d_2 \times \ldots \times d_r` can be expressed as

.. math::
    T_{i_1, i_2, \ldots, i_r} \in \mathbb{C}^{d_1 \times d_2 \times \ldots \times d_r}.
    
Where each :math:`i_n` is an *index* of dimension :math:`d_n` - it can take values ranging from :math:`1` to :math:`d_n`-, and the number of indices :math:`r` is known as the *rank* of the tensor. We say :math:`T` is a rank-r tensor.

.. tip::
    Some authors refer to the indices of the tensors as their dimensions. In this tutorial, these two concepts will have have different meanings, although related.

For example, a scalar :math:`s` is a rank-0 tensor, a vector :math:`v_i` is a rank-1 tensor and a matrix :math:`G_{i,j}` is a rank-2 tensor.
    
A beautiful and powerful tool accompanying tensors (networks) is their graphical language representation. The diagram of a tensor is simply a geometric shape with a leg sticking out of it for every index in the tensor. For example,

TODO: add diagram here as the second part of the equation.

.. math::
    T_{i,j,k,l} = 

We can apply this same idea to represent a scalar, a vector and a matrix:

TODO: add diagrams here.

.. math::
    s = 
    
.. math::
    v_i =
    
.. math::
    G_{i,j} =  

Does the last diagram seem familiar? It is because this is the representation of a single-qubit gate! We will see later in this tutorial the relation between quantum circuits and tensor networks. 

Some authors choose to give the shape of the tensor an additional meaning. For example, you might encounter square tensors representing symmetric matrices, to represent its invariance under transposition.

TODO: add diagram here showing: 1. Square matrix 2. Bending of wires as transpose 3. Final matrix

In addition, an isometry :math:`V \in \mathbb{C}^{n \times p}` - i.e., a rectangular matrix such that :math:`V V^\dagger = I_p` but :math:`V^\dagger V \neq I_n` - with :math:`n > p`  can be depicted using a triangle to emphasize the isometry property:

TODO: add diagram here showing the isometry definition (identity from the smaller space to the bigger space). See https://www.math3ma.com/blog/matrices-as-tensor-network-diagrams

For quantum states, it is often useful to adopt the convention that writing the legs towards one direction (e.g. the right) corresponds to a ket, i.e., a vector living in the Hilbert space, while drawing the legs to the opposite direction (e.g. left) means they are a bra vector, i.e., living in the dual space.

TODO: 1) drawing of a vector with legs towards right diretion (ket) 2) legs towards left (bra)

TODO: add reference here for category theory. P. Selinger. A survey of graphical languages for monoidal categories. Lecture Notes
in Physics, page 289–355, 2010.

.. tip::
    The diagrammatic representation of tensors is rooted in category theory, which equips the diagrams with all the relevant information so they can used in proofs and formal reasoning!

Creating a tensor in code is straightforward, and chances are you have already created one yourself. Using ``Numpy``, all we have to do is to create a ``np.array`` of the desired rank. For instance, we can start crearting a rank-1 tensor (a vector).
"""

import numpy as np

tensor_rank1 = np.array([1, 2, 3])
print("rank: ", tensor_rank1.ndim)
print("dimensions: ", tensor_rank1.shape)

##############################################################################
# Then, we can use this to constructor a rank-2 tensor (a matrix).

tensor_rank2 = np.array([tensor_rank1, tensor_rank1])
print("rank: ", tensor_rank2.ndim)
print("dimensions: ", tensor_rank2.shape)

##############################################################################
# As you might have guessed, we can repeat this procedure to create a rank-3 tensor.

tensor_rank3 = np.array([tensor_rank2])
print("rank: ", tensor_rank3.ndim)
print("dimensions: ", tensor_rank3.shape)
print("Rank-3 tensor: \n", tensor_rank3)
##############################################################################
# Similarly, we can create a tensor of arbitrary rank following a similar procedure. This recursive approach is instructive to understand a rank-r tensor as made up of rank-(r-1) tensors, which translates to the code as adding an additional level in the nested bracket structure ``[tensor_rank_r-1]``.

##############################################################################
# From matrix multiplication to tensor contractions
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# Matrix-matrix and matrix-vector multiplications are familiar operations within the context of quantum computing. We can now study these operations under the lens of the tensor notation introduced above. First, a matrix and a vector can be multiplied as
#
# TODO: add diagram at the end of the equation.
#
# .. math::
#     (w)_i = G \cdot v = \sum_j G_ij v_j =
#
# We see that summing over the shared index :math:`j` is equivalent to **contracting** the corresponding legs from the matrix and vector diagrams. As expected, the result of this multiplication is another rank-1 tensor with dangling leg :math:`i`. Similarly, we can look at the matrix-matrix multiplication:
#
# TODO: add diagram at the end of the equation.
#
# .. math::
#     (G^3)_{j,k} = G^1 \cdot G^2 = \sum_j G^{1}_{i,j} G^{2}_{j,k} =
#
# In this case, the resulting tensor has two dangling indices, :math:`i` and :math:`k`, which defines a matrix, as expected!
#
# We can now generalize this concept to tensors, and consequently, to more than a pair of legs being contracted. For example, let us look at three tensors :math:`A_{i,j,k}`, :math:`B_{j,l,m}` and :math:`C_{k,m,n}`. To contract them, all we need to do is to sum over repeated indices (:math:`j`, :math:`k`, :math:`m`), just as we would do in Einstein convention. Thus, the (i,l,n)-th element of the resulting tensor :math:`D` is
#
# .. math::
#     (D)_{i,l,n} = \sum_{j,k,m} `A_{i,j,k} B_{j,l,m} C_{k,m,n} .
#
# Note how the resulting rank-3 tensor is made up of the open legs from all the initial tensors (i,l,n). The diagrammatic representation of this equation is obtained by sticking all the legs with the same indices together.
#
# TODO: add figure here.
#
# With the above contraction we have formed a network of tensors, i.e. a **Tensor Network**!
#
# .. tip::
#   A common question arising when drawing a tensor is "what is the correct order to draw the indices". For instance, in the figure above we have adopted the convention that a tensor :math:`A_{i,j,k}` corresponds to a diagram with the the first leg (i) pointing left, the second leg (j) pointing upwards and the third leg (k) pointing right, and similarly for the other two tensors. However, this need not be the case. We could have defined the first leg to be the one pointing upwards, for example. Based on the use case, and the user, some conventions might seem more natural than others. The only important thing to keep in mind is to be consistent. In other words, once we choose a convetion for the order, we should apply it to all the tensors to avoid contracting the wrong indices ❌.
#
# Remember we pointed out the similarity in the notation for the tensor network contractions? Then it doesn't come as a suprise that we can perform a contraction using the function ``np.einsum``. We start creating the 3 tensors in the network by reshaping a 1D array (coming from ``np.arange``) into rank-3 tensors of the right dimensions.

# Create the individual rank-3 tensors
A = np.arange(6).reshape(1, 2, 3)  # ijk
B = np.arange(6).reshape(2, 3, 1)  # jlm
C = np.arange(6).reshape(3, 1, 2)  # kmn

D = np.einsum("ijk, jlm, kmn -> iln", A, B, C)
print(D.shape)

# The ``np.einsum`` takes as inputs the tensors to be contracted and a string showing the indices of the each tensor and (optionally) the indices of the output tensor.
"""

The cost of contracting a network (bubbling):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Mention that the resulting tensor network doesn't change but the way we arrive to the final tensor affects how expensive it is to get there.
- Show how can we can calculate the complexity of a contraction by means of a simple example using 2 matrices (rank 2 tensors): dimension_contracted x (dimensions_open).
    Intuition behind: we perform one operation (contraction) and repeat many times to "populate" the resulting tensor (dimension_open1 x dimension_open2). Show the equation with indices.
- Show an example with at least three tensors where they all have different dimensions. Walk through it showing that choosing to contract two indices (the ones with lower dimensions) results in a worst computational complexity than contracting other ones (the ones with higher dimensions).
- For this reason there exist heuristics for optimizing contraction path complexity. NP problem -> no perfect solution but great heuristics (https://arxiv.org/pdf/2002.01935).
    (optional) mention the idea behind some of them 
    Link to quimb examples.
- CODE: show this using np.einsum, timeit, and very large dimensions expecting to see a difference.

From tensor networks to quantum circuits:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Quantum circuits are a restricted subclass of tensor networks
- show examples on https://arxiv.org/pdf/1912.10049 page 8 and 9 showing a quantum circuit for a bell state, defining each component as a tensor and show their contraction.
- What else?
"""

"""
DRAFT:

1) 
- Definition of a tensor as an n-dimensional array. Show notation with n indices, stating that it belongs to C^{d1,...,dn}. Define rank, index, dimension (mention how these terms are sometimes used (wrongly?) interchangeably in literature).
- Graphical notation. Mention that there exist certain representations in the literature that allow to represent properties of the tensors (e.g. symmetry, orthogonality). In our case, we can adhere to a general circle.
- Specific examples used in a day-to-day: scalars, vectors, matrices. Mention that for quantum states, we can adopt the convention that the legs in one direction mean that the state belongs to one Hilbert space, and the legs to the other side to the dual space.
- CODE: include code using numpy creating a >2 dimensional array.

2)

- Show the matrix multiplication in terms of summation over indices, then using the diagrammatic representation. This results in another rank 2 tensor (matrix)
- Analagously, we can represent matrix-vector multiplication resulting in a rank 1 tensor (vector). Just as we expected!
- We can generalize this concept to tensors. This is done by summing over repeated indices (just as in einstein convention - external link for it) resulting in another tensor made up of the open legs of all the tensors together.
    In diagrammatic notation, this is simply sticking together legs with same indices! (show nice diagram with >3 tensors). We have just formed a network of tensors, i.e. a Tensor Network!
- CODE: Talking about einstein convetion, we can perform this contraction of tensors using `np.einsum`.
"""