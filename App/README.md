# App

This is the VoiceOfOpenDoor Workbench - a local, Windows-first, screen-reader-first web application. Same interface pattern as Open Door Design's other apps (vanilla HTML/CSS/JS backed by a small local Python server), but launched like a desktop app rather than requiring a terminal command every time - see "Launch Model" below.

## Launch Model

Decision: **local web server behind a browser UI, started with a double-clickable launcher** (Option C, discussed with Dean/Chap on July 28, 2026) - not a bare Flask dev command, and not a separate native Windows GUI framework.

- `launch.py` starts the server with debug mode off and opens the default browser automatically.
- `Launch VoiceOfOpenDoor.bat` and `Setup.bat` live at the repository root (`VoiceOfOpenDoor/`), not in this folder — Dean relocated them there on July 29, 2026, since a top-level entry point is more discoverable than one buried inside `App/`. They point at `App/launch.py` and `App/requirements.txt` respectively. `launch.py` and `requirements.txt` themselves stay in this folder along with the rest of the App code.
- `App/backend/app.py` can still be run directly (`python app.py`) for development - that keeps Flask's debug reloader on.

This matches the same interface style as Media Workflow Assistant (HTML tested directly against JAWS/NVDA) while removing the need to open a terminal and type a command every time the app is used.

## Vision: The Minimum Lovable Product

Every tool in the nav is a real route today, even where the screen behind it isn't built yet:

- Home (built)
- Recordings (built)
- Analyze (stub)
- Transcripts (stub)
- Segments (stub)
- Train (stub)
- Generate Speech (stub)
- Settings (stub)

A stub page says plainly "Not yet built" and what it will do - it never fakes functionality. The nav itself is a real, working, screen-reader-navigable skeleton of the whole application, not a plan for one.

(This list consolidates the earlier, longer tool list from the Voice Pipeline Roadmap - e.g. Pronunciations folds into Segments/Train, Models and Evaluate Voice fold into Train, Reports folds into Settings - into the tighter nav Dean and Chap converged on. If that consolidation stops making sense once those areas are actually built, split them back out.)

## What's Actually Built

**Home screen** (`/`) — the current-status summary (recording counts by classification, one recommended next action). This is the landing view, kept to a simple current-task-style summary rather than requiring navigation through documentation to find what to do next.

**Recordings screen** (`/recordings`) — the full recording list grouped by classification, each linking to a detail page. Backed by `Dataset/Metadata/recordings.json`, which is itself built by `Tools/Dataset Utilities/build_manifest.py` from the real analyze.py report plus the classifications documented in Recording Assessment v1/v2.

**Recording detail page** (`/recording/<file>`) — duration, classification, the documented basis for that classification, and any objective flags from analyze.py. Also a real management screen (play, change classification, notes, delete) - see the July 29 session below.

**Add Recordings** (`/recordings/import`) — added July 30, 2026, per the Development and Testing Roadmap's Phase 1 requirement. See the dedicated section below.

**Shared shell** (`base.html`) — skip-to-content link, a `<nav aria-label="Workbench">` landmark with all 8 tools, `aria-current="page"` on the active one. This exists so a screen reader user can jump straight past the nav via landmark navigation on repeat visits, while it's still fully available to tab/arrow through when wanted.

**Kept as a separate page, not inlined** - Dean explicitly left that choice to Claude. Reasoning: the Recordings page already has five classification sections; adding a full file-input form to it would be exactly the kind of complexity-for-its-own-sake the project's Prime Directive treats as a defect. A single entry point under its own heading, leading to a dedicated page, keeps the list page focused on browsing while the import workflow gets room to breathe (two separate forms, format/duplicate explanation text) without crowding either.

**Heading structure fixed (July 30, 2026):** the "Add Recordings" entry point on the Recordings page was a bare button floating before the H1's content, with no heading of its own - inconsistent with every other section on that page. Wrapped it in its own `<section>` with an `<h2>Add Recordings</h2>`, matching the pattern used everywhere else.

## Add Recordings (July 30, 2026)

Per the Development and Testing Roadmap: the app had no way to add recordings back after they'd been reviewed and deleted - a real gap Dean caught. `/recordings/import` (linked from the Recordings page) accepts one or more `.wav`/`.mp3`/`.m4a` files and, for each one:

- Rejects unsupported types with a specific reason (`.mov` explicitly called out as "not supported yet - audio-track extraction hasn't been built," rather than a generic rejection).
- Rejects filename duplicates (a file already in the corpus with that exact name) without overwriting.
- Rejects content duplicates by SHA-256 checksum, even under a different filename, naming which existing recording it matches.
- Detects damaged/unreadable files - not just an explicit ffprobe error, but also the case where ffprobe returns valid-but-empty JSON for a non-audio file (a real bug caught during testing - see below).
- On success: saves the file under its original filename, runs it through the same `analyze.py` used for the rest of the corpus, and adds a manifest entry classified as Evaluation Only with a note recording when and how it was imported.
- Reports exact per-file results on a dedicated results page (imported / skipped / failed, with a specific reason for every skip and failure) - not a single summary line, since multiple files can fail for different reasons in one import.

**A real bug found and fixed during testing:** the first version checked for an explicit `error` key from the analyzer to detect damaged files. A garbage/non-audio file doesn't necessarily make `ffprobe` error out - it can return valid, parseable JSON with no audio stream found at all (no codec, zero duration). That file was incorrectly imported as if it were valid audio. Fixed by also treating a missing codec or zero/missing duration as a failure, not just an explicit error.

