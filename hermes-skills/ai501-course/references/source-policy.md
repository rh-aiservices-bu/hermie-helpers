# Source and Version Policy

Use the checkout commit recorded in each repository's `.git/HEAD` as the content
version. Prefer the configured `AI501_CONTENT_REF`; do not silently fetch another
branch during a learner conversation.

When checking expected output, quote only the minimum identifying value or status
from the exercise. Separate literal expected output from explanatory examples.

When sources conflict:

1. Prefer the current exercise over a module README.
2. Prefer the current exercise over implementation defaults when the exercise
   intentionally overrides them.
3. Prefer current repository code over Mem0.
4. Describe a conflicting Mem0 incident as historical and potentially outdated.

If the learner appears to follow a different revision, ask for the page heading or
small relevant snippet rather than assuming the current mirror applies.

