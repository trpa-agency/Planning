# Next steps: zoning edits

What's left for Mason to do, with Claude Code in this repo. Work top to bottom. Last updated 2026-11-24.

State on 2026-11-24: all edits are in `SDE.mtb-edits`. Done there: E01, E03, and E04, every table fix from the 2026-11-20 package, F35, and F36. Nothing has been reconciled into Alyssa's version or posted to DEFAULT. Details are in [EDIT_REQUESTS.md](EDIT_REQUESTS.md).

## Now

1. ~~Decide what this public repo should show.~~ Decided 2026-11-24: leave it as is. `trpa-agency/Planning` is public, and the `Zoning` docs and config name the server connection folder, version owners, and staff. They hold no credentials, and none ever go in the repo.
2. **Reconcile and post `mtb-edits` into `Misc edits Nov 2026`** in Pro. Use the Versioning tab: reconcile by attribute, in favor of the target version, aborting on conflicts the first time. Then post.
3. **Verify the post.** Make `Vector_misc.sde` pointing at Alyssa's version and a `config.server.yaml` that uses it, then snapshot both versions and compare. Ask Claude: "verify the reconcile". The compare should show no differences beyond anything Alyssa edited after Nov. 23.
4. **Send Alyssa the review note:** [REVIEW_2026-11-24.md](REVIEW_2026-11-24.md).

## When Alyssa answers

5. **045 Incline Village Commercial (E02).** Either a density change on WCTAP_045 (15 to 25 units per acre) or a real split with a boundary she names. Ask Claude to build the package from her answer, check the Washoe code Article 220 entry first, and post it like E01.
6. **Her two small checks:** the PLAN_TYPE on the Carson City special designations, and the "units per State Park Lands" unit on East Shore employee housing. Ask Claude to reverse either one if she disagrees.

## After Alyssa posts to DEFAULT

7. **Run the parcel ETL** so `SDE.Parcel_Master` (also published as LocalPlan/MapServer/0) picks up the WCTAP_ IDs.
8. **Snapshot DEFAULT and confirm.** Ask Claude: "snapshot DEFAULT and compare with mtb-edits". Then check that every Washoe parcel's ZONING_ID has a matching District and use rows.
9. **Retest the apps** that join parcel zoning to the use table: LongRange `district-explorer.html` and `parcel-lookup.html`, and Permitting `zoning-lookup.html` and the parcel viewers. A quick scan found no hardcoded zoning IDs, but check the Washoe lookups in a browser.
10. **Delete the `mtb-edits` version** once DEFAULT is confirmed.

## Remaining fixes

11. **District shapes (F25 to F29, then F34 acres).** These are three invalid shapes, overlaps at 111_SA2 and TVAP_TC_NP, 030 and 040, and 114 and 114_SA1, and the 1 acre hole in Tahoe Valley. They need `TRPA_Zoning_QA_Fixes_2026-11-20.zip`, which holds the replacement shapes geodatabase. Find it, put it in `Zoning/data/`, and ask Claude to build a geometry posting script with the same guards.
12. **Open planner decisions** R01 to R17 (in `CLAUDE.md` section 8, and in `fix_package/csv/pending_rulings.csv` and `area_pending_rulings.csv`). R18 is settled by the 055 and 056 split. Each answer becomes a small package.
13. **South Shore Area Plan** (179 rows) needs Douglas County Code Chapter 20.703. **PCAP_REC_HOMEWOOD** needs the Homewood Mountain Resort Master Plan. Get the documents; Claude parses and compares them.

## Pipeline work (from CLAUDE.md section 11)

14. **Rebuild the QA as a maintained pipeline:** extract, parse, compare, and fixes, with the prototype outputs in `tests/fixtures/` as regression tests. Start with the extract and the Plan Area Statement parser.
15. **New checks:** area plan and community plan densities (not checked yet; WCTAP_045 is a live example), Special Designation content against the documents, and whether each File_URL is the current adopted plan.
16. **Rerun the full QA** against DEFAULT after everything above is posted. The expected result is no mismatches beyond the known artifacts and open decisions.
