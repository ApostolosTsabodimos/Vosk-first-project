# Voice to Cursor — Vision & Roadmap

A living document. Ideas go here first, then get refined, then become GitHub issues, then become code.

---

## Core Thesis

We are not building a dictation tool. We are building a **voice interface for technical work** — one that understands domain context, runs entirely locally, and lives inside the editor.

Commercial tools (Dragon, Whisper cloud APIs, Copilot) are either generic, cloud-dependent, or both. Our differentiator: **local, open-source, and domain-aware**.

---

## Phase 1: Math Dictation That Actually Works

This is the hardest unsolved problem in voice-to-text and the one worth solving first. The current Ollama-based approach (dump raw transcription into an LLM prompt) works for trivial cases but fails on anything nested or ambiguous.

### Why math dictation is hard

1. **Math is 2D, speech is 1D.** A fraction has a numerator *above* a denominator — speech is linear.
2. **Ambiguity is everywhere.** "Two thirds" — is it `\frac{2}{3}` or the words "two thirds"? "f of x plus y" — is it `f(x+y)` or `f(x) + y`?
3. **No standard exists.** Mathematicians don't agree on how to *speak* math. The 1983 *Handbook for Spoken Mathematics* (Lawrence Chang) tried to standardize it but never gained universal adoption.
4. **LLMs aren't reliable here.** Recent research (2025) shows LLMs have strong bias toward *written* LaTeX and struggle with naturally spoken verbalizations. They hallucinate notation.

### Prior art and what we can learn

| Project | Approach | Strength | Weakness |
|---------|----------|----------|----------|
| **SayTeX** (MIT, 2019) | Strict grammar: rigid 1-to-1 spoken commands to LaTeX | Unambiguous, predictable | Unnatural — must memorize syntax |
| **VoTeX** (LA Hacks) | ML model learns speech-to-LaTeX associations | More natural input | Unreliable without massive training data |
| **Phoenix** (2025) | Context-aware — tracks previously entered equations | Resolves ambiguity using surrounding math | Research prototype, not usable |
| **Speech Rule Engine** | Converts math *to* speech via semantic trees | Proves that structured intermediate representations work | Solves the inverse problem |
| **Greek2MathTeX** (2024) | Greek speech to LaTeX via ASR + post-correction | Multilingual | Narrow scope |
| **S2L Dataset** (2024) | 66k human + 571k synthetic samples for speech-to-LaTeX | Shows the data scale needed for end-to-end ML | Dataset only, no usable system |
| **Handbook for Spoken Mathematics** (1983) | Standardized verbal expressions with explicit delimiters | Battle-tested conventions | Never widely adopted |

**Key insight from the research**: The projects that *work* (SayTeX, the Handbook) use **explicit structure in speech** — delimiters like "begin fraction ... over ... end fraction". The projects that try pure natural language either need enormous datasets or fail on anything complex.

### Our approach: Structured Natural Speech + Context

We don't want the rigidity of SayTeX or the unreliability of pure LLM translation. The design is a **three-layer pipeline**:

```
[Voice] → [Whisper ASR] → [Structured Parser] → [Context-Aware LLM] → [LaTeX]
```

#### Layer 1: Speech conventions (the user learns these)

The user speaks math using lightweight conventions. These are closer to how mathematicians *actually* talk than SayTeX's rigid commands, but with enough structure to be unambiguous.

**Delimiter pairs** for nested structures:

| Spoken | LaTeX | Notes |
|--------|-------|-------|
| "fraction ... over ... end fraction" | `\frac{...}{...}` | Explicit start/end |
| "power ... end power" | `^{...}` | For complex exponents |
| "sub ... end sub" | `_{...}` | For complex subscripts |
| "begin paren ... end paren" | `\left( ... \right)` | Grouping |
| "begin bracket ... end bracket" | `\left[ ... \right]` | Grouping |
| "integral from ... to ... of ... d ..." | `\int_{...}^{...} ... \, d...` | Natural phrasing |
| "sum from ... to ... of ..." | `\sum_{...}^{...} ...` | Natural phrasing |
| "limit as ... approaches ..." | `\lim_{... \to ...}` | Natural phrasing |
| "square root of ... end root" | `\sqrt{...}` | Explicit end |
| "nth root of ... end root" | `\sqrt[n]{...}` | Explicit end |

