# Zoning edit requests

Edit requests from planning staff, tracked against the 2026-11-20 QA fix package (see `CLAUDE.md` sections 7 and 8). Each request gets an E-series ID. Fix IDs (F, A) and decision IDs (R) keep their meaning from the package.

Live service checks below ran on 2026-11-23 against `Zoning/MapServer`, `Boundaries/MapServer`, and the 2026-11-20 snapshot.

## Requests from Alyssa (Senior Planner), 2026-11-23

| ID | Request | Status |
|---|---|---|
| E01 | Add use lists for 056, WCTAP_056, 055, WCTAP_055, 032B, and 035_SA1 | Mostly built (A04); Carson City lists not built |
| E02 | Split 045 Incline Village Commercial into Town Center and non-Town Center districts | Blocked: no non-Town Center area on the current boundary |
| E03 | Delete Crystal Bay Condominiums OBJECTID 842 without losing the use table for OBJECTID 405 | Method below; needs confirmation of 842's ZONING_ID |
| E04 | Prefix Washoe County zoning IDs with WCTAP | Scoped; run last |

### E01: Use lists for the empty Washoe and Carson City districts

What exists today:

- The service has no Permissible Use rows for 032B, 035_SA1, 055, or 056. [Certain]
- Fix A04 inserts 158 rows from the Washoe County code: 032B (59), 035_SA1 (36), 055 (39), and 056 (24). [Certain]

What Alyssa's list adds:

- She lists a Carson City and a Washoe County version of both 055 and 056. That means splitting each polygon at the Carson City line, which also settles R18 (each is about 42 percent in Carson City). [Likely]
- The Washoe portions become WCTAP_055 and WCTAP_056 and take the A04 rows, rekeyed.
- The Carson City portions keep 055 and 056 and need use lists from the Plan Area Statements. Carson City has no area plan, so the PAS still governs there. [Likely] The PAS PDFs exist at `.../documents/archive/2/055.pdf` and `.../056.pdf`, but the prototype PAS pass did not parse them, because District folds both into WCTAP. Those are new parser runs.

Open points:

- Which line to split on. `Boundaries/MapServer/10` Jurisdictions Combined looks like generalized Census county lines (section 3). Splitting zoning on a generalized line moves real parcels to the wrong side. Prefer the county line from parcel fabric or the official Carson City and Washoe boundary.
- Special Designation has one row each for 055 and 056. Both halves probably need a copy.

### E02: Split 045 into Town Center and non-Town Center

The current service carries Multiple Family Dwelling at 15 units per acre on 045 (Special Use) and 045_SA1 (Allowed). Alyssa wants 25 inside the Town Center and 15 outside.

The problem: on the published Town Center layer (`Boundaries/MapServer/1`, Incline Village Commercial, 207.86 acres), all of 045 is inside the Town Center. [Certain]

| District | Acres | Inside Town Center | Outside |
|---|---|---|---|
| 045 | 133.43 | 133.37 | 0.06 |
| 045_SA1 | 48.27 | 48.27 | 0 |
| 045_SA2 | 2.06 | 2.06 | 0 |
| 045_SA3 | 23.88 | 23.88 | 0 |

The 0.06 acres is a sliver, not a district. The Parcel layer agrees: all 325 parcels in 045 and its special areas carry the Incline Village Commercial Town Center.

Question for Alyssa: which boundary defines "outside the Town Center"? Possibilities are an amended Town Center line from the Washoe area plan, a different district (for example 046 or 047), or a Town Center layer that needs its own update. The split can't be drawn until that's settled. Once it is, the edit is a polygon split, a new ZONING_ID, a copy of the 045 use rows to the new ID, and a density change on one Multiple Family Dwelling row. Density is an Integer field, so 25 and 15 store fine.

### E03: Delete OBJECTID 842 and keep the 405 use table

Why it happens:

- Both relationships from District (to `SDE.PermissibleUses` and `SDE.Special_Designation`) are simple, not composite, and keyed on ZONING_ID. [Certain]
- In a simple relationship, deleting an origin feature sets the foreign key to null on every related row. [Certain] Both Crystal Bay Condominiums features share one ZONING_ID, so deleting either one nulls the key on all of them. The rows are still there, but they belong to no district.
- The 33 Permissible Use rows with a null Zoning_ID in the 2026-11-20 snapshot are probably the same symptom from an earlier delete. [Likely]

OBJECTID 842 isn't in the published service. Only OBJECTID 405 (035, 62.18 acres) is. So 842 exists only in Alyssa's version or in an unpublished state. [Certain] Today 035 has 28 Permissible Use rows and 1 Special Designation row.

Method, in Alyssa's version (scriptable, dry run first):

1. Confirm 842's ZONING_ID and that its geometry adds nothing that 405 lacks.
2. Save the GlobalIDs of every Permissible Use and Special Designation row where the ZONING_ID equals that value.
3. Delete OBJECTID 842.
4. Set ZONING_ID back on those rows, matched by GlobalID.
5. Verify: same row counts as step 2, no new null keys, and the relate from 405 returns the full table.

Another route: change 842's ZONING_ID to a throwaway value before deleting it. Don't use it. If the edit session cascades key changes, the 405 rows would move to the throwaway value. [Guessing]

### E04: Prefix Washoe County zoning IDs with WCTAP

Scope: 38 districts carry PLAN_ID WCTAP (019 through 056, including special areas). The format to confirm is `WCTAP_` plus the current ID, for example `WCTAP_045_SA1`.

ZONING_ID is the join key for everything, so the rename touches more than the District layer:

| Target | How it follows the rename |
|---|---|
| SDE.District | The edit itself |
| SDE.PermissibleUses, SDE.Special_Designation | Simple relationship on ZONING_ID. Update the keys explicitly in the same edit, then verify the counts. Don't count on the relationship cascading the change. |
| Parcel ZONING_ID (Zoning layer 1, LocalPlan layer 0) | Not related. Separate update, or rerun whatever populates it. |
| Fix package | Every WCTAP row in A01 to A04, plus F21's "45" to 045 change, uses the old IDs |
| Web apps | LongRange district explorer and parcel lookup, and the Permitting zoning lookup and parcel viewers, read the Zoning service. No hardcoded zoning IDs turned up in a quick scan. Retest them after the rename. |
| 019 Martis Peak | Folded into WCTAP in District, but the Local Plan layer keeps it as its own PAS. Confirm it should get the prefix. |
| 055 and 056 Carson City halves | Keep their current IDs (E01) |

The rename goes last. Do every edit keyed on the old IDs first, then rename in one pass.

## Recommended order

1. Confirm the SDE versioning model (see below) and set up the edit versions.
2. E03: delete 842 with the key restore.
3. Post the 2026-11-20 fix package, or the parts of it staff accept, on the old IDs.
4. E01: split 055 and 056 at the county line and add the Carson City PAS lists.
5. E02: once the boundary question is settled.
6. E04: the WCTAP rename across District, both tables, and parcels.
7. Rerun the QA against the edited version before reconcile and post.

## Versioning

The service reports `isDataVersioned: true`. The map service doesn't say whether it's traditional or branch versioning. Check in ArcGIS Pro under the dataset's properties.

- Traditional versioning: a child version under Alyssa's version works. Our edits reconcile into hers, and hers into DEFAULT.
- Branch versioning: every named version must be a direct child of DEFAULT. A version under Alyssa's version isn't possible. Edits also have to go through a feature service with version management, not a direct `.sde` connection. Use two sibling versions under DEFAULT, keep the edits apart by request, and reconcile hers first.
