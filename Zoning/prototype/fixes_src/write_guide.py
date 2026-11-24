"""Generate docs/EDIT_GUIDE.md and docs/SQL_BY_GLOBALID.md from the fix tables so the guide always matches the data."""
import json, pandas as pd
rd=lambda f: pd.read_csv('outputs/'+f,dtype=str,keep_default_na=False)
up=rd('pu_updates.csv'); de=rd('pu_deletes.csv'); ins=rd('pu_inserts.csv'); sd=rd('sd_deletes.csv')
rep=rd('district_repair_geometry.csv'); cl=rd('district_clip_and_fill_polygons.csv'); rp=rd('district_replacement_shapes.csv')
pu=rd('parcel_updates.csv'); pend=rd('pending_rulings.csv'); split=rd('pending_split_parcels.csv')
aup=rd('area_pu_updates.csv'); ade=rd('area_pu_deletes.csv'); ains=rd('area_pu_inserts.csv'); apend=rd('area_pending_rulings.csv')
D=pd.DataFrame(json.load(open('data/raw/district_attr.json'))).set_index('ZONING_ID')
GDB='Zoning_QA_Fixes_2026-11-20.gdb'
L=[]; G=['# SQL selections by GlobalID','','Use these only if the OBJECTID check in Part 0 fails. Each block selects the same rows as the matching step in EDIT_GUIDE.md.','']
w=L.append
def sql_oid(ids): return f"OBJECTID IN ({', '.join(ids)})"
def sql_gid(gids): return "GlobalID IN (" + ", ".join(f"'{g}'" for g in gids) + ")"
def val_expr(field,v):
    if field=='Density': return 'None' if v=='' else v
    return 'None' if v=='' else f'"{v}"'
step=[0]
def S(title):
    step[0]+=1; w(f'\n### Step {step[0]}. {title}\n'); return step[0]

w('# Zoning QA fixes: ArcGIS Pro editing guide')
w('')
w('Prepared November 20, 2026. Edits are based on the live Zoning MapServer as of that date and on the plan documents linked in LocalPlan layer 1: 94 Plan Area Statements, five of the six area plans, and all three community plans. The South Shore Area Plan could not be checked because its use table lives in Douglas County Development Code Chapter 20.703, which is not linked (decision R15).')
w('')
w('Each step names its fix ID (F01 and so on), how many rows or features it changes, and how sure we are. Certain means the PDF text or the table itself proves it. Likely means strong evidence that a planner should glance at before posting. Decisions (R01 to R10) are listed at the end and are not edits.')
w('')
w('## What is in this package')
w('')
w('| Item | Use |')
w('|---|---|')
w(f'| `data/{GDB}` | Every fix as a table or feature class, in NAD 1983 UTM Zone 10N (the District feature class projection) |')
w('| `data/csv/` | The same fixes as CSV files, for review in Excel |')
w('| `docs/EDIT_GUIDE.md` | This guide |')
w('| `docs/SQL_BY_GLOBALID.md` | Backup selection queries keyed on GlobalID |')
w('| `docs/METHODS.md` | How the fixes were found and checked |')
w('| `scripts/replace_district_shapes.py` | Optional Python window snippet for Part 3, Method B |')
w('| `src/` | The Python that built the fixes, for rerunning or auditing |')
w('')
w('## Summary of edits')
w('')
w('| Part | Layer | Edits | Rows after |')
w('|---|---|---|---|')
w(f'| 1 | PermissibleUses, Plan Area Statements | {up.OBJECTID.nunique()} rows updated ({len(up)} field changes), {len(de)} deleted, {len(ins)} added | 10,805 (from 10,812) |')
w(f'| 1B | PermissibleUses, area and community plans | {len(aup)} rows updated, {len(ade)} deleted, {len(ains)} added | 10,963 |')
w(f'| 2 | Special_Designation | {len(sd)} duplicates deleted | 482 (from 515) |')
w(f'| 3 | District | {len(rep)} repaired, 3 clipped, 1 gap filled, ACRES recalculated | 281 (unchanged) |')
w(f'| 4 | Parcel | {pu.APN.nunique()} parcels updated ({len(pu)} field changes) | 61,275 (unchanged) |')
w('')
w('## Part 0. Before you start')
S('Connect and add the layers')
w('In a new map in ArcGIS Pro, add these from the SDE connection: District, Parcel, the PermissibleUses table, and the Special_Designation table. Then add every layer and table from `'+GDB+'` (Catalog pane, browse to the folder, drag the geodatabase items into the map).')
S('Work in a version, or back up first')
w('If the zoning data is versioned, create and switch to a named version such as `zoning_qa_fixes_2026_11_20` (Data tab on any of the four layers, Versioning). If it is not versioned, export all four to a backup file geodatabase first with Export Features and Export Table. Either way you can undo the whole set.')
S('Confirm row counts and IDs match this package')
w('Open each attribute table and check the record count: District 281, PermissibleUses 10,812, Special_Designation 515, Parcel 61,275. Then run Select By Attributes on PermissibleUses with this clause:')
w('```sql\nOBJECTID = 3789\n```')
w('It should select one row: Zoning_ID 057, Use_Type Selection Cut, Use_Status Allowed. If it does not, the SDE OBJECTIDs differ from the published service. Use the GlobalID queries in `SQL_BY_GLOBALID.md` for every selection below instead.')
S('Start editing')
w('On the Edit tab, confirm editing is enabled for the SDE workspace. Save edits after each part (Edit tab, Save). If a selection count does not match the guide, stop and check before calculating.')

