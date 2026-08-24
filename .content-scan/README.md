# Content scan

An automated check that keeps identifying information out of the template library.

Every document here is a *template*. Its value depends on containing no real organization and no
real person. This scan is the gate that keeps it that way. The full rationale, the severity model,
and every regular expression are specified in [`meta/content-scan-spec.md`](../meta/content-scan-spec.md).

## Running it

```bash
python3 .content-scan/scan.py                    # whole working tree
python3 .content-scan/scan.py policies/          # one directory
python3 .content-scan/scan.py --warn-only        # report, never exit non-zero
```

Findings print as `file:line:tier:rule:matched-text`. Emails, phone numbers, names, and keys are
masked in the output — a CI log is not a private place to print the secret you just found.

Exit codes: `0` clean, `1` at least one BLOCK, `2` configuration problem.

No dependencies. Python 3.9 or later, standard library only, so the CI job needs no install step.

## Where it runs

| Job | Scope | Behavior |
|---|---|---|
| `gate` | Markdown files changed in the pull request | Fails the build on any BLOCK |
| `baseline` | The whole working tree | Advisory — reports the inherited backlog without failing |

The split is deliberate. The library still carries pre-consolidation findings (see
[`meta/consolidation-plan.md`](../meta/consolidation-plan.md)), and a gate that fails on inherited
debt is a gate that gets switched off within a month. The gate holds the line on new work; the
baseline keeps the backlog visible until the consolidation retires it. Once the baseline reaches
zero, point the `gate` job at the whole tree and delete `baseline`.

Also worth installing locally:

```bash
ln -s ../../.content-scan/pre-commit .git/hooks/pre-commit
```

A scan that only fires in CI catches the problem after it is already in a commit — and for identity
leakage, the commit is the event you were trying to prevent.

## The denylists

`known-names.txt` and `known-orgs.txt` are the rules that actually work; no regex identifies a
person's name reliably. They are also, in plaintext, exactly the disclosure this check exists to
prevent — publishing a list of real names to a public repository is the most common way a
secret-scanning setup leaks the thing it protects.

So only the salted hashes are committed:

| File | Committed | Contents |
|---|---|---|
| `known-names.hashes` | yes | `sha256(salt + lowercased term)`, one per line |
| `known-orgs.hashes` | yes | same |
| `known-names.txt` | **no** — gitignored | the plaintext, held locally and by the maintainer |
| `known-orgs.txt` | **no** — gitignored | the plaintext |

The salt lives in `CONTENT_SCAN_SALT`: a repository secret in GitHub Actions, an environment
variable in your shell profile locally. Without it, the hashes cannot be reproduced and rules 1.4a
and 1.5 go quietly inert — which is why CI passes `--require-denylist`, so a missing secret fails
loudly instead of silently disabling the two rules that matter most.

### Adding a name or an organization

```bash
export CONTENT_SCAN_SALT='…'
echo "Alex Example" >> .content-scan/known-names.txt
python3 .content-scan/scan.py --hash-denylist known-names.txt > .content-scan/known-names.hashes
```

Commit the `.hashes` file only. Add a name whenever a document is drafted from a real source, and
add the initial-form too (`A. Example` as well as `Alex Example`) — a scrub that catches the
full name routinely leaves the initials behind.

## Suppressing a finding

A reviewer who decides a match is legitimate marks it inline, with a stated reason:

```markdown
<!-- scan-ok: illustrative example -->
```

The scanner skips the line the comment sits on and the line immediately following. Requiring a
reason rather than a bare suppression is what keeps the allowlist honest.

Suppression exists for documents that *quote* the patterns — the specification matches its own
regular expressions by construction, and `meta/content-scan-spec.md` carries three of these
comments for exactly that reason. It is not a way to pass a real finding. An identity leak in a
template is fixed, not annotated, and a suppression comment on one is a review failure.

## Files

| File | Purpose |
|---|---|
| `scan.py` | The scanner |
| `config.yml` | Path exemptions, standing allowlist, required frontmatter keys |
| `vendors.txt` | Vendor terms for the §2.1 rule (off by default) |
| `pre-commit` | Git hook, installed by symlink |
| `*.hashes` | Salted denylists |

## Tuning order

Tier 1 first, to zero. Tier 2 only after. The volume of warnings otherwise hides the blocks, which
inverts the whole purpose of the severity split.

The vendor rule (§2.1) ships **disabled**. Tool references are acceptable in this library — they
are scrubbed when a template is adapted for a specific engagement, which is the right point to
decide them. Enable it in `config.yml` only if that position changes, and review
`vendor_check_exempt` at each release: it is the place where exceptions quietly accumulate.