**Simple cases need no delimiters** — the parser infers structure:

| Spoken | LaTeX | Rule |
|--------|-------|------|
| "x squared" | `x^2` | `<var> squared/cubed` → simple exponent |
| "x sub i" | `x_i` | `<var> sub <var>` → simple subscript |
| "alpha plus beta" | `\alpha + \beta` | Greek letter names → commands |
| "pi" | `\pi` | Direct mapping |
| "infinity" | `\infty` | Direct mapping |
| "dot dot dot" or "ellipsis" | `\ldots` | Direct mapping |

**Mode signals** to separate math from prose:

| Spoken | Effect |
|--------|--------|
| "math mode" / "inline math" | Opens `$...$`, everything until "end math" is parsed as math |
| "display math" | Opens `\[...\]` |
| "end math" | Closes the current math environment |
| "text mode" | Returns to prose (default) |
| "equation" / "end equation" | Opens/closes `\begin{equation}...\end{equation}` |

**Example dictation session:**

> "In this section we prove that the series converges. Display math. Sum from n equals 1 to infinity of fraction 1 over n squared end fraction equals fraction pi squared over 6 end fraction. End math. The proof uses the integral test."

Produces:
```latex
In this section we prove that the series converges.
\[
\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}
\]
The proof uses the integral test.
```

#### Layer 2: The Structured Parser

A rule-based parser (not an LLM) that handles the unambiguous parts:
- Tokenize the transcription
- Match delimiter pairs ("fraction ... over ... end fraction")
- Resolve simple patterns ("x squared", "alpha", Greek letters)
- Track math/text mode state
- Build a **semantic tree** (inspired by Speech Rule Engine) as intermediate representation

This parser handles ~80% of cases deterministically. No hallucination, no latency, no model dependency.

#### Layer 3: Context-Aware LLM (for the remaining 20%)

The LLM handles ambiguity, corrections, and edge cases:
- **Surrounding context**: Feed the previous 5-10 lines of the document. If the user has been writing about `$\sigma$-algebras`, then "sigma" is `\sigma`, not `\Sigma`.
- **Ambiguity resolution**: When the parser can't determine structure, the LLM resolves it using context.
- **Correction**: "No, I meant x cubed not x squared" — the LLM understands corrections in context.
- **Style matching**: If the document uses `\left(` and `\right)` for delimiters, the output should too.

The LLM is a **fallback and refinement layer**, not the primary translator. This is the key architectural decision — it means the system works even if Ollama is down (just with less polish).

#### Layer 4 (Future): Feedback loop

- Track when the user edits LLM-corrected output (the correction was wrong)
- Build a personal dictionary of term preferences
- Over time, the parser rules improve and the LLM is needed less

### Implementation plan for math dictation

```
Step 1: Define the speech convention spec (a JSON/YAML file mapping patterns to LaTeX)
Step 2: Build the rule-based parser (Python, no dependencies)
Step 3: Integrate parser before the LLM in the pipeline (parser first, LLM refines)
Step 4: Feed document context to the LLM prompt
Step 5: Add math/text mode tracking as state in the server
Step 6: User testing — dictate real LaTeX documents, iterate on conventions
```

---

## Phase 2: Voice Commands

Once dictation works, add a **command mode** so the voice interface can control the editor.

### Design

The LLM classifies each utterance as one of:
- **Dictation**: insert text at cursor
- **Command**: execute an editor action
- **Meta**: change voice system settings ("switch to Greek", "slow down")

Commands the system should understand:

| Spoken | Action |
|--------|--------|
| "select last equation" | Highlight the previous math environment |
| "wrap in theorem" | Surround selection with `\begin{theorem}...\end{theorem}` |
| "undo" / "undo that" | Trigger editor undo |
| "new line" / "new paragraph" | Insert `\n` or `\n\n` |
| "go to line 42" | Move cursor |
| "delete last sentence" | Select and delete |
| "compile" | Trigger LaTeX build |
| "save" | Save file |
| "commit with message ..." | Git commit |

