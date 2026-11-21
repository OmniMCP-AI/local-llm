export const catalogApiPath = "/api/v1/catalog";
export const catalogKinds = ["cards", "machines", "models", "runtimes"];
export const catalogPageSize = 25;
export const catalogQueryLength = 200;
export const catalogMaxOffset = 999_999;

const nullableText = { type: ["string", "null"] };
const count = { type: "integer", minimum: 0 };

export function catalogOpenApi(revision) {
  const parameter = (name, description, schema, required = false) =>
    ({ in: "query", name, description, required, schema });
  const response = (description, schema) =>
    ({ description, content: { "application/json": { schema } } });
  const failure = { type: "object", required: ["error"], properties: { error: { type: "string" } } };
  const entry = {
    type: "object", required: ["id", "name", "detail", "source", "html", "markdown"],
    properties: {
      id: { type: "string" }, name: { type: "string" }, detail: nullableText, source: nullableText,
      html: { type: "string", format: "uri-reference" }, markdown: { type: "string", format: "uri-reference" },
    },
  };
  return {
    openapi: "3.1.0",
    info: {
      title: "fastest.ai catalog API", version: "1",
      description: "Public hardware, machine, model repository and runtime metadata from an exact PostgreSQL publication. Benchmark evidence has its own release and API.",
    },
    servers: [{ url: "/" }],
    paths: { [catalogApiPath]: { get: {
      operationId: "searchReleasedCatalog",
      summary: "Browse or search one catalog collection",
      parameters: [
        parameter("kind", "Catalog collection.", { type: "string", enum: catalogKinds }, true),
        parameter("revision", "Catalog release. Omit for the current release. Subsequent pages require the first response’s revision.",
          { type: "string", pattern: "^v1-[a-f0-9]{16}$", examples: [revision] }),
        parameter("q", "Case-insensitive search of catalog names, IDs, descriptions and aliases. Model search accepts an exact owner/repository ID. Omit to browse.",
          { type: "string", maxLength: catalogQueryLength }),
        parameter("limit", "Maximum results on this page.",
          { type: "integer", minimum: 1, maximum: catalogPageSize, default: catalogPageSize }),
        parameter("offset", "Zero-based offset with a pinned revision for any nonzero value. Model browsing uses owner-prefix shard order and published row order.",
          { ...count, maximum: catalogMaxOffset, default: 0 }),
      ],
      responses: {
        200: response("Published catalog records with their source and profile links.", {
          type: "object", required: ["apiVersion", "revision", "snapshotId", "kind", "manifest", "scope", "results", "pagination"],
          properties: {
            apiVersion: { const: "1" }, revision: { type: "string" }, snapshotId: { type: "string" },
            kind: { type: "string", enum: catalogKinds }, manifest: { type: "string", format: "uri-reference" },
            scope: { type: "string" }, results: { type: "array", items: entry },
            pagination: {
              type: "object", required: ["limit", "offset", "total", "nextOffset"],
              properties: { limit: count, offset: count, total: count, nextOffset: { type: ["integer", "null"], minimum: 0 } },
            },
          },
        }),
        400: response("Invalid or repeated selectors.", failure),
        404: response("The requested catalog release is unavailable.", failure),
        410: response("The requested catalog release was withdrawn.", failure),
        503: response("Catalog data or the withdrawal policy is unavailable.", failure),
      },
    } } },
  };
}
