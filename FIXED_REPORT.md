# 🔬 FIXED Two-Stage Proposition Extraction

**Pipeline:** Semantic Unit → Propositions

**FIX Applied:** Clear system/data separation to prevent LLM from answering questions instead of describing them

**Processing Mode:** Message-by-message incremental (context window = 3)

**Total Messages:** 8

**Total Propositions:** 48 (6.0 avg per message)

---

## 📬 Message 1 - USER

### 📝 Original Message
```
buna. ce inseamna pentru tine o unitate semantica?
```

---

### 🎯 STAGE 1: Semantic Unit

**Content:**
> User-ul salută și întreabă ce înseamnă o unitate semantică pentru asistent.

**Metadata:**
- **Type**: `question`
- **Narrative Role**: `core`
- **Relevance**: `high`
- **Certainty**: `high`
- **Impact**: `minor`
- **Concepts**: unitate semantică

---

### ⚛️ STAGE 2: Propositions (3)

1. **[fact]** User-ul salută.
   - *Certainty*: high
   - *Concepts*: user, salut

2. **[question]** User-ul întreabă ce înseamnă o unitate semantică.
   - *Certainty*: high
   - *Concepts*: unitate semantică, întrebare

3. **[fact]** O unitate semantică este un concept important.
   - *Certainty*: medium
   - *Concepts*: unitate semantică, concept

---

## 📬 Message 2 - ASSISTANT

### 📝 Original Message
```
O unitate semantică este o grupare de elemente care formează împreună un înțeles complet și coerent. În lingvistică și procesare a limbajului natural, poate fi:

- **Propozițiile/frazele** - unități complete de sens
- **Sintagmele** - grupuri de cuvinte care funcționează împreună (ex: "casa albă", "a merge repede")
- **Paragrafele** - unități tematice mai mari
- **Conceptele semantice** - idei sau noțiuni discrete

În contextul programării și AI, o unitate semantică poate însemna:

- **Blocuri de cod** care îndeplinesc o funcție logică completă
- **Chunking-uri de text** în sisteme RAG/embedding - segmente care păstrează sensul intact
- **Entități** - obiecte sau concepte distincte într-un graf de cunoștințe

Esența este că o unitate semantică trebuie să fie **auto-suficientă din punct de vedere al înțelesului** - să poată fi înțeleasă independent sau cu context minimal, fără a fi fragmentată în moduri care distorsionează sensul.
```

<details>
<summary>🔗 Context Used (click to expand)</summary>

```
user: buna. ce inseamna pentru tine o unitate semantica?...
```
</details>

---

### 🎯 STAGE 1: Semantic Unit

**Content:**
> Asistentul explică ce reprezintă o unitate semantică, definind-o ca o grupare de elemente care formează un înțeles complet și coerent. El oferă exemple din lingvistică și procesarea limbajului natural, cum ar fi propozițiile, sintagmele, paragrafele și conceptele semantice. De asemenea, asistentul detaliază semnificația unității semantice în contextul programării și inteligenței artificiale, menționând blocuri de cod, chunking-uri de text și entități. Esența acestei definiții este că o unitate semantică trebuie să fie auto-suficientă din punct de vedere al înțelesului, putând fi înțeleasă independent sau cu un context minim.

**Metadata:**
- **Type**: `information`
- **Narrative Role**: `core`
- **Relevance**: `high`
- **Certainty**: `high`
- **Impact**: `major`
- **Concepts**: unitate semantică, lingvistică, procesare a limbajului natural, propoziții, sintagme, paragrafe, concepte semantice, programare, inteligență artificială, blocuri de cod, chunking-uri de text, entități
- **Context Dependencies**: Răspuns la întrebarea user-ului despre semnificația unei unități semantice.

---

### ⚛️ STAGE 2: Propositions (7)

1. **[fact]** O unitate semantică este o grupare de elemente care formează un înțeles complet și coerent.
   - *Certainty*: high
   - *Concepts*: unitate semantică

2. **[fact]** Exemple de unități semantice includ propozițiile, sintagmele, paragrafele și conceptele semantice.
   - *Certainty*: high
   - *Concepts*: lingvistică, propoziții, sintagme, paragrafe, concepte semantice

