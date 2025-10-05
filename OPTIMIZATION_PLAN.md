# 🚀 Stage 1 Optimization Plan

## PROBLEMA IDENTIFICATĂ
- Prompt prea verbos: ~1500 tokens
- Latency: 5-7s per mesaj
- 58% din total extraction time

## SOLUȚIE: Prompt Compact + System Message

### ÎNAINTE (1500 tokens):
```python
prompt = f"""TU EȘTI UN ANALIZOR...
═══════════════════
TASK: ... (10 linii)
═══════════════════
EXEMPLE: ... (8 linii)
═══════════════════
...
"""
```

### DUPĂ (400 tokens):
```python
# System message (se trimite o singură dată)
system = """Analizor conversații: extrage semantic unit JSON.
Type: question/statement/command
Certainty: high/medium/low  
Narrative_role: core/supportive/peripheral"""

# User prompt (compact)
prompt = f"""Context: {context}
Message ({role}, {timestamp}): {message}

JSON:
{{
  "unit_id": "{id}",
  "content": "descriere mesaj",
  "type": "...",
  "concepts": [...],
  "certainty": "...",
  "narrative_role": "..."
}}"""
```

## BENEFICII AȘTEPTATE:
- ⚡ Tokens: -70% (1500 → 450)
- ⚡ Latency: -50% (6s → 3s)
- ⚡ Cost: -70%
- ✅ Quality: SAME (esența e păstrată)

## IMPLEMENTARE:

### Opțiunea 1: System Message în ChatAnthropic
```python
llm = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    system=SYSTEM_PROMPT,  # ← Trimis o singură dată
    temperature=0.3
)

# În node:
messages = [{"role": "user", "content": compact_prompt}]
response = llm.invoke(messages)
```

### Opțiunea 2: Few-Shot Examples în System
```python
SYSTEM_PROMPT = """Analizor semantic.

Exemple:
Input: "buna claude"
Output: {"content": "User salută", "type": "greeting", ...}

Input: "cum configurez warehouse?"  
Output: {"content": "User întreabă despre configurare warehouse", "type": "question", ...}

Extrage similar pentru orice mesaj."""
```

### Opțiunea 3: Prompt Template Optimizat
```python
COMPACT_TEMPLATE = """
Context: {context}
Msg: {message}

Extract JSON: unit_id, content, type, concepts, certainty, narrative_role
"""
```

## TESTARE A/B:
1. Tag runs cu "prompt_version": "v1_verbose" / "v2_compact"
2. Rulează 20 mesaje cu fiecare
3. Compară în LangSmith:
   - Latency
   - Quality (manual check propositions)
   - Token count

## ROLLBACK STRATEGY:
Dacă quality degradează → revert la verbose
Dacă quality OK → keep compact, reduce cu încă 20%

## NEXT LEVEL (după success):
- Cache system prompt (Anthropic Prompt Caching)
- Batch multiple messages în 1 request
- Parallel Stage1 user + assistant
