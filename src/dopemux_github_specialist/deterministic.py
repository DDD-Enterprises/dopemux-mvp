from __future__ import annotations

from typing import Iterable, Callable, TypeVar, List

T = TypeVar("T")


def stable_sort(items: Iterable[T], key: Callable[[T], object]) -> List[T]:
    return sorted(list(items), key=key)


def stable_unique(items: Iterable[T]) -> List[T]:
    seen = set()
    out: List[T] = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def top_k(items: Iterable[T], k: int = 3) -> List[T]:
    out = list(items)
    return out[:k]