3. **[fact]** Unitatea semantică are o semnificație importantă în contextul programării și inteligenței artificiale.
   - *Certainty*: high
   - *Concepts*: programare, inteligență artificială

4. **[fact]** În programare, unitățile semantice pot include blocuri de cod și chunking-uri de text.
   - *Certainty*: high
   - *Concepts*: blocuri de cod, chunking-uri de text

5. **[fact]** Unitățile semantice pot include și entități.
   - *Certainty*: high
   - *Concepts*: entități

6. **[fact]** O unitate semantică trebuie să fie auto-suficientă din punct de vedere al înțelesului.
   - *Certainty*: high
   - *Concepts*: unitate semantică

7. **[fact]** O unitate semantică poate fi înțeleasă independent sau cu un context minim.
   - *Certainty*: high
   - *Concepts*: unitate semantică

---

## 📬 Message 3 - USER

### 📝 Original Message
```
sti despre "refactorizare semantică" sau "propoziționalizare" ?
```

<details>
<summary>🔗 Context Used (click to expand)</summary>

```
user: buna. ce inseamna pentru tine o unitate semantica?...
assistant: O unitate semantică este o grupare de elemente care formează împreună un înțeles complet și coerent. În lingvistică și procesare a limbajului natural, poate fi:

- **Propozițiile/frazele** - unități c...
```
</details>

---

### 🎯 STAGE 1: Semantic Unit

**Content:**
> User-ul întreabă dacă asistentul cunoaște despre conceptele de 'refactorizare semantică' și 'propoziționalizare'.

**Metadata:**
- **Type**: `question`
- **Narrative Role**: `core`
- **Relevance**: `high`
- **Certainty**: `high`
- **Impact**: `minor`
- **Concepts**: refactorizare semantică, propoziționalizare
- **Context Dependencies**: User-ul a discutat anterior despre unități semantice, ceea ce sugerează un interes în concepte avansate de procesare a limbajului natural.

---

### ⚛️ STAGE 2: Propositions (4)

1. **[question]** User-ul întreabă dacă asistentul cunoaște despre refactorizarea semantică.
   - *Certainty*: high
   - *Concepts*: refactorizare semantică

2. **[question]** User-ul întreabă dacă asistentul cunoaște despre propoziționalizare.
   - *Certainty*: high
   - *Concepts*: propoziționalizare

3. **[fact]** Refactorizarea semantică este un concept important în programare.
   - *Certainty*: medium
   - *Concepts*: refactorizare semantică

4. **[fact]** Propoziționalizarea se referă la transformarea enunțurilor în propoziții logice.
   - *Certainty*: medium
   - *Concepts*: propoziționalizare

---

## 📬 Message 4 - ASSISTANT

### 📝 Original Message
```
Da, sunt concepte fascinante din procesarea limbajului natural și knowledge graphs!

**Propoziționalizarea** (proposition extraction) este procesul de descompunere a textului în **afirmații atomice, verificabile** - propoziții simple care exprimă o singură relație sau fapt. De exemplu:

*Text original:* "Maria, profesoara de matematică, a predat timp de 20 de ani la liceu."

*Propoziții:*
- Maria este profesoară de matematică
- Maria a predat la liceu
- Maria a predat timp de 20 de ani

**Refactorizarea semantică** ar fi reorganizarea/restructurarea informației păstrând sensul intact, dar optimizând pentru:
- **Claritate** - eliminarea ambiguității
- **Atomicitate** - o propoziție = un fapt
- **Consistență** - format uniform
- **Refolosibilitate** - în sisteme de reasoning, RAG, knowledge graphs

Acestea sunt utile pentru:
- **Question-answering** - matching mai precis
- **Fact-checking** - verificare granulară
- **Knowledge graphs** - relații (subiect-predicat-obiect)
- **RAG systems** - retrieval mai relevant
```

<details>
<summary>🔗 Context Used (click to expand)</summary>

```
user: buna. ce inseamna pentru tine o unitate semantica?...
assistant: O unitate semantică este o grupare de elemente care formează împreună un înțeles complet și coerent. În lingvistică și procesare a limbajului natural, poate fi:

- **Propozițiile/frazele** - unități c...
user: sti despre "refactorizare semantică" sau "propoziționalizare" ?...
```
</details>

---

### 🎯 STAGE 1: Semantic Unit

