"""PHI pre-commit hook — v1.9 (2026-09-05, Python).

Importable module. Entry point is `main()`. `pre-commit` is a thin wrapper.

Six-pattern gate:
1. Patient-name slugs in Maieutic/Themis/Nostos reasoning paths (scans staged
   content AND the staged file paths themselves)
2. Proper-noun name adjacent to PHI field (DOB/MRN/insurance/patient/plaintiff),
   incl. value-shaped record rows (name + DOB-value + id) like a CSV line
3. Credential files (.env, credentials.json, *secrets.{yml,json}, *private_key*)
4. PHI-risk binary files (pdf/docx/xlsx/png/jpg/tif/dcm) outside allowlisted
   paths; PHI-suggestive basenames block even under allowlisted paths
5. API-token / secret shapes (Anthropic, OpenAI, AWS, GitHub, Google, Slack,
   Stripe live, private-key PEM blocks). Tight regex + length anchors;
   truncated doc placeholders (sk-..., AKIAIOSFODNN7EXAMPLE) pass.
6. Structured-data files (.csv/.tsv/.psv) outside allowlisted paths

Path allowlist skips synthetic-fixture directories:
  TestCase_*/ | fixtures/ | test_data/ | tests/fixtures/ |
  test-fixtures/ | scripts/test-* | scripts/demo-*

Install (per repo): ln -sf ../../hooks/pre-commit .git/hooks/pre-commit
There is no override flag: a false positive is fixed in the allowlists below.
Full-history audit (existing repos): python hooks/scan-history.py

Changelog:
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
    r"(?:[Mm]aieutic|[Tt]hemis|[Nn]ostos)"
    r"/[A-Za-z0-9_/-]+/\d{4}-\d{2}-\d{2}-([a-z]+)-([a-z]+)-[a-z]"
)

DISEASE_ALLOWLIST = re.compile(
    r"\b(kawasaki|dermatomyositis|crohns?|bromfed|adhd|incomplete|"
    r"respiratory|failure|syndrome|disease|treatment|resident|guide|"
    r"update|workup|optimization|pediatric|ddx|myositis|discharge|"
    r"hospital|emergency|dka|sepsis|bronchiolitis|asthma|pneumonia|"
    r"influenza|covid|case-update|pivot-protocol|mri|exam|"
    # anatomical/clinical descriptors for MSK/neuro case slugs. Used with
    # fullmatch on EACH captured token (v1.5b semantics): a slug passes only
    # when BOTH tokens are clinical vocabulary — hence the standalone ue/le
    # abbreviations, so 2026-..-bilateral-ue-entrapment-neuropathy stays green.
    r"bilateral|unilateral|entrapment|neuropathy|neuropathic|radiculopathy|"
    r"tunnel|plexus|epicondylitis|tendinopathy|tendinitis|carpal|cubital|"
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
_NAME_TOKEN = (
    r"(?:[A-Z][a-z]{1,20}|[A-Z]['’][A-Z][a-z]{1,20})" r"(?:[-'’][A-Z]?[a-z]{1,20})?"
)
# First [optional middle initial] Last — the middle initial closes the "John A. Smith" gap.
NAME_SHAPE = r"\b" + _NAME_TOKEN + r"(?:[ ][A-Z]\.?)?[ \-]" + _NAME_TOKEN + r"\b"
PHI_FIELD = r"\b(DOB|MRN|dob|mrn|date[_ ]of[_ ]birth|insurance[_ ]?id)\b"

NAME_THEN_PHI = re.compile(NAME_SHAPE + r"[^A-Za-z\n]{0,60}" + PHI_FIELD)
LABEL_THEN_NAME = re.compile(
    r"\b(?i:patient[\s_-]?name|plaintiff|defendant|patient)\b"
    r"[\s\'\"`:=]{1,10}"
    r"[\'\"`]?" + NAME_SHAPE
)

# ----- Content allowlist — known-safe proper-noun phrases
# Ralph's own name is case-sensitive (proper noun, not a substring match).
# Bracketed placeholders like [Patient Name, DOB] are template literals.
SELF_NAME_ALLOW = re.compile(r"\bRalph Martello\b")
# Strip ONLY literal placeholder vocabulary, never an arbitrary [Cap Cap] pair — the old
# `[A-Z][a-z]+ [A-Z][a-z]+` form stripped a real bracketed `[<First> <Last>, DOB ...]` and
# immunized it.
BRACKET_PLACEHOLDER_ALLOW = re.compile(
    r"\[(?:"
    r"patient[\s_-]?name|full[\s_-]?name|first[\s_-]?(?:and[\s_-]?)?last|"
    r"first[\s_-]?name|last[\s_-]?name|name|patient|first|last|"
    r"dob|mrn|date[\s_-]?of[\s_-]?birth|insurance[\s_-]?id|insert[\s\w]*|your[\s\w]*"
    r")(?:,[^\]]*)?\]",
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
    r"[^/]*private_key[^/]*"
    r")$"
)

# ----- Pattern 4: PHI-risk binary extensions
# Any file of these types anywhere NOT under a binary allowlist path is blocked.
BINARY_RISK = re.compile(
    r"\.(pdf|docx?|xlsx?|pptx?|png|jpe?g|tiff?|dcm|dicom|heic|webp)$",
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
    r"(^|/)[^/]*(patient|mrn|dob|chart|x[-_]?ray|imaging)[^/]*"
    r"\.(pdf|docx?|xlsx?|pptx?|png|jpe?g|tiff?|dcm|dicom|heic|webp)$",
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

# ----- Path allowlist for synthetic-fixture directories AND metadata files
FIXTURE_PATH = re.compile(
    r"(^|/)("
    r"TestCase_|tests?/|test_data/|test-fixtures/|"
    r"fixtures/|scripts/test[-_]|scripts/demo[-_]|scripts/smoke[-_]|"
    r"demo_cases\.ts|test-complex-case\.ts|"
    r"\.github/|"
    r"CaseTemplate/|"
    r"plugin\.json|marketplace\.json|package\.json|package-lock\.json|"
    r"LICENSE"
    r")"
)


def staged_files():
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [f for f in r.stdout.splitlines() if f]


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
        for m in PATH_SLUG.finditer(line):
            t1, t2 = m.group(1), m.group(2)
            if (t1.lower(), t2.lower()) in SLUG_NAME_ALLOWLIST:
                continue  # vetted non-patient name (e.g. Ralph's dog)
            if DISEASE_ALLOWLIST.fullmatch(t1) and DISEASE_ALLOWLIST.fullmatch(t2):
                continue  # clinical-topic slug, not a patient name
            hits.append((line.rstrip(), m.group(0)))
            break
    return hits


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
            or LABEL_THEN_NAME.search(stripped)
            or RECORD_ROW.search(stripped)
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
        if BINARY_ALLOW_PATH.search(f):
            continue
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
            return re.sub(re.escape(cand) + _TOKEN_RUN, "[REDACTED]", line, count=1)
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
    name_hits = [f for f in fails if f[0] == "name_phi"]
    cred_hits = [f for f in fails if f[0] == "credential"]
    bin_hits = [f for f in fails if f[0] == "binary"]
    secret_hits = [f for f in fails if f[0] == "secret"]
    data_hits = [f for f in fails if f[0] == "data"]

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
            "⚠️  pre-commit: proper-noun name adjacent to PHI field (DOB/MRN/insurance/patient):"
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
        print("   or non-PHI reference data, move it under tests/ | fixtures/ | docs/,")
        print("   otherwise confirm no patient info and add the path to BINARY_ALLOW_PATH. Hooks are never bypassed.")
        print()

    print("Commit blocked. See feedback_no_phi_in_repos.md for policy.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
