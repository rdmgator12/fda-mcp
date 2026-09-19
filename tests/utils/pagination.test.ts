/**
 * Cursor pagination tests.
 *
 * The tool, resource and prompt registries all paginate their list responses
 * through this service, so its round-trip behaviour is part of what the
 * contract test above depends on.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

import { PaginationService } from '../../src/utils/pagination.js';

function withService<T>(
  fn: (service: PaginationService) => T,
  config?: ConstructorParameters<typeof PaginationService>[0]
): T {
  const service = new PaginationService(config);
  try {
    return fn(service);
  } finally {
    service.dispose();
  }
}

const ITEMS = Array.from({ length: 25 }, (_, i) => `item-${i}`);

describe('PaginationService.paginateArray', () => {
  it('returns the first page and a cursor when more remain', () => {
    withService((service) => {
      const page = service.paginateArray(ITEMS, {}, 10);

      assert.deepEqual(page.results, ITEMS.slice(0, 10));
      assert.equal(typeof page.nextCursor, 'string');
    });
  });

  it('walks every item exactly once across pages', () => {
    withService((service) => {
      const seen: string[] = [];
      let cursor: string | undefined;

      do {
        const page = service.paginateArray(ITEMS, { cursor }, 10);
        seen.push(...page.results);
        cursor = page.nextCursor;
      } while (cursor);

      assert.deepEqual(seen, ITEMS);
    });
  });

  it('omits the cursor on the last page', () => {
    withService((service) => {
      const page = service.paginateArray(ITEMS, {}, 100);

      assert.deepEqual(page.results, ITEMS);
      assert.equal(page.nextCursor, undefined);
    });
  });

  it('returns no cursor for an empty collection', () => {
    withService((service) => {
      const page = service.paginateArray([], {}, 10);

      assert.deepEqual(page.results, []);
      assert.equal(page.nextCursor, undefined);
    });
  });

  it('caps the page size at the configured maximum', () => {
    withService(
      (service) => {
        const page = service.paginateArray(ITEMS, {}, 1000);
        assert.equal(page.results.length, 5);
      },
      { maxPageSize: 5 }
    );
  });

  it('falls back to the default page size when none is given', () => {
    withService(
      (service) => {
        const page = service.paginateArray(ITEMS, {});
        assert.equal(page.results.length, 3);
      },
      { defaultPageSize: 3 }
    );
  });
});

describe('PaginationService.parseCursor', () => {
  it('starts at position zero with no cursor', () => {
    withService((service) => {
      assert.deepEqual(service.parseCursor(), { position: 0, metadata: {} });
    });
  });

  it('rejects a cursor it never issued', () => {
    withService((service) => {
      assert.throws(() => service.parseCursor('not-a-real-cursor'), /cursor not found or expired/i);
    });
  });

  it('rejects a cursor once it has expired', () => {
    withService(
      (service) => {
        const cursor = service.createCursor(10, 25);
        assert.ok(cursor);
        assert.throws(() => service.parseCursor(cursor), /expired/i);
      },
      // Already expired the moment it is issued.
      { cursorExpirationMs: -1 }
    );
  });

  it('rejects a cursor after the store is cleared', () => {
    withService((service) => {
      const page = service.paginateArray(ITEMS, {}, 10);
      assert.ok(page.nextCursor);

      service.clearCursors();
      assert.throws(() => service.parseCursor(page.nextCursor), /cursor not found or expired/i);
    });
  });
});

describe('PaginationService.createCursor', () => {
  it('does not issue a cursor at or past the end of the set', () => {
    withService((service) => {
      assert.equal(service.createCursor(25, 25), undefined);
      assert.equal(service.createCursor(30, 25), undefined);
    });
  });

  it('issues a distinct cursor each time', () => {
    withService((service) => {
      const first = service.createCursor(10, 25);
      const second = service.createCursor(10, 25);

      assert.ok(first && second);
      assert.notEqual(first, second);
    });
  });

  it('counts its live cursors', () => {
    withService((service) => {
      assert.equal(service.getStats().activeCursors, 0);

      service.createCursor(10, 25);
      service.createCursor(20, 25);
      assert.equal(service.getStats().activeCursors, 2);

      service.clearCursors();
      assert.equal(service.getStats().activeCursors, 0);
    });
  });
});

describe('PaginationService.paginateAsync', () => {
  it('passes the cursor position through to the data source', async () => {
    const service = new PaginationService();
    try {
      const calls: { offset: number; limit: number }[] = [];
      const source = async (offset: number, limit: number) => {
        calls.push({ offset, limit });
        return { items: ITEMS.slice(offset, offset + limit), totalCount: ITEMS.length };
      };

      const first = await service.paginateAsync(source, {}, 10);
      assert.deepEqual(first.results, ITEMS.slice(0, 10));
      assert.ok(first.nextCursor);

      const second = await service.paginateAsync(source, { cursor: first.nextCursor }, 10);
      assert.deepEqual(second.results, ITEMS.slice(10, 20));

      assert.deepEqual(calls, [
        { offset: 0, limit: 10 },
        { offset: 10, limit: 10 }
      ]);
    } finally {
      service.dispose();
    }
  });
});

describe('PaginationService.dispose', () => {
  it('clears cursors and stops the cleanup timer', () => {
    const service = new PaginationService();
    service.createCursor(10, 25);
    assert.equal(service.getStats().activeCursors, 1);

    service.dispose();
    assert.equal(service.getStats().activeCursors, 0);

    // Disposing twice must not throw.
    service.dispose();
  });
});
