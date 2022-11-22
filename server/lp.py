import json
import math
from typing import List, Any

import numpy as np
import pulp

from functools import reduce

from pulp import PULP_CBC_CMD

from server.meta_data import MetaData, Mode


class Data:
    """
    Класс для промежуточной подготовки исходных данных.
    """

    x: np.ndarray
    y: np.ndarray
    r: float
    m: int
    delta: float
    omega: np.ndarray

    def __init__(self, meta_data: MetaData):
        self.delta = meta_data.delta
        self.r = meta_data.r
        self._set_y(meta_data)
        self._set_x(meta_data)
        self._calculation_omega()

        if meta_data.mode is Mode.PIECEWISE_GIVEN:
            self.m = meta_data.m

    def _set_x(self, meta_data: MetaData):
        x = []
        for array in meta_data.load_data:
            index = 0
            arr = []
            for item in array:
                if index != meta_data.var_y - 1:
                    arr.append(item)
                index += 1
            x.append(arr)

        if meta_data.free_chlen:
            _x = []
            for items in x:
                line = [1]
                line.extend(items)
                _x.append(line)
            x = _x

        self.x = np.array(x)

    def _set_y(self, meta_data: MetaData):
        y = []
        for array in meta_data.load_data:
            index = 0
            for item in array:
                if index == meta_data.var_y - 1:
                    y.append(item)
                index += 1

        self.y = np.array(y)

    def _calculation_omega(self):
        omega = []

        n = self.y.size
        for k in range(n - 1):
            for s in range(k + 1, n):
                exp = self.y[k] - self.y[s]
                if exp > 0:
                    omega.append(1)
                elif exp < 0:
                    omega.append(-1)
                else:  # == 0
                    omega.append(0)

        self.omega = np.array(omega)


