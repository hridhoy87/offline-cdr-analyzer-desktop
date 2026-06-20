"""
Offline Forensic Intelligence Engine for Advanced CDR & Cell Tower Analytics.
Optimized Production Edition - Fully Vectorized & Re-architected for Desktop Suite.
Incorporates Spatial-Temporal Chronological Route Map Computations.
"""
import os
import sys
import json
import time
import pandas as pd
from difflib import SequenceMatcher

# Global cache container for the Type Allocation Code hardware database
TAC_DB = None

def lookup_imei(imei):
    """Resolves manufacturer and device model specifications from the TAC database."""
    global TAC_DB
    if not imei or len(str(imei)) < 8:
        return None
    try:
        if TAC_DB is None:
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.dirname(__file__)
            db_path = os.path.join(base_path, "tac_db.csv")
            if os.path.exists(db_path):
                TAC_DB = pd.read_csv(db_path, dtype=str)
                TAC_DB['TAC'] = TAC_DB['TAC'].str.strip()
            else:
                return None
        
        tac = str(imei)[:8]
        match = TAC_DB[TAC_DB['TAC'] == tac]
        if not match.empty:
            row = match.iloc[0]
            return f"{row['Manufacturer']} {row['Model']}"
    except:
        pass
    return None

def _clean_phone_number(val):
    """Standardizes dialing string markers into a uniform clean 11-digit string profile."""
    val_str = str(val).strip().split('.')[0]
    if val_str.startswith('+88'): 
        val_str = val_str[3:]
    elif val_str.startswith('88'): 
        val_str = val_str[2:]
    val_digits = "".join(c for c in val_str if c.isdigit())
    return val_digits if val_digits not in ['nan', 'None', ''] else ''

