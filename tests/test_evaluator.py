from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import numpy as np
import pandas as pd

from xopt import Evaluator


class TestEvaluator:
    @staticmethod
    def f(x, a=True):
        if a:
            return {"f": x["x1"] ** 2 + x["x2"] ** 2}
        else:
            return {"f": False}

    @staticmethod
    def g(x, a=True):
        return False

    @staticmethod
    def identity(x, a=True):
        return {k + "_out": v for k, v in x.items()}

    def test_submit(self):
        evaluator = Evaluator(function=self.f)
        candidates = pd.DataFrame(np.random.rand(10, 2), columns=["x1", "x2"])
        futures = evaluator.submit_data(candidates)
        assert len(futures) == 10

        # try with a bad function
        evaluator = Evaluator(function=self.g)
        candidates = pd.DataFrame(np.random.rand(10, 2), columns=["x1", "x2"])
        futures = evaluator.submit_data(candidates)
        assert len(futures) == 10

    def test_type_preservation(self):
        """
        Tests for these problems:
        iterrows does not necessarily preserve types:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.iterrows.html
        itertuples does not preserve column names with understores or colons.
        """
        evaluator = Evaluator(function=self.identity)

        #  Test with ints and floats ONLY. A
        candidates = pd.DataFrame(
            {
                "ints": [1, 2, 3],
                "floats": [2.0, 3.0, 4.0],
                "_leading": [2.0, 3.0, 4.0],
                "has:colon": [1, 2.0, 3],
                ":colon:leading": [2.0, 3.0, 4.0],
                #  Do not add these.
                # 'strings': ['a','b','c'],
                # 'booleans': [True, False, True],
                # 'lists': [[1,2,3],[4,5,6],[7,8,9]],
                # 'dicts': [{'a':1,'b':2},{'c':3,'d':4},{'e':5,'f':6}],
                # 'tuples': [(1,2,3),(4,5,6),(7,8,9)]
            },
            index=[7, 8, 9],
        )
        futures = evaluator.submit_data(candidates)
        data = [fut.result() for fut in futures]
        df2 = pd.DataFrame(data, index=candidates.index)
        # Strip additional Xopt columns
        for key in df2.columns:
            if key.startswith("xopt_"):
                df2.pop(key)

        df2.columns = df2.columns.str.replace("_out", "")
        assert df2.equals(candidates), "DataFrame types were not preserved"

    def test_init(self):
        test_dict = {
            "function": self.f,
            "max_workers": 1,
        }
        evaluator = Evaluator(**test_dict)
        candidates = pd.DataFrame(np.random.rand(10, 2), columns=["x1", "x2"])
        futures = evaluator.submit_data(candidates)
        assert len(futures) == 10

        evaluator = Evaluator(**test_dict)
        candidates = pd.DataFrame(np.random.rand(10, 2), columns=["x1", "x2"])
        futures = evaluator.submit_data(candidates)
        assert len(futures) == 10

        test_dict["function_kwargs"] = {"a": False}
        evaluator = Evaluator(**test_dict)
        candidates = pd.DataFrame(np.random.rand(10, 2), columns=["x1", "x2"])
        futures = evaluator.submit_data(candidates)
        assert len(futures) == 10
        assert futures[0].result()["f"] is False

    def test_serialize(self):
        test_dict = {
            "function": self.f,
            "max_workers": 1,
        }

        for Executor in [ThreadPoolExecutor, ProcessPoolExecutor]:
            test_dict["executor"] = Executor()
            ev = Evaluator(**test_dict)
            ev.json()