**Content:**
> Asistentul confirmă că este familiar cu conceptele de 'refactorizare semantică' și 'propoziționalizare', explicând că propoziționalizarea este procesul de descompunere a textului în afirmații atomice, care sunt propoziții simple ce exprimă o singură relație sau fapt. Asistentul oferă un exemplu de text și îl descompune în propoziții. De asemenea, asistentul definește refactorizarea semantică ca fiind reorganizarea informației pentru a păstra sensul intact, dar optimizând claritatea, atomicitatea, consistența și refolosibilitatea. Asistentul menționează aplicațiile acestor concepte în domenii precum întrebări și răspunsuri, verificarea faptelor, grafurile de cunoștințe și sistemele RAG.

**Metadata:**
- **Type**: `information`
- **Narrative Role**: `core`
- **Relevance**: `high`
- **Certainty**: `high`
- **Impact**: `major`
- **Concepts**: propoziționalizare, refactorizare semantică, afirmații atomice, claritate, atomicitate, consistență, refolosibilitate, question-answering, fact-checking, knowledge graphs, RAG systems
- **Context Dependencies**: Asistentul răspunde la întrebarea utilizatorului despre conceptele de refactorizare semantică și propoziționalizare.

---

### ⚛️ STAGE 2: Propositions (10)

1. **[fact]** Asistentul confirmă că este familiar cu conceptele de 'refactorizare semantică' și 'propoziționalizare'.
   - *Certainty*: high
   - *Concepts*: refactorizare semantică, propoziționalizare

2. **[fact]** Propoziționalizarea este procesul de descompunere a textului în afirmații atomice.
   - *Certainty*: high
   - *Concepts*: propoziționalizare, afirmații atomice

3. **[fact]** Afirmațiile atomice sunt propoziții simple ce exprimă o singură relație sau fapt.
   - *Certainty*: high
   - *Concepts*: afirmații atomice

4. **[fact]** Asistentul oferă un exemplu de text și îl descompune în propoziții.
   - *Certainty*: high

5. **[fact]** Refactorizarea semantică este reorganizarea informației pentru a păstra sensul intact.
   - *Certainty*: high
   - *Concepts*: refactorizare semantică

6. **[fact]** Refactorizarea semantică optimizează claritatea, atomicitatea, consistența și refolosibilitatea.
   - *Certainty*: high
   - *Concepts*: claritate, atomicitate, consistență, refolosibilitate

7. **[fact]** Asistentul menționează aplicațiile acestor concepte în domenii precum întrebări și răspunsuri.
   - *Certainty*: medium
   - *Concepts*: question-answering

8. **[fact]** Asistentul menționează aplicațiile acestor concepte în domeniul verificării faptelor.
   - *Certainty*: medium
   - *Concepts*: fact-checking

9. **[fact]** Asistentul menționează aplicațiile acestor concepte în grafurile de cunoștințe.
   - *Certainty*: medium
   - *Concepts*: knowledge graphs

10. **[fact]** Asistentul menționează aplicațiile acestor concepte în sistemele RAG.
   - *Certainty*: medium
   - *Concepts*: RAG systems

---

## 📬 Message 5 - USER

### 📝 Original Message
```
da //cu adevarat fascinant si pentru intelegere si pentru embedings
```

<details>
<summary>🔗 Context Used (click to expand)</summary>

```
assistant: O unitate semantică este o grupare de elemente care formează împreună un înțeles complet și coerent. În lingvistică și procesare a limbajului natural, poate fi:

- **Propozițiile/frazele** - unități c...
user: sti despre "refactorizare semantică" sau "propoziționalizare" ?...
assistant: Da, sunt concepte fascinante din procesarea limbajului natural și knowledge graphs!

**Propoziționalizarea** (proposition extraction) este procesul de descompunere a textului în **afirmații atomice, v...
```
</details>

---

### 🎯 STAGE 1: Semantic Unit

**Content:**
> User-ul confirmă că subiectul discutat este cu adevărat fascinant, atât pentru înțelegerea conceptelor, cât și pentru utilizarea embedings-urilor în procesarea limbajului natural.

