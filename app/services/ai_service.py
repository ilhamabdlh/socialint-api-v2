import google.generativeai as genai
import concurrent.futures
import time
from typing import List, Tuple
from app.config.settings import settings

# Initialize Gemini
genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel(settings.gemini_model)

class AIAnalysisService:
    def __init__(self):
        self.max_workers = settings.max_workers
        self.model = gemini_model
    
    def language_based_cleansing(self, batch_data: List[str]) -> List[str]:
        """Filter only Indonesian language texts using AI"""
        
        language_prompt = (
            "Evaluate the following text. Return FALSE if the text's language "
            "in general is Indonesian or dialects spoken in indonesia. "
            "Otherwise return TRUE if it's not in Indonesian language or dialects spoken in Indonesia. "
            "Respond with only TRUE or FALSE"
        )
        
        def check_language(text: str) -> Tuple[str, str]:
            prompt = f"{language_prompt} Text: {text}"
            retries = 0
            while retries < 3:
                try:
                    response = self.model.generate_content(prompt)
                    if response and response.text:
                        decision = response.text.strip().upper()
                        return (decision, text)
                    return ('ERROR', text)
                except Exception as e:
                    retries += 1
                    if retries >= 3:
                        return ('ERROR', text)
                    time.sleep(1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(check_language, batch_data))
        
        # Keep only Indonesian texts (FALSE means Indonesian)
        cleaned = [text for decision, text in results if decision == "FALSE"]
        return cleaned
    
    def sentiment_analysis(self, batch_data: List[str]) -> List[str]:
        """Analyze sentiment of texts"""
        
        sentiment_prompt = (
            "Analyze the sentiment of the following text and classify it as "
            "'Positive', 'Negative', or 'Neutral'. Respond only with one of these three words."
        )
        
        def get_sentiment(text: str) -> str:
            prompt = f"{sentiment_prompt} Text: {text}"
            retries = 0
            while retries < 3:
                try:
                    response = self.model.generate_content(prompt)
                    if response and response.text:
                        return response.text.strip()
                    return 'Neutral'
                except Exception as e:
                    retries += 1
                    if retries >= 3:
                        return 'Neutral'
                    time.sleep(1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            sentiments = list(executor.map(get_sentiment, batch_data))
        
        return sentiments
    
    def topic_analysis(self, batch_data: List[str], existing_topics: List[str]) -> List[str]:
        """Identify main topics from texts"""
        
        topic_prompt = f"""Analyze the following text and infer its main topic.

Consider the following existing topic labels: {existing_topics}

If the text's topic is closely related to one of the existing labels, return that label.
If the text's topic is unique and does not closely approximate any of the existing labels, 
invent a new, concise topic label (2-4 words) and return ONLY the new label.

Respond only with an existing or a new topic label."""
        
        def get_topic(text: str) -> str:
            prompt = f"{topic_prompt} Text: {text}"
            retries = 0
            while retries < 3:
                try:
                    response = self.model.generate_content(prompt)
                    if response and response.text:
                        return response.text.strip()
                    return 'Unknown'
                except Exception as e:
                    retries += 1
                    if retries >= 3:
                        return 'Unknown'
                    time.sleep(1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            topics = list(executor.map(get_topic, batch_data))
        
        # Update existing topics list with new ones
        for topic in topics:
            if topic not in existing_topics and topic != 'Unknown':
                existing_topics.append(topic)
        
        return topics
    
    # TODO: implement these for future audience profiling features
    def interest_analysis(self, batch_data: List[str], existing_interests: List[str]) -> List[str]:
        """Analyze user interests - for Layer 2 audience profiling"""
        # Will be implemented when we add comprehensive audience profiles
        pass
    
    def communication_style_analysis(self, batch_data: List[str]) -> List[str]:
        """Analyze communication style - for audience profiling"""
        # Will be implemented for audience profiling
        pass
    
    def values_analysis(self, batch_data: List[str], existing_values: List[str]) -> List[str]:
        """Analyze user values - for audience profiling"""
        # Will be implemented for audience profiling
        pass
    
    def emotions_analysis(self, batch_data: List[str]) -> List[str]:
        """
        Analyze emotions expressed in texts
        Returns: joy, anger, sadness, fear, surprise, disgust, trust, anticipation
        """
        
        emotions_prompt = (
            "Analyze the emotion expressed in the following text. "
            "Choose the PRIMARY emotion from: joy, anger, sadness, fear, surprise, disgust, trust, anticipation, neutral. "
            "Respond with ONLY ONE emotion word."
        )
        
        def get_emotion(text: str) -> str:
            prompt = f"{emotions_prompt} Text: {text}"
            retries = 0
            while retries < 3:
                try:
                    response = self.model.generate_content(prompt)
                    if response and response.text:
                        emotion = response.text.strip().lower()
                        # Validate emotion
                        valid_emotions = ['joy', 'anger', 'sadness', 'fear', 'surprise', 'disgust', 'trust', 'anticipation', 'neutral']
                        if emotion in valid_emotions:
                            return emotion
                        return 'neutral'
                    return 'neutral'
                except Exception as e:
                    retries += 1
                    if retries >= 3:
                        return 'neutral'
                    time.sleep(1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            emotions = list(executor.map(get_emotion, batch_data))
        
        return emotions
    
    def extract_demographics(self, batch_data: List[str]) -> List[dict]:
        """
        Extract demographic hints from user text
        Returns: age_group, gender, location_hint
        """
        
        demographics_prompt = (
            "Analyze the following text and infer demographic information about the author. "
            "Return ONLY a JSON object with these fields: "
            '{"age_group": "18-24 or 25-34 or 35-44 or 45-54 or 55+ or unknown", '
            '"gender": "male or female or neutral or unknown", '
            '"location_hint": "city/country if mentioned or unknown"}. '
            "Respond ONLY with valid JSON."
        )
        
        def get_demographics(text: str) -> dict:
            prompt = f"{demographics_prompt} Text: {text}"
            retries = 0
            while retries < 3:
                try:
                    response = self.model.generate_content(prompt)
                    if response and response.text:
                        import json
                        # Try to extract JSON from response
                        text_response = response.text.strip()
                        # Remove markdown code blocks if present
                        if text_response.startswith('```'):
                            text_response = text_response.split('\n', 1)[1]
                            text_response = text_response.rsplit('\n', 1)[0]
                        
                        demographics = json.loads(text_response)
                        return demographics
                    return {"age_group": "unknown", "gender": "unknown", "location_hint": "unknown"}
                except Exception as e:
                    retries += 1
                    if retries >= 3:
                        return {"age_group": "unknown", "gender": "unknown", "location_hint": "unknown"}
                    time.sleep(1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            demographics = list(executor.map(get_demographics, batch_data))
        
        return demographics
    
    async def analyze_topics(self, text: str) -> dict:
        """Analyze topics in text"""
        try:
            prompt = f"""
            Analyze the following text and identify the main topics. 
            Return a JSON response with this format:
            {{
                "topics": [
                    {{"topic": "topic_name", "relevance": 0.8, "confidence": 0.9}}
                ]
            }}
            
            Text: {text}
            """
            
            response = self.model.generate_content(prompt)
            if response and response.text:
                import json
                try:
                    return {"success": True, "data": json.loads(response.text)}
                except:
                    # Fallback if JSON parsing fails
                    return {
                        "success": True, 
                        "data": {
                            "topics": [{"topic": "general", "relevance": 0.5, "confidence": 0.7}]
                        }
                    }
            return {"success": False, "message": "No response from AI"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment of text"""
        try:
            prompt = f"""
            Analyze the sentiment of the following text. 
            Return a JSON response with this format:
            {{
                "sentiment": "positive/negative/neutral",
                "sentiment_score": 0.8,
                "confidence": 0.9
            }}
            
            Text: {text}
            """
            
            response = self.model.generate_content(prompt)
            if response and response.text:
                import json
                try:
                    return {"success": True, "data": json.loads(response.text)}
                except:
                    # Fallback if JSON parsing fails
                    return {
                        "success": True,
                        "data": {
                            "sentiment": "neutral",
                            "sentiment_score": 0.0,
                            "confidence": 0.5
                        }
                    }
            return {"success": False, "message": "No response from AI"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def analyze_emotions(self, text: str) -> dict:
        """Analyze emotions in text"""
        try:
            prompt = f"""
            Analyze the emotions expressed in the following text. 
            Return a JSON response with this format:
            {{
                "emotions": {{
                    "joy": 0.3,
                    "anger": 0.1,
                    "fear": 0.0,
                    "sadness": 0.1,
                    "surprise": 0.2,
                    "trust": 0.4,
                    "anticipation": 0.3,
                    "disgust": 0.0
                }}
            }}
            
            Text: {text}
            """
            
            response = self.model.generate_content(prompt)
            if response and response.text:
                import json
                try:
                    return {"success": True, "data": json.loads(response.text)}
                except:
                    # Fallback if JSON parsing fails
                    return {
                        "success": True,
                        "data": {
                            "emotions": {
                                "joy": 0.2,
                                "anger": 0.1,
                                "fear": 0.0,
                                "sadness": 0.1,
                                "surprise": 0.1,
                                "trust": 0.3,
                                "anticipation": 0.2,
                                "disgust": 0.0
                            }
                        }
                    }
            return {"success": False, "message": "No response from AI"}
        except Exception as e:
            return {"success": False, "message": str(e)}

