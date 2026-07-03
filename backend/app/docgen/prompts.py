DOCSTRING_PROMPT = """You are an expert Python documentation generator.
Generate a high-quality Google-style docstring for the following Python code snippet.
Return ONLY the docstring itself, enclosed in triple quotes. Do not include any markdown formatting, extra explanation, or code.

Code:
{code_snippet}
"""

README_SECTION_PROMPT = """You are an expert technical writer and developer.
Draft the '{section_name}' section of a README.md file for a repository based on the provided audit summary and code details.

Context & Code Details:
{context}

Guidelines:
- Return ONLY the content for the '{section_name}' section.
- Use professional, clear, and descriptive Markdown formatting.
- Do not repeat the section name as a title if it would create redundant headings.
- Be concise and focus on actual implementation details rather than generic placeholders.
"""
