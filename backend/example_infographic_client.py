"""
Example client for infographic generation

This demonstrates how to use the infographic API endpoints from a client application.
"""

import httpx
import base64
import asyncio
from pathlib import Path


async def example_generate_infographic_from_research():
    """Example 1: Generate infographic from existing research results"""

    print("=" * 80)
    print("Example 1: Generate Infographic from Research Results")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Run deep research
        print("\n📊 Step 1: Running deep research...")

        research_response = await client.post(
            "http://localhost:8000/deep-research/analyze",
            json={
                "dataset_id": "your_dataset_id_here",
                "question": "What are the key sales trends and patterns?",
                "max_sub_questions": 10,
                "enable_python": True,
                "enable_world_knowledge": True
            }
        )

        if research_response.status_code != 200:
            print(f"❌ Research failed: {research_response.text}")
            return

        research_result = research_response.json()
        print(f"✅ Research complete!")
        print(f"   Direct Answer: {research_result['direct_answer'][:100]}...")

        # Step 2: Generate infographic
        print("\n📊 Step 2: Generating infographic...")

        infographic_response = await client.post(
            "http://localhost:8000/deep-research/generate-infographic",
            json={
                "research_result": research_result,
                "infographic_request": {
                    "format": "pdf",
                    "color_scheme": "professional",
                    "include_charts": True,
                    "include_visualizations": True
                }
            }
        )

        if infographic_response.status_code != 200:
            print(f"❌ Infographic generation failed: {infographic_response.text}")
            return

        infographic_result = infographic_response.json()

        if not infographic_result['success']:
            print(f"❌ Error: {infographic_result.get('error')}")
            return

        print(f"✅ Infographic generated!")
        print(f"   Filename: {infographic_result['filename']}")
        print(f"   Size: {infographic_result['size_bytes']:,} bytes")

        # Step 3: Save to file
        output_dir = Path("downloads")
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / infographic_result['filename']
        pdf_bytes = base64.b64decode(infographic_result['data'])

        with open(output_file, 'wb') as f:
            f.write(pdf_bytes)

        print(f"💾 Saved to: {output_file}")


async def example_analyze_with_infographic():
    """Example 2: All-in-one - Research + Infographic"""

    print("\n" + "=" * 80)
    print("Example 2: Analyze with Infographic (All-in-One)")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=120.0) as client:
        print("\n📊 Running analysis and generating infographic...")

        response = await client.post(
            "http://localhost:8000/deep-research/analyze-with-infographic",
            json={
                "dataset_id": "your_dataset_id_here",
                "question": "What are the key sales trends and patterns?",
                "max_sub_questions": 10,
                "enable_python": True,
                "enable_world_knowledge": True,
                "format": "pdf",
                "color_scheme": "corporate",
                "include_charts": True,
                "include_visualizations": True
            }
        )

        if response.status_code != 200:
            print(f"❌ Request failed: {response.text}")
            return

        result = response.json()

        if not result['success']:
            print(f"❌ Error in processing")
            return

        print(f"✅ Analysis complete!")

        # Access research results
        research = result['research']
        print(f"\n📋 Research Results:")
        print(f"   Question: {research['main_question']}")
        print(f"   Answer: {research['direct_answer'][:100]}...")
        print(f"   Key Findings: {len(research['key_findings'])} findings")
        print(f"   Execution Time: {research['execution_time_seconds']:.2f}s")

        # Access infographic
        infographic = result['infographic']
        print(f"\n🎨 Infographic:")
        print(f"   Filename: {infographic['filename']}")
        print(f"   Format: {infographic['format']}")
        print(f"   Size: {infographic['size_bytes']:,} bytes")

        # Save infographic
        output_dir = Path("downloads")
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / infographic['filename']
        pdf_bytes = base64.b64decode(infographic['data'])

        with open(output_file, 'wb') as f:
            f.write(pdf_bytes)

        print(f"💾 Saved to: {output_file}")


async def example_multiple_formats():
    """Example 3: Generate infographic in multiple formats"""

    print("\n" + "=" * 80)
    print("Example 3: Generate Multiple Format Infographics")
    print("=" * 80)

    # First get research result
    async with httpx.AsyncClient(timeout=120.0) as client:
        research_response = await client.post(
            "http://localhost:8000/deep-research/analyze",
            json={
                "dataset_id": "your_dataset_id_here",
                "question": "What are the key sales trends?",
                "max_sub_questions": 5
            }
        )

        if research_response.status_code != 200:
            print(f"❌ Research failed")
            return

        research_result = research_response.json()

        # Generate in different formats and color schemes
        formats = [
            ("pdf", "professional"),
            ("pdf", "modern"),
            ("pdf", "corporate"),
            ("png", "professional")
        ]

        for format_type, color_scheme in formats:
            print(f"\n📊 Generating {format_type} with {color_scheme} theme...")

            infographic_response = await client.post(
                "http://localhost:8000/deep-research/generate-infographic",
                json={
                    "research_result": research_result,
                    "infographic_request": {
                        "format": format_type,
                        "color_scheme": color_scheme,
                        "include_charts": True,
                        "include_visualizations": False
                    }
                }
            )

            if infographic_response.status_code == 200:
                result = infographic_response.json()
                if result['success']:
                    # Save file
                    output_dir = Path("downloads")
                    output_dir.mkdir(exist_ok=True)

                    filename = f"infographic_{color_scheme}.{format_type}"
                    output_file = output_dir / filename

                    file_bytes = base64.b64decode(result['data'])
                    with open(output_file, 'wb') as f:
                        f.write(file_bytes)

                    print(f"✅ Saved: {output_file} ({result['size_bytes']:,} bytes)")
                else:
                    print(f"❌ Failed: {result.get('error')}")
            else:
                print(f"❌ HTTP Error: {infographic_response.status_code}")


async def main():
    """Run all examples"""

    print("\n🚀 Infographic Generation Examples\n")

    # Note: Replace 'your_dataset_id_here' with an actual dataset ID
    # You can get dataset IDs by calling GET /datasets

    try:
        # Uncomment the example you want to run:

        # await example_generate_infographic_from_research()
        # await example_analyze_with_infographic()
        # await example_multiple_formats()

        print("\n⚠️  Note: Update 'your_dataset_id_here' with a real dataset ID")
        print("📝 Then uncomment an example in main() to run it")

    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to backend")
        print("   Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
