#!/usr/bin/env python3
"""
Translate a single SICP XHTML file from English to Burmese.

Usage: python3 translate_file.py <input.xhtml> <output.xhtml> <model>

Model should be like: google-antigravity/gemini-3-flash
"""

import sys
import os
import subprocess
import tempfile
import re

MAX_CHUNK_SIZE = 20000  # bytes per chunk for translation


def make_prompt(html_chunk, file_context=""):
    return f"""Translate the following XHTML content from English to Burmese (Myanmar language, Unicode UTF-8).

RULES:
1. Translate ALL English prose/natural language text to Burmese
2. Do NOT translate: HTML tags, attributes, CSS classes, IDs, URLs
3. Do NOT translate content inside <code>, <pre>, <samp> tags — keep code exactly as-is
4. Do NOT translate navigation text (Next:, Prev:, Up:, Contents, etc.)
5. Keep author names, proper nouns, book titles in original form
6. For CS technical terms: translate if natural Burmese equivalent exists, otherwise keep English
7. Return ONLY the translated XHTML — no explanations, no markdown code fences, no preamble
8. Preserve ALL HTML structure, tags, attributes, nesting exactly as-is
9. Keep all footnote references, anchor links, and IDs intact
10. Do NOT wrap output in ```html or ``` markers

Context: SICP (Structure and Interpretation of Computer Programs) textbook. {file_context}

XHTML to translate:
{html_chunk}"""


def call_model(prompt_text, model):
    """Call pi with the given prompt and model."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(prompt_text)
        prompt_file = f.name

    try:
        result = subprocess.run(
            ['pi', '-p', '--model', model, '--no-session', f'@{prompt_file}'],
            capture_output=True, text=True, timeout=600
        )
        output = result.stdout.strip()

        # Remove markdown code fences if model added them
        if output.startswith('```'):
            lines = output.split('\n')
            lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            output = '\n'.join(lines)

        return output
    except subprocess.TimeoutExpired:
        print(f"  WARNING: Translation timed out", file=sys.stderr)
        return prompt_text
    finally:
        os.unlink(prompt_file)


def split_body_into_chunks(body_html, max_size=MAX_CHUNK_SIZE):
    """Split body HTML into chunks at heading boundaries."""
    # Split at h2, h3, h4 boundaries
    pattern = r'(?=<h[2-4][\s>])'
    parts = re.split(pattern, body_html)

    chunks = []
    current = ""

    for part in parts:
        if len(current) + len(part) > max_size and current:
            chunks.append(current)
            current = part
        else:
            current += part

    if current.strip():
        chunks.append(current)

    # If any chunk is still too large, split by paragraphs
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_size * 2:
            # Split by </p> or </blockquote>
            sub_parts = re.split(r'(</p>|</blockquote>)', chunk)
            sub_current = ""
            for sp in sub_parts:
                if len(sub_current) + len(sp) > max_size and sub_current:
                    final_chunks.append(sub_current)
                    sub_current = sp
                else:
                    sub_current += sp
            if sub_current.strip():
                final_chunks.append(sub_current)
        else:
            final_chunks.append(chunk)

    return final_chunks


def translate_file(input_path, output_path, model):
    """Translate a full XHTML file."""
    filename = os.path.basename(input_path)
    print(f"Translating {filename} with {model}...")

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract body content
    body_match = re.search(r'(<body[^>]*>)(.*?)(</body>)', content, re.DOTALL)
    if not body_match:
        print(f"  No body found, copying as-is")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return

    body_tag = body_match.group(1)
    body_inner = body_match.group(2)
    body_close = body_match.group(3)

    file_context = f"File: {filename}"

    if len(body_inner) < 25000:
        # Translate whole body at once
        print(f"  Single chunk ({len(body_inner)} bytes)")
        prompt = make_prompt(body_inner, file_context)
        translated = call_model(prompt, model)
    else:
        # Split into chunks
        chunks = split_body_into_chunks(body_inner)
        print(f"  Split into {len(chunks)} chunks")

        translated_parts = []
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}/{len(chunks)} ({len(chunk)} bytes)...")
            prompt = make_prompt(chunk, file_context)
            result = call_model(prompt, model)
            translated_parts.append(result)

        translated = '\n'.join(translated_parts)

    # Reassemble
    before_body = content[:body_match.start()]
    after_body = content[body_match.end():]

    new_content = before_body + body_tag + '\n' + translated + '\n' + body_close + after_body

    # Update lang to Burmese
    new_content = new_content.replace('xml:lang="en"', 'xml:lang="my"')
    new_content = new_content.replace('lang="en"', 'lang="my"')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  Done: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <input.xhtml> <output.xhtml> <model>")
        sys.exit(1)

    translate_file(sys.argv[1], sys.argv[2], sys.argv[3])
