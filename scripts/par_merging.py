from typing import Any, Collection
from common_types import Extension
from attrs import define, Factory


@define
class ParSpec:
    name: str
    mode: "ParMode"
    bindExpr: str | None = None
    expr: str | None = None
    val: Any = None


@define
class ParMerger:
    ext: Extension
    _cache: dict[str, ParSpec] = Factory(dict)

    def cache_settings(self):
        for page in self.ext.ownerComp.customPages:
            for par in page:
                self._cache[par.name] = ParSpec(
                    name=par.name,
                    mode=par.mode,
                    bindExpr=par.bindExpr,
                    expr=par.expr,
                    val=par.val,
                )

    def clear_pages(self, ignore: Collection[str] = tuple()):
        for page in self.ext.ownerComp.customPages:
            if page.name in ignore:
                continue
            page.destroy()

    def restore_settings(self):
        for page in self.ext.ownerComp.customPages:
            for par in page:
                spec = self._cache.get(par.name)
                if spec is not None:
                    par.mode = spec.mode
                    par.bindExpr = spec.bindExpr
                    par.expr = spec.expr
                    par.val = spec.val
