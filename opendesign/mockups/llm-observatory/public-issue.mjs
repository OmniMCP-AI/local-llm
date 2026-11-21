const newIssue = "https://github.com/OmniMCP-AI/local-llm/issues/new";

export function publicIssueHref(category) {
  if (category === "missing") return newIssue + "?template=benchmark-request.yml";
  if (category === "correction") return newIssue + "?template=result-correction.yml";
  return newIssue + "/choose";
}
