"""
Forensic PDF Report Generator Matrix Engine.
Implements universal, highly compressed monochromatic A4 document formatting
with strict compliance for technical intelligence dossiers.
Includes automated font-point scaling (Arial), full-bleed table word-wrapping,
identity alias phonebook mapping bolding, and the upgraded 24-hour temporal heatmap grid matrix.
"""

import os
from PyQt6.QtCore import QMarginsF
from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter

def compile_case_pdf_report(output_pdf_path, metrics, alias_database=None, location_request="N/A", timeline_analysis="N/A", cdr_names=None):
    """
    Assembles the complete case intelligence package into a clean monochromatic PDF file brief.
    """
    if alias_database is None:
        alias_database = {}
    if cdr_names is None:
        cdr_names = []

    # Helper function to check and bold registered aliases
    def format_target(number):
        num_str = str(number).strip()
        if num_str in alias_database:
            return f"<b>{num_str} ({alias_database[num_str]})</b>"
        return num_str

    # Format CDR name strings
    cdr_names_str = ", ".join(cdr_names) if cdr_names else "None Selected"

    # Ingest spatial roadmap for Section 3 (Chronological Spatial Roadmap Stays)
    spatial_roadmap = metrics.get("spatial_roadmap", [])
    roadmap_rows_html = ""
    for idx, row in enumerate(spatial_roadmap):
        ap = row.get("A-Party", row.get("ap", "Unknown"))
        bp = row.get("B-Party", row.get("bp", "Unknown"))
        bts = row.get("BTS Address", row.get("bts_address", "Unknown"))
        reason = row.get("Reason", row.get("reason", "In Transit"))
        time_str = row.get("Time", row.get("timestamp", "N/A"))
        lac = row.get("LAC", row.get("lac", "--Empty--"))
        cell = row.get("Cell", row.get("cell_id", "--Empty--"))

        roadmap_rows_html += f"""
        <tr>
            <td>{time_str}</td>
            <td>{format_target(ap)}</td>
            <td>{format_target(bp)}</td>
            <td>{lac}</td>
            <td>{cell}</td>
            <td>{bts}</td>
            <td>{reason}</td>
        </tr>
        """

    # Ingest Take A Peek Raw Log preview rows for Section 1
    peek_data = metrics.get("peek_data", [])
    peek_rows_html = ""
    for row in peek_data:
        time_str = row.get("Time", row.get("timestamp", "N/A"))
        ap = row.get("A-Party", row.get("ap", "Unknown"))
        bp = row.get("B-Party", row.get("bp", "Unknown"))
        lac = row.get("LAC", row.get("lac", "--Empty--"))
        freq = row.get("Frequency", row.get("frequency", "1"))
        bts = row.get("BTS Address", row.get("bts_address", "Unknown"))

        peek_rows_html += f"""
        <tr>
            <td>{time_str}</td>
            <td>{format_target(ap)}</td>
            <td>{format_target(bp)}</td>
            <td>{lac}</td>
            <td>{freq}</td>
            <td>{bts}</td>
        </tr>
        """

    # Generate 24-Hour Temporal Heatmap Matrix HTML (Section 2)
    heatmap_matrix = metrics.get("heatmap_matrix", {})
    heatmap_html = ""
    if heatmap_matrix:
        for target, hourly_counts in heatmap_matrix.items():
            heatmap_html += f"""
            <div class='heatmap-section' style='page-break-inside: avoid; margin-top: 15pt;'>
                <p style='font-size: 11pt; margin-bottom: 5pt;'><b>Target Stream Activity Profile: {format_target(target)}</b></p>
                <table class='heatmap-table'>
                    <thead>
                        <tr>
                            <th>00</th><th>01</th><th>02</th><th>03</th><th>04</th><th>05</th>
                            <th>06</th><th>07</th><th>08</th><th>09</th><th>10</th><th>11</th>
                            <th>12</th><th>13</th><th>14</th><th>15</th><th>16</th><th>17</th>
                            <th>18</th><th>19</th><th>20</th><th>21</th><th>22</th><th>23</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
            """
            for count in hourly_counts:
                # Monochromatic density shading classification
                bg_style = "background-color: #ffffff;"
                text_style = "color: #000000;"
                if count > 0:
                    if count < 5:
                        bg_style = "background-color: #e0e0e0; font-weight: bold;"
                    elif count < 15:
                        bg_style = "background-color: #a0a0a0; font-weight: bold; color: #ffffff;"
                    else:
                        bg_style = "background-color: #000000; font-weight: bold; color: #ffffff;"
                heatmap_html += f"<td style='{bg_style} {text_style} text-align: center;'>{count}</td>"
            heatmap_html += f"""
                        </tr>
                    </tbody>
                </table>
            </div>
            """
    else:
        heatmap_html = "<p style='font-size: 12pt;'>No temporal frequency metric configurations populated inside the active case cache.</p>"

    # Unified Master HTML Content Layout template structure
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * {{
                color: #000000 !important;
                font-family: 'Arial', sans-serif;
                box-sizing: border-box;
            }}
            body {{
                margin: 0in; /* Margins handled explicitly by QPageLayout */
                font-size: 12pt;
                line-height: 1.4;
            }}
            .header-banner {{
                text-align: center;
                font-weight: bold;
                font-size: 12pt;
                letter-spacing: 2px;
                margin-bottom: 15pt;
            }}
            .title-block {{
                text-align: center;
                margin-bottom: 20pt;
            }}
            .title-block h1 {{
                font-size: 18pt;
                margin: 0 0 5pt 0;
                font-weight: bold;
                text-transform: uppercase;
            }}
            .setup-metadata {{
                margin: 10pt auto;
                font-size: 11pt;
                width: 100%;
                border-top: 1px solid #000000;
                border-bottom: 1px solid #000000;
                padding: 6pt 0;
                text-align: left;
            }}
            .section-title {{
                font-size: 13pt;
                font-weight: bold;
                margin-top: 20pt;
                margin-bottom: 8pt;
                text-transform: uppercase;
                border-bottom: 1.5pt solid #000000;
                padding-bottom: 3pt;
                page-break-after: avoid;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 8pt;
                font-size: 10pt;
                table-layout: fixed;
            }}
            th, td {{
                border: 0.5pt solid #000000;
                padding: 4pt 6pt;
                text-align: left;
                word-wrap: break-word;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            .heatmap-table {{
                width: 100%;
                table-layout: fixed;
                border-collapse: collapse;
                font-size: 9pt;
            }}
            .heatmap-table th, .heatmap-table td {{
                padding: 4pt 1pt;
                border: 0.5pt solid #000000;
                text-align: center;
            }}
            .heatmap-table th {{
                background-color: #eaeaea;
            }}
            .footer-banner {{
                text-align: center;
                font-weight: bold;
                font-size: 12pt;
                letter-spacing: 2px;
                margin-top: 20pt;
            }}
        </style>
    </head>
    <body>
        <div class="header-banner"><b>SECRET</b></div>
        
        <div class="title-block">
            <h1>Forensic Case Intelligence Dossier</h1>
            <div class="setup-metadata">
                <b>Location Request:</b> {location_request} &nbsp;|&nbsp; 
                <b>Timeline Analysis:</b> {timeline_analysis}<br>
                <b>Source CDR Logs:</b> {cdr_names_str}
            </div>
        </div>

        <div class="section-title">Section 1: Live Logs Ingestion Summary (Take A Peek)</div>
        <table>
            <colgroup>
                <col style="width: 15%;">
                <col style="width: 13%;">
                <col style="width: 13%;">
                <col style="width: 10%;">
                <col style="width: 10%;">
                <col style="width: 39%;">
            </colgroup>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Ap</th>
                    <th>Bp</th>
                    <th>LAC</th>
                    <th>Frequency</th>
                    <th>BTS Address</th>
                </tr>
            </thead>
            <tbody>
                {peek_rows_html if peek_rows_html else "<tr><td colspan='6'>No index data staged in the target record view frames.</td></tr>"}
            </tbody>
        </table>

        <div class="section-title">Section 2: 24-Hour Temporal Activity Heatmaps</div>
        {heatmap_html}

        <div class="section-title">Section 3: Chronological Spatial Roadmap Stays</div>
        <table>
            <colgroup>
                <col style="width: 14%;">
                <col style="width: 12%;">
                <col style="width: 12%;">
                <col style="width: 9%;">
                <col style="width: 9%;">
                <col style="width: 32%;">
                <col style="width: 12%;">
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
                {roadmap_rows_html if roadmap_rows_html else "<tr><td colspan='7'>No continuous tracking vectors computed inside this case framework.</td></tr>"}
            </tbody>
        </table>

        <div class="footer-banner"><b>SECRET</b></div>
    </body>
    </html>
    """

    # Instantiate print rendering objects
    document = QTextDocument()
    document.setHtml(html_content)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_pdf_path)
    
    # Configure absolute monochrome A4 blueprint metrics
    page_layout = QPageLayout()
    page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    page_layout.setOrientation(QPageLayout.Orientation.Portrait)
    page_layout.setMargins(QMarginsF(0.4, 0.4, 0.4, 0.4), QPageLayout.Unit.Inch)
    printer.setPageLayout(page_layout)

    # Compile paint device
    document.print_(printer)