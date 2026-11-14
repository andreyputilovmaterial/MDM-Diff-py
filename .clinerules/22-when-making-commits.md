# When making commits

- Only make commits when the user asked for it.
- Split into multiple commits if the changed files contain conceptually unrelated changes. But that only means significantly unrelated changes. For example, multiple minor styling updates in the UI without new functionality added should not be split. Multiple updates in docs are usually one commit (until user asks to explicitly separate it), cause there are no unrelated changes in functionality.
- Decide whether changes are unrelated and should be split into separate commits based on changes in functionality — whether something changed for the user. If there were only styling updates in the UI without a real change in functionality, don't split.
- If there were new items in docs/roadmap.md recorded during the task, they usually belong to the commit.
