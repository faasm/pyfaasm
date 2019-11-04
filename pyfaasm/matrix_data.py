import numpy as np

from pyfaasm.config import MatrixConf, get_submatrix_byte_offset


def subdivide_matrix_into_file(mat, file_path):
    all_bytes = do_subdivide_matrix(mat)

    with open(file_path, "wb") as fh:
        fh.write(all_bytes)


def do_subdivide_matrix(mat):
    # Step through rows and columns of original matrix, appending submatrix bytes
    # to the overall byte stream
    all_bytes = b''
    for row_idx in range(0, MatrixConf.submatrices_per_row):
        for col_idx in range(0, MatrixConf.submatrices_per_row):
            # Work out the position of the top left and bottom right corner of the submatrix
            row_start = row_idx * MatrixConf.submatrix_size
            col_start = col_idx * MatrixConf.submatrix_size

            row_end = row_start + MatrixConf.submatrix_size
            col_end = col_start + MatrixConf.submatrix_size

            # Extract the submatrix and write to bytes
            sub_mat = mat[row_start:row_end, col_start:col_end]
            all_bytes += sub_mat.tobytes()

    return all_bytes


def reconstruct_matrix_from_file(file_path):
    with open(file_path, "rb") as fh:
        all_bytes = fh.read()

    return do_reconstruct_matrix(all_bytes)


def do_reconstruct_matrix(all_bytes):
    result = None

    # Need to read in row by row concatenate the rows
    for row_idx in range(0, MatrixConf.submatrices_per_row):
        submatrices = []
        for col_idx in range(0, MatrixConf.submatrices_per_row):
            byte_idx = get_submatrix_byte_offset(row_idx, col_idx)
            this_submat = np.frombuffer(all_bytes[byte_idx: byte_idx + MatrixConf.bytes_per_submatrix])
            this_submat = this_submat.reshape(MatrixConf.submatrix_size, MatrixConf.submatrix_size)
            submatrices.append(this_submat)

        this_row = np.concatenate(submatrices, axis=1)

        if row_idx == 0:
            # Initialise the result
            result = this_row
        else:
            # Add the row to the existing result
            result = np.concatenate((result, this_row), axis=0)

    return result
