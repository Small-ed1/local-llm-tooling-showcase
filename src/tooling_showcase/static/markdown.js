(function (global) {
  "use strict";

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function renderInlineMarkdown(text) {
    return escapeHtml(text)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  }

  function renderMarkdownBlocks(text) {
    const lines = String(text || "").split("\n");
    const html = [];
    let paragraph = [];
    let listType = null;
    let listItems = [];

    const flushParagraph = () => {
      if (!paragraph.length) return;
      html.push(`<p>${renderInlineMarkdown(paragraph.join(" "))}</p>`);
      paragraph = [];
    };
    const flushList = () => {
      if (!listType) return;
      html.push(`<${listType}>${listItems.map((item) => `<li>${renderInlineMarkdown(item)}</li>`).join("")}</${listType}>`);
      listType = null;
      listItems = [];
    };

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        flushParagraph();
        flushList();
        return;
      }
      const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
      if (heading) {
        flushParagraph();
        flushList();
        const level = heading[1].length + 2;
        html.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
        return;
      }
      const unordered = trimmed.match(/^[-*]\s+(.+)$/);
      if (unordered) {
        flushParagraph();
        if (listType && listType !== "ul") flushList();
        listType = "ul";
        listItems.push(unordered[1]);
        return;
      }
      const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
      if (ordered) {
        flushParagraph();
        if (listType && listType !== "ol") flushList();
        listType = "ol";
        listItems.push(ordered[1]);
        return;
      }
      flushList();
      paragraph.push(trimmed);
    });
    flushParagraph();
    flushList();
    return html.join("");
  }

  function renderSafeMarkdown(text) {
    const source = String(text || "");
    const parts = [];
    const fence = /```([\w.+-]*)\n?([\s\S]*?)```/g;
    let cursor = 0;
    let match;
    while ((match = fence.exec(source))) {
      if (match.index > cursor) parts.push(renderMarkdownBlocks(source.slice(cursor, match.index)));
      const language = match[1] ? ` data-language="${escapeHtml(match[1])}"` : "";
      parts.push(`<pre class="markdown-code"${language}><code>${escapeHtml(match[2].replace(/^\n|\n$/g, ""))}</code></pre>`);
      cursor = fence.lastIndex;
    }
    if (cursor < source.length) parts.push(renderMarkdownBlocks(source.slice(cursor)));
    return parts.join("") || "";
  }

  global.ShowcaseMarkdown = Object.freeze({
    escapeHtml,
    renderInlineMarkdown,
    renderMarkdownBlocks,
    renderSafeMarkdown
  });
})(globalThis);
