# Submodules & commits

- Constraint: every submodule commit that becomes part of this (outer)
  repository's history must exist on that submodule's own remote.
- "Exists in the remote" is a state: the commit record is present on the
  submodule's remote repository (i.e. it has been pushed there). The exact
  steps used to get it there are not specified.
- This outer repository must never contain a submodule pointer whose target
  commit is absent from the submodule's remote.
