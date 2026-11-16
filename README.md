# Knowledge audit skill for Claude

Puts Claude on Claude. It reads everything Claude keeps about you (memory, people files, each project's memory, your own skills, and optionally each project's Google Drive folder), checks every piece against a simple schema, and flags what is in the wrong place:

- **Red:** information in the wrong place. It has to move or go (a step-by-step procedure sitting in memory, a balance copied into a skill, a filled-in template).
- **Yellow:** a duplicate, or something with no clear purpose. Worth a look, your call.

You get a clickable Knowledge map page and a numbered list of up to 20 fixes you can approve with "yes 1-6, no 7". Nothing changes until you say so.

## Install (claude.ai web or desktop app)

1. Turn on code execution: Settings > Capabilities.
2. Go to Customize > Skills, click "+", then "Create skill" > "Upload a skill", and upload [`knowledge-audit.zip`](https://github.com/bangiamanu/knowledge-audit/raw/main/knowledge-audit.zip) (download it from this page first).
3. Open a regular chat (not inside a project) and type: `run the knowledge audit`.

Optional: connect Google Drive to also check each project's Drive folder.

## Make it yours

The default schema is in SKILL.md under "The rules". If you already keep your own rules for where knowledge lives in your Claude preferences, the skill uses those instead. Projects you have archived can go under "Skip list" at the bottom of SKILL.md (the skill offers to add them for you).

## Files

- `knowledge-audit.zip`: the ready-to-upload skill
- `knowledge-audit/SKILL.md`: the instructions Claude follows
- `knowledge-audit/scripts/build_page.py`: builds the Knowledge map page
- `knowledge-audit/assets/tpl.html`: the page template (no personal data; the script fills it in)
