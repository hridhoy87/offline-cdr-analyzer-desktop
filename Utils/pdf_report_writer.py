import os
import json
import pandas as pd
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

# =========================================================================
# 📝 HTML/CSS TEMPLATE ENGINE FOR CHROMIUM PDF RENDERING
# =========================================================================
PDF_STYLE = """
<style>
    /* Base A4 Layout Properties */
    body { font-family: 'Helvetica', 'Arial', sans-serif; color: #1a1a1a; font-size: 10pt; line-height: 1.4; margin: 0; padding: 0; background-color: #ffffff; }
    
    /* Document Headers */
    h1 { color: #0d1117; font-size: 18pt; border-bottom: 3px solid #b91c1c; padding-bottom: 5px; margin-bottom: 15px; text-transform: uppercase; }
    h2 { color: #1f6feb; font-size: 14pt; border-bottom: 2px solid #d0d7de; padding-bottom: 3px; margin-top: 30px; margin-bottom: 12px; page-break-after: avoid; }
    h3 { color: #24292f; font-size: 11pt; margin-top: 15px; margin-bottom: 8px; page-break-after: avoid; }
    
    /* Table of Contents */
    .toc-box { background-color: #f6f8fa; border: 1px solid #d0d7de; padding: 15px; border-radius: 6px; margin-bottom: 25px; }
    .toc-box ul { list-style-type: none; padding-left: 0; }
    .toc-box li { margin-bottom: 8px; }
    .toc-box a { color: #0969da; text-decoration: none; font-weight: bold; }
    .toc-box a:hover { text-decoration: underline; }

    /* Tables */
    .meta-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 10pt; }
    .meta-table td { padding: 6px; vertical-align: top; border: 1px solid #d0d7de; }
    .meta-label { font-weight: bold; color: #1a1a1a; background-color: #f0f6fc; width: 25%; }
    
    .data-table { width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 8pt; }
    .data-table th { background-color: #24292f; color: #ffffff; font-weight: bold; text-align: left; padding: 7px; border: 1px solid #000000; }
    .data-table td { padding: 6px; border: 1px solid #d0d7de; vertical-align: top; page-break-inside: avoid; }
    .stripe { background-color: #f6f8fa; }
    
    .heatmap-table { width: 100%; border-collapse: collapse; font-size: 7pt; text-align: center; margin-bottom: 15px; }
    .heatmap-table th { background-color: #f0f6fc; border: 1px solid #d0d7de; padding: 4px; }
    .heatmap-table td { border: 1px solid #d0d7de; padding: 4px; font-weight: bold; }
    
    ul.cdr-list { font-size: 9pt; font-family: monospace; color: #57606a; background: #f6f8fa; padding: 10px 10px 10px 30px; border: 1px solid #d0d7de; }
    .empty-state { font-style: italic; color: #8b949e; padding: 10px; border: 1px dashed #d0d7de; background-color: #f6f8fa; }

    /* 🛡️ REPEATING HEADERS & FOOTERS TRICK FOR CHROMIUM PDF */
    table.report-container { width: 100%; border: none; }
    thead.report-header { display: table-header-group; }
    tfoot.report-footer { display: table-footer-group; }
    .header-info, .footer-info { text-align: center; font-weight: bold; color: #b91c1c; font-size: 11pt; padding: 10px 0; letter-spacing: 2px; }
    .footer-info { border-top: 1px solid #b91c1c; }
    .header-info { border-bottom: 1px solid #b91c1c; }
</style>
"""

# =========================================================================
# HTML GENERATOR FUNCTIONS
# =========================================================================
def generate_heatmap_html(heatmap_matrix, alias_db):
    if not heatmap_matrix: return "<div class='empty-state'>No chronological transmission density logs available.</div>"
    html = ""
    for target_ap, distribution in heatmap_matrix.items():
        display_name = f"{alias_db.get(target_ap, target_ap)} [{target_ap}]" if target_ap in alias_db else target_ap
        max_val = max(distribution.values()) if distribution.values() else 1
        if max_val == 0: max_val = 1
        
        html += f"<h4>Target: {display_name}</h4><table class='heatmap-table'><tr>"
        for h in range(24): html += f"<th>{h:02d}:00</th>"
        html += "</tr><tr>"
        for h in range(24):
            val = distribution.get(str(h), 0)
            bg_color = f"rgba(31, 111, 235, {val/max_val})" if val > 0 else "#ffffff"
            text_color = "#ffffff" if (val / max_val) > 0.5 else "#000000"
            html += f"<td style='background-color: {bg_color}; color: {text_color};'>{val}</td>"
        html += "</tr></table>"
    return html

