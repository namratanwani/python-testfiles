import math
from typing import List, Tuple


def default_matrix_multiplication(a: List, b: List) -> List:
    """
    Computes the multiplication of two 2x2 matrices by creating a new matrix with
    the dot product of corresponding elements.

    Args:
        a (List): 2-dimensional matrix to be multiplied with another 2-dimensional
            matrix.
        b (List): 2x2 matrix that is multiplied with the 2-dimensional list `a`.

    Returns:
        List: a list of two lists, where each sublist represents the result of
        multiplying two 2x2 matrices.

    """
    if len(a) != 2 or len(a[0]) != 2 or len(b) != 2 or len(b[0]) != 2:
        raise Exception("Matrices are not 2x2")
    new_matrix = [
        [a[0][0] * b[0][0] + a[0][1] * b[1][0], a[0][0] * b[0][1] + a[0][1] * b[1][1]],
        [a[1][0] * b[0][0] + a[1][1] * b[1][0], a[1][0] * b[0][1] + a[1][1] * b[1][1]],
    ]
    return new_matrix


def matrix_addition(matrix_a: List, matrix_b: List):
    """
    Takes two lists of lists, matrix A and B, and returns a new list of lists by
    adding corresponding elements of each matrix and storing the result in a new
    list.

    Args:
        matrix_a (List): 2D array to be added with another 2D array, `matrix_b`,
            element-wise.
        matrix_b (List): 2nd matrix to be added to the first matrix in the function.

    Returns:
        list: a list of lists, where each inner list represents the sum of the
        corresponding elements of two input matrices.

    """
    return [
        [matrix_a[row][col] + matrix_b[row][col] for col in range(len(matrix_a[row]))]
        for row in range(len(matrix_a))
    ]


def matrix_subtraction(matrix_a: List, matrix_b: List):
    """
    Takes two list arguments, `matrix_a` and `matrix_b`, and returns a new list
    containing the difference between corresponding elements of the two input matrices.

    Args:
        matrix_a (List): 2D array that is subtracted from another 2D array represented
            by `matrix_b`.
        matrix_b (List): 2nd matrix that is being subtracted from the 1st matrix,
            `matrix_a`.

    Returns:
        list: a list of lists, where each sub-list represents the difference between
        the corresponding elements of two input matrices.

    """
    return [
        [matrix_a[row][col] - matrix_b[row][col] for col in range(len(matrix_a[row]))]
        for row in range(len(matrix_a))
    ]


def split_matrix(
    a: List,
) -> Tuple[List, List, List, List]:
    """
    Splits a given matrix into four smaller matrices along the diagonal and
    horizontal lines, such that each smaller matrix has the same size as the
    original matrix.

    Args:
        a (List): 2D matrix to be split into four sub-matrices.

    Returns:
        Tuple[List, List, List, List]: a tuple of four lists, each representing a
        quarter of the input matrix.

    """
    if len(a) % 2 != 0 or len(a[0]) % 2 != 0:
        raise Exception("Odd matrices are not supported!")

    matrix_length = len(a)
    mid = matrix_length // 2

    top_right = [[a[i][j] for j in range(mid, matrix_length)] for i in range(mid)]
    bot_right = [
        [a[i][j] for j in range(mid, matrix_length)] for i in range(mid, matrix_length)
    ]

    top_left = [[a[i][j] for j in range(mid)] for i in range(mid)]
    bot_left = [[a[i][j] for j in range(mid)] for i in range(mid, matrix_length)]

    return top_left, top_right, bot_left, bot_right


def matrix_dimensions(matrix: List) -> Tuple[int, int]:
    return len(matrix), len(matrix[0])


def print_matrix(matrix: List) -> None:
    """
    Prints each element of a given list or matrix using a for loop.

    Args:
        matrix (List): 2D array that will be printed line by line using the `print()`
            function in the `print_matrix()` function.

    """
    for i in range(len(matrix)):
        print(matrix[i])