# -------- Part 1
w('\n## Part 1. PermissibleUses table\n')
w('For each step: open the PermissibleUses table, click Select By Attributes, switch to SQL mode, paste the clause, apply, and check the selection count. Then right-click the field header, choose Calculate Field, set the expression type to Python 3, paste the expression, and run it. Calculate Field only changes the selected rows.')
for fix in up.FIX_ID.unique():
    f=up[up.FIX_ID==fix]
    sig=f.groupby('OBJECTID',sort=False).apply(lambda x: tuple(zip(x.FIELD,x.NEW_VALUE)))
    for s_,oids in sig.groupby(sig,sort=False):
        g=f[f.OBJECTID.isin(oids.index)]; n=len(oids); zs=', '.join(sorted(set(g.Zoning_ID))); conf=g.CONFIDENCE.iloc[0]
        what=' and '.join(f'{fl} to {v if v else "null"}' for fl,v in s_)
        k=S(f'{fix}: set {what} ({n} row{"s" if n>1 else ""})')
        if n<=6: w(f'Districts: {zs}. ' + ' '.join(x.rstrip('.')+'.' for x in dict.fromkeys(g.REASON)) + f' Source: {"; ".join(sorted(set(g.SOURCE)))}. Confidence: {conf}.')
        else: w(f'{n} rows in {g.Zoning_ID.nunique()} districts. {g.REASON.iloc[0].rstrip(".")}. Confidence: {conf}. The full list is in `F01_F23_PermissibleUse_Updates`.')
        w(f'\nSelect (expect {n}):\n```sql\n{sql_oid(list(oids.index))}\n```')
        for fl,v in s_: w(f'Calculate Field, field `{fl}`:\n```python\n{val_expr(fl,v)}\n```')
        G.append(f'**Step {k} ({fix})**\n```sql\n{sql_gid(list(dict.fromkeys(g.GlobalID)))}\n```')
