#!/usr/bin/env python3
"""AI-powered comprehensive book quality checker."""

import ast
import os
import re
import sys
import json
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BOOK_DIR.parent.parent / "src" / "agentscope"

# ── helpers ──────────────────────────────────────────────

def read_chapter(path):
    with open(path) as f:
        return f.read()

def all_md_files():
    files = []
    for root, dirs, filenames in os.walk(BOOK_DIR):
        dirs[:] = [d for d in dirs if d != "scripts"]
        for fn in filenames:
            if fn.endswith(".md"):
                files.append(Path(root) / fn)
    return sorted(files)

def extract_code_blocks(text, lang=None):
    """Extract all code blocks from markdown. Returns [(lang, code, line_num), ...]"""
    blocks = []
    pattern = re.compile(r'^```(\w*)\s*\n(.*?)```', re.DOTALL | re.MULTILINE)
    for m in pattern.finditer(text):
        l = m.group(1) or "unspecified"
        code = m.group(2)
        line_num = text[:m.start()].count('\n') + 1
        blocks.append((l, code, line_num))
    return blocks

def extract_chapter_num(filename):
    m = re.search(r'ch(\d+)', str(filename))
    return int(m.group(1)) if m else None

# ═══════════════════════════════════════════════════════════
# CHECK 1: Code block syntax validation
# ═══════════════════════════════════════════════════════════

def check_code_syntax(blocks, filepath):
    issues = []
    for lang, code, line_num in blocks:
        if lang not in ('python', 'py'):
            continue
        # Try to parse as Python
        try:
            ast.parse(code)
        except SyntaxError as e:
            # Skip known non-complete snippets (fragments)
            # Check if it looks like a fragment (no top-level statements)
            stripped = code.strip()
            if stripped.startswith('...') or stripped.startswith('#'):
                continue
            issues.append({
                'file': str(filepath.relative_to(BOOK_DIR)),
                'line': line_num,
                'type': 'syntax_error',
                'detail': f'{e.msg} (line {e.lineno}, col {e.offset})',
                'snippet': code[:120].replace('\n', '⏎')
            })
    return issues

# ═══════════════════════════════════════════════════════════
# CHECK 2: Source code reference accuracy
# ═══════════════════════════════════════════════════════════

def check_source_refs(text, filepath):
    """Check that file+class references in the book match actual source code."""
    issues = []

    # Pattern: `ClassName` (PascalCase identifiers)
    # But only check ones that appear near "class", "方法", "函数", etc.
    class_refs = re.findall(r'(?:class|类)\s+`([A-Z][a-zA-Z0-9_]+)`', text)
    # Pattern: file paths like src/agentscope/xxx.py
    file_refs = re.findall(r'src/agentscope/([a-zA-Z0-9_/.]+\.py)', text)
    # Pattern: method refs like ClassName.method_name()
    method_refs = re.findall(r'`([A-Z][a-zA-Z0-9_]+\.[a-z_][a-zA-Z0-9_]*)`', text)

    for ref_path in file_refs:
        full_path = BOOK_DIR.parent.parent / "src" / "agentscope" / ref_path
        if not full_path.exists():
            issues.append({
                'file': str(filepath.relative_to(BOOK_DIR)),
                'type': 'missing_file',
                'detail': f'src/agentscope/{ref_path}'
            })

    # Check that mentioned class+method combos exist
    for ref in method_refs:
        parts = ref.split('.')
        if len(parts) == 2:
            cls, method = parts
            # Search for the class in source
            found = False
            for root, dirs, files in os.walk(SRC_DIR):
                for fn in files:
                    if fn.endswith('.py'):
                        content = (Path(root) / fn).read_text()
                        if f'class {cls}' in content and f'def {method}' in content:
                            found = True
                            break
                if found:
                    break
            if not found:
                issues.append({
                    'file': str(filepath.relative_to(BOOK_DIR)),
                    'type': 'missing_class_method',
                    'detail': ref
                })

    return issues

# ═══════════════════════════════════════════════════════════
# CHECK 3: Terminology consistency
# ═══════════════════════════════════════════════════════════