def actual_strassen(matrix_a: List, matrix_b: List) -> List:
    """
    Takes two lists representing a 2D matrix and multiplies them using Strassen's
    algorithm, yielding a new 2D matrix as output.

    Args:
        matrix_a (List): 2D array to be multiplied with the second argument `matrix_b`.
        matrix_b (List): 2nd matrix to be multiplied with the first matrix `matrix_a`.

    Returns:
        List: a list of numbers representing the result of multiplying two matrices
        using the Strassen algorithm.

    """
    if matrix_dimensions(matrix_a) == (2, 2):
        return default_matrix_multiplication(matrix_a, matrix_b)

    a, b, c, d = split_matrix(matrix_a)
    e, f, g, h = split_matrix(matrix_b)

    t1 = actual_strassen(a, matrix_subtraction(f, h))
    t2 = actual_strassen(matrix_addition(a, b), h)
    t3 = actual_strassen(matrix_addition(c, d), e)
    t4 = actual_strassen(d, matrix_subtraction(g, e))
    t5 = actual_strassen(matrix_addition(a, d), matrix_addition(e, h))
    t6 = actual_strassen(matrix_subtraction(b, d), matrix_addition(g, h))
    t7 = actual_strassen(matrix_subtraction(a, c), matrix_addition(e, f))

    top_left = matrix_addition(matrix_subtraction(matrix_addition(t5, t4), t2), t6)
    top_right = matrix_addition(t1, t2)
    bot_left = matrix_addition(t3, t4)
    bot_right = matrix_subtraction(matrix_subtraction(matrix_addition(t1, t5), t3), t7)

    # construct the new matrix from our 4 quadrants
    new_matrix = []
    for i in range(len(top_right)):
        new_matrix.append(top_left[i] + top_right[i])
    for i in range(len(bot_right)):
        new_matrix.append(bot_left[i] + bot_right[i])
    return new_matrix


def strassen(matrix1: List, matrix2: List) -> List:
    """
    Calculates the result of multiplying two matrices by adding zeros to their
    dimensions so that the arrays have the same dimensions and power of 2, and
    then performing the actual multiplication using a modified Strassen algorithm.

    Args:
        matrix1 (List): 2D matrix to be multiplied with another 2D matrix, provided
            as the `matrix2` input parameter.
        matrix2 (List): 2D array to be multiplied with the first argument `matrix1`.

    Returns:
        List: a list of matrices, where each matrix represents the result of
        multiplying the input matrices using the Strassen algorithm.

    """
    if matrix_dimensions(matrix1)[1] != matrix_dimensions(matrix2)[0]:
        raise Exception(
            f"Unable to multiply these matrices, please check the dimensions. \n"
            f"Matrix A:{matrix1} \nMatrix B:{matrix2}"
        )
    dimension1 = matrix_dimensions(matrix1)
    dimension2 = matrix_dimensions(matrix2)

    if dimension1[0] == dimension1[1] and dimension2[0] == dimension2[1]:
        return matrix1, matrix2

    maximum = max(max(dimension1), max(dimension2))
    maxim = int(math.pow(2, math.ceil(math.log2(maximum))))
    new_matrix1 = matrix1
    new_matrix2 = matrix2

    # Adding zeros to the matrices so that the arrays dimensions are the same and also
    # power of 2
    for i in range(0, maxim):
        if i < dimension1[0]:
            for j in range(dimension1[1], maxim):
                new_matrix1[i].append(0)
        else:
            new_matrix1.append([0] * maxim)
        if i < dimension2[0]:
            for j in range(dimension2[1], maxim):
                new_matrix2[i].append(0)
        else:
            new_matrix2.append([0] * maxim)

    final_matrix = actual_strassen(new_matrix1, new_matrix2)

    # Removing the additional zeros
    for i in range(0, maxim):
        if i < dimension1[0]:
            for j in range(dimension2[1], maxim):
                final_matrix[i].pop()
        else:
            final_matrix.pop()
    return final_matrix