k=S(f'Delete {len(de)} rows (F12, F13, F14, F20, F21, F22)')
w('These rows are either not in the PDF or are exact duplicates, an all-null row, and the second copy of the "45" row. Reasons per row are in `F12_F22_PermissibleUse_Deletes`.\n')
w('| Fix | OBJECTID | Zoning_ID | Use_Type | Confidence |\n|---|---|---|---|---|')
for r in de.itertuples(): w(f'| {r.FIX_ID} | {r.OBJECTID} | {r.Zoning_ID} | {r.Use_Type} | {r.CONFIDENCE} |')
w(f'\nSelect (expect {len(de)}):\n```sql\n{sql_oid(de.OBJECTID)}\n```')
w('With the rows selected, on the Edit tab click Delete. Record count should drop to 10,795.')
G.append(f'**Step {k} (deletes)**\n```sql\n{sql_gid(de.GlobalID)}\n```')
k=S(f'Add {len(ins)} rows (F15 to F19)')
w('Open the Append tool (Analysis tab, Tools, search Append).\n')
w('- Input Datasets: `F15_F19_PermissibleUse_Inserts` from the fixes geodatabase')
w('- Target Dataset: the SDE PermissibleUses table')
w('- Field Matching Type: Use the field map to reconcile field differences')
w('- Field Map: Zoning_ID, Category, Subcategory, Use_Type, Use_Status, Density, Unit, and Notes map by name. Leave Zoning_Description, Plan_Name, and Plan_Type empty, as every existing row has them empty. FIX_ID, CONFIDENCE, SOURCE, and REASON have no target and are dropped.\n')
w('Rows being added:\n\n| Fix | Zoning_ID | Category | Subcategory | Use_Type | Use_Status | Density | Unit |\n|---|---|---|---|---|---|---|---|')
for r in ins.itertuples(): w(f'| {r.FIX_ID} | {r.Zoning_ID} | {r.Category} | {r.Subcategory} | {r.Use_Type} | {r.Use_Status} | {r.Density or ""} | {r.Unit} |')
w('\nRecord count should be 10,805. Notes is "NA" on the new rows except the two timeshare rows, which carry the same note as the existing 103 timeshare rows. Save edits.')

# -------- Part 1B
w('\n## Part 1B. PermissibleUses table: area plans and community plans\n')
w('Do Part 1 first. These steps use the same Select By Attributes and Calculate Field pattern. Sources are the Washoe County Development Code Article 220 (Dec 17, 2025), the Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), the Meyers Area Plan (March 2018), the Tahoe Valley Area Plan (amended Dec 18, 2024), the Tourist Core Area Plan (Dec 2024), and the Round Hill (1993), Bijou/Al Tahoe (1995), and South Y Industrial Tract (2003) community plans. Page numbers for every row are in the A tables in the geodatabase.')
for new,g_ in aup.groupby('NEW_VALUE',sort=False):
    n=len(g_)
    k=S(f'A01: set Use_Status to {new} ({n} row{"s" if n>1 else ""})')
    w('| OBJECTID | Zoning_ID | Use_Type | Now | Source |\n|---|---|---|---|---|')
    for r in g_.itertuples(): w(f'| {r.OBJECTID} | {r.Zoning_ID} | {r.Use_Type} | {r.OLD_VALUE or "null"} | {r.SOURCE} |')
    w(f'\nSelect (expect {n}):\n```sql\n{sql_oid(g_.OBJECTID)}\n```')
    w(f'Calculate Field, field `Use_Status`:\n```python\n"{new}"\n```')
    G.append(f'**Step {k} (A01, {new})**\n```sql\n{sql_gid(g_.GlobalID)}\n```')
