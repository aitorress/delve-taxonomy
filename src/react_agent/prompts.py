"""Default prompts used by the agent."""

SYSTEM_PROMPT = """You are a helpful AI assistant.

System time: {system_time}"""

from langchain_core.prompts import ChatPromptTemplate

FEEDBACK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant that analyzes user feedback about taxonomy clusters. Your task is to determine whether the user wants to:
1. Continue with the current taxonomy and proceed to document labeling ("continue")
2. Modify the existing taxonomy based on their feedback ("modify")

You should output:
- A decision ("continue" or "modify")
- A brief explanation of why you made this decision
- Any specific feedback provided by the user (if they gave any)

Guidelines for analysis:
- Look for explicit approval words like "yes", "approve", "good", "continue"
- Look for modification requests like "change", "modify", "update", "revise"
- Consider the overall sentiment and specific suggestions in the feedback
- If there's any criticism or suggested changes, choose "modify"
- Only choose "continue" if the user clearly indicates approval"""),
    
    ("human", "Please analyze this user feedback about the taxonomy clusters: {input}"),
])

TAXONOMY_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """# Instruction

## Context

- **Goal**: Your goal is to cluster the input data into meaningful categories for the given use case.

- **Data**: The input data will be a list of human-AI conversation summaries in XML format, including the following elements:

  - **id**: conversation index.

  - **text**: conversation summary.

- **Use case**: {use_case}

- **Previous feedback**: {feedback}

## Requirements

### Format

- Output clusters in **XML format** with each cluster as a `<cluster>` element, containing the following sub-elements:

  - **id**: category number starting from 1 in an incremental manner.

  - **name**: category name should be **within {cluster_name_length} words**. It can be either verb phrase or noun phrase, whichever is more appropriate.

  - **description**: category description should be **within {cluster_description_length} words**.

Here is an example of your output:

```xml

<clusters>

  <cluster>

    <id>category id</id>

    <name>category name</name>

    <description>category description</description>

  </cluster>

</clusters>

```

- Total number of categories should be **no more than {max_num_clusters}**.

- Output should be in **English** only.

### Quality

- **No overlap or contradiction** among the categories.

- **Name** is a concise and clear label for the category. Use only phrases that are specific to each category and avoid those that are common to all categories.

- **Description** differentiates one category from another.

- **Name** and **description** can **accurately** and **consistently** classify new data points **without ambiguity**.

- **Name** and **description** are *consistent with each other*.

 Output clusters match the data as closely as possible, without missing important categories or adding unnecessary ones.

- Output clusters should strive to be orthogonal, providing solid coverage of the target domain.

- Output clusters serve the given use case well.

- Output clusters should be specific and meaningful. - - Do not invent categories that are not in the data.

# Data

<conversations>

{data_xml}

</conversations>"""),
    ("human", """# Questions

## Q1. Please generate a cluster table from the input data that meets the requirements.

Tips

- If user feedback was provided, make sure to address their specific concerns and suggestions in your clustering.
     
- The cluster table should be a **flat list** of **mutually exclusive** categories. Sort them based on their semantic relatedness.

- Though you should aim for {max_num_clusters} categories, you can have *fewer than {max_num_clusters} categories* in the cluster table;  but **do not exceed the limit.** 

- Be **specific** about each category. **Do not include vague categories** such as "Other", "General", "Unclear", "Miscellaneous" or "Undefined" in the cluster table.

- You can ignore low quality or ambiguous data points.

- 

## Q2. Why did you cluster the data the way you did? Explain your reasoning **within {explanation_length} words**.

## Provide your answers between the tags: <cluster_table>your generated cluster table with no more than {max_num_clusters} categories</cluster_table>, <explanation>explanation of your reasoning process within {explanation_length} words</explanation>.

# Output""")
])