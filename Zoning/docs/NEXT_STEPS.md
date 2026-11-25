# Next steps: zoning edits

What's left for Mason to do, with Claude Code in this repo. Work top to bottom. Last updated 2026-11-24.

State on 2026-11-24: E01, E03, and E04, every table fix from the 2026-11-20 package, F35, and F36 were made in `SDE.mtb-edits` and posted into Alyssa's `Misc edits Nov 2026`. The district shape fixes (F26 to F29, F34) were written in `mtb-edits` later that day and posted into Alyssa's version too. Nothing is in DEFAULT yet. Details are in [EDIT_REQUESTS.md](EDIT_REQUESTS.md).

## Now

1. ~~Decide what this public repo should show.~~ Decided 2026-11-24: leave it as is. `trpa-agency/Planning` is public, and the `Zoning` docs and config name the server connection folder, version owners, and staff. They hold no credentials, and none ever go in the repo.
2. ~~Reconcile and post `mtb-edits` into `Misc edits Nov 2026`.~~ Done 2026-11-24. A snapshot of Alyssa's version at 00:31 shows 283 districts, 11,034 use rows, and 486 special designation rows, matching `mtb-edits`, with no null keys and no duplicate district IDs. Optional full check: snapshot `mtb-edits` again and compare it with the 00:31 snapshot; there should be no differences. Original instructions: reconcile `mtb-edits` into `Misc edits Nov 2026` in Pro. Use the Versioning tab: reconcile by attribute, in favor of the target version, aborting on conflicts the first time. Then post.
3. **Verify the post.** Make `Vector_misc.sde` pointing at Alyssa's version and a `config.server.yaml` that uses it, then snapshot both versions and compare. Ask Claude: "verify the reconcile". The compare should show no differences beyond anything Alyssa edited after Nov. 23.
4. **Send Alyssa the review note:** [REVIEW_2026-11-24.md](REVIEW_2026-11-24.md). It now covers the district shape fixes too.

## When Alyssa answers

5. **045 Incline Village Commercial (E02).** Either a density change on WCTAP_045 (15 to 25 units per acre) or a real split with a boundary she names. Ask Claude to build the package from her answer, check the Washoe code Article 220 entry first, and post it like E01.
6. **Her two small checks:** the PLAN_TYPE on the Carson City special designations, and the "units per State Park Lands" unit on East Shore employee housing. Ask Claude to reverse either one if she disagrees.

## After Alyssa posts to DEFAULT

7. **Run the parcel ETL** so `SDE.Parcel_Master` (also published as LocalPlan/MapServer/0) picks up the WCTAP_ IDs.
8. **Snapshot DEFAULT and confirm.** Ask Claude: "snapshot DEFAULT and compare with mtb-edits". Then check that every Washoe parcel's ZONING_ID has a matching District and use rows.
9. **Retest the apps** that join parcel zoning to the use table: LongRange `district-explorer.html` and `parcel-lookup.html`, and Permitting `zoning-lookup.html` and the parcel viewers. A quick scan found no hardcoded zoning IDs, but check the Washoe lookups in a browser.
10. **Delete the `mtb-edits` version** once DEFAULT is confirmed.

## Remaining fixes

11. ~~District shapes.~~ Done 2026-11-24: written in `mtb-edits` at 11:04 (4 shapes, ACRES on 83 districts), confirmed by a rerun, reconciled, and posted into `Misc edits Nov 2026`. Original notes: built 2026-11-24; no zip needed. It computes F26 to F29 from the version's current shapes and recalculates ACRES (F34). Its shapes match the 2026-11-20 replacement shapes exactly. F25 is dropped because Esri Check Geometry finds nothing wrong with those shapes. Steps:
    1. Dry run: `python Zoning/scripts/fix_district_geometry.py`. Expect F26 -6.4386, F27 -0.5213, F28 -0.0117, and F29 +1.0451 acres, and F34 on about 81 districts.
    2. Open `Zoning/outputs/geometry_<time>/proposed.gdb` in Pro and look at the new shapes, removed overlaps, and hole fill.
    3. Write: set `write_to_db: true`, rerun, and restore the config.
    4. Snapshot, then reconcile and post into Alyssa's version again.
