# Commit process involving changes in submodules

These rules apply when a commit needs to be made that includes changed code in submodules or a changed submodule pointer. The rule: if a submodule pointer is going to be added to a commit in the parent repository, the commit it points to must already exist in that submodule's remote. Never record a submodule commit in history that was not pushed to its remote.

- Constraint: every submodule commit that becomes part of this (outer)
  repository's history must exist on that submodule's own remote.
- "Exists in the remote" is a state: the commit record is present on the
  submodule's remote repository (i.e. it has been pushed there). The exact
  steps used to get it there are not specified.
- This outer repository must never contain a submodule pointer whose target
  commit is absent from the submodule's remote.