def process_cdr_data(file_paths, intended_location, output_dir, start_ts=None, end_ts=None, progress_callback=None):
    """Parses staged CDR worksheets, extracts network patterns, and compiles an intelligence suite."""
    try:
        if not file_paths: 
            return {"status": "error", "message": "No files selected."}
        
        if progress_callback: progress_callback(15, "Ingesting worksheet data arrays...")
        all_dataframes = []
        is_single_file = (len(list(file_paths)) == 1)

        # Step 1: Ingest and validate spreadsheet documents
        for path in file_paths:
            if not os.path.exists(path): 
                continue
            try:
                excel_file = pd.ExcelFile(path, engine="openpyxl")
                df = excel_file.parse(sheet_name=excel_file.sheet_names[0], dtype=str)
                if not df.empty and len(df.columns) >= 12:
                    all_dataframes.append(df)
            except: 
                continue

        if not all_dataframes: 
            return {"status": "error", "message": "No readable data found."}
            
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        combined_df = combined_df.fillna("--Empty--")
        combined_df = combined_df.replace(['nan', 'NaN', 'None', ''], "--Empty--")
        
        if len(combined_df.columns) < 13: 
            return {"status": "error", "message": "Invalid CDR format."}

        # Coordinate column names dynamically based on default structural placements
        col_A, col_B, col_C, col_D, col_E, col_F, col_G, col_H, col_I, col_J, col_K, col_L = (
            combined_df.columns[0], combined_df.columns[1], combined_df.columns[2], 
            combined_df.columns[3], combined_df.columns[4], combined_df.columns[5], 
            combined_df.columns[6], combined_df.columns[7], combined_df.columns[8], 
            combined_df.columns[9], combined_df.columns[10], combined_df.columns[11]
        )

        # Step 2: Temporal bounding mask routines
        if start_ts and end_ts:
            temp_time = pd.to_datetime(combined_df[col_A], errors='coerce')
            mask = (temp_time >= pd.to_datetime(start_ts)) & (temp_time <= pd.to_datetime(end_ts))
            combined_df = combined_df[mask]
            if combined_df.empty: 
                return {"status": "error", "message": "No data in selected timeline."}

        if progress_callback: progress_callback(35, "Sanitizing cellular parameters and formatting identifiers...")
        # Step 3: Vectorized structural cleanups & sanitization
        raw_c_values = combined_df[col_C].astype(str)
        raw_d_values = combined_df[col_D].astype(str)

        combined_df[col_C] = combined_df[col_C].apply(_clean_phone_number)
        combined_df[col_D] = combined_df[col_D].apply(_clean_phone_number)
        
        for col in [col_B, col_F, col_G, col_H, col_I, col_K, col_L, col_J]: 
            combined_df[col] = combined_df[col].fillna('--Empty--').astype(str).str.strip().replace(['nan', 'NaN', 'None', ''], '--Empty--')
        for col in [col_H, col_I, col_J]: 
            combined_df[col] = combined_df[col].apply(lambda x: str(x).split('.')[0] if x != '--Empty--' else '--Empty--')

        # Concat anomalies with non-mobile designators instead of hard row dropping
        mask_c_valid = combined_df[col_C].str.len() == 11
        mask_d_valid = combined_df[col_D].str.len() == 11

        combined_df.loc[~mask_c_valid, col_C] = raw_c_values[~mask_c_valid] + "--[not a mobile number]"
        combined_df.loc[~mask_d_valid, col_D] = raw_d_values[~mask_d_valid] + "--[not a mobile number]"

        # Store parsed timeline mappings for node summaries
        combined_df['_parsed_dt'] = pd.to_datetime(combined_df[col_A], errors='coerce')
        unique_a_parties = [num for num in combined_df[col_C].unique() if num and str(num) != '--Empty--']
        summary_a_parties_str = ", ".join(unique_a_parties)

        if progress_callback: progress_callback(55, "Scanning hardware registries for twin-SIM device swaps...")
        # Step 4: Accurate Twin-Accumulator Hardware Mapping
        raw_imei_clean = combined_df[(combined_df[col_J] != '--Empty--') & (combined_df[col_C] != '--Empty--')]
        imei_to_sims_accumulator = {}
        sim_to_imeis_accumulator = {}
        
        unique_pairs = raw_imei_clean[[col_C, col_J]].drop_duplicates()
        for _, row in unique_pairs.iterrows():
            sim_num = str(row[col_C]).strip()
            imei_num = str(row[col_J]).strip()
            if sim_num.lower() == '--empty--' or imei_num.lower() == '--empty--': 
                continue
            imei_to_sims_accumulator.setdefault(imei_num, []).append(sim_num)
            sim_to_imeis_accumulator.setdefault(sim_num, []).append(imei_num)

        true_swapped = []
        for sim, imeis in sim_to_imeis_accumulator.items():
            if len(imeis) >= 3:
                true_swapped.append(f"{sim} ({len(imeis)} profiles)")
            elif len(imeis) == 2:
                model1 = lookup_imei(imeis[0])
                model2 = lookup_imei(imeis[1])
                brand1 = str(model1).split()[0].lower() if model1 else "unknown1"
                brand2 = str(model2).split()[0].lower() if model2 else "unknown2"
                if brand1 != brand2 and "unknown" not in (brand1 + brand2):
                    true_swapped.append(f"{sim} (Device Switch: {model1} ➔ {model2})")

        summary_imei_swappers_str = f"IMEI Swappers: {', '.join(true_swapped)}" if true_swapped else "Hardware Stability: No device swapping observed."
        true_multi = [f"Handset {i} ({len(s)} numbers)" for i, s in imei_to_sims_accumulator.items() if len(s) >= 3]
        summary_multi_sim_str = f"Multi-SIM Burners: {', '.join(true_multi)}" if true_multi else "Device Identity: No multi-SIM handset anomalies."

        if progress_callback: progress_callback(75, "Grouping chronological stay locations and movement signatures...")
        # Step 5: Chronological Spatial Mapping (Night Stays Locator)
        night_df = combined_df[combined_df['_parsed_dt'].dt.hour.isin([18,19,20,21,22,23,0,1,2,3,4,5])].copy()
        total_night_count = len(night_df)
        deep_night_count = len(night_df[night_df['_parsed_dt'].dt.hour.isin([1,2,3,4])])

        night_stays_list = []
        if total_night_count > 0:
            valid_locs = night_df[col_L].value_counts().head(5)
            for addr_text, _ in valid_locs.items():
                matching = night_df[night_df[col_L] == addr_text]
                tower_groups = matching.groupby([col_H, col_I]).size().reset_index(name='count')
                if not tower_groups.empty:
                    tower = tower_groups.sort_values(by='count', ascending=False).iloc[0]
                    night_stays_list.append(f"{addr_text} [LAC: {tower[col_H]}, Cell: {tower[col_I]}]")

        summary_night_stays_str = " | ".join(night_stays_list) if night_stays_list else "Insufficient Data"
        deep_night_pct = round((deep_night_count / total_night_count) * 100, 1) if total_night_count > 0 else 0
        summary_night_routine_str = f"Critical Windows: {deep_night_pct}% of night actions occurred between 01:00 AM and 04:00 AM."

        # UNIFIED COMPLETE SPATIAL-TEMPORAL ROADMAP LAYER WITH NATIVE ROW INJECTIONS
        spatial_roadmap_list = []
        roadmap_df = combined_df.copy()
        roadmap_df = roadmap_df.dropna(subset=['_parsed_dt']).sort_values(by='_parsed_dt').reset_index(drop=True)
        
        if not roadmap_df.empty:
            loc_signatures = roadmap_df[col_L].astype(str) + "_L_" + roadmap_df[col_H].astype(str) + "_C_" + roadmap_df[col_I].astype(str)
            roadmap_df['loc_block'] = (loc_signatures != loc_signatures.shift()).cumsum()
            
            grouped_blocks = roadmap_df.groupby('loc_block')
            sequence_id = 1
            for _, block in grouped_blocks:
                arr_time = block['_parsed_dt'].min()
                dep_time = block['_parsed_dt'].max()
                delta_duration = dep_time - arr_time
                
                total_seconds = int(delta_duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes} mins"
                if total_seconds < 60:
                    duration_str = "Instantaneous Transaction"

                # Extracting strict raw row indices natively to prevent garbage text parsing overrides
                spatial_roadmap_list.append({
                    "Sequence": f"{sequence_id:02d}",
                    "A_Party": str(block[col_C].iloc[0]),
                    "B_Party": str(block[col_D].iloc[0]),
                    "Type": str(block[col_B].iloc[0]),
                    "Location": str(block[col_L].iloc[0]),
                    "LAC": str(block[col_H].iloc[0]),
                    "Cell": str(block[col_I].iloc[0]),
                    "Arrived": arr_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "Departed": dep_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "Duration": duration_str
                })
                sequence_id += 1

        if progress_callback: progress_callback(90, "Writing structural data packages into output Excel ledger...")
        # Step 6: Query keyword filtration constraint loops
        final_condition = pd.Series(True, index=combined_df.index)
        if intended_location:
            keywords = [loc.strip().lower() for loc in intended_location.split(",") if loc.strip()]
            if keywords: 
                final_condition = combined_df[col_L].str.lower().apply(lambda val: any(k in val for k in keywords))

        filtered_df = combined_df[final_condition].copy()
        if filtered_df.empty: 
            return {"status": "error", "message": "No rows matched constraints."}
            
        filtered_df[col_E] = pd.to_numeric(filtered_df[col_E], errors="coerce").fillna(0)
        filtered_df["Frequency"] = filtered_df[col_D].map(filtered_df[col_D].value_counts())
        filtered_df[col_E] = filtered_df[col_D].map(filtered_df.groupby(col_D)[col_E].sum()) / 60
        filtered_df[col_E] = filtered_df[col_E].round(2)

        # Cross-file global contact matching logic
        b_to_as = combined_df.groupby(col_D)[col_C].nunique()
        extracted_common = b_to_as[b_to_as > 1].index.tolist()

        if is_single_file:
            summary_common_b_str = "N/A (Single File)"
        else:
            summary_common_b_str = ", ".join(extracted_common) if extracted_common else "None"
            filtered_df["Common?"] = filtered_df[col_D].apply(lambda x: "Yes" if x in extracted_common else "No")

        filtered_df["Has_Multiple_IMEI"] = filtered_df[col_C].apply(lambda x: "Yes" if len(sim_to_imeis_accumulator.get(x, [])) >= 3 else "No")
        filtered_df = filtered_df.drop_duplicates(subset=[col_D], keep="first")
        
        filtered_df[col_A] = filtered_df['_parsed_dt'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(x) else "")
        filtered_df = filtered_df.sort_values(by=['_parsed_dt'], ascending=False)

        top_b_data = [{"b_party": str(row[col_D]), "frequency": str(row["Frequency"]), "last_called": str(row[col_A])} for _, row in filtered_df.head(10).iterrows()]
        area_clusters = [{"area": str(k), "count": int(v)} for k, v in combined_df[col_L].value_counts().head(12).items() if str(k).strip() != '']
        preview_data = [{"dt": str(row[col_A]), "ap": str(row[col_C]), "bp": str(row[col_D]), "freq": str(row["Frequency"]), "loc": str(row[col_L])} for _, row in filtered_df.head(50).iterrows()]

        hourly_activity = {}
        for a_p in unique_a_parties:
            a_df = combined_df[combined_df[col_C] == a_p].copy()
            dist = a_df['_parsed_dt'].dt.hour.value_counts().reindex(range(24), fill_value=0).to_dict()
            hourly_activity[a_p] = {str(h): int(v) for h, v in dist.items()}

        output_filename = f"{''.join(c for c in (unique_a_parties[0] if unique_a_parties else 'Unknown') if c.isalnum())}-CDR-{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_excel_path = os.path.join(output_dir, output_filename)
        with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
            vertical_summary = {
                "Metric": ["A-Parties", "Top Contacts", "Night Stays", "Common Contacts", "IMEI Swaps", "Multi-SIM", "Critical Windows"],
                "Intelligence": [summary_a_parties_str, ", ".join([i["b_party"] for i in top_b_data]), summary_night_stays_str, summary_common_b_str, summary_imei_swappers_str, summary_multi_sim_str, summary_night_routine_str]
            }
            pd.DataFrame(vertical_summary).astype(str).to_excel(writer, sheet_name="Summary", index=False)
            filtered_df.astype(str).to_excel(writer, sheet_name="Data", index=False)
            for ws in [writer.sheets["Summary"], writer.sheets["Data"]]:
                for row in ws.iter_rows():
                    for cell in row: cell.number_format = "@"

        a_areas = combined_df.groupby(col_C)[col_L].agg(lambda x: x.value_counts().index[0] if not x.empty else "Unknown").to_dict()
        b_areas = combined_df.groupby(col_D)[col_L].agg(lambda x: x.value_counts().index[0] if not x.empty else "Unknown").to_dict()
        
        node_profiles = {}
        for entity_col, area_map in [(col_C, a_areas), (col_D, b_areas)]:
            for item in combined_df[entity_col].unique():
                sitem = str(item)
                if sitem and sitem != '--Empty--' and sitem not in node_profiles:
                    sub_df = combined_df[combined_df[entity_col] == item]['_parsed_dt'].dropna()
                    node_profiles[sitem] = {
                        "total": len(combined_df[combined_df[entity_col] == item]),
                        "first": sub_df.min().strftime("%Y-%m-%d %H:%M:%S") if not sub_df.empty else "Unknown",
                        "last": sub_df.max().strftime("%Y-%m-%d %H:%M:%S") if not sub_df.empty else "Unknown",
                        "top_loc": str(area_map.get(item, "Unknown"))
                    }

        detailed_imei_map = {
            str(imei): {"sims": sims, "hardware": lookup_imei(imei) or "Unknown Device"}
            for imei, sims in imei_to_sims_accumulator.items() if len(sims) > 1
        }
        sim_to_imei_map = {
            str(sim): [{"imei": str(i), "hw": lookup_imei(i) or "Generic Handset"} for i in imeis]
            for sim, imeis in sim_to_imeis_accumulator.items()
        }
        
        sim_to_imei_data = {"links": [], "nodes": []}
        seen_nodes = set()
        for sim, imeis in sim_to_imeis_accumulator.items():
            if len(imeis) > 1:
                sap = str(sim)
                if sap not in seen_nodes:
                    sim_to_imei_data["nodes"].append({"id": sap, "type": "SIM"})
                    seen_nodes.add(sap)
                for imei in imeis:
                    simei = str(imei)
                    if simei not in seen_nodes:
                        sim_to_imei_data["nodes"].append({"id": simei, "type": "IMEI", "hw": lookup_imei(imei) or "Generic Handset"})
                        seen_nodes.add(simei)
                    sim_to_imei_data["links"].append({"source": sap, "target": simei})

        common_nums = set(extracted_common) if not is_single_file else set()
        uncommon_map = {a: [] for a in unique_a_parties}
        common_map = {}
        for _, row in combined_df.iterrows():
            a, b = str(row[col_C]), str(row[col_D])
            if b in common_nums:
                common_map.setdefault(b, set()).add(a)
            else:
                if a in uncommon_map and b not in uncommon_map[a]: 
                    uncommon_map[a].append(b)
        
        for a in uncommon_map: 
            uncommon_map[a] = list(set(uncommon_map[a]))

        graph_data = json.dumps({
            "centers": unique_a_parties, 
            "uncommon-links": [{"source": a, "target-links": t} for a, t in uncommon_map.items()], 
            "common-links": [{"target": cb, "source": list(s)} for cb, s in common_map.items()], 
            "area_clusters": area_clusters, 
            "all_party_areas": {**a_areas, **b_areas},
            "node_profiles": node_profiles,
            "imei_to_sim_map": detailed_imei_map,
            "sim_to_imei_graph": sim_to_imei_data,
            "sim_to_imei_map": sim_to_imei_map
        }, ensure_ascii=False)

        return {"status": "success", "output_path": output_excel_path, "metrics": {"a_parties": summary_a_parties_str, "top_b_parties": top_b_data, "night_stays": summary_night_stays_str, "common_b_parties": summary_common_b_str, "imei_swappers": summary_imei_swappers_str, "multi_sim": summary_multi_sim_str, "night_routine": summary_night_routine_str, "area_clusters": area_clusters, "hourly_activity": hourly_activity, "preview_rows": preview_data, "graph_data": graph_data, "spatial_roadmap": spatial_roadmap_list}}
    except Exception as e: 
        return {"status": "error", "message": f"Engine failure: {str(e)}"}

