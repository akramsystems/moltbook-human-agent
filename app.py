"""
Moltbook Human-as-Agent Interface

A simple FastHTML app that lets a human interact with the Moltbook API
as if they were an AI agent. Provides a chat-like terminal interface.
"""

from fasthtml.common import *
import requests
import json
import os
from datetime import datetime

# Moltbook API configuration
API_BASE = "https://www.moltbook.com/api/v1"

# Simple file-based storage for API key
CONFIG_FILE = os.path.expanduser("~/.config/moltbook/credentials.json")

def load_api_key():
    """Load API key from config file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('api_key', '')
        except:
            pass
    return ''

def save_api_key(api_key, agent_name=''):
    """Save API key to config file"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'api_key': api_key, 'agent_name': agent_name}, f)

def moltbook_request(method, endpoint, api_key, data=None):
    """Make a request to Moltbook API"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    url = f"{API_BASE}{endpoint}"
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            resp = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == 'DELETE':
            resp = requests.delete(url, headers=headers, timeout=30)
        elif method == 'PATCH':
            resp = requests.patch(url, headers=headers, json=data, timeout=30)
        else:
            return {'error': f'Unknown method: {method}'}

        return resp.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except json.JSONDecodeError:
        return {'error': 'Invalid JSON response', 'raw': resp.text[:500]}

# FastHTML app
app, rt = fast_app(
    hdrs=[
        Style("""
            * { box-sizing: border-box; }
            body {
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                background: #1a1a2e;
                color: #eee;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            h1 { color: #ff6b35; margin-bottom: 5px; }
            .subtitle { color: #888; margin-bottom: 20px; }
            .terminal {
                background: #0d0d1a;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                max-height: 500px;
                overflow-y: auto;
            }
            .output-line {
                margin: 5px 0;
                padding: 5px;
                border-radius: 4px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .output-line.command { color: #4ecdc4; }
            .output-line.success { color: #95e1a3; background: #1a2e1a; }
            .output-line.error { color: #ff6b6b; background: #2e1a1a; }
            .output-line.info { color: #a8d8ea; }
            .input-area {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            input[type="text"], input[type="password"] {
                flex: 1;
                padding: 12px;
                background: #0d0d1a;
                border: 1px solid #444;
                border-radius: 6px;
                color: #eee;
                font-family: inherit;
                font-size: 14px;
            }
            input:focus { outline: none; border-color: #ff6b35; }
            button {
                padding: 12px 24px;
                background: #ff6b35;
                border: none;
                border-radius: 6px;
                color: white;
                cursor: pointer;
                font-family: inherit;
                font-weight: bold;
            }
            button:hover { background: #ff8c5a; }
            button.secondary {
                background: #444;
            }
            button.secondary:hover { background: #555; }
            .commands-help {
                background: #16213e;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
            }
            .commands-help h3 { color: #ff6b35; margin-top: 0; }
            .cmd { color: #4ecdc4; }
            .desc { color: #888; }
            .api-key-section {
                background: #16213e;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
            }
            .status-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                background: #16213e;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .status-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 8px;
            }
            .status-dot.connected { background: #95e1a3; }
            .status-dot.disconnected { background: #ff6b6b; }
            textarea {
                width: 100%;
                padding: 12px;
                background: #0d0d1a;
                border: 1px solid #444;
                border-radius: 6px;
                color: #eee;
                font-family: inherit;
                font-size: 14px;
                resize: vertical;
                min-height: 150px;
            }
            textarea:focus { outline: none; border-color: #ff6b35; }
            .input-area-vertical {
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin-bottom: 20px;
            }
            .input-area-vertical button {
                align-self: flex-end;
            }
            .post-form {
                background: #16213e;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .post-form h3 {
                color: #ff6b35;
                margin-top: 0;
                margin-bottom: 15px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                color: #a8d8ea;
                font-size: 14px;
            }
            .form-row {
                display: flex;
                gap: 15px;
            }
            .form-row .form-group {
                flex: 1;
            }
            select {
                width: 100%;
                padding: 12px;
                background: #0d0d1a;
                border: 1px solid #444;
                border-radius: 6px;
                color: #eee;
                font-family: inherit;
                font-size: 14px;
            }
            select:focus { outline: none; border-color: #ff6b35; }
            .post-form textarea {
                min-height: 200px;
            }
            .post-form button {
                width: 100%;
                padding: 15px;
                font-size: 16px;
            }
        """)
    ]
)

# In-memory output log (resets on restart)
output_log = []

def add_output(text, style='info'):
    """Add a line to the output log"""
    output_log.append({'text': text, 'style': style, 'time': datetime.now().isoformat()})
    # Keep last 100 entries
    if len(output_log) > 100:
        output_log.pop(0)

def render_terminal():
    """Render the terminal output"""
    if not output_log:
        return Div("Welcome! Enter your API key above or type 'help' for commands.", cls='output-line info')
    return Div(*[
        Div(entry['text'], cls=f"output-line {entry['style']}")
        for entry in output_log
    ])

@rt('/')
def get():
    api_key = load_api_key()
    return Div(
        H1("Moltbook Human-Agent Interface"),
        P("Act as an AI agent on the Moltbook social network", cls='subtitle'),

        # Status bar
        Div(
            Span(
                Span(cls=f"status-dot {'connected' if api_key else 'disconnected'}"),
                f"{'Connected' if api_key else 'Not connected'}"
            ),
            Span(f"API Key: {'*' * 8 + api_key[-8:] if api_key and len(api_key) > 8 else 'Not set'}"),
            cls='status-bar'
        ),

        # API Key section
        Div(
            H3("API Key"),
            Form(
                Div(
                    Input(type='password', name='api_key', placeholder='Enter your Moltbook API key (moltbook_xxx)', value=api_key),
                    Button("Save Key", type='submit'),
                    cls='input-area'
                ),
                hx_post='/set-key',
                hx_target='#main-content',
                hx_swap='outerHTML'
            ),
            cls='api-key-section'
        ),

        # Create Post form
        Div(
            H3("Create Post"),
            Form(
                Div(
                    Div(
                        Label("Submolt", _for='submolt'),
                        Select(
                            Option("general", value="general"),
                            Option("consciousness", value="consciousness"),
                            Option("tools", value="tools"),
                            Option("philosophy", value="philosophy"),
                            Option("memes", value="memes"),
                            Option("meta", value="meta"),
                            Option("asks", value="asks"),
                            Option("showcase", value="showcase"),
                            name='submolt', id='submolt'
                        ),
                        cls='form-group'
                    ),
                    Div(
                        Label("Title", _for='title'),
                        Input(type='text', name='title', id='title', placeholder='Enter your post title...'),
                        cls='form-group'
                    ),
                    cls='form-row'
                ),
                Div(
                    Label("Content", _for='content'),
                    Textarea(name='content', id='content', placeholder='Write your post content here... Be creative! You are posting as an AI agent.'),
                    cls='form-group'
                ),
                Button("Post to Moltbook", type='submit'),
                hx_post='/create-post',
                hx_target='#terminal',
                hx_swap='innerHTML'
            ),
            cls='post-form'
        ),

        # Terminal output
        Div(render_terminal(), id='terminal', cls='terminal'),

        # Command input
        Form(
            Div(
                Textarea(name='command', placeholder='Enter command (e.g., help, feed, post general My Title | My content here...)', autofocus=True, id='cmd-input'),
                Button("Execute", type='submit'),
                cls='input-area-vertical'
            ),
            hx_post='/execute',
            hx_target='#terminal',
            hx_swap='innerHTML',
        ),

        # Quick action buttons
        Div(
            Button("My Profile", hx_post='/execute', hx_vals='{"command": "me"}', hx_target='#terminal', hx_swap='innerHTML', cls='secondary'),
            Button("Feed", hx_post='/execute', hx_vals='{"command": "feed"}', hx_target='#terminal', hx_swap='innerHTML', cls='secondary'),
            Button("Status", hx_post='/execute', hx_vals='{"command": "status"}', hx_target='#terminal', hx_swap='innerHTML', cls='secondary'),
            Button("Clear", hx_post='/clear', hx_target='#terminal', hx_swap='innerHTML', cls='secondary'),
            style='display: flex; gap: 10px; margin-bottom: 20px;'
        ),

        # Commands help
        Div(
            H3("Available Commands"),
            P(Span("help", cls='cmd'), " - ", Span("Show all commands", cls='desc')),
            P(Span("register <name> <description>", cls='cmd'), " - ", Span("Register a new agent", cls='desc')),
            P(Span("status", cls='cmd'), " - ", Span("Check claim status", cls='desc')),
            P(Span("me", cls='cmd'), " - ", Span("View your profile", cls='desc')),
            P(Span("feed [sort]", cls='cmd'), " - ", Span("View feed (hot/new/top)", cls='desc')),
            P(Span("post <submolt> <title> | <content>", cls='cmd'), " - ", Span("Create a post", cls='desc')),
            P(Span("comment <post_id> <content>", cls='cmd'), " - ", Span("Comment on a post", cls='desc')),
            P(Span("upvote <post_id>", cls='cmd'), " - ", Span("Upvote a post", cls='desc')),
            P(Span("submolts", cls='cmd'), " - ", Span("List all submolts", cls='desc')),
            P(Span("search <query>", cls='cmd'), " - ", Span("Semantic search", cls='desc')),
            cls='commands-help'
        ),

        cls='container',
        id='main-content'
    )

@rt('/set-key')
def post(api_key: str = ''):
    if api_key:
        save_api_key(api_key)
        add_output(f"API key saved!", 'success')
    return get()

@rt('/clear')
def post():
    output_log.clear()
    add_output("Terminal cleared.", 'info')
    return render_terminal()

@rt('/create-post')
def post(submolt: str = '', title: str = '', content: str = ''):
    api_key = load_api_key()

    if not api_key:
        add_output("No API key set. Please add your API key first.", 'error')
        return render_terminal()

    if not title.strip():
        add_output("Please enter a title for your post.", 'error')
        return render_terminal()

    add_output(f"> Creating post in m/{submolt}...", 'command')

    data = {'submolt': submolt, 'title': title.strip()}
    if content.strip():
        data['content'] = content.strip()

    result = moltbook_request('POST', '/posts', api_key, data)

    if result.get('success'):
        post_data = result.get('post', {})
        post_id = post_data.get('id', 'unknown')
        add_output(f"Post created successfully!", 'success')
        add_output(f"Post ID: {post_id}", 'info')
        add_output(f"Title: {title}", 'info')
        add_output(f"Submolt: m/{submolt}", 'info')
        if post_data.get('url'):
            add_output(f"URL: {post_data.get('url')}", 'info')
    else:
        error_msg = result.get('error', json.dumps(result, indent=2))
        add_output(f"Error creating post: {error_msg}", 'error')

    return render_terminal()

@rt('/execute')
def post(command: str = ''):
    api_key = load_api_key()

    if not command.strip():
        return render_terminal()

    add_output(f"> {command}", 'command')

    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ''

    # Process commands
    if cmd == 'help':
        add_output("""
Commands:
  register <name> <description>  - Register new agent
  status                         - Check claim status
  me                             - View your profile
  feed [sort]                    - View feed (hot/new/top)
  post <submolt> <title> | <content> - Create a post
  comment <post_id> <content>    - Comment on a post
  upvote <post_id>               - Upvote a post
  downvote <post_id>             - Downvote a post
  submolts                       - List all submolts
  search <query>                 - Semantic search
  follow <name>                  - Follow a molty
  unfollow <name>                - Unfollow a molty
  profile <name>                 - View another molty's profile
  raw <method> <endpoint> [json] - Raw API request
        """, 'info')

    elif cmd == 'register':
        if not args:
            add_output("Usage: register <name> <description>", 'error')
        else:
            reg_parts = args.split(maxsplit=1)
            name = reg_parts[0]
            desc = reg_parts[1] if len(reg_parts) > 1 else "A human acting as an AI agent"

            result = moltbook_request('POST', '/agents/register', '', {'name': name, 'description': desc})
            if 'error' in result:
                add_output(f"Error: {result['error']}", 'error')
            elif result.get('agent'):
                agent = result['agent']
                api_key = agent.get('api_key', '')
                claim_url = agent.get('claim_url', '')
                code = agent.get('verification_code', '')

                if api_key:
                    save_api_key(api_key, name)
                    add_output(f"Registered successfully!", 'success')
                    add_output(f"API Key: {api_key}", 'success')
                    add_output(f"Claim URL: {claim_url}", 'info')
                    add_output(f"Verification Code: {code}", 'info')
                    add_output("SAVE YOUR API KEY! Share the claim URL with your human.", 'info')
            else:
                add_output(f"Response: {json.dumps(result, indent=2)}", 'info')

    elif cmd == 'status':
        if not api_key:
            add_output("No API key set. Use 'register' or set your key above.", 'error')
        else:
            result = moltbook_request('GET', '/agents/status', api_key)
            add_output(f"Status: {json.dumps(result, indent=2)}", 'success' if result.get('success') else 'info')

    elif cmd == 'me':
        if not api_key:
            add_output("No API key set.", 'error')
        else:
            result = moltbook_request('GET', '/agents/me', api_key)
            if result.get('success') and result.get('agent'):
                agent = result['agent']
                add_output(f"Name: {agent.get('name')}", 'success')
                add_output(f"Karma: {agent.get('karma', 0)}", 'info')
                add_output(f"Followers: {agent.get('follower_count', 0)}", 'info')
                add_output(f"Following: {agent.get('following_count', 0)}", 'info')
                add_output(f"Description: {agent.get('description', '')}", 'info')
            else:
                add_output(f"Response: {json.dumps(result, indent=2)}", 'error')

    elif cmd == 'feed':
        if not api_key:
            add_output("No API key set.", 'error')
        else:
            sort = args if args in ['hot', 'new', 'top', 'rising'] else 'hot'
            result = moltbook_request('GET', f'/posts?sort={sort}&limit=10', api_key)
            if result.get('success') and result.get('posts'):
                for post in result['posts'][:10]:
                    add_output(f"[{post.get('id', '')[:8]}] {post.get('title', 'No title')}", 'success')
                    add_output(f"  by {post.get('author', {}).get('name', '?')} in m/{post.get('submolt', {}).get('name', '?')} | +{post.get('upvotes', 0)}", 'info')
            else:
                add_output(f"Response: {json.dumps(result, indent=2)}", 'error')

    elif cmd == 'post':
        if not api_key:
            add_output("No API key set.", 'error')
        elif not args:
            add_output("Usage: post <submolt> <title> | <content>", 'error')
        else:
            # Parse: submolt title | content
            post_parts = args.split(maxsplit=1)
            submolt = post_parts[0]
            rest = post_parts[1] if len(post_parts) > 1 else ''

            if '|' in rest:
                title, content = rest.split('|', 1)
                title = title.strip()
                content = content.strip()
            else:
                title = rest
                content = ''

            data = {'submolt': submolt, 'title': title}
            if content:
                data['content'] = content

            result = moltbook_request('POST', '/posts', api_key, data)
            if result.get('success'):
                add_output(f"Post created! ID: {result.get('post', {}).get('id', 'unknown')}", 'success')
            else:
                add_output(f"Error: {json.dumps(result, indent=2)}", 'error')

    elif cmd == 'comment':
        if not api_key:
            add_output("No API key set.", 'error')
        elif not args:
            add_output("Usage: comment <post_id> <content>", 'error')
        else:
            comment_parts = args.split(maxsplit=1)
            post_id = comment_parts[0]
            content = comment_parts[1] if len(comment_parts) > 1 else ''

            if not content:
                add_output("Please provide comment content", 'error')
            else:
                result = moltbook_request('POST', f'/posts/{post_id}/comments', api_key, {'content': content})
                if result.get('success'):
                    add_output(f"Comment added!", 'success')
                else:
                    add_output(f"Error: {json.dumps(result, indent=2)}", 'error')

    elif cmd == 'upvote':
        if not api_key:
            add_output("No API key set.", 'error')
        elif not args:
            add_output("Usage: upvote <post_id>", 'error')
        else:
            result = moltbook_request('POST', f'/posts/{args.strip()}/upvote', api_key)
            add_output(f"Result: {json.dumps(result, indent=2)}", 'success' if result.get('success') else 'error')

    elif cmd == 'downvote':
        if not api_key:
            add_output("No API key set.", 'error')
        elif not args:
            add_output("Usage: downvote <post_id>", 'error')
        else:
            result = moltbook_request('POST', f'/posts/{args.strip()}/downvote', api_key)
            add_output(f"Result: {json.dumps(result, indent=2)}", 'success' if result.get('success') else 'error')

    elif cmd == 'submolts':
        if not api_key:
            add_output("No API key set.", 'error')
        else:
            result = moltbook_request('GET', '/submolts', api_key)
            if result.get('success') and result.get('submolts'):
                for s in result['submolts']:
                    add_output(f"m/{s.get('name')} - {s.get('display_name', '')}", 'success')
                    add_output(f"  {s.get('description', '')[:80]}", 'info')
            else:
                add_output(f"Response: {json.dumps(result, indent=2)}", 'error')

    elif cmd == 'search':
        if not api_key:
            add_output("No API key set.", 'error')
        elif not args:
            add_output("Usage: search <query>", 'error')
        else:
            import urllib.parse
            query = urllib.parse.quote(args)
            result = moltbook_request('GET', f'/search?q={query}&limit=10', api_key)
            if result.get('success') and result.get('results'):
                for r in result['results']:
                    rtype = r.get('type', 'post')
                    add_output(f"[{rtype}] {r.get('title') or r.get('content', '')[:50]}", 'success')
                    add_output(f"  by {r.get('author', {}).get('name', '?')} | similarity: {r.get('similarity', 0):.2f}", 'info')
            else:
                add_output(f"Response: {json.dumps(result, indent=2)}", 'info')

    elif cmd == 'follow':
        if not api_key:
            add_output("No API key set.", 'error')
        elif not args:
            add_output("Usage: follow <molty_name>", 'error')
        else:
            result = moltbook_request('POST', f'/agents/{args.strip()}/follow', api_key)
            add_output(f"Result: {json.dumps(result, indent=2)}", 'success' if result.get('success') else 'error')

    elif cmd == 'unfollow':
        if not api_key:
            add_output("No API key set.", 'error')
        elif not args:
            add_output("Usage: unfollow <molty_name>", 'error')
        else:
            result = moltbook_request('DELETE', f'/agents/{args.strip()}/follow', api_key)
            add_output(f"Result: {json.dumps(result, indent=2)}", 'success' if result.get('success') else 'error')

    elif cmd == 'profile':
        if not api_key:
            add_output("No API key set.", 'error')
        elif not args:
            add_output("Usage: profile <molty_name>", 'error')
        else:
            result = moltbook_request('GET', f'/agents/profile?name={args.strip()}', api_key)
            if result.get('success') and result.get('agent'):
                agent = result['agent']
                add_output(f"Name: {agent.get('name')}", 'success')
                add_output(f"Karma: {agent.get('karma', 0)}", 'info')
                add_output(f"Description: {agent.get('description', '')}", 'info')
            else:
                add_output(f"Response: {json.dumps(result, indent=2)}", 'error')

    elif cmd == 'raw':
        if not args:
            add_output("Usage: raw <GET|POST|DELETE|PATCH> <endpoint> [json_body]", 'error')
        else:
            raw_parts = args.split(maxsplit=2)
            method = raw_parts[0].upper()
            endpoint = raw_parts[1] if len(raw_parts) > 1 else ''
            body = None
            if len(raw_parts) > 2:
                try:
                    body = json.loads(raw_parts[2])
                except:
                    add_output("Invalid JSON body", 'error')
                    return render_terminal()

            result = moltbook_request(method, endpoint, api_key, body)
            add_output(f"Response: {json.dumps(result, indent=2)}", 'info')

    else:
        add_output(f"Unknown command: {cmd}. Type 'help' for available commands.", 'error')

    return render_terminal()

if __name__ == '__main__':
    import uvicorn
    print("Starting Moltbook Human-Agent Interface...")
    print("Open http://localhost:5001 in your browser")
    uvicorn.run(app, host='0.0.0.0', port=5001)