class Result:
    mode: Mode

    a: list
    eps: list
    l: list
    yy: list
    e: float
    osp: float
    count_rows: int
    N: float
    resp_vector: list
    L: float

    def __init__(self, mode: Mode):
        self.mode = mode

        self.a = []
        self.eps = []
        self.l = []
        self.yy = []
        self.resp_vector = []

    @staticmethod
    def new_result(data=None):
        result = Result(Mode.build(Result.get_value(data, 'mode')))
        if data is not None:
            result.a = Result.get_value(data, 'a')
            result.eps = Result.get_value(data, 'eps')
            result.l = Result.get_value(data, 'l')
            result.yy = Result.get_value(data, 'yy')
            result.e = Result.get_value(data, 'e')
            result.osp = Result.get_value(data, 'osp')
            result.count_rows = Result.get_value(data, 'count_rows')
            result.N = Result.get_value(data, 'N')
            result.L = Result.get_value(data, 'L')
            result.resp_vector = Result.get_value(data, 'resp_vector')

        return result

    @staticmethod
    def get_value(data, key):
        try:
            return data[key]
        except KeyError:
            return None

    @property
    def m(self) -> float:
        """
        Получает сумму модулей ошибок.
        """
        m = 0
        for item in self.eps:
            m += abs(item)

        return m

    def calculation(self, _x: np.ndarray, _y: np.ndarray):
        """
        Шаблонный метод для вычисления агрегированных результатов вычислений.
        """
        self._set_yy(_x)
        self._epsilon_e(_y)
        self._set_max_rows()
        self._set_osp(_y)
        self._set_n(_y)
        self._set_L()

        if self.mode == Mode.PIECEWISE_GIVEN:
            self.response_vector(_x)

    def response_vector(self, _x: np.ndarray):
        """
        Рассчитывает вектор срабатываний.
        """
        self.resp_vector = []

        for i in range(len(self.yy)):
            min_x = self.a[0] * _x[i][0]
            min_index = 0
            for j in range(1, len(self.a)):
                if min_x > self.a[j] * _x[i][j]:
                    min_x = self.a[j] * _x[i][j]
                    min_index = j
            self.resp_vector.append(min_index + 1)

    def _set_osp(self, y: np.ndarray):
        """
        Обобщенный критерий согласованности поведения.
        """
        a = []
        for i in range(len(y) - 1):
            for j in range(i + 1, len(y)):
                a.append(self._sign((self.yy[i] - self.yy[j]) * (y[i] - y[j])))

        self.osp = sum(a)

    def _set_yy(self, _x: np.ndarray):
        self.yy = list(map(lambda item: sum(list(map(lambda x, a: x * a, item, self.a))), _x))

    def _epsilon_e(self, _y: np.ndarray):
        """
        Расчёт оценки ошибки аппроксимации.
        """
        self.e = 1 / len(_y) * reduce(
            lambda x, y: x + y, list(map(lambda x, y: math.fabs(x / y), self.eps, _y))) * 100

    def _set_L(self):
        self.L = sum(self.l)

    def _set_max_rows(self):
        self.count_rows = max(len(self.l), len(self.a), len(self.yy), len(self.eps))

    def _set_n(self, _y: np.ndarray):
        """
        Расчёт оценки непрерывного критерия согласованности поведения.
        """

        _sum = 0
        index_l = 0
        for k in range(_y.size - 1):
            for s in range(k + 1, _y.size):
                _sum += (self.l[index_l] / (_y[k] + _y[s]))
                index_l += 1

        self.N = _sum * ((2 * 100) / (_y.size * (_y.size - 1)))

    def get_max_rows(self):
        return list(map(int, range(self.count_rows)))

    def print(self) -> list:
        arr = []

        for index in range(self.count_rows):
            line = []

            if index < len(self.a):
                line.append(self.a[index])
            else:
                line.append(None)

            if index < len(self.l):
                line.append(self.l[index])
            else:
                line.append(None)

            if index == 0:
                line.append(self.L)
            else:
                line.append(None)

            if index < len(self.eps):
                line.append(self.eps[index])
            else:
                line.append(None)

            if self.mode == Mode.PIECEWISE_GIVEN:
                if index < len(self.resp_vector):
                    line.append(self.resp_vector[index])
                else:
                    line.append(None)

            if index == 0:
                line.append(self.e)
            else:
                line.append(None)

            if index == 0:
                line.append(self.osp)
            else:
                line.append(None)

            if index == 0:
                line.append(self.m)
            else:
                line.append(None)

            if index == 0:
                line.append(self.N)
            else:
                line.append(None)

            arr.append(line)
        return arr

    @staticmethod
    def _sign(x) -> int:
        return 1 if x > 0 else 0

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель MetaData в JSON формат.
        """

        def default(self, obj):
            if isinstance(obj, Result):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)


class LpSolve:
    """
    Задача линейного программирования.
    """

    mode: Mode
    data: Data
    result: Result
    _vars: dict
    _problem: pulp.LpProblem

    def __init__(self, mode: Mode, data: Data):
        self.mode = mode
        self.data = data
        self.result = Result(mode)
        self._vars = {}
        self._problem = pulp.LpProblem('0', pulp.const.LpMinimize)
        self._create_variable_u_v()
        self._create_variable_l()

        if self.mode is Mode.MNM:
            self._create_variable_beta_gamma()
        elif self.mode is Mode.PIECEWISE_GIVEN:
            self._create_variable_alfa()
            self._create_variable_z()
            self._create_variable_sigma()

        self._build_function_c()

        if self.mode is Mode.MNM:
            self._build_restrictions_for_mnm()
        elif self.mode is Mode.PIECEWISE_GIVEN:
            self._build_restrictions_for_mao()

        self._execute()
        self._set_result()

    def _create_variable_u_v(self):
        for index in range(self.data.y.size):
            var_name_u = f'u{index}'
            var_name_v = f'v{index}'
            self._vars.setdefault(var_name_u, pulp.LpVariable(var_name_u, lowBound=0))
            self._vars.setdefault(var_name_v, pulp.LpVariable(var_name_v, lowBound=0))

    def _create_variable_l(self):
        for k in range(self.data.y.size - 1):
            for s in range(k + 1, self.data.y.size):
                var_name = f'l{k}{s}'
                self._vars.setdefault(var_name, pulp.LpVariable(var_name, lowBound=0))

    def _create_variable_beta_gamma(self):
        for index in range(len(self.data.x[0])):
            var_name_beta = f'b{index}'
            var_name_gamma = f'g{index}'
            self._vars.setdefault(var_name_beta, pulp.LpVariable(var_name_beta, lowBound=0))
            self._vars.setdefault(var_name_gamma, pulp.LpVariable(var_name_gamma, lowBound=0))

    def _create_variable_z(self):
        for index in range(self.data.y.size):
            var_name = f'z{index}'
            self._vars.setdefault(var_name, pulp.LpVariable(var_name, lowBound=0))

    def _create_variable_sigma(self):
        for k in range(self.data.x.size):
            for i in range(len(self.data.x[0])):
                var_name = f'sigma{k}{i}'
                self._vars.setdefault(var_name, pulp.LpVariable(var_name, cat=pulp.const.LpBinary))

    def _create_variable_alfa(self):
        for i in range(self.data.x.size):
            var_name = f'alfa{i}'
            self._vars.setdefault(var_name, pulp.LpVariable(var_name))

    def _build_function_c(self):
        params = []

        for index in range(self.data.y.size):
            params.append((self._vars.get(f'u{index}'), self.data.r))
        for index in range(self.data.y.size):
            params.append((self._vars.get(f'v{index}'), self.data.r))
        for k in range(self.data.y.size - 1):
            for s in range(k + 1, self.data.y.size):
                params.append((self._vars.get(f'l{k}{s}'), 1 - self.data.r))

        if self.mode is Mode.MNM:
            for index in range(len(self.data.x[0])):
                params.append((self._vars.get(f'b{index}'), self.data.delta))
                params.append((self._vars.get(f'g{index}'), self.data.delta))

        self._problem += pulp.LpAffineExpression(params), 'Функция цели'

    def _build_restrictions_for_mnm(self):
        index_restriction = 0
        for index in range(self.data.y.size):
            params = []
            for index_x in range(len(self.data.x[0])):
                params.append((self._vars.get(f'b{index_x}'), self.data.x[index][index_x]))
                params.append((self._vars.get(f'g{index_x}'), -1 * self.data.x[index][index_x]))
            params.append((self._vars.get(f'u{index}'), 1))
            params.append((self._vars.get(f'v{index}'), -1))

            self._problem += pulp.LpAffineExpression(params) == self.data.y[index], str(index_restriction)
            index_restriction += 1

        index_omega = 0
        for k in range(self.data.y.size - 1):
            for s in range(k + 1, self.data.y.size):
                params = []
                for index in range(len(self.data.x[0])):
                    x = self.data.x[k][index] - self.data.x[s][index]
                    params.append((self._vars.get(f'b{index}'), x * self.data.omega[index_omega]))
                    params.append((self._vars.get(f'g{index}'), -1 * x * self.data.omega[index_omega]))
                params.append((self._vars.get(f'l{k}{s}'), 1))

                self._problem += pulp.LpAffineExpression(params) >= 0, str(index_restriction)
                index_restriction += 1

                index_omega += 1

    def _build_restrictions_for_mao(self):
        index_restriction = 0
        for i in range(self.data.y.size):
            params = [(self._vars.get(f'z{i}'), 1), (self._vars.get(f'u{i}'), 1), (self._vars.get(f'v{i}'), -1)]
            self._problem += pulp.LpAffineExpression(params) == self.data.y[i], str(index_restriction)

            index_restriction += 1

        for k in range(self.data.y.size):
            for i in range(len(self.data.x[0])):
                params = [(self._vars.get(f'alfa{i}'), self.data.x[k][i]),
                          (self._vars.get(f'z{k}'), -1)]
                self._problem += pulp.LpAffineExpression(params) >= 0, str(index_restriction)

                index_restriction += 1

        for k in range(self.data.y.size):
            for i in range(len(self.data.x[0])):
                params = [(self._vars.get(f'alfa{i}'), self.data.x[k][i]),
                          (self._vars.get(f'z{k}'), -1),
                          (self._vars.get(f'sigma{k}{i}'), self.data.m)]
                self._problem += pulp.LpAffineExpression(params) <= self.data.m, str(index_restriction)

                index_restriction += 1

        for k in range(self.data.y.size):
            params = []
            for i in range(len(self.data.x[0])):
                params.append((self._vars.get(f'sigma{k}{i}'), 1))
            self._problem += pulp.LpAffineExpression(params) == 1, str(index_restriction)

            index_restriction += 1

        index_omega = 0
        for k in range(self.data.y.size - 1):
            for s in range(k + 1, self.data.y.size):
                params = [(self._vars.get(f'z{k}'), self.data.omega[index_omega]),
                          (self._vars.get(f'z{s}'), -1 * self.data.omega[index_omega]),
                          (self._vars.get(f'l{k}{s}'), 1)]
                self._problem += pulp.LpAffineExpression(params) >= 0, str(index_restriction)
                index_omega += 1

                index_restriction += 1

    def _execute(self):
        # PULP_CBC_CMD(msg=0) так библиотека в лог будет писать только ошибки.
        self._problem.solve(PULP_CBC_CMD(msg=0))

    def _set_result(self):
        b, g, u, v = [], [], [], []

        for var in self._problem.variables():
            if 'b' in var.name:
                b.append(var.varValue)
            elif 'alfa' in var.name:
                self.result.a.append(var.varValue)
            elif 'g' in var.name:
                g.append(var.varValue)
            elif 'l' in var.name:
                self.result.l.append(var.varValue)
            elif 'u' in var.name:
                u.append(var.varValue)
            elif 'v' in var.name:
                v.append(var.varValue)

        for index in range(len(b)):
            self.result.a.append(b[index] - g[index])

        if self.mode == Mode.PIECEWISE_GIVEN:
            for i in range(len(self.data.y)):
                self.result.eps.append(
                    self.data.y[i] - min(list(map(lambda a, x: a * x, self.result.a, self.data.x[i]))))
        else:
            for index in range(len(u)):
                self.result.eps.append(u[index] - v[index])

        self.result.calculation(self.data.x, self.data.y)


class Pod:
    """
    Подзадача LpIdealDot.
    Хранит агрегированный результат решения задачи ЛП.
    """

    r: float
    E: float
    M: float
    L: float
    r_dot: float
    is_max: bool

    def __init__(self, r, e, m, l_, r_dot, is_max=False):
        self.r = r
        self.E = e
        self.M = m
        self.L = l_
        self.r_dot = r_dot
        self.is_max = is_max

    def __lt__(self, other):
        return self.r < other.r

    def __eq__(self, other):
        return self.r == self.r

    def __str__(self):
        return f'r: {self.r}, E: {self.E}, M: {self.M}, L: {self.L}, r_dot: {self.r_dot}'

    def copy(self):
        return Pod(self.r, self.E, self.M, self.L, self.r_dot, self.is_max)


class IdealDotResult:
    """
    Результаты поиска идеальной точки.
    Так же используется для хранения промежуточных результатов вычислений.
    """

    pods: List[Pod]
    result: Result
    pods_: List[Pod]
    r: float

    def __init__(self):
        self.pods = []

    def get_pod_by_max_r_dot(self) -> Pod | None:
        """Возвращает Pod с максимальным значением r_dot."""
        if not self.pods_:
            return None

        pod = self.pods_[0]
        for i in range(len(self.pods_)):
            if pod.r_dot < self.pods_[i].r_dot:
                pod = self.pods_[i]

        return pod

    def copy(self) -> List[Pod]:
        pods = []
        for item in self.pods:
            pods.append(item.copy())

        return pods


class LpIdealDot:
    """Задача поиска идеальной точки."""

    result: []
    pre_result: IdealDotResult
    data: Data

    def __init__(self, data: Data):
        self.result = []
        self.pre_result = IdealDotResult()
        self.data = data

        self._calculation()

    def _calculation(self):
        r = self._find_non_trivial_solution()

        if not r:
            raise Exception("Все решения тривиальны!")

        self._second_iteration(r)

        self.get_result_pods()

        self.data.r = self.pre_result.get_pod_by_max_r_dot().r
        self.pre_result.r = self.data.r
        self.pre_result.result = LpSolve(Mode.MNM, self.data).result

    def get_result_pods(self):
        self.pre_result.pods.sort(key=lambda x: x.r)

        pods = self._calculate_score()
        ideal_r_dot = self._find_index_ideal_dot(pods)

        for i in range(len(pods)):
            pods[i].r = float('{:.2f}'.format(pods[i].r))

        result: List[Pod] = []

        added_indexes = []
        for i in range(len(pods)):
            if i in ideal_r_dot:
                pods[i].is_max = True
                result.append(pods[i])
                added_indexes.append(i)
            elif i == 0:
                result.append(pods[i])
                added_indexes.append(i)
            elif i == len(pods) - 1:
                result.append(pods[i])
                added_indexes.append(i)
            elif pods[i].r in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
                result.append(pods[i])
                added_indexes.append(i)

        if ideal_r_dot[0] - 1 not in added_indexes and ideal_r_dot[0] - 1 >= 0:
            result.append(pods[ideal_r_dot[0] - 1])
            added_indexes.append(ideal_r_dot[0] - 1)
        if len(ideal_r_dot) > 1 and ideal_r_dot[len(ideal_r_dot) - 1] + 1 not in added_indexes \
                and 0 <= ideal_r_dot[0] + 1 < len(pods):
            result.append(pods[ideal_r_dot[len(ideal_r_dot) - 1] + 1])
            added_indexes.append(ideal_r_dot[len(ideal_r_dot) - 1] + 1)
        elif ideal_r_dot[0] + 1 not in added_indexes and 0 <= ideal_r_dot[0] + 1 < len(pods):
            result.append(pods[ideal_r_dot[0] + 1])
            added_indexes.append(ideal_r_dot[0] + 1)

        result.sort(key=lambda x: x.r)
        self.pre_result.pods_ = result

    def _second_iteration(self, r_left):
        for r in np.arange(r_left, 1.01, 0.01):
            if float('{:.2f}'.format(r)) == 1.01:
                continue
            data = self.data
            data.r = r
            result = LpSolve(Mode.MNM, data).result
            self.pre_result.pods.append(Pod(r, result.e, result.m, result.L, None))

    @staticmethod
    def _find_index_ideal_dot(pods: List[Pod]) -> List[int]:
        """Ищет индексы с идеальной точкой."""
        ideal_indexes = []
        ideal_index = 0
        for i in range(len(pods)):
            if pods[ideal_index].r_dot < pods[i].r_dot:
                ideal_index = i

        for i in range(len(pods)):
            if pods[ideal_index].r_dot == pods[i].r_dot:
                ideal_indexes.append(i)

        return ideal_indexes

    def _calculate_score(self) -> List[Pod]:
        """Вычисляет оценки параметров и считает антиточку."""
        pods = self.pre_result.copy()

        divider_E = max(list(map(lambda item: item.E, pods)))
        divider_M = max(list(map(lambda item: item.M, pods)))
        divider_L = max(list(map(lambda item: item.L, pods)))

        for i in range(len(pods)):
            pods[i].E /= divider_E
            pods[i].M /= divider_M
            pods[i].L /= divider_L

            pods[i].r_dot = (1 - pods[i].E) + (1 - pods[i].M) + (1 - pods[i].L)

        return pods

    def _find_non_trivial_solution(self) -> float:
        """Ищет не тривиальное решение."""

        for r in np.arange(0.01, 1, 0.01):
            data = self.data
            data.r = r
            result = LpSolve(Mode.MNM, data).result
            if result.L != 0:
                return r


if __name__ == '__main__':
    lp = LpIdealDot(None)

# 5  1 6
# 7  7 8
# 9  4 2
# 3  3 5

# problem = pulp.LpProblem('', pulp.const.LpMinimize)
#
# u1 = pulp.LpVariable('u1', lowBound=0)
# u2 = pulp.LpVariable('u2', lowBound=0)
# u3 = pulp.LpVariable('u3', lowBound=0)
# u4 = pulp.LpVariable('u4', lowBound=0)
# v1 = pulp.LpVariable('v1', lowBound=0)
# v2 = pulp.LpVariable('v2', lowBound=0)
# v3 = pulp.LpVariable('v3', lowBound=0)
# v4 = pulp.LpVariable('v4', lowBound=0)
# l12 = pulp.LpVariable('l12', lowBound=0)
# l13 = pulp.LpVariable('l13', lowBound=0)
# l14 = pulp.LpVariable('l14', lowBound=0)
# l23 = pulp.LpVariable('l23', lowBound=0)
# l24 = pulp.LpVariable('l24', lowBound=0)
# l34 = pulp.LpVariable('l34', lowBound=0)
# b1 = pulp.LpVariable('b1', lowBound=0)
# g1 = pulp.LpVariable('g1', lowBound=0)
# b2 = pulp.LpVariable('b2', lowBound=0)
# g2 = pulp.LpVariable('g2', lowBound=0)
#
# problem += 0.3*u1 + 0.3*u2 + 0.3*u3 + 0.3*u4 + 0.3*v1 + 0.3*v2 + 0.3*v3 + 0.3*v4 \
#     + 0.7*l12 + 0.7*l13 + 0.7*l14 + 0.7*l23 + 0.7*l24 + 0.7*l34 \
#     + 0.000001*b1 + 0.000001*g1 + 0.000001*b2 + 0.000001*g2, 'Function'
#
# problem += 6*b1 - 6*g1 + 2*b2 - 2*g2 + l12 >= 0
# problem += 3*b1 - 3*g1 - 4*b2 + 4*g2 + l13 >= 0
# problem += -2*b1 + 2*g1 + b2 - g2 + l14 >= 0
# problem += -3*b1 + 3*g1 - 6*b2 + 6*g2 + l23 >= 0
# problem += 4*b1 - 4*g1 + 3*b2 - 3*g2 + l24 >= 0
# problem += b1 - g1 - 3*b2 + 3*g2 + l34 >= 0
#
# problem += b1 - g1 + 6*b2 - 6*g2 + u1 - v1 == 5
# problem += 7*b1 - 7*g1 + 8*b2 - 8*g2 + u2 - v2 == 7
# problem += 4*b1 - 4*g1 + 2*b2 - 2*g2 + u3 - v3 == 9
# problem += 3*b1 - 3*g1 + 5*b2 - 5*g2 + u4 - v4 == 3
#
# problem.solve()
# for variable in problem.variables():
#     print(variable.name, "=", variable.varValue)
# print(abs(pulp.value(problem.objective)))

# Результаты решения (совпали с ожидаемыми):
# b1 = 0.64285714
# b2 = 0.21428571
# g1 = 0.0
# g2 = 0.0
# l12 = 0.0
# l13 = 0.0
# l14 = 1.0714286
# l23 = 3.2142857
# l24 = 0.0
# l34 = 0.0
# u1 = 3.0714286
# u2 = 0.78571429
# u3 = 6.0
# u4 = 0.0
# v1 = 0.0
# v2 = 0.0
# v3 = 0.0
# v4 = 0.0
# 5.95714373414285