def export_same_location_to_excel(json_data, output_path):
    """Saves compiled location overlap frames back into a standalone spreadsheet document."""
    try:
        data = json.loads(json_data)
        if not data: 
            return {"status": "error", "message": "No data to export."}
        df = pd.DataFrame(data)
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Same Location Analysis")
            ws = writer.sheets["Same Location Analysis"]
            for row in ws.iter_rows():
                for cell in row: cell.number_format = "@"
        return {"status": "success", "output_path": output_path}
    except Exception as e: 
        return {"status": "error", "message": str(e)}

def search_cdr_data(file_paths, search_query):
    """Cross-scans raw files for keyword patterns and constructs an HTML diagnostic output."""
    try:
        if not file_paths: 
            return {"status": "error", "message": "No files provided."}
        terms = [s.strip() for s in str(search_query).split(",") if s.strip()]
        
        all_dfs = []
        for path in file_paths:
            if not os.path.exists(path): 
                continue
            try:
                df = pd.read_excel(path, engine="openpyxl", dtype=str)
                if df.empty or len(df.columns) < 12: 
                    continue
                nums = df[df.columns[2]].apply(lambda x: "".join(c for c in str(x) if c.isdigit())[-11:]).unique()
                a_party = nums[-1] if len(nums) > 0 else "Unknown"
                
                df['_internal_a'] = a_party
                df['_internal_time'] = pd.to_datetime(df[df.columns[0]], errors='coerce')
                df['_internal_loc'] = df[df.columns[11]].fillna('--Empty--').astype(str).str.strip()
                all_dfs.append(df)
            except: 
                continue
            
        if not all_dfs: 
            return {"status": "error", "message": "No data extracted."}
        combined = pd.concat(all_dfs, ignore_index=True).fillna('--Empty--')
        dialog_lines = []
        
        for term in terms:
            mask = combined.astype(str).apply(lambda col: col.str.contains(term, case=False, na=False)).any(axis=1)
            match_df = combined[mask]
            
            if match_df.empty:
                dialog_lines.append(f"<font color='#ff5555'><b>Query Target: {term}</b></font><br/>&nbsp;&nbsp;Status: <i>No structural hits inside ledger logs.</i>")
            else:
                hit_cols = [str(col) for col in combined.columns if not str(col).startswith('_internal') and match_df[col].astype(str).str.contains(term, case=False, na=False).any()]
                suspects = sorted(list(set(match_df['_internal_a'].astype(str).tolist())))
                hours = match_df['_internal_time'].dt.hour
                night_count = len(hours[(hours >= 18) | (hours < 6)])
                intensity = "Night Activation Heavy" if night_count > len(match_df)/2 else "Day Activation Heavy"
                
                locs = match_df['_internal_loc'][match_df['_internal_loc'] != '--Empty--'].value_counts().head(3)
                loc_str = ", ".join(locs.index) if not locs.empty else "N/A"
                
                res = [
                    f"<b>Forensic Term Hit: <font color='#58a6ff'>{term}</font></b>",
                    f"• Intercepted Suspect Profiles: {', '.join(suspects)}",
                    f"• Vector Match Coordinates: {', '.join(hit_cols[:3])}",
                    f"• Activity Intensity Metrics: {len(match_df)} transaction hits ({intensity})",
                    f"• Top Associated Cluster Hubs: {loc_str}"
                ]
                dialog_lines.append("<br/>".join(res))
                
        return {"status": "success", "summary_html": "<br/><br/>".join(dialog_lines)}
    except Exception as e: 
        return {"status": "error", "message": str(e)}

