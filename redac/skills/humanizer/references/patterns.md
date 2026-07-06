## CONTENT PATTERNS

### 1. Undue Emphasis on Significance, Legacy, and Broader Trends

**Words to watch:** stands/serves as, is a testament/reminder, a vital/significant/crucial/pivotal/key role/moment, underscores/highlights its importance/significance, reflects broader, symbolizing its ongoing/enduring/lasting, contributing to the, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted

**Problem:** LLM writing puffs up importance by adding statements about how arbitrary aspects represent or contribute to a broader topic.

**Before:**
> The Statistical Institute of Catalonia was officially established in 1989, marking a pivotal moment in the evolution of regional statistics in Spain. This initiative was part of a broader movement across Spain to decentralize administrative functions and enhance regional governance.

**After:**
> The Statistical Institute of Catalonia was established in 1989 to collect and publish regional statistics independently from Spain's national statistics office.

---

### 2. Undue Emphasis on Notability and Media Coverage

**Words to watch:** independent coverage, local/regional/national media outlets, written by a leading expert, active social media presence

**Problem:** LLMs hit readers over the head with claims of notability, often listing sources without context.

**Before:**
> Her views have been cited in The New York Times, BBC, Financial Times, and The Hindu. She maintains an active social media presence with over 500,000 followers.

**After:**
> In a 2024 New York Times interview, she argued that AI regulation should focus on outcomes rather than methods.

---

### 3. Superficial Analyses with -ing Endings

**Words to watch:** highlighting/underscoring/emphasizing..., ensuring..., reflecting/symbolizing..., contributing to..., cultivating/fostering..., encompassing..., showcasing...

**Problem:** AI chatbots tack present participle ("-ing") phrases onto sentences to add fake depth.

---

### 4. Promotional and Advertisement-like Language

**Words to watch:** boasts a, vibrant, rich (figurative), profound, enhancing its, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking (figurative), renowned, breathtaking, must-visit, stunning

---

### 5. Vague Attributions and Weasel Words

**Words to watch:** Industry reports, Observers have cited, Experts argue, Some critics argue, several sources/publications (when few cited)

---

### 6. Outline-like "Challenges and Future Prospects" Sections

**Words to watch:** Despite its... faces several challenges..., Despite these challenges, Challenges and Legacy, Future Outlook

---

### 7. Overused "AI Vocabulary" Words

**High-frequency AI words:** Additionally, align with, comprehensive/complet (used as generic praise — "a comprehensive guide", "un guide complet"), crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate/intricacies, key (adjective), landscape (abstract noun), pivotal, showcase, tapestry (abstract noun), testament, underscore (verb), valuable, vibrant

---

### 8. Avoidance of "is"/"are" (Copula Avoidance)

**Words to watch:** serves as/stands as/marks/represents [a], boasts/features/offers [a]

---

### 9. Negative Parallelisms

"Not only...but..." or "It's not just about..., it's..." constructions.

---

### 10. Rule of Three Overuse

LLMs force ideas into groups of three to appear comprehensive.

---

### 11. Elegant Variation (Synonym Cycling)

AI repetition-penalty causes excessive synonym substitution for the same referent.

---

### 12. False Ranges

"from X to Y" constructions where X and Y aren't on a meaningful scale.

---

### 13. Em Dash Removal

Em dashes (— in Unicode, --- in LaTeX, -- in some editors) are a strong marker of AI-generated text. LLMs overuse them to create a "punchy" rhythm that humans rarely produce in natural writing. **Remove all em dashes systematically.**

**Actions:**
- Replace with commas, periods, parentheses, or restructure the sentence
- In LaTeX: search for `---` and `--` (en dash) used as em dash substitutes
- Do not keep em dashes "for style" — their mere presence is suspicious
- Acceptable exception: direct quotes where the original author used them

**Before:**
> The new model — trained on a larger dataset — outperforms all baselines.

**After:**
> The new model, trained on a larger dataset, outperforms all baselines.

---

### 14. Overuse of Boldface

AI chatbots emphasize phrases in boldface mechanically. Remove most bold.

---

### 15. Inline-Header Vertical Lists

Items starting with bolded headers followed by colons. Rewrite as prose.

---

### 16. Title Case in Headings

AI capitalizes all main words. Use sentence case instead.

---

### 17. Emojis

AI decorates headings or bullet points with emojis. Remove them.

---

### 18. Curly Quotation Marks

ChatGPT uses curly quotes ("\u201c...\u201d") instead of straight quotes ("..."). Replace.

---

### 19. Collaborative Communication Artifacts

**Words to watch:** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., let me know, here is a...

---

### 20. Knowledge-Cutoff Disclaimers

**Words to watch:** as of [date], Up to my last training update, While specific details are limited/scarce...

---

### 21. Sycophantic/Servile Tone

Overly positive, people-pleasing language. Remove and state facts directly.

---

### 22. Filler Phrases

- "In order to achieve this goal" -> "To achieve this"
- "Due to the fact that" -> "Because"
- "At this point in time" -> "Now"
- "has the ability to" -> "can"
- "It is important to note that" -> (remove)

---

### 23. Excessive Hedging

Over-qualifying statements. "It could potentially possibly be argued that the policy might have some effect" -> "The policy may affect outcomes."

---

### 24. Generic Positive Conclusions

Vague upbeat endings. Replace with concrete next steps or facts.

---

## Reference

Based on [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup.
