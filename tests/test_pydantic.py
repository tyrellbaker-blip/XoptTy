import json
from functools import partial
from types import FunctionType, MethodType

import pytest
from pydantic.json import custom_pydantic_encoder

from xopt.pydantic import (
    CallableModel,
    get_callable_from_string,
    JSON_ENCODERS,
    ObjLoader,
    validate_and_compose_signature,
)


def misc_fn(x, y=1, *args, **kwargs):
    pass


class MiscClass:
    @staticmethod
    def misc_static_method(x, y=1, *args, **kwargs):
        return

    @classmethod
    def misc_cls_method(cls, x, y=1, *args, **kwargs):
        return cls

    def misc_method(self, x, y=1, *args, **kwargs):
        return


class TestJsonEncoders:

    misc_class = MiscClass()

    @pytest.mark.parametrize(
        ("fn",),
        [
            (misc_fn,),
            pytest.param(misc_class.misc_method, marks=pytest.mark.xfail(strict=True)),
            (misc_class.misc_static_method,),
            pytest.param(
                misc_class.misc_cls_method, marks=pytest.mark.xfail(strict=True)
            ),
        ],
    )
    def test_function_type(self, fn):
        encoder = {FunctionType: JSON_ENCODERS[FunctionType]}
        json_encoder = partial(custom_pydantic_encoder, encoder)

        serialized = json.dumps(fn, default=json_encoder)
        loaded = json.loads(serialized)
        callable_from_str = get_callable_from_string(loaded)

        assert fn == callable_from_str

    @pytest.mark.parametrize(
        ("fn",),
        [
            pytest.param(
                misc_class.misc_static_method, marks=pytest.mark.xfail(strict=True)
            ),
            pytest.param(misc_fn, marks=pytest.mark.xfail(strict=True)),
            (misc_class.misc_method,),
            pytest.param(
                misc_class.misc_cls_method, marks=pytest.mark.xfail(strict=True)
            ),
        ],
    )
    def test_method_type(self, fn):
        encoder = {MethodType: JSON_ENCODERS[MethodType]}
        json_encoder = partial(custom_pydantic_encoder, encoder)

        serialized = json.dumps(fn, default=json_encoder)
        loaded = json.loads(serialized)
        callable = get_callable_from_string(loaded, bind=self.misc_class)

        assert fn == callable

    @pytest.mark.parametrize(
        ("fn",),
        [
            (misc_class.misc_static_method,),
            (misc_fn,),
            (misc_class.misc_method,),
            (misc_class.misc_cls_method,),
        ],
    )
    def test_full_encoder(self, fn):
        json_encoder = partial(custom_pydantic_encoder, JSON_ENCODERS)
        serialized = json.dumps(fn, default=json_encoder)
        loaded = json.loads(serialized)

        get_callable_from_string(loaded)


