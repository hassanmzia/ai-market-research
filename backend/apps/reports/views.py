import csv
import io
import json
import logging
import re

import markdown
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SavedReport, ReportTemplate
from .serializers import (
    SavedReportSerializer,
    SavedReportCreateSerializer,
    ReportTemplateSerializer,
)

logger = logging.getLogger(__name__)


class SavedReportViewSet(viewsets.ModelViewSet):
    """CRUD operations for saved reports, plus export action."""
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ('create',):
            return SavedReportCreateSerializer
        return SavedReportSerializer

    def get_queryset(self):
        return SavedReport.objects.filter(
            user=self.request.user
        ).select_related('task')

    def create(self, request, *args, **kwargs):
        """Create a saved report, accepting task_id (UUID) instead of task (FK int)."""
        task_id = request.data.get('task_id')
        if task_id and 'task' not in request.data:
            from apps.research.models import ResearchTask
            try:
                task_obj = ResearchTask.objects.select_related('result').get(
                    task_id=task_id,
                    project__user=request.user,
                )
            except ResearchTask.DoesNotExist:
                return Response(
                    {'detail': 'Research task not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            # Build report_data from the research result
            report_data = {}
            if hasattr(task_obj, 'result') and task_obj.result:
                report_data = {
                    'report_markdown': task_obj.result.report_markdown or '',
                    'executive_summary': task_obj.result.executive_summary or '',
                    'swot_analysis': task_obj.result.swot_analysis or {},
                    'recommendations': task_obj.result.recommendations or [],
                }
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            data['task'] = task_obj.pk
            data['report_data'] = report_data
            data.setdefault('format', 'markdown')
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            headers = self.get_success_headers(serializer.data)
            return Response(
                SavedReportSerializer(serializer.instance, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='share')
    def share(self, request, pk=None):
        """Make a report public and return the share token/URL."""
        report = self.get_object()
        report.is_public = True
        report.save(update_fields=['is_public'])
        share_url = request.build_absolute_uri(
            f'/api/reports/shared/{report.share_token}/'
        )
        return Response({
            'share_token': str(report.share_token),
            'share_url': share_url,
        })

    @action(detail=True, methods=['get'], url_path='export/(?P<export_format>[a-z]+)')
    def export(self, request, pk=None, export_format=None):
        """Export a report in PDF or CSV format."""
        report = self.get_object()

        if export_format == 'csv':
            return self._export_csv(report)
        elif export_format == 'pdf':
            return self._export_pdf(report)
        elif export_format == 'html':
            return self._export_html(report)
        elif export_format in ('markdown', 'md'):
            return self._export_markdown(report)
        else:
            return Response(
                {'error': f'Unsupported export format: {export_format}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _export_csv(self, report):
        """Export report data as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        report_data = report.report_data or {}

        writer.writerow(['Section', 'Key', 'Value'])

        for section, data in report_data.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    writer.writerow([section, key, str(value)])
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    writer.writerow([section, f'item_{i}', str(item)])
            else:
                writer.writerow([section, '', str(data)])

        report.download_count += 1
        report.save(update_fields=['download_count'])

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report.title}.csv"'
        return response

    def _export_pdf(self, report):
        """Export report as PDF using ReportLab."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
            )

            report_data = report.report_data or {}
            md_content = report_data.get('report_markdown', '')

            if not md_content and hasattr(report.task, 'result'):
                md_content = report.task.result.report_markdown or ''

            if not md_content:
                md_content = f"# {report.title}\n\n{report.description or 'No content available.'}"

            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer, pagesize=A4,
                leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                topMargin=0.75 * inch, bottomMargin=0.75 * inch,
            )

            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                'ReportTitle', parent=styles['Title'],
                textColor=HexColor('#1a1a2e'), fontSize=22, spaceAfter=6,
            ))
            styles.add(ParagraphStyle(
                'ReportH2', parent=styles['Heading2'],
                textColor=HexColor('#16213e'), fontSize=16, spaceBefore=18, spaceAfter=8,
            ))
            styles.add(ParagraphStyle(
                'ReportH3', parent=styles['Heading3'],
                textColor=HexColor('#0f3460'), fontSize=13, spaceBefore=12, spaceAfter=6,
            ))
            styles.add(ParagraphStyle(
                'ReportBody', parent=styles['BodyText'],
                fontSize=10, leading=15, spaceAfter=8,
            ))
            styles.add(ParagraphStyle(
                'ReportBullet', parent=styles['BodyText'],
                fontSize=10, leading=15, leftIndent=20, bulletIndent=10,
                spaceAfter=4,
            ))

            story = []
            # Title
            story.append(Paragraph(report.title, styles['ReportTitle']))
            if report.description:
                story.append(Paragraph(report.description, styles['ReportBody']))
            story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#16213e')))
            story.append(Spacer(1, 12))

            # Parse markdown line by line
            for line in md_content.split('\n'):
                stripped = line.strip()
                if not stripped:
                    story.append(Spacer(1, 6))
                elif stripped.startswith('### '):
                    story.append(Paragraph(stripped[4:], styles['ReportH3']))
                elif stripped.startswith('## '):
                    story.append(Paragraph(stripped[3:], styles['ReportH2']))
                elif stripped.startswith('# '):
                    story.append(Paragraph(stripped[2:], styles['ReportTitle']))
                elif stripped.startswith(('- ', '* ', '• ')):
                    text = stripped[2:]
                    # Escape XML special chars for ReportLab
                    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(f"• {text}", styles['ReportBullet']))
                elif stripped.startswith('---'):
                    story.append(HRFlowable(width="100%", thickness=0.5))
                else:
                    # Escape XML special chars and handle bold/italic markdown
                    text = stripped.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
                    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
                    story.append(Paragraph(text, styles['ReportBody']))

            # Footer
            story.append(Spacer(1, 24))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#cccccc')))
            footer_style = ParagraphStyle(
                'Footer', parent=styles['Normal'],
                fontSize=8, textColor=HexColor('#666666'), alignment=1,
            )
            story.append(Paragraph("Generated by AI Market Research Assistant", footer_style))

            doc.build(story)

            report.download_count += 1
            report.save(update_fields=['download_count'])

            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
            return response

        except ImportError:
            logger.warning("reportlab not available, falling back to HTML export.")
            return self._export_html(report)
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return Response(
                {'error': 'PDF generation failed. Try Markdown or CSV export.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _export_html(self, report):
        """Export report as HTML."""
        report_data = report.report_data or {}
        md_content = report_data.get('report_markdown', '')

        if not md_content and hasattr(report.task, 'result'):
            md_content = report.task.result.report_markdown or ''

        html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

        report.download_count += 1
        report.save(update_fields=['download_count'])

        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="{report.title}.html"'
        return response

    def _export_markdown(self, report):
        """Export report as Markdown."""
        report_data = report.report_data or {}
        md_content = report_data.get('report_markdown', '')

        if not md_content and hasattr(report.task, 'result') and report.task.result:
            md_content = report.task.result.report_markdown or ''

        if not md_content:
            md_content = f"# {report.title}\n\n{report.description or 'No content available.'}"

        report.download_count += 1
        report.save(update_fields=['download_count'])

        response = HttpResponse(md_content, content_type='text/markdown')
        response['Content-Disposition'] = f'attachment; filename="{report.title}.md"'
        return response


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """CRUD operations for report templates."""
    permission_classes = [IsAuthenticated]
    serializer_class = ReportTemplateSerializer

    def get_queryset(self):
        from django.db.models import Q
        return ReportTemplate.objects.filter(
            Q(is_default=True) | Q(created_by=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ShareReportView(APIView):
    """Public endpoint to view a shared report by share token."""
    permission_classes = [AllowAny]

    def get(self, request, share_token):
        try:
            report = SavedReport.objects.select_related('task').get(
                share_token=share_token,
                is_public=True,
            )
        except SavedReport.DoesNotExist:
            return Response(
                {'error': 'Report not found or is not public.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(SavedReportSerializer(report, context={'request': request}).data)


class ExportReportView(APIView):
    """Generate and export a report in the requested format."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        task_id = request.data.get('task_id')
        export_format = request.data.get('format', 'html')
        title = request.data.get('title', 'Research Report')

        if not task_id:
            return Response(
                {'error': 'task_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.research.models import ResearchTask
        try:
            task = ResearchTask.objects.select_related('result').get(
                task_id=task_id,
                project__user=request.user,
            )
        except ResearchTask.DoesNotExist:
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not hasattr(task, 'result'):
            return Response(
                {'error': 'No results available for this task.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a saved report
        report = SavedReport.objects.create(
            user=request.user,
            task=task,
            title=title,
            report_data={
                'report_markdown': task.result.report_markdown,
                'executive_summary': task.result.executive_summary,
                'swot_analysis': task.result.swot_analysis,
                'recommendations': task.result.recommendations,
            },
            format=export_format,
        )

        return Response(
            SavedReportSerializer(report, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
