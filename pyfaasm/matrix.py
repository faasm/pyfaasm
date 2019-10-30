from pyfaasm.core import setState, getState, getStateOffset
import numpy as np

# Work out the item size in a matrix
_temp_mat = np.array([1.1, 2.2], [3.3, 4.4])
NP_ELEMENT_SIZE = _temp_mat.itemsize


def _key(prefix, mat_size):
    return "{}_{}".format(prefix, mat_size)


def write_matrix_to_state(key, mat):
    setState(key, mat.tobytes())


def read_matrix_from_state(key, n):
    byte_len = n * n * NP_ELEMENT_SIZE
    mat_bytes = getState(key, byte_len)
    return np.frombuffer(mat_bytes).reshape(n, n)


def subdivide_matrix_into_state(initial, m):
    n = m.shape[0]
    half_n = n // 2

    # Split the matrix into quadrants
    m_a = m[0:half_n, 0:half_n]
    m_b = m[0:half_n, half_n:n]
    m_c = m[half_n:n, 0:half_n]
    m_d = m[half_n:n, half_n:n]

    # Write the quadrants in a contiguous array to state
    all_bytes = m_a.tobytes() + m_b.tobytes() + m_c.tobytes() + m_d.tobytes()
    k = _key(initial, n)
    setState(k, all_bytes)

    return k


def read_submatrix_from_state(full_key, full_n, submatrix_idx):
    total_len = full_n * full_n * NP_ELEMENT_SIZE

    half_n = full_n // 2
    offset_len = half_n * half_n * NP_ELEMENT_SIZE

    offset = submatrix_idx * half_n

    getStateOffset(full_key, total_len, offset, offset_len)


def _reconstruct_matrix(m_a, m_b, m_c, m_d):
    
    return np.concatenate(
        (
            np.concatenate((m_a, m_b), axis=1),
            np.concatenate((m_c, m_d), axis=1)
        ),
        axis=0
    )


def _dnc_multiply(a_key, b_key, mat_size):
    a = _load_mat(a_key, mat_size)
    b = _load_mat(b_key, mat_size)

    n = a.shape[0]

    # Do naive divide and conquer
    k_aa, k_ab, k_ac, k_ad = _subdivide_matrix("a", a)
    k_ba, k_bb, k_bc, k_bd = _subdivide_matrix("b", b)

    # Keep dividing and conquering down to a limit
    sub_size = mat_size // 2
    if n > 4:
        r_a = _dnc_multiply(k_aa, k_ba, sub_size) + _dnc_multiply(k_ab, k_bc, sub_size)
        r_b = _dnc_multiply(k_aa, k_bb, sub_size) + _dnc_multiply(k_ab, k_bd, sub_size)
        r_c = _dnc_multiply(k_ac, k_ba, sub_size) + _dnc_multiply(k_ad, k_bc, sub_size)
        r_d = _dnc_multiply(k_ac, k_bb, sub_size) + _dnc_multiply(k_ad, k_bd, sub_size)
    else:
        m_aa = _load_mat(k_aa, sub_size)
        m_ab = _load_mat(k_ab, sub_size)
        m_ac = _load_mat(k_ac, sub_size)
        m_ad = _load_mat(k_ad, sub_size)

        m_ba = _load_mat(k_ba, sub_size)
        m_bb = _load_mat(k_bb, sub_size)
        m_bc = _load_mat(k_bc, sub_size)
        m_bd = _load_mat(k_bd, sub_size)

        r_a = np.dot(m_aa, m_ba) + np.dot(m_ab, m_bc)
        r_b = np.dot(m_aa, m_bb) + np.dot(m_ab, m_bd)
        r_c = np.dot(m_ac, m_ba) + np.dot(m_ad, m_bc)
        r_d = np.dot(m_ac, m_bb) + np.dot(m_ad, m_bd)

    return _reconstruct_matrix(r_a, r_b, r_c, r_d)


def main():
    # Note, numpy assumes floats by default
    a = np.array((
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0],
        [17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0],
        [25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0],
        [33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0],
        [41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0],
        [49.0, 50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0],
        [57.0, 58.0, 59.0, 60.0, 61.0, 62.0, 63.0, 64.0],
    ))

    b = np.array((
        [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5],
        [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5],
        [17.5, 18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.5],
        [25.5, 26.5, 27.5, 28.5, 29.5, 30.5, 31.5, 32.5],
        [33.5, 34.5, 35.5, 36.5, 37.5, 38.5, 39.5, 40.5],
        [41.5, 42.5, 43.5, 44.5, 45.5, 46.5, 47.5, 48.5],
        [49.5, 50.5, 51.5, 52.5, 53.5, 54.5, 55.5, 56.5],
        [57.5, 58.5, 59.5, 60.5, 61.5, 62.5, 63.5, 64.5],
    ))

    expected = np.dot(a, b)

    # Do divide and conquer multiplication
    r.set("mat_a", a.tobytes())
    r.set("mat_b", b.tobytes())
    actual = _dnc_multiply("mat_a", "mat_b", a.shape[0])

    # Print results
    print("\nEXPECTED\n {}".format(expected))
    print("\nACTUAL\n{}".format(actual))


if __name__ == "__main__":
    main()