def generate_link_analysis_html(graph_data, alias_db):
    common = graph_data.get("common-links", [])
    if not common: return "<div class='empty-state'>No cross-link common contacts detected.</div>"
    html = "<table class='data-table'><tr><th>Common Shared Target (B-Party)</th><th>Shared By Intercepts (A-Parties)</th></tr>"
    for i, link in enumerate(common):
        stripe = "class='stripe'" if i % 2 != 0 else ""
        tgt_raw = str(link.get('target', 'Unknown'))
        tgt = f"{alias_db[tgt_raw]} [{tgt_raw}]" if tgt_raw in alias_db else tgt_raw
        srcs = []
        for s in link.get('source', []):
            s_raw = str(s)
            srcs.append(f"{alias_db[s_raw]} [{s_raw}]" if s_raw in alias_db else s_raw)
        html += f"<tr {stripe}><td><b>{tgt}</b></td><td>{', '.join(srcs)}</td></tr>"
    html += "</table>"
    return html

def generate_sim_imei_html(graph_data, alias_db):
    sim_map = graph_data.get("sim_to_imei_map", {})
    if not sim_map: return "<div class='empty-state'>No subscriber hardware linkages found.</div>"
    html = "<table class='data-table'><tr><th>Subscriber SIM Profile</th><th>Hardware Handset ID (IMEI)</th><th>Device Signature</th></tr>"
    row_idx = 0
    for sim, records in sim_map.items():
        sim_display = f"{alias_db[sim]} [{sim}]" if sim in alias_db else sim
        for r in records:
            stripe = "class='stripe'" if row_idx % 2 != 0 else ""
            html += f"<tr {stripe}><td>{sim_display}</td><td>{r.get('imei','')}</td><td>{r.get('hw','Generic Handset')}</td></tr>"
            row_idx += 1
    html += "</table>"
    return html

def generate_regional_clusters_html(graph_data):
    clusters = graph_data.get("area_clusters", [])
    if not clusters: return "<div class='empty-state'>No regional clustering data available.</div>"
    html = "<table class='data-table'><tr><th>Regional Base Sector (Location)</th><th>Recorded Intercept Frequency</th></tr>"
    for i, c in enumerate(clusters):
        stripe = "class='stripe'" if i % 2 != 0 else ""
        html += f"<tr {stripe}><td>{c.get('area','Unknown')}</td><td><b>{c.get('count', 0)}</b> events</td></tr>"
    html += "</table>"
    return html

def generate_bparty_freq_html(preview_rows, alias_db):
    if not preview_rows: return "<div class='empty-state'>No B-Party telemetry records available.</div>"
    html = "<table class='data-table'><tr><th>Date/Time (Most Recent)</th><th>A-Party Source</th><th>B-Party Destination</th><th>Call Frequency</th><th>Base Sector Location</th></tr>"
    for i, row in enumerate(preview_rows[:250]): # Display up to 250 rows to prevent PDF bloat
        stripe = "class='stripe'" if i % 2 != 0 else ""
        ap_raw = str(row.get('ap',''))
        bp_raw = str(row.get('bp',''))
        
        ap_disp = f"{alias_db[ap_raw]} [{ap_raw}]" if ap_raw in alias_db else ap_raw
        bp_disp = f"{alias_db[bp_raw]} [{bp_raw}]" if bp_raw in alias_db else bp_raw
        
        html += f"<tr {stripe}><td>{row.get('dt','')}</td><td>{ap_disp}</td><td>{bp_disp}</td><td><b>{row.get('freq','')}</b></td><td>{row.get('loc','')}</td></tr>"
    html += "</table>"
    return html

def generate_grouped_loc_html(data, alias_db):
    if not data: return "<div class='empty-state'>No grouped timeline route data available.</div>"
    html = ""
    for date_node in data:
        current_date = date_node.get("date", "Unknown Date")
        html += f"<h4>📅 Timeline Group: {current_date}</h4>"
        html += "<table class='data-table'><tr><th>Target A-Party</th><th>Duration Window</th><th>LAC</th><th>Cell ID</th><th>BTS Location</th></tr>"
        row_count = 0
        for cdr_node in date_node.get("data", []):
            tgt_raw = str(cdr_node.get("cdr", "Unknown"))
            target = f"{alias_db[tgt_raw]} [{tgt_raw}]" if tgt_raw in alias_db else tgt_raw
            
            for loc in cdr_node.get("loc-data", []):
                stripe = "class='stripe'" if row_count % 2 != 0 else ""
                start = loc.get("start_time", "")
                end = loc.get("end_time", "")
                window = f"{start} to {end}" if start != end else start
                
                # Check if the location string itself contains a raw number that needs aliasing
                loc_str = str(loc.get('address',''))
                for num, name in alias_db.items():
                    if num in loc_str: loc_str = loc_str.replace(num, f"{name} [{num}]")

                html += f"<tr {stripe}><td>{target}</td><td>{window}</td><td>{loc.get('lac','')}</td><td>{loc.get('cell','')}</td><td>{loc_str}</td></tr>"
                row_count += 1
        html += "</table>"
    return html

