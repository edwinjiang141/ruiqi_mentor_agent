from typing import Annotated  # 用于类型注解
from langgraph.graph import END, StateGraph, START  # 导入状态图的相关常量和类
from langgraph.graph.message import add_messages  # 用于在状态中处理消息
from langgraph.checkpoint.memory import MemorySaver  # 内存保存机制，用于保存检查点
from typing_extensions import TypedDict  # 用于定义带有键值对的字典类型
from langchain_core.messages import AIMessage, HumanMessage


class CodeAssistantAgent:
    def __init__(self, coder,assistant,inputs):
        self.coder = coder
        self.assistant = assistant
        self.inputs = inputs
        print(self.inputs)
        self.create_graph()

    # 定义状态类，使用TypedDict以保存消息
    class State(TypedDict):
        messages: Annotated[list, add_messages]  # 使用注解确保消息列表使用add_messages方法处理
        # 异步生成节点函数：生成内容（如作文）
    # 输入状态，输出包含新生成消息的状态
    def generation_node(self,state: State) -> State:
        # 调用生成器(writer)，并将消息存储到新的状态中返回
        return {"messages": [self.coder.invoke(state['messages'])]}

    # 异步反思节点函数：对生成的内容进行反思和反馈
    # 输入状态，输出带有反思反馈的状态
    def reflection_node(self,state: State) -> State:
        # 创建一个消息类型映射，ai消息映射为HumanMessage，human消息映射为AIMessage
        cls_map = {"ai": HumanMessage, "human": AIMessage}
        
        # 处理消息，保持用户的原始请求（第一个消息），转换其余消息的类型
        translated = [state['messages'][0]] + [
            cls_map[msg.type](content=msg.content) for msg in state['messages'][1:]
        ]
        
        # 调用反思器(reflect)，将转换后的消息传入，获取反思结果
        res = self.assistant.invoke(translated)
        
        # 返回新的状态，其中包含反思后的消息
        return {"messages": [HumanMessage(content=res.content)]}
    
    # 定义条件函数，决定是否继续反思过程
    # 如果消息数量超过6条，则终止流程
    def should_continue(self,state: State):
        MAX_ROUND = 5
        if len(state["messages"]) > MAX_ROUND:
            return END  # 达到条件时，流程结束
        return "reflect"  # 否则继续进入反思节点
    
    def create_graph(self):
        builder = StateGraph(self.State)

        # 在状态图中添加"writer"节点，节点负责生成内容
        builder.add_node("writer", self.generation_node)

        # 在状态图中添加"reflect"节点，节点负责生成反思反馈
        builder.add_node("reflect", self.reflection_node)

        # 定义起始状态到"writer"节点的边，从起点开始调用生成器
        builder.add_edge(START, "writer")
        # 在"writer"节点和"reflect"节点之间添加条件边
        # 判断是否需要继续反思，或者结束
        builder.add_conditional_edges("writer", self.should_continue)

        # 添加从"reflect"节点回到"writer"节点的边，进行反复的生成-反思循环
        builder.add_edge("reflect", "writer")

        # 创建内存保存机制，允许在流程中保存中间状态和检查点
        memory = MemorySaver()

        # 编译状态图，使用检查点机制
        self.graph = builder.compile(checkpointer=memory)
        
    def generate_code(self):
        config = {"configurable": {"thread_id": "1"}}
        return self.graph.stream(self.inputs,config)