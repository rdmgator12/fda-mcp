/**
 * Parse Purple Book Excel file
 */

import ExcelJS from 'exceljs';
import type { PurpleBookBiologic } from '../../types/orange-purple-book/index.js';
import { logger } from '../../logging/index.js';

/**
 * FDA Purple Book column layout (1-indexed, as of April 2026 monthly download):
 *   1: N/R/U flag        2: Applicant            3: BLA Number       4: Proprietary Name
 *   5: Proper Name       6: License Type         7: Strength         8: Dosage Form
 *   9: Route of Admin   10: Product Presentation 11: Marketing Status 12: Licensure
 *  13: Approval Date    14: Inter. Approval Date 15: Ref Proper Name  16: Ref Proprietary Name
 *  17: Suppl. Number    18: Submission Type      19: Inter. Suppl.    20: License Number
 *  21: Product Number   22: Center               23: Date of First Lic 24: Exclusivity Exp
 *  25: First Interch.   26: Ref Exclusivity Exp  27: Orphan Excl. Exp
 *
 * Rows 1-3 are preamble (title + "N/R/U" legend). Row 4 is the header row.
 * Data starts at row 5.
 */
const COL = {
  applicant: 2,
  blaNumber: 3,
  proprietaryName: 4,
  properName: 5,
  licenseType: 6,
  strength: 7,
  dosageForm: 8,
  routeOfAdmin: 9,
  marketingStatus: 11,
  licensureStatus: 12,
  approvalDate: 13,
  refProductProperName: 15,
  refProductProprietaryName: 16,
  dateOfFirstLicensure: 23,
  exclusivityExp: 24,
  firstInterchangeableExclusivity: 25,
  orphanExclusivityExp: 27,
} as const;

const DATA_START_ROW = 5;

/**
 * Normalize a cell value to a trimmed string.
 * Handles ExcelJS's varied value shapes: primitives, Dates, rich text, formula results, hyperlinks.
 */
function getCellString(row: ExcelJS.Row, col: number): string {
  const value = row.getCell(col).value;
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number' || typeof value === 'boolean') return String(value).trim();
  if (value instanceof Date) return value.toISOString().slice(0, 10);
  if (typeof value === 'object') {
    const v = value as unknown as Record<string, unknown>;
    if (Array.isArray(v.richText)) {
      return (v.richText as Array<{ text: string }>).map((r) => r.text).join('').trim();
    }
    if (v.result !== undefined && v.result !== null) return String(v.result).trim();
    if (v.text !== undefined && v.text !== null) return String(v.text).trim();
  }
  return String(value).trim();
}

export async function parsePurpleBook(excelPath: string): Promise<PurpleBookBiologic[]> {
  logger.info('Parsing Purple Book Excel file...');

  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.readFile(excelPath);
  const worksheet = workbook.worksheets[0];
  if (!worksheet) {
    throw new Error('Purple Book workbook has no worksheets');
  }

  const totalRows = worksheet.rowCount;
  const dataRowCount = Math.max(0, totalRows - (DATA_START_ROW - 1));
  logger.info(`Found ${dataRowCount} rows in Purple Book`);

  const biologics: PurpleBookBiologic[] = [];

  for (let rowNum = DATA_START_ROW; rowNum <= totalRows; rowNum++) {
    const row = worksheet.getRow(rowNum);

    const applicant = getCellString(row, COL.applicant);
    const blaNumber = getCellString(row, COL.blaNumber);
    if (!blaNumber) continue;

    const proprietaryName = getCellString(row, COL.proprietaryName);
    const properName = getCellString(row, COL.properName);
    const licenseType = getCellString(row, COL.licenseType);
    const strength = getCellString(row, COL.strength);
    const dosageForm = getCellString(row, COL.dosageForm);
    const routeOfAdmin = getCellString(row, COL.routeOfAdmin);
    const marketingStatus = getCellString(row, COL.marketingStatus);
    const licensureStatus = getCellString(row, COL.licensureStatus);
    const approvalDate = getCellString(row, COL.approvalDate);
    const refProductProperName = getCellString(row, COL.refProductProperName);
    const refProductProprietaryName = getCellString(row, COL.refProductProprietaryName);
    const dateOfFirstLicensure = getCellString(row, COL.dateOfFirstLicensure);
    const exclusivityExpDate = getCellString(row, COL.exclusivityExp);
    const firstInterchangeableExclusivity = getCellString(row, COL.firstInterchangeableExclusivity);
    const orphanExclusivity = getCellString(row, COL.orphanExclusivityExp);

    const cleanedRefProductProperName =
      refProductProperName && refProductProperName !== 'N/A' ? refProductProperName.trim() : '';
    const hasReferenceProduct = cleanedRefProductProperName !== '';
    const isBiosimilar = licenseType.startsWith('351(k)') || hasReferenceProduct;
    const isInterchangeable =
      licenseType.toLowerCase().includes('interchangeable') || !!firstInterchangeableExclusivity;

    biologics.push({
      blaNumber,
      properName,
      proprietaryName,
      dateOfLicensure: dateOfFirstLicensure || approvalDate,
      licensureStatus,
      marketingStatus,
      applicant,
      applicantFullName: applicant,
      strength,
      dosageForm,
      routeOfAdministration: routeOfAdmin,
      referenceProduct: '',
      referenceProductProperName: cleanedRefProductProperName,
      referenceProductProprietaryName: refProductProprietaryName,
      biosimilar: isBiosimilar ? 'Yes' : 'No',
      interchangeable: isInterchangeable ? 'Yes' : 'No',
      interchangeableDate: firstInterchangeableExclusivity,
      exclusivityExpirationDate: exclusivityExpDate,
      orphanExclusivity,
      pediatricExclusivity: '',
    });
  }

  logger.info(`Parsed ${biologics.length} biologics from Purple Book`);

  return biologics;
}
