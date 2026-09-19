/**
 * MCP contract test.
 *
 * Pins the surface the server advertises over stdio: server identity, the one
 * tool and its input schema, the five resources and the six prompts. A
 * dependency bump or a refactor that moves any of this fails here instead of
 * needing a hand-written diff against a previous run.
 *
 * Update the expectations below deliberately when the surface is meant to
 * change, and say so in the pull request.
 */

import { after, before, describe, it } from 'node:test';
import assert from 'node:assert/strict';

import {
  McpStdioClient,
  PROTOCOL_VERSION,
  type InitializeResult,
  type PromptDefinition,
  type ResourceDefinition,
  type ToolDefinition
} from '../helpers/mcp-stdio-client.js';

/** The tool names the server exposes. */
const EXPECTED_TOOLS = ['fda_info'];

/** `fda_info.method` accepts exactly these values. */
const EXPECTED_FDA_INFO_METHODS = [
  'lookup_drug',
  'lookup_device',
  'search_orange_book',
  'get_therapeutic_equivalents',
  'get_patent_exclusivity',
  'analyze_patent_cliff',
  'search_purple_book',
  'get_biosimilar_interchangeability'
];

/** The resource URIs the server exposes, in registration order. */
const EXPECTED_RESOURCE_URIS = [
  'fda://safety/alerts/current',
  'fda://safety/top-drugs-aes',
  'fda://recalls/active',
  'fda://shortages/current',
  'fda://intelligence/high-risk-therapeutic-areas'
];

/**
 * The prompt names the server exposes. The prompt registry constructs seven
 * prompts; `fda_weekly_surveillance_report` is built but not enabled in
 * settings, so it must not appear here.
 */
const EXPECTED_PROMPTS = [
  'fda_drug_safety_profile',
  'fda_company_portfolio_analysis',
  'fda_generic_competition_landscape',
  'fda_supply_chain_risk_assessment',
  'fda_regulatory_due_diligence',
  'fda_market_access_analysis'
];

/** Prompt name -> its required argument names. */
const EXPECTED_REQUIRED_PROMPT_ARGS: Record<string, string[]> = {
  fda_drug_safety_profile: ['drug_name'],
  fda_company_portfolio_analysis: ['company_name'],
  fda_generic_competition_landscape: [],
  fda_supply_chain_risk_assessment: [],
  fda_regulatory_due_diligence: [],
  fda_market_access_analysis: []
};

