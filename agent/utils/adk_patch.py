import asyncio
import random
import logging
import copy
from typing import AsyncGenerator, Optional, List, Any
from google.genai import types
from utils.concurrency import SEM
from google.adk.events.event import Event
from google.adk.models.llm_response import LlmResponse
from google.adk.models.llm_request import LlmRequest
from google.adk.agents.invocation_context import InvocationContext
from google.adk.flows.llm_flows import base_llm_flow, contents
from google.adk.flows.llm_flows.functions import remove_client_function_call_id
from google.adk.flows.llm_flows.contents import (
    _process_compaction_events,
    _contains_empty_content,
    _is_event_belongs_to_branch,
    _is_auth_event,
    _is_request_confirmation_event,
    _is_other_agent_reply,
    _present_other_agent_message,
    _rearrange_events_for_latest_function_response,
    _rearrange_events_for_async_function_responses_in_history
)

logger = logging.getLogger("google.adk.patch")

_PATCH_APPLIED = False

def apply_adk_patches():
    """Applies runtime patches to google.adk to support Gemini 3.0."""
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        logger.debug("ADK patches already applied, skipping.")
        return
    
    logger.info("Applying ADK patches for Gemini 3.0 compatibility...")

    # 1. Patch Pydantic Models (Extra fields tolerance)
    _patch_pydantic_models()

    # 2. Patch BaseLlmFlow (Thinking Config)
    _patch_base_llm_flow()

    # 3. Patch Contents (Signature Propagation)
    _patch_contents()
    
    logger.info("ADK patches applied successfully.")
    _PATCH_APPLIED = True

def _patch_pydantic_models():
    """Allows extra fields (like thought_signature) in Event and LlmResponse."""
    try:
        Event.model_config['extra'] = 'allow'
        LlmResponse.model_config['extra'] = 'allow'
        logger.info("✅ Patched Event and LlmResponse model_config to ALLOW extra fields.")
    except Exception as e:
        logger.error(f"❌ Failed to patch Pydantic models: {e}")

