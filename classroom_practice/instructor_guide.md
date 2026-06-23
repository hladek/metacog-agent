# Instructor Guide: CRAAP Blog Analyzer Classroom Practice

## Preparation

Before class, decide whether students will use a saved analysis or analyze a new URL.

### Option A: Use Saved Analyses

Use this option when you want the activity to run quickly and consistently.

1. Start the Streamlit app.
2. Students load an existing analysis from the sidebar.
3. Students complete the worksheet using the loaded result.

This option avoids delays from downloading pages, web search, and model calls.

### Option B: Analyze a New URL

Use this option when you want students to evaluate a current source selected for the class.

1. Make sure the required environment variables are configured.
2. Start the app in admin mode.
3. Enter the selected URL and run the analysis before students begin the AI comparison section.

Example command:

```bash
CRAAP_ADMIN=true uv run streamlit run app.py
```

The app may also require `OPENAI_API_KEY` or the custom CRAAP model environment variables used by your deployment.

## Source Selection Advice

Choose a source that gives students enough material to evaluate. A useful classroom source usually has:

- A named or traceable author.
- A visible publisher or organization.
- At least a few factual claims.
- Some links, citations, statistics, examples, or references.
- A purpose that students can debate.

Avoid sources that are too short, purely personal, paywalled, or impossible for the app to extract.

## Suggested Timing

### 50-Minute Version

| Time | Activity |
| --- | --- |
| 5 min | Warm-up and first impressions |
| 5 min | Define research need |
| 15 min | Student CRAAP first pass |
| 15 min | Compare with tool output |
| 5 min | Verify one claim |
| 5 min | Final judgment |

### 75-Minute Version

| Time | Activity |
| --- | --- |
| 5 min | Warm-up and first impressions |
| 10 min | Define research need and discuss relevance |
| 20 min | Student CRAAP first pass |
| 20 min | Compare with tool output |
| 15 min | Verify one or two claims |
| 5 min | Final judgment |

## Facilitation Notes

Emphasize that CRAAP is context-dependent. A source can be current and authoritative but still irrelevant to a student's research question. A source can also be relevant but not accurate enough to cite.

Ask students to separate these three things:

- What the source says.
- What the tool says about the source.
- What outside evidence confirms or challenges.

When students disagree with the AI output, require evidence. A disagreement is strongest when students can point to the article text, the author or publisher record, or an outside verification source.

## Common Student Issues

### Students accept the AI output too quickly

Prompt them with:

- What evidence did the tool use?
- What evidence did it miss?
- Which part of the tool's response is strongest?
- Which part would you verify before trusting?

### Students confuse relevance with accuracy

Use this distinction:

- Relevance asks whether the source fits the student's need.
- Accuracy asks whether the source's claims are true, supported, and verifiable.

### Students verify with weak sources

Require students to explain why the outside source is trustworthy. A search result alone is not evidence.

### Students cannot find author information

That is a valid finding. Students should record that the author is unclear or anonymous and explain how that affects Authority.

## Discussion Prompts

- Which CRAAP category was easiest to evaluate? Which was hardest?
- Did the tool notice something you missed?
- Did you notice something the tool missed?
- Which claims from the article most needed verification?
- Would your final decision change for a different research purpose?

## Grading Suggestion

Use the rubric in [README.md](README.md). For a low-stakes classroom activity, grade primarily on evidence quality and reflection rather than on whether students reached a specific conclusion.

