"""PHI pre-commit hook — v1.13 (2026-09-16, Python).

Importable module. Entry point is `main()`. `pre-commit` is a thin wrapper.

Six-pattern gate:
1. Patient-name slugs in Maieutic/Themis/Nostos reasoning paths (scans staged
   content AND the staged file paths themselves)
2. Proper-noun name adjacent to PHI field (DOB/MRN/SSN/insurance/patient/plaintiff) in
   either order, ALL-CAPS names beside a field, a phone number beside a name, a standalone
   SSN value, and value-shaped record rows (name/DOB/id; `Last, First` too) like a CSV line
3. Credential files (.env, credentials.json, *secrets.{yml,json}, *private_key*)
4. PHI-risk binary files (pdf/docx/xlsx/png/jpg/tif/dcm) outside allowlisted
   paths; PHI-suggestive basenames block even under allowlisted paths
5. API-token / secret shapes (Anthropic, OpenAI, AWS, GitHub, Google, Slack,
   Stripe live, private-key PEM blocks). Tight regex + length anchors;
   truncated doc placeholders (sk-..., AKIAIOSFODNN7EXAMPLE) pass.
6. Structured-data files (.csv/.tsv/.psv) outside fixture paths (v1.12: docs/ etc. no
   longer exempt them)

Path allowlist skips synthetic-fixture directories:
  TestCase_*/ | fixtures/ | test_data/ | tests/fixtures/ |
  test-fixtures/ | scripts/test-* | scripts/demo-*

Install (per repo): ln -sf ../../hooks/pre-commit .git/hooks/pre-commit
There is no override flag: a false positive is fixed in the allowlists below.
Full-history audit (existing repos): python hooks/scan-history.py

Changelog:
  v1.13 — Pattern 7, `prose`: a proper-noun name in clinical prose with NO field label — the only class
         that has actually leaked from these repos (Themis 2026-07-02: a credential beside a surname,
         staff names, a case caption; caught by hand, twice). Four shapes, each priced on the 16-repo
         tracked corpus (tools/price-pattern.py, 238,362 lines after FIXTURE_PATH + allowlist) BEFORE
         adoption: name pair within 30 chars of an N-year-old/Nyo form or directly followed by `aged N`;
         Dr./Nurse + surname; surname + strong credential (RN LPN CRNA RPh PharmD APRN MSN BSN) unless an
         author list; space-separated name pair + comma + ambiguous credential (MD DO NP PA RT — states,
         prior-auth, author initials and `Standardized MD` priced those at 8 lines bare); credential +
         `, Surname`. Raw pricing: name+age 11, title+name 25, name+credential 27, credential+name 0.
         Residual after the widened self-name strip (middle initial, `Dr.` — bounded to Ralph's own name)
         and a demonym strip: 8 corpus lines, all synthetic vignettes or bylines — MedLegal_System
         README:145, Maieutic examples/jdm-12yo-treatment.md:3, EHI-Request README:220 (a public-figure
         credit), MedicalLegal MCP tools/expert_conflict.py:107, BlackBerryAI BLUEPRINT.md:4, Stele
         CHANGELOG.md:34 / docs/REVIEW-STATUS.md:88 / quote_fidelity.py:103 (`Dr. <placeholder>` examples).
         They block only when those lines are next edited; the fix is a `<Surname>` placeholder.
         REJECTED on the same corpus: name+date (285 — changelogs), a case caption `X v. Y` (135 / 80
         without a reporter cite — Themis IS case law; the active case's caption is the opt-in blocklist
         layer's job, ~/.git-hooks/blocklist_scan.py), name+clinical verb (1,363), name+facility (56),
         name + any two signals (34); bare 6–10-digit numbers were never a candidate (PMIDs). Residual
         MISSES, by shape: `<First> <Last> was admitted on <date>`; `patient <First> <Last> was seen`;
         a bare `<Surname> MD`; a caption; a verbatim chart quote with no identifier (unreachable by
         regex). demo_case/ joins FIXTURE_PATH (SourceMind's synthetic record set, 13 of the raw hits).
         Companion changes the same day: pre-push v1.6 — every finding carries its commit and the footer
         names the commits at fault (the first live block of an Alethoskopia push named only the ref);
         deploy-hook v1.3 — a repo's own differing pre-commit wrapper is KEPT (Stele's fail-closed one
         was silently replaced), and a repo carrying hooks/pre-push receives the whole family. Suite 207.
  v1.12.1 — Pattern 1 undated variant no longer fires on a date template: `reasoning/YYYY-MM-DD-
         [topic]-bias-audit.md` (four lines in Maieutic's SKILL/INSTALL/CHANGELOG/references,
         caught by the deployed v1.12 on Maieutic's reinit root commit). yyyy/yy/mm/dd are
         accepted slug tokens; a name beside one still blocks (test + control).
  v1.12 — /poll review, 9 seats, every claim executed against this module before any edit
         (record: ~/.claude/bench/phi_review_20260916/). Pattern 6: docs/*.csv no longer exempt
         (6 seats). Pattern 1: tokens any case, third token optional, undated variant, notes/
         encounters/patients dirs; the panel's every-token vocabulary check was REJECTED by a
         census of 104 real slug tokens (78 legitimate clinical words). Pattern 2: field→name,
         ALL-CAPS beside a field, SSN label + standalone SSN value (kind "ssn"), phone beside a
         name-shaped pair, Last-First rows and labels, ID-first rows, Latin-script Unicode
         tokens, insert/your placeholders bounded. Priced against v1.11 on 272,209 tracked
         lines in 17 repos: +13 lines newly flagged (8 phone; 3 were this file's own comment
         examples, now <First> <Last> placeholders — a hook source must not trip itself, and a
         test enforces it). REJECTED by the same pricing: a word-tolerant name↔field gap (+45,
         citations) and an any-order field-set row (+19, bibliographies). redact() shows a
         20-char window. Key-material files, mail/archive/audio containers, encounter-document
         basenames gated; .github/ leaves the PHI-content exemption. pre-push v1.5: a first push
         with no remote-tracking ref scans from the empty tree (was: the tip commit only —
         reproduced 1 of 3). scan-history v2.3: secrets in every blob; undecodable text counted.
         TEST RUNNER: unittest.main() sat mid-file since v1.9, so the direct command ran 128 of
         163 defined tests; the earlier "+N → M" counts were that undercount. Now 191, and the
         suite gate asserts the count. Residuals, documented: words between a name and its
         field; a surname at slug token 3+; prose with no field at all (v1.13 density gate).
  v1.11 — <clinical>-<ordinary-word> false-positive class (2026-09-15/16): PATH_SLUG takes
         the two tokens after the date, and Pattern 1 exempts only when BOTH are vocabulary,
         so 2026-04-12-hfnc-journal-club tripped on ('hfnc','journal') — likewise
         sepsis-bundle, asthma-pathway. Reproducing it showed the diagnosis was half right:
         'hfnc' was missing from the vocabulary too, so BOTH tokens needed adding. Fix is
         purely additive: hfnc plus 18 clinical-education / QI descriptors join
         DISEASE_ALLOWLIST. The both-tokens rule is untouched, so a surname
         beside any new word still blocks (smith-journal, martello-bundle — tested). The
         alternative, "either token clinical unless a surname", was rejected: no surname
         list exists and one can never be complete, so it would turn a fail-closed gate
         fail-open. +2 tests → 128.
  v1.10 — Alethoskopia audit F26/F28/F29 (2026-09-10): the staged file list is
         NUL-separated (a git-quoted name was re-read as a literal pathspec and went
         unscanned); a bracket is a placeholder only when EVERY comma-separated item is
         placeholder vocabulary (`[Patient Name, <real>, DOB <date>]` was stripped whole);
         Pattern 1 fires on the repo-relative `reasoning/` and `cases/` layouts the
         pre-commit hook actually sees, not only on a Maieutic/Themis/Nostos prefix.
  v1.9 — Alethoskopia audit F27/F30/F31 (2026-09-05): secret-token scanning runs on EVERY
         staged file (fixture/metadata path exemptions now apply to PHI-shape patterns
         only — a real key in .github/workflows/*.yml or package.json blocked nothing);
         the patient/plaintiff/defendant label is case-insensitive (`Patient Morgan …`
         evaded it); diagnostics REDACT the matched value (the blocked token was being
         copied into terminal history and logs); the bypass-flag advice is gone —
         hooks are never bypassed, a false positive is fixed in the allowlist.
  v1.8 — SLUG_NAME_ALLOWLIST added: exact (token1, token2) pairs vetted as
         non-patient are exempted from Pattern 1 (slug). First entry
         ("palmer","martello") = Ralph's dog / canine-cAD teaching dashboard,
         already in both Maieutic repos' history (Ralph sign-off 2026-07-13).
         Exact-pair match keeps a real patient sharing one token (e.g.
         john-martello) blocked. +2 tests (pass + adversarial control) → 126.
  v1.7 — UNION MERGE of two forked lineages. "v1.5" was accidentally minted
         twice: v1.5a (this repo, 2026-05-13) added the secret-token gate;
         v1.5b (Parent-Helper, 2026-06-19) was an independent recall-hardening
         pass. v1.6 built on v1.5a only, so each lineage blocked leaks the
         other allowed. v1.7 = strictest-wins union: v1.5b's data-file gate
         (renumbered Pattern 6), record-row matching, slug-on-paths, both-token
         slug allowlisting, NAME_SHAPE middle-initial/apostrophe, narrowed
         bracket strip, and broadened CRED_FILE — combined with v1.5a/v1.6's
         secret-token gate (Pattern 5), icons/ allowlist, and PHI-basename
         guard. DISEASE_ALLOWLIST = union vocab + ue/le (anatomical
         abbreviations, so known-legit slugs like -bilateral-ue-… survive the
         stricter both-token rule). Merged test suite; scan-history v2.0
         (blob-walk engine + multi-repo + secrets coverage); pre-push v1.2.
  v1.6 — icons/ allowlisted for Pattern 4 (Ralph sign-off 2026-07-02: the
         documented --no-verify escape for legit icon commits collides with
         the CLAUDE.md no---no-verify rule, so the escape hatch became a
         real allowlist entry). The v1.4-RC hole that forced the original
         revert (rogue icons/patient_chart.png) is closed the general way:
         NEW basename guard blocks PHI-suggestive binary names
         (patient|mrn|dob|chart|xray|imaging) even under allowlisted paths
         — docs/patient_chart.pdf now blocks too (it previously passed).
         favicons/ + logos/ stay non-allowlisted. DISEASE_ALLOWLIST gains
         the MSK/neuro descriptor block (ported from the deployed copy,
         which had drifted ahead of this source).
  v1.5b (Parent-Helper lineage) — Recall-hardening pass (closed
         false-negatives found in review): (1) structured-data gate
         (.csv/.tsv/.psv) — a patient line-list is the likeliest clinician
         leak and evaded both the binary gate and the label heuristics.
         (2) Pattern 2 also matches a value-shaped record row (name +
         DOB-value + id, e.g. a CSV line) — labels DOB/MRN need not appear
         literally. (3) Pattern 1 scans the staged file PATHS, not just diff
         content, so a patient-named file under Maieutic/Themis/Nostos can't
         slip in unechoed. (4) Disease allowlist requires BOTH slug tokens to
         be clinical (was: any single disease word exempted the whole slug,
         so 'johnson-asthma-r' passed). (5) NAME_SHAPE catches middle
         initials (John A. Smith) and apostrophes (O'Brien). (6) Bracket-
         placeholder strip narrowed to literal placeholder vocab (was: any
         [Cap Cap] pair, which immunized a real bracketed name). (7) CRED_FILE
         catches prefixed secrets (config-secrets.yaml) + .json.
  v1.5a — Added Pattern 5 (secret-token shape). Free-plan compensating
         control: confirmed 2026-05-13 that GitHub Advanced Security is
         required for secret scanning on private repos (422 'Advanced
         security has not been purchased' on rdmgator12). High-precision
         patterns with length anchors + word boundaries to minimize FP.
         AWS canonical doc fake (AKIAIOSFODNN7EXAMPLE) allowlisted.
         Stripe publishable keys (pk_live_) deliberately NOT blocked —
         public by design.
  v1.4 — Extracted scan logic into importable module. Added Pattern 4
         (binary-file gate) with path allowlist (assets/docs/images/
         screenshots/references/static/public/.github). icons/favicons/
         logos deliberately NOT allowlisted — tight gate beats clean scan.
         Fixed .env.production regex bug (v1.3 had `$` anchor that broke
         alt-group matching). Allowlisted .env.example / .env.sample /
         .env.template. Replaced content-allowlist short-circuit with
         strip-before-match (self-name and bracket placeholder no longer
         immunize real PHI on the same line). Split CONTENT_ALLOWLIST:
         Ralph self-name is case-sensitive, bracketed placeholder keeps
         IGNORECASE. Pattern 1 (slug) now respects FIXTURE_PATH via
         main()'s pre-filter — lets the hook's own test file (which
         contains synthetic patient-name slugs) commit without
         --no-verify. Added stdlib unittest suite under hooks/tests/
         (42 tests, zero deps). Added hooks/scan-history.py for
         retroactive full-history scans.
  v1.3 — Dropped bare "name:" label trigger (matched CI workflow step
         names like "name: Use Node"). Kept specific labels: patient,
         plaintiff, defendant, patient name. Added path allowlist for
         .github/, CaseTemplate/, plugin/marketplace/package metadata.
         Added content allowlist for "Ralph Martello" (self-identity
         is not PHI per feedback_ralph_name_public_repos.md).
  v1.2 — Python rewrite. Proper word boundaries, testable patterns.
         Fixed alternation-grouping bug.
  v1.1 — Pattern 2 tightened (name+PHI-field) + fixture allowlist.
  v1.0 — Initial 3-pattern gate.
"""