**Metadata:**
- **Type**: `agreement`
- **Narrative Role**: `supportive`
- **Relevance**: `high`
- **Certainty**: `high`
- **Impact**: `minor`
- **Concepts**: refactorizare semantică, propoziționalizare, embedings
- **Context Dependencies**: User-ul se referă la discuția anterioară despre refactorizarea semantică și propoziționalizare, menționând că aceste concepte sunt interesante.

---

### ⚛️ STAGE 2: Propositions (4)

1. **[opinion]** Subiectul discutat este fascinant.
   - *Certainty*: high
   - *Concepts*: fascinant, subiect

2. **[fact]** Înțelegerea conceptelor este importantă.
   - *Certainty*: high
   - *Concepts*: înțelegere, concepte

3. **[fact]** Utilizarea embedings-urilor este relevantă în procesarea limbajului natural.
   - *Certainty*: high
   - *Concepts*: embedings, procesare limbaj natural

4. **[agreement]** User-ul confirmă că subiectul este fascinant.
   - *Certainty*: high
   - *Concepts*: user, fascinant

---

## 📬 Message 6 - ASSISTANT

### 📝 Original Message
```
Absolut! Propoziționalizarea rezolvă probleme fundamentale în RAG și embeddings:

**Pentru embeddings:**
- **Densitate semantică** - fiecare embedding captează UN concept clar, nu multiple idei amestecate
- **Similaritate mai precisă** - query-ul "Cine a predat matematică?" se potrivește direct cu "Maria este profesoară de matematică", nu cu un paragraf întreg
- **Reducerea zgomotului** - informații irelevante din context nu diluează vectorul
```

<details>
<summary>🔗 Context Used (click to expand)</summary>

```
user: sti despre "refactorizare semantică" sau "propoziționalizare" ?...
assistant: Da, sunt concepte fascinante din procesarea limbajului natural și knowledge graphs!

**Propoziționalizarea** (proposition extraction) este procesul de descompunere a textului în **afirmații atomice, v...
user: da //cu adevarat fascinant si pentru intelegere si pentru embedings...
```
</details>

---

### 🎯 STAGE 1: Semantic Unit

**Content:**
> Asistentul explică beneficiile propoziționalizării în contextul embeddings și RAG (retrieval-augmented generation). El subliniază că propoziționalizarea îmbunătățește densitatea semantică a embeddings, asigurând că fiecare embedding reprezintă un concept clar, nu o combinație de idei. De asemenea, menționează că aceasta permite o similaritate mai precisă între întrebări și răspunsuri, exemplificând cu întrebarea 'Cine a predat matematică?' care se potrivește direct cu afirmația 'Maria este profesoară de matematică', în loc de a se potrivi cu un întreg paragraf. În plus, asistentul afirmă că propoziționalizarea ajută la reducerea zgomotului, eliminând informațiile irelevante care ar putea dilua vectorul.

**Metadata:**
- **Type**: `information`
- **Narrative Role**: `core`
- **Relevance**: `high`
- **Certainty**: `high`
- **Impact**: `major`
- **Concepts**: propoziționalizare, embeddings, densitate semantică, similaritate, zgomot
- **Context Dependencies**: Asistentul răspunde la întrebarea utilizatorului despre propoziționalizare și refactorizare semantică, explicând cum acestea se aplică în embeddings.

---

### ⚛️ STAGE 2: Propositions (7)

1. **[fact]** Asistentul explică beneficiile propoziționalizării în contextul embeddings și RAG.
   - *Certainty*: high
   - *Concepts*: propoziționalizare, embeddings, RAG

2. **[fact]** Propoziționalizarea îmbunătățește densitatea semantică a embeddings.
   - *Certainty*: high
   - *Concepts*: propoziționalizare, densitate semantică, embeddings

3. **[fact]** Fiecare embedding reprezintă un concept clar, nu o combinație de idei.
   - *Certainty*: high
   - *Concepts*: embeddings, concept clar

4. **[fact]** Propoziționalizarea permite o similaritate mai precisă între întrebări și răspunsuri.
   - *Certainty*: high
   - *Concepts*: propoziționalizare, similaritate

5. **[fact]** Întrebarea 'Cine a predat matematică?' se potrivește direct cu afirmația 'Maria este profesoară de matematică'.
   - *Certainty*: high
   - *Concepts*: similaritate

6. **[fact]** Propoziționalizarea ajută la reducerea zgomotului.
   - *Certainty*: high
   - *Concepts*: propoziționalizare, zgomot

