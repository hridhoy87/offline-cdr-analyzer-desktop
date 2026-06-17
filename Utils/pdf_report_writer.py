import os
import json
import time
from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize, QPainter, QFont
from PyQt6.QtCore import QMarginsF, QPointF, QRectF, Qt
from PyQt6.QtPrintSupport import QPrinter

class CustomForensicPrinter(QPrinter):
    """Custom printer wrapper that injects running headers and footers on every page."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def paint_page_decorations(self, painter, rect):
        painter.save()
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(Qt.GlobalColor.black)
        
        # 1. Paint Top Header
        painter.drawText(
            QRectF(rect.left(), rect.top() - 25, rect.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            "SECRET"
        )
        
        # 2. Paint Bottom Footer
        painter.drawText(
            QRectF(rect.left(), rect.bottom() + 10, rect.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            "SECRET"
        )
        painter.restore()

def compile_case_pdf_report(file_path, case_name, summary_html, preview_rows, same_loc_json, graph_json_str, 
                            alias_database=None, location_request="N/A", timeline_analysis="N/A", cdr_names=None):
    """Compiles a polished, multi-section forensic intelligence brief into a single structured PDF.
    
    Adheres strictly to Arial font, monochromatic pure black text, standard 12pt typography, 
    custom column layouts, unified 'SECRET' running classification tags, and processing metadata setup lines.
    """
    try:
        doc = QTextDocument()
        alias_db = alias_database if alias_database else {}
        processed_cdrs = cdr_names if cdr_names else ["N/A"]

        def format_bold_aliases(text):
            """Helper function to cleanly strip bullet icons and bold phonebook database matches."""
            cleaned = str(text).replace('📌 ', '').replace('🎯 ', '').replace('🌙 ', '').replace('🔗 ', '')
            for target_num, name in alias_db.items():
                match_str = f"{name} [{target_num}]"
                if match_str in cleaned:
                    cleaned = cleaned.replace(match_str, f"<b>{match_str}</b>")
                elif target_num in cleaned:
                    cleaned = cleaned.replace(target_num, f"<b>{target_num}</b>")
            return cleaned

        # --- SECTION 2: RE-ARRANGED LINK CORRELATION INSIGHTS TABLE ---
        try:
            graph_data = json.loads(graph_json_str) if graph_json_str else {}
        except:
            graph_data = {}

        common_links_list = graph_data.get("common-links", [])
        node_profiles = graph_data.get("node_profiles", {})
        
        link_analysis_table_html = ""
        if not common_links_list:
            link_analysis_table_html = "<p><i>No cross-link common contacts or correlations detected between target subjects in this run.</i></p>"
        else:
            link_analysis_table_html = """
            <table class="forensic-table">
                <colgroup>
                    <col style="width: 8%;" />
                    <col style="width: 30%;" />
                    <col style="width: 47%;" />
                    <col style="width: 15%;" />
                </colgroup>
                <thead>
                    <tr>
                        <th>Sl</th>
                        <th>Shared Common Contact ID</th>
                        <th>Connected Target Profiles Matrix</th>
                        <th>Interaction Total</th>
                    </tr>
                </thead>
                <tbody>
            """
            for idx, item in enumerate(common_links_list, 1):
                common_b_party = item.get("target")
                associated_a_parties = item.get("source", [])
                
                bolded_a_parties = []
                for a_p in associated_a_parties:
                    raw_num = a_p.replace('📌 ', '').split(' [')[0].strip() if ' [' in a_p else a_p.replace('📌 ', '').strip()
                    if raw_num in alias_db:
                        bolded_a_parties.append(f"<b>📌 {alias_db[raw_num]} [{raw_num}]</b>")
                    else:
                        bolded_a_parties.append(a_p)
                
                targets_str = ", ".join(bolded_a_parties)
                profile = node_profiles.get(str(common_b_party), {})
                total_calls = profile.get("total", "N/A")
                
                b_party_display = common_b_party
                for target_num, name in alias_db.items():
                    if target_num in str(common_b_party):
                        b_party_display = f"<b>{name} [{target_num}]</b>"
                        break

                link_analysis_table_html += f"""
                    <tr>
                        <td>{idx}</td>
                        <td>{b_party_display}</td>
                        <td>{targets_str}</td>
                        <td><b>{total_calls} hits</b></td>
                    </tr>
                """
            link_analysis_table_html += "</tbody></table>"

        # Format CDR array block cleanly into a wrapped comma-separated line
        cdr_string_line = ", ".join(processed_cdrs)

        # --- RE-ASSEMBLE FULL HTML ARCHITECTURE BODY SHEET ---
        html_content = f"""
        <html>
        <head>
            <style>
                /* --- Monochromatic Print Lock --- */
                * {{
                    color: #000000 !important;
                    font-family: Arial, sans-serif !important;
                }}
                
                /* --- Tightened Document Spacing & Page Margin --- */
                body {{
                    font-size: 12pt;
                    line-height: 1.3;
                    margin: 0.4in; /* Overall page margin reduced for high density */
                }}
                
                h1 {{
                    font-size: 14pt;
                    font-weight: bold;
                    text-transform: uppercase;
                    border-bottom: 1.5pt solid #000000;
                    padding-bottom: 4pt;
                    margin-top: 24pt;
                    margin-bottom: 12pt;
                }}
                h2 {{
                    font-size: 12pt;
                    font-weight: bold;
                    margin-top: 16pt;
                    margin-bottom: 6pt;
                    text-transform: uppercase;
                }}
                p, li, td, th {{
                    font-size: 12pt;
                }}
                
                /* --- Polished Thin Border Tables & Low Padding --- */
                .forensic-table {{
                    width: 100%;
                    table-layout: fixed;
                    border-collapse: collapse; /* Merges borders into clean lines */
                    margin-top: 8pt;
                    margin-bottom: 20pt;
                }}
                .forensic-table th, .forensic-table td {{
                    border: 0.5pt solid #000000; /* Aesthetic hair-thin black grid border */
                    padding: 4pt 6pt;           /* Decreased cell padding to prevent bloat */
                    text-align: left;
                    vertical-align: top;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }}
                .forensic-table th {{
                    font-weight: bold;
                    background-color: #f2f2f2;
                }}
                .section-container {{
                    margin-bottom: 20pt;
                }}
                .setup-metadata-box {{
                    text-align: left; 
                    margin: 12pt auto; 
                    max-width: 95%; 
                    font-size: 12pt; 
                    line-height: 1.5;
                    border-top: 1pt dashed #000000;
                    padding-top: 8pt;
                }}
            </style>
        </head>
        <body>
            <div style="text-align: center; margin-bottom: 35pt; border-bottom: 2.5pt solid #000000; padding-bottom: 10pt;">
                <h1 style="border: none; margin: 0; font-size: 18pt;">📡 CDR TELEMETRY INTELLIGENCE BRIEF</h1>
                <div style="font-size: 13pt; font-weight: bold; margin-top: 6pt;">ACTIVE WORKSPACE CASE DOSSIER: {case_name.upper()}</div>
                <div style="font-size: 11pt; margin-top: 4px;">Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                
                <div class="setup-metadata-box">
                    <b>Location Request:</b> {location_request if location_request else "N/A"}<br/>
                    <b>Timeline Analysis:</b> {timeline_analysis if timeline_analysis else "N/A"}<br/>
                    <b>Name of the CDRs:</b> {cdr_string_line}
                </div>
            </div>

            <h1>🎯 Section 1: Operational Summary Matrix</h1>
            <div class="section-container">
                {format_bold_aliases(summary_html)}
            </div>

            <h1>🧬 Section 2: Link Correlation Insights Matrix</h1>
            <div class="section-container">
                {link_analysis_table_html}
            </div>

            <h1>📱 Section 3: Subscriber Device Profile Lists</h1>
            <div class="section-container">
        """
        
        sim_to_imei_map = graph_data.get("sim_to_imei_map", {})
        imei_to_sim_map = graph_data.get("imei_to_sim_map", {})

        if not sim_to_imei_map and not imei_to_sim_map:
            html_content += "<p><i>No tracking hardware signature links mapped inside log blocks.</i></p>"
        else:
            if sim_to_imei_map:
                html_content += "<h2>📡 Subscriber SIM Profile Index (SIM ➔ IMEIs)</h2>"
                html_content += "<table class=\"forensic-table\"><colgroup><col style='width: 35%;'/><col style='width: 65%;'/></colgroup><thead><tr><th>Subscriber SIM</th><th>Associated IMEI Signatures & Model Info</th></tr></thead><tbody>"
                for sim, records in sim_to_imei_map.items():
                    imei_details = ""
                    for r in records:
                        imei_details += f"• {r.get('imei','N/A')} — {r.get('hw','Generic Handset')}<br/>"
                    sim_display = f"<b>{alias_db[sim]} [{sim}]</b>" if sim in alias_db else sim
                    html_content += f"<tr><td>{sim_display}</td><td>{imei_details}</td></tr>"
                html_content += "</tbody></table>"

            if imei_to_sim_map:
                html_content += "<h2>🛡️ Handset Core Terminal Index (IMEI ➔ SIMs)</h2>"
                html_content += "<table class=\"forensic-table\"><colgroup><col style='width: 40%;'/><col style='width: 30%;'/><col style='width: 30%;'/></colgroup><thead><tr><th>Handset Make/Model Info</th><th>Signature IMEI Hash</th><th>Linked Subscriber IMSIs</th></tr></thead><tbody>"
                for imei, info in imei_to_sim_map.items():
                    sims_linked_list = []
                    for s in info.get("sims", []):
                        sims_linked_list.append(f"<b>{alias_db[s]} [{s}]</b>" if s in alias_db else s)
                    html_content += f"<tr><td><b>{info.get('hardware','Generic Device')}</b></td><td>{imei}</td><td>{', '.join(sims_linked_list)}</td></tr>"
                html_content += "</tbody></table>"

        # --- SECTION 4: RAW RECORDS PREVIEW MATRIX (TAKE A PEEK) ---
        # Column headers constraint: Time, Ap, Bp, LAC, Frequency, BTS Address
        # --- SECTION 4: RAW RECORDS PREVIEW MATRIX (TAKE A PEEK) ---
        # Adjusted: Removed LAC column layout, header, and data row cell mappings
        html_content += f"""
            </div>
            <h1>👁️ Section 4: Telemetry Logs Preview (Take A Peek)</h1>
            <div class="section-container">
        """
        if not preview_rows:
            html_content += "<p><i>No data preview ledger generated in this execution path run.</i></p>"
        else:
            html_content += """
                <table class="forensic-table">
                    <colgroup>
                        <col style="width: 18%;" />
                        <col style="width: 16%;" />
                        <col style="width: 16%;" />
                        <col style="width: 10%;" />
                        <col style="width: 40%;" />
                    </colgroup>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Ap</th>
                            <th>Bp</th>
                            <th>Frequency</th>
                            <th>BTS Address</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for row in preview_rows[:50]:  
                ap_raw = row.get('ap', '')
                bp_raw = row.get('bp', '')
                ap_display = f"<b>{alias_db[ap_raw]} [{ap_raw}]</b>" if ap_raw in alias_db else ap_raw
                bp_display = f"<b>{alias_db[bp_raw]} [{bp_raw}]</b>" if bp_raw in alias_db else bp_raw
                
                html_content += f"""
                        <tr>
                            <td>{row.get('dt','')}</td>
                            <td>{ap_display}</td>
                            <td>{bp_display}</td>
                            <td>{row.get('freq','')}</td>
                            <td>{row.get('loc','')}</td>
                        </tr>
                """
            html_content += "                    </tbody></table>"

        # --- SECTION 5: MOVED SPATIAL CRITICAL CROSS-OVER MATRIX TO THE VERY END ---
        # Column headers constraint: Time, Ap, Bp, LAC, Cell, BTS Address, Reason
        html_content += """
            </div>
            <h1>📍 Section 5: Spatial Cross-Over Interceptions</h1>
            <div class="section-container">
        """
        try:
            same_loc_records = json.loads(same_loc_json) if same_loc_json else []
        except:
            same_loc_records = []

        if not same_loc_records:
            html_content += "<p><i>Analysis yielded zero concurrent target location overlaps.</i></p>"
        else:
            html_content += """
                <table class="forensic-table">
                    <colgroup>
                        <col style="width: 15%;" />
                        <col style="width: 15%;" />
                        <col style="width: 15%;" />
                        <col style="width: 8%;" />
                        <col style="width: 8%;" />
                        <col style="width: 31%;" />
                        <col style="width: 8%;" />
                    </colgroup>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Ap</th>
                            <th>Bp</th>
                            <th>LAC</th>
                            <th>Cell</th>
                            <th>BTS Address</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for row in same_loc_records:
                a_p = row.get('A_Party', '')
                b_p = row.get('B_Party', '')
                a_disp = f"<b>{alias_db[a_p]} [{a_p}]</b>" if a_p in alias_db else a_p
                b_disp = f"<b>{alias_db[b_p]} [{b_p}]</b>" if b_p in alias_db else b_p

                html_content += f"""
                        <tr>
                            <td>{row.get('Time','')}</td>
                            <td>{a_disp}</td>
                            <td>{b_disp}</td>
                            <td>{row.get('LAC','')}</td>
                            <td>{row.get('Cell','')}</td>
                            <td>{row.get('BTS_Loc','')}</td>
                            <td>{row.get('Reason','')}</td>
                        </tr>
                """
            html_content += "                    </tbody></table>"

        html_content += "</div></body></html>"

        doc.setHtml(html_content)
        
        printer = CustomForensicPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        
        layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4), 
            QPageLayout.Orientation.Portrait, 
            QMarginsF(15, 15, 15, 15)
        )
        printer.setPageLayout(layout)
        
        doc.print(printer)
        return {"status": "success", "file_path": file_path}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}