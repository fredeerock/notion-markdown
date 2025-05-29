# Notion to Jekyll GitHub Pages

This project automatically syncs content from a Notion database to a Jekyll static site hosted on GitHub Pages. The sync happens every 5 minutes via GitHub Actions.

## Features

- 🔄 Automatic sync from Notion database to markdown files
- 📝 Supports paragraphs, headings, lists, to-dos, and images
- 🏠 Special "Home" page type for homepage content
- 🧭 Automatic navigation for pages marked as "Page" type
- 🗑️ **Automatic cleanup** - Deleted/renamed pages in Notion are removed from the site
- ⚡ Runs on GitHub Pages for free

## Setup Instructions

### 1. Fork or Clone This Repository

Fork this repository or use it as a template for your new GitHub repository.

### 2. Set Up Your Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Give it a name and select your workspace
4. Copy the **Internal Integration Token** (starts with `ntn_`)
5. In your Notion database:
   - Click the three dots menu (•••) in the top right
   - Go to "Connections" 
   - Add your integration

### 3. Get Your Notion Database ID

1. Open your Notion database in a web browser
2. Copy the database ID from the URL:
   ```
   https://notion.so/workspace/DATABASE_ID?v=...
   ```
   The `DATABASE_ID` is the 32-character string after your workspace name.

### 4. Configure GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these two secrets:

   - **Name**: `NOTION_DATABASE_ID`
   - **Value**: Your 32-character database ID

   - **Name**: `NOTION_TOKEN`  
   - **Value**: Your integration token (starts with `ntn_`)

### 5. Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under **Source**, select "Deploy from a branch"
3. Select **Branch**: `main` (or `master`)
4. Select **Folder**: `/ (root)`
5. Click **Save**

### 6. Set Up Your Notion Database

Your Notion database should have these properties:

- **Title** (Title property) - The page title
- **Type** (Select property) - Use these values:
  - `Home` - For your homepage content
  - `Page` - For pages that appear in navigation
  - Other values for pages that don't appear in navigation

### 7. Trigger the First Sync

1. Go to **Actions** tab in your GitHub repository
2. Click on "Sync Notion to Markdown" workflow
3. Click **Run workflow** → **Run workflow**
4. Wait for it to complete (should take 1-2 minutes)

### 8. View Your Site

Your site will be available at: `https://YOUR_USERNAME.github.io/YOUR_REPOSITORY_NAME`

## How It Works

1. **GitHub Action** runs every 5 minutes and fetches your Notion database
2. **Python script** converts Notion pages to markdown files:
   - Pages with Type "Home" become `index.md` (homepage)
   - Pages with Type "Page" go in `_pages/` folder and appear in navigation
   - Other pages go in `_pages/` but don't appear in navigation
   - **Automatically removes** old markdown files when pages are deleted/renamed in Notion
3. **Jekyll** builds the static site from markdown files
4. **GitHub Pages** serves your site

## Content Management

### Adding Pages
- Create new pages in your Notion database
- Set the "Type" property to "Home" or "Page" as needed
- Content appears on your site within 5 minutes

### Updating Pages
- Edit content directly in Notion
- Changes sync automatically to your site

### Deleting/Renaming Pages
- When you delete a page from Notion, it's automatically removed from your site
- When you rename a page in Notion, the old file is deleted and a new one is created
- This prevents orphaned content from cluttering your site

## Customization

### Change Sync Frequency

Edit `.github/workflows/notion-sync.yml` and modify the cron schedule:

```yaml
schedule:
  - cron: '*/5 * * * *'  # Every 5 minutes
  # - cron: '*/15 * * * *'  # Every 15 minutes
  # - cron: '0 * * * *'     # Every hour
```

### Customize Styling

Edit `_layouts/default.html` to change the appearance of your site.

### Add More Block Types

Edit `.github/scripts/notion_to_markdown.py` to support additional Notion block types (quotes, code blocks, etc.).

## Troubleshooting

### Action Fails with "KeyError"
- Check that your Notion database has a "Title" property (not "Name")
- Verify your `NOTION_DATABASE_ID` and `NOTION_TOKEN` secrets are correct

### Pages Don't Appear in Navigation
- Make sure pages have `Type` set to "Page" in your Notion database
- Re-run the sync action

### Site Shows Directory Listing
- Ensure you have a page with Type "Home" in your Notion database
- Check that the action completed successfully

### Need Help?
Create an issue in this repository with details about your problem.

## License

MIT License - feel free to use this for your own projects!
