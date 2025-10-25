# models/prompts.py

# Minimal prompt: only descriptions of criteria
INDIVIDUAL_PROMPT_MINIMAL = """
Evaluate the following user stories against the below-mentioned individual-level QUS criterion/criteria:
{criteria_list}

User stories:
"{stories_list}"

INSTRUCTIONS:
- Evaluate each story against the provided criterion (if there is one criterion) or all provided criteria.
- For each criterion, return PASS/FAIL and a one-sentence justification (why it fails or why it passes).
- If a story fails a criterion, propose a concise repair (a SINGLE (not a list) improved user story) that addresses that criterion.
- Return ONLY a JSON array, where each element corresponds to one story.
- Each element should have this structure:
{{
    {{
      "story_id": "<unique story ID>",
      "story": "<original story text>",
      "criteria": {{
         "<CriterionName>": {{ "pass": true|false, "reason": "<short explanation>" }},
         ...
      }},
      "repairs": {{
         "<CriterionName>": "<suggested improved user story text>",
         ...
      }}
    }},
    ...
}}

EXAMPLE OUTPUT (Generate the output on the basis of the following pattern):
```{{ 
 {{
    "story_id": "Story 60",
    "story": "As a shopper, I want to apply multiple coupons.",
    "criteria": {{
      "Well-formed": {{
        "pass": true,
        "reason": "The story includes user role and goal, following the standard format."
      }}
    }},
    "repairs": {{}}
  }},
  {{
    "story_id": "Story 61",
    "story": "Leave request approval or denial should be enabled for users.",
    "criteria": {{
      "Well-formed": {{
        "pass": false,
        "reason": "The story lacks user role and clear goal format."
      }}
    }},
    "repairs": {{
      "Well-formed": "As a manager, I want to approve or deny leave requests so that I can manage team availability."
    }}
  }},
 ...
}}```

Do not omit the "story_id" field. The JSON output must be properly formatted (The keys are quoted, The value does not have colon (:)) 
The JSON be used to map results in Python.
Do not add extra commentary. Use short sentences in reasons and repairs.
"""


