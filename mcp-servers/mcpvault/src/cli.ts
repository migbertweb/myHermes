export interface ParsedCliArgs {
  vaultPathArg: string;
  readOnly: boolean;
}

/**
 * Parse runtime options without importing server.ts, which starts the MCP
 * server as a side effect. Unknown positional arguments remain part of the
 * vault path so unquoted paths with spaces continue to work.
 */
export function parseCliArgs(args: string[]): ParsedCliArgs {
  const pathArgs: string[] = [];
  let readOnly = false;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index]!;

    if (arg === "--read-only") {
      const next = args[index + 1]?.toLowerCase();
      if (next === "true" || next === "false") {
        readOnly = next === "true";
        index += 1;
      } else {
        readOnly = true;
      }
      continue;
    }

    if (arg.startsWith("--read-only=")) {
      const value = arg.slice("--read-only=".length).toLowerCase();
      if (value !== "true" && value !== "false") {
        throw new Error("--read-only must be true or false");
      }
      readOnly = value === "true";
      continue;
    }

    pathArgs.push(arg);
  }

  return {
    vaultPathArg: pathArgs.join(" ").trim(),
    readOnly,
  };
}
