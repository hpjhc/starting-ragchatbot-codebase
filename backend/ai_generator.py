import anthropic
import os
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant for educational course content. You have two tools:

Tool 1 - `get_course_outline`: Use this to answer ANY question about course structure — listing lessons, syllabus, overview, number of lessons, "what does this course cover". It returns ALL lesson titles, numbers, course title, and link.

Tool 2 - `search_course_content`: Use this ONLY for questions about specific material taught inside lessons (e.g., "what is prompt caching", "how does filtering work").

IMPORTANT RULES:
- Never use search_course_content to answer "what lessons are in this course" — it does NOT return lesson titles, it returns content snippets.
- One search per query maximum.
- Synthesize search results into accurate, fact-based responses.
- If search yields no results, state this clearly without offering alternatives.
- General knowledge questions: Answer without searching.
- Course-specific questions: Search first, then answer.
- Provide only the direct answer. No meta-commentary.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
            log_path = "D:/learning/starting-ragchatbot-codebase/backend/debug.log"
            if os.path.getsize(log_path) > 5 * 1024 * 1024:
                os.remove(log_path)
            with open(log_path, "a") as f:
                f.write(f"Tools provided: {[t['name'] for t in tools]}\n")
                for t in tools:
                    desc = t.get('description', '')[:100]
                    f.write(f"  {t['name']}: {desc}...\n")

        # Get response from Claude
        with open("D:/learning/starting-ragchatbot-codebase/backend/debug.log", "a") as f:
            f.write(f"System prompt (first 200): {system_content[:200]}...\n")
        response = self.client.messages.create(**api_params)

        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            with open("D:/learning/starting-ragchatbot-codebase/backend/debug.log", "a") as f:
                f.write("stop_reason=tool_use\n")
            return self._handle_tool_execution(response, api_params, tool_manager)
        
        # Return direct response
        return response.content[0].text
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()

        # Add AI's tool use response
        messages.append({"role": "assistant", "content": initial_response.content})

        # Execute all tool calls and collect results
        tool_results = []
        for content_block in initial_response.content:
            if content_block.type == "tool_use":
                with open("D:/learning/starting-ragchatbot-codebase/backend/debug.log", "a") as f:
                    f.write(f"AI called tool: {content_block.name} with input: {content_block.input}\n")
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name,
                        **content_block.input
                    )
                except Exception as e:
                    tool_result = f"Error executing tool '{content_block.name}': {str(e)}"
                    with open("D:/learning/starting-ragchatbot-codebase/backend/debug.log", "a") as f:
                        f.write(f"Tool execution error: {e}\n")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })

        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        # Prepare final API call without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
        }

        # Get final response
        try:
            final_response = self.client.messages.create(**final_params)
            return final_response.content[0].text
        except Exception as e:
            with open("D:/learning/starting-ragchatbot-codebase/backend/debug.log", "a") as f:
                f.write(f"Final API call failed: {e}\n")
            return f"I retrieved some information but encountered an error generating the final response. Please try rephrasing your question."