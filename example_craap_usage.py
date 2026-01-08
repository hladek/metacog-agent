"""
Example usage of the CRAAP API.

This script demonstrates various ways to use the CRAAP API for blog analysis.
"""

import asyncio
import json
from craap_api import (
    analyze_blog,
    analyze_blog_sync,
    analyze_blog_batch,
    print_analysis_report,
    CRAAPAnalysisResult
)


def example_1_basic_sync():
    """Example 1: Basic synchronous analysis."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Synchronous Analysis")
    print("="*80)
    
    url = "https://example.com/blog-post"
    result = analyze_blog_sync(url, analyze_author=False, analyze_publisher=False)
    print_analysis_report(result)


async def example_2_async_with_authority():
    """Example 2: Async analysis with full authority checks."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Async Analysis with Authority Checks")
    print("="*80)
    
    url = "https://example.com/blog-post"
    result = await analyze_blog(url, analyze_author=True, analyze_publisher=True)
    print_analysis_report(result)


async def example_3_batch_analysis():
    """Example 3: Batch analysis of multiple blogs."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Batch Analysis")
    print("="*80)
    
    urls = [
        "https://blog1.com/post",
        "https://blog2.com/article",
        "https://blog3.com/story"
    ]
    
    results = await analyze_blog_batch(
        urls, 
        analyze_author=False,
        analyze_publisher=False
    )
    
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"\n[{i}] Error: {result}")
        else:
            print(f"\n[{i}] {result.url}")
            print(f"    Author: {result.metadata.author_name}")
            print(f"    Publisher: {result.metadata.publisher_name}")
            print(f"    Has Sources: {result.accuracy.has_sources}")


def example_4_export_to_json():
    """Example 4: Export analysis to JSON."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Export to JSON")
    print("="*80)
    
    url = "https://example.com/blog-post"
    result = analyze_blog_sync(url, analyze_author=False, analyze_publisher=False)
    
    # Convert to dictionary
    data = result.to_dict()
    
    # Export to JSON
    json_str = json.dumps(data, indent=2, default=str)
    print(json_str[:500] + "...")
    
    # Save to file
    with open("craap_analysis.json", "w") as f:
        f.write(json_str)
    print("\nSaved to craap_analysis.json")


async def example_5_custom_scoring():
    """Example 5: Custom credibility scoring."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Custom Credibility Scoring")
    print("="*80)
    
    url = "https://example.com/blog-post"
    result = await analyze_blog(url, analyze_author=False, analyze_publisher=False)
    
    # Custom scoring logic
    score = 0
    max_score = 10
    
    # Currency (2 points)
    if result.currency.is_maintained:
        score += 1
    if result.currency.has_recent_references:
        score += 1
    
    # Accuracy (3 points)
    if result.accuracy.has_sources:
        score += 1
    if result.accuracy.verifiable:
        score += 1
    if result.accuracy.error_free:
        score += 1
    
    # Authority (2 points)
    if not result.metadata.is_anonymous:
        score += 1
    if result.metadata.author_affiliation != "Unknown":
        score += 1
    
    # Purpose (3 points)
    if "objective" in result.purpose.tone.lower():
        score += 1
    if "none" in result.purpose.bias.lower():
        score += 1
    if "none" in result.purpose.hate.lower():
        score += 1
    
    # Calculate credibility
    credibility_percent = (score / max_score) * 100
    
    print(f"\nURL: {url}")
    print(f"Credibility Score: {score}/{max_score} ({credibility_percent:.0f}%)")
    print(f"\nBreakdown:")
    print(f"  Currency: {'✓' if result.currency.is_maintained else '✗'} Maintained")
    print(f"  Currency: {'✓' if result.currency.has_recent_references else '✗'} Recent references")
    print(f"  Accuracy: {'✓' if result.accuracy.has_sources else '✗'} Has sources")
    print(f"  Accuracy: {'✓' if result.accuracy.verifiable else '✗'} Verifiable")
    print(f"  Accuracy: {'✓' if result.accuracy.error_free else '✗'} Error free")
    print(f"  Authority: {'✓' if not result.metadata.is_anonymous else '✗'} Not anonymous")
    print(f"  Authority: {'✓' if result.metadata.author_affiliation != 'Unknown' else '✗'} Has affiliation")
    print(f"  Purpose: {'✓' if 'objective' in result.purpose.tone.lower() else '✗'} Objective tone")
    print(f"  Purpose: {'✓' if 'none' in result.purpose.bias.lower() else '✗'} No bias")
    print(f"  Purpose: {'✓' if 'none' in result.purpose.hate.lower() else '✗'} No hate speech")
    
    if credibility_percent >= 80:
        print(f"\n✅ HIGH CREDIBILITY - Recommended source")
    elif credibility_percent >= 50:
        print(f"\n⚠️  MEDIUM CREDIBILITY - Use with caution")
    else:
        print(f"\n❌ LOW CREDIBILITY - Not recommended")


async def example_6_selective_analysis():
    """Example 6: Run only specific analyses."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Selective Analysis (Currency and Accuracy only)")
    print("="*80)
    
    from craap_api import (
        download_blog,
        analyze_currency,
        analyze_accuracy
    )
    
    url = "https://example.com/blog-post"
    
    # Download content
    text, metadata = download_blog(url)
    
    if text:
        # Run only specific analyses
        currency = await analyze_currency(text)
        accuracy = await analyze_accuracy(text)
        
        print(f"\nURL: {url}")
        print(f"\n📅 Currency:")
        print(f"  Published: {currency.published_date}")
        print(f"  Last Updated: {currency.last_updated}")
        print(f"  Is Maintained: {currency.is_maintained}")
        
        print(f"\n✓ Accuracy:")
        print(f"  Has Sources: {accuracy.has_sources}")
        print(f"  Verifiable: {accuracy.verifiable}")
        print(f"  Error Free: {accuracy.error_free}")


def example_7_error_handling():
    """Example 7: Proper error handling."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Error Handling")
    print("="*80)
    
    urls = [
        "https://valid-blog.com/post",
        "https://invalid-url-that-does-not-exist.com/post",
        "https://another-valid.com/article"
    ]
    
    for url in urls:
        try:
            result = analyze_blog_sync(
                url,
                analyze_author=False,
                analyze_publisher=False
            )
            print(f"✅ Success: {url}")
            print(f"   Author: {result.metadata.author_name}")
        except ValueError as e:
            print(f"❌ Download Error: {url}")
            print(f"   {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {url}")
            print(f"   {type(e).__name__}: {e}")


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("CRAAP API - Usage Examples")
    print("="*80)
    
    # Uncomment the examples you want to run:
    
    # example_1_basic_sync()
    # await example_2_async_with_authority()
    # await example_3_batch_analysis()
    # example_4_export_to_json()
    # await example_5_custom_scoring()
    # await example_6_selective_analysis()
    # example_7_error_handling()
    
    print("\n✅ Examples completed!")
    print("\nTo run specific examples, uncomment them in the main() function.")


if __name__ == "__main__":
    # For running individual examples from command line
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num == "1":
            example_1_basic_sync()
        elif example_num == "4":
            example_4_export_to_json()
        elif example_num == "7":
            example_7_error_handling()
        else:
            asyncio.run(main())
    else:
        print("\nUsage: python example_craap_usage.py [1-7]")
        print("Or edit main() to uncomment specific examples")
