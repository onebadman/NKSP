import math
from typing import List


class Results:
    approximation_error: List[float]
    ksp: List[float]
    relative_ksp: List[float]
    continuous_ksp: List[float]
    relative_continuous_ksp: List[float]
    sum_error_modules: List[float]
    maximum_error: List[float]
    maximum_relative_error: List[float]
    sum_squared_errors: List[float]
    multiple_determination_criterion: List[float]

    def to_print(self):
        data = []

        n = len(self.ksp)
        for index in range(n):
            data.append([])

            data[index].append(f'y{index + 1}')

            data[index].append(self.approximation_error[index])
            data[index].append(self.ksp[index])
            data[index].append(self.relative_ksp[index])
            data[index].append(self.continuous_ksp[index])
            data[index].append(self.relative_continuous_ksp[index])
            data[index].append(self.sum_error_modules[index])
            data[index].append(self.maximum_error[index])
            data[index].append(self.maximum_relative_error[index])
            data[index].append(self.sum_squared_errors[index])
            data[index].append(self.multiple_determination_criterion[index])

        return data


class Criteria:
    data: list
    actual_values: List[float]
    calculated_values: List[List[float]]

    results: Results

    def __init__(self, data: list):
        self.data = data
        self.results = Results()

        self.data_preparation()

        self.calculation()

    def calculation(self):
        self.get_approximation_error()
        self.get_ksp()
        self.get_relative_ksp()
        self.get_continuous_ksp()
        self.get_relative_continuous_ksp()
        self.get_sum_error_modules()
        self.get_maximum_error()
        self.get_maximum_relative_error()
        self.get_sum_squared_errors()
        self.get_multiple_determination_criterion()

    def data_preparation(self):
        self.actual_values = []
        self.calculated_values = []

        m = len(self.data)
        n = len(self.data[0])
        for i in range(m):
            for j in range(n):
                if j == 0:
                    self.actual_values.append(self.data[i][j])
                else:
                    if len(self.calculated_values) < j:
                        self.calculated_values.append([])

                    self.calculated_values[j - 1].append(self.data[i][j])

    def get_approximation_error(self):
        self.results.approximation_error = []

        n = len(self.actual_values)
        for items in self.calculated_values:
            value = 0

            for index in range(n):
                value += abs((self.actual_values[index] - items[index]) / self.actual_values[index])

            value /= n

            value *= 100

            self.results.approximation_error.append(value)

    def get_ksp(self):
        self.results.ksp = []

        n = len(self.actual_values)
        for items in self.calculated_values:
            value = 0

            for k in range(n - 1):
                for s in range(k + 1, n):
                    exp = (self.actual_values[k] - self.actual_values[s]) * (items[k] - items[s])
                    if exp >= 0:
                        value += 1

            self.results.ksp.append(value)

    def get_relative_ksp(self):
        self.results.relative_ksp = []

        n = len(self.actual_values)
        for ksp_value in self.results.ksp:
            value = (200 * ksp_value) / (n * (n - 1))

            self.results.relative_ksp.append(value)

    def get_continuous_ksp(self):
        self.results.continuous_ksp = []

        n = len(self.actual_values)
        for items in self.calculated_values:
            value = 0

            for k in range(n - 1):
                for s in range(k + 1, n):
                    if (self.actual_values[k] - self.actual_values[s]) * (items[k] - items[s]) < 0:
                        value += abs(items[k] - items[s])

            self.results.continuous_ksp.append(value)

    def get_relative_continuous_ksp(self):
        self.results.relative_continuous_ksp = []

        n = len(self.actual_values)
        for items in self.calculated_values:
            value = 0

            for k in range(n - 1):
                for s in range(k + 1, n):
                    if (self.actual_values[k] - self.actual_values[s]) * (items[k] - items[s]) < 0:
                        value += abs(items[k] - items[s]) / (self.actual_values[k] - self.actual_values[s])

            value *= (200 / (n * (n - 1)))

            self.results.relative_continuous_ksp.append(value)

    def get_sum_error_modules(self):
        self.results.sum_error_modules = []

        n = len(self.actual_values)
        for items in self.calculated_values:
            value = 0

            for index in range(n):
                value += abs(self.actual_values[index] - items[index])

            self.results.sum_error_modules.append(value)

    def get_maximum_error(self):
        self.results.maximum_error = []

        n = len(self.actual_values)
        for items in self.calculated_values:
            errors = []

            for index in range(n):
                errors.append(abs(self.actual_values[index] - items[index]))

            self.results.maximum_error.append(max(errors))

    def get_maximum_relative_error(self):
        self.results.maximum_relative_error = []

        n = len(self.actual_values)
        for items in self.calculated_values:
            errors = []

            for index in range(n):
                errors.append(abs((self.actual_values[index] - items[index]) / self.actual_values[index]))

            self.results.maximum_relative_error.append(100 * max(errors))

    def get_sum_squared_errors(self):
        self.results.sum_squared_errors = []

        n = len(self.actual_values)
        for items in self.calculated_values:
            value = 0

            for index in range(n):
                value += math.pow(self.actual_values[index] - items[index], 2)

            self.results.sum_squared_errors.append(value)

    def get_multiple_determination_criterion(self):
        self.results.multiple_determination_criterion = []

        n = len(self.actual_values)
        for items in self.calculated_values:
            y = 0
            for index in range(n):
                y += self.actual_values[index]
            y /= n

            numerator = 0
            denominator = 0

            for index in range(n):
                numerator += math.pow(y - items[index], 2)
                denominator += math.pow(self.actual_values[index] - items[index], 2)

            value = numerator / denominator

            self.results.multiple_determination_criterion.append(value)
