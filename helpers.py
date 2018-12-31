import os
import collections
import numpy as np
import pandas as pd


class MisalignmentError(Exception):
    pass


def assert_misalignment(condition, message):
    if not condition:
        raise MisalignmentError(message)


def read_first_column_tuple(file_path):
    first_col = pd.read_csv(file_path, header=None, skiprows=3).iloc[1:, 0]
    return tuple(first_col[~first_col.isin([np.nan, '', ' '])])


def as_num(val):
    try:
        return int(val)
    except ValueError:
        return False


def get_longest_common_prefix_less_trailing_nums(specific_treatment_name, all_treatment_names):
    max = 0
    match = None
    for treatment_name in all_treatment_names:
        if specific_treatment_name != treatment_name:
            prefix = os.path.commonprefix([specific_treatment_name, treatment_name])
            if len(prefix) > max:
                max = len(prefix)
                match = prefix
    return match.rstrip('123456789')


def get_longest_common_substring(strings):
    substr = ''
    if len(strings) > 1 and len(strings[0]) > 0:
        for i in range(len(strings[0])):
            for j in range(len(strings[0]) - i + 1):
                if j > len(substr) and is_substr(strings[0][i:i + j], strings):
                    substr = strings[0][i:i + j]
    return substr


def is_substr(find, data):
    if len(data) < 1 and len(find) < 1:
        return False
    for i in range(len(data)):
        if find not in data[i]:
            return False
    return True


def stack_treatment_data(channel_column, header_indexes):
    default_dict = collections.defaultdict(list)
    channel_column_copy = list(channel_column)  # so our pop does not affect outer scope
    for slice_start, slice_end in zip(header_indexes, header_indexes[1:]):
        treatment_subset = channel_column_copy[slice_start:slice_end]
        treatment_name = channel_column_copy.pop(0)
        default_dict[treatment_name].extend(treatment_subset)
    return default_dict


