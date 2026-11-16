---
name: knowledge-audit
description: Audit everything Claude keeps about you (global memory, people files, each project's memory, your own skills, optionally each project's Drive folder) against a simple knowledge schema; builds a Knowledge map page with red and yellow flags and returns up to 20 yes/no fixes. Use when the user says run the knowledge audit, audit my memory, or /knowledge-audit.
---

# Knowledge audit

Claude's memory grows by itself. Over months it fills with procedures that belong in skills, project status that belongs in project docs, numbers copied from spreadsheets, and the same fact in three places. This skill puts Claude on Claude: it reads everything, checks each piece against a schema, and shows what is in the wrong place.

**Where to run it.** In a regular chat, OUTSIDE any project. Inside a project only that project's memory is visible: if you are inside one, say so in one line and ask the user to start it from a regular chat.

**What it needs.** Memory turned on, and code execution (Settings > Capabilities). Optional: a Google Drive connector (for the Drive check) and the ability to publish an artifact (for the page). Without them, skip those parts and say so in one line.

## The rules

If the user's preferences or memory already contain their own rules for where knowledge lives (for example a section titled "Where knowledge lives" or "schema"), audit against those, as they read today. Otherwise use this default schema:

1. **Skills** hold everything a recurring task needs to run right: steps, order, sources, rules.
   - Not in skills: figures (data that changes from run to run, or that a spreadsheet owns, like balances, totals, counts) and stored column letters or row numbers. Read headers and labels from the sheet at run time.
   - Allowed: ids and links (spreadsheet ids, folder links); fixed rule thresholds (a spend cap); slow-changing settings no sheet holds (a yearly premium), kept in one labelled place in the skill with the date set.
   - Naming: a project's skills start with the project's name, lowercase, spaces as dashes (e.g. travel-...). Skills used across projects start with global-.
