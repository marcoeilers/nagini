# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class MyClass:
    def __init__(self) -> None:
        self.x = 0

def f1(m: MyClass) -> None:
    Requires(Acc(m.x) and m.x == 0)
    Ensures(Acc(m.x))
    Ensures(m.x == 1)
    while True:
        Invariant(Acc(m.x) and m.x == 0)
        try:
            break
        finally:
            m.x = 1


def f2(m: MyClass) -> None:
    Requires(Acc(m.x) and m.x == 0)
    Ensures(Acc(m.x))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(m.x == 0)
    while True:
        Invariant(Acc(m.x) and m.x == 0)
        try:
            break
        finally:
            m.x = 1


def f3(m: MyClass) -> None:
    Requires(Acc(m.x) and m.x == 0)
    Ensures(Acc(m.x))
    while True:
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(Acc(m.x) and m.x == 0)
        try:
            continue
        finally:
            m.x = 1


def f4(m: MyClass) -> None:
    Requires(Acc(m.x) and m.x == 0)
    Ensures(Acc(m.x))
    l = 0
    while True:
        Invariant(Acc(m.x) and m.x == l)
        l += 1
        try:
            continue
        finally:
            m.x += 1


def f5(m: MyClass) -> None:
    Requires(Acc(m.x) and m.x == 0)
    Ensures(Acc(m.x))
    l = 0
    while True:
        Invariant(Acc(m.x) and m.x == l)
        try:
            try:
                continue
            finally:
                m.x += 1
        finally:
            l += 1


def f6(m: MyClass) -> None:
    Requires(Acc(m.x) and m.x == 0)
    Ensures(Acc(m.x))
    l = 0
    while True:
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(Acc(m.x) and m.x == 0)
        try:
            try:
                continue
            finally:
                m.x += 1
        finally:
            l += 1


def f7(m: MyClass) -> int:
    Requires(Acc(m.x) and m.x == 0)
    Ensures(Acc(m.x) and Result() == m.x + 1)
    l = 0
    try:
        while True:
            Invariant(Acc(m.x) and m.x == l)
            try:
                try:
                    break
                finally:
                    m.x += 1
            finally:
                l += 1
    finally:
        l += 1
    return l


def f8(m: MyClass) -> int:
    Requires(Acc(m.x) and m.x == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(m.x) and Result() == m.x)
    l = 0
    try:
        while True:
            Invariant(Acc(m.x) and m.x == l)
            try:
                try:
                    break
                finally:
                    m.x += 1
            finally:
                l += 1
    finally:
        l += 1
    return l


def f9(m: MyClass) -> None:
    Requires(Acc(m.x) and m.x == 0)
    Ensures(Acc(m.x))
    Ensures(m.x == 0)
    while True:
        Invariant(Acc(m.x) and m.x == 0)
        try:
            break
        except Exception:
            m.x = 1
