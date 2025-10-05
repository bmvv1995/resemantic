#!/usr/bin/env python3
"""
Test extraction quality pe conversații simulate
Generează raport detaliat pentru analiză
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Neo4jConfig, SQLiteConfig
from neo4j import GraphDatabase
import sqlite3

# Test conversations
CONVERSATIONS = {
    "technical_deepdive": [
        {"role": "user", "content": "Cum configurez un warehouse pentru textile în ERP?"},
        {"role": "assistant", "content": "Pentru warehouse textile ai nevoie de: 1) Zone de stocare separate (bumbac, sintetice, mixte), 2) Reguli de inventar specifice (FIFO pentru sezoniere), 3) Labels cu compoziție materială. Hai să vedem pas cu pas..."},
        {"role": "user", "content": "Am nevoie de integrare cu Shopify pentru sync real-time?"},
        {"role": "assistant", "content": "Da, pentru sync real-time recomand: webhook-uri Shopify pentru comenzi noi, API pentru update stoc, și queue system (Redis) pentru retry la erori de network. Alternativa e polling la 5 min, dar pierde comenzi în rush hours."},
        {"role": "user", "content": "Ok, mergem cu webhooks. Cum handling erorilor?"},
        {"role": "assistant", "content": "Pentru webhooks: 1) Retry exponential (2^n seconds, max 3 attempts), 2) Dead letter queue pentru failed events, 3) Monitoring cu alerting la >5% failure rate. Critic: webhooks trebuie să răspundă în <5s sau Shopify le marchează failed."},
        {"role": "user", "content": "Perfect. Deci decizia: webhooks cu retry logic și DLQ. Implementăm?"},
        {"role": "assistant", "content": "Da! Rezumat decizie: Webhooks pentru real-time sync, exponential retry cu max 3 attempts, DLQ pentru failures, monitoring activ. Reasoning: Real-time > polling pentru customer experience, retry logic previne data loss, DLQ asigură recovery. Începem cu webhook endpoint setup."}
    ],
    
    "problem_solving": [
        {"role": "user", "content": "Stage 1 extraction ia 6 secunde per mesaj. E prea mult!"},
        {"role": "assistant", "content": "6s e mult. Posibile cauze: 1) Prompt size mare (~1500 tokens), 2) Model răspuns lent (network?), 3) JSON parsing complex. Hai să verificăm prompt size primul."},
        {"role": "user", "content": "Da, promptul e lung. Are decorații și exemple multe."},
        {"role": "assistant", "content": "Exact! Decorații = waste tokens. Soluții: A) Compact prompt (400 tokens vs 1500), B) System message (sent once), C) Few-shot minimal (2 examples vs 10). Recomand: B+C = ~70% token reduction."},
        {"role": "user", "content": "Dar quality nu scade cu prompt mai scurt?"},
        {"role": "assistant", "content": "Risc valid! Trade-off: Tokens↓ = Latency↓ + Cost↓, DAR Quality↓?. Mitigare: A/B test (20 msgs cu fiecare), compară quality manual. Dacă quality OK → keep compact. Dacă degradează → keep verbose dar add caching."},
        {"role": "user", "content": "Ok, facem A/B test. Deci decizia: testăm compact prompt, validăm quality, apoi deploy."},
        {"role": "assistant", "content": "Perfect! Decision logged: Compact prompt cu A/B validation. Reasoning: Performance gain justifică test, dar quality e gatekeeper. Next: Implement compact_v2 cu LangSmith tags pentru compare."}
    ],
    
    "mixed_context": [
        {"role": "user", "content": "Salut! Hai sa discutăm despre ReSemantic graph structure."},
        {"role": "assistant", "content": "Bună! Cu plăcere. ReSemantic folosește graph nativ: nodes = propositions, edges = temporal (NEXT) + semantic (COHERENT). Ce te interesează specific?"},
        {"role": "user", "content": "De ce edges ponderate, nu simple connections?"},
        {"role": "assistant", "content": "Weights = semantic similarity scores (0.4-1.0). Permit: 1) Traversal inteligent (follow doar >0.7 pentru high-confidence), 2) Sleep cycles (degrade weak edges), 3) Retrieval rankning. Simple edges = all equal, pierde nuanță."},
        {"role": "user", "content": "Ce mai faci apropo?"},
        {"role": "assistant", "content": "Bine, mulțumesc! Tu cum te simți cu proiectul?"},
        {"role": "user", "content": "Ok, ok. Deci la edges, cum calculating similarity?"},
        {"role": "assistant", "content": "Cosine similarity pe embeddings (1536-dim). Formula: cos(A,B) = A·B / (||A|| ||B||). Result ∈ [-1,1], dar folosim doar [0.4, 1.0] pentru positive correlation. Sub 0.4 = no edge (noise)."},
        {"role": "user", "content": "Mulțumesc, e clar acum!"},
        {"role": "assistant", "content": "Cu plăcere! Dacă mai ai întrebări, sunt aici."}
    ]
}

def analyze_extraction_quality(conversation_name, messages):
    """Rulează extraction și analizează quality"""
    
    print(f"\n{'='*80}")
    print(f"🔬 ANALYZING: {conversation_name}")
    print(f"{'='*80}\n")
    
    # Aici ar rula extraction real prin graph
    # Pentru acum, simulăm să vedem structura raportului
    
    print(f"📊 CONVERSATION STATS:")
    print(f"   Total messages: {len(messages)}")
    print(f"   User messages: {sum(1 for m in messages if m['role'] == 'user')}")
    print(f"   Assistant messages: {sum(1 for m in messages if m['role'] == 'assistant')}")
    
    # Message length distribution
    lengths = [len(m['content']) for m in messages]
    print(f"\n📏 MESSAGE LENGTHS:")
    print(f"   Min: {min(lengths)} chars")
    print(f"   Max: {max(lengths)} chars")
    print(f"   Avg: {sum(lengths)/len(lengths):.0f} chars")
    
    # Simulate extraction results
    print(f"\n🧪 EXTRACTION SIMULATION:")
    print(f"   (Run actual extraction to populate this)")
    print(f"   Expected propositions: ~{len(messages) * 3} (avg 3 per msg)")
    print(f"   Expected concepts: ??? (to analyze)")
    print(f"   Expected decisions: ??? (to track)")
    
    return {
        "name": conversation_name,
        "message_count": len(messages),
        "avg_length": sum(lengths)/len(lengths)
    }

def main():
    print("🧪 RESEMANTIC EXTRACTION QUALITY TEST")
    print("="*80)
    
    results = []
    
    for name, messages in CONVERSATIONS.items():
        result = analyze_extraction_quality(name, messages)
        results.append(result)
    
    print(f"\n\n📋 SUMMARY:")
    print(f"{'='*80}")
    for r in results:
        print(f"   {r['name']:20} | {r['message_count']:2} msgs | {r['avg_length']:.0f} chars avg")
    
    print(f"\n✅ Next: Implementare extraction real și analiza output!")

if __name__ == "__main__":
    main()