a2=ade[ade.FIX_ID=='A02']
k=S(f'A02: delete {len(a2)} rows the documents do not support')
w('| OBJECTID | Zoning_ID | Use_Type | Reason |\n|---|---|---|---|')
for r in a2.itertuples(): w(f'| {r.OBJECTID} | {r.Zoning_ID} | {r.Use_Type} | {r.REASON} |')
w(f'\nSelect (expect {len(a2)}):\n```sql\n{sql_oid(a2.OBJECTID)}\n```\nDelete, then save.')
G.append(f'**Step {k} (A02)**\n```sql\n{sql_gid(a2.GlobalID)}\n```')
a5=ade[ade.FIX_ID=='A05']; zl=sorted(set(a5.Zoning_ID)-{''})
k=S(f'A05: delete all Tahoe Valley and Tourist Core rows, plus the orphan rows ({len(a5)} rows)')
w('Both plans were rewritten in December 2024 with consolidated use categories (for example "Forest and Timber Resource Management" covers reforestation, thinning, and the other timber uses). The service mixes the new names with the old Code names and has status errors, so the cleanest fix is to replace every row for these 17 districts from the 2024 tables (step A06). The 32 rows with no Zoning_ID are Tahoe Valley and Tourist Core template rows and go too. Confidence: Certain for the 17 districts, Likely for the orphans. Confirm decision R14 first.\n')
w(f'Select (expect {len(a5)}):\n```sql\nZoning_ID IN ({", ".join(chr(39)+z+chr(39) for z in zl)}) OR Zoning_ID IS NULL\n```\nDelete, then save. Record count should be {10805-len(a2)-len(a5):,}.')
G.append(f'**Step {k} (A05)**\n```sql\nZoning_ID IN ({", ".join(chr(39)+z+chr(39) for z in zl)}) OR Zoning_ID IS NULL\n```')
k=S(f'A03, A04, and A06: add {len(ains)} rows')
c=ains.FIX_ID.value_counts()
w(f'- A03 ({c.get("A03",0)} rows): uses the documents list that the service is missing, across Washoe, Placer, Meyers, and the community plans.')
w(f'- A04 ({c.get("A04",0)} rows): full use lists for four Washoe districts that have no rows at all: 032B Crystal Bay Tourist, 035_SA1 Crystal Bay Condominiums Special Area, 055 East Shore, and 056 Marlette Lake (see decision R18 for 055 and 056).')
w(f'- A06 ({c.get("A06",0)} rows): the complete 2024 Tahoe Valley and Tourist Core tables. Density, Unit, and Notes carry over from the old row where the same use existed; footnote text from the tables is added to Notes. TCAP_TSC_MUC_SA1 excludes the uses footnote 9 says are not permitted there.\n')
w('Run Append with Input Datasets `A03_A06_PermissibleUse_Inserts`, Target Dataset the SDE PermissibleUses table, and Field Matching Type "Use the field map". Map Zoning_ID, Category, Subcategory, Use_Type, Use_Status, Density, Unit, and Notes by name; leave the rest unmapped.')
w(f'\nRecord count should be 10,963. Save edits.')
# -------- Part 2
w('\n## Part 2. Special_Designation table\n')
k=S(f'F24: delete {len(sd)} duplicate rows')
w(f'Every one is a second copy of a Transfer of Development Rights receiving area (multi-family residential units) row for the same district with the same notes. The lower OBJECTID copy is kept. Confidence: Certain.\n')
w(f'Select (expect {len(sd)}):\n```sql\n{sql_oid(sd.OBJECTID)}\n```')
w('Delete, then check the record count is 482. Save edits.')
G.append(f'**Step {k} (F24)**\n```sql\n{sql_gid(sd.GlobalID)}\n```')

