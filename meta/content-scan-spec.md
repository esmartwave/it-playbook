---
title: "Repository Content Scan Specification"
document_type: "Specification"
version: "1.0"
status: "Ready to implement"
owner: "[DOCUMENT OWNER]"
---

# Repository Content Scan Specification

A specification for an automated check that prevents identifying information from re-entering the
template library.

## Problem this solves

The library is published. Every document in it is a *template* — its value depends on containing no
real organization and no real person. Three things break that, and all three arrived in this
repository through ordinary work rather than carelessness:

1. **Identity leakage** — a document is drafted from a real one and the scrub is incomplete.
2. **Contact leakage** — an email, phone number, or private document link survives a copy-paste.
3. **Credential leakage** — a key, token, or identifier is pasted into an example and left there.

Tool and product references are **not** in scope. Those are scrubbed when a template is adapted for
a specific engagement, which is the right point to decide them — the reader adapting the document
knows their own stack, and a generic placeholder would only be replaced with a real product name
anyway. A rule for them is specified in §2.1 but ships disabled.

The check runs on every pull request. It is a gate, not a report.

## Severity model

| Tier | Meaning | CI behavior |
|---|---|---|
| **BLOCK** | Identifying information. Cannot be merged. | Fail the build |
| **WARN** | Structural or hygiene problem. Needs a human decision. | Annotate, do not fail |
| **ALLOW** | Matched an allowlist entry. | Silent |

The split matters. A phone number is never acceptable, so it blocks. A missing README entry is a
tidiness problem, so it warns. A check that blocks on both gets disabled within a month, because
the false positives outnumber the true ones — and a disabled check catches nothing at all.

---

## Tier 1 — BLOCK

### 1.1 Email addresses

```
[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}
```

**Allowlist:** addresses whose local part is a bracketed placeholder, and the reserved example
domains from RFC 2606, which exist precisely for documentation.

```
\[[A-Z][A-Z ]+\]@          # [SECURITY TEAM EMAIL]@…
@example\.(com|org|net)$
@(.*\.)?(invalid|test|localhost)$
```

### 1.2 Telephone numbers

```
(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}
\+\d{1,3}[-. ]\d{2,4}[-. ]\d{3,4}[-. ]\d{3,4}
```

**Allowlist:** the reserved 555-01xx range (RFC 3849 equivalent for phone), and bracketed
placeholders.

```
\d{3}[-. ]555[-. ]01\d{2}
\[CONTACT PHONE\]
```

<!-- scan-ok: pattern documentation, not a contact detail -->
> Note: `414-555-5555` looks reserved but is **not** in the reserved 555-0100–555-0199 block. Treat
> anything outside that block as a real number.

### 1.3 Private document URLs

Links to collaboration platforms are, by definition, links into someone's tenancy.

```
https?://docs\.google\.com/\S+
https?://drive\.google\.com/\S+
https?://\S*\.sharepoint\.com/\S+
https?://\S*\.atlassian\.net/\S+
https?://\S*\.slack\.com/(archives|files)/\S+
https?://\S*\.notion\.(so|site)/\S+
https?://\S*\.box\.com/\S+
https?://\S*\.dropbox\.com/s/\S+
https?://\S*\.zoom\.us/(rec|j)/\S+
```

**No allowlist.** A template never needs to link into a live tenancy. Internal references use
`[LINK: description]`.

### 1.4 Person names

Heuristic, not exhaustive — no regex identifies a name reliably. Two complementary rules:

**a. Denylist file.** `.content-scan/known-names.txt`, one name per line, covering every real
person previously found in the repository, plus initial-forms (`A. Example`) and any name a
reviewer adds. Matched case-insensitively on word boundaries. This is the rule that actually works.

**b. Structural heuristic (WARN, not BLOCK).** Two consecutive capitalized words inside a table
cell in a column headed *Name*, *Owner*, *Approver*, *Contact*, or *Reviewer*, where the value is
not a bracketed placeholder:

```
\|\s*([A-Z][a-z]+ [A-Z][A-Za-z'’-]+)\s*\|
```

Expect false positives on role titles. That is why it warns.

### 1.5 Known organization names

`.content-scan/known-orgs.txt`, one per line, including possessive and abbreviated forms. Seed it
with every organization already found, and add to it whenever a document is drafted from a real
source.

Also block the generic tell that a scrub was started but not finished:

```
\b(Corp|Inc|LLC|Ltd|GmbH|PLC)\b\.?          # WARN — often legitimate in legal boilerplate
```

### 1.6 Credentials and identifiers

Cheap to add, expensive to omit:

```
AKIA[0-9A-Z]{16}                                  # AWS access key
gh[pousr]_[A-Za-z0-9]{36,}                        # GitHub token
sk-[A-Za-z0-9]{20,}                               # generic API secret
xox[baprs]-[A-Za-z0-9-]{10,}                      # chat platform token
-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----   # private key
\b\d{3}-\d{2}-\d{4}\b                             # US SSN
```

---

## Tier 2 — WARN

### 2.1 Vendor product names in mandates

> **Off by default.** Tool references are acceptable in this library and are scrubbed at the point
> of reuse, not at the point of publication. Enable this rule only if that position changes — for
> example, if a specific engagement requires a fully tool-neutral set. The rule is specified here
> so it is ready, not because it should be switched on.

The signal is not the product name. It is a product name **inside a requirement**. Match a vendor
term within 120 characters of a modal keyword on the same line:

```
\b(MUST|MUST NOT|SHALL|SHALL NOT|REQUIRED|Required for)\b.{0,120}\b<VENDOR>\b
\b<VENDOR>\b.{0,120}\b(MUST|MUST NOT|SHALL|SHALL NOT|REQUIRED)\b
```

