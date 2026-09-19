/**
 * Builds a synthetic Orange Book ZIP in a temp directory.
 *
 * The real archive is a ~15 MB download from the FDA, so the suite ships a
 * small hand-written stand-in with the same layout: three tilde-delimited text
 * files, each with a header row. All data here is invented - it is shaped like
 * Orange Book data but describes no real application.
 */

import AdmZip from 'adm-zip';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

export const PRODUCTS_HEADER =
  'Ingredient~DF;Route~Trade_Name~Applicant~Strength~Appl_Type~Appl_No~Product_No~TE_Code~Approval_Date~RLD~RS~Type~Applicant_Full_Name';

export const PATENT_HEADER =
  'Appl_Type~Appl_No~Product_No~Patent_No~Patent_Expire_Date_Text~Drug_Substance_Flag~Drug_Product_Flag~Patent_Use_Code~Delist_Flag~Submission_Date';

export const EXCLUSIVITY_HEADER =
  'Appl_Type~Appl_No~Product_No~Exclusivity_Code~Exclusivity_Date';

/** Two well-formed product rows. The second exercises a multi-segment route. */
export const PRODUCTS_ROWS = [
  'TESTOLOL~TABLET;ORAL~FICTIMOL~ACME LABS~10MG~N~099001~001~AB~Jan 2, 2020~Yes~Yes~RX~ACME LABORATORIES INC',
  'TESTOLOL~INJECTABLE;INJECTION;IV~FICTIMOL IV~ACME LABS~5MG/ML~A~099002~002~~Mar 15, 2021~No~No~DISCN~ACME LABORATORIES INC'
];

export const PATENT_ROWS = [
  'N~099001~001~9999999~Jan 2, 2031~Y~~U-1234~~Feb 1, 2020'
];

export const EXCLUSIVITY_ROWS = [
  'N~099001~001~NCE~Jan 2, 2025'
];

export interface FixtureOverrides {
  /** Omit a file entirely, to exercise the missing-file error path. */
  omit?: ('products' | 'patent' | 'exclusivity')[];
  /** Extra product rows appended after PRODUCTS_ROWS. */
  extraProductRows?: string[];
}

export interface OrangeBookFixture {
  zipPath: string;
  cleanup: () => void;
}

function joinFile(header: string, rows: string[]): string {
  return [header, ...rows].join('\n') + '\n';
}

/**
 * Write a synthetic Orange Book ZIP and return its path plus a cleanup hook.
 * Entries are nested under a directory to match the real archive, which is why
 * the parser matches on `entryName.includes(...)` rather than an exact name.
 */
export function createOrangeBookZip(overrides: FixtureOverrides = {}): OrangeBookFixture {
  const omit = new Set(overrides.omit ?? []);
  const dir = mkdtempSync(path.join(tmpdir(), 'fda-mcp-orange-book-'));
  const zipPath = path.join(dir, 'orange-book.zip');

  const zip = new AdmZip();

  if (!omit.has('products')) {
    zip.addFile(
      'EOBZIP_2026_01/products.txt',
      Buffer.from(joinFile(PRODUCTS_HEADER, [...PRODUCTS_ROWS, ...(overrides.extraProductRows ?? [])]), 'utf8')
    );
  }
  if (!omit.has('patent')) {
    zip.addFile('EOBZIP_2026_01/patent.txt', Buffer.from(joinFile(PATENT_HEADER, PATENT_ROWS), 'utf8'));
  }
  if (!omit.has('exclusivity')) {
    zip.addFile(
      'EOBZIP_2026_01/exclusivity.txt',
      Buffer.from(joinFile(EXCLUSIVITY_HEADER, EXCLUSIVITY_ROWS), 'utf8')
    );
  }

  // A file the parser must ignore.
  zip.addFile('EOBZIP_2026_01/readme.txt', Buffer.from('not a data file\n', 'utf8'));

  zip.writeZip(zipPath);

  return {
    zipPath,
    cleanup: () => rmSync(dir, { recursive: true, force: true })
  };
}