**Tested for real**, in a disposable copy: imported a genuine new file with spaces in its filename; correctly rejected a duplicate filename; correctly rejected duplicate content under a different filename (named the actual matching file); correctly rejected an unsupported `.mov`; correctly failed a garbage/non-audio file (after finding and fixing the bug above) with a specific reason; confirmed the manifest went from 18 to 19 entries with correct metadata; confirmed the newly imported recording appears in the right classification group on Recordings and its detail page works normally, including play/classify/notes/delete. Also tested folder selection specifically: simulated a folder-selected file (path-prefixed filename, e.g. `MyRecordings/Session1/take1.mp3`, which is what a browser actually sends for `webkitdirectory` selection) and confirmed it correctly flattens to just `take1.mp3` on both the results page and disk, with no stray subdirectory created in `Dataset/Raw Audio/`.

**Folder import**, added after Dean asked whether it existed: a second form on the Add Recordings page uses `webkitdirectory` to let Chrome/Edge select an entire folder; every file inside (including subfolders) is submitted and processed through the same per-file logic as individual file selection. Not supported in Firefox or Safari - stated on the page rather than silently failing there. Files two levels of subfolders deep with the same base filename would collide under the flat corpus structure the same way any other filename duplicate would - a known, accepted limitation given the corpus is flat everywhere else, not something worked around here.

**Not implemented:** video audio-track extraction for `.mov` files selected via either form.

## Fixes From Dean's JAWS Test (July 28, 2026)

Dean tested the Recordings and recording detail pages with JAWS on Windows and reported two real problems, not hypothetical ones:

**1. Too many landmarks.** Each category section (`aria-labelledby`) was exposed as a separate named "region," so JAWS reported six regions on the Recordings page alone. Fixed: removed `aria-labelledby`/`id` from every category and content section across Home, Recordings, and the detail page. `<section>` without an accessible name isn't exposed as a landmark at all - only `<nav>` and `<main>` are regions now, everywhere, consistently. H2 headings are unchanged and still fully usable for heading navigation.

**2. The detail page was a report, not a working screen.** Dean opened a rejected recording and found nothing he could actually do there. Added real actions:
- **Play Recording** — a native `<audio controls>` element, served from a new `/audio/<file>` route. Native browser control, no custom JS widget.
- **Change Classification** — a `<select>` + native `<button>`, covers moving a recording between any category (including restoring a Rejected recording) with a single control rather than two overlapping ones - see the note on that choice below.
- **Notes** — a separate `user_notes` field (distinct from the documented assessment "Basis," so an ad hoc note never overwrites the recorded engineering conclusion).
- **Delete Recording** — button leads to a required confirmation page (`/recording/<file>/delete/confirm`) before anything is removed. The confirmation page's own heading takes focus. Only a POST from that confirmation page actually deletes the file and its manifest entry - visiting the confirmation page alone deletes nothing.
- **Return to Recordings** — unchanged, kept as a plain link since it's navigation, not an action.

After Save Classification, Save Notes, or Delete, the server redirects to a page with a `status-message` element (`tabindex="-1"`); a small shared script (`static/app.js`) moves focus there on load, so focus never gets stranded at the top of the page or in an unlabeled field.

**On "Move or restore recording":** Dean's list named this as a capability separate from "Change classification." In the current data model, categories ARE the corpus organization - there's no separate physical folder structure a file also lives in - so "moving" a recording between categories and "changing its classification" are the same operation. Implemented as one control rather than two, per the project's own standing rule against shipping two interaction paths for the same decision. If Dean meant something else by "move" (e.g. an actual filesystem reorganization independent of classification), say so and it'll be built as a distinct feature.

## Design System

As of July 29, 2026, this app uses Open Door Design's shared design system (`DesignPhilosophyAndStandards` repository) instead of a one-off local stylesheet. `odd-theme.css`, `odd-layout.css`, `odd-components.css`, and `odd-utilities.css` are vendored into `frontend/static/` and linked before `style.css`, which now only contains what's actually specific to this app (the button-as-link pattern's visual treatment and the status-message box). This replaces a bespoke blue accent color and hand-rolled focus/skip-link styling with the same tokens, palette, focus treatment, touch targets, and skip-link behavior used across other Open Door Design apps.

**Resynced July 30, 2026 - no-blue palette.** Open Door Design's design standard was updated (in a separate session, after this app's original sync) to exclude blue and navy entirely, not just avoid pairing them with green - headings and the color previously called "secondary" changed from navy (`#102A43` / `#17324D`) to near-black/charcoal (`#111111` / `#3B3B3B`). This app's vendored CSS was still on the old navy values until Dean provided the updated `DesignPhilosophyAndStandards` upload. Resynced all four shared CSS files; since every color in this app's own `style.css` already referenced the shared tokens (`var(--odd-color-...)`) rather than hardcoded values, no changes were needed there - it inherited the fix automatically. Confirmed zero blue/navy hex values remain anywhere in the App's CSS.