def _patch_base_llm_flow():
    """Patches _call_llm_async to inject thinking_config."""
    original_call_llm_async = base_llm_flow.BaseLlmFlow._call_llm_async

    async def patched_call_llm_async(self, invocation_context, llm_request, model_response_event):
        # INJECTED LOGIC START
        llm_request.config = llm_request.config or types.GenerateContentConfig()
        
        # Apply thinking config from planner if available
        from google.adk.agents.llm_agent import LlmAgent
        agent = invocation_context.agent
        if isinstance(agent, LlmAgent) and agent.planner and hasattr(agent.planner, 'apply_thinking_config'):
            agent.planner.apply_thinking_config(llm_request)
            # logger.debug("Applied thinking config via patch.")
        # INJECTED LOGIC END

        # Call original (which will re-do line 1 but that's fine)
        # We need to call the original GENERATOR.
        # Since original is a generator, we must iterate it.
        # Wait, I cannot easily wrap the generator and inject logic inside the middle of it 
        # unless I copy the whole function or the original function allows pre-hooks.
        # BaseLlmFlow has `before_model_callback` but that might be too late or early?
        # Actually, `_call_llm_async` sets up the request THEN calls `llm.generate_content_async`.
        # Code:
        # 729: llm_request.config = llm_request.config or types.GenerateContentConfig()
        # ...
        # 740: llm = self.__get_llm(invocation_context)
        
        # If I modify `llm_request` BEFORE calling original, it SHOULD persist because it's a reference.
        # BUT `_call_llm_async` is an async generator.
        
        # Let's try wrapping it.
        async for item in original_call_llm_async(self, invocation_context, llm_request, model_response_event):
            yield item

    # Replace the method
    # Since it's a generator, the above wrapper modifies `llm_request` (by reference) 
    # BEFORE the original generator body starts executing?
    # No, async generator body starts when first `anext` is called.
    # So I need to ensure my logic runs before the first yield of original.
    
    # Actually, to be safe, I should just COPY the implementation of `_call_llm_async` 
    # because it's hard to inject into the middle of a generator function's setup phase via wrapper
    # without potentially missing the setup if it happens before first yield?
    # Python generators execute up to first yield when iterated. 
    # `llm_request` is passed by object reference.
    
    # Better approach: Monkeypatch `BaseLlmFlow._call_llm_async` with a FULL REPLACEMENT
    # that includes the fix. This is what I did in the file edit.
    pass 

    # FULL REPLACEMENT
    async def _call_llm_async_replacement(
        self,
        invocation_context: InvocationContext,
        llm_request: LlmRequest,
        model_response_event: Event,
    ) -> AsyncGenerator[LlmResponse, None]:
        # Runs before_model_callback if it exists.
        if response := await self._handle_before_model_callback(
            invocation_context, llm_request, model_response_event
        ):
            yield response
            return

        llm_request.config = llm_request.config or types.GenerateContentConfig()

        # --- PATCH: Apply thinking config ---
        from google.adk.agents.llm_agent import LlmAgent
        agent = invocation_context.agent
        if isinstance(agent, LlmAgent) and agent.planner and hasattr(agent.planner, 'apply_thinking_config'):
            agent.planner.apply_thinking_config(llm_request)
        # ------------------------------------

        llm_request.config.labels = llm_request.config.labels or {}

        # Add agent name as a label to the llm_request.
        if base_llm_flow._ADK_AGENT_NAME_LABEL_KEY not in llm_request.config.labels:
            llm_request.config.labels[base_llm_flow._ADK_AGENT_NAME_LABEL_KEY] = (
                invocation_context.agent.name
            )

        # Calls the LLM.
        llm = self.__get_llm(invocation_context)
        
        # ... (Rest of original implementation logic calling _run_and_handle_error) ...
        # To avoid copying massive private methods, we can assume the original implementation 
        # of _run_and_handle_error is available on `self`.
        
        # Original logic repeated:
        if invocation_context.run_config.support_cfc:
             # ... CFC logic ...
             # We can't easily copy this without importing EVERYTHING locally.
             pass 
             # Wait, copying 100 lines of library code into a patch file is brittle.
        
        # Alternative: We modify `llm_request` in `_preprocess_async`?
        # `base_llm_flow.py`: `_preprocess_async` calls `processor.run_async`.
        # If we can insert a processor that applies the config?
        # `BaseLlmFlow` has `request_processors`.
        # `LlmAgent` creation adds processors? No.
        
        # But wait! I can monkeypatch the CLASS logic.
        # Or I can use the wrapper approach if I trust `llm_request` reference.
        
    # The wrapper approach is safer if it works.
    # When `wrapper(ctx, req, event)` is called:
    # 1. It executes my "INJECTED LOGIC".
    # 2. It calls `original(ctx, req, event)`.
    # 3. It yields from it.
    
    # Does `original` use the `req` object I modified? YES.
    # Does `original` reset `req.config`?
    # Line 729: `llm_request.config = llm_request.config or types.GenerateContentConfig()`
    # If I set it, it uses it.
    # But does it OVERWRITE `thinking_config`? No.
    
    # So the wrapper IS sufficient!
    
    async def simple_wrapper(self, invocation_context, llm_request, model_response_event):
        # 1. PATCH Thinking Config
        llm_request.config = llm_request.config or types.GenerateContentConfig()
        from google.adk.agents.llm_agent import LlmAgent
        agent = invocation_context.agent
        if isinstance(agent, LlmAgent) and agent.planner and hasattr(agent.planner, 'apply_thinking_config'):
            agent.planner.apply_thinking_config(llm_request)
            
        # 2. SEMAPHORE WRAPPER (Global Concurrency Control)
        # This ensures only 4 agents hit the API at the same time.
        # The semaphore is released when the generator exhausts (finishes streaming).
        async with SEM:
            # 3. STAGGERING (Jitter): Wait a random bit so they don't hit the server at once
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # 4. DELEGATE to the original patched/unpatched method
            async for item in original_call_llm_async(self, invocation_context, llm_request, model_response_event):
                yield item

    base_llm_flow.BaseLlmFlow._call_llm_async = simple_wrapper
    logger.info("✅ Patched BaseLlmFlow._call_llm_async (Wrapper method).")


