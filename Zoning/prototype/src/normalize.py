"""Map Plan Area Statement use phrases to the Permissible Use table's Use_Type vocabulary."""
import re
def key(s):
    s=s.lower().replace('- ','-').replace('trans-mission','transmission').replace('non-','non').replace('non ','non').replace('&',' and ').replace('–','-')
    s=re.sub(r'[^a-z ]',' ',s)
    w=[x[:-1] if len(x)>3 and x.endswith('s') and not x.endswith('ss') else x for x in s.split()]
    return ' '.join(w)
# phrase -> one or more canonical service Use_Type values
EXPAND={
 'participant sport facilitie rural sport':['Participant Sports Facilities','Rural Sports'],
 'structural and nonstructural fish wildlife habitat management':['Structural Fish Habitat Management','Nonstructural Fish Habitat Management','Structural Wildlife Habitat Management','Nonstructural Wildlife Habitat Management'],
 'sensitive and uncommon plant management':['Sensitive Plant Management','Uncommon Plant Community Management'],
 'rural sport and group facilitie':['Rural Sports','Group Facilities'],
 'single family dwelling a and summer home':['Single Family Dwelling','Summer Home'],
}
ALIAS={
 'range pasture management':'Ranch Pasture Management','snow mobile course':'Snowmobile Courses','hiking and riding trail':'Riding and Hiking Trails',
 'participant facilitie sport':'Participant Sports Facilities','participant sport and facilitie':'Participant Sports Facilities','beach launching facilitie':'Boat Launching Facilities',
 'selection':'Selection Cut','animal husbandry':'Animal Husbandry Services','local public health safety facilitie':'Local Public Health and Safety Facilities',
 'hotel motel and other transient dwelling':'Hotel, Motel, and Other Transient Dwelling Units','recreation center':'Recreation Centers',
 'transportation with the understanding that thi could be required a part of the preparation of an ea or ei on the drainage project route':'Transportation Routes',
 'fuel treatment management':'Fuels Treatment Management','fuel treatment':'Fuels Treatment Management','fuel treatment management':'Fuels Treatment Management',
 'early successional stage vegetation management':'Early Successional Vegetation Management','early successional stage management':'Early Successional Vegetation Management',
 'sez restoration':'Stream Environmental Zone (SEZ) Restoration','stream environment zone restoration':'Stream Environmental Zone (SEZ) Restoration',
 'run off control':'Runoff Control','cross country skiing course':'Cross Country Ski Courses','cemeterie':'Cemetery',
 'church':'Religious Assembly','churche':'Religious Assembly','local post office':'Local Post Office','local post':'Local Post Office',
 'transit station':'Transit Stations and Terminals','transit station and terminal':'Transit Stations and Terminals',
 'pipeline and power transmission line':'Pipelines and Power Transmission','pipeline and power transmission':'Pipelines and Power Transmission',
 'public health and safety facilitie':'Local Public Health and Safety Facilities','local public and health safety facilitie':'Local Public Health and Safety Facilities',
 'local public safety facilitie':'Local Public Health and Safety Facilities','public safety facilitie':'Local Public Health and Safety Facilities',
 'regional public health and safety':'Regional Public Health and Safety Facilities',
 'utility center':'Public Utility Centers','participant sport':'Participant Sports Facilities','recreation participant sport facilitie':'Participant Sports Facilities',
 'day care center pre school':'Day Care Centers/Pre-Schools','day care center pre school':'Day Care Centers/Pre-Schools','day care center':'Day Care Centers/Pre-Schools',
 'multiple family dwelling':'Multiple Family Dwelling','multi family dwelling':'Multiple Family Dwelling','multi family dwelling senior citizen housing only':'Multiple Family Dwelling',
 'multi person dwelling':'Multi-Person Dwelling','mobile home dwelling':'Mobile Home Dwelling','summer home':'Summer Home','resident care':'Residential Care',
 'hotel motel and other transient dwelling unit':'Hotel, Motel, and Other Transient Dwelling Units','hotel motel and other transient unit':'Hotel, Motel, and Other Transient Dwelling Units',
 'hotel motel and other transient dwelling unit accommodation':'Hotel, Motel, and Other Transient Dwelling Units',
 'timeshare residential design':'Time Sharing (Residential Design)','timesharing residential design':'Time Sharing (Residential Design)',
 'timeshare hotel motel design':'Time Sharing (Hotel/Motel Design)','timeshare motel hotel design':'Time Sharing (Hotel/Motel Design)',
 'visitor information center':'Visitor Information Centers','visitor center':'Visitor Information Centers',
 'developed campground':'Developed Campgrounds','undeveloped campground':'Undeveloped Campgrounds',
 'recreation vehicle park':'Recreational Vehicle Parks','recreational vehicle park':'Recreational Vehicle Parks',
 'skiing facilitie':'Downhill Ski Facilities','rural sport facilitie':'Rural Sports','riding and hiking':'Riding and Hiking Trails',
 'publicly owned assembly and entertainment facilitie':'Publicly Owned Assembly and Entertainment','publicly owned assemble and entertainment':'Publicly Owned Assembly and Entertainment',
 'public assembly and entertainment facilitie':'Publicly Owned Assembly and Entertainment','public assembly and entertainment':'Publicly Owned Assembly and Entertainment',
 'local public assembly and entertainment facilitie':'Local Assembly and Entertainment',
 'food and beverage retail store':'Food and Beverage Retail Sales','amusement and recreation service':'Amusements and Recreation Services','amusement and recreational service':'Amusements and Recreation Services',
 'outdoor amusement':'Outdoor Amusements','range improvement':'Range Improvement','farm and ranch accessory structure':'Farm/Ranch Accessory Structures',
 'fire direction and suppression':'Fire Detection and Suppression','prescribed fire management':'Prescribed Fire/Burning Management',
 'timber stand management':'Timber Stand Improvement','school kindergarten through secondary':'Schools - Kindergarten Through Secondary',
 'school pre school':'Schools - Pre-Schools','school college':'Schools - College','school business and vocational':'Schools - Business and Vocational',
 'social service organization':'Social Service Organizations','marina':'Marinas','general merchandise store':'General Merchandise Stores',
 'special cut':'Special Cut','laundrie and dry cleaning plant':'Laundries and Dry Cleaning Plant','auto mobile home and vehicle dealer':'Auto, Mobile Home and Vehicle Dealers',
}
STRIP=r'^(management|recreation|and|a\.?\s*retail|b\.?\s*entertainment|c\.?\s*services|a\.?\s*general|b\.?\s*linear public facilities)\s+'
def canon(raw, vocab_by_key):
    s=raw.lower().strip()
    if s.startswith('transportation') and s.endswith('routes'): return ['Transportation Routes']
    s=re.sub(r'\(\s*[a-z]\s*§?\s*\)','',s) if 'summer' not in s else s
    for _ in range(2): s=re.sub(STRIP,'',s)
    s=re.sub(r'^[a-c]\.\s*','',s)
    k0=key(raw)
    if k0 in ALIAS: return [ALIAS[k0]]
    if k0 in vocab_by_key: return [vocab_by_key[k0]]
    k=key(s)
    if k in EXPAND: return EXPAND[k]
    if k in ALIAS: return [ALIAS[k]]
    if k in vocab_by_key: return [vocab_by_key[k]]
    return [None]