**A note on the source repository itself:** while resyncing, found that `DesignPhilosophyAndStandards/Components/CSS/` and `Components/Carousel/` both had stray duplicate files reappear - identical copies of content already safely archived under `Archive/CSS-Pre-Website-Sync-2026-07-29/`. This is almost certainly the same zip-overlay pattern flagged before (extracting a new zip over an existing folder doesn't remove files that were deleted in the new zip) rather than anything intentional. Not fixed here since it's a different repository - flagged to Dean.

One deliberate local deviation, not a gap: the nav and internal navigation use `<button class="as-link">` instead of `<a>` (see below), so the shared `.nav-list a` rules in `odd-layout.css` don't apply to them directly. `style.css` mirrors those same rules onto `.nav-list .as-link` rather than duplicating the whole nav styling independently.

## External Data Architecture (Aug 5, 2026)

**Follow-up fix, same day - Original Recordings wasn't actually authoritative yet.** After the architecture above shipped, Dean reported that recordings genuinely present in the configured Original Recordings folder still showed as "0 recordings total" on Home after a full restart. The gap: the manifest, not the folder, was the only thing the app actually treated as truth - a file with no manifest entry was invisible no matter where it physically sat. Fixed with real discovery/registration, not just documentation:

- **Startup discovery**: runs once when `app.py` is imported - not inside `if __name__ == "__main__"`, since that block never executes on the real launch path (`launch.py` imports `app` as a module and calls `.run()` itself; only direct `python app.py` hits `__main__`). If a valid data root is already configured, Original Recordings is scanned before the server starts accepting requests, so the very first page already reflects reality - no in-page "scanning" progress UI needed, since nothing has been served yet for focus to land on. Status prints to the console, consistent with `launch.py`'s existing startup messages.
- **Manual scan** (`/recordings/scan`, POST): a "Scan Existing Recordings" button on both the Recordings page and Settings, for files copied in while the app is already running. Same underlying function as startup discovery - one implementation, not two.
- Matches files primarily by filename (stable within the flat Original Recordings folder) and secondarily by content checksum, so a file that's actually a duplicate under a different name is recognized as already-registered rather than added a second time - tested explicitly (copied a registered file under a new name, confirmed it did not get double-registered).
- Valid new files get real analysis (via the same `analyze_file()` everyone else uses) and are classified Evaluation Only, matching Add Recordings' own default. Damaged/unsupported files are reported with a specific reason but *not* added to the manifest - consistent with how Add Recordings already treats a bad upload, not a new, different behavior.
- One failure never stops the rest of a scan - same pattern as Analyze's batch hardening.
- **Damaged manifest recovery**: `load_manifest()` now catches a corrupt/unparseable JSON file instead of crashing the whole app. The damaged file is renamed to `recordings.json.damaged` (preserved, not deleted) and treated as empty so discovery can rebuild it from Original Recordings. Rebuilding is honest, not magic: a classification or note that only existed in the corrupted file is genuinely gone - discovery rebuilds fresh (Evaluation Only, discovery note), it does not recover lost human judgments from unparseable JSON. Tested explicitly: corrupted a real manifest, restarted, confirmed no crash, confirmed the `.damaged` backup exists, confirmed the rebuilt entry is honestly `Evaluation Only` rather than falsely showing the pre-corruption value.
- Add Recordings' "file already exists on disk" message now specifically points to Scan Existing Recordings instead of a generic "not overwritten" note - addresses the directive's "if a user selects the Original Recordings folder itself" case without needing two separate code paths for what's functionally the same outcome.

**Tested for real**, in a disposable external folder, not claimed: empty folder, files present with no manifest at all, multiple valid files, an unsupported file, a damaged file, files added between restarts, a file added while the app was running (picked up by the next process's own startup scan, confirming both mechanisms are consistent), a duplicate under a new filename, a missing manifest, a corrupted manifest, one bad file inside an otherwise-valid batch, and - critically - that an existing entry's manually-edited classification and notes survive completely untouched across a restart that also discovers new files.

## Workflow-Based Recommendation (Aug 5, 2026)

**The problem:** after discovery/registration shipped, Dean reported that Home recommended "review the first Evaluation Only recording" - arbitrary, and not reflective of an analysis-first architecture. Replaced entirely, not patched.

**A new axis, deliberately separate from classification:** `compute_workflow_status(record)` returns `Analysis Clear` / `Needs Review` / `Analysis Failed` / `Not Analyzed` - computed fresh from the stored analysis every time, never cached on the record, so it can't drift out of sync. This is never written into `classification` and never auto-promotes anything to `Candidate` - a human still decides that. The two fields answer different questions: classification is "does this belong in the corpus," workflow status is "does this need a look right now."

**A specific whitelist, not "any flag":** only clipping/near-clipping, unusually low level, excessive silence, unusual channel configuration, and analysis failure put a recording in Needs Review. The existing low-bitrate flag is real and stays visible on the recording's own page, but doesn't by itself trigger Needs Review - it isn't one of the categories Dean specified. `analyze.py` itself was extended to actually support two categories it didn't check for before: excessive silence (a new percentage-based metric - total silence duration over total duration, not a raw context-free segment count) and unusual channel configuration (anything other than mono or stereo).

**Analysis-first, for real:** discovery, manual scan, and Add Recordings all now call `run_analysis()` as part of registration - one call, reused for both validating the file and producing the stored analysis, not analyzed twice. A newly discovered or imported recording is never left sitting as "Not Analyzed" waiting for someone to remember to run Analyze separately.

**Startup console output** matches the exact sequence specified: `Scanning local recordings...` → `Analyzing N new recordings...` → `Analysis complete: X clear, Y need review, Z failed.` - not a line per file.

**Home and Recordings rebuilt around this:** Home states the workflow-outcome tally in the required wording and links to "Review recordings with possible issues (N)" - a real filtered view, not a single arbitrary file - or states "No recordings currently require attention." when nothing does, verified for the exact wording in both cases. Recordings gained three new views (recordings with possible issues, analysis failed, no objective issues) alongside the existing classification groups, which are unchanged and still the default view.

**A real bug found and fixed while testing, not shipped with it:** a damaged file found during discovery was never actually being registered - just reported and then invisible, meaning it silently disappeared from Home's tally instead of showing as "could not be analyzed." Fixed to register failed analyses too, with the specific failure reason visible on the recording's own page. That fix then exposed a second bug: the manifest-save condition only checked whether anything had been *successfully* added, so a scan that only found a failed file never persisted it - fixed in all three places that check it (startup discovery, manual scan, and the post-setup scan).

**Tested for real**, in a disposable external folder, not claimed: all-recordings-clear (verified the exact "No recordings currently require attention" wording), some-flagged (verified the exact recommendation wording and count), all-analysis-failed (after the two-bug fix above - verified the failed recording persists, shows in Home's tally, and renders its failure reason on its own page), a mixed batch in one scan (one already-registered/stale file, one new valid file, one damaged file - confirmed the valid one succeeded and the batch didn't stop), source-file-changed staleness (confirmed the Analyze page's existing stale detection - built in an earlier round - correctly coexists with the new workflow status, which deliberately does not itself account for staleness; that remains an Analyze-page concern, not a "needs review" trigger), and restart persistence for both a successful and a failed registration.

## External Data Architecture - original build (Aug 5, 2026)

VoiceOfOpenDoor is now published on GitHub. The repository holds application code only - every recording, the manifest, transcripts, segments, and models live in a folder Dean chooses, outside the repository entirely.

**Configuration:** `App/local-settings.json` stores the chosen path (`{"data_root": "..."}`), gitignored, never committed. `App/local-settings.example.json` is committed with a placeholder path, never Dean's real one. `App/backend/local_data.py` is the module that owns loading/saving config, validating a folder (exists + writable), creating the required subfolders, and migration.

**Required subfolders**, created automatically once a data root is confirmed: `Incoming Recordings`, `Original Recordings`, `Processed Recordings`, `Rejected Recordings`, `Transcripts`, `Segments`, `Models`, `Exports`, `Backups`, and `Metadata` (not one of the nine named in the directive, but the manifest itself contains Dean's private classifications and notes - it can't stay in a public repository either, so it gets its own folder alongside the required nine rather than being placed loose at the data root without explanation).

**Enforcement, not a suggestion:** a `before_request` hook checks every route except the setup flow itself. If the configured folder is missing, unconfigured, or unwritable, every request redirects to `/setup` - there is no code path that falls back to reading or writing the old in-repo `Dataset/Raw Audio/` location silently. `AUDIO_DIR` and `MANIFEST_PATH` are no longer fixed module constants; `get_audio_dir()` / `get_manifest_path()` read the current config on every call, so changing the data root from Settings takes effect immediately without a restart.

**First run / change folder (`/setup`):** one form, a text path field. A native OS folder-picker dialog was considered and deliberately not built - the directive itself hedges this as "where practical," and a real native dialog invoked from inside a Flask request handler (e.g. via `tkinter.filedialog`) is exactly the kind of thing that can hang a request or behave unpredictably depending on the desktop session, and nothing in this sandbox could verify it works before shipping it. A typed/pasted path is reliable, fully keyboard accessible, and matches how Dean actually gave the real path in the first place. If the folder doesn't exist yet, it's created; if it exists but isn't writable, a clear error is shown - never a silent failure.

**Migration (`/setup/migrate`):** if recordings are still found in the old in-repo `Dataset/Raw Audio/`, the app detects them and offers Move, Copy, or Skip before continuing to Home. Both Move and Copy verify the destination file's SHA-256 checksum matches the source exactly before Move deletes anything - if verification fails, the bad partial copy is removed and the original is left completely untouched. The manifest (classifications, notes, analysis results) migrates alongside the audio, merged into the new location rather than overwritten.

**Settings (`/settings`) is now real**, not a stub: current data folder path, availability, writable status, and recording/transcript/segment/model counts, plus Validate Data Folder, Open Data Folder (uses `os.startfile()` on Windows - the reference platform; reports a clear message rather than failing silently elsewhere, though this specific call couldn't be exercised in this sandbox at all, Linux-only, no Windows to test against), and Change Data Folder (routes back through the same setup flow).

**Recording lifecycle:** a new `status` field (`Active` / `Archived`), default `Active`, distinct from the existing `classification` field. Archiving removes a recording from the active workflow (excluded from Home's counts and the Recordings page's main groups) without deleting it - a new "Archived" section on Recordings and an Archive/Restore action on each recording's detail page. Reconciled deliberately with what already existed rather than duplicating it: the directive's "Rejected" and "Deleted" states already exist as `classification: "Rejected"` and the existing hard-delete-with-confirmation flow, both already correct per the directive's own description of what they should do (retained until explicit permanent deletion, confirmation required). Only "Archived" was genuinely new and got built as such - flagged here explicitly in case a fully separate parallel status field was actually wanted instead of this reconciliation.

**Tested for real**, in disposable copies with disposable temp folders, not claimed: an unavailable/unconfigured folder correctly redirects to setup with a clear error; confirming a new path creates all ten subfolders; migration correctly detects the real 20-file legacy corpus and offers Move/Copy/Skip; Copy migration verified (originals untouched, manifest merged with classifications intact); a fresh process (restart simulation) loads the configured folder directly with no setup redirect and the corpus intact; audio streaming and Analyze both work against a recording stored only in the external folder; Add Recordings saves into the external `Original Recordings` and Settings' count updates correctly; changing the data root takes effect without restarting the app. **Not reliably testable in this sandbox:** the read-only-folder rejection path - this sandbox runs as root, and Linux permission checks are bypassed for root regardless of a folder's actual permission bits, so `os.access(root, os.W_OK)` returns `True` even on a folder chmod'd to read-only. The check exists and is structurally correct, but its real-world behavior on Dean's Windows machine, running as a normal user, is unverified by anything in this session.

**Zip delivery change:** per the directive, this and future deliveries no longer include the private recording corpus or the real manifest content - `Dataset/Raw Audio/` and `Dataset/Metadata/` ship empty (matching what `.gitignore` will exclude going forward). This does not delete anything from Dean's own repository folder - because extracting a zip over an existing folder never removes files absent from the new zip (the same behavior noted several times earlier for deleted files), his real corpus stays exactly where it is until he runs the new Setup/Migration flow himself to move it out to the external folder for good.

## Analyze (July 30/Aug 5, 2026)

Real, working production feature, built per Dean's explicit production directive - not documentation, not a design direction, an actual `/analyze` page.

**How it works:** `App/backend/analysis_service.py` is the adapter between the App and `Tools/Audio Processing/analyze.py` - it calls the real `analyze_file()` function, doesn't reimplement any analysis logic. Results are stored on each recording's manifest entry under a new `"analysis"` object: status, timestamp, analyzer version, source file modification time (for staleness detection), and every field the real analyzer produces (duration, codec, sample rate, channels, size, mean/peak volume, silence segment count, objective flags). Nothing invented beyond what `analyze.py` actually supports - no speech detection, speaker count, or music detection, since no real tool implements those yet.

**Actions available**, group-based first per Dean's explicit anti-checkbox-clutter direction:
- Analyze All Needing Analysis (one button, no selection required) - the primary path.
- Analyze all recordings in one classification (one button per non-empty group).
- Re-analyze all recordings whose source file changed since last analysis ("stale").
- Analyze Selected / Re-analyze Selected (checkboxes) - the explicit exception mechanism for cherry-picking, not the default.
- Re-run Analysis directly from a recording's detail page - returns to that same recording with a status message, not the generic batch results page.

**Persistence:** `Tools/Dataset Utilities/build_manifest.py`'s merge logic was extended to preserve the `analysis` field across manifest regeneration, the same way it already preserves classification and notes.

**A real, pre-existing bug found and fixed while testing this, unrelated to Analyze itself:** two recordings (`Editedaudio1407063783.m4a`, `RecUpAppTest Recording.mp3` - both re-imported earlier after being deleted) existed as real files in `Dataset/Raw Audio/` but had no manifest entry at all, making them invisible to the entire App - Recordings list, Home counts, everything. Root cause not fully traced, but repaired using real `analyze_file()` output for the technical fields and the same classification/note Add Recordings would have assigned, rather than fabricated data.

**A real accessibility bug caught during testing, not shipped:** the first version displayed the analysis timestamp as a raw ISO string (`2026-08-05T18:04:30+00:00`) and duration as raw decimal seconds (`39.13 seconds`) - both violate the project's own established natural-language-time requirement. Fixed with a new `natural_datetime()` helper (`August 5, 2026 at 6:07 PM`) and reused the existing `natural_duration()` helper for duration. The datetime formatter deliberately avoids the `%-I`/`%#I` strftime flags for a no-leading-zero hour - those are platform-specific (Linux vs. Windows) and this must run correctly on Windows; hour formatting is computed manually instead.

**Tested for real**, in disposable copies, not claimed: single-file analysis, group analysis, "all needing" analysis (all 20), re-analysis (confirmed the timestamp actually updates), a batch containing two failures plus one valid file (confirmed the valid one still succeeds - a failure doesn't stop the batch), a damaged/non-audio file, a missing file, an unsupported-format file (funnels through the same "no readable audio stream" path as damaged, which is reasonable since `analyze_file()` doesn't discriminate by extension), a fresh process simulating an app restart (data persisted), and manifest regeneration (analysis preserved, same as classification/notes). Classification and Notes confirmed unchanged by every analysis run.

**Not implemented / known limitations:** no live per-file progress announcement during a batch ("Analyzing recording 3 of 12...") - this is a synchronous request/response; for the corpus's current scale that completes quickly, but a much larger corpus would need real async/progress infrastructure this pass didn't build. The completion summary is the "one navigable location" for progress, not a live-updating one.

**Hardening pass (Aug 5, 2026), per Chap's review:** the original `run_analysis()` called `analyze_file()` unguarded. `analyze.py`'s `subprocess.run()` calls have no exception handling of their own - if FFmpeg/FFprobe isn't on PATH, that raises an uncaught `FileNotFoundError` that would propagate all the way up through the Flask route's batch loop, crashing that request entirely and stopping every remaining file in the batch from being processed - a direct violation of "one failure must not stop the rest of a batch." Reproduced for real (mocked `subprocess.run` to raise `FileNotFoundError`, confirmed the exception actually reached and crashed the un-hardened code) before fixing it, not just fixed on Chap's say-so. `run_analysis()` now catches `FileNotFoundError` (with a specific "FFmpeg or FFprobe was not found... run Setup" message), `PermissionError`, and any other exception, converting each into a structured failed result instead of an unhandled crash. Verified the fix at two levels: the isolated function (confirmed it now returns a clean failure instead of raising), and the actual Flask route end-to-end (simulated FFprobe going missing partway through a 3-file batch sent via a real HTTP request - confirmed a 200 response, the first file succeeding, and the remaining two failing cleanly with the specific message, rather than the request crashing).

## Home Graphic (July 30, 2026, corrected same day)

Dean provided `dino_home_wave.png` (a welcoming image, same style as the "standing in doorway welcoming visitors" image already used on the Open Door Design website's carousel). Placed in `App/frontend/static/` and wired into the Home nav button using the shared design system's existing `.home-link` pattern (`odd-layout.css`), which was already defined for exactly this purpose but unused until now.

**Correction (July 30, 2026, per Chap's review):** the changelog originally described replacing `alt=""` with real alt text as having "fixed a real accessibility bug." That overclaimed the evidence. `alt=""` should normally be silent - Dean was right not to accept it regardless of mechanism, and real alt text matching the established site-wide convention is a genuine improvement on its own merits - but three facts together show it wasn't actually the cause of the "Unlabeled graphic" reports: JAWS continued reporting "Unlabeled graphic" in testing *after* this change; Chrome's own "get image descriptions" feature was already off, so that generic fallback phrase doesn't diagnose anything; and the direct accessibility-tree investigation below found zero unlabeled images anywhere in the app's DOM, before or after the change. The alt-text change stands as a correct, worthwhile fix - it just isn't *the* fix for the symptom Dean was chasing, and shouldn't have been described that way.

**Also fixed, not just a style nitpick:** the source image was 1254x1254px and ~2.7MB despite displaying at 64-96px. Resized to 192px (2x headroom for high-DPI displays) and re-saved with PNG optimization - 69KB, a 97.5% reduction. Worth doing regardless - and now known, per the accessibility-tree investigation below, to have been unrelated to the "Unlabeled graphic" reports, not the cause as originally suspected.

**Confirmed via testing:** the image appears in exactly one place - the nav's Home button, which is part of `base.html` and therefore appears near the top of every page, right after the skip link. Not a footer, not duplicated. It's encountered repeatedly during a JAWS session simply because it's on every page you visit, by design.

**Investigated directly, July 30, 2026 - not from this application.** Per Dean/Chap's suggestion, rather than continue guessing from JAWS transcripts, the real Chrome accessibility tree was queried directly (Playwright + Chromium, the same underlying engine as Chrome, via the accessibility snapshot API - equivalent to what Chrome DevTools' Accessibility panel shows). Every page was checked in full: Home (60 nodes), Recordings (224 nodes), Add Recordings (81 nodes). Result: **exactly one `image`-role node exists on each page, and it is always correctly named "Dino waves you home."** There is no second image, no unlabeled image, no unnamed graphic anywhere in this application's own DOM on any page tested. The file inputs on Add Recordings render as native Chrome buttons with real accessible names ("Audio file or files," "Folder") - not as images.

Conclusion: the application does not expose an unlabeled image - confirmed directly, not inferred. The remaining "Unlabeled graphic" announcements appear to originate outside the application's DOM; that's what the evidence supports, not a specific claim about which external component produced them. A later JAWS transcript (July 30, 2026) adds real corroborating detail without being definitive proof of the exact source: JAWS's own Picture Smart AI description feature, triggered on some of these graphics, described them as app icons under headings literally labeled "ChatGPT" and "Claude" - a four-color pinwheel-style icon and a moon/sun day-night icon, each with a "New" badge. Those are other applications' icons, not anything in this repository, which is consistent with - though doesn't by itself prove - an alt-tab, taskbar, or browser-chrome source. Nothing to remediate in the application; documented with direct evidence rather than left as inference.

## Documentation Corrections (July 30, 2026)

Dean caught two stale hardcoded corpus counts: the main README's Current Status still said "20 archived recordings" (actual count: 18, and changing), and `App/backend/app.py`'s top docstring said "tested against the actual manifest for all 20 corpus recordings." Both fixed - not just updated to 18, but reworded to not hardcode a count that Add Recordings and deletion will keep changing; the README now points to the Home page as the live source of the current total instead. `Documentation/Recording Assessment v2.md`'s "20 recordings" was deliberately left alone - it's a dated historical record of a real past state (before any deletions), not a current-status claim, and changing it would misrepresent history rather than fix staleness.

## Fixes From Dean's July 29 JAWS Session

Two real issues, reported directly, no guessing:

**1. Focus jumping to the top instead of the status message.** The `app.js` focus script ran on `DOMContentLoaded` and called `.focus()` immediately. On a full page navigation, JAWS resets its own virtual cursor to the top of the document and starts reading from there - the script's `.focus()` call could lose that race if JAWS hadn't finished initializing its buffer for the new page yet. Fixed by moving the call to the later `load` event plus a short delay (150ms) before focusing. This is a known, somewhat unreliable race condition in screen reader focus management generally, not something a single change eliminates with certainty - if it's still inconsistent after retesting, the delay may need adjusting.

**2. Too many links for JAWS's link-specific quick navigation (U/V keys).** With up to 19 recordings on the Recordings page alone, plus the 8-item nav on every page, JAWS's unvisited/visited link navigation became noisy without the visited-state distinction actually meaning anything useful. Every internal navigation point (nav menu, recording list items, "Return to Recordings," "Browse all recordings," the Home recommended-action link, "Cancel and return," stub pages' "Back to Home") is now a native `<button type="button" class="as-link" data-href="...">` instead of an `<a>`, styled to look identical to the links they replace. A shared click handler in `app.js` navigates via `window.location.href`. Buttons are excluded from JAWS's link-specific navigation entirely, while remaining fully keyboard operable (native buttons already respond to Enter and Space).

Trade-off, stated plainly rather than left implicit: this loses native "open in new tab" (Ctrl+click / middle-click) and "copy link address" on these elements, since they're no longer real links. For a single-user local app with no reason to open recordings in separate tabs, that trade seems right - flagging it in case that assumption is wrong.

**The skip link** (`<a href="#main-content">`) was left as an `<a>` - that's the one standard, universally-understood exception, and it isn't part of the link-list clutter problem since there's exactly one per page. Also added `tabindex="-1"` to `<main id="main-content">`, since without it, activating the skip link would scroll to the main region but not necessarily move actual keyboard focus there - a separate, related correctness gap not previously caught.

**"DesignPhilosophyAndStandards":** resolved later the same day - see the Design System section above. Dean provided the repository; it's now the design authority for this app.

## Fix: Focus After Delete Not Returning to Working Context (July 29, later session)

Confirmed via a real JAWS session: the landmark fix, button conversion, and delete flow all held up under repeated real use (5 recordings deleted in one session, "2 Regions" consistent throughout). One real problem: after each delete, focus returned to the top of the Recordings page (near the status message, positioned right after the H1). Dean was reviewing and deleting a run of "Evaluation Only" recordings and had to re-navigate past Candidates and Conditional Candidates every single time to get back to where he was working.

Fixed: the delete route now remembers which classification group the deleted recording belonged to, and the Recordings page places the status message right after that specific group's heading instead of at the top of the page - so after deleting an "Evaluation Only" recording, focus lands back at "Evaluation Only," not back at the top of a 5-category list. Also made all five classification groups always render, even at a count of zero, instead of disappearing when emptied out - otherwise deleting the last recording in a group would leave nothing for the message to attach to, and headings shifting in and out of existence as you delete things makes navigation less predictable, not more.

Tested in a disposable copy: deleted a real recording, confirmed the redirect carries the correct group, confirmed the status message renders directly under that group's heading (not the top), and confirmed an emptied group still shows its heading with "(0)" and a plain "No recordings currently in this category" line.

Not synchronized this round: Dean's message this time was a JAWS transcript, not a new zip upload, so the corpus in this delivery is still the 19-recording state from the last real upload, not the 15 remaining after his 5 deletes. That will resync automatically the next time an actual zip comes in - this fix doesn't depend on knowing the current count.

## Verification Status

| Item | Windows 11 (Dean's system) | Temporary AI-assistant sandbox |
|---|---|---|
| Flask app runs, all 9 routes return correctly | Confirmed — app launched successfully on Windows 11, July 28 2026 | Verified — ran against the real corpus manifest |
| No `aria-labelledby`/region on category or content sections (only nav + main are landmarks) | **Confirmed fixed — JAWS retest July 29 2026, "Page has 2 Regions" (nav + main only)** | Verified — 0 occurrences of `aria-labelledby` on Home and Recordings |
| `aria-current="page"` follows the active nav item | Not yet verified | Verified, all pages checked |
| Play Recording (native audio control, streamed from `/audio/<file>`) | **Confirmed working, no issue — Dean's JAWS test, July 29 2026** | Verified — route returns `200 audio/mpeg` for a real file |
| Change Classification (persists to the manifest) | **Confirmed — Dean changed a real classification via JAWS, persisted correctly** | Verified — posted a change, confirmed it persisted on reload |
| Notes (separate field from the documented Basis) | **Confirmed — Dean saved real notes on two recordings via JAWS, persisted correctly** | Verified — posted a note, confirmed it persisted and appears in the textarea on reload |
| Delete: confirmation page required, GET alone deletes nothing | Not yet verified | Verified — visited the confirmation page, confirmed the file was untouched |
| Delete: POST from confirmation actually removes file + manifest entry | **Confirmed — Dean deleted a real recording (RecUpAppTest Recording.mp3) via JAWS; corpus is now 19, confirmed from his own uploaded repository state** | Verified, in a disposable copy — file removed from disk, entry removed from the manifest |
| Deleted recording 404s afterward | Not yet verified | Verified |
| Status message present and read after save/delete | **Confirmed the message itself is read ("Classification updated to Candidate," "Notes saved," "RecUpAppTest Recording.mp3 was permanently deleted.") — but Dean reported focus was jumping to the top of the page instead of landing there reliably; fixed (see below), not yet retested** | Verified `tabindex="-1"` status element renders after each action |
| Home page (skip link, nav region, main region, single H1, heading order, page title, recommended-action link) | **Confirmed working — full JAWS pass, July 28 2026** | Not testable here |
| Internal navigation as native buttons instead of links (nav, recording list, Return to Recordings, etc.) | **Confirmed working across a real multi-delete JAWS session, July 29 2026** — "2 Regions" and correct button behavior held through 5 real deletions in a row | Verified — no `<a href>` remains anywhere except the skip link; buttons render and are keyboard-operable |
| Delete-with-confirmation, repeated in one session | **Confirmed — Dean deleted 5 recordings in a row via JAWS; all persisted correctly, counts updated correctly each time** | Verified — see disposable-copy testing above |
| Status message lands at the relevant classification group after delete, not the top of the page | **New this round, not yet retested** — fixes a real problem Dean reported: focus returning to the top forced re-navigating past every earlier category each time | Verified — deleted a real recording, confirmed the message renders directly under the correct group's heading, not at the top |
| All 5 classification groups always render, even at zero, instead of disappearing when emptied | **New this round, not yet retested** | Verified — emptied a group, confirmed it still shows "(0)" and a "no recordings" line |
| Missing-Flask error message and exit code | Not yet verified | Verified |
| Duplicate-instance detection | Not yet verified | Verified |
| Waits for real server readiness before opening browser | Confirmed — server started and Chrome opened correctly | Verified |
| `launch.py` / the .bat double-click experience end to end on Windows | **Confirmed working July 28; broke again July 29 after being moved to repo root; fixed, not yet retested** | Not testable (no Windows, no browser/display in this sandbox) — path resolution logic re-simulated and confirmed correct from the repo root |

### What went wrong the first time, and what changed

Dean ran `Launch VoiceOfOpenDoor.bat` on Windows 11. A Command Prompt window opened briefly and closed; the app never opened in Chrome. The original `.bat` only ran `python launch.py` with no error handling — any failure (missing Python, missing Flask, an import error) would print to a console window that closed immediately, so the actual error was never visible.

**Second break, July 29, 2026:** after the fix above, Dean moved `Launch VoiceOfOpenDoor.bat` to the repository root for discoverability. Since the `.bat` does `cd /d "%~dp0"` (change to its own folder) and then ran `py launch.py`, moving the `.bat` without moving `launch.py` broke the relative path — Windows reported `can't open file '...\VoiceOfOpenDoor\launch.py': [Errno 2] No such file or directory`. Fixed by keeping `launch.py` in `App/` (where it already correctly resolves its own backend path regardless of caller location) and updating the root-level `.bat` to call `App\launch.py` explicitly. `Setup.bat` was moved and fixed the same way for consistency, and the now-redundant copies inside `App/` were deleted rather than left alongside the root ones.

Fixed:
- The `.bat` now checks for a Python interpreter itself (`py` first, then `python`) before doing anything else, and prints a clear message plus `pause`s if neither is found.
- The `.bat` checks `launch.py`'s exit code and `pause`s on any non-zero result, so the window stays open and the error is readable.
- `launch.py` checks Flask is importable before doing anything else, and prints the exact `pip install` command to fix it if not.
- `launch.py` checks whether the app is already running (a real socket connection to port 5000) before starting a new server, so double-clicking twice doesn't start a duplicate server or open two browser tabs.
- `launch.py` waits for the server to actually respond (polling the real port) before opening the browser, instead of a fixed sleep.
- Added `Setup.bat` and `requirements.txt` so dependencies install in one step instead of being discovered one at a time.

None of this has been re-tested on Windows yet — only the underlying Python logic, in the sandbox (see table above).

## Run It

**Windows (day-to-day use), from the repository root (`VoiceOfOpenDoor/`):**
1. Double-click `Setup.bat` once (installs Flask).
2. Double-click `Launch VoiceOfOpenDoor.bat` to run the app.

**Development** (keeps the debug reloader):
```
pip install flask
cd App/backend
python app.py
```

## Do Not Continue Building Until

Per Dean's direction (July 28, 2026): no new screens until the launcher works reliably on Windows and Home/Recordings have been tested with JAWS. The fixes above address the specific failure reported, but need to be confirmed on the actual machine before anything else gets built on top of this.

## Data Flow

```
Tools/Audio Processing/analyze.py  -->  analyze report (JSON)
                                              |
Tools/Dataset Utilities/build_manifest.py    |  (merges with the existing
                                              v   manifest if one exists -
Dataset/Metadata/recordings.json  <----------    preserves any classification/
        ^  |                                     notes changes made through
        |  v                                     the app; only re-seeds from
        |  App/backend/app.py  -->  Home, Recordings, detail, 6 stub screens   Documentation/Recording
        |                                                                      Assessment v1/v2 for a
        +---- classification/notes changes, and deletes, write back here ------ recording not already
                                                                                 in the manifest
```

## Next Steps

Per the corrected sequence in `Documentation/Development and Testing Roadmap.md`: close out Phase 1 formally, then build Analyze, then - only then - transcript work. Not straight to Transcripts.

1. Confirm Add Recordings, the focus-after-delete fix, and the Home graphic all work correctly with JAWS - the remaining open items against the Phase 1 Completion Gate.
2. Once Phase 1 is formally closed: build Phase 2, Audio Analysis - replace the Analyze placeholder with a working workflow (select a recording, run the existing analyzer, review results, re-run as needed).
3. Only after Analyze is built and tested: Phase 3, the transcript data model and engine preparation, then Phase 4, the transcript review prototype. This is where local transcription becomes a UI, not a bare CLI tool - see `Documentation/Transcript Editing Design Principles.md` for the interaction design it's governed by.

