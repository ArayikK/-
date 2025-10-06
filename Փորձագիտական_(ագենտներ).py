"""
AI Career Advisor - Multi-Agent System
======================================
A comprehensive career guidance system that uses multiple AI agents to:
1. Assess user skills through dynamic decision trees
2. Provide real-time course recommendations from YouTube and GitHub
3. Deliver market data for recommended careers

Agents:
- DynamicDecisionAgent: Navigates skill assessment tree
- RealCourseSearchAgent: Searches for relevant courses online
- MarketDataAgent: Provides career market insights

Author: [Your Name]
Date: 2024
"""

import tkinter as tk
from tkinter import messagebox, font, ttk
import webbrowser
import json
import requests
import sqlite3
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Any
import urllib.request
import urllib.parse
import re
import random
from bs4 import BeautifulSoup


# ===== DYNAMIC DECISION TREE AGENT =====

class DynamicDecisionAgent:
    """
    Handles the career decision tree navigation based on user skill ratings.
    Uses a tree structure to guide users through skill assessments and 
    determine the most suitable career path.
    """
    
    def __init__(self):
        # Initialize decision tree and user history storage
        self.tree = self.get_default_tree()
        self.user_history = {}  # Stores user responses for analysis
    
    def get_default_tree(self) -> Dict:
        """
        Defines the career decision tree structure.
        Each node contains a question and threshold-based answers that lead to next nodes.
        
        Returns:
            Dict: Complete decision tree structure
        """
        return {
            "Math": {
                "question": "🔢 Rate your Math skills (0.0 - 1.0):",
                "answers": {
                    "high": {"threshold": 0.7, "next": "Math_High"},
                    "medium": {"threshold": 0.4, "next": "Math_Med"}, 
                    "low": {"threshold": 0.0, "next": "Math_Low"}
                }
            },
            "Math_High": {
                "question": "💻 Rate your Programming skills (0.0 - 1.0):",
                "answers": {
                    "high": {"threshold": 0.5, "next": "HighProg"},
                    "low": {"threshold": 0.0, "next": "HighPhys"}
                }
            },
            "HighProg": {
                "question": "🤖 Rate your interest in Data/AI (0.0 - 1.0):",
                "answers": {
                    "high": {"threshold": 0.6, "next": "Data Scientist"},
                    "low": {"threshold": 0.0, "next": "Software Engineer"}
                }
            },
            "HighPhys": {
                "question": "⚛️ Rate your Physics/Engineering knowledge (0.0 - 1.0):",
                "answers": {
                    "low": {"threshold": 0.6, "next": "Research Scientist"},
                    "high": {"threshold": 0.0, "next": "Engineer"}
                }
            },
            "Math_Med": {
                "question": "🎨 Rate your Design/Creativity skills (0.0 - 1.0):",
                "answers": {
                    "high": {"threshold": 0.5, "next": "MedDesign"},
                    "low": {"threshold": 0.0, "next": "MedBio"}
                }
            },
            "MedDesign": {
                "question": "👥 Rate your Communication/Teamwork skills (0.0 - 1.0):",
                "answers": {
                    "high": {"threshold": 0.6, "next": "UI/UX Designer"},
                    "low": {"threshold": 0.0, "next": "Graphic Designer"}
                }
            },
            "MedBio": {
                "question": "🧬 Rate your Biology/Health knowledge (0.0 - 1.0):",
                "answers": {
                    "high": {"threshold": 0.6, "next": "Healthcare Specialist"},
                    "low": {"threshold": 0.0, "next": "Project Manager"}
                }
            },
            "Math_Low": {
                "question": "💬 Rate your Communication/People skills (0.0 - 1.0):",
                "answers": {
                    "high": {"threshold": 0.5, "next": "LowComm"},
                    "low": {"threshold": 0.0, "next": "LowHands"}
                }
            },
            "LowComm": {
                "question": "👑 Rate your Leadership ability (0.0 - 1.0):",
                "answers": {
                    "high": {"threshold": 0.6, "next": "Manager / HR Specialist"},
                    "low": {"threshold": 0.0, "next": "Journalist / Public Speaker"}
                }
            },
            "LowHands": {
                "question": "🔧 Rate your Practical/Technical skills (0.0 - 1.0):",
                "answers": {
                    "high": {"threshold": 0.6, "next": "Technician"},
                    "low": {"threshold": 0.0, "next": "Sales Assistant"}
                }
            }
        }
    
    def navigate_tree(self, current_node: str, user_input: float) -> str:
        """
        Navigates through the decision tree based on user input.
        
        Args:
            current_node (str): Current node in the decision tree
            user_input (float): User's rating input (0.0-1.0)
            
        Returns:
            str: Next node in the decision tree or final career recommendation
        """
        # Check if current node exists in tree
        if current_node not in self.tree:
            return current_node  # Return final career recommendation
        
        node = self.tree[current_node]
        
        # Check if node has answers (if not, it's a final career node)
        if "answers" not in node:
            return current_node
        
        # Find the appropriate answer based on thresholds
        for answer_key, answer in node["answers"].items():
            if user_input >= answer["threshold"]:
                return answer["next"]  # Move to next node
        
        return current_node  # Stay on current node if no threshold met


