# it-playbook Consolidation Plan

**Prepared:** 2026-08-24
**Scope:** Merge the 42-file `it-playbook` repository with the 46-file governance template
library into a single published library.
**Decisions taken:** Rebuild in place · Public portfolio and client asset · Drop the
domain-specific procedures · Write the missing documents in full.

---

## 1. The problem this solves

Two document sets exist that overlap in purpose but not in quality. The playbook is broad,
opinionated, and written in your voice, but roughly a third of it is stubs and shorthand. The new
template library is deep, consistent, and organization-neutral, but narrower — it is a security and
data governance set, with no coverage of planning, maturity, org design, or IT operations.

Neither, on its own, is publishable as evidence of a method. Merged and finished, the combined set
is a complete governance library: about 79 documents that a growing organization could adopt, and
that a prospective client could read as a demonstration of what SmartWave brings.

## 2. Outcome to achieve

A single public repository where:

- Every file follows one metadata and naming convention.
- No file is empty, and every incomplete file is visibly marked as incomplete.
- No real organization, person, or contact detail appears anywhere — including git history.
- Every internal cross-reference resolves to a document that exists.
- The README indexes the whole set with a status column, so a reader can tell adopted-quality
  material from a draft at a glance.

---

## 3. Blocking decision: git history

> **This needs your answer before the repository is published.**

`policies/Policy-Communication.md` and `policies/Policy-CodeOfEthicsandCoreValues.md` name a real
organization 19 times between them, plus a real email address at that organization's domain.
`documents/Communications Template for IT Teams to Users.md` carries a real email address at a
second domain. Both policy files are also raw Google Docs export dumps — the converter's warning banners
and error notices are still in the body text.

Rewriting the working files removes this from the current state of the repository. It does **not**
remove it from prior commits, which stay readable on a public GitHub repo.

**Options:**

| Option | What it costs | What it leaves |
|---|---|---|
| **A. Rewrite history** (`git filter-repo`, then force-push) | Rewrites every commit hash; anyone with a clone must re-clone | Clean history. The right answer for a public repo. |
| **B. Fresh start** — new orphan commit as the new root, old history discarded | Loses the commit record entirely | Clean history, no forensic trail of the old work |
| **C. Accept it** — clean the working files only | Nothing | The names remain discoverable in history |

My assessment, not a sourced fact: for a repository whose purpose is to be read by prospective
clients, option A or B is the only defensible choice. A former client's name and internal policy
text sitting in the history of your public consulting portfolio is the kind of detail a
security-conscious buyer will notice, and it undercuts the exact competence the repository is
meant to demonstrate.

**Until you pick one, I will build everything on a branch and not push.**

---

## 4. Target structure

Eight folders. Six come from the new library; two are added because the playbook's best material
does not fit any of the six.

```
it-playbook/
├── README.md              Master index with status column
├── LICENSE
├── policies/              What the organization's position is (9 docs)
├── standards/             Testable requirements implementing the policies (17)
├── plans/                 Continuity, recovery, incident response (3)
├── procedures/            Step-by-step operational runbooks (5)
├── templates/             Copy-and-complete per instance (10)
├── guides/                Reusable guide shapes (6)
├── frameworks/            Thinking models and assessment tools (5)  ← new
└── roles/                 Job descriptions (4)                      ← new
```

**Why `frameworks/` and `roles/` are separate.** The playbook's maturity index, risk appetite
model, strategic planning guidance, and documentation hierarchy are not templates — nobody fills
them in. They are ways of thinking about a problem, closer to a consulting method than a document
to adopt. Filing them under `templates/` would bury them among fill-in forms and misrepresent what
they are. Job descriptions are likewise neither policy nor template. Analogy: a cookbook separates
recipes from the chapter on knife technique — both belong in the book, but a reader looking for one
is not looking for the other.

**House convention, applied to every file:**

- Filenames kebab-case, no `DRAFT-` prefix (status lives in frontmatter, not the filename).
- YAML frontmatter: `title`, `document_type`, `version`, `status`, `owner`, `approver`,
  `effective_date`, `review_cycle`, `applies_to`.
- The standard "How to use this template" callout below the H1.
- All organization-specific values as `[BRACKETED PLACEHOLDERS]`.

This is the new library's convention. 46 of the 88 files already follow it, so adopting it is the
cheaper direction of travel.

---

## 5. File-by-file disposition

### 5.1 Retire — superseded by a better equivalent (8 files)

| Playbook file | Superseded by | Why |
|---|---|---|
| `documents/Policy template.md` | `templates/generic-page-template.md` | 38-line skeleton vs. 164-line template with drafting language. Its drafting-guideline bullets are already carried into the replacement. |
| `documents/User Guide Template.md` | `guides/application-user-guide-template.md` | 39 lines vs. 222 |
| `documents/Admin Guide Template.md` | `guides/tool-setup-and-configuration-guide-template.md` | 47 lines vs. 567 |
| `documents/Procedure Guide Template.md` | `guides/end-user-how-to-and-troubleshooting-template.md` | 41 lines vs. 215 |
| `policies/Policy-MobileDeviceManagement.md` | `standards/byod-standard.md` | Title only, 29 bytes, no content |
| `policies/Policy-PatchManagement.md` | New patch/vulnerability standard (§5.5) | Title only, 22 bytes |
| `Process-SelectingSoftware.md` | Merged software evaluation doc (§5.2) | Title only, 38 bytes |
| `process/process-selecting systems.md` | Merged software evaluation doc (§5.2) | Fragment with a malformed table |
| `documents/DRAFT-Authentication Policies Planning Template.md` | New access control policy (§5.5) | Title only, 44 bytes |

