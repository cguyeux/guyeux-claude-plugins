---
name: humanizer
description: >-
  Remove AI writing patterns from text to make it sound natural and human.
  Eliminates AI-isms: inflated significance, em-dash overuse, rule-of-three,
  sycophantic tone, filler phrases, boldface abuse, vague attributions.
  Adds voice, specificity, and rhythm.

  Use when: humanizing AI-generated text, removing ChatGPT patterns, making
  writing sound less robotic, or editing text for Wikipedia/publication.
disable-model-invocation: true
---

# Humanizer: Remove AI Writing Patterns

Identify and remove signs of AI-generated text. Make writing sound natural and human.

## Process

1. **Identify AI patterns**, scan for the 24 pattern categories (see [patterns reference](references/patterns.md))
2. **Rewrite problematic sections**, replace AI-isms with natural alternatives
3. **Preserve meaning**, keep the core message intact
4. **Add soul**, don't just remove bad patterns; inject actual personality

## Key principles

**Have opinions.** Don't just report facts, react to them.

**Vary your rhythm.** Short punchy sentences. Then longer ones that take their time.

**Acknowledge complexity.** "This is impressive but also kind of unsettling" beats "This is impressive."

**Use "I" when it fits.** First person isn't unprofessional, it's honest.

**Be specific.** Not "this is concerning" but "there's something unsettling about agents churning away at 3am while nobody's watching."

## Pattern categories (quick reference)

**Content**: inflated significance (1), notability claims (2), -ing analyses (3), promotional language (4), vague attributions (5), "challenges and prospects" (6)

**Language**: AI vocabulary (7), copula avoidance (8), negative parallelisms (9), rule of three (10), synonym cycling (11), false ranges (12)

**Style**: em dash removal (13), boldface abuse (14), inline-header lists (15), title case headings (16), emojis (17), curly quotes (18)

**Communication**: chatbot artifacts (19), knowledge-cutoff disclaimers (20), sycophantic tone (21), filler phrases (22), excessive hedging (23), generic conclusions (24)

For detailed patterns with before/after examples, see [references/patterns.md](references/patterns.md).

## Output

1. The rewritten text
2. A brief summary of changes made (optional)

## Full example

**Before (AI-sounding):**
> The new software update serves as a testament to the company's commitment to innovation. Moreover, it provides a seamless, intuitive, and powerful user experience, ensuring that users can accomplish their goals efficiently. It's not just an update, it's a revolution in how we think about productivity.

**After (Humanized):**
> The software update adds batch processing, keyboard shortcuts, and offline mode. Early feedback from beta testers has been positive, with most reporting faster task completion.

Based on [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
