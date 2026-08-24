# it-playbook

A playbook for implementing IT in organizations of various sizes.

Every document here is a **template**. Its value depends on containing no real organization and no
real person — replace every `[BRACKETED PLACEHOLDER]` with your own details before adopting one.

## Content scan

Pull requests are gated by an automated check that keeps identifying information — names, contact
details, private document links, credentials — out of the library.

```bash
python3 .content-scan/scan.py
```

See [`.content-scan/README.md`](.content-scan/README.md) for how to run it, install the pre-commit
hook, and maintain the denylists. The rules are specified in
[`meta/content-scan-spec.md`](meta/content-scan-spec.md).

## Placeholder key

Placeholders used across the library. A placeholder that appears in a document but not in this
table raises a warning — a reader cannot substitute what is not documented.

| Placeholder | Replace with |
|---|---|
| `[ORGANIZATION]` | Your organization's legal or common name |
| `[DOCUMENT OWNER]` | The role accountable for keeping the document current |
| `[APPROVER]` | The role that formally approves the document |
| `[NAME]` | A person's name, when the instance genuinely needs one |
| `[DATE]` | A specific calendar date |
| `[EFFECTIVE DATE]` | The date the document takes effect |
| `[CLASSIFICATION]` | The document's handling classification |
| `[SYSTEM OF RECORD]` | The authoritative system for the data in question |
| `[SYNCHRONOUS CHANNEL]` | Your real-time communication tool |
| `[ASYNCHRONOUS CHANNEL]` | Your message or ticket-based tool |
| `[APPROVED EXTERNAL CHANNEL]` | The sanctioned channel for communicating outside the organization |
| `[IT HELPDESK EMAIL]` | Your support intake address |
| `[SECURITY TEAM EMAIL]` | Your security intake address |
| `[CONTACT PHONE]` | A contact telephone number |
| `[TARGET]` | The numeric target for the measure described |
| `[TOC]` | Replaced by your renderer's table of contents |

Two markers are not placeholders to substitute, but flags for the maintainer:

| Marker | Meaning |
|---|---|
| `[SOURCE GAP]` | Content the adopting organization must supply; no template text exists |
| `[VERIFY BEFORE ADOPTION]` | An external citation that has not been confirmed |

## Structure

The library is mid-consolidation. [`meta/consolidation-plan.md`](meta/consolidation-plan.md)
describes the target eight-folder structure, the file-by-file disposition, and the decisions still
outstanding.

| Folder | Contents |
|---|---|
| `policies/` | What the organization's position is |
| `documents/` | Templates and outlines, pending redistribution per the consolidation plan |
| `job-descriptions/` | Role definitions |
| `process/` | Process documents |
| `meta/` | Documents about the library itself, not part of the published set |

## License

See [LICENSE](LICENSE).