def crop_cdr_data(file_paths, location_query, start_ts, end_ts, output_dir):
    """Extracts bounded time frames or location sub-segments into a separate workbook file."""
    try:
        all_dfs = [pd.read_excel(p, engine="openpyxl", dtype=str) for p in file_paths if os.path.exists(p)]
        if not all_dfs: 
            return {"status": "error", "message": "No data available."}
        combined = pd.concat(all_dfs, ignore_index=True).fillna('--Empty--')
        temp_time = pd.to_datetime(combined[combined.columns[0]], errors='coerce')
        mask = (temp_time >= pd.to_datetime(start_ts)) & (temp_time <= pd.to_datetime(end_ts))
        if location_query.strip(): 
            mask &= combined[combined.columns[11]].fillna('--Empty--').astype(str).str.contains(location_query, case=False, na=False)
        cropped = combined[mask].copy().astype(str).replace('nan', '--Empty--')
        if cropped.empty: 
            return {"status": "error", "message": "No matches found."}
        out_path = os.path.join(output_dir, f"{time.strftime('%Y%m%d_%H%M%S')}_{len(file_paths)}CDRsCropped.xlsx")
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            cropped.to_excel(writer, index=False)
            for row in writer.sheets['Sheet1'].iter_rows():
                for cell in row: cell.number_format = '@'
        return {"status": "success", "output_path": out_path, "count": len(cropped)}
    except Exception as e: 
        return {"status": "error", "message": str(e)}

