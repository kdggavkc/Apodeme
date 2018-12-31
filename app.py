import collections
from os import path, listdir

from helpers import (assert_misalignment,
                     MisalignmentError,
                     read_first_column_tuple,
                     as_num,
                     get_longest_common_substring,
                     get_longest_common_prefix_less_trailing_nums)

# if __name__ == '__main__':

def run_process():
    filepath = input("Where is the directory where your CSV's are stored?")
    input_threshold_values = input('What are the threshold values? Format: channel_1_number, channel_2_number')
    threshold_values = tuple(int(i) for i in input_threshold_values.split(', '))

    csv_targets = sorted([path.join(filepath, f) for f in listdir(filepath) if f.endswith('.csv')])
    assert len(csv_targets) == 2, "Provided file directory does not contain 2 csv files!"

    # expect format ['name', '2', '3', ... 'name2', '1', '3' ... ] for both channels
    raw_channel1 = read_first_column_tuple(csv_targets[0])
    raw_channel2 = read_first_column_tuple(csv_targets[1])

    # ensure basic formatting expectations
    assert_misalignment(not any([as_num(raw_channel1[0]), as_num(raw_channel2[0])]),
                        "Expected first value to be a string -- exiting.")

    assert_misalignment(len(raw_channel1) == len(raw_channel2),
                        "Input data does not align! Make sure you supplied *related* files from Batch.")

    # saving raw for validation later
    channel1 = list(raw_channel1)
    channel2 = list(raw_channel2)

    # ----------------------------------------------------------
    # Identify Header Locations and Cast Non-Headers as Integers
    # ----------------------------------------------------------

    headers = []
    header_indexes = []
    for i, (cell_c1, cell_c2) in enumerate(zip(channel1, channel2)):
        as_numbers = [as_num(cell_c1), as_num(cell_c2)]

        if not any(as_numbers):
            assert_misalignment(cell_c1 == cell_c2, "Paired headers do not match!")
            headers.append(cell_c1)
            header_indexes.append(i)

        elif all(as_numbers):
            channel1[i], channel2[i] = as_numbers

        # one is a number and the other is not
        else:
            print("Error found at index: {}. Data = {} & {}".format(i, cell_c1, cell_c2))
            raise MisalignmentError("A paired value is an integer and another is a string! Datapoints are misaligned!")

    # -----------------------------------------------
    # Simplify and Group Headers into Treatment names
    # -----------------------------------------------

    # there are some visually-identifiable patterns in these header naming conventions, but because I only tested a
    # subset of datasets, it was better to make this string grouping robust rather than coding specifically for the
    # naming conventions I saw.

    # EXAMPLES OF STRINGS WE NEED TO GROUP TOGETHER
    #
    # [
    # 'BAFasyncy5dspgfpgal8tritcz02_R3D_D3D-Surfaces-Surfaces-2017-5-30-1',
    # 'BAFasyncy5dspgfpgal8tritcz03_R3D_D3D-Surfaces-Surfaces-2017-5-30-2',
    # 'BAFasyncy5dspgfpgal8tritcz04_R3D_D3D-Surfaces-Surfaces-2017-5-30-3',
    # 'BAFasyncy5dspgfpgal8tritcz05_R3D_D3D-Surfaces-Surfaces-2017-5-30-4',
    # 'BAFasyncy5dspgfpgal8tritcz06_R3D_D3D-Surfaces-Surfaces-2017-5-30-5' ...
    # ]

    # We want to remap all above strings to: "BAFasyncy5dspgfpgal8tritcz"

    # [
    #                    ____desired experiment name
    #                   |
    #                   |          ____image count per experiment
    #                   |         |
    #                   |         |                 ____long generic substring
    #                   |         |                |
    #                   |         |                |                 _____run date
    #                   |         |                |                |
    #                   |         |                |                |      ____total image count so far
    #                   |         |                |                |     |
    #                   |         |                |                |     |
    # 'LLOMEasyncy5dspgfplc3tritcz01_R3D_D3D-Surfaces-Surfaces-2017-5-30-34',
    # 'LLOMEasyncy5dspgfplc3tritcz02_R3D_D3D-Surfaces-Surfaces-2017-5-30-35',
    # 'LLOMEasyncy5dspgfplc3tritcz03_R3D_D3D-Surfaces-Surfaces-2017-5-30-36',
    # 'LLOMEasyncy5dspgfplc3tritcz04_R3D_D3D-Surfaces-Surfaces-2017-5-30-37',
    # 'LLOMEasyncy5dspgfplc3tritcz05_R3D_D3D-Surfaces-Surfaces-2017-5-30-38' ...
    # ]

    # We want to remap all above strings to: "LLOMEasyncy5dspgfplc3tritcz"

    lcs = get_longest_common_substring(headers)

    treatment_names_with_image_nums = [
        header.split(lcs)[0]
        for header in headers
    ]  # 'LLOMEasyncy5dspgfplc3tritcz01_R3D_D3D-Surfaces-Surfaces-2017-5-30-34' -> LLOMEasyncy5dspgfplc3tritcz01

    treatment_names_without_image_nums = [
        get_longest_common_prefix_less_trailing_nums(header, treatment_names_with_image_nums)
        for header in treatment_names_with_image_nums
    ]  # i.e. LLOMEasyncy5dspgfplc3tritcz01 -> LLOMEasyncy5dspgfplc3tritcz

    # replace headers with treatment names
    header_treatment_map = dict(zip(headers, treatment_names_without_image_nums))
    for header_index, header in zip(header_indexes, headers):
        channel1[header_index] = channel2[header_index] = header_treatment_map[header]

    # stack data by treatment name
    treatment_data_map_c1 = collections.defaultdict(list)
    treatment_data_map_c2 = collections.defaultdict(list)
    for slice_start, slice_end in zip(header_indexes, header_indexes[1:]):
        treatment_subset_c1 = channel1[slice_start:slice_end]
        treatment_subset_c2 = channel2[slice_start:slice_end]

        treatment_name_c1 = treatment_subset_c1.pop(0)
        treatment_name_c2 = treatment_subset_c2.pop(0)

        treatment_data_map_c1[treatment_name_c1].extend(treatment_subset_c1)
        treatment_data_map_c2[treatment_name_c2].extend(treatment_subset_c2)

    # -----------
    # Validations
    # -----------

    lengths = [len(x) for x in [raw_channel1, raw_channel2, channel1, channel2]]
    assert_misalignment(len(set(lengths)) == 1, "Misalignment has occurred, stopping. {}, {}, {}, {}".format(*lengths))

    # checking integrity -- (resist the urge to abstract this re-occuring pattern out)
    for index, cells in enumerate(zip(channel1, channel2)):

        if index not in header_indexes:
            # faster to convert int to strings than inverse
            assert list(map(str, cells)) == [raw_channel1[index], raw_channel2[index]]

        # skip header/treatment names since we know they are now different
        else:
            continue

    # ------------------------------------------------
    # Truth Table Assessments Against Threshold Values
    # ------------------------------------------------

    treatment_threshold_results = {}
    for (name_c1, data_c1), (name_c2, data_c2) in zip(treatment_data_map_c1.items(), treatment_data_map_c2.items()):

        assert_misalignment(name_c1 == name_c2, "Not iterating over the same treatment -- data is misaligned!")

        bool_map = {
            (True, True): [],
            (True, False): [],
            (False, True): [],
            (False, False): []
        }

        for cell_c1, cell_c2 in zip(data_c1, data_c2):
            bool_c1 = cell_c1 > threshold_values[0]
            bool_c2 = cell_c2 > threshold_values[1]
            truth_table = (bool_c1, bool_c2)
            bool_map[truth_table].append((cell_c1, cell_c2))

        treatment_threshold_results[name_c1] = bool_map
