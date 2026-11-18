READ-ONLY on memory, skills and Drive. You may only rewrite the flag file(s) you are given under /home/claude/kaudit/flags/ and write your notes under /home/claude/kaudit/review/.

Read /home/claude/kaudit/RULE.md first: the rules, the never-flag decisions, the tests and the output format are all there. Then, for the flag file(s) and files in your scope:

A. Check every existing flag.
   1. The quoted "line" must be findable by plain text search in the file. If it is a paraphrase or has "...", replace it with an exact quote (max 20 words) of the first offending text. Keep "(and N similar)" at the end if there was one, after the exact quote.
   2. It must clearly fail the test it names, the label must be the right one for that test, and "easy" must follow RULE.md.
   3. If it does not clearly fail a test, or falls under a never-flag decision, REMOVE it and record why.
   4. Do not change "status" or "why_new" on a flag you keep.
B. Look for misses. Read every file in your scope line by line against every test for its layer, independently of the first pass. Also run `python3 /home/claude/kaudit/mech.py <your files or folders>` and make sure every hit is either covered by a flag or clearly not a break. Add a flag only for something that clearly fails a test: if you have to argue for it, leave it out. Added flags get "status":"new", "why_new":"missed before", "found_by":"review".
C. One flag per file per test (merge same-test flags in one file into one with "(and N similar)").
D. Duplicates: flag only the copy that should go. The home is decided like this: steps and rules a recurring run needs live in the SKILL; facts about the user, a person or a project live in MEMORY; records a sheet holds live in the SHEET. If your file holds the copy that should stay, remove the Duplicate flag from your side.

Output:
- Overwrite your flag file(s) in place, same format, every key still present ([] when clean), valid JSON.
- /home/claude/kaudit/review/<flag file name>: {"removed":[{"key","line","reason"}],"added":[{"key","line","test"}],"requoted":<count>}
Report in under 70 words: kept / removed / added / requoted, and final red and yellow totals.