def generate_overlap_html(data, alias_db):
    if not data: return "<div class='empty-state'>Zero concurrent spatial crossovers detected.</div>"
    html = "<table class='data-table'><tr><th>Time Match</th><th>A-Party</th><th>B-Party</th><th>LAC / Cell</th><th>Location Match</th><th>Match Reason</th></tr>"
    for i, row in enumerate(data):
        stripe = "class='stripe'" if i % 2 != 0 else ""
        ap_raw = str(row.get('A_Party',''))
        bp_raw = str(row.get('B_Party',''))
        
        ap_disp = f"{alias_db[ap_raw]} [{ap_raw}]" if ap_raw in alias_db else ap_raw
        bp_disp = f"{alias_db[bp_raw]} [{bp_raw}]" if bp_raw in alias_db else bp_raw
        
        html += f"<tr {stripe}><td>{row.get('Time','')}</td><td>{ap_disp}</td><td>{bp_disp}</td><td>{row.get('LAC','')} / {row.get('Cell','')}</td><td>{row.get('BTS_Loc','')}</td><td>{row.get('Reason','')}</td></tr>"
    html += "</table>"
    return html

def generate_roadmap_html(roadmap_data, alias_db):
    if not roadmap_data: return "<div class='empty-state'>No sequential movement tracking data available.</div>"
    html = "<table class='data-table'><tr><th>Seq #</th><th>Arrived</th><th>Departed</th><th>Duration</th><th>Target A-Party</th><th>Destination B-Party</th><th>Network (LAC/Cell)</th><th>Sector Location</th></tr>"
    for i, node in enumerate(roadmap_data):
        stripe = "class='stripe'" if i % 2 != 0 else ""
        
        ap_raw = str(node.get("A_Party", ""))
        bp_raw = str(node.get("B_Party", ""))
        
        ap_display = f"{alias_db[ap_raw]} [{ap_raw}]" if ap_raw in alias_db else ap_raw
        bp_display = f"{alias_db[bp_raw]} [{bp_raw}]" if bp_raw in alias_db else bp_raw
        
        # Replace targets embedded in the location string
        loc_str = str(node.get('Location',''))
        for num, name in alias_db.items():
            if num in loc_str: loc_str = loc_str.replace(num, f"{name} [{num}]")
        
        html += f"<tr {stripe}>"
        html += f"<td>{node.get('Sequence','')}</td>"
        html += f"<td>{node.get('Arrived','')}</td>"
        html += f"<td>{node.get('Departed','')}</td>"
        html += f"<td><b>{node.get('Duration','')}</b></td>"
        html += f"<td>{ap_display}</td>"
        html += f"<td>{bp_display}</td>"
        html += f"<td>{node.get('LAC','')} / {node.get('Cell','')}</td>"
        html += f"<td>{loc_str}</td>"
        html += "</tr>"
    html += "</table>"
    return html

def generate_alias_db_html(alias_db):
    if not alias_db: return "<div class='empty-state'>No aliases registered in this workspace.</div>"
    html = "<table class='data-table' style='width: 50%;'><tr><th>Target Identifier</th><th>Assigned Alias Profile</th></tr>"
    for i, (num, name) in enumerate(alias_db.items()):
        stripe = "class='stripe'" if i % 2 != 0 else ""
        html += f"<tr {stripe}><td>{num}</td><td><b>{name}</b></td></tr>"
    html += "</table>"
    return html