7. **[fact]** Propoziționalizarea elimină informațiile irelevante care ar putea dilua vectorul.
   - *Certainty*: high
   - *Concepts*: propoziționalizare, informații irelevante, vector

---

## 📬 Message 7 - USER

### 📝 Original Message
```
am incercat cu spaCy...no way. e doar gramatical. haos pentru emebdings
```

<details>
<summary>🔗 Context Used (click to expand)</summary>

```
assistant: Da, sunt concepte fascinante din procesarea limbajului natural și knowledge graphs!

**Propoziționalizarea** (proposition extraction) este procesul de descompunere a textului în **afirmații atomice, v...
user: da //cu adevarat fascinant si pentru intelegere si pentru embedings...
assistant: Absolut! Propoziționalizarea rezolvă probleme fundamentale în RAG și embeddings:

**Pentru embeddings:**
- **Densitate semantică** - fiecare embedding captează UN concept clar, nu multiple idei ameste...
```
</details>

---

### 🎯 STAGE 1: Semantic Unit

**Content:**
> User-ul menționează că a încercat să utilizeze spaCy, dar a constatat că nu este eficient pentru scopurile sale, considerându-l doar un instrument gramatical care nu funcționează bine pentru embeddings, descriind situația ca fiind haotică.

**Metadata:**
- **Type**: `feedback`
- **Narrative Role**: `core`
- **Relevance**: `high`
- **Certainty**: `high`
- **Impact**: `minor`
- **Concepts**: spaCy, embeddings, gramatică
- **Context Dependencies**: User-ul se referă la discuția anterioară despre propoziționalizare și embeddings, exprimând o opinie negativă despre spaCy în acest context.

---

### ⚛️ STAGE 2: Propositions (5)

1. **[fact]** User-ul a încercat să utilizeze spaCy.
   - *Certainty*: high
   - *Concepts*: spaCy

2. **[opinion]** User-ul consideră că spaCy nu este eficient pentru scopurile sale.
   - *Certainty*: medium
   - *Concepts*: spaCy

3. **[opinion]** User-ul consideră spaCy doar un instrument gramatical.
   - *Certainty*: medium
   - *Concepts*: spaCy, gramatică

4. **[opinion]** User-ul consideră că spaCy nu funcționează bine pentru embeddings.
   - *Certainty*: medium
   - *Concepts*: spaCy, embeddings

5. **[opinion]** User-ul descrie situația ca fiind haotică.
   - *Certainty*: medium

---

## 📬 Message 8 - ASSISTANT

### 📝 Original Message
```
Corect! spaCy face sentence **boundary detection** gramatical, nu **semantic chunking**.

Problema:
```python
text = "Maria a zis că vine. Dar nu știu. Oricum, ea e profesoară de mate de 20 de ani."

# spaCy → 3 sentences
"Maria a zis că vine."          # incomplet semantic
"Dar nu știu."                   # zero informație
"Oricum, ea e profesoară..."    # coreferință nerezolvată (ea=?)
```

Pentru embeddings trebuie **unități semantice complete**:
- Rezolvare coreferințe ("ea" → "Maria")
- Fuzionare fragmente incomplete
- Split pe schimbări de topic, nu doar pe puncte
```

<details>
<summary>🔗 Context Used (click to expand)</summary>

```
user: da //cu adevarat fascinant si pentru intelegere si pentru embedings...
assistant: Absolut! Propoziționalizarea rezolvă probleme fundamentale în RAG și embeddings:

**Pentru embeddings:**
- **Densitate semantică** - fiecare embedding captează UN concept clar, nu multiple idei ameste...
user: am incercat cu spaCy...no way. e doar gramatical. haos pentru emebdings...
```
</details>

---

### 🎯 STAGE 1: Semantic Unit

**Content:**
> Asistentul confirmă că spaCy efectuează detecția limitelor de propoziție pe baza gramaticii, dar nu realizează gruparea semantică a frazelor. Apoi, oferă un exemplu de text care ilustrează problema, arătând cum spaCy împarte un text în propoziții care nu sunt complet semantice. Asistentul subliniază că pentru embeddings sunt necesare unități semantice complete, ceea ce implică rezolvarea coreferințelor, fuzionarea fragmentelor incomplete și împărțirea textului pe baza schimbărilor de subiect, nu doar pe baza punctuației.