def same_location_analysis(file_paths, progress_callback=None, start_ts=None, end_ts=None):
    """Identifies concurrent location overlaps across multi-device data logs."""
    try:
        paths = [str(p).strip() for p in file_paths if p and str(p) != 'None' and len(str(p)) > 5]
        if len(paths) < 2:
            return {"status": "error", "message": f"Need at least 2 CDRs. Found: {len(paths)} valid files."}
            
        all_data = []
        for p in paths:
            if os.path.exists(p):
                df = pd.read_excel(p, engine="openpyxl", dtype=str)
                if not df.empty and len(df.columns) >= 12:
                    t = pd.DataFrame()
                    t['R'] = pd.to_datetime(df[df.columns[0]], errors='coerce')
                    t['D'] = t['R'].dt.date
                    t['S'] = df[df.columns[0]].fillna('--Empty--').astype(str)
                    t['A'] = df[df.columns[2]].fillna('--Empty--').astype(str).str.strip().apply(_clean_phone_number)
                    t['B'] = df[df.columns[3]].fillna('--Empty--').astype(str).str.strip().apply(_clean_phone_number)
                    t['L'] = df[df.columns[7]].fillna('--Empty--').astype(str).str.strip().apply(lambda x: str(x).split('.')[0] if x != '--Empty--' else '--Empty--')
                    t['C'] = df[df.columns[8]].fillna('--Empty--').astype(str).str.strip().apply(lambda x: str(x).split('.')[0] if x != '--Empty--' else '--Empty--')
                    t['Loc'] = df[df.columns[11]].fillna('--Empty--').astype(str).str.strip()
                    all_data.append(t)
                    
        if len(all_data) < 2: 
            return {"status": "error", "message": "Insufficient valid data layers."}
        combined = pd.concat(all_data, ignore_index=True).dropna(subset=['D', 'A'])
        results = []

        # --- NEW TIMELINE FILTERING LOGIC INJECTION ---
        if start_ts and end_ts:
            mask = (combined['R'] >= pd.to_datetime(start_ts)) & (combined['R'] <= pd.to_datetime(end_ts))
            combined = combined[mask]
            if combined.empty:
                return {"status": "success", "data": "[]"}
        # ----------------------------------------------
        
        unique_days = sorted(combined['D'].unique())
        total_days = len(unique_days)
        
        for i, d in enumerate(unique_days):
            day_df = combined[combined['D'] == d]
            if day_df['A'].nunique() < 2: 
                if progress_callback: 
                    progress_callback(int((i + 1) / total_days * 100))
                continue
                
            valid_lac = day_df[(day_df['L'] != '') & (day_df['L'] != '--Empty--')]
            if not valid_lac.empty:
                matches = valid_lac.groupby('L').filter(lambda x: x['A'].nunique() > 1)
                for _, row in matches.iterrows():
                    is_c = day_df[(day_df['L'] == row['L']) & (day_df['C'] == row['C'])]['A'].nunique() > 1
                    results.append({"Time": row['S'], "A_Party": row['A'], "B_Party": row['B'], "LAC": row['L'], "Cell": row['C'], "BTS_Loc": row['Loc'], "Reason": "LAC+Cell Match" if is_c else "LAC Match"})
            
            a_list = sorted(list(day_df['A'].unique()))
            addr_map = day_df[day_df['Loc'] != '--Empty--'].groupby('A')['Loc'].unique().to_dict()
            for i_ap in range(len(a_list)):
                for j_ap in range(i_ap+1, len(a_list)):
                    ap1, ap2 = a_list[i_ap], a_list[j_ap]
                    for ad1 in addr_map.get(ap1, []):
                        for ad2 in addr_map.get(ap2, []):
                            if SequenceMatcher(None, str(ad1).lower(), str(ad2).lower()).ratio() >= 0.7:
                                rows = day_df[(day_df['A'].isin([ap1, ap2])) & (day_df['Loc'].isin([ad1, ad2]))]
                                for _, r in rows.iterrows():
                                    results.append({"Time": r['S'], "A_Party": r['A'], "B_Party": r['B'], "LAC": r['L'], "Cell": r['C'], "BTS_Loc": r['Loc'], "Reason": "Tower Similarity (>70%)"})
            
            if progress_callback:
                progress_callback(int((i + 1) / total_days * 100))

        if not results: 
            return {"status": "success", "data": "[]"}
        final = pd.DataFrame(results).drop_duplicates(subset=['Time', 'A_Party'])
        return {"status": "success", "data": json.dumps(final.sort_values('Time', ascending=False).head(1500).to_dict('records'), ensure_ascii=False)}
    except Exception as e: 
        return {"status": "error", "message": f"Critical Location Error: {str(e)}"}