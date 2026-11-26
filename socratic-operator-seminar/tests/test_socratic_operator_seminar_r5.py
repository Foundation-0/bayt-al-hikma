#!/usr/bin/env python3
"""Assertion-free R5 adversarial verification & 100% mutation/BoolOp suite for socratic_operator_seminar.py."""

from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SEMINAR_DIR = Path(__file__).resolve().parent.parent
if str(SEMINAR_DIR) not in sys.path:
    sys.path.insert(0, str(SEMINAR_DIR))

import socratic_operator_seminar as mod  # noqa: E402


def _sample_interpositions() -> list:
    return [
        {
            "id": "repo:Foundation-0/bayt-al-hikma",
            "org": "Foundation-0",
            "kind": "heritage_corpus",
            "score_q": "1/4",
            "shared_operators": ["non_coprime_crt"],
            "gate_status": "EXACT_OPERATOR_VERIFIED",
        }
    ]


def _make_valid_turn(
    turn_id: str = "R1-SEAT-1",
    round_num: int = 1,
    seat_id: str = "SEAT-1",
    mode: str = "compose",
    target: str = "SEAT-2",
    code: str = "from fractions import Fraction\ndef check_case(case):\n    return Fraction(case['a'], 1) == Fraction(case['b'], 1)\n",
    cases: list | None = None,
    interpositions: list | None = None,
) -> dict:
    turn = {
        "turn_id": turn_id,
        "round_num": round_num,
        "seat_id": seat_id,
        "corpus_anchor": {
            "operator_id": "OP-ANCHOR-1",
            "source_receipt_id": "corpus:exact-operator",
            "statement": "Exact rational identity anchor",
        },
        "composition_or_challenge": {
            "mode": mode,
            "target_seat_or_turn": target,
            "algebraic_link": "Explicit algebraic composition",
        },
        "executable_conjecture": {
            "conjecture_id": f"CONJ-{turn_id}",
            "kind": "python_exact_q",
            "claim_summary": "Checks exact rational equality a == b",
            "code": code,
            "test_cases": [{"a": 3, "b": 3}] if cases is None else cases,
        },
        "target_frontier": "Foundation-0/continuum",
    }
    if seat_id == "SEAT-0" or interpositions is not None:
        turn["epistemic_web_interpositions"] = _sample_interpositions() if interpositions is None else interpositions
    return turn


