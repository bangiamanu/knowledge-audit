---
name: knowledge-audit
description: Audit everything Claude keeps about you (global memory, people files, each project's memory, your own skills, optionally each project's Drive folder) against a simple knowledge schema; builds a Knowledge map page with red and yellow flags and returns up to 20 yes/no fixes. Use when the user says run the knowledge audit, audit my memory, or /knowledge-audit.
---

# Knowledge audit

Claude's memory grows by itself. Over months it fills with procedures that belong in skills, project status that belongs in project docs, numbers copied from spreadsheets, and the same fact in three places. This skill puts Claude on Claude: it reads everything, checks each piece against a schema with fixed tests, and shows what is in the wrong place.

**Where to run it.** In a regular chat, OUTSIDE any project. Inside a project only that project's memory is visible: if you are inside one, say so in one line and ask the user to start it from a regular chat.

**What it needs.** Memory turned on, and code execution (Settings > Capabilities). Works best with the ability to launch parallel agents. Optional: a Google Drive connector (for the Drive check) and the ability to publish an artifact (for the page, and to keep last run's flags for comparison). Without them, skip those parts and say so in one line.

In this skill, "this skill's folder" is the folder this SKILL.md sits in; `scripts/` and `assets/` are inside it.

## The rules

If the user's preferences or memory already contain their own rules for where knowledge lives (for example a section titled "Where knowledge lives" or "schema"), audit against those, as they read today, and adjust `assets/fixed-tests.txt` to match them in the same turn (through a skill edit the user approves) so the rules and the tests never drift. Otherwise use this default schema:

1. **Skills** hold everything a recurring task needs to run right: steps, order, sources, rules.
   - Not allowed: numbers from a past run (balances, totals, counts, sizes, a price seen once) or anything a spreadsheet owns.
   - Not allowed: column letters, row numbers or cell references. Name the column and find it in the header row at run time.
   - Allowed: ids and links; column names; fixed numbers the run needs (spend caps, a vendor's standing fee); dated lessons without the run's numbers ("Nov 4: X failed, so do Y"); slow-changing settings no sheet holds, kept in one labelled place with the date set.
   - Naming: a project's skills start with the project's name, lowercase, spaces as dashes (e.g. travel-...). Skills used across projects start with global-.
2. **Project docs** (.md files in a project, or the project's Drive folder) hold nice-to-have context: background, decisions and why, contacts. Never a copy of a skill's procedure.
3. **Memory** holds facts about the user and how they want Claude to work. Global memory loads in every chat; project memory only inside that project.
   - A fact only one project needs goes in that project's memory. A fact two or more projects need stays global, because projects cannot read each other's memory.
   - Each project's memory index file holds the project's ids (Drive folders, sheets, docs).
   - Not allowed anywhere in memory: procedures (step sequences, which tool in what order). A one-line rule about how the user wants something done is fine.
   - Status (a plan, a pending decision, an open to-do) never goes in global memory. Project memory may hold it, dated ("As of <date>: ..."). A fact with a date is not status.
   - A project may set its own conventions in its memory. They apply inside that project only, and that project enforces them.
4. **Master data** lives in spreadsheets or documents, never in .md files. One home per fact; everything else points to it. When something could sit in two places: steps and run rules live in the skill; facts about the user, a person or a project live in memory; records live in the sheet.
   - Exception: a figure fixed for good (an amount already paid, a signed price, a past date) may be repeated.
5. **Templates are blank**: placeholders only (City A, <date>, <name>), never a real person's, client's or month's details.
   - Exception: worked examples inside a skill, under a clear "EXAMPLE ONLY" heading.
6. **Keep only what earns its place**: every stored item needs a purpose (a skill run, decision or recurring question that would go wrong or be slower without it). No purpose means deleted, not moved.
7. **Changing these rules**: never just append. Reread the whole set, put the change where it belongs, and word it as concisely as possible.

The audit tests rules 1 to 6 (rule 7 is about how the rules get edited). `assets/fixed-tests.txt` is rules 1 to 6 written as checks.

**What this audit is for.** The TYPE of each piece of information and whether it sits in the right place. It is not a content review: never flag things for being out of date or contradicting each other. "No purpose" is a rule (nothing uses it), not a judgement on whether it is current.

**The user's skills are their own.** Every skill in scope can be changed with a skill edit the user approves. Never describe any of them as built-in, locked or not editable. Anthropic's built-in skills (under /mnt/skills/public or /mnt/skills/examples, or anything the user did not write) are out of scope.

**Never flag these.** A project's own conventions (never apply or flag them here; each project enforces its own); dated status in PROJECT memory; column NAMES listed in a skill; this skill's own Skip list, Decisions and Standing exceptions sections. When the user rules on a flag ("leave it", "that's fine"), add it under "Decisions" at the bottom of this file with a skill edit, so it is never raised again.

**Every run works the same way, so one run can be compared with the next.** (1) The same fixed tests for every file (`assets/fixed-tests.txt`); never write fresh worker briefs or add a test mid-run. (2) A text search first (`scripts/mech.py`) for the mechanical things. (3) The last run's flags as a checklist: each one is confirmed, fixed or dismissed. (4) A second pass (`assets/REVIEW.md`) that checks every flag and looks for misses. (5) The lead verifies that every quoted line is in its file. A change to the tests or to the never-flag list is made between runs, and the next run's output says so, because it moves the counts.

## Step 1: Dump everything to disk

Work in `DUMP=/home/claude/kaudit` with folders `memory/`, `flags/`, `drive/`, `notes/`, `review/`, `prev/`. Write the rules used, one per line, to `$DUMP/rules.txt` (the page shows them). Copy `scripts/mech.py` and `assets/REVIEW.md` from this skill's folder into `$DUMP/`. Build `$DUMP/RULE.md` so every worker reads the same thing: the rules; the projects to audit (names and ids); the valid skill prefixes (each project's name in lowercase with dashes, plus global-); the "Never flag these" paragraph, the Decisions and Standing exceptions at the bottom of this file; the files that changed since the last run; and the whole of `assets/fixed-tests.txt`, verbatim.

**Baseline.** If a previous run published the page as an artifact with a `baseline.json` next to it, read that file and split it into `$DUMP/prev/<flag file name>` plus `prev/drive.json`; it holds the last run's flags and the time of that run. A file counts as changed when its updated time (memory_list) or modified time (skill file) is later than the baseline's time. No baseline: run without a checklist and say so in the output.

**Flag schema**, one JSON object per flag file: `{"<memory path or skill name>": [{"label", "test", "line", "suggest", "easy", "status", "why_new"}]}` (full format in `assets/fixed-tests.txt`). Labels, exactly: Procedure in memory, Project status in memory, Single-project fact in global, Duplicate, Figures in .md/skill, Naming, Filled-in template, No purpose, Unclear home. Only flag what clearly fails one of the fixed tests: if it has to be argued for, it is not a flag. Count each problem once.

**Severity.** Red = information in the wrong place (every label except Duplicate and No purpose): it has to move or go. Yellow = Duplicate or No purpose: worth checking, the user's call. A red flag is "easy" when the fix needs no judgement (delete a line whose content already lives in its proper home, swap a real value for a placeholder, rename a skill to the right prefix, fix a broken pointer).

1. **Projects.** `memory_list` with no prefix. For each `/projects/<id>/`, read its index file for a name; if none, infer one from the files and mark it "(no name set)". Leave out anything on the Skip list. If there are projects you have not seen before, ask the user once (multi-select) which are archived or should be skipped, and offer to add them to the Skip list with a skill edit so they are never asked again. Write `$DUMP/projects.json` as `{id: name}` for the projects to audit, and `$DUMP/paths.txt` with every memory path of global memory and those projects, one per line.
2. **Skills.** Find the user's own skills: every SKILL.md under /mnt/skills/user/, ~/.claude/skills/ and /root/.claude/skills/ (any depth), one copy per skill name, skipping built-in ones. Write `$DUMP/skills.json` as `{name: path}`.
3. **First pass.** Launch in ONE message, all in parallel (or in sequence if agents are not available). The groups are fixed: the same split every run; add a group only when a new project or skill family appears. Every worker's brief has three parts and nothing else: read `$DUMP/RULE.md` first and follow it exactly; your scope (the exact paths or skill folders, the layer and its tests, and which memory or skills to compare against for duplicates); your output files (`flags/<name>.json` and `notes/<name>.json`). Groups, about 50KB of files each:
   - global: /profile.md, /preferences.md, /areas/ → `flags/global-areas.json`
   - global: /people/, /topics/ → `flags/global-people-topics.json`
   - project memory: the largest project alone if over ~40KB, the rest split into two or three groups → `flags/proj-<x>.json`
   - skills: one worker per name prefix family (each project's skills, the global- skills, the rest) → `flags/skills-<family>.json`
   - Drive (optional, needs a Drive connector): for each project, find its Drive folder (search folders by project name). List contents one level deep. Classify files as context doc, transcript/prep, master data, other. Save each context doc verbatim to `$DUMP/drive/<project>/<title>.md` (skip any over 60KB and say so), flag it, and write `$DUMP/drive/inventory.json`: `{"projects":[{"name","folder_url","note","files":[{"title","kind","modified","url","saved_path","flags"}]}],"not_found":[names],"not_found_notes":{name: note}}`. Use the names from projects.json exactly. No connector: skip; the page says "Not checked".
4. Check every worker reported; a missing flag file means that group is re-run, not skipped. If the same key turns up in two flag files, merge its flags into one file.
5. **Second pass**, once every first-pass file is in: launch reviewers in parallel, one per flag file (the two global files together). Each brief has two parts and nothing else: read `$DUMP/REVIEW.md` and follow it; your flag file(s), where the files they cover sit on disk, and your notes file `review/<name>.json`. Reviewers read the dump on disk and the skills in place; they call no memory tool.
6. **Lead checks, by script:** every flag's quoted line must be found in its file by plain search (strip a leading "Broken pointer:" or "Secret:" and a trailing "(and N similar)"); any that is not goes back to its reviewer. Where a Duplicate is flagged on both copies, keep one flag, on the copy that should go.
7. Count confirmed, new, fixed and dismissed from the flag, notes and review files, for the output.

## Step 2: Secrets

Grep the dump and the skills for passwords, tokens, API keys, door or gate codes and full account numbers (`grep -rniE "pass(word)?|token|secret|api.?key|door code|codes? used|=\s*'[^']{12,}'"`, then judge). Write the exact strings to `$DUMP/redact.json` (a JSON list). They are blanked on the page, and each one becomes the first fix in Step 4, unless it is listed under Standing exceptions at the bottom of this file (still blank it on the page, but never flag it).

## Step 3: Build and publish the page

Run `python3 <this skill's folder>/scripts/build_page.py $DUMP $DUMP/knowledge-map.html "<today's date>"`. It reads `assets/tpl.html` and writes a complete HTML page: a file browser with Global memory, People, Projects and Skills on the left, red and yellow counts on every branch, flags new this run marked, and an overview with totals, a projects table and the rules.

Publish it as an artifact titled "Knowledge Map Review" (if one exists from an earlier run, publish over it so the link stays the same), together with `baseline.json` for the next run's checklist: `{"date", "at": <ISO time of this run>, "flags": {<flag file name>: <its content>}, "drive": [{"project", "title", "url", "flags"}]}`. It must not contain any string from redact.json. If artifacts are not available, send the HTML file and say the next run will have no checklist.

## Step 4: Output

Keep it short. Answer first: total red and yellow, and per project. Then the page link. Then one line comparing with the last run: how many flags were confirmed, dropped (fixed, or did not hold up) and new, and for the new ones whether the file changed or it was missed before. If the tests or the never-flag list changed since the last run, say that first, because the counts are then not comparable. Then the easy reds, grouped by project, each group written as a note the user can paste into that project: one line per fix with the exact file, the quoted words and the action. Then ONE numbered list of at most 20 fixes, red first and yellow after, each marked Red or Yellow, so the user can reply "yes 1-6, no 7":
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
- Rebuild and republish the page at the end so it reflects the fixes.

Tip for the user: open each project afterwards and say "the knowledge audit found these flags, what do you think?", then let Claude debate the options with you before cleaning. Running this monthly as a scheduled task keeps things tidy.

## Skip list

Projects never to audit (archived or deleted). One line per project: name and id.
- (none yet)

## Decisions

Flags the user has ruled on; never raise them again. One line each, with the date.
- (none yet)

## Standing exceptions

Secrets or other items the user has chosen to keep where they are. Blank them on the page, never flag them.
- (none yet)
