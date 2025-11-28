import trafilatura

def download_webpage(url: str):
    """
    Download a web page and extract all available information using trafilatura.
    
    Args:
        url: The URL of the web page to download
    
    """
    downloaded = trafilatura.fetch_url(url)
    
    metadata = trafilatura.extract_metadata(downloaded)
    
    json_output = trafilatura.extract(
        downloaded,
        include_comments=include_comments,
        include_tables=include_tables,
        output_format='json'
    )

    return json_output
    


if __name__ == '__main__':
    # Example usage
    url = 'https://example.com'
    result = download_webpage(url)
    
    if result.get('error'):
        print(f"Error: {result['error']}")
    else:
        print("Metadata:", result['metadata'])
        print("\nExtracted Text:", result['text'][:500] if result['text'] else None)