2. **Project docs** (.md files in a project, or the project's Drive folder) hold nice-to-have context: background, decisions and why, contacts. Never a copy of a skill's procedure. A project's index file holds the ids relevant to it (Drive folders, sheets).
3. **Memory** holds facts about the user and how they want Claude to work. A fact only one project needs goes in that project's memory. A fact two or more projects need stays global, because projects cannot read each other's memory.
   - Not in memory: procedures, project status.
4. **Master data** lives in spreadsheets or documents, never in .md files. One home per fact; everything else points to it.
   - Exception: a figure fixed for good (an amount already paid, a signed price, a past date) may be repeated.
5. **Templates are blank**: placeholders only (City A, <date>, <name>), never a real person's, client's or month's details.
   - Exception: worked examples inside a skill, under a clear "EXAMPLE ONLY" heading.
6. **Keep only what earns its place**: every stored item needs a purpose (a skill run, decision or recurring question that would go wrong or be slower without it). No purpose means deleted, not moved.

Write the rules you used, one per line, to `$DUMP/rules.txt`. The page shows them.

**What this audit is for.** The TYPE of each piece of information and whether it sits in the right place. It is not a content review: do not flag things for being out of date or contradicting each other. "No purpose" is a rule (nothing uses it), not a judgement on whether it is current.

**Never audit:** Anthropic's built-in skills (anything under /mnt/skills/public or /mnt/skills/examples, or that the user did not write), and projects listed under "Skip list" at the bottom of this file.

## Step 1: Dump everything to disk

Work in `DUMP=/home/claude/kaudit` with folders `memory/`, `flags/`, `drive/`. Write the rules plus the flag schema below to `$DUMP/RULE.md` so every reader uses the same thing.

**Flag schema**, one JSON file per group: `{"<memory path or skill name>": [{"label": ..., "line": "<offending line, max 20 words>", "suggest": "<where it should go, max 12 words>", "easy": true|false}]}`. Labels, exactly:
- Procedure in memory
- Project status in memory
- Single-project fact in global
- Duplicate (name the other home)
- Figures in .md/skill (only run-to-run data or sheet-owned numbers; ids, links and fixed thresholds are never flagged)
- Naming (a project skill not starting with its project's name, or a cross-project skill not starting with global-)
- Filled-in template
- No purpose (nothing would go wrong without it: delete, don't move)
- Unclear home

Empty list when clean. Only flag what really breaks a rule. Count each problem once: when the same text sits in two homes, flag only the copy that should go and name the one to keep.

**Severity.** Red = information in the wrong place (every label except Duplicate and No purpose): it has to move or go. Yellow = Duplicate or No purpose: some duplication is fine and the audit cannot know every purpose, so these are the user's call. For every red flag set `"easy": true` when the fix needs no judgement (delete a line whose content already lives in its proper home, swap a real value for a placeholder, rename a skill to the right prefix, fix a broken pointer); otherwise false.

1. **Projects.** `memory_list` with no prefix. For each `/projects/<id>/`, read its index file for a name; if none, infer one from the files and mark it "(no name set)". Leave out anything on the Skip list. If there are projects you have not seen before, ask the user once (multi-select) which are archived or should be skipped, and offer to add them to the Skip list with a skill edit so they are never asked again. Write `$DUMP/projects.json` as `{id: name}` for the projects to audit.
2. **Memory.** Copy every memory file VERBATIM to `$DUMP/memory<path>` (drop any size header the read tool adds). Flag as you go:
   - global /profile.md, /preferences.md, /areas/, /topics/, /people/ (a person or topic only one project uses is "Single-project fact in global"; how-to files are "Procedure in memory")
   - each project's memory (project memory may hold single-project facts; still flag procedures, status, figures and duplicates with global or other projects)
3. **Skills.** Find the user's own skills: every SKILL.md under /mnt/skills/user/, ~/.claude/skills/ and /root/.claude/skills/ (any depth), one copy per skill name, skipping built-in ones. Write `$DUMP/skills.json` as `{name: path}`. Do not flag the procedure itself. Do flag figures, stored columns or rows, duplicates with memory or other skills, facts about the user or a project that belong in memory or a project doc, naming, and filled-in templates.
4. **Drive (optional, needs a Drive connector).** For each project, find its Drive folder (search folders by project name). List contents one level deep. Classify files as context doc, transcript/prep, master data, other. Save each context doc verbatim to `$DUMP/drive/<project>/<title>.md` (skip any over 60KB and say so), flag it, and write `$DUMP/drive/inventory.json`: `{"projects":[{"name","folder_url","note","files":[{"title","kind","modified","url","saved_path","flags"}]}],"not_found":[names],"not_found_notes":{name: note}}`. Use the names from projects.json exactly. No connector: skip, the page says "Not checked".

If you can launch parallel agents, split the work (about 50KB of files per agent: global memory, people and topics, projects in two or three groups, skills, Drive), each writing its own `flags/<group>.json`, and check every agent reported before going on; a missing flag file means that group is re-run, not skipped. Otherwise do it in sequence.

## Step 2: Secrets

Grep the dump and the skills for passwords, tokens, API keys, door or gate codes and full account numbers (`grep -rniE "pass(word)?|token|secret|api.?key|door code|=\s*'[^']{12,}'"`, then judge). Write the exact strings to `$DUMP/redact.json` (a JSON list). They are blanked on the page, and each becomes the first fix in Step 4.

## Step 3: Build the page

Run `python3 <this skill's folder>/scripts/build_page.py $DUMP $DUMP/knowledge-map.html "<today's date>"`. It reads `assets/tpl.html` and writes a complete HTML page: a file browser with Global memory, People, Projects and Skills on the left, red and yellow counts on every branch, and an overview with totals, a projects table and the rules.

Publish it as an artifact titled "Knowledge Map Review" (if one already exists from an earlier run, publish over it so the link stays the same). If artifacts are not available, send the HTML file.

## Step 4: Output

Keep it short. Answer first: total red and yellow, and per project. Then the page link. Then the easy reds, grouped by project, each as one line with the exact file, the quoted words and the action, written so the user can paste a group into that project. Then ONE numbered list of at most 20 fixes, red first and yellow after, each marked Red or Yellow, so the user can reply "yes 1-6, no 7":
1. Secrets in plain text.
2. Global memory that breaks the rules: procedures, project status, single-project facts (say which project it moves to).
3. Duplicates across layers or projects (skill vs memory, skill vs skill, project vs project), naming which copy to keep.
4. Skills that break the skill rules: figures, stored columns or rows, filled-in templates, wrong name prefix.
5. Information with no purpose.
6. Projects with no name set, or (if Drive was checked) no Drive folder.

Issues local to one project roll into one line per project: "<project>: <n> red / <n> yellow, worst: ..." (the page lists them all). If nothing is wrong, say so in one line.

## Step 5: Change nothing until the user answers

Then, for the approved fixes only:
- **Memory (global and project):** edit directly; read each file first; smallest edit that does the job.
- **Skills:** propose the complete updated SKILL.md through the skill review card if available; otherwise give the updated file for the user to upload. A rename is a new skill; say the old one must be removed by hand.
- **Drive docs:** edit in place; figures move to their spreadsheet, the doc keeps a pointer.
- **Secrets:** remove them and tell the user where to keep them instead (a password manager); never write a secret anywhere new.
- Rebuild the page at the end so it reflects the fixes.

Tip for the user: a good habit is to open each project afterwards and say "the knowledge audit found these flags, what do you think?", then let Claude debate the options with you before cleaning. Running this monthly as a scheduled task keeps things tidy.

## Skip list

Projects never to audit (archived or deleted). Add a line per project: name and id.
- (none yet)