# =========================================================================
# BACKGROUND WORKER THREAD
# =========================================================================
class PDFReportWorker(QThread):
    finished_html = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, mode, output_path, metrics, compiler_config):
        super().__init__()
        self.mode = mode
        self.output_path = output_path
        self.metrics = metrics
        self.config = compiler_config
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".cdr_analyzer_cache")

    def _lazy_load_json(self, filename):
        path = os.path.join(self.cache_dir, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        return []

    def _lazy_load_parquet(self, filename):
        path = os.path.join(self.cache_dir, filename)
        if os.path.exists(path):
            return pd.read_parquet(path).to_dict('records')
        return []

    def run(self):
        try:
            alias_db = self.config.get("alias_database", {})
            cdr_names = self.config.get("cdr_names", [])

            if self.mode == "heatmap":
                html_doc = f"<html><head>{PDF_STYLE}</head><body>"
                html_doc += f"<h1>Isolated Forensic Brief: HEATMAP</h1><p><b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p><p><b>Source Vectors:</b> {', '.join(cdr_names)}</p>"
                html_doc += generate_heatmap_html(self.metrics.get("heatmap_matrix", {}), alias_db)
                html_doc += "</body></html>"
                self.finished_html.emit(html_doc, self.output_path)
                return
            
            overlap_data = self._lazy_load_parquet("overlap_matrix.parquet")
            grouped_data = self._lazy_load_json("grouped_locations.json")
            graph_data = self._lazy_load_json("graph_data.json")
            preview_data = self._lazy_load_json("preview_rows.json")
            roadmap_data = self._lazy_load_json("spatial_roadmap.json")

            cdr_list_html = "".join([f"<li>{name}</li>" for name in cdr_names])

            html_doc = f"""
            <html>
            <head>{PDF_STYLE}</head>
            <body>
                <table class="report-container">
                    <thead class="report-header">
                        <tr><td><div class="header-info">SECRET // CONFIDENTIAL INTELLIGENCE BRIEF</div></td></tr>
                    </thead>
                    <tfoot class="report-footer">
                        <tr><td><div class="footer-info">SECRET // LAW ENFORCEMENT SENSITIVE</div></td></tr>
                    </tfoot>
                    <tbody>
                        <tr>
                            <td>
                                <h1 id="top">{self.config.get('case_title', 'COMPREHENSIVE INTELLIGENCE BRIEF')}</h1>
                                
                                <div class="toc-box">
                                    <h3>📑 Table of Contents</h3>
                                    <ul>
                                        <li><a href="#metadata">Analysis Parameters & Source Logs</a></li>
                                        <li><a href="#sec1">Section 1: Intelligence Summary & Density Heatmaps</a></li>
                                        <li><a href="#sec2">Section 2: Topology, Hardware & Regional Clusters</a></li>
                                        <li><a href="#sec3">Section 3: Target Intercept Frequencies (B-Party Log)</a></li>
                                        <li><a href="#sec4">Section 4: Grouped Location History by Date</a></li>
                                        <li><a href="#sec5">Section 5: Spatial Cross-Over Matrix</a></li>
                                        <li><a href="#sec6">Section 6: Stay Point Intercept Roadmap</a></li>
                                        <li><a href="#sec7">Section 7: Registered Alias Profile Database</a></li>
                                    </ul>
                                </div>

                                <h2 id="metadata">Analysis Parameters & Vectors</h2>
                                <table class="meta-table">
                                    <tr><td class="meta-label">Timeline for Analysis:</td><td>{self.config.get('timeline_analysis', 'Full Set')}</td></tr>
                                    <tr><td class="meta-label">Specific Keyword for Location:</td><td>{self.config.get('location_request', 'Unfiltered')}</td></tr>
                                    <tr><td class="meta-label">Date Compiled:</td><td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>
                                </table>

                                <h3>Data Source Logs (CDRs Taken):</h3>
                                <ul class="cdr-list">
                                    {cdr_list_html if cdr_names else "<li>No target files staged.</li>"}
                                </ul>

                                <h2 id="sec1">Section 1: Executive Analytics</h2>
                                <h3>1a. Intelligent Summary</h3>
                                {self.config.get('aliased_summary', '')}
                                <h3>1b. Transmission Density Heatmaps</h3>
                                {generate_heatmap_html(self.metrics.get('heatmap_matrix', {}), alias_db)}

                                <h2 id="sec2">Section 2: Node Topology & Infrastructure</h2>
                                <h3>2a. Link Analysis Table (Shared Contacts)</h3>
                                {generate_link_analysis_html(graph_data, alias_db)}
                                <h3>2b. SIM to IMEI Hardware Mapping Table</h3>
                                {generate_sim_imei_html(graph_data, alias_db)}
                                <h3>2c. Regional Area Cluster Frequency</h3>
                                {generate_regional_clusters_html(graph_data)}

                                <h2 id="sec3">Section 3: Target Frequencies (B-Party Analysis)</h2>
                                {generate_bparty_freq_html(preview_data, alias_db)}

                                <h2 id="sec4">Section 4: Grouped Location History by Date</h2>
                                {generate_grouped_loc_html(grouped_data, alias_db)}

                                <h2 id="sec5">Section 5: Spatial Cross-Over Matrix</h2>
                                {generate_overlap_html(overlap_data, alias_db)}

                                <h2 id="sec6">Section 6: Stay Point Intercept Roadmap</h2>
                                {generate_roadmap_html(roadmap_data, alias_db)}

                                <h2 id="sec7">Section 7: Alias Tracking Database</h2>
                                {generate_alias_db_html(alias_db)}

                            </td>
                        </tr>
                    </tbody>
                </table>
            </body>
            </html>
            """

            self.finished_html.emit(html_doc, self.output_path)
        
        except Exception as e:
            self.error_occurred.emit(str(e))