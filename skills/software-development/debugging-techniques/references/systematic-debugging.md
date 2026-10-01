# Systematic Root Cause Debugging (4-Phase Process)

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

## Phase 1: Root Cause Investigation (BEFORE ANY fix)

### 1. Read Error Messages Carefully
- Read stack traces completely, note line numbers, file paths, error codes
- Use `read_file` on relevant source files
- Use `search_files` to find the error string in the codebase

### 2. Reproduce Consistently
- Can you trigger it reliably? What are the exact steps?
- If not reproducible → gather more data, don't guess
- Run the failing test with verbose output: `pytest tests/test_module.py::test_name -v --tb=long`

### 3. Check Recent Changes
```bash
git log --oneline -10
git diff
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems
Before proposing fixes, add diagnostic instrumentation at EACH component boundary:
- Log what enters and exits each component
- Verify environment/config propagation
- Run once to gather evidence, THEN analyze to identify the failing component

### 5. Trace Data Flow
- Where does the bad value originate?
- What called this function with the bad value?
- Fix at the source, not at the symptom
- Use `search_files` to trace function references upstream

## Phase 2: Pattern Analysis

1. Find working examples of similar code in the same codebase
2. Read reference implementations COMPLETELY
3. List every difference between working and broken code
4. Understand dependencies and assumptions

## Phase 3: Hypothesis and Testing

1. Form a single hypothesis: "I think X is root cause because Y"
2. Make the SMALLEST possible change to test it
3. One variable at a time — don't fix multiple things at once
4. Not working? Form NEW hypothesis

## Phase 4: Implementation

1. Create failing test case first (simplest possible reproduction)
2. Implement single fix addressing the root cause
3. Verify with regression test + full suite
4. If fix doesn't work: STOP after 3 tries. Question the architecture.
   - 3+ failed fixes = likely architectural problem, not a simple bug
   - Discuss with the user before attempting more fixes

## Red Flags — STOP and Follow Process

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "I don't fully understand but this might work"
- "One more fix attempt" (when already tried 2+)
- Proposing solutions before tracing data flow

## One-Shot Recipes

**"Why is this dict missing a key?"**
```python
breakpoint()
(Pdb) pp d
(Pdb) pp list(d.keys())
(Pdb) w
```

**"This test passes in isolation but fails in the suite."**
```bash
source .venv/bin/activate
python -m pytest tests/ -x --pdb -p no:xdist
```

## References

- `python-debugpy.md` — when you need breakpoints and step-through
- `node-inspect-debugger.md` — when you need Node.js debugging