# -------- Part 3
w('\n## Part 3. District feature class\n')
k=S('F25: repair three self-touching polygons')
w('Shapely flags these as ring self-intersections. The repair changes area by zero square meters. Esri validation sometimes allows self-touching rings, so check first.\n')
w('| OBJECTID | ZONING_ID |\n|---|---|')
for r in rep.itertuples(): w(f'| {r.OBJECTID} | {r.ZONING_ID} |')
w(f'\nSelect (expect 3) on District:\n```sql\n{sql_oid(rep.OBJECTID)}\n```')
w('Run Check Geometry (Esri validation method) on the District layer. If it reports problems for these features, run Repair Geometry on the District layer with the selection active, Validation Method Esri, and Delete Features with Null Geometry unchecked. If Check Geometry reports nothing, skip the repair.')
G.append(f'**Step {k} (F25)**\n```sql\n{sql_gid(rep.GlobalID)}\n```')
w('\nThe next three steps remove district overlaps. Method A uses the Clip edit tool and the clip polygons in `F26_F29_District_ClipAndFill`. Method B swaps in the finished shapes from `F26_F29_District_ReplacementShapes` with a short Python script. Use one method, not both.')
for r in cl[cl.FIX_ID.isin(['F26','F27','F28'])].itertuples():
    lose=D.loc[r.CLIP_FROM_ZONING_ID]
    k=S(f'{r.FIX_ID}: clip {r.CLIP_FROM_ZONING_ID} where it overlaps {r.KEEP_ZONING_ID} ({r.ACRES} acres)')
    w(f'{r.REASON}. Confidence: {r.CONFIDENCE}.\n')
    w(f'1. In the District layer, select only {r.CLIP_FROM_ZONING_ID} (OBJECTID {lose.OBJECTID}):\n```sql\nOBJECTID = {lose.OBJECTID}\n```')
    w(f'2. On the Edit tab, open Modify, then Clip. Choose Discard (remove the area inside the clipping feature) and a buffer distance of 0.')
    w(f'3. Click the {r.FIX_ID} polygon in the `F26_F29_District_ClipAndFill` layer as the clipping feature, then click Clip.')
    w(f'4. Check that {r.CLIP_FROM_ZONING_ID} lost about {r.ACRES} acres and {r.KEEP_ZONING_ID} is unchanged.')
    G.append(f'**Step {k} ({r.FIX_ID})**\n```sql\nGlobalID = \'{lose.GlobalID}\'\n```')
f29=cl[cl.FIX_ID=='F29'].iloc[0]; tg=D.loc['TVAP_TC_G']
k=S(f'F29: fill the {f29.ACRES} acre hole in Tahoe Valley and give it to TVAP_TC_G')
w(f'{f29.REASON}. Confidence: {f29.CONFIDENCE}.\n')
w('1. In the `F26_F29_District_ClipAndFill` layer, select the F29 polygon. On the Edit tab, click Copy.')
w('2. Open the Paste menu, choose Paste Special, and pick the SDE District layer as the target. A new District feature with empty attributes appears.')
w(f'3. Select the new feature and TVAP_TC_G (OBJECTID {tg.OBJECTID}) together. On the Edit tab, open Modify, then Merge.')
w(f'4. In the Merge pane, choose to keep the attributes of OBJECTID {tg.OBJECTID} (TVAP_TC_G) and merge into it. The pasted feature is removed and the District count returns to 281.')
w('\n**Method B for steps F26 to F29.** Instead of Clip and Merge, open the Python window in Pro with editing started and run `scripts/replace_district_shapes.py` (instructions are at the top of the file). It replaces the shape of 111_SA2, 030, 114, and TVAP_TC_G by GlobalID with the shapes in `F26_F29_District_ReplacementShapes` and prints the before and after acres.')
k=S('F34: recalculate ACRES for every district')
w('Six districts already had an ACRES value more than 1 percent off their shape (TVAP_TC_G, TVAP_TC_OS, TVAP_TC_C, PCAP_REC_HOMEWOOD, PCAP_RES_CHAMBERS, and 040), and steps F26 to F29 changed four more. The stored values match planar area in UTM Zone 10N for the other 275, so use that method.\n')
w('Clear the selection on District. Run Calculate Geometry Attributes with Input Features District, Field ACRES, Property Area, Area Unit Acres (US survey or international, whichever matches your existing values; they differ by about 4 parts per million), and Coordinate System NAD 1983 UTM Zone 10N. Expected new values for the edited districts:\n')
w('| ZONING_ID | ACRES before | ACRES after |\n|---|---|---|')
for r in rp.itertuples(): w(f'| {r.ZONING_ID} | {float(r.ACRES_OLD):,.2f} | {float(r.ACRES):,.2f} |')
k=S('Check the District edits')
w('Run Check Geometry on District and confirm no new problems. Run Count Overlapping Features on District; any area with a count of 2 or more should be under one square meter. Save edits.')