# Rich prompt: with examples
INDIVIDUAL_PROMPT_RICH = """


QUS framework defines 13 quality criteria for User Story quality. QUS framework's criteria are organized in following 3 categories:

'Syntactic quality', concerning the textual structure of a user story without considering its meaning;
'Semantic quality', concerning the relations and meaning of (parts of) the user story text;
'Pragmatic quality', considers the audience's subjective interpretation of the user story text aside from syntax and semantics.

The 13 quality criteria are described as below:

Note: The last word (Individual/ Set) classifies the criteria depending on whether they relate to an individual user story or to a set of user stories.

Syntactic
1. Well-formed:
A user story includes at least a role and a means. Individual
2. Atomic:
A user story expresses a requirement for exactly one feature. Individual
3. Minimal:
A user story contains nothing more than role, means, and ends. Individual

Semantic
1. Conceptually sound:
The means expresses a feature and the ends expresses a rationale. Individual
2. Problem-oriented:
A user story only specifies the problem, not the solution to it. Individual
3. Unambiguous:
A user story avoids terms or abstractions that lead to multiple interpretations. Individual
4. Conflict-free:
A user story should not be inconsistent with any other user story. Set

Pragmatic
1. Full sentence:
A user story is a well-formed full sentence. Individual
2. Estimatable:
A story does not denote a coarse-grained requirement that is difficult to plan and prioritize. Individual
3. Unique:
Every user story is unique, duplicates are avoided. Set
4. Uniform:
All user stories in a specification employ the same template. Set
5. Independent:
The user story is self-contained and has no inherent dependencies on other stories. Set
6. Complete:
Implementing a set of user stories creates a feature-complete application, no steps are missing. Set

We follow the following format for writing user story:
As a <role>, I want to <means>, so that <ends>.

Help me in evaluating the quality of user stories I have.

I am providing you more details (enclosed with in ```) about the 8 quality criteria ('Individual') along with an example for each. 

Use these details and underlying knowledge to reach at a more correct, concrete and reliable quality evaluation of the user stories I shall be providing as input.

```

1. Well-formed

Before it can be considered a user story, the core text of the requirement needs to include a role and the expected functionality: the means.
US1: I want to see an error when I cannot see recommendations after I upload an article.
User story US1 mentioned above does not adhere to this syntax, as it has no role. It is likely that the user story writer has forgotten to include the role. The story can be fixed by adding the role:
"As a Member, I want to see an error when I cannot see recommendations after I upload an article."

2. Atomic

A user story should concern only one feature. Although common in practice, merging multiple user stories into a larger, generic one diminishes the accuracy of effort estimation. The user story US2 mentioned below consists of two separate requirements: the act of clicking on a location and the display of associated landmarks.
US2: As a User, I want to click a particular location from the map and thereby perform a search of landmarks associated with that latitude longitude combination.
This user story should be split into two:
• US2A: "As a User, I want to click a particular location from the map";
• US2B: "As a User, I want to see landmarks associated with the latitude and longitude combination of a particular location."

3. Minimal

User stories should contain a role, a means, and (optimally) some ends. Any additional information such as comments, descriptions of the expected behavior, or testing hints should be left to additional notes.
Consider
US3: As a care professional, I want to see the registered hours of this week (split into products and activities). See: Mockup from Alice NOTE—first create the overview screen—then add validations.
Aside from a role and means, it includes a reference to an undefined mockup and a note on how to approach the implementation. The requirements engineer should move both to separate user story attributes like the description or comments, and retain only the basic text of the story: "As a care professional, I want to see the registered hours of this week."

4. Conceptually sound

The means and end parts of a user story play a specific role. The means should capture a concrete feature, while the end expresses the rationale for that feature.
Consider
US4: As a User, I want to open the interactive map, so that I can see the location of landmarks.
The end is actually a dependency on another (hidden) functionality, which is required in order for the means to be realized, implying the existence of a landmark database which is not mentioned in any of the other stories. A significant additional feature that is erroneously represented as an end, but should be a means in a separate user story, for example:
US4A: "As a User, I want to open the interactive map";
US4B: "As a User, I want to see the location of landmarks on the interactive map."

5. Problem-oriented

In line with the problem specification principle for RE proposed by Zave and Jackson, a user story should specify only the problem. If absolutely necessary, implementation hints can be included as comments or descriptions. Aside from breaking the minimal quality criteria,
US5: As a care professional I want to save a reimbursement—add save button on top right (never grayed out).
includes implementation details (a solution) within the user story text. The story could be rewritten as follows:
"As a care professional, I want to save a reimbursement."

6. Unambiguous

Ambiguity is intrinsic to natural language requirements, but the requirements engineer writing user stories has to avoid it to the extent this is possible. Not only should a user story be internally unambiguous, but it should also be clear in relationship to all other user stories. The Taxonomy of Ambiguity Types [5] is a comprehensive overview of the kinds of ambiguity that can be encountered in a systematic requirements specification.
In
US6: As a User, I am able to edit the content that I added to a person's profile page.
"content" is a superclass referring to audio, video, and textual media uploaded to the profile page as specified in three other, separate user stories in the real-world user story set. The requirements engineer should explicitly mention which media are editable; for example, the story can be modified as follows:
"As a User, I am able to edit video, photo and audio content that I added to a person's profile page."

7. Full sentence

A user story should read like a full sentence, without typos or grammatical errors.
For instance,
US9: Server configuration
is not expressed as a full sentence (in addition to not complying with syntactic quality). By reformulating the feature as a full sentence user story, it will automatically specify what exactly needs to be configured. For example, US9 can be modified to "As an Administrator, I want to configure the server's sudo-ers."

8. Estimable/ Estimable

As user stories grow in size and complexity, it becomes more difficult to accurately estimate the required effort. Therefore, each user story should not become so large that estimating and planning it with reasonable certainty becomes impossible.
For example,
US10: As a care professional I want to see my route list for next/future days, so that I can prepare myself (for example I can see at what time I should start traveling)
requests a route list so that care professionals can prepare themselves. While this might be just an unordered list of places to go to during a workday, it is just as likely that the feature includes ordering the routes algorithmically to minimize distance travelled and/or showing the route on a map. These many functionalities inhibit accurate estimation and call for splitting the user story into multiple user stories; for example,
• US10A: "As a Care Professional, I want to see my route list for next/future days, so that I can prepare myself";
• US10B: "As a Manager, I want to upload a route list for care professionals."


Evaluate the following user stories against the below-mentioned individual-level QUS criterion/criteria:
{criteria_list}

User stories:
"{stories_list}"

INSTRUCTIONS:
- Evaluate each story against the provided criterion (if there is one criterion) or all provided criteria.
- For each criterion, return PASS/FAIL and a one-sentence justification (why it fails or why it passes).
- If a story fails a criterion, propose a concise repair (a SINGLE (not a list) improved user story) that addresses that criterion.
- Return ONLY a JSON array, where each element corresponds to one story.
- Each element should have this structure:
{{
    {{
      "story_id": "<unique story ID>",
      "story": "<original story text>",
      "criteria": {{
         "<CriterionName>": {{ "pass": true|false, "reason": "<short explanation>" }},
         ...
      }},
      "repairs": {{
         "<CriterionName>": "<suggested improved user story text>",
         ...
      }}
    }},
    ...
}}

EXAMPLE OUTPUT (Generate the output on the basis of the following pattern):
```{{ 
 {{
    "story_id": "Story 60",
    "story": "As a shopper, I want to apply multiple coupons.",
    "criteria": {{
      "Well-formed": {{
        "pass": true,
        "reason": "The story includes user role and goal, following the standard format."
      }}
    }},
    "repairs": {{}}
  }},
  {{
    "story_id": "Story 61",
    "story": "Leave request approval or denial should be enabled for users.",
    "criteria": {{
      "Well-formed": {{
        "pass": false,
        "reason": "The story lacks user role and clear goal format."
      }}
    }},
    "repairs": {{
      "Well-formed": "As a manager, I want to approve or deny leave requests so that I can manage team availability."
    }}
  }},
 ...
}}```

Do not omit the "story_id" field. The JSON output must be properly formatted (The keys are quoted, The value does not have colon (:)) 
The JSON be used to map results in Python.
Do not add extra commentary. Use short sentences in reasons and repairs.
"""


def get_prompt(prompt_type: str) -> str:
    if prompt_type.lower() == "minimal":
        return INDIVIDUAL_PROMPT_MINIMAL
    elif prompt_type.lower() == "rich":
        return INDIVIDUAL_PROMPT_RICH
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}")