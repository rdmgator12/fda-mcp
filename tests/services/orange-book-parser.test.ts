/**
 * Orange Book parser tests.
 *
 * `extractOrangeBookZip` is the one place the repo calls adm-zip directly
 * (`new AdmZip(path)`, `.getEntries()`, `entry.entryName`, `entry.getData()`),
 * so these tests double as the seam test for that dependency: an adm-zip bump
 * that changes any of those four fails here.
 */

import { after, before, describe, it } from 'node:test';
import assert from 'node:assert/strict';

import {
  extractOrangeBookZip,
  parseExclusivity,
  parseOrangeBook,
  parsePatents,
  parseProducts
} from '../../src/services/orange-purple-book/orange-book-parser.js';

import {
  createOrangeBookZip,
  EXCLUSIVITY_HEADER,
  PATENT_HEADER,
  PRODUCTS_HEADER,
  PRODUCTS_ROWS,
  type OrangeBookFixture
} from '../helpers/orange-book-fixture.js';

describe('extractOrangeBookZip', () => {
  let fixture: OrangeBookFixture;

  before(() => {
    fixture = createOrangeBookZip();
  });

  after(() => {
    fixture.cleanup();
  });

  it('pulls the three data files out of the archive', () => {
    const { productsText, patentsText, exclusivityText } = extractOrangeBookZip(fixture.zipPath);

    assert.ok(productsText.startsWith(PRODUCTS_HEADER), 'products.txt content is wrong');
    assert.ok(patentsText.startsWith(PATENT_HEADER), 'patent.txt content is wrong');
    assert.ok(exclusivityText.startsWith(EXCLUSIVITY_HEADER), 'exclusivity.txt content is wrong');
  });

  it('finds entries nested in a directory inside the archive', () => {
    // The real FDA archive nests its files; the parser matches on a substring
    // of entryName rather than an exact name, and this locks that in.
    const { productsText } = extractOrangeBookZip(fixture.zipPath);
    assert.ok(productsText.includes('FICTIMOL'), 'nested products.txt was not found');
  });

  it('throws when a required file is missing', () => {
    const partial = createOrangeBookZip({ omit: ['patent'] });
    try {
      assert.throws(
        () => extractOrangeBookZip(partial.zipPath),
        /missing required files/i
      );
    } finally {
      partial.cleanup();
    }
  });
});

describe('parseProducts', () => {
  it('parses a product row into typed fields', () => {
    const products = parseProducts([PRODUCTS_HEADER, PRODUCTS_ROWS[0]].join('\n'));

    assert.equal(products.length, 1);
    assert.deepEqual(products[0], {
      ingredient: 'TESTOLOL',
      dosageForm: 'TABLET',
      route: 'ORAL',
      tradeName: 'FICTIMOL',
      applicant: 'ACME LABS',
      strength: '10MG',
      applType: 'N',
      applNo: '099001',
      productNo: '001',
      teCode: 'AB',
      approvalDate: 'Jan 2, 2020',
      rld: 'Yes',
      rs: 'Yes',
      type: 'RX',
      applicantFullName: 'ACME LABORATORIES INC'
    });
  });

  it('keeps every segment after the first when the route has several', () => {
    // "INJECTABLE;INJECTION;IV" splits into dosage form INJECTABLE and route
    // "INJECTION;IV" - dropping the tail here would silently lose data.
    const products = parseProducts([PRODUCTS_HEADER, PRODUCTS_ROWS[1]].join('\n'));

    assert.equal(products[0].dosageForm, 'INJECTABLE');
    assert.equal(products[0].route, 'INJECTION;IV');
  });

  it('skips the header row', () => {
    const products = parseProducts([PRODUCTS_HEADER, ...PRODUCTS_ROWS].join('\n'));
    assert.equal(products.length, 2);
    assert.ok(!products.some((p) => p.ingredient === 'Ingredient'));
  });

  it('skips malformed rows rather than throwing', () => {
    const text = [PRODUCTS_HEADER, 'TOO~FEW~FIELDS', PRODUCTS_ROWS[0]].join('\n');
    const products = parseProducts(text);

    assert.equal(products.length, 1);
    assert.equal(products[0].tradeName, 'FICTIMOL');
  });

  it('ignores blank lines', () => {
    const text = [PRODUCTS_HEADER, '', PRODUCTS_ROWS[0], '   ', ''].join('\n');
    assert.equal(parseProducts(text).length, 1);
  });

  it('trims surrounding whitespace on every field', () => {
    const padded = PRODUCTS_ROWS[0]
      .split('~')
      .map((field) => `  ${field}  `)
      .join('~');
    const products = parseProducts([PRODUCTS_HEADER, padded].join('\n'));

    assert.equal(products[0].ingredient, 'TESTOLOL');
    assert.equal(products[0].applicantFullName, 'ACME LABORATORIES INC');
  });

  it('returns an empty list for a header-only file', () => {
    assert.deepEqual(parseProducts(PRODUCTS_HEADER), []);
  });
});

describe('parsePatents', () => {
  it('parses a patent row into typed fields', () => {
    const patents = parsePatents(
      [PATENT_HEADER, 'N~099001~001~9999999~Jan 2, 2031~Y~~U-1234~~Feb 1, 2020'].join('\n')
    );

    assert.equal(patents.length, 1);
    assert.deepEqual(patents[0], {
      applType: 'N',
      applNo: '099001',
      productNo: '001',
      patentNo: '9999999',
      patentExpireDate: 'Jan 2, 2031',
      drugSubstanceFlag: 'Y',
      drugProductFlag: '',
      patentUseCode: 'U-1234',
      delistFlag: '',
      submissionDate: 'Feb 1, 2020'
    });
  });

  it('skips rows with too few fields', () => {
    const patents = parsePatents([PATENT_HEADER, 'N~099001~001'].join('\n'));
    assert.deepEqual(patents, []);
  });
});

describe('parseExclusivity', () => {
  it('parses an exclusivity row into typed fields', () => {
    const exclusivity = parseExclusivity([EXCLUSIVITY_HEADER, 'N~099001~001~NCE~Jan 2, 2025'].join('\n'));

    assert.equal(exclusivity.length, 1);
    assert.deepEqual(exclusivity[0], {
      applType: 'N',
      applNo: '099001',
      productNo: '001',
      exclusivityCode: 'NCE',
      exclusivityDate: 'Jan 2, 2025'
    });
  });

  it('skips rows with too few fields', () => {
    assert.deepEqual(parseExclusivity([EXCLUSIVITY_HEADER, 'N~099001'].join('\n')), []);
  });
});

describe('parseOrangeBook', () => {
  let fixture: OrangeBookFixture;

  before(() => {
    fixture = createOrangeBookZip();
  });

  after(() => {
    fixture.cleanup();
  });

  it('parses the whole archive in one call', () => {
    const { products, patents, exclusivity } = parseOrangeBook(fixture.zipPath);

    assert.equal(products.length, 2);
    assert.equal(patents.length, 1);
    assert.equal(exclusivity.length, 1);

    // The patent and exclusivity rows point at the first product.
    assert.equal(patents[0].applNo, products[0].applNo);
    assert.equal(exclusivity[0].applNo, products[0].applNo);
  });
});