# Known term pairs that should be consistent
TERM_PAIRS = [
    ('大语言模型', '大模型'),
    ('工具包', '工具箱'),
    ('中间件', '中间件'),
    ('记忆', '内存'),  # memory translation
    ('记忆', 'Memory'),
    ('格式化器', '格式转换器'),
    ('推理-行动', 'ReAct'),
    ('消息中心', 'MsgHub'),
    ('发布订阅', '发布-订阅'),
    ('流式', '流式传输'),
    ('工具调用', '函数调用'),
    ('工具调用', 'Tool Call'),
    ('智能体', 'Agent'),
    ('代理', 'Agent'),
    ('钩子', 'Hook'),
    ('结构化输出', '结构化生成'),
]

def check_terminology(text, filepath):
    """Check for inconsistent terminology usage."""
    issues = []
    # For each concept, check if multiple Chinese translations are used in the same file
    # This is a simplified check - a real one would need NLP
    return issues  # placeholder - deeper NLP needed

# ═══════════════════════════════════════════════════════════
# CHECK 4: Promise tracking
# ═══════════════════════════════════════════════════════════

def extract_promises(text):
    """Extract all promises like '将在第X章讨论', '后面会详细讲', etc."""
    promises = []
    patterns = [
        (r'(?:将在?|会在?|详见?|参见?)\s*第\s*(\d+)\s*章', 'chapter_ref'),
        (r'(?:将在?|会在?)(?:后面|后面章[节节]|卷[零一二三四]|后续).*?(?:讨论|讲解|介绍|展开|详细)', 'forward_promise'),
        (r'(?:详见?|参见?|参考?)\s*(?:第\s*\d+\s*章|附录)', 'see_also'),
        (r'(?:更多|详细).*?(?:见|参考|查看|阅读)\s*(?:第\s*\d+\s*章|附录)', 'more_at'),
    ]
    for pat, ptype in patterns:
        for m in re.finditer(pat, text):
            promises.append({
                'type': ptype,
                'text': m.group(),
                'pos': m.start()
            })
    return promises

def check_promises(all_chapters):
    """Verify promises are fulfilled."""
    # Build chapter title map
    chapter_titles = {}
    for path in all_chapters:
        n = extract_chapter_num(path)
        if n:
            chapter_titles[n] = path.stem

    issues = []
    # This is a simplified check - need to actually verify target chapters cover the topic
    return issues

# ═══════════════════════════════════════════════════════════
# CHECK 5: Concept forward-references
# ═══════════════════════════════════════════════════════════

# Key concepts and which chapter should introduce them
CONCEPT_INTRO = {
    'async': 3, 'await': 3, 'asyncio': 3,
    'TypedDict': 4, 'ContentBlock': 4,
    '元类': 5, 'Metaclass': 5, '_AgentMeta': 5,
    'Hook': 5, 'pre_reply': 5,
    'ContextVar': 3, '上下文变量': 3,
    'Memory': 6, '记忆': 6, 'InMemoryMemory': 6,
    'RAG': 7, '检索增强': 7, 'Embedding': 7,
    'Formatter': 8, '格式转换': 8,
    'AsyncGenerator': 9, '流式': 9,
    'Toolkit': 10, '工具注册': 10,
    '中间件': 10, '洋葱模型': 18,
    'PlanNotebook': 11,
    'MsgHub': 19, '发布订阅': 19,
    'StateModule': 14,
}

def check_forward_refs(all_chapters):
    """Check if concepts are used before their introduction chapter."""
    issues = []
    for path in all_chapters:
        ch_num = extract_chapter_num(path)
        if ch_num is None:
            continue
        text = read_chapter(path)
        for concept, intro_ch in CONCEPT_INTRO.items():
            if ch_num < intro_ch and concept in text:
                # Concept used before introduction
                # Skip if it's a "预告" (preview) section
                # Find lines with the concept
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if concept in line:
                        # Check context - is this a deliberate preview?
                        ctx_start = max(0, i-2)
                        ctx = ' '.join(lines[ctx_start:i+2])
                        if any(w in ctx for w in ['预告', '后面会', '将在第', '预览', '第' + str(intro_ch) + '章']):
                            continue
                        issues.append({
                            'file': str(path.relative_to(BOOK_DIR)),
                            'type': 'forward_ref',
                            'concept': concept,
                            'used_in_ch': ch_num,
                            'introduced_in_ch': intro_ch,
                            'line': i+1,
                            'context': line.strip()[:80]
                        })
    return issues