import re
import subprocess
import sys

# ----- Pattern 1: Maieutic/Themis/Nostos path slug with patient-name shape
PATH_SLUG = re.compile(
    r"(?:(?:[Mm]aieutic|[Tt]hemis|[Nn]ostos)/[A-Za-z0-9_/-]+"
    # v1.10 (F29): `git diff --name-only` hands the pre-commit hook REPO-RELATIVE paths, so
    # inside the Maieutic repo a case file is `reasoning/<date>-<first>-<last>-…` with no
    # project prefix — the rule never fired where it was installed. The case dirs by name;
    # a dated file anywhere else (docs/<date>-fix-list.md) is still not a slug.
    r"|(?<![A-Za-z0-9_-])(?:[Rr]easoning|[Cc]ases|[Nn]otes|[Ee]ncounters|[Pp]atients))"
    # v1.12: tokens are ANY case and the third token is OPTIONAL. Through v1.11 the regex demanded
    # `-[a-z]` after token 2 and lowercase tokens, so `reasoning/2026-05-12-<first>-<last>.md` and
    # `…-<First>-<Last>-r.md` never matched at all (2026-09-16 /poll review, 6 of 9 seats; both
    # reproduced). The slug ends at `-`, `.`, `/` or end-of-string.
    r"/\d{4}-\d{2}-\d{2}-([A-Za-z]+)-([A-Za-z]+)(?=[-./]|$)"
)
# v1.12: an UNDATED name-shaped file directly under a case dir — reasoning/<first>-<last>-followup.md.
# Same two-token rule; the date prefix was never the signal, the dir + first-last shape is.
UNDATED_CASE_SLUG = re.compile(
    r"(?<![A-Za-z0-9_-])(?:[Rr]easoning|[Cc]ases|[Nn]otes|[Ee]ncounters|[Pp]atients)"
    r"/([A-Za-z]+)-([A-Za-z]+)(?=[-./]|$)"
)