describe('MCP stdio contract', () => {
  let client: McpStdioClient;
  let initializeResult: InitializeResult;
  let tools: ToolDefinition[];
  let resources: ResourceDefinition[];
  let prompts: PromptDefinition[];

  before(async () => {
    const started = await McpStdioClient.start();
    client = started.client;
    initializeResult = started.initializeResult;

    const [toolsRes, resourcesRes, promptsRes] = await Promise.all([
      client.request('tools/list'),
      client.request('resources/list'),
      client.request('prompts/list')
    ]);

    assert.equal(toolsRes.error, undefined, `tools/list errored: ${toolsRes.error?.message}`);
    assert.equal(resourcesRes.error, undefined, `resources/list errored: ${resourcesRes.error?.message}`);
    assert.equal(promptsRes.error, undefined, `prompts/list errored: ${promptsRes.error?.message}`);

    tools = (toolsRes.result as { tools: ToolDefinition[] }).tools;
    resources = (resourcesRes.result as { resources: ResourceDefinition[] }).resources;
    prompts = (promptsRes.result as { prompts: PromptDefinition[] }).prompts;
  });

  after(async () => {
    await client?.stop();
  });

  describe('initialize', () => {
    it('reports the server identity', () => {
      assert.equal(initializeResult.serverInfo.name, 'fda-mcp-server');
      assert.equal(initializeResult.serverInfo.version, '1.0.0');
    });

    it('negotiates the expected protocol version', () => {
      assert.equal(initializeResult.protocolVersion, PROTOCOL_VERSION);
    });

    it('advertises the tools, prompts and resources capabilities', () => {
      const capabilities = initializeResult.capabilities;
      assert.ok(capabilities.tools, 'missing tools capability');
      assert.ok(capabilities.prompts, 'missing prompts capability');
      assert.ok(capabilities.resources, 'missing resources capability');
      assert.ok(capabilities.logging, 'missing logging capability');
    });
  });

  describe('tools/list', () => {
    it('exposes exactly the expected tools', () => {
      assert.deepEqual(tools.map((t) => t.name).sort(), [...EXPECTED_TOOLS].sort());
    });

    it('gives every tool a non-empty description', () => {
      for (const tool of tools) {
        assert.ok(
          typeof tool.description === 'string' && tool.description.length > 0,
          `tool ${tool.name} has no description`
        );
      }
    });

    it('pins the fda_info input schema', () => {
      const fdaInfo = tools.find((t) => t.name === 'fda_info');
      assert.ok(fdaInfo, 'fda_info tool is missing');

      assert.equal(fdaInfo.inputSchema.type, 'object');
      assert.deepEqual(
        [...(fdaInfo.inputSchema.required ?? [])].sort(),
        ['method', 'search_term']
      );

      const method = fdaInfo.inputSchema.properties.method;
      assert.ok(method, 'fda_info.method is missing from the input schema');
      assert.deepEqual([...(method.enum ?? [])].sort(), [...EXPECTED_FDA_INFO_METHODS].sort());
    });

    it('keeps the documented fda_info parameters in the input schema', () => {
      const fdaInfo = tools.find((t) => t.name === 'fda_info');
      assert.ok(fdaInfo);

      // A representative slice across the API surface: the core query
      // parameters, an adverse-event filter, and an Orange/Purple Book field.
      for (const field of ['search_term', 'search_type', 'limit', 'reaction_meddra_pt', 'nda_number', 'reference_product']) {
        assert.ok(
          field in fdaInfo.inputSchema.properties,
          `fda_info input schema lost the "${field}" property`
        );
      }
    });
  });

  describe('resources/list', () => {
    it('exposes exactly the expected resource URIs', () => {
      assert.deepEqual(resources.map((r) => r.uri).sort(), [...EXPECTED_RESOURCE_URIS].sort());
    });

    it('gives every resource a name and the JSON mime type', () => {
      for (const resource of resources) {
        assert.ok(
          typeof resource.name === 'string' && resource.name.length > 0,
          `resource ${resource.uri} has no name`
        );
        assert.equal(
          resource.mimeType,
          'application/json',
          `resource ${resource.uri} changed mime type`
        );
      }
    });
  });

  describe('prompts/list', () => {
    it('exposes exactly the expected prompts', () => {
      assert.deepEqual(prompts.map((p) => p.name).sort(), [...EXPECTED_PROMPTS].sort());
    });

    it('does not expose the prompt that settings leave disabled', () => {
      assert.ok(
        !prompts.some((p) => p.name === 'fda_weekly_surveillance_report'),
        'fda_weekly_surveillance_report is registered but must not be exposed'
      );
    });

    it('pins each prompt\'s required arguments', () => {
      for (const prompt of prompts) {
        const expected = EXPECTED_REQUIRED_PROMPT_ARGS[prompt.name];
        assert.ok(expected, `unexpected prompt ${prompt.name}`);

        const actual = (prompt.arguments ?? [])
          .filter((arg) => arg.required === true)
          .map((arg) => arg.name)
          .sort();

        assert.deepEqual(actual, [...expected].sort(), `prompt ${prompt.name} changed required arguments`);
      }
    });
  });

  describe('stdio hygiene', () => {
    it('writes nothing but JSON-RPC to stdout', () => {
      assert.deepEqual(
        client.nonJsonStdoutLines,
        [],
        'the server wrote non-JSON to stdout, which corrupts the stdio transport'
      );
    });

    it('sends its diagnostics to stderr', () => {
      assert.ok(
        client.stderr.length > 0,
        'expected the server to log startup diagnostics on stderr'
      );
    });
  });
});