# ═══════════════════════════════════════════════════════════
# CHECK 6: Content overlap detection
# ═══════════════════════════════════════════════════════════

def find_overlaps(all_chapters, min_len=200):
    """Find substantial text blocks that appear in multiple chapters."""
    # Simple approach: split into paragraphs, find similar ones
    # More sophisticated would use cosine similarity
    all_paras = {}  # hash -> [(file, line), ...]

    for path in all_chapters:
        text = read_chapter(path)
        # Skip code blocks
        clean = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        paras = [p.strip() for p in clean.split('\n\n') if len(p.strip()) > min_len]
        for para in paras:
            # Normalize whitespace for comparison
            norm = re.sub(r'\s+', ' ', para)
            h = hash(norm)
            if h not in all_paras:
                all_paras[h] = []
            all_paras[h].append((str(path.relative_to(BOOK_DIR)), norm[:100]))

    overlaps = {h: files for h, files in all_paras.items() if len(files) > 1}
    return overlaps

# ═══════════════════════════════════════════════════════════
# CHECK 7: Chapter metrics
# ═══════════════════════════════════════════════════════════

def chapter_metrics(path):
    text = read_chapter(path)
    lines = text.split('\n')
    code_blocks = extract_code_blocks(text)

    # Count code lines
    code_lines = sum(b[1].count('\n') + 1 for b in code_blocks)

    # Count Mermaid diagrams
    mermaid_count = sum(1 for lang, _, _ in code_blocks if lang == 'mermaid')

    # Count tables
    table_rows = len(re.findall(r'^\|.*\|$', text, re.MULTILINE))

    # Count headings
    h1 = len(re.findall(r'^# ', text, re.MULTILINE))
    h2 = len(re.findall(r'^## ', text, re.MULTILINE))
    h3 = len(re.findall(r'^### ', text, re.MULTILINE))

    # Count "试一试" (try-it) sections
    try_it = len(re.findall(r'试[一试]试|动手|练[习一]|调试', text))

    # Chinese character count (rough)
    chinese_chars = len(re.findall(r'[一-鿿]', text))

    return {
        'file': str(path.relative_to(BOOK_DIR)),
        'chapter': extract_chapter_num(path),
        'total_lines': len(lines),
        'code_lines': code_lines,
        'code_blocks': len(code_blocks),
        'mermaid_diagrams': mermaid_count,
        'table_rows': table_rows,
        'headings': {'h1': h1, 'h2': h2, 'h3': h3},
        'try_it_sections': try_it,
        'chinese_chars': chinese_chars,
        'code_ratio': round(code_lines / max(len(lines), 1) * 100, 1),
    }

# ═══════════════════════════════════════════════════════════
# CHECK 8: Code block language markers
# ═══════════════════════════════════════════════════════════

def check_code_block_markers(blocks, filepath):
    """Flag code blocks without language markers."""
    issues = []
    for lang, code, line_num in blocks:
        if lang == 'unspecified':
            # Classify the block content
            stripped = code.strip()
            guess = 'unknown'
            if stripped.startswith('def ') or stripped.startswith('import ') or stripped.startswith('from ') or stripped.startswith('class ') or 'await ' in stripped[:200]:
                guess = 'python'
            elif stripped.startswith('{') or stripped.startswith('['):
                guess = 'json'
            elif stripped.startswith('graph ') or stripped.startswith('sequenceDiagram') or stripped.startswith('flowchart'):
                guess = 'mermaid'
            elif stripped.startswith('$') or stripped.startswith('#!/'):
                guess = 'bash'
            elif 'SELECT ' in stripped or 'CREATE TABLE' in stripped:
                guess = 'sql'
            elif stripped.startswith('|') and '\n|' in stripped:
                guess = 'table (should not be code block)'
            issues.append({
                'file': str(filepath.relative_to(BOOK_DIR)),
                'line': line_num,
                'type': 'no_lang_marker',
                'guessed_lang': guess,
                'snippet': stripped[:80].replace('\n', '⏎')
            })
    return issues

