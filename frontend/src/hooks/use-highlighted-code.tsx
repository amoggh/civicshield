import * as React from 'react';

/**
 * Lightweight, zero-dependency JSON syntax highlighter for CodeBlock lines.
 * Colors keys in light cyan/blue, strings in emerald green, numbers in amber,
 * booleans/nulls in purple, and punctuation in zinc.
 */
export function useHighlightedCode(code: string, _lang: string = 'json'): React.ReactNode[] {
  return React.useMemo(() => {
    if (!code) return [];

    const lines = code.split('\n');
    return lines.map((line, lineIndex) => {
      // Tokenize JSON line
      const parts: React.ReactNode[] = [];
      let keyCounter = 0;

      // Regex matching: keys "key":, strings "value", numbers, booleans/null, punctuation
      const tokenRegex = /("(?:\\.|[^"\\])*")(?:\s*:)?|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|(\btrue\b|\bfalse\b|\bnull\b)|([{}[\],:])/g;
      let lastIndex = 0;
      let match: RegExpExecArray | null;

      while ((match = tokenRegex.exec(line)) !== null) {
        // Text before match (whitespace / indents)
        if (match.index > lastIndex) {
          parts.push(
            <span key={`${lineIndex}-text-${keyCounter++}`}>
              {line.substring(lastIndex, match.index)}
            </span>
          );
        }

        const fullMatch = match[0];
        const stringToken = match[1];
        const numberToken = match[2];
        const keywordToken = match[3];
        const punctuationToken = match[4];

        if (stringToken) {
          if (fullMatch.endsWith(':')) {
            // It's an object key
            parts.push(
              <span key={`${lineIndex}-key-${keyCounter++}`} className="text-sky-300 font-medium">
                {stringToken}
              </span>
            );
            parts.push(
              <span key={`${lineIndex}-colon-${keyCounter++}`} className="text-zinc-500">
                :
              </span>
            );
          } else {
            // It's a string value
            parts.push(
              <span key={`${lineIndex}-str-${keyCounter++}`} className="text-emerald-300">
                {stringToken}
              </span>
            );
          }
        } else if (numberToken) {
          parts.push(
            <span key={`${lineIndex}-num-${keyCounter++}`} className="text-amber-300">
              {numberToken}
            </span>
          );
        } else if (keywordToken) {
          parts.push(
            <span key={`${lineIndex}-kw-${keyCounter++}`} className="text-purple-300 font-semibold">
              {keywordToken}
            </span>
          );
        } else if (punctuationToken) {
          parts.push(
            <span key={`${lineIndex}-punc-${keyCounter++}`} className="text-zinc-400">
              {punctuationToken}
            </span>
          );
        }

        lastIndex = tokenRegex.lastIndex;
      }

      if (lastIndex < line.length) {
        parts.push(
          <span key={`${lineIndex}-tail-${keyCounter++}`}>
            {line.substring(lastIndex)}
          </span>
        );
      }

      return parts.length > 0 ? parts : <span>{line || ' '}</span>;
    });
  }, [code]);
}
