# Report of findings

This report shows the findings of building the SI-Mapper agent. 

# History

## LLMs as providers of intelligence through function calling

Here we implemented LLMs as providers of intelligence through function calling. The business logic was implemented on standard python code. The LLMs were called for specific tasks such as image recognition and text generation. This approach is very close to wiriting standard code that can have "wild card" functions. The python function behaves like a wild card in the sense that you can ask arbitrarly complex questions to the LLM and it will return the answer as the answer of the python function. However, this approach has the disadvantage that the business logic is hardcoded and depends on the human writing the code. Moreover, the LLM is not aware of the context of the application and cannot make decisions on its own. 

At this time we were using gemini 1.5 flash. At this time LangChain was trendy, and it was a good option to implement this approach. 

## Using workflows for AI agents

Here we implemented workflows for AI agents. The idea was to use workflows to define the behavior of the agents. The workflow is defined as a sequence of steps that the agent will execute. Each step can be a function call or a sub-agent. This approach is more flexible than the first approach because it allows the better exploit the capabilities of the LLMs. However, the business logic is still hardcoded and depends on the human writing the code. The only difference is that the business logic is implemented in a workflow instead of a python function. Moreover, the LLM is not aware of the context of the application and cannot make decisions on its own. 

At this time we were using gemini 1.5 flash. At this time LangChain was still trendy, and it was a good option to implement this approach. LangGraph was explored at this stage, but it was abandoned due to its high costs of running commercial applications on it.

## Using ADK for workflows with AI agents

Here we implemented ADK for agents. ADK is a framework for building agents provided by google. It provides a way to define the behavior of the agents and to manage the state of the agents. This stage used still workflows for defining the behavior of the agents. Thus, the business logic was still hardcoded and depended on the human writing the code. Results were saved on a local SQL database. 

At this time we were using gemini 2.0 flash. At his time ADK was recently released. Therefore, some of its functionalities were still under development and sometimes it was difficult to find documentation and examples. AI coding agents didn't know the library, so, it was not possible to use them for building the application. We implemented a local RAG system to provide the worflow agents the ability to access documentation to find proper classes to model the equipements. 


## Using ADK for AgenticAI with a Master agent

The fourth attempt was to test capabilities of agentic AI. We decided to use ADK for agents with a master agent. The idea was to use a single master agent to complete all tasks. This approach exploited the intelligence of the agent and allowed the agent to make decisions on its own. However, the prompts were very long and complex, and the agent was not able to complete all tasks. Adding a while loop to the agent was not enough to overcome this limitation.

At this time, we were using gemini 2.5 flash. Even with the thinking mode enabled, the agent was not able to complete all tasks. Moreover, at this time the frontend was introduced. The introduction of the frontend added CopilotKit to the Agent Development Kit. CopilotKit is a framework that implemented the Agent-to-UI protocol. This protocol allows the frontend to communicate with the agent. Moreover, we introduced the management of artifacts to manage files uploaded by the user. We also introduced MCP tools. Instead of handling tools locally, the tools were developed inside an MCP server. 

## Using ADK for AgenticAI with the PAR Architecture
Here we implemented the Plan-Act-Review (PAR) Architecture. The idea was to use a sequential agent that contained three sub-agents: a planner agent, an actor agent and a reviewer agent. The idea was to split the request of the user into a fixed execution sequence. First the **Plan** agent will create a plan for the user request. Then, the **Act** agent will execute the plan. Finally, the **Review** agent will review the plan and the execution of the plan. This improved the results but the agent finished its tasks too early. Adding a loop agent on top of the PAR architecture improved more the results, but it was not enough to produce good results. 

At this time, we were using gemini 2.5 flash. At this time we realized that it was difficult to know what the agent was doing. So, we decided to use the frontend to display the agent's thoughts and actions in real-time. Despite improvements, prompts remained complex and the agent was not able to produce good enough results. 

## Using ADK for AgenticAI with a Master agent + PAR Architecture as subagent
Here we implemented the Plan-Act-Review (PAR) Architecture as a subagent of a master agent. The idea was to use a master agent to decide to act or to delegate tasks to sub-agents. We implemented only one subagent which was the PAR architecture. Both the master and the subagent were given full autonomy to decide what to do. However, the PAR subagent was not able to produce good enough results. 

At this time, we were using gemini 2.5 flash. Results were not good enough on the UI. We add tracking of tool calls and state variables to the frontend, to visualize the agent's actions and state variables. 


## Using ADK with Master Agent + Workflows
Here we deleted the PAR architecture and the Master agent was repurposed to decide to act or to delegate tasks to sub-agents. The PAR agent was not performing good. Thus, two new agents were added before the PAR, a image recognition agent and a equipement recognition agent. The PAR architecture transformed into the Drawing Architecture. The first agent was responsible for recognizing the image and counting the number of equipements. The second agent was responsible for identifying on the image the equipements that were previously counted by the image recognition agent. Thus, the Drawing Architecture become an hybrid, where the image recognition agents were workflows, and the PAR was agentic. This was not working good. Thus, all sequence was transformed into a workflow again. New prompts were created for the whole drawing sequence, but, results were not good enough. 

At this time, we were using gemini 2.5 flash.

## Using ADK with Master Agent + Workflows + Parallel execution
Here we changed the two agents charged of image recognition for a parallel agent. The parallel agent contained one agent inside for each type of equipment. This allowed to provide detail instructions to each agent for each type of equipment to improve the image recogntion capability. After the parallel agent, the plan, act and review agents were kept as workflows. 

At this time, we were using gemini 2.5 flash. Results improved here considerably in terms of speed. Parallel agents can significantly reduce the total processing time. However, the images reproduced by the agent were not good enough. 

## Using ADK with Master Agent + Workflows + Gemini 3.0 flash
Here we changed the model to gemini 3.0 flash. This improved the results considerably in terms of accuracy. The drawing agent was still a workflow. The architecture of the parallel agent was improved to reduce token consumption. 

At this time, we are using gemini 3.0 flash. We also tested gemini 3.0 pro, but it takes considerably longer to produce results. 

## Test of Agentic AI using skills instead of subagents

## Test of Agentic Vision for image recognition

## Test of visual validation for the review agent using the MCP puppeteer 

## Current test: Agentic AI (single agent) using skills + Agentic Vision + MCP puppeteer for visual validation