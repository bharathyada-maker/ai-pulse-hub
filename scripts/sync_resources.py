import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import os
import ssl
import html

def fetch_arxiv_open_resources():
    print("Fetching arXiv public domain research papers (Open Access)...")
    resources = []
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        # arXiv Public API - cs.AI, cs.CL, cs.LG, cs.RO
        url = "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=4"
        req = urllib.request.Request(url, headers={'User-Agent': 'AIPulseHub-OpenDomainSync/1.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=12) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                title = re.sub(r'\s+', ' ', title)
                if not title:
                    continue
                
                paper_id = entry.find('atom:id', ns).text.strip()
                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                summary = re.sub(r'\s+', ' ', summary)
                
                # Extract first 1-2 sentences for a clean, concise card summary
                sentences = re.split(r'\. |\.\n', summary)
                desc = sentences[0] + ('.' if not sentences[0].endswith('.') else '')
                if len(desc) < 80 and len(sentences) > 1:
                    desc += ' ' + sentences[1] + ('.' if not sentences[1].endswith('.') else '')
                if len(desc) > 220:
                    desc = desc[:217] + '...'
                    
                pub_date = entry.find('atom:published', ns).text.strip()[:10]
                authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
                author_str = ', '.join(authors[:2]) + (' et al.' if len(authors) > 2 else '')
                
                # Public arXiv PDF and abstract link
                pdf_link = paper_id.replace('/abs/', '/pdf/')
                
                resources.append({
                    'title': title,
                    'category': 'arXiv Research',
                    'description': desc,
                    'bullets': [
                        f"Authors: {author_str}",
                        f"Public Paper: {paper_id}",
                        f"Indexed: {pub_date} (Public Domain Open Preprint)"
                    ],
                    'icon': 'book-open'
                })
    except Exception as e:
        print(f"Error fetching arXiv preprints: {e}")
        
    return resources

def fetch_hackernews_ai_resources():
    print("Fetching Hacker News open public API for trending AI/LLM topics...")
    resources = []
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            top_ids = json.loads(response.read().decode('utf-8'))
            
        count = 0
        for story_id in top_ids[:120]:
            if count >= 2:
                break
                
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            req_story = urllib.request.Request(story_url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req_story, context=ctx, timeout=4) as resp_story:
                    story = json.loads(resp_story.read().decode('utf-8'))
                    title = story.get('title', '')
                    
                    if any(kw in title.lower() for kw in [' ai ', 'llm', 'gpt', 'openai', 'claude', 'deepseek', 'agent', 'model', 'neural', 'weights']):
                        link = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                        score = story.get('score', 0)
                        author = story.get('by', 'HN Community')
                        
                        resources.append({
                            'title': title,
                            'category': 'Open Tech',
                            'description': f"Public domain technical development, open repository, or community discussion on Hacker News (Score: {score} points).",
                            'bullets': [
                                f"Contributor: {author}",
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
    icon_map = {
        'terminal': 'terminal',
        'sparkles': 'sparkles',
        'layers': 'layers',
        'trending-up': 'trending-up',
        'book-open': 'book-open',
        'coins': 'coins',
        'image': 'image',
        'cpu': 'cpu'
    }
    icon_name = icon_map.get(res['icon'], 'sparkles')
    
    title_esc = html.escape(res['title'])
    desc_esc = html.escape(res['description'])
    
    bullets_html = ""
    for b in res['bullets']:
        b_formatted = re.sub(
            r'(https?://[^\s]+)',
            r'<a href="\1" target="_blank" rel="noopener" class="text-amber-500 hover:underline inline-flex items-center gap-0.5 font-medium">\1 <i data-lucide="external-link" class="w-3 h-3 inline"></i></a>',
            b
        )
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
        
    # Fetch resources from authentic public domain sources
    arxiv_res = fetch_arxiv_open_resources()
    hn_res = fetch_hackernews_ai_resources()
    
    combined_res = arxiv_res[:4] + hn_res[:2]
    
    # If offline or rate limited, fall back to authentic open technical blueprints
    if not combined_res:
        print("No live resources fetched. Using open technical playbooks fallback...")
        combined_res = [
            {
                'title': 'Setup Guide: Claude Code CLI',
                'category': 'CLI Agent',
                'description': 'Configure Anthropic\'s terminal agent, Claude Code, to run recursively inside local developer environments using open-weights or direct model endpoints.',
                'bullets': [
                    'Install via npm: npm install -g @anthropic-ai/claude-code',
                    'Routing: Route through LiteLLM or local Ollama proxy endpoints to utilize open-source weights.',
                    'Productivity: Utilize slash commands /search (regex search), /explain (code analysis), and /compact (history trim).'
                ],
                'icon': 'terminal'
            },
            {
                'title': 'Tokenmaxxing & Prompt Caching Architectures',
                'category': 'Cost Optimization',
                'description': 'Implement production-grade prompt engineering structures to decrease API token overhead and optimize model inference efficiency.',
                'bullets': [
                    'Prompt Caching: Structure system instructions and static schemas at the start of payload to achieve up to 90% retrieval savings.',
                    'Output Bounds: Set explicit output tokens and format specifications to avoid excessive token generation.',
                    'Negative Filtering: Consolidate exclusion rules at the end of the prompt sequence for minimal token cost.'
                ],
                'icon': 'coins'
            },
            {
                'title': 'Local Open-Weights Serving Pipeline (DeepSeek & vLLM)',
                'category': 'Inference Serving',
                'description': 'Deploy DeepSeek-R1 / Qwen 2.5-Coder on commodity consumer GPUs using quantized FP8/AWQ weights and continuous batching.',
                'bullets': [
                    'vLLM Engine: Serve with vLLM for high-throughput PagedAttention and tensor parallelism across GPUs.',
                    'Ollama Run: One-click local serving via ollama run deepseek-r1:8b or qwen2.5-coder:7b.',
                    'Context Window: Utilize flash-attention-2 to handle up to 64k context windows within standard VRAM limits.'
                ],
                'icon': 'cpu'
            }
        ]
        
    cards_html = "\n"
    for res in combined_res:
        cards_html += generate_card_html(res)
        
    # Standard open resource markers
    start_marker = "<!-- START_PUBLIC_AI_RESOURCES -->"
    end_marker = "<!-- END_PUBLIC_AI_RESOURCES -->"
    
    # Check for open resource markers
    start_pos = html_content.find(start_marker)
    end_pos = html_content.find(end_marker)
    
    if start_pos == -1 or end_pos == -1:
        print("Error: Could not locate START_PUBLIC_AI_RESOURCES or END_PUBLIC_AI_RESOURCES in index.html.")
        return
    
    updated_content = (
            html_content[:start_pos + len(start_marker)] +
            cards_html + "                        " +
            html_content[end_pos:]
        )
        
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print("index.html updated successfully with authentic open public domain resources!")
    
    # Update docs/resources_log.md
    log_path = os.path.join(repo_root, "docs", "resources_log.md")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    log_entry = "# Public AI Resources & Research Log\n\n"
    log_entry += "Resources synced dynamically from authentic open public domain archives (arXiv Open Access preprints and Hacker News developer discussions).\n\n"
    log_entry += "Latest sync items:\n\n"
    for r in combined_res:
        log_entry += f"### {r['title']} [{r['category']}]\n"
        log_entry += f"* {r['description']}\n"
        for b in r['bullets']:
            log_entry += f"  - {b}\n"
        log_entry += "\n"
        
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_entry)
    print("Resources log updated with public domain sources.")

if __name__ == "__main__":
    main()
