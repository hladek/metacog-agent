import trafilatura
import sys

def download_webpage(url: str):
    """
    Download a web page and extract all available information using trafilatura.
    
    Args:
        url: The URL of the web page to download
    
    """
    downloaded = trafilatura.fetch_url(url)
    #print(downloaded)
    
    metadata = trafilatura.extract_metadata(downloaded)
    print(metadata.as_dict())

    #comments = trafilatura.extract_comments(downloaded)
    #print(comments)

    
    json_output = trafilatura.extract(
        downloaded,
        include_comments=True,
        include_tables=True,
        output_format='json'
    )

    return json_output
    


if __name__ == '__main__':
    # Example usage
    url = sys.argv[1]
    import trafilatura.sitemaps
    import trafilatura.feeds
    sitemap =  trafilatura.sitemaps.sitemap_search(url)
    print(sitemap)
    feeds = trafilatura.feeds.find_feed_urls(url)
    result = download_webpage(url)
    print(result)
    
    #if result.get('error'):
    #    print(f"Error: {result['error']}")
    #else:
    print("Metadata:", result['metadata'])
    print("\nExtracted Text:", result['text'][:500] if result['text'] else None)
