"""LaTeX post-processing: converts spoken math to LaTeX via Ollama."""

from backend.ollama_client import generate

LATEX_SYSTEM_PROMPT = """\
You are a LaTeX transcription assistant. You receive speech-to-text output that \
may contain spoken mathematics. Your job:

1. Convert spoken math notation into valid LaTeX commands.
2. Leave prose and non-math text UNCHANGED.
3. Do NOT add document preamble, \\begin{document}, or any wrapping.
4. Do NOT explain your changes. Output ONLY the corrected text.

Examples of conversions:
- "fraction x over y" -> \\frac{x}{y}
- "x squared plus y squared equals z squared" -> $x^2 + y^2 = z^2$
- "the integral from zero to infinity of e to the minus x dx" -> $\\int_0^{\\infty} e^{-x} \\, dx$
- "consider the function f of x" -> "consider the function $f(x)$"
- "In this section we prove" -> "In this section we prove" (unchanged, pure prose)
- "alpha plus beta" -> $\\alpha + \\beta$
- "sum from i equals 1 to n" -> $\\sum_{i=1}^{n}$\
"""


def process(text: str, file_type: str, model: str = "mistral", temperature: float = 0.3) -> str:
    """Post-process transcription. Only applies LaTeX conversion for .tex files."""
    if file_type != ".tex":
        return text

    if not text.strip():
        return text

    result = generate(
        prompt=text,
        system=LATEX_SYSTEM_PROMPT,
        model=model,
        temperature=temperature,
    )

    # Fall back to raw text if Ollama fails
    return result if result.strip() else text
