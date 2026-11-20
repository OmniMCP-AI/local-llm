const inlinePattern = /(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|\x60[^\x60]+\x60)/g;

export function markdownInline(line) {
  return line.split(inlinePattern).filter(Boolean).map((chunk) => {
    const link = chunk.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (link) return { type: "link", text: link[1], href: link[2] };
    if (chunk.startsWith("**") && chunk.endsWith("**")) return { type: "strong", text: chunk.slice(2, -2) };
    if (chunk.startsWith("\x60") && chunk.endsWith("\x60")) return { type: "code", text: chunk.slice(1, -1) };
    return { type: "text", text: chunk };
  });
}

export function markdownBlocks(body) {
  return body.trim().split(/\r?\n\s*\r?\n/g).filter(Boolean).map((block) => {
    if (block.startsWith("## ")) return { type: "heading", text: block.slice(3).trim() };
    const lines = block.split(/\r?\n/);
    if (lines.every((line) => line.startsWith("- "))) return { type: "list", items: lines.map((line) => line.slice(2)) };
    return { type: "paragraph", text: lines.join(" ") };
  });
}