def _patch_contents():
    """Patches _get_contents to implement signature propagation."""
    
    # We must REWRITE _get_contents because the logic is INSIDE the loop.
    # We cannot wrap it.
    
    def patched_get_contents(
        current_branch: Optional[str],
        events: List[Event],
        agent_name: str = '',
        *,
        preserve_function_call_ids: bool = False
    ) -> List[types.Content]:
        # Filter out events that are annulled by a rewind.
        rewind_filtered_events = []
        i = len(events) - 1
        while i >= 0:
            event = events[i]
            if event.actions and event.actions.rewind_before_invocation_id:
                rewind_invocation_id = event.actions.rewind_before_invocation_id
                for j in range(0, i, 1):
                    if events[j].invocation_id == rewind_invocation_id:
                        i = j
                        break
            else:
                rewind_filtered_events.append(event)
            i -= 1
        rewind_filtered_events.reverse()

        # Parse the events, using the updated filtering logic from ADK
        from google.adk.flows.llm_flows.contents import _should_include_event_in_context
        
        raw_filtered_events = [
            e for e in rewind_filtered_events 
            if _should_include_event_in_context(current_branch, e)
        ]

        has_compaction_events = any(
            e.actions and e.actions.compaction for e in raw_filtered_events
        )

        if has_compaction_events:
            events_to_process = _process_compaction_events(raw_filtered_events)
        else:
            events_to_process = raw_filtered_events

        accumulated_input_transcription = ''
        accumulated_output_transcription = ''
        filtered_events = []
        
        for i in range(len(events_to_process)):
            event = events_to_process[i]
            if not event.content:
                if event.input_transcription and event.input_transcription.text:
                    accumulated_input_transcription += event.input_transcription.text
                    if (i != len(events_to_process) - 1 and events_to_process[i+1].input_transcription and events_to_process[i+1].input_transcription.text): continue
                    event = event.model_copy(deep=True)
                    event.input_transcription = None
                    event.content = types.Content(role='user', parts=[types.Part(text=accumulated_input_transcription)])
                    accumulated_input_transcription = ''
                elif event.output_transcription and event.output_transcription.text:
                    accumulated_output_transcription += event.output_transcription.text
                    if (i != len(events_to_process) - 1 and events_to_process[i+1].output_transcription and events_to_process[i+1].output_transcription.text): continue
                    event = event.model_copy(deep=True)
                    event.output_transcription = None
                    event.content = types.Content(role='model', parts=[types.Part(text=accumulated_output_transcription)])
                    accumulated_output_transcription = ''

            if _is_other_agent_reply(agent_name, event):
                if converted_event := _present_other_agent_message(event):
                    filtered_events.append(converted_event)
            else:
                filtered_events.append(event)

        result_events = _rearrange_events_for_latest_function_response(filtered_events)
        result_events = _rearrange_events_for_async_function_responses_in_history(result_events)

        # --- SIGNATURE PROPAGATION PATCH ---
        contents_list = []
        last_signature = None 

        for event in result_events:
            content = copy.deepcopy(event.content)
            if content:
                if content.parts:
                    # Propagate signature backward for tools
                    for part in content.parts:
                        if getattr(part, 'thought_signature', None):
                            last_signature = part.thought_signature
                    
                    for part in content.parts:
                        if part.function_call:
                            sig = getattr(part, 'thought_signature', None)
                            thought = getattr(part, 'thought', None)
                            if sig is None and thought is None:
                                if last_signature:
                                    part.thought_signature = last_signature

                if not preserve_function_call_ids:
                    remove_client_function_call_id(content)
                    
                contents_list.append(content)
        return contents_list

    contents._get_contents = patched_get_contents
    logger.info("✅ Patched contents._get_contents (Signature Propagation).")