DISEASE_ALLOWLIST = re.compile(
    r"\b(kawasaki|dermatomyositis|crohns?|bromfed|adhd|incomplete|"
    r"respiratory|failure|syndrome|disease|treatment|resident|guide|"
    r"update|workup|optimization|pediatric|ddx|myositis|discharge|"
    r"hospital|emergency|dka|sepsis|bronchiolitis|asthma|pneumonia|"
    r"influenza|covid|case|pivot|mri|exam|"
    # anatomical/clinical descriptors for MSK/neuro case slugs. Used with
    # fullmatch on EACH captured token (v1.5b semantics): a slug passes only
    # when BOTH tokens are clinical vocabulary — hence the standalone ue/le
    # abbreviations, so 2026-..-bilateral-ue-entrapment-neuropathy stays green.
    r"bilateral|unilateral|entrapment|neuropathy|neuropathic|radiculopathy|"
    r"tunnel|plexus|epicondylitis|tendinopathy|tendinitis|carpal|cubital|"
    # v1.11: clinical-education / QI descriptors. Closes the <clinical>-<ordinary-word>
    # false-positive class WITHOUT touching the both-tokens rule — a surname paired with
    # any of these still blocks (smith-journal, martello-bundle: tested).
    r"hfnc|journal|club|bundle|pathway|protocol|guidelines?|handout|checklist|curriculum|"
    r"algorithm|teaching|lecture|conference|audit|qi|refresher|orderset|"
    r"ue|le)\b",
    re.IGNORECASE,
)

# ----- Slug name-pair allowlist — known-safe NON-patient names
# Exempted by EXACT (token1, token2) pair so a real patient who shares only one
# token (e.g. a different-first-name Martello) still blocks. Distinct from
# DISEASE_ALLOWLIST (clinical vocabulary): these are specific proper-noun pairs
# vetted as non-PHI.
#   ("palmer", "martello") = Ralph's dog — canine atopic-dermatitis teaching
#   dashboard slug (2026-04-11-palmer-martello-cad); already in the committed
#   history of both Maieutic repos. Ralph-approved 2026-07-13.
SLUG_NAME_ALLOWLIST = {
    ("palmer", "martello"),
}

# ----- Pattern 2: proper-noun name adjacent to PHI field
# A name token: capitalized first/last, allowing an internal apostrophe/hyphen compound
# (Mary-Jane, D'Angelo) or a cap-apostrophe-cap head (O'Brien). All-caps tokens (MRI, CT)
# are deliberately excluded — the first segment requires a lowercase tail.
# v1.12: Latin-script letters beyond ASCII (José, María, Müller, Nguyễn) — Florida is not ASCII.
# Loose classes on purpose: Latin-1 Supplement + Extended-A/B + Extended Additional; the SHAPE
# (capital head, lowercase tail, two tokens) still does the work.
_UP = r"[A-Z\u00C0-\u024F\u1E00-\u1EFF]"
_LO = r"[a-z\u00DF-\u024F\u1E00-\u1EFF]"
_NAME_TOKEN = (
    r"(?:" + _UP + _LO + r"{1,20}|" + _UP + r"['’]" + _UP + _LO + r"{1,20})"
    r"(?:[-'’]" + _UP + r"?" + _LO + r"{1,20})?"
)
# First [optional middle initial] Last — the middle initial closes the "John A. Smith" gap.
NAME_SHAPE = r"\b" + _NAME_TOKEN + r"(?:[ ][A-Z]\.?)?[ \-]" + _NAME_TOKEN + r"\b"
# v1.12: ALL-CAPS name shape — EHR exports and radiology headers print SMITH JOHN. Used ONLY beside a
# PHI-field co-signal, never alone (MRI CT would flood). 0 hits on 271,221 real lines with the co-signal.
CAPS_NAME_SHAPE = r"\b[A-Z]{2,20}(?:[ ][A-Z]\.)?[ ,][ ]?[A-Z]{2,20}\b"
# v1.12: SSN label joins the PHI fields (the human phi-sweep battery had it; the hook did not).
PHI_FIELD = (
    r"\b(DOB|MRN|dob|mrn|date[_ ]of[_ ]birth|insurance[_ ]?id|"
    r"SSN|ssn|Ssn|social[_ ]security|Social[_ ]Security|SOCIAL[_ ]SECURITY)\b"
)
_GAP = r"[^A-Za-z\n]{0,60}"  # v1.12 note: a word-tolerant gap was priced on real lines and REJECTED for FPs — words between a name and its field remain a documented residual.
# v1.12 value shapes. A 3-2-4 hyphenated number is an SSN often enough, and rare enough otherwise
# (0 hits on 271,221 tracked lines), to be a STANDALONE finding. A phone number is not PHI by itself —
# every README carries one — so it counts only within 60 chars of a name-shaped pair. Priced against
# v1.11 on 272,209 tracked lines: +8 lines newly flagged by this rule (business-name + phone lines
# included — "Golf Shop: 727-…" is a proper-noun pair and blocks; that is the accepted cost).
SSN_VALUE = re.compile(r"(?<![\d-])\d{3}-\d{2}-\d{4}(?![\d-])")
_PHONE_VALUE = r"(?:\(\d{3}\)|\d{3})[-. ]\d{3}[-. ]\d{4}(?!\d)"

