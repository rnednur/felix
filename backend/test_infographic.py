"""
Test script for infographic generation

Run with: python test_infographic.py
"""

import sys
import base64
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.infographic_service import InfographicService


def test_infographic_generation():
    """Test infographic generation with sample data"""

    # Sample research result (mimicking output from DeepResearchService)
    sample_research_result = {
        'research_id': 'test_research_001',
        'main_question': 'What are the key trends in sales performance over the last quarter?',
        'sub_questions_count': 8,
        'direct_answer': 'Sales performance showed a 23% increase over Q3, driven primarily by strong performance in the Technology and Healthcare segments. The EMEA region showed the highest growth at 35%, while North America remained stable with 12% growth. Customer acquisition costs decreased by 15%, indicating improved marketing efficiency.',
        'key_findings': [
            'Total revenue increased by 23% YoY, reaching $4.2M in Q3 2024',
            'Technology segment contributed 45% of total revenue, up from 38% in Q2',
            'Customer retention rate improved to 87%, the highest in company history',
            'Average deal size grew by 18%, from $12,500 to $14,750',
            'Sales cycle time decreased by 22%, from 45 days to 35 days',
            'Top 3 products accounted for 68% of total revenue',
            'Marketing ROI improved by 31% compared to previous quarter'
        ],
        'supporting_details': [
            {
                'question': 'What was the total revenue?',
                'method': 'sql',
                'success': True,
                'data': {'sql': 'SELECT SUM(revenue) FROM sales', 'rows': 1, 'preview': [{'sum': 4200000}]}
            },
            {
                'question': 'Which segment performed best?',
                'method': 'sql',
                'success': True,
                'data': {'sql': 'SELECT segment, SUM(revenue) FROM sales GROUP BY segment', 'rows': 3}
            },
            {
                'question': 'What are the sales trends?',
                'method': 'python',
                'success': True,
                'data': {'trend': 'increasing', 'growth_rate': 0.23}
            }
        ],
        'data_coverage': {
            'questions_answered': 7,
            'total_questions': 8,
            'gaps': ['Regional breakdown by product category not available'],
            'methods_used': ['sql', 'python']
        },
        'follow_up_questions': [
            'What specific products drove the Technology segment growth?',
            'How does customer retention vary by region?',
            'What marketing channels contributed most to the improved ROI?',
            'Are there seasonal patterns in the sales data?',
            'What is the projected growth for Q4 based on current trends?'
        ],
        'visualizations': [],
        'stages_completed': [
            'Question decomposition',
            'Schema mapping',
            'Query execution',
            'Knowledge enrichment',
            'Insight synthesis',
            'Follow-up generation'
        ],
        'execution_time_seconds': 12.45,
        'execution_summary': {
            'total_queries': 8,
            'successful': 7,
            'failed': 1,
            'methods_used': ['sql', 'python']
        }
    }

    print("=" * 80)
    print("Testing Infographic Generation")
    print("=" * 80)

    # Test PDF generation with different color schemes
    for color_scheme in ['professional', 'modern', 'corporate']:
        print(f"\n📊 Generating {color_scheme} PDF infographic...")

        try:
            service = InfographicService(template=color_scheme)

            result = service.generate_infographic(
                research_result=sample_research_result,
                format='pdf',
                include_charts=True,
                include_visualizations=False
            )

            print(f"✅ Success!")
            print(f"   Filename: {result['filename']}")
            print(f"   Size: {result['size_bytes']:,} bytes")
            print(f"   Format: {result['format']}")

            # Save to file for inspection
            output_dir = Path(__file__).parent / 'test_outputs'
            output_dir.mkdir(exist_ok=True)

            output_file = output_dir / f"infographic_{color_scheme}.pdf"
            pdf_bytes = base64.b64decode(result['data'])

            with open(output_file, 'wb') as f:
                f.write(pdf_bytes)

            print(f"   Saved to: {output_file}")

        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            import traceback
            traceback.print_exc()

    # Test PNG generation
    print(f"\n📊 Generating PNG infographic...")

    try:
        service = InfographicService(template='professional')

        result = service.generate_infographic(
            research_result=sample_research_result,
            format='png',
            include_charts=True,
            include_visualizations=False
        )

        print(f"✅ Success!")
        print(f"   Filename: {result['filename']}")
        print(f"   Size: {result['size_bytes']:,} bytes")
        print(f"   Format: {result['format']}")

        # Save to file
        output_dir = Path(__file__).parent / 'test_outputs'
        output_file = output_dir / "infographic_professional.png"
        png_bytes = base64.b64decode(result['data'])

        with open(output_file, 'wb') as f:
            f.write(png_bytes)

        print(f"   Saved to: {output_file}")

    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("✅ Infographic generation tests complete!")
    print(f"📁 Check output files in: {output_dir}")
    print("=" * 80)


if __name__ == '__main__':
    test_infographic_generation()
