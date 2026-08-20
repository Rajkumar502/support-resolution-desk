import os
import json
import datetime
from src.config import settings
from src.services.llm import get_gemini_model
from src.graph.workflow import graph
from src.schemas.tickets import TicketResolutionState, TicketMetadata

def run_custom_evaluation():
    golden_path = "tests/golden_dataset.json"
    if not os.path.exists(golden_path):
        print("❌ Golden dataset not found at tests/golden_dataset.json")
        return

    with open(golden_path, "r") as f:
        dataset = json.load(f)

    # Use your existing central Gemini model client as the judge
    judge_llm = get_gemini_model(temperature=0.0)

    print(f"🚀 Starting Lightweight RAG Evaluation using {settings.MODEL_NAME}...")

    for idx, item in enumerate(dataset[:2]):
        query = item.get("input")
        if not query:
            continue
            
        item.get("expected_category", "order_status")

        print(f"\n--- Running Graph for Ticket #{idx+1}: '{query[:40]}...' ---")
        initial_state = TicketResolutionState(
            raw_email_text=query,
            metadata=TicketMetadata(
                sender_email="eval@example.com", 
                subject="Eval Run", 
                timestamp=str(datetime.datetime.utcnow()),
                thread_id=f"eval_{idx}"
            )
        )
        
        result = graph.invoke(initial_state, config={"configurable": {"thread_id": f"eval_{idx}"}})
        actual_output = result.get("final_output", "")
        
        # Extract RAG chunks if available
        retrieved_docs = result.get("retrieved_docs")
        context = " ".join(retrieved_docs.chunks) if retrieved_docs and hasattr(retrieved_docs, "chunks") else "General support context."

        # Prompt the judge model directly for faithfulness & relevancy scoring
        eval_prompt = f"""
        You are an AI system evaluator. Evaluate the following customer support response based on the Context and User Query.
        
        User Query: {query}
        Retrieved Context: {context}
        Generated Response: {actual_output}
        
        Provide your evaluation strictly in the following JSON format:
        {{
            "faithfulness_score": <float between 0.0 and 1.0, where 1.0 means fully grounded in context>,
            "relevancy_score": <float between 0.0 and 1.0, where 1.0 means perfectly addresses the query>,
            "reasoning": "Brief explanation of the scores"
        }}
        """

        print(f"⚖️ Grading Ticket #{idx+1} with Gemini Judge...")
        evaluation_response = judge_llm.invoke(eval_prompt)
        
        try:
            content = evaluation_response.content
            # Handle if content is returned as a list of blocks by LangChain
            if isinstance(content, list):
                content = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content])
            
            content = str(content).strip()
            
            # Clean markdown code blocks
            if "```" in content:
                content = content.split("```")[1].replace("json", "").strip()
                
            scores = json.loads(content)
            print(f"✅ Ticket #{idx+1} Results:")
            print(f"   - Faithfulness Score: {scores.get('faithfulness_score')}")
            print(f"   - Relevancy Score:    {scores.get('relevancy_score')}")
            print(f"   - Reasoning:          {scores.get('reasoning')}")
        except Exception as e:
            print(f"⚠️ Parsing Error: {e} | Raw Output: {evaluation_response.content}")

if __name__ == "__main__":
    run_custom_evaluation()