NAME_THEN_PHI = re.compile(NAME_SHAPE + _GAP + PHI_FIELD)
PHI_THEN_NAME = re.compile(PHI_FIELD + _GAP + NAME_SHAPE)              # v1.12: `MRN 1234567 <First> <Last>`
CAPS_NAME_THEN_PHI = re.compile(CAPS_NAME_SHAPE + _GAP + PHI_FIELD)    # v1.12: `<LAST> <FIRST> DOB …`
PHI_THEN_CAPS_NAME = re.compile(PHI_FIELD + _GAP + CAPS_NAME_SHAPE)
NAME_NEAR_PHONE = re.compile(NAME_SHAPE + _GAP + _PHONE_VALUE + r"|" + _PHONE_VALUE + _GAP + NAME_SHAPE)
LABEL_THEN_NAME = re.compile(
    r"\b(?i:patient[\s_-]?name|plaintiff|defendant|patient)\b"
    r"[\s\'\"`:=]{1,10}"
    r"[\'\"`]?" + NAME_SHAPE
)

# ----- Pattern 7 (v1.13): proper-noun name in clinical PROSE — no field label at all.
# The only class that has actually leaked from these repos (Themis 2026-07-02: `Source 1 RN, <Surname>`,
# staff names with credentials, a case caption). Every rule below was priced on 238,362 tracked lines
# (tools/price-pattern.py) BEFORE adoption: name+age 11, title+name 25, name+credential 27, credential+name 0
# raw; the survivors after the self-name and demonym strips are listed in the changelog. REJECTED on the
# same corpus: name+date (285 — changelogs), a case caption `X v. Y` (135 — Themis IS case law; the active
# case's caption is the opt-in blocklist layer's job), name+clinical verb (1,363), name+facility (56),
# name + any two signals (34). Bare 6–10-digit numbers were never a candidate (PMIDs are 8 digits).
# Age: an `N-year-old` / `Nyo` form within 30 chars of a name pair (an 80-char gap let a Title Case tool
# name 50 chars before an age through, twice); an age token glued to a slug or link character (`12yo](`,
# `12yo-treatment`) is filename text, not prose; the `aged N` form only when it directly follows the
# pair (`<First> <Last>, aged 45`, `<First> <Last> (aged 45)`) — `children aged 2-6` beside any Title
# Case phrase was the corpus's whole false-positive class for that form.
_GAP30 = r"[^\n]{0,30}?"
AGE_OLD = r"\b(?:\d{1,3}[- ](?:year|yr|month|mo|week|wk|day)s?[- ]old|\d{1,2}\s?(?:yo|y/o|m/o))\b(?![-_/\]])"
AGE_AGED = r"\b(?:age|aged)\s+\d{1,3}\b"
NAME_NEAR_AGE = re.compile(
    NAME_SHAPE + _GAP30 + AGE_OLD + r"|" + AGE_OLD + _GAP30 + NAME_SHAPE
    + r"|" + NAME_SHAPE + r"[ ,(]{1,3}" + AGE_AGED
)
# Credentials: clinical only — PhD / Esq / JD are deliberately absent (an engineer or a lawyer is not PHI).
# Two tiers, priced: a STRONG credential is unambiguous after a single surname (`<Surname> RN`), unless the
# line is an author list (`<Surname> RN et al`, `<Surname> RN, <Surname> J`). The AMBIGUOUS two-letter ones
# collide with states, prior-auth, author initials and "Standardized MD" (8 corpus lines: `Pittsburgh, PA`,
# `Build PA`, `Tatonetti NP et al`, `Breton MD et al`), so they count only after a two-token name pair with
# the comma (`<First> <Last>, MD`; `<First> <Last>, PA-C`). A bare `<Surname> MD` is a documented residual.
_CRED_STRONG = r"(?:RN|LPN|CRNA|RPh|PharmD|APRN|MSN|BSN)"
_CRED_AMBIG = r"(?:MD|DO|NP|PA|RT)"
_CRED = r"(?:" + _CRED_STRONG + r"|" + _CRED_AMBIG + r")"
_NOT_AUTHOR_LIST = r"(?!\s*(?:et al|,\s*" + _UP + _LO + r"+\s+[A-Z]{1,3}\b))"
# Space-separated pair only: NAME_SHAPE also joins tokens with a hyphen, which made a hyphenated
# locality triplet (`<City>-<City>-<City>, MD`) read as a name pair beside a state.
_SPACED_PAIR = r"\b" + _NAME_TOKEN + r"(?:[ ][A-Z]\.?)?[ ]" + _NAME_TOKEN + r"\b"
TITLE_THEN_NAME = re.compile(r"\b(?:Dr|Doctor|Nurse)\.?\s+" + _NAME_TOKEN + r"\b")   # `Dr. <Surname> ordered`
NAME_THEN_CRED = re.compile(
    r"\b" + _NAME_TOKEN + r",?\s+" + _CRED_STRONG + r"\b" + _NOT_AUTHOR_LIST            # `<Surname> RN`
    + r"|" + _SPACED_PAIR + r",\s+" + _CRED_AMBIG + r"\b" + _NOT_AUTHOR_LIST            # `<First> <Last>, MD`
)
CRED_THEN_NAME = re.compile(                                                             # `Source 1 RN, <Surname>`
    r"\b" + _CRED + r",\s+" + _NAME_TOKEN + r"\b(?!\s+[A-Z]{1,3}\b[,.])"                # …but not `RN, <Surname> J,` (author list)
)

