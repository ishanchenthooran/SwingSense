# SwingSense 🏌️‍♂️
---
## Visuals
![App Preview](./screenshots/SS-home.png)
![App Preview](./screenshots/SS-logs.png) 
![App Preview](./screenshots/SS-plans.png) 

---
## Inspiration  
Golf has been a part of my life since I was five years old, and over the years, I’ve progressed from a beginner to becoming a competitive player. Along the way, I’ve faced challenges at every stage of the game, from struggling to hit consistent shots to refining advanced techniques.  

Since starting university, it hasn’t been as easy to get rounds in and stay on the course as much as I’d like. I wanted a way to stay connected to the game while continuing to improve. Without professional lessons, self-learning can be frustrating—finding actionable feedback isn’t always easy.  

This inspired me to create **SwingSense**:an AI-powered coaching platform built not just for myself, but for golfers of all skill levels, to provide personalized feedback, training plans, and resources that make improvement more accessible and effective.  

---

## What It Does  
**SwingSense** is an AI-powered golf coaching application that combines retrieval-augmented generation (RAG) with personalized feedback. Answers are grounded in a curated golf knowledge corpus — not generated from open-domain model knowledge — making responses more accurate and defensible. The platform allows golfers to:  
- Ask swing-related questions and receive instant, grounded advice cited from golf instruction material.  
- Generate custom 4-week training plans based on handicap, experience, and goals.  
- Access AI-curated resources including drills, videos, and articles targeted to swing issues.  
- Track progress and review improvement over time through a secure user dashboard.  

---

## Core Features  
- **RAG-Powered Q&A** – Answers grounded in a curated golf corpus via FAISS vector retrieval + GPT-4o-mini.  
- **Training Plan Generation** – Custom 4-week plans tailored to skill level and goals.  
- **Curated Resources** – Drills, videos, and articles matched to swing challenges.  
- **Progress Tracking** – Review Q&A history and training logs over time.  
- **User Authentication** – Secure login/signup with Supabase.  

---

## Tech Stack  

### Frontend  
- **Next.js 14 (App Router)**  
- **React 18** with **TypeScript**  
- **Tailwind CSS**  
- **Supabase** for authentication  
- **Axios** for API calls  
- **Lucide React** for icons  

### Backend  
- **FastAPI (Python)**  
- **PostgreSQL** with **SQLAlchemy ORM**  
- **Alembic** for migrations  
- **OpenAI GPT-4o-mini** for response generation  
- **OpenAI text-embedding-3-small** for document and query embeddings  
- **FAISS (IndexFlatIP)** for cosine similarity vector search  
- **RAG pipeline** — PDF preprocessing → chunking → embedding → FAISS index → retrieval → grounded response  
- **Supabase JWT authentication**  
- **Pydantic** for validation  

---

## Deployment  
- **Frontend**: Vercel (Next.js optimized)  
- **Backend**: Render or similar cloud platform  
- **Database**: Cloud-hosted PostgreSQL (e.g., Supabase, NeonDB, RDS)  

---

## Future Enhancements  
- **Computer Vision Swing Analysis** – Use OpenCV + MediaPipe to analyze swings and compare against professional benchmarks.  
- **Social Features** – Enable golfers to connect, share progress, and learn from each other.  

---
