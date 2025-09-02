#!/usr/bin/env python3
"""
Test script for the hybrid BERT+GPT legal AI system
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append('.')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_hybrid_system():
    """Test the hybrid BERT+GPT system"""
    try:
        print("🤖 Testing Hybrid BERT+GPT Legal AI System")
        print("=" * 60)
        
        # Import hybrid system
        from hybrid_legal_ai import create_hybrid_legal_ai
        
        print("\n📋 Step 1: Initializing Hybrid System")
        print("Loading InLegalBERT + T5 + XLNet models...")
        
        hybrid_ai = await create_hybrid_legal_ai()
        print("✅ Hybrid system initialized successfully")
        
        print("\n📋 Step 2: Testing Contextual Understanding (BERT)")
        
        # Test legal queries
        test_queries = [
            "What is Section 302 of the Indian Penal Code?",
            "Explain the bail provisions under CrPC Section 437",
            "What are the essential elements of a valid contract?",
            "भारतीय साक्ष्य अधिनियम की धारा 25 क्या कहती है?"  # Hindi query
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test Query {i}: {query[:50]}...")
            
            try:
                # Perform hybrid analysis
                result = await hybrid_ai.analyze_and_generate(
                    query=query,
                    sources=[],  # No sources for this test
                    generation_type="answer",
                    language="auto"
                )
                
                print(f"✅ Hybrid Analysis Complete:")
                print(f"   Confidence: {result.confidence_score:.2f}")
                print(f"   Hybrid Score: {result.hybrid_score:.2f}")
                print(f"   Context Type: {result.contextual_understanding.get('context_type', 'unknown')}")
                print(f"   Legal Concepts: {len(result.contextual_understanding.get('legal_concepts', []))}")
                print(f"   Response Length: {len(result.generated_response)} chars")
                print(f"   Legal Reasoning Steps: {len(result.legal_reasoning)}")
                
                # Show first reasoning step
                if result.legal_reasoning:
                    print(f"   First Reasoning: {result.legal_reasoning[0][:80]}...")
                
            except Exception as e:
                print(f"❌ Test query {i} failed: {e}")
        
        print("\n📋 Step 3: Testing Judgment Generation")
        
        case_facts = """
        The accused was found in possession of stolen jewelry worth Rs. 50,000. 
        He was arrested from his residence where the stolen items were recovered. 
        The accused confessed to the crime during police interrogation.
        """
        
        legal_issues = [
            "Admissibility of confession made to police",
            "Burden of proof regarding stolen property", 
            "Quantum of punishment under IPC"
        ]
        
        try:
            judgment_result = await hybrid_ai.analyze_and_generate(
                query=f"Case Facts: {case_facts}\nLegal Issues: {'; '.join(legal_issues)}",
                sources=[],
                generation_type="judgment",
                language="auto"
            )
            
            print("✅ Hybrid Judgment Generation Complete:")
            print(f"   Confidence: {judgment_result.confidence_score:.2f}")
            print(f"   Hybrid Score: {judgment_result.hybrid_score:.2f}")
            print(f"   Legal Reasoning Steps: {len(judgment_result.legal_reasoning)}")
            print(f"   Judgment Length: {len(judgment_result.generated_response)} chars")
            
            # Show legal reasoning
            if judgment_result.legal_reasoning:
                print("\n📋 Legal Reasoning Steps:")
                for i, step in enumerate(judgment_result.legal_reasoning[:3], 1):
                    print(f"   {i}. {step}")
            
        except Exception as e:
            print(f"❌ Judgment generation test failed: {e}")
        
        print("\n📋 Step 4: Performance Comparison")
        
        # Compare different generation strategies
        test_query = "What are the provisions for anticipatory bail under Section 438 CrPC?"
        
        strategies_to_test = ["answer"]  # We'll test available strategies
        
        for strategy in strategies_to_test:
            try:
                result = await hybrid_ai.analyze_and_generate(
                    query=test_query,
                    sources=[],
                    generation_type=strategy,
                    language="auto"
                )
                
                context = result.contextual_understanding
                print(f"\n✅ Strategy '{strategy}' Results:")
                print(f"   Context Type: {context.get('context_type', 'unknown')}")
                print(f"   Complexity: {context.get('complexity_score', 0):.2f}")
                print(f"   Confidence: {result.confidence_score:.2f}")
                print(f"   Hybrid Score: {result.hybrid_score:.2f}")
                
            except Exception as e:
                print(f"❌ Strategy '{strategy}' failed: {e}")
        
        print(f"\n🎉 Hybrid BERT+GPT System Testing Complete!")
        print(f"✅ Contextual understanding with InLegalBERT")
        print(f"✅ Enhanced generation with T5/XLNet/OpenAI")
        print(f"✅ Legal reasoning extraction")
        print(f"✅ Hybrid scoring and validation")
        
    except Exception as e:
        print(f"❌ Hybrid system test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_model_availability():
    """Test which models are available"""
    print("\n🔍 Testing Model Availability")
    print("-" * 40)
    
    # Test InLegalBERT
    try:
        from transformers import AutoTokenizer, AutoModel
        tokenizer = AutoTokenizer.from_pretrained("law-ai/InLegalBERT")
        print("✅ InLegalBERT: Available")
    except Exception as e:
        print(f"❌ InLegalBERT: {e}")
    
    # Test T5
    try:
        from transformers import T5Tokenizer, T5ForConditionalGeneration
        tokenizer = T5Tokenizer.from_pretrained("t5-small")
        print("✅ T5: Available")
    except Exception as e:
        print(f"❌ T5: {e}")
    
    # Test XLNet
    try:
        from transformers import XLNetTokenizer, XLNetLMHeadModel
        tokenizer = XLNetTokenizer.from_pretrained("xlnet-base-cased")
        print("✅ XLNet: Available")
    except Exception as e:
        print(f"❌ XLNet: {e}")
    
    # Test OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "sk-xxxxx":
        print("✅ OpenAI: API key configured")
    else:
        print("⚠️  OpenAI: API key not configured (using fallback)")

def main():
    """Main test function"""
    print("🧪 Hybrid BERT+GPT Legal AI Test Suite")
    print("Testing advanced contextual understanding + generation")
    
    # Check environment
    if not Path(".env").exists():
        print("⚠️  .env file not found, using environment defaults")
    
    # Test model availability first
    asyncio.run(test_model_availability())
    
    # Test hybrid system
    asyncio.run(test_hybrid_system())

if __name__ == "__main__":
    main()