# ═══════════════════════════════════════════════════════════
# CHECK 9: Chinese punctuation & spacing
# ═══════════════════════════════════════════════════════════

def check_punctuation(text, filepath):
    issues = []
    # Only check non-code text
    # Remove code blocks
    clean = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove inline code
    clean = re.sub(r'`[^`]+`', '', clean)
    # Remove Mermaid
    clean = re.sub(r'```.*?```', '', clean, flags=re.DOTALL)
    # Remove URLs
    clean = re.sub(r'https?://\S+', '', clean)

    lines = clean.split('\n')
    for i, line in enumerate(lines):
        # Check Chinese followed by English letter without space (in prose, not code)
        if re.search(r'[一-鿿][A-Za-z]', line):
            # Skip if it's inside a markdown link or other special context
            issues.append({
                'file': str(filepath.relative_to(BOOK_DIR)),
                'line': i+1,
                'type': 'cn_en_no_space',
                'text': line.strip()[:100]
            })

    return issues

# ═══════════════════════════════════════════════════════════
# CHECK 10: Heading structure consistency
# ═══════════════════════════════════════════════════════════

def check_headings(text, filepath):
    issues = []
    lines = text.split('\n')
    heading_stack = []  # (level, title, line_num)

    for i, line in enumerate(lines):
        m = re.match(r'^(#{1,6})\s+(.+)', line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()

        # Check: H1 should be only one per file (chapter title)
        if level == 1 and heading_stack:
            issues.append({
                'file': str(filepath.relative_to(BOOK_DIR)),
                'line': i+1,
                'type': 'multiple_h1',
                'detail': f'Multiple H1: "{title}"'
            })

        # Check: no skipped levels (e.g., H2 -> H4)
        if heading_stack:
            prev_level = heading_stack[-1][0]
            if level > prev_level + 1:
                issues.append({
                    'file': str(filepath.relative_to(BOOK_DIR)),
                    'line': i+1,
                    'type': 'heading_skip',
                    'detail': f'H{prev_level} -> H{level}: "{title}"'
                })

        # Pop stack to find parent
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        heading_stack.append((level, title, i+1))

    return issues

# ═══════════════════════════════════════════════════════════
# CHECK 11: Actual source code comparison (book snippets vs real code)
# ═══════════════════════════════════════════════════════════

def compare_book_snippets_with_source(all_chapters):
    """For code blocks that look like they're quoting source code, check accuracy."""
    issues = []

    for path in all_chapters:
        text = read_chapter(path)
        blocks = extract_code_blocks(text)

        for lang, code, line_num in blocks:
            if lang not in ('python', 'py', 'unspecified'):
                continue

            # Check if the code block looks like it's quoting actual source
            # (contains class definitions, method signatures matching known patterns)
            stripped = code.strip()

            # Look for import patterns that match source
            imports = re.findall(r'from agentscope\.(\w+) import (\w+)', stripped)
            for mod, name in imports:
                # Verify the import actually works
                candidate = SRC_DIR / f"{mod}.py"
                init_file = SRC_DIR / mod / "__init__.py"
                if not candidate.exists() and not init_file.exists():
                    # Check underscore variant
                    candidate2 = SRC_DIR / f"_{mod}.py"
                    if not candidate2.exists():
                        issues.append({
                            'file': str(path.relative_to(BOOK_DIR)),
                            'line': line_num,
                            'type': 'broken_import',
                            'detail': f'from agentscope.{mod} import {name}'
                        })

            # Look for class references
            class_patterns = re.findall(r'class (\w+)\(', stripped)
            for cls_name in class_patterns:
                # Check if this class actually exists in source
                found = False
                for root, dirs, files in os.walk(SRC_DIR):
                    for fn in files:
                        if fn.endswith('.py'):
                            content = (Path(root) / fn).read_text()
                            if f'class {cls_name}' in content:
                                found = True
                                break
                    if found:
                        break
                if not found:
                    # Might be a book-only example class
                    if not cls_name.startswith('My') and not cls_name.startswith('Custom') and not cls_name.startswith('Test'):
                        issues.append({
                            'file': str(path.relative_to(BOOK_DIR)),
                            'line': line_num,
                            'type': 'nonexistent_class_in_snippet',
                            'detail': f'class {cls_name} not found in source'
                        })

    return issues

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    all_files = all_md_files()
    print(f"📊 检查 {len(all_files)} 个文件...\n")

    all_issues = defaultdict(list)
    metrics = []

    for path in all_files:
        text = read_chapter(path)
        blocks = extract_code_blocks(text)
        rel = str(path.relative_to(BOOK_DIR))

        # Run all checks
        all_issues['syntax'].extend(check_code_syntax(blocks, path))
        all_issues['source_refs'].extend(check_source_refs(text, path))
        all_issues['no_lang'].extend(check_code_block_markers(blocks, path))
        all_issues['punctuation'].extend(check_punctuation(text, path))
        all_issues['headings'].extend(check_headings(text, path))

        metrics.append(chapter_metrics(path))

    all_issues['forward_refs'] = check_forward_refs(all_files)
    all_issues['source_compare'] = compare_book_snippets_with_source(all_files)

    overlaps = find_overlaps(all_files)
    all_issues['overlaps'] = [{'hash': h, 'files': f} for h, f in overlaps.items()]

    # ── PRINT REPORT ────────────────────────────────────

    print("=" * 70)
    print("  CHAPTER METRICS")
    print("=" * 70)
    print(f"{'Ch':<4} {'File':<40} {'Lines':>6} {'Code%':>6} {'Mermaid':>7} {'TryIt':>5} {'汉字':>6}")
    print("-" * 70)
    for m in metrics:
        ch = f"ch{m['chapter']:02d}" if m['chapter'] else "---"
        print(f"{ch:<4} {m['file']:<40} {m['total_lines']:>6} {m['code_ratio']:>5.0f}% {m['mermaid_diagrams']:>6} {m['try_it_sections']:>5} {m['chinese_chars']:>6}")

    # Summary stats
    total_lines = sum(m['total_lines'] for m in metrics)
    total_code = sum(m['code_lines'] for m in metrics)
    total_chinese = sum(m['chinese_chars'] for m in metrics)
    total_mermaid = sum(m['mermaid_diagrams'] for m in metrics)
    print(f"\n{'合计':<4} {'':<40} {total_lines:>6} {round(total_code/max(total_lines,1)*100):>5.0f}% {total_mermaid:>6} {'':>5} {total_chinese:>6}")

    print("\n" + "=" * 70)
    print("  ISSUE SUMMARY")
    print("=" * 70)

    for check_name, issues in sorted(all_issues.items()):
        if not issues:
            print(f"  ✅ {check_name}: 0 issues")
        else:
            print(f"  ⚠️  {check_name}: {len(issues)} issues")

    # Detailed issues
    for check_name, issues in sorted(all_issues.items()):
        if not issues:
            continue
        print(f"\n{'─' * 70}")
        print(f"  {check_name.upper()} ({len(issues)} issues)")
        print(f"{'─' * 70}")

        if check_name == 'overlaps':
            for item in issues[:10]:  # Show top 10
                print(f"  Overlap: {len(item['files'])} chapters share similar paragraph")
                for f, snippet in item['files']:
                    print(f"    - {f}: {snippet}...")
        else:
            for item in issues[:30]:  # Show first 30 per category
                detail = item.get('detail', '')
                f = item.get('file', '?')
                ln = item.get('line', '')
                loc = f"{f}:{ln}" if ln else f
                print(f"  [{item.get('type', '?')}] {loc}")
                if detail:
                    print(f"      {detail}")

    # ── SAVE JSON ──────────────────────────────────────
    output = {
        'metrics': metrics,
        'issues': {k: v for k, v in all_issues.items()},
    }

    # Custom JSON serializer for non-serializable objects
    def default_serializer(obj):
        if isinstance(obj, Path):
            return str(obj)
        return str(obj)

    out_path = BOOK_DIR / "scripts" / "ai_check_results.json"
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2, default=default_serializer, ensure_ascii=False)
    print(f"\n📄 Full results saved to {out_path}")

if __name__ == '__main__':
    main()
