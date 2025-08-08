"""
Locust load testing file for FisioRAG API.
Advanced scenarios with realistic user behavior patterns.
"""

import json
import random
import time
from typing import Dict, Any
import uuid

from locust import HttpUser, task, between
from locust.exception import RescheduleTask

from config import LoadTestConfig, TestScenario, SCENARIO_CONFIGS


class FisioRAGUser(HttpUser):
    """
    Simulates a realistic FisioRAG user behavior.
    Models physiotherapy students and professionals usage patterns.
    """
    
    wait_time = between(2, 8)  # Realistic think time between requests
    
    def on_start(self):
        """Initialize user session and authentication."""
        self.config = LoadTestConfig()
        self.session_id = None
        self.user_id = f"load_test_user_{uuid.uuid4().hex[:8]}"
        self.tenant_slug = random.choice(self.config.test_tenants)
        
        # User profile affects behavior
        self.user_type = random.choice([
            "student",      # 60% - University students
            "professional", # 30% - Working professionals  
            "researcher"    # 10% - Academic researchers
        ])
        
        # Initialize conversation session
        self.initialize_session()
    
    def initialize_session(self):
        """Create a new conversation session."""
        try:
            response = self.client.post("/chat", json={
                "message": "Ciao, sono qui per studiare fisioterapia",
                "user_id": self.user_id,
                "tenant_slug": self.tenant_slug,
                "search_type": "hybrid"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
            
        except Exception as e:
            print(f"Session initialization failed: {e}")
    
    @task(30)
    def ask_clinical_question(self):
        """
        Main task: Ask clinical questions (most common user behavior).
        Weight: 30 (30% of total actions)
        """
        if not self.session_id:
            self.initialize_session()
            if not self.session_id:
                raise RescheduleTask()
        
        # Select question based on user type
        query = self.get_realistic_query()
        
        request_data = {
            "message": query,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_slug": self.tenant_slug,
            "search_type": self.get_search_preference(),
            "metadata": {
                "user_type": self.user_type,
                "context": "clinical_study"
            }
        }
        
        with self.client.post(
            "/chat",
            json=request_data,
            name="chat_clinical_question",
            catch_response=True
        ) as response:
            self.validate_chat_response(response, "clinical_question")
    
    @task(15)
    def follow_up_question(self):
        """
        Follow-up questions in conversation context.
        Weight: 15 (15% of total actions)
        """
        if not self.session_id:
            raise RescheduleTask()
        
        follow_ups = [
            "Puoi spiegare meglio questo concetto?",
            "Ci sono controindicazioni da considerare?",
            "Quale è l'evidenza scientifica di questo trattamento?",
            "Come si valuta l'efficacia di questo approccio?",
            "Esistono alternative terapeutiche?",
            "Quali sono i tempi di recupero tipici?"
        ]
        
        request_data = {
            "message": random.choice(follow_ups),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_slug": self.tenant_slug,
            "search_type": "vector"
        }
        
        with self.client.post(
            "/chat",
            json=request_data,
            name="chat_follow_up",
            catch_response=True
        ) as response:
            self.validate_chat_response(response, "follow_up")
    
    @task(10)
    def streaming_chat(self):
        """
        Test streaming chat functionality.
        Weight: 10 (10% of total actions)
        """
        if not self.session_id:
            raise RescheduleTask()
        
        query = random.choice(self.config.sample_queries)
        
        request_data = {
            "message": query,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_slug": self.tenant_slug,
            "search_type": "hybrid",
            "stream": True
        }
        
        with self.client.post(
            "/chat/stream",
            json=request_data,
            name="chat_streaming",
            stream=True,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Consume stream
                try:
                    for line in response.iter_lines():
                        if line:
                            # Validate streaming format
                            if line.startswith(b"data: "):
                                data = line[6:]
                                if data != b"[DONE]":
                                    json.loads(data)
                    response.success()
                except Exception as e:
                    response.failure(f"Stream parsing error: {e}")
            else:
                response.failure(f"Streaming failed: {response.status_code}")
    
    @task(5)
    def health_check(self):
        """
        Regular health checks (monitoring behavior).
        Weight: 5 (5% of total actions)
        """
        with self.client.get(
            "/health",
            name="health_check",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    response.success()
                else:
                    response.failure(f"Unhealthy status: {data.get('status')}")
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(3)
    def detailed_health_check(self):
        """
        Detailed health monitoring.
        Weight: 3 (3% of total actions)
        """
        with self.client.get(
            "/health/detailed",
            name="health_detailed",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Validate response structure
                    required_fields = ["status", "database", "graph_database"]
                    if all(field in data for field in required_fields):
                        response.success()
                    else:
                        response.failure("Missing required health fields")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON in health response")
            else:
                response.failure(f"Detailed health failed: {response.status_code}")
    
    @task(2)
    def database_status(self):
        """
        Database status monitoring.
        Weight: 2 (2% of total actions)
        """
        with self.client.get(
            "/status/database",
            name="database_status",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Database status failed: {response.status_code}")
    
    def get_realistic_query(self) -> str:
        """Get realistic query based on user type."""
        if self.user_type == "student":
            # Students ask more basic, educational questions
            student_queries = [
                "Cos'è la propriocezione e come si allena?",
                "Differenze tra contrazione isometrica ed isotonica",
                "Come si valuta la forza muscolare?",
                "Principi della riabilitazione post-trauma",
                "Tecniche di stretching più efficaci",
                "Anatomia del ginocchio e biomeccanica",
                "Fasi della guarigione tissutale",
                "Indicazioni per l'uso del ghiaccio vs calore"
            ]
            return random.choice(student_queries)
        
        elif self.user_type == "professional":
            # Professionals ask specific clinical questions
            return random.choice(self.config.sample_queries)
        
        else:  # researcher
            # Researchers ask evidence-based questions
            research_queries = [
                "Evidenze scientifiche per l'efficacia della terapia manuale",
                "Systematic review sui protocolli ACL",
                "Meta-analisi sull'elettroterapia per dolore cronico",
                "Studi clinici randomizzati su mobilizzazione spinale",
                "Outcome measures validati per spalla dolorosa",
                "Biomeccanica del movimento e analisi cinematica",
                "Neurofisiologia del controllo motorio",
                "Plasticità neurale nella riabilitazione"
            ]
            return random.choice(research_queries)
    
    def get_search_preference(self) -> str:
        """Get search type preference based on user type."""
        if self.user_type == "student":
            # Students prefer comprehensive hybrid search
            return random.choice(["hybrid", "vector", "hybrid"])
        elif self.user_type == "professional":
            # Professionals balance between specific and broad search
            return random.choice(["vector", "graph", "hybrid"])
        else:  # researcher
            # Researchers prefer graph for connections
            return random.choice(["graph", "hybrid", "graph"])
    
    def validate_chat_response(self, response, task_name: str):
        """Validate chat response quality and performance."""
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Validate response structure
                required_fields = ["message", "session_id"]
                if not all(field in data for field in required_fields):
                    response.failure(f"Missing required fields in {task_name}")
                    return
                
                # Validate response content quality
                message = data.get("message", "")
                if len(message) < 50:
                    response.failure(f"Response too short in {task_name}")
                    return
                
                # Validate performance (already tracked by Locust)
                if response.elapsed.total_seconds() > self.config.response_time_p95_threshold:
                    print(f"Slow response in {task_name}: {response.elapsed.total_seconds():.2f}s")
                
                response.success()
                
            except json.JSONDecodeError:
                response.failure(f"Invalid JSON in {task_name}")
        
        elif response.status_code == 429:
            # Rate limiting - reschedule
            response.failure(f"Rate limited in {task_name}")
            raise RescheduleTask()
        
        else:
            response.failure(f"{task_name} failed: {response.status_code}")


class StudentUser(FisioRAGUser):
    """Specialized user class for university students."""
    weight = 60  # 60% of users are students
    
    def on_start(self):
        super().on_start()
        self.user_type = "student"


class ProfessionalUser(FisioRAGUser):
    """Specialized user class for healthcare professionals.""" 
    weight = 30  # 30% of users are professionals
    
    def on_start(self):
        super().on_start()
        self.user_type = "professional"


class ResearcherUser(FisioRAGUser):
    """Specialized user class for researchers."""
    weight = 10  # 10% of users are researchers
    
    def on_start(self):
        super().on_start() 
        self.user_type = "researcher"
        # Researchers have longer think time
        self.wait_time = between(5, 15)