# -------- Part 4
w('\n## Part 4. Parcel feature class\n')
w('Parcel ZONING_ID is an overlay of the District layer. If your process rebuilds it from District, rerun that process after Part 3 instead of these steps, then spot check the APNs below. Use these steps only if the parcel fields are edited by hand.\n')
w('Separate issue for whoever publishes the service: the Parcel layer in Zoning/MapServer and the Parcels/MapServer layer return null geometry for every feature. LocalPlan/MapServer layer 0 returns geometry normally.')
for fix in pu.FIX_ID.unique():
    f=pu[pu.FIX_ID==fix]
    sig=f.groupby('APN',sort=False).apply(lambda x: tuple(zip(x.FIELD,x.NEW_VALUE)))
    for s_,apns in sig.groupby(sig,sort=False):
        g=f[f.APN.isin(apns.index)]; n=len(apns)
        k=S(f'{fix}: update {n} parcel{"s" if n>1 else ""} to {dict(s_).get("ZONING_ID", "the plan of their district")}')
        w(f'{g.REASON.iloc[0].rstrip(".")}. Confidence: {g.CONFIDENCE.iloc[0]}.\n')
        al=", ".join(f"'{a}'" for a in apns.index)
        w(f'Select on Parcel (expect {n}):\n```sql\nAPN IN ({al})\n```')
        for fl,v in s_: w(f'Calculate Field, field `{fl}`:\n```python\n"{v}"\n```')
w('\nSave edits. If you are in a version, reconcile and post it. Then let the QA owner know so the checks can be rerun against the posted data.')

# -------- Part 5
w('\n## Part 5. Decisions needed before more edits\n')
w('These rows are prepared in `R01_R05_Pending_Rulings`, `R07_Pending_SplitParcels`, and `R06_Review_CoverageGaps` but should not be applied until someone decides.\n')
w('| ID | Item | Question |\n|---|---|---|')
seen=set()
for r in pend.itertuples():
    if r.FIX_ID in seen: continue
    seen.add(r.FIX_ID); n=(pend.FIX_ID==r.FIX_ID).sum()
    item={'R01':'073 Multiple Family Dwelling','R02':'154 and 154_MF','R03':'112 skiing facilities row','R05':'PCAP_MUN_DH special designation'}[r.FIX_ID]
    w(f'| {r.FIX_ID} | {item} | {r.QUESTION} |')
w('| R06 | 26 coverage gaps and slivers | The largest is 4,157 acres at the south end of the Region with no district or plan. A 24 acre gap sits inside the South Shore Area Plan. About 10 acres of district area lies outside the TRPA boundary. Which zoning applies, or is the TRPA boundary layer generalized? |')
w(f'| R07 | {len(split)} split parcels | Each spans two districts and carries the one covering less of it. Confirm the intended zoning. |')
w('| R08 | 154_MF plan ID | The 154_MF parcels carry PLAN_ID 155 (Tahoma Commercial), but the district is 83 percent inside the PAS 154 boundary. Settle with R02. |')
w('| R09 | Tahoe Valley plan ID | District uses PLAN_ID TVAP; the plan layer and 467 parcels use 110. Pick one. |')
for r in apend.drop_duplicates('FIX_ID').itertuples():
    item={'R11':'PCAP_COM/PS_KINGS single family dwelling','R12':'Fish habitat rows in PCAP_MU_R, MU_TOR, MU_WREC','R13':'113 open space line'}.get(r.FIX_ID,r.Zoning_ID)
    w(f'| {r.FIX_ID} | {item} | {r.QUESTION} |')
w('| R10 | PDF problems | 079 lists single family dwelling and 118 lists transportation routes with no (A) or (S). 089B Stateline/Ski Run has no PDF link. |')
open('docs/EDIT_GUIDE.md','w').write('\n'.join(L)+'\n'); open('docs/SQL_BY_GLOBALID.md','w').write('\n\n'.join(G)+'\n')
print('steps',step[0],'| guide lines',len(L))