12. **Open planner decisions** R01 to R17. Added to the review note for Alyssa on 2026-11-24, with suggested answers where we have one. They are (in `CLAUDE.md` section 8, and in `fix_package/csv/pending_rulings.csv` and `area_pending_rulings.csv`). R18 is settled by the 055 and 056 split. Each answer becomes a small package.
13. **South Shore Area Plan** (179 rows) needs Douglas County Code Chapter 20.703. **PCAP_REC_HOMEWOOD** needs the Homewood Mountain Resort Master Plan. Get the documents; Claude parses and compares them.

## CNEL table (replaces AGIS_TRPA/MapServer/82)

State on 2026-11-24: the reference CSV (283 districts), `cnel_build_table.py`, and the GeoPackage (`data/cnel/district_cnel.gpkg`, with district values, highway centerlines, noise corridors, and the legacy layer) are on `mtb-edits` (last commit 6dab2da, not pushed). Nothing has run in SDE. Details are in [CNEL.md](CNEL.md).

1. **Push `mtb-edits` and merge to `main`** so the server clone can pull the CNEL scripts.
2. **Build `SDE.District_CNEL`** on the server, in `mtb-edits` (the E04 IDs are already there). First do a dry run, then review `changes.csv` and `cnel_review.gdb` against layer 82. Then write with `write_to_db: true` and `create_table: true`, restore the config afterward, and snapshot the version.
3. **Send Alyssa the CNEL questions** with the R-series list: N01 to N08 from CNEL.md. N01 (25 versus 45 CNEL for wilderness) and N03 (Tahoe Valley table versus policy) matter most. Add three corridor questions:
   - Is 300 feet from the centerline the right corridor width where a plan gives none?
   - Should the 2,026 acres with no corridor standard (1,117 of them in Placer) use the district value, or a basin default for each route?
   - What shape is the "airport corridor" in PAS 117 and 120 and the "approved flight paths" in PAS 100?
4. **Get the airport noise contours.**
   - Ask ESA (project 161008, through Jeanne) or the airport for the 2019 ALUCP CNEL contour GIS.
   - The 1987 CLUP shapefile holds safety zones, and the ALUCP report has the contours only as Figure 1-2, so neither one works.
   - Once we have the data, ask Claude to add an `airport_corridor` layer: the 60 CNEL contour split by PAS 100, 117, and 120, with a config entry for the source. Don't trace the figure unless the data can't be had.
5. **Decide where the corridors live.** `noise_corridors` is only in the GeoPackage now. Choose whether it becomes an SDE feature class next to `District_CNEL` or stays a derived file rebuilt by `cnel_export_gpkg.py`.
6. **Rebuild the GeoPackage from the version** after Alyssa posts to DEFAULT. Run `python Zoning/scripts/cnel_export_gpkg.py --source version` so it picks up the Carson City halves of 055 and 056 and the post-E04 IDs without the service workaround.
7. **Republish layer 82** as District joined to `District_CNEL`, plus the corridors if they go to SDE. Before replacing it, find what uses `AGIS_TRPA/MapServer/82` (web maps, apps, and the noise threshold work) and tell the owners about the 33 value changes.
8. **Send Andy the summary message** with the GitHub links to CNEL.md, the GeoPackage, the CSV, and the commit. It's drafted but not sent.

## Pipeline work (from CLAUDE.md section 11)

14. **Rebuild the QA as a maintained pipeline:** extract, parse, compare, and fixes, with the prototype outputs in `tests/fixtures/` as regression tests. Start with the extract and the Plan Area Statement parser.
15. **New checks:** area plan and community plan densities (not checked yet; WCTAP_045 is a live example), Special Designation content against the documents, and whether each File_URL is the current adopted plan.
16. **Rerun the full QA** against DEFAULT after everything above is posted. The expected result is no mismatches beyond the known artifacts and open decisions.