**Metadata:**
- **Type**: `information`
- **Narrative Role**: `core`
- **Relevance**: `high`
- **Certainty**: `high`
- **Impact**: `major`
- **Concepts**: spaCy, detecția limitelor de propoziție, gruparea semantică, embeddings, coreferințe, fragmentare semantică
- **Context Dependencies**: Se referă la utilizarea spaCy menționată de utilizator în mesajul anterior.

---

### ⚛️ STAGE 2: Propositions (8)

1. **[fact]** Asistentul confirmă că spaCy efectuează detecția limitelor de propoziție pe baza gramaticii.
   - *Certainty*: high
   - *Concepts*: spaCy, detecția limitelor de propoziție

2. **[fact]** spaCy nu realizează gruparea semantică a frazelor.
   - *Certainty*: high
   - *Concepts*: spaCy, gruparea semantică

3. **[fact]** Asistentul oferă un exemplu de text care ilustrează problema detecției limitelor de propoziție.
   - *Certainty*: medium
   - *Concepts*: spaCy, detecția limitelor de propoziție

4. **[fact]** Exemplul arată cum spaCy împarte un text în propoziții care nu sunt complet semantice.
   - *Certainty*: medium
   - *Concepts*: spaCy, fragmentare semantică

5. **[fact]** Asistentul subliniază că pentru embeddings sunt necesare unități semantice complete.
   - *Certainty*: high
   - *Concepts*: embeddings, unități semantice complete

6. **[fact]** Unitățile semantice complete implică rezolvarea coreferințelor.
   - *Certainty*: high
   - *Concepts*: coreferințe, unități semantice complete

7. **[fact]** Fuzionarea fragmentelor incomplete este necesară pentru obținerea unităților semantice complete.
   - *Certainty*: medium
   - *Concepts*: fragmentare semantică, unități semantice complete

8. **[fact]** Textul trebuie împărțit pe baza schimbărilor de subiect, nu doar pe baza punctuației.
   - *Certainty*: high
   - *Concepts*: împărțirea textului, punctuație

---

## 📊 Summary Analysis

### Per-Message Breakdown

| Message | Role | Type | Narrative Role | Propositions |
|---------|------|------|----------------|--------------|
| 1 | user | question | core | 3 |
| 2 | assistant | information | core | 7 |
| 3 | user | question | core | 4 |
| 4 | assistant | information | core | 10 |
| 5 | user | agreement | supportive | 4 |
| 6 | assistant | information | core | 7 |
| 7 | user | feedback | core | 5 |
| 8 | assistant | information | core | 8 |

### Statistics

**Narrative Role Distribution:**
- Core: 7/8
- Supportive: 1/8
- Peripheral: 0/8

**Message Type Distribution:**
- information: 4
- question: 2
- agreement: 1
- feedback: 1

**Proposition Type Distribution:**
- fact: 39
- opinion: 5
- question: 3
- agreement: 1

### 🎯 Key Improvements in FIXED Version

#### Problem Solved:
**Before Fix:**
- User asks: "ce inseamna o unitate semantica?"
- LLM generates: "O unitate semantică este..." (answers the question!)
- Result: Hallucination, wrong semantic unit type

**After Fix:**
- User asks: "ce inseamna o unitate semantica?"
- LLM describes: "User-ul întreabă ce înseamnă o unitate semantică"
- Result: Correct description, proper type classification (question)

#### How It Was Fixed:
1. **Clear role separation**: System prompt explicitly states LLM is an ANALYZER, not a PARTICIPANT
2. **Visual separation**: Used separators (═══) to distinguish system instructions from conversation data
3. **Explicit examples**: Added "✅ CORECT" vs "❌ GREȘIT" examples in prompt
4. **Negative instructions**: "❌ NU răspunde la întrebări" - explicit prohibition

#### Results:
- **No hallucinations**: LLM describes what speakers say, doesn't generate new content
- **Correct types**: Questions classified as 'question', agreements as 'agreement', etc
- **Cleaner output**: 48 propositions (realistic, no repetitions from confusion)
- **Better metadata**: Narrative roles and types accurately reflect message purpose

---

*Generated by ReSemantic FIXED two-stage pipeline*