class TestSignatureValidateAndCompose:

    misc_class = MiscClass()

    @pytest.mark.parametrize(
        ("args", "kwargs"),
        [
            pytest.param((5, 2, 1), {"x": 2}, marks=pytest.mark.xfail(strict=True)),
            pytest.param((), ({"y": 2}), marks=pytest.mark.xfail(strict=True)),
            pytest.param((2,), ({"x": 2}), marks=pytest.mark.xfail(strict=True)),
            ((), ({"x": 2})),
            ((), {}),
        ],
    )
    def test_validate_kwarg_only(self, args, kwargs):
        def run(*, x: int = 4):
            pass

        signature_model = validate_and_compose_signature(run, *args, **kwargs)
        assert all(
            [kwargs[kwarg] == getattr(signature_model, kwarg) for kwarg in kwargs]
        )
        # run

        args, kwargs = signature_model.build()

        run(*args, **kwargs)

    @pytest.mark.parametrize(
        ("args", "kwargs"),
        [
            pytest.param(
                (
                    5,
                    3,
                    2,
                ),
                {"x": 1},
                marks=pytest.mark.xfail(strict=True),
            ),
            ((2, 1, 0), {}),
            ((), {}),
        ],
    )
    def test_validate_var_positional(self, args, kwargs):
        def run(*args):
            pass

        signature_model = validate_and_compose_signature(run, *args, **kwargs)
        args, kwargs = signature_model.build()
        assert len(kwargs) == 0
        assert len(args) == len(args)

        # run
        run(*args)

    @pytest.mark.parametrize(
        ("args", "kwargs"),
        [
            pytest.param((5,), {"x": 2}, marks=pytest.mark.xfail(strict=True)),
            ((), {"x": 2, "y": 3}),
            pytest.param((), {}, marks=pytest.mark.xfail(strict=True)),
            (
                (
                    2,
                    4,
                ),
                {},
            ),
            ((2,), {"y": 4, "extra": True}),
            ((2,), {"y": 4}),
            ((2,), {"y": 4, "z": 3}),
        ],
    )
    def test_validate_full_sig(self, args, kwargs):
        def run(x, y, z=4, *args, **kwargs):
            pass

        signature_model = validate_and_compose_signature(run, *args, **kwargs)
        args, kwargs = signature_model.build()

        # run
        run(*args, **kwargs)

    @pytest.mark.parametrize(
        ("args", "kwargs"),
        [
            pytest.param((5, 1), {"y": 2}, marks=pytest.mark.xfail(strict=True)),
            (
                (
                    2,
                    4,
                ),
                {},
            ),
            ((5,), {"y": 2}),
        ],
    )
    def test_validate_classmethod(self, args, kwargs):

        signature_model = validate_and_compose_signature(
            self.misc_class.misc_cls_method, *args, **kwargs
        )
        args, kwargs = signature_model.build()
        self.misc_class.misc_cls_method(*args, **kwargs)

    @pytest.mark.parametrize(
        ("args", "kwargs"),
        [
            pytest.param((5, 1), {"y": 2}, marks=pytest.mark.xfail(strict=True)),
            (
                (
                    2,
                    4,
                ),
                {},
            ),
            ((5,), {"y": 2}),
        ],
    )
    def test_validate_staticmethod(self, args, kwargs):

        signature_model = validate_and_compose_signature(
            self.misc_class.misc_static_method, *args, **kwargs
        )
        args, kwargs = signature_model.build()
        self.misc_class.misc_static_method(*args, **kwargs)

    @pytest.mark.parametrize(
        ("args", "kwargs"),
        [
            pytest.param((5, 1), {"y": 2}, marks=pytest.mark.xfail(strict=True)),
            (
                (
                    2,
                    4,
                ),
                {},
            ),
            ((5,), {"y": 2}),
        ],
    )
    def test_validate_bound_method(self, args, kwargs):

        signature_model = validate_and_compose_signature(
            self.misc_class.misc_method, *args, **kwargs
        )

        args, kwargs = signature_model.build()

        self.misc_class.misc_method(*args, **kwargs)


class TestCallableModel:

    misc_class = MiscClass()

    @pytest.mark.parametrize(
        ("fn", "args", "kwargs"),
        [
            (misc_fn, (5,), {"y": 2}),
            (misc_class.misc_cls_method, (5,), {"y": 2}),
            (misc_class.misc_static_method, (5,), {"y": 2}),
            pytest.param(
                misc_class.misc_method,
                (5,),
                {"y": 2},
                marks=pytest.mark.xfail(strict=True),
            ),
        ],
    )
    def test_construct_callable(self, fn, args, kwargs):
        json_encoder = partial(custom_pydantic_encoder, JSON_ENCODERS)
        serialized = json.dumps(fn, default=json_encoder)
        loaded = json.loads(serialized)

        callable = CallableModel(callable=loaded)
        callable(*args, **kwargs)

    @pytest.mark.parametrize(
        ("fn", "args", "kwargs"),
        [
            pytest.param(misc_fn, (5,), {"y": 2}, marks=pytest.mark.xfail(strict=True)),
            pytest.param(
                misc_class.misc_cls_method,
                (5,),
                {"y": 2},
                marks=pytest.mark.xfail(strict=True),
            ),
            pytest.param(
                misc_class.misc_static_method,
                (5,),
                {"y": 2},
                marks=pytest.mark.xfail(strict=True),
            ),
            (misc_class.misc_method, (5,), {"y": 2}),
        ],
    )
    def test_bound_callables(self, fn, args, kwargs):
        json_encoder = partial(custom_pydantic_encoder, JSON_ENCODERS)
        serialized = json.dumps(fn, default=json_encoder)
        loaded = json.loads(serialized)

        callable = CallableModel(callable=loaded, bind=self.misc_class)
        callable(*args, **kwargs)


class TestObjLoader:

    misc_class_loader_type = ObjLoader[MiscClass]

    def test_class_loader(self):
        loader = self.misc_class_loader_type()
        assert loader.object_type == MiscClass

    def test_load_model(self):
        loader = self.misc_class_loader_type()
        misc_obj = loader.load()
        assert isinstance(misc_obj, (MiscClass,))

    def test_serialize_loader(self):
        loader = self.misc_class_loader_type()

        json_encoder = partial(custom_pydantic_encoder, JSON_ENCODERS)
        serialized = json.dumps(loader, default=json_encoder)
        self.misc_class_loader_type.parse_raw(serialized)
