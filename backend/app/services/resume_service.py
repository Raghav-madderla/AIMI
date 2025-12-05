import os
import uuid
import json
import re
import hashlib
from typing import Dict, List, Set, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models import Resume
from app.services.vector_store import vector_store
from app.services.rag_service import rag_service
from app.services.embedding_service import embedding_service
from app.services.agents.resume_summary_agent import resume_summary_agent
from app.services.local_llm_service import local_llm_service
from app.core.config import settings
import docx
import io
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat


class ResumeService:
    """Service for processing resumes with Docling and LLM-based domain matching"""
    
    # Define available domains for matching (only these 9 domains)
    ALL_DOMAINS = [
        "Python",
        "SQL",
        "Data Engineering",
        "Data Analysis",
        "Machine Learning",
        "Deep Learning",
        "Artificial Intelligence",
        "System Design",
        "Statistics"
    ]
    
    # For domain matching, we'll use all domains for both technical rounds
    TECHNICAL_DOMAINS = ALL_DOMAINS
    BEHAVIORAL_DOMAINS = []  # No behavioral domains, all are technical
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
        # Initialize Docling converter
        # DocumentConverter can be initialized simply with allowed_formats
        # PdfPipelineOptions seems to cause issues in docling 2.0+, so using defaults
        self.docling_converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF]
        )
    
    @staticmethod
    def compute_file_hash(file_content: bytes) -> str:
        """
        Compute SHA256 hash of file content for deduplication
        
        Args:
            file_content: Binary content of the file
        
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(file_content).hexdigest()
    
    def check_duplicate_resume(self, file_hash: str, db: Session) -> Optional[Resume]:
        """
        Check if a resume with the same hash already exists
        
        Args:
            file_hash: SHA256 hash of the file
            db: Database session
        
        Returns:
            Existing Resume object if found, None otherwise
        """
        return db.query(Resume).filter(Resume.file_hash == file_hash).first()
    
    def _extract_text_from_pdf(self, file_content: bytes, file_path: str) -> str:
        """Extract text from PDF file using Docling"""
        # Save temporary file for Docling
        temp_path = file_path + ".temp"
        with open(temp_path, "wb") as f:
            f.write(file_content)
        
        try:
            # Convert PDF using Docling
            result = self.docling_converter.convert(temp_path)
            # Extract text from document
            text_content = result.document.export_to_markdown() if hasattr(result.document, 'export_to_markdown') else str(result.document)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return text_content
        except Exception as e:
            # Fallback: try reading as text
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise ValueError(f"Error parsing PDF with Docling: {str(e)}")
    
    def _extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        doc_file = io.BytesIO(file_content)
        doc = docx.Document(doc_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    def _parse_resume_text(self, text: str) -> Dict:
        """Parse resume text to extract structured information"""
        lines = text.split("\n")
        
        skills = []
        experience = []
        education = []
        
        # Enhanced skill keywords
        skill_keywords = [
            "python", "java", "sql", "javascript", "react", "node", "typescript",
            "machine learning", "data science", "aws", "docker", "kubernetes",
            "tensorflow", "pytorch", "flask", "django", "fastapi", "spring",
            "mongodb", "postgresql", "redis", "elasticsearch", "kafka",
            "gcp", "azure", "terraform", "ansible", "jenkins", "git"
        ]
        
        for line in lines:
            line_lower = line.lower()
            # Extract skills
            for skill in skill_keywords:
                if skill in line_lower and skill.title() not in skills:
                    skills.append(skill.title())
            
            # Extract sections
            if any(keyword in line_lower for keyword in ["experience", "work", "employment", "career"]):
                experience.append(line)
            elif any(keyword in line_lower for keyword in ["education", "academic", "degree", "university"]):
                education.append(line)
        
        return {
            "full_text": text,
            "skills": skills[:15],  # Limit to 15 skills
            "experience": experience[:5],
            "education": education[:3]
        }
    
    def _identify_sections(self, text: str) -> Dict[str, str]:
        """
        Identify resume sections and extract their content
        
        Returns:
            Dictionary mapping section names to their content
        """
        lines = text.split('\n')
        sections = {}
        current_section = None
        current_content = []
        
        # Common section headings patterns
        section_keywords = {
            'summary': ['summary', 'profile', 'objective', 'about'],
            'experience': ['experience', 'work experience', 'employment', 'work history', 'career'],
            'education': ['education', 'academic', 'qualifications', 'degrees'],
            'projects': ['projects', 'project', 'portfolio'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise'],
            'certifications': ['certifications', 'certificates', 'certification'],
            'achievements': ['achievements', 'awards', 'honors', 'accomplishments'],
            'publications': ['publications', 'papers', 'research']
        }
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            line_lower = line_stripped.lower()
            
            # Check if this line is a section heading
            is_heading = False
            for section_name, keywords in section_keywords.items():
                # Check if line starts with a section keyword (possibly followed by colon or dash)
                for keyword in keywords:
                    if (line_lower.startswith(keyword) or 
                        line_lower == keyword or
                        keyword in line_lower and len(line_lower) < len(keyword) + 20):  # Short line likely a heading
                        # This is a section heading
                        if current_section and current_content:
                            # Save previous section
                            sections[current_section] = '\n'.join(current_content)
                        current_section = section_name
                        current_content = []
                        is_heading = True
                        break
                if is_heading:
                    break
            
            if not is_heading:
                if current_section:
                    current_content.append(line_stripped)
                else:
                    # Content before any section identified - likely summary/profile
                    if 'summary' not in sections:
                        current_section = 'summary'
                        current_content = [line_stripped]
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _parse_section_entries(self, section_name: str, section_content: str) -> List[str]:
        """
        Parse individual entries within a section
        
        Args:
            section_name: Name of the section
            section_content: Content of the section
        
        Returns:
            List of individual entry strings (each is a child chunk)
        """
        entries = []
        
        if section_name == 'experience':
            # Each job/role is typically separated by:
            # - Dates (e.g., "2020 - 2023")
            # - Company names
            # - Job titles
            lines = section_content.split('\n')
            current_entry = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Heuristic: New entry if line starts with date pattern or company name pattern
                # (Job titles often preceded by dates or companies)
                is_new_entry = False
                
                # Check for date patterns (YYYY - YYYY, MM/YYYY, etc.)
                date_pattern = r'(\d{4}|\d{1,2}[/-]\d{4})'
                if re.search(date_pattern, line) and len(line) < 50:
                    is_new_entry = True
                
                # If we have content and encounter what looks like a new entry
                if is_new_entry and current_entry:
                    entries.append('\n'.join(current_entry))
                    current_entry = [line]
                else:
                    current_entry.append(line)
            
            if current_entry:
                entries.append('\n'.join(current_entry))
        
        elif section_name == 'education':
            # Each degree/institution is an entry
            lines = section_content.split('\n')
            current_entry = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_entry:
                        entries.append('\n'.join(current_entry))
                        current_entry = []
                    continue
                
                # New entry if line starts with degree name or university
                # (Often degrees are on their own line)
                if current_entry and (line.lower().startswith(('bachelor', 'master', 'phd', 'doctorate')) or 
                                     any(word in line.lower() for word in ['university', 'college', 'institute'])):
                    entries.append('\n'.join(current_entry))
                    current_entry = [line]
                else:
                    current_entry.append(line)
            
            if current_entry:
                entries.append('\n'.join(current_entry))
        
        elif section_name == 'projects':
            # Each project is an entry
            lines = section_content.split('\n')
            current_entry = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_entry:
                        entries.append('\n'.join(current_entry))
                        current_entry = []
                    continue
                
                # Project names are often standalone lines or start with bullet points
                if line.startswith(('*', '-', '*', '')) or (len(line) < 100 and current_entry):
                    if current_entry and not line.startswith(('*', '-', '*', '')):
                        entries.append('\n'.join(current_entry))
                        current_entry = [line]
                    else:
                        current_entry.append(line)
                else:
                    current_entry.append(line)
            
            if current_entry:
                entries.append('\n'.join(current_entry))
        
        else:
            # For other sections (summary, skills, etc.), split by paragraphs or bullets
            if section_content:
                # Split by double newlines (paragraphs)
                paragraphs = section_content.split('\n\n')
                entries = [p.strip() for p in paragraphs if p.strip()]
                
                # If no paragraphs, try splitting by bullet points
                if len(entries) == 1:
                    bullets = entries[0].split('\n')
                    entries = [b.strip() for b in bullets if b.strip() and 
                              (b.strip().startswith(('*', '-', '*', '')) or len(b.strip()) > 20)]
        
        return entries
    
    def _chunk_resume_hierarchically(self, text: str) -> List[Dict[str, str]]:
        """
        Chunk resume hierarchically: sections as parents, entries as children
        
        Returns:
            List of chunk dictionaries with:
            - text: chunk content
            - parent_section: section name (e.g., "experience", "education")
            - chunk_type: "section" for parent, "entry" for child
            - entry_index: index within section (for entries)
        """
        chunks = []
        
        # Identify sections
        sections = self._identify_sections(text)
        
        for section_name, section_content in sections.items():
            # Add section header as parent chunk (optional - for context)
            # For now, we'll skip parent chunks and only store entries
            
            # Parse entries within section
            entries = self._parse_section_entries(section_name, section_content)
            
            if not entries:
                # If no entries parsed, use entire section as one chunk
                entries = [section_content]
            
            # Each entry is a child chunk
            for idx, entry in enumerate(entries):
                if entry.strip():  # Only add non-empty entries
                    chunks.append({
                        'text': entry.strip(),
                        'parent_section': section_name,
                        'chunk_type': 'entry',
                        'entry_index': idx
                    })
        
        return chunks
    
    async def _match_chunk_to_domains(self, chunk: str, round_type: str = "technical") -> List[str]:
        """
        Use LLM to match a chunk to relevant domains
        
        Args:
            chunk: Text chunk from resume
            round_type: "technical" or "behavioral"
        
        Returns:
            List of matched domain names
        """
        available_domains = self.TECHNICAL_DOMAINS if round_type == "technical" else self.BEHAVIORAL_DOMAINS
        
        prompt = f"""Analyze the following resume chunk and identify which domain(s) it relates to.