### Architecture

```
[Transcription] → [Intent Classifier] → dictation → [Parser + LLM] → insert text
                                       → command  → [Command Router] → VS Code API
                                       → meta     → [Config Update]  → system state
```

The intent classifier can be a small fine-tuned model or even rule-based (commands start with imperative verbs, dictation doesn't).

---

## Phase 3: Multi-Editor & Standalone

The backend is already editor-agnostic. Expand to:

- **Neovim plugin**: Thin Lua WebSocket client (~100 LOC)
- **JetBrains plugin**: Kotlin WebSocket client
- **Emacs package**: elisp WebSocket client
- **Standalone tray app**: For dictating into *any* application via OS-level text insertion (`xdotool type` on X11, `wtype` on Wayland, accessibility APIs on macOS/Windows)

All editors share the same backend — one model loaded, one process running.

---

## Phase 4: Streaming & Real-Time

Currently: record → stop → transcribe → insert (batch mode).

Target: **live transcription** — text appears as you speak, like live captioning.

faster-whisper supports streaming. The challenge is:
- Partial results may be wrong and need correction as more audio arrives
- Math delimiters ("begin fraction") need buffering until the structure is complete
- The editor needs to handle replacing partial text with final text

Design: ghost text (greyed out) for partial results, solidified when confident.

---

## Phase 5: Multilingual & Personal

- **Bilingual dictation**: Greek prose with English mathematical terms, or vice versa. Whisper already supports language detection — extend this to per-segment detection.
- **Custom vocabulary**: Personal dictionary of frequently used terms, theorem names, citation keys. Biases Whisper's beam search.
- **Voice profiles**: The system learns your pronunciation patterns over time. "When Apostolos says 'sigma', he means lowercase 98% of the time."

---

## Phase 6: The Moonshot — Open-Source Copilot Voice

An open-source, local-first, privacy-preserving voice interface for programming and technical writing. Features:
- Voice-driven coding with full editor integration
- Domain-aware transcription (LaTeX, code, prose)
- Context-aware — reads your document, understands your project
- Works offline, no cloud, no telemetry
- Accessibility-first — usable by developers with RSI or motor disabilities
- Plugin architecture for custom post-processors and domain vocabularies

**Why this matters**: There is no serious open-source voice interface for programming. GitHub Copilot has no voice mode. Dragon NaturallySpeaking doesn't understand code or LaTeX. Talon is powerful but has a steep learning curve. There's a real gap.

---

## Open Questions

- [ ] Should the speech conventions be configurable per-user, or should we pick one standard and stick with it?
- [ ] How to handle corrections? "No wait, I meant..." — does this require undo support?
- [ ] Should the parser be a formal grammar (PEG/CFG) or pattern-matching rules?
- [ ] What's the minimum viable set of math speech conventions to cover 90% of undergraduate LaTeX?
- [ ] Can we use Whisper's word-level timestamps to improve delimiter matching?
- [ ] How to handle dictation in languages other than English while keeping math commands in English?

---

## References

- [SayTeX](https://github.com/arvid220u/saytex) — MIT, grammar-based spoken LaTeX
- [Handbook for Spoken Mathematics](https://dokumen.pub/handbook-for-spoken-mathematics.html) — Lawrence Chang, 1983
- [Speech Rule Engine](https://speechruleengine.org/) — math-to-speech via semantic trees
- [Phoenix](https://arxiv.org/pdf/2508.07576) — context-aware voice math editor (2025)
- [S2L Dataset](https://arxiv.org/html/2508.03542v1) — speech-to-LaTeX dataset (2024)
- [Greek2MathTeX](https://arxiv.org/pdf/2412.12167) — Greek speech to LaTeX (2024)
- [Towards Spoken Mathematical Reasoning](https://arxiv.org/pdf/2505.15000) — benchmarking speech math models (2025)
- [Speakable Math (Fateman, Berkeley)](https://people.eecs.berkeley.edu/~fateman/papers/speakmath.pdf)
- [Ambiguity in Spoken Mathematics](https://files.eric.ed.gov/fulltext/EJ1169645.pdf)