### 5.2 Merge — several files covering one topic (6 files → 2)

**`standards/software-evaluation-and-selection-standard.md`** ← consolidates:

- `documents/Evaluating Software for Solutions Outline and Template.md` (116 lines — the fullest
  version, and the structural base)
- `documents/DRAFT-Purchasing Software Guidelines Template.md` (180 lines — contributes the
  budget-first sequencing and the scoring matrix; its pasted spreadsheet formula gets rewritten as
  a described scoring method rather than a raw formula)
- The two selecting-software stubs listed above

These three describe the same five-step process — classify, define criteria, walkthrough, rank,
score — in three states of completeness. One document.

**`frameworks/risk-appetite-and-tolerance.md`** ← consolidates:

- `documents/Establishing Organization Risk Appetite and Tolerance Template.md` (57 lines)
- `documents/Memo for Risk Appetite and Tolerance Template.md` (57 lines)

The second is the memo format for communicating the output of the first. They are one method split
across two files; merging keeps the speed-limit analogy (appetite 55, tolerance 10-over, controls
are the signs and tickets), which is the clearest explanation of the distinction in either folder.

### 5.3 Rewrite — real-name scrub required (2 files)

| File | New location | Work |
|---|---|---|
| `policies/Policy-Communication.md` | `policies/communications-policy.md` | Strip converter artifacts and HTML tables, replace 10 org references with `[ORGANIZATION]`, remove the real email, restructure to house frontmatter |
| `policies/Policy-CodeOfEthicsandCoreValues.md` | `policies/code-of-ethics-policy.md` | Same, plus repair the broken internal anchor link the converter flagged |

Both have genuinely good content underneath the mess. The ethics and moral-leadership framing is
the philosophical spine of the SmartWave positioning — worth salvaging rather than dropping.

### 5.4 Carry forward from the new library (41 of 46)

All of `policies/` (5), `standards/` (14), `compliance-plans/` (3 → `plans/`), `templates/` (8),
and `guides/` (6) transfer unchanged apart from folder placement.

**Dropped per your decision — five industry-specific procedures:**

`client-bill-submission-process.md`, `data-gap-triage-and-resolution-sop.md`,
`resolving-duplicate-and-overlapping-meters-sop.md`, `resolving-duplicate-readings-sop.md`,
`transitioning-manual-meter-to-automated-sop.md`

**Five procedures retained**, but flagged for a generalization pass — they lean toward a data
operations context without being locked to metering: `document-ai-needs-review-qa-sop.md`,
`code-review-and-vulnerability-check-runbook.md`,
`customer-data-quality-check-communications-procedure.md`,
`data-quality-event-procedure-and-comms-templates.md`, `threat-intelligence-procedure.md`.

**One correction to make.** The library's own README lists "Data Change and Decision Record
Standard" but links it to `standards/application-logging-and-audit-standard.md`. The title and the
filename describe different documents. I will read the file and name it for what it actually
contains.

**Two files carry `[VERIFY BEFORE ADOPTION]` flags** on external citations that could not be
confirmed: `ai-solution-deployment-standard.md` and
`agentic-sdlc-standard-and-configuration.md`. For a public repository these need resolving — an
unverifiable framework citation in a published governance document is a credibility risk. I will
list the specific citations for you rather than deciding them myself.

### 5.5 Write in full — the eight gaps (8 new documents)

Neither folder covers these. Several are already referenced as `[LINK: …]` upstream documents by
files in the new library, so those cross-references currently point at nothing.

| New document | Folder | Why it is needed |
|---|---|---|
| Access Control and Identity Policy | `policies/` | Referenced by `byod-standard.md` as a downstream document; nothing exists |
| Acceptable Use Policy | `policies/` | Referenced by `byod-standard.md`; the single most commonly requested policy in an IT program |
| Data Classification and Handling Policy | `policies/` | Referenced by `byod-standard.md`. Also the missing dependency for the DLP, masking, and destruction standards, which all assume classification levels exist |
| Asset Management Policy | `policies/` | Referenced by `byod-standard.md`. Pairs with the playbook's Systems Ownership template, which is the inventory instrument this policy would mandate |
| Change Management Standard | `standards/` | The playbook has only a Change Request Form stub. Change control is the most common audit finding in a growing IT function |
| Patch and Vulnerability Management Standard | `standards/` | Replaces the empty playbook policy; the code review runbook assumes it exists |
| Security Awareness and Training Standard | `standards/` | No coverage anywhere; required by most compliance frameworks |
| Risk Register Template | `templates/` | The operational instrument the risk appetite framework produces. Framework without register is theory without practice |