Resume Chunk:
{chunk[:1000]}

Available Domains:
{', '.join(available_domains)}

Return a JSON object with a "domains" key containing an array of domain names that this chunk is relevant to. Only include domains that are clearly mentioned or strongly related to the content.

Example response: {{"domains": ["Python", "Data Engineering"]}}

Response:"""
        
        try:
            messages = [
                {"role": "system", "content": "You are a domain classification expert. Return only valid JSON objects with a 'domains' key containing an array of domain names."},
                {"role": "user", "content": prompt}
            ]
            
            result = await local_llm_service.generate_json_async(messages, max_new_tokens=200, temperature=0.3)
            
            if result:
                # Extract domains array from JSON object
                domains = result.get("domains", [])
                if isinstance(domains, str):
                    domains = [domains]
                elif not isinstance(domains, list):
                    domains = []
                
                # Filter to only include valid domains
                matched_domains = [d for d in domains if d in available_domains]
                return matched_domains[:3]  # Limit to 3 domains per chunk
            else:
                # Fallback: simple keyword matching
                chunk_lower = chunk.lower()
                matched_domains = [d for d in available_domains if d.lower() in chunk_lower]
                return matched_domains[:3] if matched_domains else ["Python"]
                
        except Exception as e:
            # Fallback: simple keyword matching
            chunk_lower = chunk.lower()
            matched_domains = [d for d in available_domains if d.lower() in chunk_lower]
            return matched_domains[:3] if matched_domains else ["Python"]  # Default fallback
    
    async def process_resume(
        self,
        file: UploadFile,
        job_role: str,
        user_id: str,
        db: Session
    ) -> Dict:
        """Process uploaded resume: parse with Docling, chunk, match domains with LLM, and store"""
        # Read file content
        file_content = await file.read()
        file_extension = file.filename.split(".")[-1].lower()
        
        # Compute hash for deduplication
        file_hash = self.compute_file_hash(file_content)
        
        # Check if this resume already exists
        existing_resume = self.check_duplicate_resume(file_hash, db)
        if existing_resume:
            return {
                "resume_id": existing_resume.resume_id,
                "skills": existing_resume.skills or [],
                "num_chunks": existing_resume.chunks_metadata.get("num_chunks", 0) if existing_resume.chunks_metadata else 0,
                "matched_domains": existing_resume.chunks_metadata.get("matched_domains", []) if existing_resume.chunks_metadata else [],
                "sections": [],
                "resume_summary": existing_resume.chunks_metadata.get("resume_summary", {}) if existing_resume.chunks_metadata else {},
                "duplicate": True,
                "original_upload_date": existing_resume.created_at.isoformat() if existing_resume.created_at else None
            }
        
        # Save file first
        resume_id = str(uuid.uuid4())
        file_path = os.path.join(self.upload_dir, f"{resume_id}.{file_extension}")
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Extract text based on file type
        if file_extension == "pdf":
            text = self._extract_text_from_pdf(file_content, file_path)
        elif file_extension in ["docx", "doc"]:
            text = self._extract_text_from_docx(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Parse resume
        parsed_content = self._parse_resume_text(text)
        
        # Chunk resume hierarchically (sections -> entries)
        hierarchical_chunks = self._chunk_resume_hierarchically(parsed_content["full_text"])
        
        # Process chunks: match domains and generate embeddings
        chunk_ids = []
        all_matched_domains = set()  # Track all domains found in resume
        chunk_domain_map = {}  # Store domain matches for each chunk
        
        # First pass: Match domains for all chunks
        for i, chunk_data in enumerate(hierarchical_chunks):
            chunk_text = chunk_data['text']
            chunk_id = f"{resume_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            
            # Match chunk to required domains (all 9 domains are technical)
            matched_domains = await self._match_chunk_to_domains(chunk_text, "technical")
            
            # If no match, assign to a default domain (Python as fallback)
            if not matched_domains:
                matched_domains = ["Python"]  # Default fallback to first required domain
            
            chunk_domain_map[i] = matched_domains
            all_matched_domains.update(matched_domains)
        
        # Generate embeddings for all chunks in batch (more efficient)
        chunk_texts = [chunk_data['text'] for chunk_data in hierarchical_chunks]
        embeddings = await embedding_service.embed_texts(chunk_texts)
        
        # Store chunks with embeddings
        for i, (chunk_data, embedding) in enumerate(zip(hierarchical_chunks, embeddings)):
            chunk_text = chunk_data['text']
            chunk_id = f"{resume_id}_chunk_{i}"
            
            # Get matched domains (already computed in first pass)
            matched_domains = chunk_domain_map[i]
            
            # Store in vector DB with hierarchical and domain metadata
            vector_store.add_documents(
                documents=[chunk_text],
                ids=[chunk_id],
                metadatas=[{
                    "resume_id": resume_id,
                    "chunk_index": i,
                    "job_role": job_role,
                    "parent_section": chunk_data.get('parent_section', 'unknown'),
                    "chunk_type": chunk_data.get('chunk_type', 'entry'),
                    "entry_index": chunk_data.get('entry_index', 0),
                    "domains": matched_domains,  # List of matched domains
                    "primary_domain": matched_domains[0] if matched_domains else "Python"  # Primary domain
                }],
                embeddings=[embedding]
            )
        
        # Generate resume summary using the Resume Summary Agent
        resume_summary_result = await resume_summary_agent(
            resume_text=parsed_content["full_text"],
            job_role=job_role
        )
        
        # Check if summary generation was successful
        if resume_summary_result and not resume_summary_result.get("error"):
            # If 'success' key exists and is False, use the fallback summary
            if resume_summary_result.get("success") is False:
                resume_summary = resume_summary_result.get("summary_points", [])
            else:
                # Direct return from successful generation
                resume_summary = resume_summary_result
        else:
            print(f"Resume summary generation failed: {resume_summary_result.get('error', 'Unknown error')}")
            resume_summary = {}
        
        # Save resume metadata to database with file hash
        resume = Resume(
            resume_id=resume_id,
            user_id=user_id,
            job_role=job_role,
            file_path=file_path,
            file_hash=file_hash,
            parsed_content=parsed_content,
            skills=parsed_content["skills"],
            chunks_metadata={
                "num_chunks": len(hierarchical_chunks),
                "matched_domains": list(all_matched_domains),
                "resume_summary": resume_summary
            },
            vector_store_ids=chunk_ids
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        return {
            "resume_id": resume_id,
            "skills": parsed_content["skills"],
            "num_chunks": len(hierarchical_chunks),
            "matched_domains": list(all_matched_domains),
            "sections": list(set(chunk_data.get('parent_section', 'unknown') 
                               for chunk_data in hierarchical_chunks)),
            "resume_summary": resume_summary,
            "duplicate": False
        }
    
    def get_resume_context(self, resume_id: str, top_k: int = 3) -> str:
        """Get resume context for RAG"""
        return rag_service.get_resume_summary(resume_id, top_k=top_k)


resume_service = ResumeService()