Where `<VENDOR>` comes from `.content-scan/vendors.txt`:

```
Jira · Confluence · Slack · Zoom · Salesforce · Workday · ServiceNow · Trello · Asana · Notion
Okta · Duo · Jamf · Kandji · Intune · CrowdStrike · SentinelOne
GitHub · GitLab · Bitbucket · Snowflake · Databricks · Tableau · Looker
Google Workspace · Microsoft 365 · SharePoint · OneDrive · Dropbox · Box
Claude · ChatGPT · OpenAI · Anthropic · Gemini · Copilot
```

**Suppression comment.** A reviewer who decides a mention is legitimate marks it inline:

```markdown
<!-- scan-ok: illustrative example -->
<!-- scan-ok: published standard name -->
<!-- scan-ok: named data feed -->
```

The scanner skips the line the comment sits on or the line immediately following. Requiring a
stated reason, rather than a bare suppression, keeps the allowlist honest.

### 2.2 Path exemptions

Some documents are *about* a specific tool, so vendor names are their subject matter. Exempt by
path in `.content-scan/config.yml`:

```yaml
vendor_check_exempt:
  - standards/ai-solution-deployment-standard.md
  - standards/agentic-sdlc-standard-and-configuration.md
  - procedures/code-review-and-vulnerability-check-runbook.md
```

Review this list at each release. It is the place where exceptions quietly accumulate.

### 2.3 Standing allowlist — never flag

These are references to published standards, methodologies, and public data sources. Stripping them
makes documents worse, not safer:

| Term | Why it is legitimate |
|---|---|
| Microsoft STRIDE | Threat modeling methodology; the name includes the originator |
| CIS Benchmarks | Published configuration standard |
| AWS Foundational Security Best Practices | Published standard |
| GitHub Security Advisories, GitHub Advisory Database | Named public vulnerability feed |
| OSV, NVD, CVE, CWE, MITRE ATT&CK | Public vulnerability and threat taxonomies |
| Openwall oss-security | Named public mailing list |
| Keep a Changelog, Semantic Versioning | Published conventions |
| ISO 27001, SOC 2, NIST CSF, GDPR, CPRA, HIPAA, PCI DSS | Frameworks and regulations |
| Terraform, Ansible, Kubernetes, Docker | Flagged only inside a mandate; fine as an IaC example |
| Snyk, Dependabot, TruffleHog, SonarQube | Named scanning tools in `e.g.` lists |

### 2.4 Placeholder integrity

Two failure modes that a scrub introduces:

**Unclosed or malformed placeholders** — BLOCK:

```
\[[A-Z][A-Z ]{2,}(?!\])[^\]\n]{0,40}$
```

**Undocumented placeholders** — WARN. Extract every `[UPPERCASE PLACEHOLDER]` in the repository and
diff against the placeholder table in `README.md`. A placeholder used but not documented means a
reader cannot know what to substitute.

### 2.5 Structural checks

| Check | Tier | Rule |
|---|---|---|
| YAML frontmatter present | BLOCK | Every `.md` outside `.content-scan/` and `meta/` opens with a `---` block |
| Required frontmatter keys | BLOCK | `title`, `document_type`, `version`, `status`, `owner` |
| Filename convention | BLOCK | `^[a-z0-9]+(-[a-z0-9]+)*\.md$` |
| README index matches disk | WARN | Every file listed exists; every file exists in the listing |
| Internal links resolve | WARN | Relative `.md` links point at a real path |
| Empty document | WARN | Body under 200 bytes after frontmatter |
| Conversion artifacts <!-- scan-ok: pattern documentation --> | BLOCK | `gd2md-html alert`, `Output copied to clipboard`, `Docs to Markdown version` |

That last row is worth keeping permanently. It is what would have caught the two Google Docs
exports on the day they were committed.

---

## Implementation notes

**Where it runs.** A pull-request check on `main`. Also worth running as a pre-commit hook — a
scan that only fires in CI catches the problem after it is already in a commit, and for identity
leakage the commit is the event you were trying to prevent.

**Scan scope.** Working tree only. Scanning history is a separate one-time exercise, not a
recurring check. See the git history decision in the consolidation plan.

**Output.** Findings as `file:line:tier:rule:matched-text`, with matched text truncated to 40
characters and phone numbers, emails, and keys masked in the log. A CI log is not a private place
to print the secret you just found.

**Tuning order.** Turn on Tier 1 first and get it to zero. Add Tier 2 only once Tier 1 is clean,
otherwise the volume of warnings hides the blocks — which inverts the whole purpose.

## Seed data to create

| File | Contents |
|---|---|
| `.content-scan/known-names.txt` | The four names found in the previous policy files, plus initial-forms |
| `.content-scan/known-orgs.txt` | The organization name found, with possessive and abbreviated forms |
| `.content-scan/vendors.txt` | The vendor list in §2.1 |
| `.content-scan/config.yml` | Path exemptions, allowlist terms, severity overrides |

> **Do not commit `known-names.txt` and `known-orgs.txt` with real values to a public repository.**
> That file would itself be the disclosure the check exists to prevent. Either store the denylist as
> salted hashes of the lowercase terms, or hold it as a CI secret injected at scan time. This is the
> single most common way a secret-scanning setup leaks the thing it protects.

---

*This specification is my own design based on what was found in this repository, not an
adaptation of a published standard. The regular expressions are written for Python `re` and
GNU `grep -P`; they will need minor adjustment for other engines. Test each Tier 1 pattern against
the existing corpus before enabling the gate — a pattern that fires on legitimate content trains
reviewers to bypass the check.*
