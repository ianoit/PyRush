"""
Report generation for PyRush stress testing results
"""

import csv
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import io
from .models import RequestResult

def export_csv(tester, filename: str):
    """
    Export test results to CSV file
    
    Args:
        tester: StressTester instance containing results
        filename: Output CSV filename
    """
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'url', 'method', 'status_code', 'response_time', 'response_size', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in tester.results:
            writer.writerow({
                'timestamp': result.timestamp,
                'url': result.url,
                'method': result.method,
                'status_code': result.status_code,
                'response_time': result.response_time,
                'response_size': result.response_size,
                'error': result.error or ''
            })

def export_json(tester, filename: str, stats: dict):
    """
    Export test results to JSON file
    
    Args:
        tester: StressTester instance containing results
        filename: Output JSON filename
        stats: Statistics dictionary
    """
    data = {
        'summary': stats,
        'results': [
            {
                'timestamp': r.timestamp,
                'url': r.url,
                'method': r.method,
                'status_code': r.status_code,
                'response_time': r.response_time,
                'response_size': r.response_size,
                'error': r.error
            } for r in tester.results
        ]
    }
    
    with open(filename, 'w') as fjson:
        json.dump(data, fjson, indent=2)

def generate_pdf_report(tester, filename: str):
    """
    Generate comprehensive PDF report from test results
    
    Args:
        tester: StressTester instance containing results and configuration
        filename: Output PDF filename
    """
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1
    )
    
    # Add title
    story.append(Paragraph("PyRush Stress Test Report", title_style))
    story.append(Spacer(1, 20))
    
    # Add start and end times
    if tester.start_time and tester.end_time:
        waktu_mulai = datetime.fromtimestamp(tester.start_time).strftime('%Y-%m-%d %H:%M:%S')
        waktu_selesai = datetime.fromtimestamp(tester.end_time).strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"Start Time: {waktu_mulai}", styles['Normal']))
        story.append(Paragraph(f"End Time: {waktu_selesai}", styles['Normal']))
        story.append(Spacer(1, 10))
    
    # Add test configuration
    story.append(Paragraph("Test Configuration", styles['Heading2']))
    config_data = [
        ['Parameter', 'Value'],
        ['URLs', ', '.join(tester.urls)],
        ['Method', tester.config.method],
        ['Total Requests', str(tester.config.num_requests)],
        ['Concurrency', str(tester.config.concurrency)],
        ['Rate Limit', str(tester.config.rate_limit) if tester.config.rate_limit else 'No limit'],
        ['Duration', f"{tester.config.duration}s" if tester.config.duration else 'N/A'],
        ['Timeout', f"{tester.config.timeout}s"],
        ['Content Type', tester.config.content_type],
    ]
    
    if tester.config.auth:
        config_data.append(['Authentication', f"{tester.config.auth[0]}:****"])
    if tester.config.proxy:
        config_data.append(['Proxy', tester.config.proxy])
    if tester.config.host:
        config_data.append(['Host Header', tester.config.host])
    
    config_table = Table(config_data, colWidths=[2*inch, 4*inch])
    config_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(config_table)
    story.append(Spacer(1, 20))
    
    # Generate and add statistics
    stats = tester.generate_statistics()
    if stats:
        story.append(Paragraph("Summary Statistics", styles['Heading2']))
        summary_data = [
            ['Metric', 'Value'],
            ['Total Requests', str(stats['total_requests'])],
            ['Successful Requests', str(stats['successful_requests'])],
            ['Failed Requests', str(stats['failed_requests'])],
            ['Success Rate', f"{stats['success_rate']:.2f}%"],
            ['Total Duration', f"{stats['total_duration']:.2f}s"],
            ['Requests per Second', f"{stats['requests_per_second']:.2f}"],
            ['Throughput (bytes/sec)', f"{stats['throughput_bytes_per_sec']:.2f}"],
        ]
        
        if 'mean_response_time' in stats:
            summary_data.extend([
                ['Mean Response Time', f"{stats['mean_response_time']:.3f}s"],
                ['Median Response Time', f"{stats['median_response_time']:.3f}s"],
                ['Min Response Time', f"{stats['min_response_time']:.3f}s"],
                ['Max Response Time', f"{stats['max_response_time']:.3f}s"],
                ['P95 Response Time', f"{stats['p95_response_time']:.3f}s"],
                ['P99 Response Time', f"{stats['p99_response_time']:.3f}s"],
            ])
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Add response time histogram
        if 'mean_response_time' in stats and tester.results:
            response_times = [r.response_time for r in tester.results if r.error is None]
            if response_times:
                fig, ax = plt.subplots(figsize=(5, 2.5))
                ax.hist(response_times, bins=20, color='#007acc', edgecolor='black')
                ax.set_title('Response Time Distribution (seconds)')
                ax.set_xlabel('Response Time (s)')
                ax.set_ylabel('Number of Requests')
                plt.tight_layout()
                
                img_buf = io.BytesIO()
                plt.savefig(img_buf, format='png')
                plt.close(fig)
                img_buf.seek(0)
                
                story.append(Paragraph("Response Time Distribution:", styles['Heading3']))
                story.append(Image(img_buf, width=5*inch, height=2.5*inch))
                story.append(Paragraph("Chart showing the distribution of response times across all requests.", styles['Normal']))
                story.append(Spacer(1, 20))
        
        # Add status code distribution
        if stats.get('status_code_distribution'):
            status_data = [['Status Code', 'Count']]
            for status_code, count in sorted(stats['status_code_distribution'].items()):
                status_data.append([str(status_code), str(count)])
            
            status_table = Table(status_data, colWidths=[2*inch, 4*inch])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.beige),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(Paragraph("Status Code Distribution:", styles['Heading3']))
            story.append(status_table)
            story.append(Spacer(1, 10))
        
        # Add 10 slowest requests
        if tester.results:
            slowest = sorted([r for r in tester.results if r.error is None], 
                           key=lambda r: r.response_time, reverse=True)[:10]
            if slowest:
                slowest_data = [['#', 'URL', 'Status', 'Response Time (s)']]
                for i, r in enumerate(slowest, 1):
                    slowest_data.append([i, r.url, r.status_code, f"{r.response_time:.3f}"])
                
                slowest_table = Table(slowest_data, colWidths=[0.4*inch, 2.5*inch, 0.8*inch, 1.2*inch])
                slowest_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.beige),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(Paragraph("10 Slowest Requests:", styles['Heading3']))
                story.append(slowest_table)
                story.append(Spacer(1, 10))
        
        # Add error distribution
        if stats.get('error_distribution'):
            error_data = [['Error Type', 'Count']]
            for error_type, count in stats['error_distribution'].items():
                error_data.append([error_type[:50] + '...' if len(error_type) > 50 else error_type, str(count)])
            
            error_table = Table(error_data, colWidths=[4*inch, 2*inch])
            error_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(Paragraph("Error Distribution:", styles['Heading3']))
            story.append(error_table)
            story.append(Spacer(1, 10))
        
        # Add automatic recommendations
        recommendations = []
        if 'p95_response_time' in stats and stats['p95_response_time'] > 1.0:
            recommendations.append("P95 response time is above 1 second, consider optimizing backend/API.")
        if stats.get('failed_requests', 0) > 0:
            recommendations.append("There are failed requests, check error distribution and backend logs.")
        if 'mean_response_size' in stats and stats['mean_response_size'] < 100:
            recommendations.append("Response size is very small, ensure API returns expected data.")
        
        if recommendations:
            story.append(Paragraph("Recommendations:", styles['Heading2']))
            for rec in recommendations:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Add sample request data
        if tester.results:
            sample_data = [['Timestamp', 'URL', 'Status', 'Response Time (s)', 'Size', 'Error']]
            for r in tester.results[:20]:  # First 20 requests
                sample_data.append([
                    datetime.fromtimestamp(r.timestamp).strftime('%H:%M:%S'),
                    r.url,
                    r.status_code,
                    f"{r.response_time:.3f}",
                    r.response_size,
                    r.error or ''
                ])
            
            sample_table = Table(sample_data, colWidths=[1*inch, 2*inch, 0.8*inch, 1*inch, 0.8*inch, 1.5*inch])
            sample_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.beige),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(Paragraph("Sample Request Data (first 20 requests):", styles['Heading2']))
            story.append(sample_table)
            story.append(Spacer(1, 10))
    
    # Build the PDF
    doc.build(story) 