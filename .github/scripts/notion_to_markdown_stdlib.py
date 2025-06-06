#!/usr/bin/env python3
"""
Notion to Markdown sync script using only Python standard library.
No external dependencies required.
"""

import os
import glob
import json
import urllib.request
import urllib.parse
import urllib.error
import re
from typing import Dict, List, Any, Optional


def load_env_file(filepath: str = ".env") -> None:
    """Load environment variables from .env file if it exists."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')


def make_notion_request(url: str, headers: Dict[str, str], data: Optional[str] = None) -> Dict[str, Any]:
    """Make a request to the Notion API."""
    req = urllib.request.Request(url, headers=headers)
    if data:
        req.data = data.encode('utf-8')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Notion API Error: {e.code} - {error_body}")
        raise


def get_database_pages(database_id: str, notion_token: str) -> List[Dict[str, Any]]:
    """Fetch all pages from a Notion database."""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    all_pages = []
    has_more = True
    next_cursor = None
    
    while has_more:
        data = {}
        if next_cursor:
            data["start_cursor"] = next_cursor
        
        # Always send POST data, even if empty
        post_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=post_data, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Notion API Error: {e.code} - {error_body}")
            raise
        
        all_pages.extend(response_data.get("results", []))
        has_more = response_data.get("has_more", False)
        next_cursor = response_data.get("next_cursor")
    
    return all_pages


def get_page_content(page_id: str, notion_token: str) -> List[Dict[str, Any]]:
    """Fetch the content blocks of a Notion page."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28"
    }
    
    all_blocks = []
    has_more = True
    next_cursor = None
    
    while has_more:
        query_url = url
        if next_cursor:
            query_url += f"?start_cursor={next_cursor}"
        
        response = make_notion_request(query_url, headers)
        all_blocks.extend(response.get("results", []))
        has_more = response.get("has_more", False)
        next_cursor = response.get("next_cursor")
    
    return all_blocks


def extract_rich_text(rich_text_array: List[Dict[str, Any]]) -> str:
    """Extract plain text from Notion rich text array."""
    if not rich_text_array:
        return ""
    
    result = ""
    for text_obj in rich_text_array:
        if text_obj.get("type") == "text":
            content = text_obj.get("text", {}).get("content", "")
            annotations = text_obj.get("annotations", {})
            
            # Apply formatting
            if annotations.get("bold"):
                content = f"**{content}**"
            if annotations.get("italic"):
                content = f"*{content}*"
            if annotations.get("code"):
                content = f"`{content}`"
            if annotations.get("strikethrough"):
                content = f"~~{content}~~"
            
            # Handle links
            if text_obj.get("text", {}).get("link"):
                link_url = text_obj["text"]["link"]["url"]
                content = f"[{content}]({link_url})"
            
            result += content
    
    return result


def block_to_markdown(block: Dict[str, Any]) -> str:
    """Convert a Notion block to markdown."""
    block_type = block.get("type", "")
    
    if block_type == "paragraph":
        text = extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
        return text + "\n\n" if text else ""
    
    elif block_type == "heading_1":
        text = extract_rich_text(block.get("heading_1", {}).get("rich_text", []))
        return f"# {text}\n\n" if text else ""
    
    elif block_type == "heading_2":
        text = extract_rich_text(block.get("heading_2", {}).get("rich_text", []))
        return f"## {text}\n\n" if text else ""
    
    elif block_type == "heading_3":
        text = extract_rich_text(block.get("heading_3", {}).get("rich_text", []))
        return f"### {text}\n\n" if text else ""
    
    elif block_type == "bulleted_list_item":
        text = extract_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
        return f"- {text}\n" if text else ""
    
    elif block_type == "numbered_list_item":
        text = extract_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
        return f"1. {text}\n" if text else ""
    
    elif block_type == "to_do":
        text = extract_rich_text(block.get("to_do", {}).get("rich_text", []))
        checked = block.get("to_do", {}).get("checked", False)
        checkbox = "[x]" if checked else "[ ]"
        return f"- {checkbox} {text}\n" if text else ""
    
    elif block_type == "quote":
        text = extract_rich_text(block.get("quote", {}).get("rich_text", []))
        return f"> {text}\n\n" if text else ""
    
    elif block_type == "code":
        text = extract_rich_text(block.get("code", {}).get("rich_text", []))
        language = block.get("code", {}).get("language", "")
        return f"```{language}\n{text}\n```\n\n" if text else ""
    
    elif block_type == "divider":
        return "---\n\n"
    
    elif block_type == "image":
        image_data = block.get("image", {})
        if image_data.get("type") == "external":
            url = image_data.get("external", {}).get("url", "")
            caption = extract_rich_text(image_data.get("caption", []))
            # Extract filename from URL for alt text if no caption
            if not caption and url:
                # Get filename from URL, remove query parameters and file extension
                import re
                filename = url.split('/')[-1].split('?')[0]
                filename = re.sub(r'\.[^.]*$', '', filename)  # Remove extension
                alt_text = filename
            else:
                alt_text = caption if caption else "Image"
            return f"![{alt_text}]({url})\n\n" if url else ""
        elif image_data.get("type") == "file":
            url = image_data.get("file", {}).get("url", "")
            caption = extract_rich_text(image_data.get("caption", []))
            # Extract filename from URL for alt text if no caption
            if not caption and url:
                import re
                filename = url.split('/')[-1].split('?')[0]
                filename = re.sub(r'\.[^.]*$', '', filename)  # Remove extension
                alt_text = filename
            else:
                alt_text = caption if caption else "Image"
            return f"![{alt_text}]({url})\n\n" if url else ""
    
    # For unsupported block types, try to extract any rich text
    for key in block.keys():
        if isinstance(block[key], dict) and "rich_text" in block[key]:
            text = extract_rich_text(block[key]["rich_text"])
            if text:
                return f"{text}\n\n"
    
    return ""


