import urllib.request
import json
import re
import os
import ssl

def fetch_stayingahead_resources():
    print("Fetching StayingAhead.ai CMS updates...")
    resources = []
    
    # Bypass SSL verification if needed for GitHub Actions environment compatibility
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 1. Fetch Dispatches (Blogs & Cheat Sheets)
    try:
        url = "https://payloadcms.stayingahead.ai/api/dispatches?limit=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            for doc in data.get('docs', []):
                title = doc.get('title', '')
                if not title:
                    continue
                # Parse description/excerpt
                desc = doc.get('excerpt', '') or doc.get('description', '')
                if isinstance(desc, dict):
                    desc_text = ""
                    for node in desc.get('root', {}).get('children', []):
                        for child in node.get('children', []):
                            desc_text += child.get('text', '')
                    desc = desc_text
                
                # Default values if empty
                if not desc:
                    desc = "Vetted cheat sheet and prompting workbook compiled by the Staying Ahead community."
                
                resources.append({
                    'title': title,
                    'category': 'Cheat Sheet' if 'cheatsheet' in title.lower() or 'guide' in title.lower() else 'AI Dispatch',
                    'description': desc,
                    'bullets': [
                        "Vetted and curated directly from the Staying Ahead community library.",
                        "Optimized prompt templates and implementation blueprints included.",
                        f"Published: {doc.get('createdAt', '')[:10]}"
                    ],
                    'icon': 'terminal' if 'code' in title.lower() or 'command' in title.lower() else 'sparkles'
                })
    except Exception as e:
        print(f"Error fetching stayingahead dispatches: {e}")

    # 2. Fetch Mappings (Video resources)
    try:
        url = "https://payloadcms.stayingahead.ai/api/video-resource-mappings?limit=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            for doc in data.get('docs', []):
                title = doc.get('title', '')
                if not title:
                    continue
                desc = doc.get('description', '')
                if not desc:
                    desc = "Step-by-step developer implementation walkthrough and blueprint mapping."
                
                resources.append({
                    'title': title,
                    'category': 'Resource Blueprint',
                    'description': desc,
                    'bullets': [
                        f"CTA: {doc.get('ctaText', 'Grab the resource').strip()}",
                        "Directly mapped to community tutorials and developer reviews.",
                        f"Indexed: {doc.get('createdAt', '')[:10]}"
                    ],
                    'icon': 'layers'
                })
    except Exception as e:
        print(f"Error fetching stayingahead mappings: {e}")
        
    return resources

def fetch_hackernews_ai_resources():
    print("Fetching Hacker News API for trending AI/LLM topics...")
    resources = []
    try:
        # Fetch top stories
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            top_ids = json.loads(response.read().decode('utf-8'))
            
        count = 0
        for story_id in top_ids[:150]:  # Scan top 150 stories
            if count >= 3:  # We only need at most 3 relevant stories
                break
                
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            req_story = urllib.request.Request(story_url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req_story) as resp_story:
                    story = json.loads(resp_story.read().decode('utf-8'))
                    title = story.get('title', '')
                    
                    # Match AI-related keywords
                    if any(kw in title.lower() for kw in [' ai ', 'llm', 'gpt', 'openai', 'claude', 'deepseek', 'machine learning', 'neural', 'transformer']):
                        link = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                        score = story.get('score', 0)
                        author = story.get('by', 'HN')
                        
                        resources.append({
                            'title': title,
                            'category': 'Trending Tech',
                            'description': f"Trending AI development, research paper, or codebase launch popular on Hacker News (Score: {score} points).",
                            'bullets': [
                                f"Author/Reporter: {author}",
                                f"Resource Link: {link}",
                                f"Discussion Thread: https://news.ycombinator.com/item?id={story_id}"
                            ],
                            'icon': 'trending-up'
                        })
                        count += 1
            except Exception:
                pass
    except Exception as e:
        print(f"Error fetching Hacker News: {e}")
    return resources