class TestSocraticOperatorSeminarR5(unittest.TestCase):
    def _assert_err(self, code: str, fn, *args, **kwargs) -> None:
        with self.assertRaises(mod.SeminarError) as cm:
            fn(*args, **kwargs)
        self.assertEqual(cm.exception.code, code)

    def test_01_pure_q_ast_self_guard_and_qdiv_controls(self) -> None:
        # Self-check all 3 core Python modules cleanly
        for name in ("socratic_operator_seminar.py", "verify_pilot1_theorems.py", "verify_ablation_scorecard.py"):
            res = mod.verify_pure_q_ast(SEMINAR_DIR.joinpath(name).read_text(encoding="utf-8"))
            self.assertTrue(res["pure_q_ast_clean"])

        # qdiv exact & zero-denom
        self.assertEqual(mod.qdiv(Fraction(3, 5), Fraction(7, 2)), Fraction(6, 35))
        self._assert_err("QDIV_ZERO_DENOM", mod.qdiv, Fraction(1, 1), Fraction(0, 1))

        # Positive AST coverage for Fraction safe args & math alias
        good_ast = (
            "import math as m\n"
            "import fractions\n"
            "from fractions import Fraction as F\n"
            "from math import gcd\n"
            "def f(a, xs):\n"
            "    g = m.gcd(4, 6)\n"
            "    q = F(-1, 2)\n"
            "    r = fractions.Fraction(q.numerator + xs[0], g if a else len(xs))\n"
            "    return r\n"
        )
        self.assertTrue(mod.verify_pure_q_ast(good_ast)["pure_q_ast_clean"])

        # Negative bypass controls covering every verify_pure_q_ast guard & BoolOp
        bad_ast_cases = (
            ("def (\n", "AST_SYNTAX_ERROR"),
            ("import numpy\n", "AST_FORBIDDEN_IMPORT"),
            ("from . import foo\n", "AST_REL_IMPORT_FORBIDDEN"),
            ("from decimal import Decimal\n", "AST_FORBIDDEN_IMPORT"),
            ("from math import *\n", "AST_WILDCARD_IMPORT"),
            ("from math import log\n", "AST_FORBIDDEN_MATH_SYM"),
            ("from fractions import gcd\n", "AST_FORBIDDEN_FRACTIONS_SYM"),
            ("assert True\n", "AST_BARE_ASSERT"),
            ("x = 1 / 2\n", "AST_DIV_FORBIDDEN"),
            ("x = 1 // 2\n", "AST_FLOORDIV_FORBIDDEN"),
            ("x = 5 % 2\n", "AST_MOD_FORBIDDEN"),
            ("from fractions import Fraction\nx = '%.2f' % Fraction(1, 3)\n", "AST_MOD_FORBIDDEN"),
            ("x = 2 ** 3\n", "AST_POW_FORBIDDEN"),
            ("x = f'{1:.3f}'\n", "AST_FORMAT_SPEC_FORBIDDEN"),
            ("x = 1.5\n", "AST_FLOAT_LITERAL"),
            ("x = 1j\n", "AST_FLOAT_LITERAL"),
            ("f = float\nx = f(1)\n", "AST_FORBIDDEN_NAME"),
            ("from fractions import Fraction\nx = Fraction.from_float(1)\n", "AST_FORBIDDEN_ATTR"),
            ("x = a.__truediv__(b)\n", "AST_FORBIDDEN_ATTR"),
            ("x = (1).__float__()\n", "AST_FORBIDDEN_ATTR"),
            ("x = (1).__complex__()\n", "AST_FORBIDDEN_ATTR"),
            ("import fractions\nx = fractions.__dict__\n", "AST_FORBIDDEN_ATTR"),
            ("import fractions\nx = fractions.__dict__['Fraction']('0.5')\n", "AST_INDIRECT_CALL"),
            ("x = __builtins__['float']\n", "AST_FORBIDDEN_NAME"),
            ("x = __builtins__['float']('1e308')\n", "AST_INDIRECT_CALL"),
            ("from fractions import Fraction\nx = type(Fraction(1, 1))('1.5')\n", "AST_INDIRECT_CALL"),
            ("from fractions import Fraction\nx = [Fraction][0]('0.5')\n", "AST_INDIRECT_CALL"),
            ("from fractions import Fraction\nlst = [Fraction]\n", "AST_FRACTION_CONTAINER"),
            ("from fractions import Fraction\nx = '{:.2f}'.format(Fraction(1, 3))\n", "AST_FORBIDDEN_CALL"),
            ("from fractions import Fraction\nx = format(Fraction(1, 3), '.2f')\n", "AST_FORBIDDEN_CALL"),
            ("x = '{a}'.format_map({'a': 1})\n", "AST_FORBIDDEN_CALL"),
            ("import math as m\nx = m.log(2)\n", "AST_FORBIDDEN_MATH_ATTR"),
            ("import math\nM = math\nx = M.sqrt(2)\n", "AST_FORBIDDEN_MATH_ATTR"),
            ("import math\nM: object = math\nx = M.sqrt(2)\n", "AST_FORBIDDEN_MATH_ATTR"),
            ("import math\n(M := math)\nx = M.sqrt(2)\n", "AST_FORBIDDEN_MATH_ATTR"),
            ("import math\nx = vars(math)\n", "AST_FORBIDDEN_CALL"),
            ("import math\nx = vars(math)['sqrt'](2)\n", "AST_INDIRECT_CALL"),
            ("x = getattr(a, 'b')\n", "AST_FORBIDDEN_CALL"),
            ("x = a.float()\n", "AST_FORBIDDEN_CALL"),
            ("from fractions import Fraction\ns = '0.5'\nx = Fraction(s)\n", "AST_FRACTION_ARITY"),
            ("from fractions import Fraction\nF = Fraction\nG = F\nx = G('0.5', 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("import fractions\nF = fractions.Fraction\nx = F('0.5', 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("import fractions\nF: object = fractions.Fraction\nx = F('0.5', 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = (F := Fraction)('0.5', 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("import fractions\nx = (F := fractions.Fraction)('0.5', 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction as F\nx = F('0.5', 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction(numerator=1)\n", "AST_FRACTION_KW"),
            ("from fractions import Fraction\nx = Fraction()\n", "AST_FRACTION_ARITY"),
            ("from fractions import Fraction\nx = Fraction(1, 2, 3)\n", "AST_FRACTION_ARITY"),
            ("from fractions import Fraction\nx = Fraction('1/3', 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction(True, 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction(1 + 'a', 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction('a' + 1, 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction(a.real, 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction(foo(1), 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction(1 if a else 'b', 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction('a' if a else 1, 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction([1], 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction(1 << 2, 1)\n", "AST_FRACTION_ARG_UNSAFE"),
            ("from fractions import Fraction\nx = Fraction(~1, 1)\n", "AST_FRACTION_ARG_UNSAFE"),
        )
        for src, code in bad_ast_cases:
            self._assert_err(code, mod.verify_pure_q_ast, src)

    def test_02_strict_json_privacy_and_pollution_guards(self) -> None:
        self.assertEqual(mod.check_nonempty_str("ok", "x"), "ok")
        for bad in (123, "", "   "):
            self._assert_err("THEATER_EMPTY_SPEC", mod.check_nonempty_str, bad, "x")

        self.assertEqual(mod.loads_strict_json_bytes(b'{"a":[1,true,null,"s"]}\n', "ok"), {"a": [1, True, None, "s"]})
        self.assertEqual(mod.MAX_JSON_DEPTH, 32)
        deep32 = b"[" * mod.MAX_JSON_DEPTH + b"1" + b"]" * mod.MAX_JSON_DEPTH
        self.assertIsInstance(mod.loads_strict_json_bytes(deep32, "ok32"), list)
        str_braces = b'{"s":"' + b"{" * 40 + b'\\"{[\\\\"}'
        self.assertEqual(mod.loads_strict_json_bytes(str_braces, "braces")["s"][:2], "{{")
        with mock.patch.object(mod.json, "loads", side_effect=AssertionError("pre-parse depth check must reject before json.loads")):
            self._assert_err(
                "JSON_DEPTH",
                mod.loads_strict_json_bytes,
                b"[" * (mod.MAX_JSON_DEPTH + 1) + b"1" + b"]" * (mod.MAX_JSON_DEPTH + 1),
                "deep33",
            )
        with mock.patch.object(mod.json, "loads", side_effect=RecursionError("deep")):
            self._assert_err("JSON_DEPTH", mod.loads_strict_json_bytes, b'{"a":1}', "rec")
        mod.validate_json_tree_no_floats(0, max_depth=0)
        self._assert_err("JSON_DEPTH", mod.validate_json_tree_no_floats, [1], max_depth=0)
        self._assert_err("JSON_DEPTH", mod.validate_json_tree_no_floats, {"k": 1}, max_depth=0)
        self._assert_err("FLOAT_FORBIDDEN", mod.validate_json_tree_no_floats, {"x": 1.25})
        self._assert_err("BAD_KEY", mod.validate_json_tree_no_floats, {1: "x"})
        self._assert_err("BAD_JSON_TYPE", mod.validate_json_tree_no_floats, {"t": (1, 2)})

        self._assert_err("UTF8_BOM_FORBIDDEN", mod.loads_strict_json_bytes, b"\xef\xbb\xbf{}", "bom")
        self._assert_err("CR_FORBIDDEN", mod.loads_strict_json_bytes, b"{}\r\n", "cr")
        self._assert_err("BAD_UTF8", mod.loads_strict_json_bytes, b"\xff\xfe", "utf8")
        self._assert_err("DUPLICATE_JSON_KEY", mod.loads_strict_json_bytes, b'{"a":1,"a":2}', "dup")
        self._assert_err("FLOAT_FORBIDDEN", mod.loads_strict_json_bytes, b'{"a":1.5}', "flt")
        self._assert_err("NONFINITE_JSON", mod.loads_strict_json_bytes, b'{"a":NaN}', "nan")
        self._assert_err("BAD_JSON", mod.loads_strict_json_bytes, b"{bad", "bad")
        self.assertEqual(mod._parse_bounded_int("9" * mod.MAX_JSON_INT_DIGITS), int("9" * mod.MAX_JSON_INT_DIGITS))
        self._assert_err("JSON_INT_TOO_LARGE", mod.loads_strict_json_bytes, b'{"x": ' + b"9" * (mod.MAX_JSON_INT_DIGITS + 1) + b"}", "big1025")
        self._assert_err("JSON_INT_TOO_LARGE", mod.loads_strict_json_bytes, b'{"x": ' + b"9" * 4400 + b"}", "big4400")

        mod.assert_clean_public_text("clean public text about Foundation-0/continuum")
        self._assert_err("BAD_TEXT", mod.assert_clean_public_text, 123)
        for bad_priv in ("aska-digital", "aletheia-corpus", chr(47) + "home" + chr(47) + "u"):
            self._assert_err("PRIVACY_VIOLATION", mod.assert_clean_public_text, bad_priv)

        polluted = "prompt mentioning " + mod.FORBIDDEN_MODEL_TOKENS[0]
        mod.assert_clean_public_text(polluted, check_model_pollution=False)
        self._assert_err("MODEL_POLLUTION", mod.assert_clean_public_text, polluted, True)

        mod.assert_variation_c_label_stripped({"seats": [{"title": "Schur Complement"}]})
        self._assert_err("VARIATION_C_LABEL_LEAK", mod.assert_variation_c_label_stripped, {"seats": [{"title": "Al-Biruni lift"}]})

    def test_03_sandbox_ast_audit_and_anti_theater_gate(self) -> None:
        good_code = (
            "import fractions\n"
            "from fractions import Fraction\n"
            "from math import gcd, isqrt\n"
            "from itertools import product\n"
            "def check_case(case):\n"
            "    return (\n"
            "        gcd(case['a'], case['b']) >= 1\n"
            "        and isqrt(4) == 2\n"
            "        and len(list(product([1]))) == 1\n"
            "        and sum(x for x in [case['a']]) == case['a']\n"
            "        and all(y >= 0 for y in [case['b']])\n"
            "    )\n"
        )
        mod.audit_conjecture_ast(good_code)

        for bad_code, exp_code in (
            ("def check_case(case):\n    return 1 +", "SANDBOX_SYNTAX_ERROR"),
            ("def check_case(case):\n    return case['a'] < 3.14\n", "SANDBOX_FLOAT_FORBIDDEN"),
            ("def check_case(case):\n    return case['a'] == 1j\n", "SANDBOX_FLOAT_FORBIDDEN"),
            ("def check_case(case):\n    return case['a'] / 2 > 0\n", "SANDBOX_DIV_FORBIDDEN"),
            ("def check_case(case):\n    s = f\"{case['a']:.3f}\"\n    return s == '1.000'\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("def check_case(case):\n    assert case['a'] == 1\n    return True\n", "SANDBOX_BARE_ASSERT"),
            ("async def f(): pass\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("async def f():\n    async for x in a:\n        pass\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("async def f():\n    async with a:\n        pass\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("def f():\n    yield 1\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("def f():\n    yield from [1]\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("def check_case(case):\n    gen = (x for x in [case['a']])\n    return list(gen)[0] == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("def check_case(case):\n    return list((g := (x for x in [case['a']])))[0] == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("def f(g):\n    return 1\ndef check_case(case):\n    return f((x for x in [case['a']])) == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("def check_case(case):\n    return (lambda g: 1)((x for x in [case['a']])) == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("def check_case(case):\n    return sum((x for x in [case['a']]), start=(y for y in [1])) == 1\n", "SANDBOX_FORBIDDEN_SYNTAX"),
            ("def sum(g):\n    return 1\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_NAME"),
            ("def f(sum):\n    return sum\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_NAME"),
            ("def check_case(case):\n    sum = 1\n    return case['a'] == sum\n", "SANDBOX_FORBIDDEN_NAME"),
            ("def check_case(case):\n    return _exact_div(case['a'], 1) == 1\n", "SANDBOX_FORBIDDEN_NAME"),
            ("import os\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_IMPORT"),
            ("from os import system\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_IMPORT"),
            ("from . import fractions\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_IMPORT"),
            ("from math import log\ndef check_case(case):\n    return case['a'] == 1\n", "SANDBOX_FORBIDDEN_IMPORT"),
            ("def check_case(case):\n    return case.__class__ == dict\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return list(x.gi_frame for x in [case])[0] == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.f_back == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.f_globals == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.cr_frame == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.ag_frame == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.tb_frame == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.co_code == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.func_globals == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.im_func == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("from fractions import Fraction\ndef check_case(case):\n    return Fraction.from_float(case['a']) == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("from fractions import Fraction\ndef check_case(case):\n    return Fraction.from_decimal(case['a']) == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.modules == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return case.builtins == 1\n", "SANDBOX_FORBIDDEN_ATTR"),
            ("def check_case(case):\n    return eval('1') == case['a']\n", "SANDBOX_FORBIDDEN_NAME"),
            ("def check_case(case):\n    m = __builtins__['__import__']('math')\n    return m.log(case['a']) > 0\n", "SANDBOX_FORBIDDEN_NAME"),
            ("def check_case(case):\n    f = float\n    return f(case['a']) > 0\n", "SANDBOX_FORBIDDEN_NAME"),
            ("def other_fn(case):\n    return case['a'] == 1\n", "THEATER_MISSING_ENTRYPOINT"),
            ("def check_case(a, b):\n    return a == b\n", "THEATER_BAD_SIGNATURE"),
            ("def check_case(case):\n    return 1 == 1\n", "THEATER_TRIVIAL_ORACLE"),
            ("def check_case(case):\n    return bool(case)\n", "THEATER_TRIVIAL_ORACLE"),
        ):
            self._assert_err(exp_code, mod.audit_conjecture_ast, bad_code)

        meta1 = mod.validate_seminar_turn(_make_valid_turn(round_num=1))
        self.assertEqual(meta1["turn_id"], "R1-SEAT-1")
        meta0 = mod.validate_seminar_turn(_make_valid_turn(turn_id="R1-S0", round_num=1, seat_id="SEAT-0", target="SEAT-1"))
        self.assertEqual(meta0["interpositions_count"], 1)
        mod.validate_seminar_turn(_make_valid_turn(round_num=mod.MAX_ROUND_NUM, target="SEAT-1"))

        self._assert_err("THEATER_BAD_TURN", mod.validate_seminar_turn, "not_dict")
        for bad_r in (True, False, 0, mod.MAX_ROUND_NUM + 1, "bad"):
            t = _make_valid_turn()
            t["round_num"] = bad_r
            self._assert_err("THEATER_BAD_ROUND", mod.validate_seminar_turn, t)
        for field in ("corpus_anchor", "composition_or_challenge", "executable_conjecture"):
            t = _make_valid_turn()
            t[field] = "prose_only"
            self._assert_err("THEATER_MISSING_FIELD", mod.validate_seminar_turn, t)
        t_mode = _make_valid_turn()
        t_mode["composition_or_challenge"]["mode"] = "monologue"
        self._assert_err("THEATER_BAD_MODE", mod.validate_seminar_turn, t_mode)
        self._assert_err("THEATER_SELF_ECHO", mod.validate_seminar_turn, _make_valid_turn(round_num=1, seat_id="SEAT-1", target="SEAT-1"))
        t_kind = _make_valid_turn()
        t_kind["executable_conjecture"]["kind"] = "prose_essay"
        self._assert_err("THEATER_BAD_KIND", mod.validate_seminar_turn, t_kind)

        mod.validate_seminar_turn(_make_valid_turn(cases=[{"a": 1, "b": 1}] * mod.MAX_TEST_CASES))
        for bad_cases in ("bad", [], [{"a": 1, "b": 1}] * (mod.MAX_TEST_CASES + 1), ["not_dict"], [{}]):
            self._assert_err("THEATER_EMPTY_SPEC", mod.validate_seminar_turn, _make_valid_turn(cases=bad_cases))  # type: ignore[arg-type]

        t_front = _make_valid_turn()
        t_front["target_frontier"] = "unknown/repo"
        self._assert_err("INVALID_FRONTIER", mod.validate_seminar_turn, t_front)

        for bad_interps in (
            "not_list",
            [],
            ["not_dict"],
            [{"id": "x", "org": "Foundation-0", "gate_status": "EXACT_OPERATOR_VERIFIED", "shared_operators": "not_list"}],
            [{"id": "x", "org": "Foundation-0", "gate_status": "EXACT_OPERATOR_VERIFIED", "shared_operators": []}],
        ):
            self._assert_err(
                "THEATER_MISSING_INTERPOSITIONS",
                mod.validate_seminar_turn,
                _make_valid_turn(seat_id="SEAT-0", target="SEAT-1", interpositions=bad_interps),  # type: ignore[arg-type]
            )

    def test_04_isolated_referee_interpose_and_dag_guards(self) -> None:
        good_conj = _make_valid_turn()["executable_conjecture"]
        self.assertEqual(mod.run_isolated_referee(good_conj, timeout_sec=1)["status"], "PASS_WITNESS")
        self.assertEqual(mod.run_isolated_referee(good_conj, timeout_sec=30)["status"], "PASS_WITNESS")

        fail_conj = copy.deepcopy(good_conj)
        fail_conj["test_cases"] = [{"a": 3, "b": 3}, {"a": 3, "b": 4}]
        v_fail = mod.run_isolated_referee(fail_conj)
        self.assertEqual(v_fail["status"], "MINIMAL_COUNTEREXAMPLE")
        self.assertEqual(v_fail["failing_case_index"], 1)

        div0_conj = copy.deepcopy(good_conj)
        div0_conj["code"] = "def check_case(case):\n    return (1 // case['a']) == 1\n"
        div0_conj["test_cases"] = [{"a": 0}]
        self.assertIn("ZeroDivisionError", mod.run_isolated_referee(div0_conj)["failure_reason"])

        nonbool_conj = copy.deepcopy(good_conj)
        nonbool_conj["code"] = "def check_case(case):\n    return 1 if case['a'] == 1 else 0\n"
        nonbool_conj["test_cases"] = [{"a": 1}]
        self.assertEqual(mod.run_isolated_referee(nonbool_conj)["failure_reason"], "NON_BOOL_RETURN:int")

        # Runtime defense-in-depth: int / int even with Fraction imported MUST fail closed (never PASS_WITNESS)
        int_div_conj = copy.deepcopy(good_conj)
        int_div_conj["code"] = "from fractions import Fraction\ndef check_case(case):\n    return (case['a'] / 2) > 0\n"
        int_div_conj["test_cases"] = [{"a": 3}]
        v_idiv = mod.run_isolated_referee(int_div_conj)
        self.assertEqual(v_idiv["status"], "MINIMAL_COUNTEREXAMPLE")
        self.assertIn("FLOAT_DIVISION_FORBIDDEN", v_idiv["failure_reason"])

        neg_pow_conj = copy.deepcopy(good_conj)
        neg_pow_conj["code"] = "def check_case(case):\n    return (case['a'] ** -1) > 0\n"
        neg_pow_conj["test_cases"] = [{"a": 2}]
        v_npow = mod.run_isolated_referee(neg_pow_conj)
        self.assertEqual(v_npow["status"], "MINIMAL_COUNTEREXAMPLE")
        self.assertIn("FLOAT_POW_FORBIDDEN", v_npow["failure_reason"])

        frac_str_conj = copy.deepcopy(good_conj)
        frac_str_conj["code"] = "from fractions import Fraction\ndef check_case(case):\n    return Fraction('0.5') > case['a']\n"
        frac_str_conj["test_cases"] = [{"a": 0}]
        v_fstr = mod.run_isolated_referee(frac_str_conj)
        self.assertEqual(v_fstr["status"], "MINIMAL_COUNTEREXAMPLE")
        self.assertIn("FRACTION_EXACT_INT_ONLY", v_fstr["failure_reason"])

        # Exact Delta-2 MED-1 gi_frame.f_back.f_back.f_globals exploit probe (AST + runtime defense-in-depth)
        exploit_code = (
            "def check_case(case):\n"
            "    box = []\n"
            "    gen = (box[0].gi_frame.f_back.f_back.f_globals for _ in [1])\n"
            "    box.append(gen)\n"
            "    globs = list(gen)[0]\n"
            "    os_mod = globs['sys'].modules['os']\n"
            "    return case['x'] == len(os_mod.uname().sysname)\n"
        )
        exploit_conj = {
            "conjecture_id": "EXPLOIT-GI-FRAME-PROBE",
            "kind": "python_exact_q",
            "claim_summary": "Probe gi_frame.f_back.f_back.f_globals sandbox escape",
            "code": exploit_code,
            "test_cases": [{"x": 5}],
        }
        self._assert_err("SANDBOX_FORBIDDEN_ATTR", mod.audit_conjecture_ast, exploit_code)
        self._assert_err("SANDBOX_FORBIDDEN_ATTR", mod.run_isolated_referee, exploit_conj)
        direct_proc = subprocess.run(
            [sys.executable, "-I", "-B", "-c", mod._ISOLATED_RUNNER_SOURCE],
            input=json.dumps({"code": exploit_code, "test_cases": [{"x": 5}]}),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(direct_proc.returncode, 0)
        direct_out = json.loads(direct_proc.stdout)
        self.assertEqual(direct_out["status"], "MINIMAL_COUNTEREXAMPLE")
        self.assertIn("KeyError", direct_out["failure_reason"])

        self._assert_err("THEATER_MISSING_FIELD", mod.run_isolated_referee, "bad")
        for bad_to in (True, 0, 31):
            self._assert_err("BAD_TIMEOUT", mod.run_isolated_referee, good_conj, timeout_sec=bad_to)
        for bad_cases in ("bad", [], [{"a": 1, "b": 1}] * (mod.MAX_TEST_CASES + 1)):
            c = copy.deepcopy(good_conj)
            c["test_cases"] = bad_cases
            self._assert_err("THEATER_EMPTY_SPEC", mod.run_isolated_referee, c)

        with mock.patch.object(mod.subprocess, "run", side_effect=mod.subprocess.TimeoutExpired(cmd="py", timeout=1)):
            self.assertEqual(mod.run_isolated_referee(good_conj, timeout_sec=1)["status"], "REFEREE_TIMEOUT")
        with mock.patch.object(mod.subprocess, "run", return_value=mock.Mock(returncode=1, stdout="")):
            self._assert_err("REFEREE_EXEC_ERROR", mod.run_isolated_referee, good_conj)
        with mock.patch.object(mod.subprocess, "run", return_value=mock.Mock(returncode=0, stdout="not_json")):
            self._assert_err("BAD_JSON", mod.run_isolated_referee, good_conj)

        # Local interpose bounds & matching
        r1 = mod.run_local_interpose("Probe", "Schur Cayley CRT", top_k=1)
        self.assertEqual(r1["matched_count"], 1)
        r12 = mod.run_local_interpose("Probe", "Schur Cayley CRT stereographic", top_k=12)
        self.assertEqual(r12["matched_count"], 4)
        r0 = mod.run_local_interpose("Probe", "unrelated xyz token", top_k=3)
        self.assertEqual(r0["matched_count"], 0)
        for bad_k in (True, 0, 13):
            self._assert_err("BAD_QUERY", mod.run_local_interpose, "Probe", "Schur", top_k=bad_k)

        # DAG evaluator guards (including pre-sort round_num/turn validation for M-2)
        t1 = _make_valid_turn(turn_id="R1-A", round_num=1, seat_id="SEAT-1", target="SEAT-2")
        self._assert_err("BAD_VARIATION", mod.evaluate_seminar_session, "S1", "bogus", "aletheia", "T1", [t1])
        self._assert_err("BAD_CHAIR", mod.evaluate_seminar_session, "S1", "scholars", "bogus", "T1", [t1])
        for bad_turns in ("not_seq", []):
            self._assert_err("BAD_SESSION", mod.evaluate_seminar_session, "S1", "scholars", "aletheia", "T1", bad_turns)
        self._assert_err("THEATER_BAD_ROUND", mod.evaluate_seminar_session, "S1", "scholars", "aletheia", "T1", [{"round_num": "bad", "turn_id": "t1"}])
        self._assert_err("THEATER_BAD_ROUND", mod.evaluate_seminar_session, "S1", "scholars", "aletheia", "T1", [_make_valid_turn(round_num=True)])
        self._assert_err("THEATER_BAD_TURN", mod.evaluate_seminar_session, "S1", "scholars", "aletheia", "T1", ["not_dict"])  # type: ignore[list-item]

        pass_v = {"conjecture_id": "C", "status": "PASS_WITNESS", "passed_cases": 1, "total_cases": 1, "failing_case_index": None, "minimal_counterexample": None, "failure_reason": None, "verdict_sha256": "a" * 64}
        cex_v = {"conjecture_id": "C", "status": "MINIMAL_COUNTEREXAMPLE", "passed_cases": 0, "total_cases": 1, "failing_case_index": 0, "minimal_counterexample": {"a": 1}, "failure_reason": "PREDICATE_RETURNED_FALSE", "verdict_sha256": "b" * 64}

        with mock.patch.object(mod, "run_isolated_referee", return_value=pass_v):
            self._assert_err("DUPLICATE_TURN_ID", mod.evaluate_seminar_session, "S1", "scholars", "aletheia", "T1", [t1, copy.deepcopy(t1)])
            t1_same = _make_valid_turn(turn_id="R1-B", round_num=1, seat_id="SEAT-2", target="R1-A")
            self._assert_err("DAG_NON_CAUSAL", mod.evaluate_seminar_session, "S1", "scholars", "aletheia", "T1", [t1, t1_same])

            s_flat = mod.evaluate_seminar_session("S-FLAT", "scholars", "none", "T1", [t1])
            self.assertFalse(s_flat["s150_g2_dynamic_compounding_passed"])
            self.assertFalse(s_flat["s150_g5_bidirectional_pollination_passed"])

            t2_s0 = _make_valid_turn(turn_id="R2-S0", round_num=2, seat_id="SEAT-0", target="R1-A")
            s_h2m = mod.evaluate_seminar_session("S-H2M", "scholars", "aletheia", "T1", [t1, t2_s0])
            self.assertEqual(len(s_h2m["historical_to_modern_edges"]), 1)
            self.assertEqual(len(s_h2m["modern_to_historical_edges"]), 0)
            self.assertFalse(s_h2m["s150_g2_dynamic_compounding_passed"])
            self.assertFalse(s_h2m["s150_g5_bidirectional_pollination_passed"])

            t2_same = _make_valid_turn(turn_id="R2-A", round_num=2, seat_id="SEAT-1", target="R1-A")
            s_same = mod.evaluate_seminar_session("S-SAME", "scholars", "none", "T1", [t1, t2_same])
            self.assertEqual(len(s_same["cross_seat_compositions"]), 0)
            self.assertEqual(len(s_same["counterexample_repairs"]), 0)

            s_reordered = mod.evaluate_seminar_session("S-REORDER", "scholars", "none", "T1", [t2_same, t1])
            self.assertEqual([r["turn_id"] for r in s_reordered["turn_records"]], ["R1-A", "R2-A"])
            self.assertEqual(s_reordered["max_dag_depth"], 2)

        with mock.patch.object(mod, "run_isolated_referee", return_value=cex_v):
            t2_cex = _make_valid_turn(turn_id="R2-B", round_num=2, seat_id="SEAT-2", target="R1-A")
            s_cex = mod.evaluate_seminar_session("S-CEX", "scholars", "none", "T1", [t1, t2_cex])
            self.assertEqual(len(s_cex["counterexample_repairs"]), 0)
            self.assertEqual(len(s_cex["cross_seat_compositions"]), 0)

    def test_05_packs_certificate_tamper_and_cli(self) -> None:
        for var, ch, expected_seats in (
            ("scholars", "aletheia", 7),
            ("scholars", "none", 6),
            ("civilizations", "aletheia", 7),
            ("operators", "aletheia", 7),
            ("operators", "none", 6),
            ("single", "none", 1),
        ):
            pack = mod.build_variation_pack(var, chair=ch)
            self.assertEqual(pack["seat_count"], expected_seats)
        self._assert_err("BAD_VARIATION", mod.build_variation_pack, "invalid")
        self._assert_err("BAD_CHAIR", mod.build_variation_pack, "scholars", chair="invalid")

        bundle = mod.build_pilot1_prompt_bundle(mod.build_variation_pack("scholars", chair="aletheia"))
        self.assertEqual(bundle["prompt_count"], 21)
        for bad_pack in ("bad", {"seats": "not_list"}):
            self._assert_err("BAD_PACK", mod.build_pilot1_prompt_bundle, bad_pack)

        cert = mod.build_self_test_certificate()
        mod.validate_certificate_payload(cert)
        self.assertTrue(cert["all_passed"])
        self.assertEqual(cert["dry_run_session"]["max_dag_depth"], 3)
        self.assertEqual(cert["dry_run_session"]["pass_witness_count"], 4)
        self.assertEqual(cert["dry_run_session"]["minimal_counterexample_count"], 1)
        self.assertTrue(cert["dry_run_session"]["s150_g2_dynamic_compounding_passed"])
        self.assertTrue(cert["dry_run_session"]["s150_g5_bidirectional_pollination_passed"])

        self._assert_err("BAD_CERT_TYPE", mod.validate_certificate_payload, [])
        bad_k = copy.deepcopy(cert)
        bad_k["extra"] = 1
        self._assert_err("BAD_CERT_KEYS", mod.validate_certificate_payload, bad_k)

        for field, val, code in (
            ("schema", "bad", "BAD_SCHEMA"),
            ("energy_power_status", "CLAIMED", "BAD_ENERGY"),
            ("zero_floats", False, "BAD_ZERO_FLOATS"),
            ("pure_q_ast_clean", False, "BAD_AST_FLAG"),
            ("all_passed", False, "GATES_NOT_ALL_PASSED"),
            ("payload_sha256", 123, "PAYLOAD_SHA_MISMATCH"),
            ("payload_sha256", "0" * 64, "PAYLOAD_SHA_MISMATCH"),
            ("certificate_sha256", 123, "CERT_SHA_MISMATCH"),
            ("certificate_sha256", "0" * 64, "CERT_SHA_MISMATCH"),
        ):
            t = copy.deepcopy(cert)
            t[field] = val
            self._assert_err(code, mod.validate_certificate_payload, t)

        # CLI roundtrip reusing freshly built cert for fast dispatch
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cp = tmp.joinpath("cert.json")
            dp = tmp.joinpath("dossiers")

            with mock.patch.object(mod, "build_self_test_certificate", return_value=cert):
                buf_w = io.StringIO()
                with mock.patch("sys.stdout", buf_w):
                    self.assertEqual(mod.main(["--write-cert", str(cp)]), 0)
                self.assertEqual(json.loads(buf_w.getvalue())["status"], "WRITTEN")

                buf_c = io.StringIO()
                with mock.patch("sys.stdout", buf_c):
                    self.assertEqual(mod.main(["--check-cert", str(cp)]), 0)
                self.assertEqual(json.loads(buf_c.getvalue())["status"], "PASS")

                sym_p = tmp.joinpath("sym_cert.json")
                sym_p.symlink_to(cp)
                self._assert_err("SYMLINK_FORBIDDEN", mod.check_certificate_file, sym_p)
                err_sym = io.StringIO()
                with mock.patch("sys.stderr", err_sym):
                    self.assertEqual(mod.main(["--check-cert", str(sym_p)]), 2)
                self.assertIn("SYMLINK_FORBIDDEN", err_sym.getvalue())
                err_sym_w = io.StringIO()
                with mock.patch("sys.stderr", err_sym_w):
                    self.assertEqual(mod.main(["--write-cert", str(sym_p)]), 2)
                self.assertIn("SYMLINK_FORBIDDEN", err_sym_w.getvalue())

                big_p = tmp.joinpath("big4400.json")
                big_p.write_text('{"x":' + "9" * 4400 + "}\n", encoding="utf-8")
                err_big = io.StringIO()
                with mock.patch("sys.stderr", err_big):
                    self.assertEqual(mod.main(["--check-cert", str(big_p)]), 2)
                self.assertIn("JSON_INT_TOO_LARGE", err_big.getvalue())

                # Grandparent symlink, FIFO, size cap, ELOOP, & os.read OSError coverage
                real_gp = tmp.joinpath("real_gp")
                real_gp.joinpath("sub").mkdir(parents=True)
                real_gp.joinpath("sub", "c.json").write_bytes(cp.read_bytes())
                gp_sym = tmp.joinpath("gp_sym")
                gp_sym.symlink_to(real_gp)
                self._assert_err("SYMLINK_FORBIDDEN", mod.read_regular_file_bytes, gp_sym.joinpath("sub", "c.json"))
                fifo_p = tmp.joinpath("pipe.json")
                mod.os.mkfifo(fifo_p)
                self._assert_err("NOT_REGULAR_FILE", mod.read_regular_file_bytes, fifo_p)
                small_p = tmp.joinpath("small.json")
                small_p.write_bytes(b"{" + b" " * 100 + b"}")
                self.assertEqual(len(mod.read_regular_file_bytes(small_p, max_bytes=102)), 102)
                with mock.patch.object(mod.os, "read", side_effect=AssertionError("st_size must fail before read")):
                    self._assert_err("FILE_TOO_LARGE", mod.read_regular_file_bytes, small_p, max_bytes=64)
                fake_st = mod.os.stat(small_p)
                with mock.patch.object(mod.os, "fstat", return_value=type("S", (), {"st_mode": fake_st.st_mode, "st_size": 10})()):
                    self._assert_err("FILE_TOO_LARGE", mod.read_regular_file_bytes, small_p, max_bytes=64)
                with mock.patch.object(mod.os, "open", side_effect=OSError(mod.errno.ELOOP, "loop")):
                    self._assert_err("SYMLINK_FORBIDDEN", mod.read_regular_file_bytes, small_p)
                with mock.patch.object(mod.os, "open", side_effect=OSError(mod.errno.EACCES, "denied")):
                    self._assert_err("READ_ERROR", mod.read_regular_file_bytes, small_p)
                with mock.patch.object(mod.os, "read", side_effect=OSError(mod.errno.EIO, "io error")):
                    self._assert_err("READ_ERROR", mod.read_regular_file_bytes, small_p)
                    err_io = io.StringIO()
                    with mock.patch("sys.stderr", err_io):
                        self.assertEqual(mod.main(["--check-cert", str(small_p)]), 2)
                    self.assertIn("READ_ERROR", err_io.getvalue())

                forged = copy.deepcopy(cert)
                forged["dry_run_session"]["pass_witness_count"] = 99
                p = {k: v for k, v in forged.items() if k not in ("payload_sha256", "certificate_sha256")}
                forged["payload_sha256"] = hashlib.sha256(mod.canonical_json_bytes(p)).hexdigest()
                b = {k: v for k, v in forged.items() if k != "certificate_sha256"}
                forged["certificate_sha256"] = hashlib.sha256(mod.canonical_json_bytes(b)).hexdigest()
                fp = tmp.joinpath("forged.json")
                fp.write_text(json.dumps(forged) + "\n", encoding="utf-8")
                self._assert_err("LIVE_RECOMPUTE_MISMATCH", mod.check_certificate_file, fp)

                err = io.StringIO()
                with mock.patch("sys.stderr", err):
                    self.assertEqual(mod.main(["--check-cert", str(tmp.joinpath("missing.json"))]), 2)
                self.assertIn("MISSING_CERT", err.getvalue())

                buf_s = io.StringIO()
                with mock.patch("sys.stdout", buf_s):
                    self.assertEqual(mod.main(["--self-test"]), 0)
                self.assertEqual(json.loads(buf_s.getvalue())["certificate_sha256"], cert["certificate_sha256"])

            buf_d = io.StringIO()
            with mock.patch("sys.stdout", buf_d):
                self.assertEqual(mod.main(["--emit-dossiers", str(dp)]), 0)
            self.assertEqual(len(json.loads(buf_d.getvalue())["files"]), 8)
            sym_d = tmp.joinpath("sym_dossiers")
            sym_d.symlink_to(dp)
            self._assert_err("SYMLINK_FORBIDDEN", mod.emit_all_dossiers, sym_d)

            buf_v = io.StringIO()
            with mock.patch("sys.stdout", buf_v):
                self.assertEqual(mod.main(["--variation", "operators", "--chair", "aletheia"]), 0)
            self.assertEqual(json.loads(buf_v.getvalue())["seat_count"], 7)

            with mock.patch.object(mod, "build_self_test_certificate", return_value=cert):
                err_io_w = io.StringIO()
                with mock.patch("sys.stderr", err_io_w):
                    self.assertEqual(mod.main(["--write-cert", str(tmp.joinpath("missing_dir", "cert.json"))]), 2)
                self.assertEqual(json.loads(err_io_w.getvalue())["error_code"], "IO_ERROR")

            # M-1: UnicodeDecodeError in build_self_test_certificate() and main() must exit RC=2 with structured JSON
            with mock.patch.object(mod, "read_regular_file_bytes", return_value=b"\xff\xfe"):
                self._assert_err("BAD_UTF8", mod.build_self_test_certificate)
                err_utf8 = io.StringIO()
                with mock.patch("sys.stderr", err_utf8):
                    self.assertEqual(mod.main([]), 2)
                self.assertNotIn("Traceback", err_utf8.getvalue())
                self.assertEqual(json.loads(err_utf8.getvalue())["error_code"], "BAD_UTF8")

            with mock.patch.object(mod, "build_self_test_certificate", side_effect=UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad")):
                err_main_utf8 = io.StringIO()
                with mock.patch("sys.stderr", err_main_utf8):
                    self.assertEqual(mod.main([]), 2)
                self.assertNotIn("Traceback", err_main_utf8.getvalue())
                self.assertEqual(json.loads(err_main_utf8.getvalue())["error_code"], "BAD_UTF8")


if __name__ == "__main__":
    unittest.main()