def page_to_markdown(page_id: str, notion_token: str, page_title: str = "") -> str:
    """Convert a Notion page to markdown content."""
    blocks = get_page_content(page_id, notion_token)
    markdown_content = ""
    
    # Add page title as H1 if we have one
    if page_title and page_title != "Untitled":
        markdown_content += f"# {page_title}\n\n"
    
    for block in blocks:
        markdown_content += block_to_markdown(block)
    
    return markdown_content.strip()


def get_page_property_value(page_properties: Dict[str, Any], property_name: str) -> str:
    """Extract a property value from a Notion page."""
    prop = page_properties.get(property_name, {})
    prop_type = prop.get("type", "")
    
    if prop_type == "title":
        title_array = prop.get("title", [])
        return extract_rich_text(title_array)
    
    elif prop_type == "rich_text":
        rich_text_array = prop.get("rich_text", [])
        return extract_rich_text(rich_text_array)
    
    elif prop_type == "select":
        select_obj = prop.get("select")
        return select_obj.get("name", "") if select_obj else ""
    
    elif prop_type == "multi_select":
        multi_select_array = prop.get("multi_select", [])
        return ", ".join([item.get("name", "") for item in multi_select_array])
    
    elif prop_type == "number":
        return str(prop.get("number", ""))
    
    elif prop_type == "checkbox":
        return "true" if prop.get("checkbox") else "false"
    
    elif prop_type == "date":
        date_obj = prop.get("date")
        if date_obj:
            return date_obj.get("start", "")
    
    return ""


def create_file_content(title: str, type_val: str, content: str) -> str:
    """Generate Jekyll front matter and content."""
    front_matter = f"---\ntitle: {title}\nlayout: default\ntype: {type_val}"
    if type_val == "Home":
        front_matter += "\nnav_exclude: true"
    else:
        permalink = re.sub(r'[^a-zA-Z0-9_]', '_', title.lower())
        front_matter += f"\npermalink: /{permalink}/"
    return f"{front_matter}\n---\n\n{content}"


def main():
    """Main function to sync Notion database to markdown files."""
    # Load environment variables
    load_env_file()
    
    NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
    NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
    
    if not NOTION_DATABASE_ID or not NOTION_TOKEN:
        print("Error: NOTION_DATABASE_ID and NOTION_TOKEN environment variables are required")
        return
    
    # Create pages directory
    os.makedirs("_pages", exist_ok=True)
    
    # Track expected files for cleanup
    expected_files = set()
    has_home_page = False
    
    try:
        # Get all pages from the database
        pages = get_database_pages(NOTION_DATABASE_ID, NOTION_TOKEN)
        
        for page in pages:
            # Extract page title
            title = get_page_property_value(page.get("properties", {}), "Name")
            if not title:
                # Fallback to title property if Name doesn't exist
                for prop_name, prop_data in page.get("properties", {}).items():
                    if prop_data.get("type") == "title":
                        title = get_page_property_value(page["properties"], prop_name)
                        break
            
            if not title:
                title = "Untitled"
            
            # Extract Type property
            type_val = get_page_property_value(page.get("properties", {}), "Type")
            
            # Convert page content to markdown
            content = page_to_markdown(page["id"], NOTION_TOKEN, title)
            
            # Create appropriate file
            if type_val == "Home":
                file_path = "index.md"
                expected_files.add(file_path)
                has_home_page = True
            else:
                filename = f"{re.sub(r'[^a-zA-Z0-9_]', '_', title.lower())}.md"
                file_path = f"_pages/{filename}"
                expected_files.add(file_path)
            
            # Write file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(create_file_content(title, type_val, content))
            
            print(f"Created: {file_path} ({type_val})")
        
        # Clean up orphaned files
        existing_files = set(glob.glob("_pages/*.md"))
        for file_path in existing_files:
            if file_path not in expected_files:
                print(f"Removing: {file_path}")
                os.remove(file_path)
        
        # Remove index.md if no Home page exists
        if os.path.exists("index.md") and not has_home_page:
            print("Removing: index.md (no Home page)")
            os.remove("index.md")
        
        print("Sync complete!")
        
    except Exception as e:
        print(f"Error during sync: {e}")
        raise


if __name__ == "__main__":
    main()
