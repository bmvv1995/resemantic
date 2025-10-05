# 🛡️ Claude Code Safety Template & Rules

**PENTRU TINE: Folosește MEREU acest template când dai task-uri la Claude Code!**

---

## 📋 TASK TEMPLATE (copy-paste & completează)

```markdown
=== TASK FOR CLAUDE CODE ===

🎯 GOAL:
[Exact ce vrei să realizezi - o propoziție clară]

📁 FILES:
Target: [exact filename.py]
Method: **EDIT ONLY** (surgical changes, NOT full rewrite!)
Location: [function name / class / lines X-Y]

⚠️ CRITICAL CONSTRAINTS:
❌ NO file versions (no _v1, _v2, _updated, _final, etc)
❌ NO structural changes (keep architecture intact)
❌ NO mock/fake data (ASK for credentials if missing)
❌ NO wholesale file rewrites (EDIT specific lines only)
❌ NO "improvements" to code not in scope

✅ PRESERVE (don't touch these):
- [list specific things to keep intact]
- 
- 

🔍 VALIDATION:
Success looks like: [how you'll verify it works]
Test command: [if applicable]

❓ IF UNCLEAR:
→ ASK questions, don't guess!
→ STOP and clarify, don't improvise!
→ Confirm approach before implementing!

📖 REMEMBER: Check CLAUDE.md for base instructions!
```

---

## 🚨 STOP TRIGGERS (when to interrupt immediately)

### Immediate STOP when you see:

```
🚩 "Creating [filename]_v2.py..."
   → STOP! Edit the original, don't version!

🚩 "Rewriting entire [file]..."
   → STOP! EDIT specific lines only!

🚩 "Adding mock/placeholder data..."
   → STOP! Ask for real credentials!

🚩 "Let me restructure the code..."
   → STOP! Was restructure requested?

🚩 "I'll try another approach..."
   → STOP! Discuss approach first!

🚩 Using "write_file" instead of "edit_file"
   → STOP! Surgical edit, not full rewrite!
```

### Your STOP command:

```
STOP! ✋

Read this again:
1. EDIT, not WRITE
2. ONE file, not multiple versions
3. ONLY what was requested
4. Check CLAUDE.md base instructions
5. Ask if unclear!

Let's restart with the template above.
```

---

## 🎯 PRE-FLIGHT CHECKLIST (before giving task)

**Check these EVERY time:**

```
□ Template filled out completely?
□ Specified EDIT vs WRITE?
□ Listed exact file + location?
□ Defined what NOT to touch?
□ Confirmed all dependencies/keys available?
□ Success criteria clear?
□ Reminded to check CLAUDE.md?
```

**If ANY checkbox is empty → DON'T START YET!**

---

## 🧠 CONTEXT ANCHORING (remind Claude Code)

### When Claude Code seems to drift:

**Anchor prompt:**
```
PAUSE! 🛑

Before continuing, please:
1. Re-read CLAUDE.md (base instructions)
2. Re-read the task template I gave you
3. Confirm you understand:
   - Exact scope (what to change)
   - Method (EDIT not WRITE)  
   - Constraints (what to preserve)
   
Then tell me your approach BEFORE implementing.
```

---

## 📊 COMMON DERAILMENT PATTERNS

### Pattern 1: "Helpful Improvements"
```
🚩 Symptom: "While I'm here, let me also optimize X..."
❌ Problem: Touching code outside scope
✅ Fix: "STOP! Only modify what was requested. Nothing else."
```

### Pattern 2: "Uncertainty Overcompensation"
```
🚩 Symptom: Creates 5 versions "to cover all cases"
❌ Problem: Version chaos
✅ Fix: "STOP! ONE approach, ONE file. Ask if uncertain."
```

### Pattern 3: "Missing Dependency Workaround"
```
🚩 Symptom: "No API key, so I'll use mock data..."
❌ Problem: Fake implementation
✅ Fix: "STOP! Ask for the real credential. No mocks ever."
```

### Pattern 4: "Structural Enthusiasm"
```
🚩 Symptom: "Let me refactor this for better structure..."
❌ Problem: Unwanted architecture changes
✅ Fix: "STOP! Keep structure intact. Surgical edit only."
```

### Pattern 5: "WRITE instead of EDIT"
```
🚩 Symptom: Rewrites entire file to change 3 lines
❌ Problem: Code drift, broken dependencies
✅ Fix: "STOP! EDIT those 3 lines. Don't touch the rest."
```

---

## 🔄 RECOVERY PROTOCOL (when things go wrong)

### Step 1: STOP Immediately
```
STOP! ✋
Don't make it worse.
```

### Step 2: Assess Damage
```
What was changed:
- Files created? List them.
- Files modified? Which ones?
- What broke? Be specific.
```

### Step 3: Revert
```
For file versions (v1, v2, etc):
→ Delete all versions
→ Keep only original or correct one

For bad edits:
→ Restore from git (if versioned)
→ Or restore from backup
→ Or manually fix
```

### Step 4: Restart with Template
```
Use the template again
More specific this time
Explicit constraints
```

---

## 💡 BEST PRACTICES (learned the hard way)

### ✅ DO:
- Use the template EVERY time
- Be hyper-specific about scope
- List explicit "don't touch" items
- Specify EDIT vs WRITE
- Confirm approach before implementation
- Reference CLAUDE.md base instructions

### ❌ DON'T:
- Give vague instructions ("fix the code")
- Assume context is clear
- Let it "try different approaches"
- Allow file versioning
- Accept mock data without asking
- Let it drift from base instructions in CLAUDE.md

---

## 🎯 SUCCESS METRICS

**Good Claude Code session:**
```
✅ ONE file touched
✅ EDIT operation (surgical)
✅ Only requested changes made
✅ No versions created
✅ Works on first try
✅ Followed CLAUDE.md base rules
```

**Bad Claude Code session (STOP these!):**
```
❌ Multiple file versions
❌ WRITE operations (rewrites)
❌ "Improvements" not requested
❌ Mock data instead of real
❌ Structural changes
❌ Ignores CLAUDE.md instructions
```

---

## 📖 QUICK REFERENCE

### Task Initiation:
1. Fill template completely
2. Pre-flight checklist ✓
3. Remind about CLAUDE.md
4. Give task
5. Monitor for red flags

### During Execution:
- Watch for STOP triggers
- Anchor if drifting
- Interrupt early if wrong direction

### If Derailed:
- STOP immediately  
- Assess damage
- Revert changes
- Restart with clearer template

---

## 🚀 RESEMANTIC INTEGRATION (future)

**When ReSemantic is ready:**

This manual template will be replaced by:
```
→ Auto-context injection
→ Constraint validation
→ Operation monitoring  
→ Drift prevention
→ Auto-recovery

But until then: USE THIS TEMPLATE!
```

---

**REMEMBER: Claude Code e puternic, dar fără context e periculos!**

**Template-ul ăsta = harness-ul lui! 🛡️**