# ----- Content allowlist — known-safe proper-noun phrases
# Ralph's own name is case-sensitive (proper noun, not a substring match).
# Bracketed placeholders like [Patient Name, DOB] are template literals.
# v1.13: middle-initial and title forms (`Ralph D. Martello, MD`, `Dr. Martello`) — Pattern 7 priced 27
# credential hits on the corpus and nearly all were this byline. Bounded to Ralph's own name: a family
# member sharing the surname still blocks.
SELF_NAME_ALLOW = re.compile(r"\b(?:Dr\.?\s+)?Ralph(?:\s+D\.?)?\s+Martello\b|\bDr\.?\s+Martello\b")
# v1.13: a compound demonym is name-SHAPED and not a name. The bias-reference vignettes read
# `45yo African American M`, which Pattern 7's name+age rule would otherwise flag.
DEMONYM_PAIR_ALLOW = re.compile(
    r"\b(?:African|Native|Asian|Hispanic|Latin|Pacific|Middle|South|North|Central|East|West|Alaska)"
    r"[ -](?:American|Islander|Eastern|Asian|African|Latino|Latina|Native)s?\b"
)
# Strip ONLY literal placeholder vocabulary, never an arbitrary [Cap Cap] pair — the old
# `[A-Z][a-z]+ [A-Z][a-z]+` form stripped a real bracketed `[<First> <Last>, DOB ...]` and
# immunized it.
_PLACEHOLDER_VOCAB = (
    r"(?:patient[\s_-]?name|full[\s_-]?name|first[\s_-]?(?:and[\s_-]?)?last|"
    r"first[\s_-]?name|last[\s_-]?name|name|patient|first|last|"
    r"dob|mrn|date[\s_-]?of[\s_-]?birth|insurance[\s_-]?id|"
    # v1.12: `insert[\s\w]*` / `your[\s\w]*` swallowed a real name — `[Insert <First> <Last> here]` was
    # stripped whole and immunised the name beside it (reproduced 2026-09-16). Bounded to placeholder words.
    r"insert(?:[\s_-]+(?:name|here|value|text|info|details|your|the|a|an|patient|date|id))*|"
    r"your(?:[\s_-]+(?:name|patient|info|details|value|text|here|date|id))*)"
)
# v1.10 (F28): a bracket is a placeholder only when EVERY comma-separated item is placeholder
# vocabulary. The v1.5b tail `(?:,[^\]]*)?` let `[Patient Name, <real name>, DOB <date>]` be
# stripped whole — one placeholder word immunised the real values beside it.
BRACKET_PLACEHOLDER_ALLOW = re.compile(
    r"\[" + _PLACEHOLDER_VOCAB + r"(?:\s*,\s*" + _PLACEHOLDER_VOCAB + r")*\s*\]",
    re.IGNORECASE,
)

# ----- Pattern 3: credential files
# .env, .env.production, .env.local are blocked.
# .env.example / .env.sample / .env.template are template files and pass.
# (v1.3 regex had a bug: `\.env($|\.)` + trailing `$` failed to match `.env.production`
#  because the outer `$` required end-of-string immediately after the alt group.)
CRED_FILE = re.compile(
    r"(^|/)("
    r"\.env(\.(?!(?:example|sample|template)\b)[^/]*)?|"
    r"credentials\.json|"
    r"[^/]*secrets?\.(?:ya?ml|json)|"  # secrets.yaml, config-secrets.yaml, app-secrets.json
    r"[^/]*private_key[^/]*|"
    # v1.12: key-material file shapes (2026-09-16 /poll review, muse-spark). Bare .pem is NOT
    # blocked — cert bundles (fullchain.pem) are public; a .pem whose name says key/private/secret is.
    r"[^/]*\.(?:key|p12|pfx)|"
    r"[^/]*(?:key|private|secret)[^/]*\.pem|"
    r"id_(?:rsa|ed25519|ecdsa|dsa)(?!\.pub)"
    r")$"
)

# ----- Pattern 4: PHI-risk binary extensions
# Any file of these types anywhere NOT under a binary allowlist path is blocked.
BINARY_RISK = re.compile(
    # v1.12 adds mail containers, archives and audio/video (dictation, screen recordings) — none is
    # content-scannable, so all are gated like PDFs (2026-09-16 /poll review, qwen + muse).
    r"\.(pdf|docx?|xlsx?|pptx?|png|jpe?g|tiff?|dcm|dicom|heic|webp|gif|bmp|"
    r"msg|eml|zip|7z|gz|tgz|tar|rar|mp3|wav|m4a|mp4|mov)$",
    re.IGNORECASE,
)
# Allowlisted locations for legitimate binaries (docs, research papers, architecture
# diagrams, license graphics, etc.). Paths matched anywhere in the file path.
BINARY_ALLOW_PATH = re.compile(
    r"(^|/)("
    r"assets/|docs/|doc/|images/|img/|screenshots/|references/|"
    r"\.github/|static/|public/|icons/"
    r")"
)
# NOTE: `favicons/` and `logos/` are deliberately NOT allowlisted (tight gate >
# clean scan). `icons/` allowlisted v1.6 with sign-off; the rogue-binary hole
# is closed by BINARY_PHI_BASENAME below instead of path exclusion.

# PHI-suggestive basenames block EVERYWHERE — even under allowlisted paths.
# Closes the v1.4-RC hole (icons/patient_chart.png) generally: the same rogue
# file under docs/ or assets/ used to pass. Tight list to limit false
# positives; extend deliberately, not reflexively.
BINARY_PHI_BASENAME = re.compile(
    # v1.12 adds encounter-document vocabulary (2026-09-16 /poll review, 5 seats). Deliberately NOT
    # bare `note` / `summary` — release-notes.pdf is a real file; discharge_summary.pdf is the leak.
    r"(^|/)[^/]*(patient|mrn|dob|chart|x[-_]?ray|imaging|"
    r"discharge|admission|consult|referral|encounter|ehr|emr|hpi|h[-_]?and[-_]?p|"
    r"progress[-_]?note|clinic[-_]?note|visit)[^/]*"
    r"\.(pdf|docx?|xlsx?|pptx?|png|jpe?g|tiff?|dcm|dicom|heic|webp|gif|bmp|msg|eml|zip|7z|gz|tgz|tar|rar|mp3|wav|m4a|mp4|mov)$",
    re.IGNORECASE,
)

