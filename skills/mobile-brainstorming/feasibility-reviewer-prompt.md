# Feasibility Reviewer Prompt Template

Use this template after all three research reports are complete.

```markdown
You are reviewing proposal feasibility and mobile skill quality.

## Project Context
[controller-curated context]

## Proposals
[paste all three reports]

## Review Criteria
- Can this become a reusable mobile design spec rather than project-specific prose?
- Does it avoid implementation before spec approval?
- Are gates explicit and enforceable?
- Are mobile constraints concrete?
- Are hallucination controls strong enough?
- Does it avoid unnecessary third-party dependencies?
- Are claims traceable to user input, repo context, or labeled inference?

## Output
- Status: COMPLETE | NEEDS_CONTEXT | BLOCKED
- Feasibility assessment per proposal
- Mobile risks
- Skill-design risks
- Missing gates
- Claims needing verification
- Recommendation
- Approval: APPROVED | NEEDS_REVISION
```
