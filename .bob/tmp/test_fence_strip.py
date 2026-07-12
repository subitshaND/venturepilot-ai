import sys; sys.path.insert(0, '.')
from app import _parse_sections

sample = """## 2. Business Model Canvas

```markdown
| Block | Description |
|---|---|
| Customer Segments | Small farmers |
| Value Propositions | AI crop monitoring |
```

## 5. Estimated Budget

```markdown
| Category | Cost | Notes |
|---|---|---|
| Dev | 250,000 | AI dev |
| **Total** | **700,000** | Year 1 |
```

## 9. Six-Month Roadmap

```markdown
| Month | Milestone | Key Activities | Success Metric |
|---|---|---|---|
| 1 | MVP | Build | Ready |
```
"""

sections = _parse_sections(sample)
for k, v in sections.items():
    has_table = '<table>' in v
    has_pre   = '<pre>'   in v
    status = 'OK  - <table>' if has_table else ('FAIL - <pre>' if has_pre else 'FAIL - neither table nor pre')
    print(f'{k}: {status}')
    if not has_table:
        print('  HTML:', v[:200])