def generate_card_html(res):
    # Map category strings to icon names
    icon_map = {
        'terminal': 'terminal',
        'sparkles': 'sparkles',
        'layers': 'layers',
        'trending-up': 'trending-up',
        'coins': 'coins',
        'refresh-cw': 'refresh-cw',
        'image': 'image'
    }
    icon_name = icon_map.get(res['icon'], 'sparkles')
    
    # Escape quotes for safety
    title_esc = res['title'].replace('"', '&quot;')
    desc_esc = res['description'].replace('"', '&quot;')
    
    bullets_html = ""
    for b in res['bullets']:
        # Format links inside bullets
        b_formatted = re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank" rel="noopener" class="text-amber-500 hover:underline inline-flex items-center gap-0.5 font-medium">\1 <i data-lucide="external-link" class="w-3 h-3 inline"></i></a>', b)
        bullets_html += f"                                <li>{b_formatted}</li>\n"
        
    card = f"""                        <!-- Auto-generated Card: {title_esc} -->
                        <div class="cyber-card p-5 rounded-2xl space-y-3">
                            <div class="flex justify-between items-start">
                                <h4 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                    <i data-lucide="{icon_name}" class="w-4 h-4 text-amber-400"></i> {title_esc}
                                </h4>
                                <span class="bg-amber-500/10 text-amber-500 border border-amber-500/20 text-[8px] font-mono font-bold px-2 py-0.5 rounded-full uppercase">{res['category']}</span>
                            </div>
                            <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed font-light">
                                {desc_esc}
                            </p>
                            <ul class="text-xs text-slate-600 dark:text-slate-400 list-disc pl-5 space-y-1.5 font-light">
{bullets_html}                            </ul>
                        </div>\n"""
    return card

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    html_path = os.path.join(repo_root, "index.html")
    
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found.")
        return
        
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()
        
    # Fetch resources
    sa_res = fetch_stayingahead_resources()
    hn_res = fetch_hackernews_ai_resources()
    
    # Combine and prioritize: take top 4 from Staying Ahead and top 2 from HN
    combined_res = sa_res[:4] + hn_res[:2]
    
    # If we couldn't fetch anything (e.g. offline), fall back to default curated templates
    if not combined_res:
        print("No live resources fetched. Using offline fallback...")
        combined_res = [
            {
                'title': 'Setup Guide: Claude Code CLI',
                'category': 'CLI Agent',
                'description': 'Configure Anthropic\'s official terminal agent, Claude Code, to run recursively inside your local environments using custom models or free API endpoints.',
                'bullets': [
                    'Local Serving: Install via global npm: npm install -g @anthropic-ai/claude-code.',
                    'Endpoint Routing: Use local server mappings (like LiteLLM or Ollama proxy routes) to point Claude Code commands to open-weights models.',
                    'Slash Cheatsheet: Boost velocity inside the shell using slash commands: /search (regex code search), /explain (line breakdown), and /compact (git history compaction).'
                ],
                'icon': 'terminal'
            },
            {
                'title': 'Tokenmaxxing (Cutting AI Bills)',
                'category': 'Cost Optimization',
                'description': 'Implement production-grade prompt engineering structures to decrease API token overhead and slash LLM monthly operation bills.',
                'bullets': [
                    'Prompt Caching: Structure system instructions and knowledge context blocks at the very top of your call payload to save up to 90% in retrieval costs.',
                    'Length Penalties: Inject clear output boundaries (e.g., max_tokens=150) and formatting constraints to prevent model verbosity.',
                    'Negative Prompt Filters: Replace verbose "do not write X" paragraphs with a single consolidated list of exclusion criteria at the end of the prompt sequence.'
                ],
                'icon': 'coins'
            }
        ]
        
    # Generate HTML cards
    cards_html = "\n"
    for res in combined_res:
        cards_html += generate_card_html(res)
        
    # Locate markers
    start_marker = "<!-- START_STAYING_AHEAD_RESOURCES -->"
    end_marker = "<!-- END_STAYING_AHEAD_RESOURCES -->"
    
    start_pos = html_content.find(start_marker)
    end_pos = html_content.find(end_marker)
    
    if start_pos == -1 or end_pos == -1:
        print("Error: Could not locate START/END comment markers in index.html.")
        return
        
    # Replace content between markers
    updated_content = (
        html_content[:start_pos + len(start_marker)] + 
        cards_html + "                        " +
        html_content[end_pos:]
    )
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print("index.html updated successfully with fresh resources!")
    
    # Update update log
    log_path = os.path.join(repo_root, "docs", "resources_log.md")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    log_entry = "# Resources Sync Log\n\nLatest sync items:\n\n"
    for r in combined_res:
        log_entry += f"### {r['title']} [{r['category']}]\n"
        log_entry += f"* {r['description']}\n"
        for b in r['bullets']:
            log_entry += f"  - {b}\n"
        log_entry += "\n"
        
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_entry)
    print("Resources log updated.")

if __name__ == "__main__":
    main()