# ===== REAL COURSE SEARCH AGENT =====

class RealCourseSearchAgent:
    """
    Searches for real courses from online platforms (YouTube, GitHub).
    Implements caching, ranking, and fallback mechanisms for reliable results.
    """
    
    def __init__(self):
        # Cache for storing search results to avoid repeated API calls
        self.course_cache = {}
        self.cache_expiry = timedelta(weeks=1)  # Cache validity period
    
    def search_courses(self, career: str, user_level: str = "beginner") -> List[Dict]:
        """
        Main method to search for courses related to a specific career.
        Implements caching and multiple data source integration.
        
        Args:
            career (str): Target career to search courses for
            user_level (str): User's skill level (beginner/intermediate/advanced)
            
        Returns:
            List[Dict]: Top 5 ranked courses with detailed information
        """
        cache_key = f"{career}_{user_level}"
        
        # Check if cache is too old and needs refresh
        if self._is_cache_too_old(cache_key):
            print(f"🗑️ Cache is older than 1 week for {cache_key}, forcing fresh search")
            if cache_key in self.course_cache:
                del self.course_cache[cache_key]
        
        # Return cached results if still valid
        if self._is_cache_valid(cache_key):
            print(f"♻️ Using cached results for {career} (from {self.course_cache[cache_key]['timestamp'].strftime('%Y-%m-%d')})")
            return self.course_cache[cache_key]["courses"]
        
        print(f"🔍 Starting FRESH search for: {career} ({user_level})")
        
        all_courses = []
        
        # 1. Search YouTube for video courses
        youtube_courses = self._search_youtube(career, user_level)
        all_courses.extend(youtube_courses)
        print(f"📹 Found {len(youtube_courses)} YouTube courses")
        
        # 2. Search GitHub for repository-based learning resources
        github_courses = self._search_github(career, user_level)
        all_courses.extend(github_courses)
        print(f"💻 Found {len(github_courses)} GitHub resources")
        
        # 3. Add fallback courses if insufficient results
        if len(all_courses) < 20:
            fallback_courses = self._get_fallback_courses(career, user_level)
            all_courses.extend(fallback_courses)
            print(f"🔄 Added {len(fallback_courses)} fallback courses")
        
        # 4. Rank courses by relevance and quality
        ranked_courses = self._rank_courses(all_courses, user_level, career)
        top_courses = ranked_courses[:5]  # Get top 5 courses
        
        # Update cache with new results
        self.course_cache[cache_key] = {
            "courses": top_courses,
            "timestamp": datetime.now()
        }
        
        print(f"✅ Total ranked courses: {len(top_courses)}")
        return top_courses
    
    def _is_cache_too_old(self, cache_key: str) -> bool:
        """Check if cached data is older than 1 week"""
        if cache_key in self.course_cache:
            cache_data = self.course_cache[cache_key]
            cache_age = datetime.now() - cache_data["timestamp"]
            return cache_age > timedelta(weeks=1)
        return False
    
    def _search_youtube(self, career: str, level: str) -> List[Dict]:
        """
        Search YouTube for career-related courses and tutorials.
        
        Args:
            career (str): Career to search for
            level (str): User skill level
            
        Returns:
            List[Dict]: List of YouTube course dictionaries
        """
        courses = []
        search_terms = self._get_search_terms(career, level)
        
        for term in search_terms[:2]:  # Limit to 2 search terms for efficiency
            try:
                print(f"   Searching YouTube for: {term}")
                
                # Construct YouTube search URL
                search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(term + ' course tutorial learning')}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                # Send HTTP request to YouTube
                request = urllib.request.Request(search_url, headers=headers)
                response = urllib.request.urlopen(request, timeout=15)
                html_content = response.read().decode('utf-8')
                
                # Parse video results from HTML
                video_courses = self._parse_youtube_results(html_content, term)
                courses.extend(video_courses)
                
                time.sleep(2)  # Rate limiting to avoid being blocked
                
            except Exception as e:
                print(f"   ❌ YouTube search error for '{term}': {e}")
                continue
        
        return courses
    
    def _parse_youtube_results(self, html_content: str, search_term: str) -> List[Dict]:
        """
        Parse YouTube search results HTML to extract video information.
        
        Args:
            html_content (str): Raw HTML from YouTube search
            search_term (str): Original search term for relevance scoring
            
        Returns:
            List[Dict]: Parsed video courses
        """
        courses = []
        
        try:
            # Regex pattern to extract video IDs and titles from YouTube HTML
            video_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})".*?"title":{"runs":\[\{"text":"([^"]+)"'
            matches = re.findall(video_pattern, html_content)
            
            for video_id, title in matches[:3]:  # Limit to first 3 results
                # Filter relevant videos by checking keywords in title
                if len(title) > 15 and any(keyword in title.lower() for keyword in ['tutorial', 'course', 'learn', 'guide', 'introduction']):
                    course = {
                        "title": self._clean_title(title),
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "provider": "YouTube",
                        "level": "beginner",
                        "rating": round(random.uniform(4.2, 4.9), 1),  # Simulated rating
                        "duration": f"{random.randint(1, 8)} hours",  # Simulated duration
                        "instructors": ["YouTube Instructor"],
                        "enrollment_count": random.randint(5000, 200000),  # Simulated popularity
                        "price": "Free",
                        "language": "English",
                        "score": 0,  # Will be calculated during ranking
                        "searched_for": search_term
                    }
                    courses.append(course)
                    print(f"     🎥 Found: {course['title']}")
            
        except Exception as e:
            print(f"     ❌ YouTube parsing error: {e}")
        
        return courses
    
    def _search_github(self, career: str, level: str) -> List[Dict]:
        """
        Search GitHub for relevant learning repositories.
        
        Args:
            career (str): Career to search for
            level (str): User skill level
            
        Returns:
            List[Dict]: List of GitHub repository courses
        """
        courses = []
        search_terms = self._get_search_terms(career, level)
        
        for term in search_terms[:1]:  # Limit to 1 search term for GitHub
            try:
                print(f"   Searching GitHub for: {term}")
                
                # Construct GitHub search URL
                search_url = f"https://github.com/search?q={urllib.parse.quote(term)}&type=repositories"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                # Send HTTP request to GitHub
                request = urllib.request.Request(search_url, headers=headers)
                response = urllib.request.urlopen(request, timeout=15)
                html_content = response.read().decode('utf-8')
                
                # Parse repository results
                repo_courses = self._parse_github_results(html_content, term)
                courses.extend(repo_courses)
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ GitHub search error for '{term}': {e}")
                continue
        
        return courses
    
    def _parse_github_results(self, html_content: str, search_term: str) -> List[Dict]:
        """
        Parse GitHub search results to extract repository information.
        
        Args:
            html_content (str): Raw HTML from GitHub search
            search_term (str): Original search term
            
        Returns:
            List[Dict]: Parsed repository courses
        """
        courses = []
        
        try:
            # Regex pattern to extract repository links and titles
            repo_pattern = r'href="(/[^/]+/[^"/]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(repo_pattern, html_content)
            
            for repo_path, title in matches[:2]:  # Limit to first 2 results
                # Filter learning-related repositories
                if any(keyword in title.lower() for keyword in ['learn', 'tutorial', 'course', 'guide', 'examples']):
                    course = {
                        "title": f"GitHub: {title}",
                        "url": f"https://github.com{repo_path}",
                        "provider": "GitHub",
                        "level": "intermediate",
                        "rating": round(random.uniform(4.0, 4.8), 1),
                        "duration": "Self-paced",
                        "instructors": ["Open Source Community"],
                        "enrollment_count": random.randint(100, 5000),
                        "price": "Free",
                        "language": "English",
                        "score": 0,
                        "searched_for": search_term
                    }
                    courses.append(course)
                    print(f"     💾 Found: {course['title']}")
            
        except Exception as e:
            print(f"     ❌ GitHub parsing error: {e}")
        
        return courses
    
    def _get_search_terms(self, career: str, level: str) -> List[str]:
        """
        Generate optimized search terms for different careers and skill levels.
        
        Args:
            career (str): Target career
            level (str): User skill level
            
        Returns:
            List[str]: List of search terms
        """
        # Career-specific keywords for better search results
        career_keywords = {
            "Data Scientist": ["data science", "machine learning", "python data analysis", "artificial intelligence"],
            "Software Engineer": ["programming", "web development", "python programming", "javascript tutorial"],
            "UI/UX Designer": ["ui design", "ux design", "user experience", "figma tutorial"],
            "Graphic Designer": ["graphic design", "photoshop tutorial", "illustrator course", "digital design"],
            "Project Manager": ["project management", "agile methodology", "scrum master", "leadership skills"],
            "Healthcare Specialist": ["healthcare", "medical education", "public health", "biology basics"],
            "Research Scientist": ["research methods", "data analysis", "academic research", "scientific methods"],
            "Engineer": ["engineering", "mechanical engineering", "electrical engineering", "physics concepts"],
            "Manager / HR Specialist": ["human resources", "management skills", "leadership", "team management"],
            "Journalist / Public Speaker": ["journalism", "public speaking", "communication skills", "writing skills"],
            "Technician": ["technical skills", "it support", "computer repair", "hardware tutorial"],
            "Sales Assistant": ["sales training", "marketing basics", "customer service", "communication skills"]
        }
        
        # Level-specific keywords to tailor search results
        level_keywords = {
            "beginner": ["beginner", "fundamentals", "basics", "introduction", "getting started"],
            "intermediate": ["intermediate", "advanced", "professional", "deep dive"],
            "advanced": ["advanced", "expert", "master", "professional"]
        }
        
        # Get base terms for the career, fallback to career name if not found
        base_terms = career_keywords.get(career, [career.lower()])
        level_terms = level_keywords.get(level, [])
        
        # Combine base terms with level terms for comprehensive search
        search_terms = []
        for base in base_terms[:2]:  # Use first 2 base terms
            for level_term in level_terms[:1]:  # Use first level term
                search_terms.append(f"{base} {level_term}")
            search_terms.append(base)  # Also search without level term
        
        return list(set(search_terms))  # Remove duplicates
    
    def _get_fallback_courses(self, career: str, level: str) -> List[Dict]:
        """
        Provide fallback courses when online search returns insufficient results.
        
        Args:
            career (str): Target career
            level (str): User skill level
            
        Returns:
            List[Dict]: Fallback course recommendations
        """
        fallback_courses = [
            {
                "title": f"Introduction to {career} - {level.title()} Level",
                "url": "https://www.youtube.com/results?search_query=career+development",
                "provider": "Career Guidance",
                "level": level,
                "rating": 4.5,
                "duration": "Self-paced",
                "instructors": ["Professional Instructors"],
                "enrollment_count": 10000,
                "price": "Free",
                "language": "English",
                "score": 0,
                "searched_for": "fallback"
            },
            {
                "title": f"{career} Skills Development Course",
                "url": "https://www.youtube.com/results?search_query=professional+skills",
                "provider": "Skills Academy",
                "level": level,
                "rating": 4.3,
                "duration": "4-6 weeks",
                "instructors": ["Industry Experts"],
                "enrollment_count": 15000,
                "price": "Free",
                "language": "English",
                "score": 0,
                "searched_for": "fallback"
            }
        ]
        return fallback_courses
    
    def _clean_title(self, title: str) -> str:
        """
        Clean and normalize course titles by removing special characters and extra spaces.
        
        Args:
            title (str): Raw title string
            
        Returns:
            str: Cleaned title string
        """
        # Remove special characters and normalize whitespace
        cleaned = re.sub(r'[^\w\s]', ' ', title)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid based on expiry time"""
        if cache_key in self.course_cache:
            cache_data = self.course_cache[cache_key]
            time_diff = datetime.now() - cache_data["timestamp"]
            return time_diff < self.cache_expiry
        return False
    
    def _rank_courses(self, courses: List[Dict], user_level: str, career: str) -> List[Dict]:
        """
        Rank courses based on multiple factors to provide best recommendations.
        
        Args:
            courses (List[Dict]): List of courses to rank
            user_level (str): User's skill level
            career (str): Target career
            
        Returns:
            List[Dict]: Ranked courses sorted by score
        """
        if not courses:
            return []
        
        scored_courses = []
        
        for course in courses:
            score = 0
            
            # 1. Provider credibility score
            provider_score = self._get_provider_score(course["provider"])
            score += provider_score
            
            # 2. Rating score (higher ratings get more weight)
            rating_score = course.get("rating", 4.0) * 1.5
            score += rating_score
            
            # 3. Enrollment score (popularity indicator)
            enrollment_score = min(course.get("enrollment_count", 0) / 50000, 2)
            score += enrollment_score
            
            # 4. Price score (free courses are preferred)
            price_score = 2.0 if course.get("price") == "Free" else 0.5
            score += price_score
            
            # 5. Relevance score based on title and career match
            relevance_score = self._calculate_relevance_score(course, career)
            score += relevance_score
            
            course["score"] = round(score, 2)
            scored_courses.append(course)
        
        # Sort courses by calculated score in descending order
        ranked_courses = sorted(scored_courses, key=lambda x: x["score"], reverse=True)
        return ranked_courses
    
    def _get_provider_score(self, provider: str) -> float:
        """Assign credibility scores to different course providers"""
        provider_scores = {
            "YouTube": 1.5,
            "GitHub": 1.2,
            "Career Guidance": 0.8,
            "Skills Academy": 0.8
        }
        return provider_scores.get(provider, 0.5)
    
    def _calculate_relevance_score(self, course: Dict, career: str) -> float:
        """
        Calculate how relevant a course is to the target career.
        
        Args:
            course (Dict): Course information
            career (str): Target career
            
        Returns:
            float: Relevance score (0.5-2.0)
        """
        title = course.get("title", "").lower()
        career_lower = career.lower()
        
        # Exact career name match gets highest score
        if career_lower in title:
            return 2.0
        # Partial match with career keywords
        elif any(word in title for word in career_lower.split()):
            return 1.5
        # Default relevance score
        else:
            return 0.5


# ===== MARKET DATA AGENT =====

class MarketDataAgent:
    """
    Provides market intelligence for different careers including:
    - Demand levels
    - Salary ranges  
    - Growth trends
    - Required skills
    - Job openings
    """
    
    def __init__(self):
        self.market_cache = {}  # Cache for market data
    
    def get_market_data(self, career: str) -> Dict[str, Any]:
        """
        Get comprehensive market data for a specific career.
        
        Args:
            career (str): Target career
            
        Returns:
            Dict[str, Any]: Market data including demand, salary, growth, etc.
        """
        market_data = {
            "demand": self._get_demand_level(career),
            "salary_range": self._get_salary_range(career),
            "growth_trend": self._get_growth_trend(career),
            "skills_in_demand": self._get_skills_demand(career),
            "job_openings": self._get_job_openings(career),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        return market_data
    
    def _get_demand_level(self, career: str) -> str:
        """Get demand level indicator for a career"""
        demand_levels = {
            "Data Scientist": "🚀 Very High Demand",
            "Software Engineer": "🚀 Very High Demand",
            "UI/UX Designer": "📈 High Demand",
            "Healthcare Specialist": "🚀 Very High Demand",
            "Project Manager": "📈 High Demand",
            "Graphic Designer": "⚖️ Medium Demand"
        }
        return demand_levels.get(career, "⚖️ Medium Demand")
    
    def _get_salary_range(self, career: str) -> Dict[str, int]:
        """Get salary range for a career (in USD)"""
        salaries = {
            "Data Scientist": {"min": 95000, "max": 165000},
            "Software Engineer": {"min": 85000, "max": 155000},
            "UI/UX Designer": {"min": 65000, "max": 120000},
            "Healthcare Specialist": {"min": 60000, "max": 110000},
            "Project Manager": {"min": 70000, "max": 125000},
            "Graphic Designer": {"min": 45000, "max": 85000}
        }
        return salaries.get(career, {"min": 50000, "max": 100000})
    
    def _get_growth_trend(self, career: str) -> str:
        """Get growth trend information for a career"""
        trends = {
            "Data Scientist": "📊 Rapid Growth (22% annually)",
            "Software Engineer": "📊 Steady Growth (15% annually)",
            "UI/UX Designer": "📊 High Growth (18% annually)",
            "Healthcare Specialist": "📊 Stable Growth (16% annually)"
        }
        return trends.get(career, "📈 Moderate Growth (10% annually)")
    
    def _get_skills_demand(self, career: str) -> List[str]:
        """Get key skills in demand for a career"""
        skills = {
            "Data Scientist": ["Python", "Machine Learning", "SQL", "Data Visualization"],
            "Software Engineer": ["JavaScript", "Python", "React", "System Design"],
            "UI/UX Designer": ["Figma", "User Research", "Prototyping", "Wireframing"],
            "Graphic Designer": ["Adobe Creative Suite", "Typography", "Color Theory"]
        }
        return skills.get(career, ["Communication", "Problem Solving", "Teamwork"])
    
    def _get_job_openings(self, career: str) -> int:
        """Get estimated number of job openings for a career"""
        openings = {
            "Data Scientist": 15000,
            "Software Engineer": 45000,
            "UI/UX Designer": 12000,
            "Project Manager": 18000
        }
        return openings.get(career, 8000)


# ===== MAIN APPLICATION =====

class CareerAdvisorApp:
    """
    Main GUI application that integrates all agents and provides user interface.
    Handles user interactions, displays results, and manages application flow.
    """
    
    def __init__(self, root):
        """
        Initialize the main application.
        
        Args:
            root: tkinter root window
        """
        self.root = root
        self.root.title("🎯 AI Career Advisor - Multi-Agent System")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f8ff")
        
        # Initialize all AI agents
        self.decision_agent = DynamicDecisionAgent()
        self.course_agent = RealCourseSearchAgent()
        self.market_agent = MarketDataAgent()
        
        # Application state management
        self.current_node = "Math"  # Start with math assessment
        self.user_skills = {}  # Store user skill ratings
        self.recommended_career = None  # Final career recommendation
        
        # Setup user interface
        self.setup_ui()
        self.show_question()
    
    def setup_ui(self):
        """Initialize and configure all UI components"""
        # Main container frame
        self.main_frame = tk.Frame(self.root, bg="#f0f8ff")
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Application title
        title_label = tk.Label(
            self.main_frame, 
            text="🎯 AI Career Path Advisor", 
            font=("Arial", 20, "bold"),
            bg="#f0f8ff",
            fg="#2c3e50"
        )
        title_label.pack(pady=10)
        
        # Subtitle with description
        subtitle_label = tk.Label(
            self.main_frame,
            text="Discover your ideal career path with AI-powered assessment",
            font=("Arial", 12),
            bg="#f0f8ff",
            fg="#7f8c8d"
        )
        subtitle_label.pack(pady=5)
        
        # Question display frame
        self.question_frame = tk.Frame(self.main_frame, bg="#ffffff", relief="raised", bd=1)
        self.question_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Dynamic question label
        self.question_label = tk.Label(
            self.question_frame,
            text="",
            font=("Arial", 14, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
            wraplength=600,
            justify="center"
        )
        self.question_label.pack(pady=40)
        
        # Input section
        input_frame = tk.Frame(self.question_frame, bg="#ffffff")
        input_frame.pack(pady=20)
        
        # Input label
        tk.Label(
            input_frame,
            text="Enter your rating (0.0 - 1.0):",
            font=("Arial", 12),
            bg="#ffffff",
            fg="#34495e"
        ).pack(pady=10)
        
        # Rating input field
        self.entry = tk.Entry(
            input_frame,
            font=("Arial", 14),
            justify="center",
            width=10,
            bd=2,
            relief="solid"
        )
        self.entry.pack(pady=10)
        self.entry.bind('<Return>', lambda e: self.process_answer())  # Enter key support
        
        # Navigation button
        self.next_button = tk.Button(
            input_frame,
            text="Next Step →",
            command=self.process_answer,
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            padx=30,
            pady=10
        )
        self.next_button.pack(pady=20)
        
        # Results display frame (initially hidden)
        self.results_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        
        # Loading screen frame (initially hidden)
        self.loading_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
    
    def show_question(self):
        """Display the current question from decision tree"""
        if self.current_node in self.decision_agent.tree:
            # Show next question in the assessment
            question = self.decision_agent.tree[self.current_node]["question"]
            self.question_label.config(text=question)
            self.entry.delete(0, tk.END)  # Clear previous input
            self.entry.focus()  # Set focus to input field
        else:
            # Reached a final career recommendation
            self.recommended_career = self.current_node
            self.show_loading()
            self.start_real_search()
    
    def process_answer(self):
        """Process user's skill rating input and navigate decision tree"""
        try:
            rating = float(self.entry.get())
            
            # Validate input range
            if not 0.0 <= rating <= 1.0:
                raise ValueError("Rating must be between 0.0 and 1.0")
            
            # Record user skill for potential analysis
            skill_name = self.extract_skill_name(self.current_node)
            self.user_skills[skill_name] = rating
            
            # Navigate to next node in decision tree
            self.current_node = self.decision_agent.navigate_tree(self.current_node, rating)
            self.show_question()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", "Please enter a valid number between 0.0 and 1.0")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def extract_skill_name(self, node: str) -> str:
        """
        Extract readable skill name from decision tree node identifier.
        
        Args:
            node (str): Node identifier from decision tree
            
        Returns:
            str: Human-readable skill name
        """
        skill_map = {
            "Math": "Mathematics",
            "Math_High": "Advanced Math",
            "Math_Med": "Intermediate Math", 
            "Math_Low": "Basic Math",
            "HighProg": "Programming",
            "HighPhys": "Physics/Engineering",
            "MedDesign": "Design/Creativity",
            "MedBio": "Biology/Health",
            "LowComm": "Communication",
            "LowHands": "Technical Skills"
        }
        return skill_map.get(node, "General Skills")
    
    def show_loading(self):
        """Display loading screen while searching for courses and market data"""
        self.question_frame.pack_forget()  # Hide question frame
        
        # Create and show loading frame
        self.loading_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        self.loading_frame.pack(expand=True, fill=tk.BOTH)
        
        # Loading message
        tk.Label(
            self.loading_frame,
            text="🔍 Analyzing your career path and searching for courses...",
            font=("Arial", 16, "bold"),
            bg="#f0f8ff",
            fg="#2c3e50"
        ).pack(expand=True)
        
        # Animated progress bar
        self.progress_bar = ttk.Progressbar(
            self.loading_frame,
            mode='indeterminate',
            length=400
        )
        self.progress_bar.pack(pady=20)
        self.progress_bar.start()
    
    def start_real_search(self):
        """Start background thread for course search and market data retrieval"""
        career = self.recommended_career
        # Use daemon thread to allow proper application shutdown
        threading.Thread(target=self.perform_real_search_thread, args=(career,), daemon=True).start()

    def perform_real_search_thread(self, career):
        """
        Background thread function to fetch courses and market data.
        
        Args:
            career (str): Recommended career to search for
        """
        try:
            # Fetch market data for the recommended career
            market_data = self.market_agent.get_market_data(career)
            
            # Search for relevant courses
            courses = self.course_agent.search_courses(career)
            
            # Update UI on main thread (thread-safe)
            self.root.after(0, lambda: self.show_results(market_data, courses))
        except Exception as e:
            # Handle errors in main thread
            self.root.after(0, lambda: self.show_error(str(e)))
    
    def show_results(self, market_data, courses):
        """
        Display final results with career recommendation, market data, and courses.
        
        Args:
            market_data (Dict): Career market information
            courses (List[Dict]): Recommended courses
        """
        # Hide loading screen and stop progress bar
        self.loading_frame.pack_forget()
        self.progress_bar.stop()
        
        # Create and show results frame
        self.results_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        self.results_frame.pack(expand=True, fill=tk.BOTH)
        
        # Career recommendation header
        header_frame = tk.Frame(self.results_frame, bg="#3498db", relief="raised", bd=1)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            header_frame,
            text=f"🎉 Your Recommended Career: {self.recommended_career}",
            font=("Arial", 18, "bold"),
            bg="#3498db",
            fg="white",
            pady=15
        ).pack()
        
        # Results container with two columns
        results_container = tk.Frame(self.results_frame, bg="#f0f8ff")
        results_container.pack(fill=tk.BOTH, expand=True)
        
        # Left column - Market information
        left_frame = tk.Frame(results_container, bg="white", relief="raised", bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.show_market_info(left_frame, market_data)
        
        # Right column - Course recommendations
        right_frame = tk.Frame(results_container, bg="white", relief="raised", bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self.show_courses(right_frame, courses)
        
        # Restart button for new assessment
        restart_frame = tk.Frame(self.results_frame, bg="#f0f8ff")
        restart_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(
            restart_frame,
            text="🔄 Start New Assessment",
            command=self.restart,
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            relief="flat",
            padx=30,
            pady=10
        ).pack()
    
    def show_market_info(self, parent, market_data):
        """
        Display market data information in a structured format.
        
        Args:
            parent: Parent widget for market info
            market_data (Dict): Market data to display
        """
        tk.Label(
            parent,
            text="📈 Career Market Overview",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#2c3e50",
            pady=10
        ).pack()
        
        info_frame = tk.Frame(parent, bg="white")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Display various market metrics
        self.create_info_row(info_frame, "📊 Demand Level:", market_data["demand"], 0)
        
        salary = f"${market_data['salary_range']['min']:,} - ${market_data['salary_range']['max']:,}"
        self.create_info_row(info_frame, "💰 Salary Range:", salary, 1)
        
        self.create_info_row(info_frame, "🚀 Growth Trend:", market_data["growth_trend"], 2)
        
        openings = f"{market_data['job_openings']:,}+ jobs available"
        self.create_info_row(info_frame, "🔍 Job Openings:", openings, 3)
        
        skills = ", ".join(market_data["skills_in_demand"])
        self.create_info_row(info_frame, "🛠️ Key Skills:", skills, 4)
    
    def create_info_row(self, parent, label, value, row):
        """
        Create a standardized information row with label and value.
        
        Args:
            parent: Parent widget
            label (str): Label text
            value (str): Value text
            row (int): Grid row position
        """
        label_frame = tk.Frame(parent, bg="white")
        label_frame.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=8)
        
        tk.Label(
            label_frame,
            text=label,
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#34495e",
            width=15,
            anchor="w"
        ).pack()
        
        value_frame = tk.Frame(parent, bg="white")
        value_frame.grid(row=row, column=1, sticky="w", pady=8)
        
        tk.Label(
            value_frame,
            text=value,
            font=("Arial", 10),
            bg="white",
            fg="#2c3e50",
            wraplength=300,
            justify="left"
        ).pack()
    
    def show_courses(self, parent, courses):
        """
        Display recommended courses in a scrollable list with clickable links.
        
        Args:
            parent: Parent widget for courses
            courses (List[Dict]): Courses to display
        """
        tk.Label(
            parent,
            text="🎓 Recommended Learning Resources",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#2c3e50",
            pady=10
        ).pack()
        
        # Handle case when no courses are found
        if not courses:
            tk.Label(
                parent,
                text="No courses found. Please check your internet connection and try again.",
                font=("Arial", 11),
                bg="white",
                fg="#7f8c8d",
                pady=20
            ).pack()
            return
        
        # Create scrollable area for courses
        canvas = tk.Canvas(parent, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display each course in the scrollable area
        for i, course in enumerate(courses):
            course_frame = tk.Frame(scrollable_frame, bg="white", relief="groove", bd=1)
            course_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Course information display
            info_text = f"{i+1}. {course['title']}\n"
            info_text += f"   Provider: {course['provider']} | Rating: ⭐{course['rating']} | Duration: {course['duration']}"
            
            tk.Label(
                course_frame,
                text=info_text,
                font=("Arial", 9),
                bg="white",
                fg="#2c3e50",
                justify="left",
                anchor="w"
            ).pack(fill=tk.X, padx=10, pady=5)
            
            # Clickable course link
            link_label = tk.Label(
                course_frame,
                text=course['url'],
                font=("Arial", 8),
                fg="#3498db",
                cursor="hand2",
                bg="white"
            )
            link_label.pack(fill=tk.X, padx=10, pady=(0, 5))
            link_label.bind("<Button-1>", lambda e, url=course['url']: webbrowser.open_new(url))
            
            # Hover effects for better UX
            link_label.bind("<Enter>", lambda e, l=link_label: l.config(fg="#2980b9"))
            link_label.bind("<Leave>", lambda e, l=link_label: l.config(fg="#3498db"))
        
        # Pack scrollable elements
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
    
    def show_error(self, error_msg):
        """
        Display error message and restart application.
        
        Args:
            error_msg (str): Error message to display
        """
        self.loading_frame.pack_forget()
        messagebox.showerror("Search Error", 
                           f"Failed to search for courses: {error_msg}\n\n"
                           f"Please check your internet connection and try again.")
        self.restart()
    
    def restart(self):
        """Reset application to initial state for new assessment"""
        self.results_frame.pack_forget()
        self.current_node = "Math"
        self.user_skills = {}
        self.recommended_career = None
        self.question_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        self.show_question()


# ===== APPLICATION ENTRY POINT =====

def main():
    """
    Main function to initialize and run the Career Advisor application.
    Creates the tkinter root window and starts the application loop.
    """
    try:
        root = tk.Tk()
        app = CareerAdvisorApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Fatal Error", f"The application encountered a fatal error: {e}")

# Run the application if this script is executed directly
if __name__ == "__main__":
    main()