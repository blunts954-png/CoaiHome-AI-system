from auto_build_shopify_store import AutomaticShopifyBuilder

def test_stripping():
    builder = AutomaticShopifyBuilder()
    test_data = {
        "text": "<p>Hello World</p>",
        "list": ["<h1>Title</h1>", "No tags"],
        "nested": {
            "val": "<ul><li>Item</li></ul>"
        }
    }
    cleaned = builder._strip_html(test_data)
    print(f"Cleaned: {cleaned}")
    
    # Check if tags remain
    import json
    if "<" in json.dumps(cleaned):
        print("❌ Still contains tags!")
    else:
        print("✅ No tags remaining.")

if __name__ == "__main__":
    test_stripping()