# ----- Pattern 5: secret tokens (v1.5)
# All patterns use length anchors + word boundaries to minimize FP.
# Tuned for free-plan personal accounts where GitHub Advanced Security secret
# scanning is paywalled.
SECRET_PATTERNS = [
    # Anthropic: sk-ant-api03-... or sk-ant-admin01-... (~108 char real shape)
    ("anthropic", re.compile(r"sk-ant-(?:api|admin)\d{2}-[A-Za-z0-9_-]{86,}")),
    # OpenAI modern project key: sk-proj-... (≥40 char alnum+_- suffix)
    ("openai_proj", re.compile(r"sk-proj-[A-Za-z0-9_-]{40,}")),
    # OpenAI legacy: sk- + exactly 48 alnum chars
    ("openai_legacy", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9]{48}(?![A-Za-z0-9])")),
    # AWS access key ID (permanent + temporary). 4-letter prefix + 16 alnum.
    (
        "aws_access_key",
        re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[0-9A-Z]{16}(?![0-9A-Z])"),
    ),
    # GitHub classic PAT / OAuth / server / refresh / user tokens
    (
        "github_token",
        re.compile(r"(?<![A-Za-z0-9_])gh[poshru]_[A-Za-z0-9]{36}(?![A-Za-z0-9])"),
    ),
    # GitHub fine-grained PAT
    (
        "github_pat_fg",
        re.compile(r"(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{82}(?![A-Za-z0-9_])"),
    ),
    # Google API key
    (
        "google_api",
        re.compile(r"(?<![A-Za-z0-9_])AIza[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"),
    ),
    # Slack tokens (bot/app/user/refresh/oauth)
    (
        "slack",
        re.compile(r"(?<![A-Za-z0-9])xox[abprso]-[A-Za-z0-9-]{10,}(?![A-Za-z0-9-])"),
    ),
    # Stripe live secret + restricted keys. pk_live_ (publishable) is public by
    # design — NOT blocked.
    (
        "stripe_live",
        re.compile(r"(?<![A-Za-z0-9])(?:sk|rk)_live_[A-Za-z0-9]{24,}(?![A-Za-z0-9])"),
    ),
    # PEM private key headers (RSA / EC / DSA / OPENSSH / generic PRIVATE)
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# Doc-friendly allowlist — strip known fake credentials before scanning.
# AWS canonical example key is documented across AWS materials and tutorials.
# No word-boundary anchors: AWS access keys are exactly 20 chars, so the
# canonical fake cannot appear as a substring of a real key. Boundary-free
# match also avoids self-FP on the regex source line where the literal is
# preceded by `\b` (a word char that blocks the boundary).
SECRET_DOC_ALLOWLIST = re.compile(r"AKIAIOSFODNN7EXAMPLE")

# ----- Pattern 6: structured-data files + value-shaped PHI records (v1.5b)
# CSV/TSV/PSV are almost always data exports (a line-list of patients is the single most
# likely PHI leak for a clinician) and are rarely legitimate source files, so they're gated
# outside the binary/fixture allowlists just like binaries.
DATA_FILE_RISK = re.compile(r"\.(csv|tsv|psv)$", re.IGNORECASE)

# A record row carrying VALUES rather than the literal labels DOB/MRN evades Pattern 2
# (Pattern 2 keys on the words "DOB"/"MRN", not on a date or an id value). Catch the strong
# record signature: a name, a date-of-birth-shaped value, and an id number, delimited by
# comma/tab/pipe — e.g. `<First> <Last>,YYYY-MM-DD,<id>`. The three-field shape keeps false
# positives low (prose with a bare date has no trailing delimited id).
_DOB_VALUE = (
    r"(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/](?:19|20)?\d{2}"
)
RECORD_ROW = re.compile(
    NAME_SHAPE + r"\s*[,\t|]\s*(?:" + _DOB_VALUE + r")\s*[,\t|]\s*\d{3,}"
)
# v1.12: the `Last, First` export layout (0 FP on 271,221 real lines).
LAST_FIRST = r"\b" + _NAME_TOKEN + r",\s*" + _NAME_TOKEN + r"\b"
RECORD_ROW_LAST_FIRST = re.compile(
    LAST_FIRST + r"\s*[,\t|]\s*(?:" + _DOB_VALUE + r")\s*[,\t|]\s*\d{3,}"
)
# v1.12: `<Last>, <First> DOB 01/01/1990` — the Last, First label form (priced: see changelog).
LAST_FIRST_THEN_PHI = re.compile(LAST_FIRST + _GAP + PHI_FIELD)
# v1.12: ID-first layout `4432101,<First> <Last>,1990-01-01`; the id must be MRN-length (7+ digits).
RECORD_ROW_ID_FIRST = re.compile(
    r"(?:^|[,\t|])\s*\d{7,}\s*[,\t|]\s*" + NAME_SHAPE + r"\s*[,\t|]\s*(?:" + _DOB_VALUE + r")"
)

# ----- Path allowlist for synthetic-fixture directories AND metadata files
FIXTURE_PATH = re.compile(
    r"(^|/)("
    r"TestCase_|tests?/|test_data/|test-fixtures/|"
    r"fixtures/|scripts/test[-_]|scripts/demo[-_]|scripts/smoke[-_]|"
    r"demo_case/|"   # v1.13: a synthetic demo record set (SourceMind) — same class as scripts/demo-
    r"demo_cases\.ts|test-complex-case\.ts|"
    # v1.12: `.github/` is no longer a PHI-content exemption — an ISSUE_TEMPLATE or workflow note
    # carrying a name+DOB was never fed to Pattern 2. It stays in BINARY_ALLOW_PATH (binaries
    # under .github/ are unaffected) and secrets were already scanned there since v1.9.
    r"CaseTemplate/|"
    r"plugin\.json|marketplace\.json|package\.json|package-lock\.json|"
    r"LICENSE"
    r")"
)


def staged_files():
    # v1.10 (F26): -z — git quotes unusual names ("note\\tsecret.txt") in the newline format,
    # and the quoted string fed back as a pathspec matched nothing, so the file went unscanned.
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRT"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [f for f in r.stdout.split("\0") if f]


def staged_diff(files):
    if not files:
        return ""
    r = subprocess.run(
        ["git", "diff", "--cached", "--"] + files,
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout


def added_lines(diff_text):
    return [
        line
        for line in diff_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


def strip_allowlisted(line):
    """Remove allowlisted substrings (self-name, bracket placeholders) from a line
    before Pattern 2 matching. Prevents the escape hatch where a placeholder or
    self-name on the same line as real PHI would short-circuit the scan.

    Example: '[Patient Name]: <FIRST> <LAST>, DOB YYYY-MM-DD'
             → ': <FIRST> <LAST>, DOB YYYY-MM-DD'  (unstripped portion still
             feeds NAME_THEN_PHI when real shapes are present)
    """
    line = SELF_NAME_ALLOW.sub("", line)
    line = BRACKET_PLACEHOLDER_ALLOW.sub("", line)
    line = DEMONYM_PAIR_ALLOW.sub("", line)  # v1.13
    return line


def scan_slug(diff_lines):
    """Pattern 1. Input: iterable of raw diff lines (or file paths). Returns
    [(line, match), ...].

    A slug is allowlisted only when BOTH descriptive tokens are clinical vocabulary.
    (Old bug: `DISEASE_ALLOWLIST.search(slug)` exempted the whole slug if ANY single
    word matched, so 'johnson-asthma-r' passed because 'asthma' is allowlisted.)
    """
    hits = []
    for line in diff_lines:
        for rx in (PATH_SLUG, UNDATED_CASE_SLUG):
            found = False
            for m in rx.finditer(line):
                t1, t2 = m.group(1).lower(), m.group(2).lower()
                if (t1, t2) in SLUG_NAME_ALLOWLIST:
                    continue  # vetted non-patient name (e.g. Ralph's dog)
                if _slug_token_ok(t1) and _slug_token_ok(t2):
                    continue  # clinical-topic slug, not a patient name
                hits.append((line.rstrip(), m.group(0)))
                found = True
                break
            if found:
                break
    return hits


DATE_TEMPLATE_TOKEN = re.compile(r"yyyy|yy|mm|dd")  # v1.12.1: doc templates, `reasoning/YYYY-MM-DD-[topic]`


def _slug_token_ok(token):
    """A slug token is not name-shaped when it is clinical vocabulary, a single case letter
    (the `2026-04-18-case-A` convention — v1.12 census: 29 real case dirs, none name-shaped),
    or a date-template placeholder (v1.12.1: the undated variant matched `reasoning/YYYY-MM`
    in Maieutic's own docs — four lines, first seen on the reinit root commit)."""
    return (len(token) == 1 or bool(DISEASE_ALLOWLIST.fullmatch(token))
            or bool(DATE_TEMPLATE_TOKEN.fullmatch(token)))


def scan_name_phi(diff_lines):
    """Pattern 2. Input: iterable of raw diff lines (already fixture-filtered).
    Returns [(line, match), ...].

    Allowlisted substrings (Ralph's self-name, bracket placeholders) are stripped
    before matching so they can't immunize real PHI that shares the same line.
    """
    hits = []
    for line in diff_lines:
        stripped = strip_allowlisted(line)
        hit = (
            NAME_THEN_PHI.search(stripped)
            or PHI_THEN_NAME.search(stripped)
            or LABEL_THEN_NAME.search(stripped)
            or CAPS_NAME_THEN_PHI.search(stripped)
            or PHI_THEN_CAPS_NAME.search(stripped)
            or NAME_NEAR_PHONE.search(stripped)
            or RECORD_ROW.search(stripped)
            or RECORD_ROW_LAST_FIRST.search(stripped)
            or LAST_FIRST_THEN_PHI.search(stripped)
            or RECORD_ROW_ID_FIRST.search(stripped)
        )
        if hit:
            hits.append((line.rstrip(), hit.group(0)))
    return hits


def scan_ssn(diff_lines):
    """v1.12 — a standalone SSN-shaped value (3-2-4). Returns [(line, match), ...]."""
    hits = []
    for line in diff_lines:
        m = SSN_VALUE.search(strip_allowlisted(line))
        if m:
            hits.append((line.rstrip(), m.group(0)))
    return hits


def scan_prose(diff_lines):
    """Pattern 7 (v1.13). Input: raw diff lines (already fixture-filtered). Returns [(line, match), ...].

    Same allowlist strip as Pattern 2, so a self-name byline or a bracket placeholder on the line
    cannot immunise a real name beside it.
    """
    hits = []
    for line in diff_lines:
        stripped = strip_allowlisted(line)
        hit = (
            NAME_NEAR_AGE.search(stripped)
            or TITLE_THEN_NAME.search(stripped)
            or NAME_THEN_CRED.search(stripped)
            or CRED_THEN_NAME.search(stripped)
        )
        if hit:
            hits.append((line.rstrip(), hit.group(0)))
    return hits


def scan_credentials(files):
    """Pattern 3. Returns list of offending file paths."""
    return [f for f in files if CRED_FILE.search(f)]


def scan_binaries(files):
    """Pattern 4. Returns list of offending binary file paths outside allowlists.

    v1.6: a PHI-suggestive basename (BINARY_PHI_BASENAME) blocks even under
    allowlisted paths — only FIXTURE_PATH (synthetic data) exempts it.
    """
    hits = []
    for f in files:
        if not BINARY_RISK.search(f):
            continue
        if FIXTURE_PATH.search(f):
            continue
        if BINARY_PHI_BASENAME.search(f):
            hits.append(f)
            continue
        if BINARY_ALLOW_PATH.search(f):
            continue
        hits.append(f)
    return hits


def scan_secrets(diff_lines):
    """Pattern 5. Returns [(line, kind, match), ...].

    Doc-allowlisted fake credentials (AKIAIOSFODNN7EXAMPLE) are stripped from
    the line before regex evaluation so a real token on the same line as a
    placeholder can't be smuggled in. One finding per line.
    """
    hits = []
    for line in diff_lines:
        cleaned = SECRET_DOC_ALLOWLIST.sub("", line)
        for kind, pat in SECRET_PATTERNS:
            m = pat.search(cleaned)
            if m:
                hits.append((line.rstrip(), kind, m.group(0)))
                break
    return hits


def scan_data_files(files):
    """Pattern 6. Structured-data files (.csv/.tsv/.psv) outside allowlists — patient
    line-list exports that evade both the binary gate and the content label heuristics.
    """
    hits = []
    for f in files:
        if not DATA_FILE_RISK.search(f):
            continue
        # v1.12: BINARY_ALLOW_PATH no longer exempts data files. `docs/census.csv` passed here
        # through v1.11 — the 2026-09-16 /poll review's most-converged finding (6 of 9 seats) —
        # while the docstring called a patient line-list the likeliest clinician leak. Only a
        # fixture path (synthetic data by declaration) exempts a CSV/TSV/PSV.
        if FIXTURE_PATH.search(f):
            continue
        hits.append(f)
    return hits


_TOKEN_RUN = r"[A-Za-z0-9_\-./+=:]{0,200}"


def redact(line, needle):
    """v1.9 (F31): the diagnostic names WHERE and WHAT KIND, never the value. `needle` is
    the matched text (or `kind:prefix40` for secrets); the whole token run around it is
    replaced, so a truncated prefix cannot leak the head of a key."""
    if not needle:
        return line
    cands = [needle]
    if ":" in needle and len(needle.split(":", 1)[0]) < 20:
        cands.append(needle.split(":", 1)[1])
    for cand in cands:
        if cand and cand in line:
            m = re.search(re.escape(cand) + _TOKEN_RUN, line)
            s, e = m.span()
            # v1.12: only a bounded window around the match is shown. The whole-line form printed
            # everything BEFORE the needle verbatim — a second name 35 chars earlier on the line
            # reached the terminal and shell history (2026-09-16 /poll review, minimax-m3;
            # reproduced). 20 chars each side keeps the finding locatable.
            pre, post = line[max(0, s - 20):s], line[e:e + 20]
            return ("…" if s > 20 else "") + pre + "[REDACTED]" + post + ("…" if e + 20 < len(line) else "")
    return "[REDACTED]"


def run_scan(files, diff_lines, slug_paths=None, secret_lines=None):
    """Pure scan orchestrator. Returns list of (kind, detail, match) tuples.

    `diff_lines` should be the added-line set from non-fixture files only.
    `slug_paths`, when given, are non-fixture file PATHS scanned with Pattern 1 — a
    patient-named file under Maieutic/Themis/Nostos must be caught even if the slug
    never appears in the file's content (the path lives only in diff headers, which
    added_lines() strips). Callers that need Pattern 1 universally call scan_slug() directly.
    """
    fails = []
    for line, m in scan_slug(diff_lines):
        fails.append(("slug", line, m))
    for line, m in scan_slug(slug_paths or []):
        fails.append(("slug", line, m))
    for line, m in scan_name_phi(diff_lines):
        fails.append(("name_phi", line, m))
    for line, m in scan_ssn(diff_lines):
        fails.append(("ssn", line, m))
    for line, m in scan_prose(diff_lines):  # v1.13
        fails.append(("prose", line, m))
    # v1.9 (F27): secrets are scanned in EVERY file — a fixture/metadata exemption is a
    # statement about PHI-shaped test data, not about credentials.
    for line, kind, m in scan_secrets(secret_lines if secret_lines is not None else diff_lines):
        fails.append(("secret", line, f"{kind}:{m[:40]}"))
    for f in scan_credentials(files):
        fails.append(("credential", f, f))
    for f in scan_binaries(files):
        fails.append(("binary", f, f))
    for f in scan_data_files(files):
        fails.append(("data", f, f))
    return fails


def main():
    files = staged_files()
    if not files:
        return 0

    non_fixture = [f for f in files if not FIXTURE_PATH.search(f)]
    diff_nf = staged_diff(non_fixture) if non_fixture else ""
    diff_all = staged_diff(files)

    fails = run_scan(
        files=files,
        diff_lines=added_lines(diff_nf),
        slug_paths=non_fixture,
        secret_lines=added_lines(diff_all),
    )

    if not fails:
        return 0

    slug_hits = [f for f in fails if f[0] == "slug"]
    name_hits = [f for f in fails if f[0] in ("name_phi", "ssn")]
    cred_hits = [f for f in fails if f[0] == "credential"]
    bin_hits = [f for f in fails if f[0] == "binary"]
    secret_hits = [f for f in fails if f[0] == "secret"]
    data_hits = [f for f in fails if f[0] == "data"]
    prose_hits = [f for f in fails if f[0] == "prose"]  # v1.13

    if slug_hits:
        print(
            "❌ pre-commit: possible patient-name slug in Maieutic/Themis/Nostos path:"
        )
        for _, line, m in slug_hits[:5]:
            print(f"    {redact(line, m)[:140]}")
        print()
        print("   Reference cases by number + clinical topic only.")
        print("   Example: 'Maieutic Case 36 — MRI + exam DDx pivot dashboard'")
        print()

    if name_hits:
        print(
            "⚠️  pre-commit: proper-noun name adjacent to PHI field (DOB/MRN/SSN/insurance/phone/patient), or an SSN:"
        )
        for _, line, m in name_hits[:5]:
            print(f"    {redact(line, m)[:140]}")
        print()
        print("   If this is synthetic test data, move it under one of:")
        print("     TestCase_*/ | fixtures/ | test_data/ | tests/fixtures/")
        print("     scripts/test-* | scripts/demo-*")
        print("   Or rename identifiers to obvious placeholders (TEST_USER_001, etc.).")
        print("   Ralph's own name / a public figure: add the exact pair to SLUG_NAME_ALLOWLIST or")
        print("   SELF_NAME_ALLOW in phi_hook.py. Hooks are never bypassed.")
        print()

    if prose_hits:
        print(
            "⚠️  pre-commit: proper-noun name in clinical prose (beside an age, a title, or a credential):"
        )
        for _, line, m in prose_hits[:5]:
            print(f"    {redact(line, m)[:140]}")
        print()
        print("   A staff or patient name needs no field label to be PHI. Use a role, or a")
        print("   placeholder (<First> <Last>, <Surname>); synthetic vignettes go under a fixture path.")
        print("   Ralph's own byline forms are allowlisted in SELF_NAME_ALLOW. Hooks are never bypassed.")
        print()

    if cred_hits:
        print("❌ pre-commit: credential/env file in staged diff:")
        for _, f, _ in cred_hits:
            print(f"    {f}")
        print()

    if bin_hits:
        print("❌ pre-commit: PHI-risk binary file in staged diff:")
        for _, f, _ in bin_hits:
            print(f"    {f}")
        print()
        print("   Move legitimate binaries under one of:")
        print("     assets/ | docs/ | images/ | references/ | screenshots/")
        print("   Or for test fixtures: tests/ | fixtures/ | TestCase_*/")
        print("   Otherwise: confirm no patient info is in the file and add its path to")
        print("   BINARY_ALLOW_PATH in phi_hook.py. Hooks are never bypassed.")
        print()

    if secret_hits:
        print("❌ pre-commit: secret / API-token shape in staged diff:")
        for _, line, m in secret_hits[:5]:
            print(f"    [{m.split(':', 1)[0]}]  in:  {redact(line, m)[:120]}")
        print()
        print("   If this is a REAL token: rotate it now, then redact + recommit.")
        print("   If this is a doc/test placeholder, use one of:")
        print("     - truncate the value (e.g., 'sk-ant-api03-...')")
        print("     - use 'AKIAIOSFODNN7EXAMPLE' (AWS canonical fake)")
        print("     - move the file under tests/ | fixtures/ | scripts/test-*")
        print()

    if data_hits:
        print("❌ pre-commit: structured-data file (.csv/.tsv) in staged diff:")
        for _, f, _ in data_hits:
            print(f"    {f}")
        print()
        print("   CSV/TSV exports are a common patient-list leak. If this is synthetic")
        print("   or non-PHI reference data, move it under tests/ | fixtures/ | test_data/.")
        print("   No other location exempts a data file (v1.12). Hooks are never bypassed.")
        print()

    print("Commit blocked. See feedback_no_phi_in_repos.md for policy.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
