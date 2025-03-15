from langchain_community.tools.tavily_search import TavilySearchResults
tools = [TavilySearchResults(max_results=3)]

from langchain import hub
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import os

# Choose the LLM that will drive the agent
llm = ChatOpenAI(model="gpt-4-turbo-preview",openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")
sys_prompt = "You are a helpful assistant."
agent_executor = create_react_agent(llm,tools,prompt=sys_prompt)
# print(agent_executor.invoke({"messages": [("user", "who is the winnner of the us open")]}))


import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict


class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str

from pydantic import BaseModel, Field


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )

from langchain_core.prompts import ChatPromptTemplate

planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.""",
        ),
        ("placeholder", "{messages}"),
    ]
)
planner = planner_prompt | ChatOpenAI(
    model="gpt-4o", openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1",temperature=0
).with_structured_output(Plan)
planner.invoke(
    {
        "messages": [
            ("user", "what is the hometown of the current Australia open winner?")
        ]
    }
)

from typing import Union
class Response(BaseModel):
    """Response to user."""

    response: str

class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
        "If you need to further use tools to get the answer, use Plan."
    )


replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the follow steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that. Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan."""
)


replanner = replanner_prompt | ChatOpenAI(
    model="gpt-4o", openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1",temperature=0
).with_structured_output(Act)


#Create the Graph
from typing import Literal
from langgraph.graph import END


async def execute_step(state: PlanExecute):
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = f"""For the following plan:
{plan_str}\n\nYou are tasked with executing step {1}, {task}."""
    agent_response = await agent_executor.ainvoke(
        {"messages": [("user", task_formatted)]}
    )
    return {
        "past_steps": [(task, agent_response["messages"][-1].content)],
    }


async def plan_step(state: PlanExecute):
    plan = await planner.ainvoke({"messages": [("user", state["input"])]})
    return {"plan": plan.steps}


async def replan_step(state: PlanExecute):
    output = await replanner.ainvoke(state)
    if isinstance(output.action, Response):
        return {"response": output.action.response}
    else:
        return {"plan": output.action.steps}


def should_end(state: PlanExecute):
    if "response" in state and state["response"]:
        return END
    else:
        return "agent"

from langgraph.graph import StateGraph, START

workflow = StateGraph(PlanExecute)

# Add the plan node
workflow.add_node("planner", plan_step)

# Add the execution step
workflow.add_node("agent", execute_step)

# Add a replan node
workflow.add_node("replan", replan_step)

workflow.add_edge(START, "planner")

# From plan we go to agent
workflow.add_edge("planner", "agent")

# From agent, we replan
workflow.add_edge("agent", "replan")

workflow.add_conditional_edges(
    "replan",
    # Next, we pass in the function that will determine which node is called next.
    should_end,
    ["agent", END],
)

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
app = workflow.compile(interrupt_before=["agent"])


import asyncio
config = {"recursion_limit": 50}
inputs = {"input": "世乒赛男团冠军是谁?"}
async def testplan():
    async for event in app.astream(inputs, config=config):
        for k, v in event.items():
            if k != "__end__":
                print(v)
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(testplan())
    loop.close()

if __name__ == '__main__':
    main()


# {'plan': ["Find out who won the Men's Singles at the 2024 Australian Open.", 'Research the hometown of the winner from step 1.']}
# {'past_steps': [("Find out who won the Men's Singles at the 2024 Australian Open.", "The winner of the Men's Singles at the 2024 Australian Open is Jannik Sinner from Italy.")]}
# {'plan': ['Research the hometown of Jannik Sinner.']}
# {'past_steps': [('Research the hometown of Jannik Sinner.', 'Jannik Sinner was born in San Candido, Italy. This is the hometown from which he originates.')]}
# {'response': "The hometown of the men's 2024 Australian Open winner, Jannik Sinner, is San Candido, Italy."}
    
# {'plan': ["Identify the most recent World Table Tennis Championships event for men's team.", "Research the winner of the men's team event at that specific World Table Tennis Championships.", 'Verify the information from a reliable source to ensure accuracy.', "State the winner of the men's team event at the most recent World Table Tennis Championships."]}
# {'past_steps': [("Identify the most recent World Table Tennis Championships event for men's team.", "The most recent World Table Tennis Championships event for men's team was the ITTF World Team Table Tennis Championships held in 2024.")]}
# {'plan': ["Research the winner of the men's team event at the ITTF World Team Table Tennis Championships held in 2024.", 'Verify the information from a reliable source to ensure accuracy.', "State the winner of the men's team event at the ITTF World Team Table Tennis Championships held in 2024."]}
# {'past_steps': [("Research the winner of the men's team event at the ITTF World Team Table Tennis Championships held in 2024.", "The winner of the men's team event at the ITTF World Team Table Tennis Championships held in 2024 is the People's Republic of China. They secured their 11th consecutive title by winning the championship.")]}
# {'response': "The winner of the men's team event at the ITTF World Team Table Tennis Championships held in 2024 is the People's Republic of China."}