# Analysis Workflow — Required Permissions

## Tools Used During Signal Analysis

### Always Needed (core analysis)
- **Read** — reading pine log CSVs, candle data CSVs, existing analysis files
- **Write** — creating analysis output files (debug/*.md), inventory files
- **Edit** — updating existing analysis files, memory files
- **Glob** — finding files by pattern (debug/*.csv, debug/*.md)
- **Grep** — searching file contents for dates, symbols, signal types
- **Task** — spawning parallel analysis agents

### Occasionally Needed
- **Bash** — git operations (status, diff, commit), file listing
- **WebSearch/WebFetch** — researching Pine Script documentation

---

## Claude Code Settings Configuration

### Global Settings (already configured)

File: `~/.claude/settings.json`

The global settings already permit all core tools (`Read`, `Edit`, `Write`, `Glob`, `Grep`) plus `Bash(git:*)`, `Bash(ls:*)`, `WebSearch`, `WebFetch`, and `Skill(*)`. No changes needed at the global level.

### Project-Level Settings (to be created)

File:
```
~/.claude/projects/-Users-mab-Library-CloudStorage-GoogleDrive-mab-bina-de-Meine-Ablage-Claude-misc-TradingView/settings.json
```

Since this file does not yet exist, the following JSON can be placed there to provide project-specific permissions. These complement (do not override) the global settings.

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Write",
      "Edit",
      "Glob",
      "Grep",
      "Task",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(ls:*)"
    ]
  }
}
```

### What Each Entry Covers

| Entry | Purpose |
|---|---|
| `Read` | Read any file in the project (pine logs, candle CSVs, analysis output) |
| `Write` | Create new files (debug/*.md, inventory files) |
| `Edit` | Update existing analysis files, memory files |
| `Glob` | Find files by pattern (debug/*.csv, debug/*.md) |
| `Grep` | Search file contents for dates, symbols, signal types |
| `Task` | Spawn parallel analysis agents for multi-symbol workflows |
| `Bash(git status:*)` | Check working tree status |
| `Bash(git diff:*)` | View staged/unstaged changes |
| `Bash(git log:*)` | View recent commit history |
| `Bash(git add:*)` | Stage files for commit |
| `Bash(git commit:*)` | Create commits |
| `Bash(ls:*)` | List directory contents |

### Note on Global vs. Project Settings

The global `~/.claude/settings.json` already allows all of these tools and more. Creating the project-level file is optional but recommended for documentation purposes — it makes the project's requirements explicit and self-contained. If the global settings change in the future, the project-level file ensures the analysis workflow continues to work.

### Paths Accessed During Analysis

- **Project root:** `/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/`
- **Debug folder:** `<project root>/debug/` (CSVs, analysis MDs)
- **Memory file:** `~/.claude/projects/-Users-mab-Library-CloudStorage-GoogleDrive-mab-bina-de-Meine-Ablage-Claude-misc-TradingView/memory/MEMORY.md`