Each written to the depth of the existing library — full frontmatter, purpose, scope, roles table,
requirements, exceptions, review cadence — with framework control references included only where I
can state them accurately, and marked where I cannot.

### 5.6 Carry forward from the playbook, upgraded (22 files)

Kept because nothing in the new library covers them. Each gets frontmatter, a kebab-case filename,
typo repair, and expansion where it is currently shorthand.

**→ `frameworks/`** (5)

| Current | Becomes | Work needed |
|---|---|---|
| `DRAFT-IT Operational Maturity Indexing.md` | `it-operational-maturity-model.md` | Substantial. The CMMI/ITIL grid is an empty table with "ITIL THING" placeholders — the structure is sound, the content is unwritten |
| `Guidelines for Strategic Plannign and Vision Set.md` | `strategic-planning-and-vision-setting.md` | Light. Fix the filename typo, add frontmatter |
| `Standards for Documentation.md` | `documentation-standards.md` | Light. This is the file that defines the policy→process→procedure→guide hierarchy the whole library rests on. Promote it prominently in the README |
| `Establishing…` + `Memo for…` Risk Appetite | `risk-appetite-and-tolerance.md` | Merge per §5.2 |
| `DRAFT-Thoughts on Modern IT and Security.md` | `modern-it-and-security-program-design.md` | Medium. The only document in either folder written in your voice with a point of view. Finish it — it is the piece that frames why the rest of the library looks the way it does |

**→ `templates/`** (10)

`Communications Template for IT Teams to Users` · `Data Dictionary Template` · `Definition of Done
Template` · `DRAFT-Change Request Form` · `Executive Summary Template` · `Process or Standards
Definition Template` · `Software Budget Template` · `Systems Ownership Template` · `Team Charter
Template` · `DRAFT-OKR and Work Planning Schedule Template`

Mostly light work. Two exceptions: the Change Request Form is a bare field list that needs building
out against the new Change Management Standard, and the OKR template is 12 lines of agenda that
needs real content or an explicit "outline only" status.

**→ `standards/`** (3)

`Outline for Standardized Object Names in Infraststructure` → `object-naming-standard.md` (fix
typo; expand the prefix list into a stated convention) · `DRAFT-Standards for Prioritization` →
`work-prioritization-standard.md` (12 lines; needs the impact/effort axes actually defined) ·
`Outline of Functional Testing for Applications` → `functional-testing-standard.md`

**→ `guides/`** (2)

`Outline for Common Intranet or Shared Knowledgebase` → `knowledge-base-structure-guide.md` ·
`Guidelines for stakeholder feedback and input` → `stakeholder-feedback-guide.md`

**→ `roles/`** (4)

The four job descriptions, unchanged apart from frontmatter and naming.

**Two requiring a judgment call before I proceed:**

- `DRAFT-Employee Review Process Template.md` — 15 lines of personal notes, including a reference
  to a specific 2024 contract negotiation. Personal, dated, and not publishable as-is. My
  recommendation: drop it, or rewrite from scratch as a performance conversation framework using
  only the Situation-Behavior-Impact model it gestures at.
- `DRAFT-Outline for a technical internships.md` — 5 lines. Recommendation: drop, or hold for a
  future pass. It is an idea, not a document.

---

## 6. Sequence

| Phase | Work | Gate |
|---|---|---|
| **1** | Branch the repo. Scrub the two real-name policy files. | Your git history decision (§3) |
| **2** | Build the eight-folder structure. Move and rename every surviving file, apply frontmatter, delete the retired and dropped files. | — |
| **3** | Execute the two merges. Upgrade the thin survivors, heaviest first: maturity model, modern IT piece, change request form, prioritization standard. | — |
| **4** | Write the eight missing documents. | — |
| **5** | Master README with status column and placeholder key. | — |
| **6** | Verify: scan for surviving real names and emails, resolve every `[LINK:]` cross-reference, confirm frontmatter consistency, confirm README index matches the files on disk. | Review before push |

Phases 3 and 4 are the bulk of the effort and will run across more than one working session.

## 7. Expected end state

| | Before | After |
|---|---|---|
| Documents | 88 across two folders | ~79 in one repository |
| Empty or near-empty files | 6 | 0 |
| Duplicate coverage | 6 files on 2 topics | 0 |
| Naming conventions in use | 4 | 1 |
| Files with structured metadata | 46 of 88 | all |
| Real organization names | 2 files, 19 references | 0 |
| Broken cross-references | 8+ | 0 |

## 8. What I need from you

1. **The git history decision** (§3) — blocks publication, not the build.
2. **Employee Review and Internships files** (§5.6) — drop, or rewrite?
3. **Nothing else.** Everything above proceeds on the decisions already made unless you redirect.

---

*Sections 5 and 7 reflect my own analysis of document overlap and quality, based on reading the
structure and topic of all 88 files and the full text of a representative sample. They are not
sourced claims. File counts, byte sizes, and the real-name occurrence counts in §3 are measured
directly from the files.*
