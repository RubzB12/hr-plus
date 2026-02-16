"""
Resume parsing utilities for extracting structured data from PDF resumes.

This module provides comprehensive resume parsing with:
- PDF text extraction
- Contact information extraction (email, phone, LinkedIn)
- Skills extraction
- Work experience extraction
- Education history extraction
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pdfplumber
from dateutil import parser as date_parser
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


class ResumeParser:
    """
    Comprehensive resume parser for PDF files.

    Extracts structured information including:
    - Contact details (email, phone, LinkedIn, location)
    - Skills
    - Work experience
    - Education history
    - Summary/objective
    """

    # Common technical skills keywords
    TECH_SKILLS = {
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php',
        'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'shell',

        # Web Technologies
        'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django',
        'flask', 'fastapi', 'spring', 'laravel', 'rails', 'asp.net', 'jquery',
        'bootstrap', 'tailwind', 'sass', 'webpack', 'babel',

        # Databases
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'dynamodb', 'cassandra', 'oracle', 'sql server', 'sqlite',

        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'circleci',
        'terraform', 'ansible', 'chef', 'puppet', 'ci/cd', 'git', 'github',
        'gitlab', 'bitbucket', 'linux', 'bash',

        # Data Science & AI
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras',
        'scikit-learn', 'pandas', 'numpy', 'data analysis', 'statistics',
        'tableau', 'power bi', 'spark', 'hadoop', 'airflow',

        # Mobile
        'ios', 'android', 'react native', 'flutter', 'xamarin', 'cordova',

        # Other
        'rest api', 'graphql', 'microservices', 'agile', 'scrum', 'jira',
        'api', 'testing', 'selenium', 'jest', 'pytest', 'junit',
    }

    # Education degree keywords
    DEGREE_KEYWORDS = {
        'phd', 'doctorate', 'ph.d', 'doctor',
        'masters', 'master', 'm.s', 'ms', 'm.a', 'ma', 'mba', 'msc',
        'bachelors', 'bachelor', 'b.s', 'bs', 'b.a', 'ba', 'b.tech', 'btech',
        'associate', 'a.s', 'as', 'a.a', 'aa',
        'diploma', 'certificate',
    }

    # Experience section headers
    EXPERIENCE_HEADERS = [
        'experience', 'work experience', 'employment', 'work history',
        'professional experience', 'career history', 'employment history'
    ]

    # Education section headers
    EDUCATION_HEADERS = [
        'education', 'academic background', 'qualifications',
        'educational background', 'academic history'
    ]

    # Skills section headers
    SKILLS_HEADERS = [
        'skills', 'technical skills', 'core competencies', 'expertise',
        'technologies', 'tools', 'programming languages'
    ]

    @staticmethod
    def extract_text_from_pdf(file: UploadedFile) -> str:
        """
        Extract text content from PDF file.

        Args:
            file: Uploaded PDF file

        Returns:
            Extracted text content
        """
        try:
            text = ""
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            logger.info(f"Extracted {len(text)} characters from PDF: {file.name}")
            return text

        except Exception as e:
            logger.error(f"Error extracting text from PDF {file.name}: {e}")
            return ""

    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extract email address from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """Extract phone number from text."""
        # Matches: (123) 456-7890, 123-456-7890, 123.456.7890, +1-123-456-7890
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US/International
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # 123-456-7890
        ]

        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def extract_linkedin(text: str) -> Optional[str]:
        """Extract LinkedIn URL from text."""
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
        match = re.search(linkedin_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    @staticmethod
    def extract_location(text: str) -> Optional[str]:
        """
        Extract location (city, state/country) from text.

        Looks for patterns like:
        - San Francisco, CA
        - New York, NY
        - London, UK
        """
        # Look for City, State/Country pattern in first 500 chars
        location_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2,}|\b[A-Z][a-z]+\b)'
        matches = re.findall(location_pattern, text[:500])

        if matches:
            city, state = matches[0]
            return f"{city}, {state}"
        return None

    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """
        Extract skills from resume text.

        Uses keyword matching against common technical skills.
        Also extracts from "Skills" section if present.
        """
        text_lower = text.lower()
        found_skills = set()

        # Method 1: Find skills from predefined list
        for skill in ResumeParser.TECH_SKILLS:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                # Capitalize properly
                found_skills.add(skill.title() if ' ' in skill else skill.upper() if skill.isupper() else skill.capitalize())

        # Method 2: Extract from Skills section
        for header in ResumeParser.SKILLS_HEADERS:
            header_pattern = rf'\b{header}\b.*?(?=\n\s*\n|\n[A-Z][A-Z\s]+\n|$)'
            match = re.search(header_pattern, text, re.IGNORECASE | re.DOTALL)

            if match:
                skills_section = match.group(0)
                # Extract comma-separated or newline-separated items
                skills_items = re.split(r'[,\n•●▪-]', skills_section)

                for item in skills_items:
                    item = item.strip()
                    # Skip headers and very long items
                    if len(item) > 3 and len(item) < 30 and not any(h in item.lower() for h in ResumeParser.SKILLS_HEADERS):
                        found_skills.add(item.title())

        return sorted(list(found_skills))

    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """
        Parse various date formats and return YYYY-MM-DD.

        Handles formats like:
        - "Jan 2020", "January 2020"
        - "2020", "2019-2020"
        - "Present", "Current"
        """
        date_str = date_str.strip().lower()

        # Handle "Present", "Current"
        if any(word in date_str for word in ['present', 'current', 'now']):
            return None  # Will be marked as is_current=True

        try:
            # Try parsing with dateutil
            parsed_date = date_parser.parse(date_str, fuzzy=True)
            return parsed_date.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            # Try to extract just the year
            year_match = re.search(r'(19|20)\d{2}', date_str)
            if year_match:
                return f"{year_match.group(0)}-01-01"
            return None

    @staticmethod
    def extract_work_experience(text: str) -> List[Dict]:
        """
        Extract work experience entries from resume text.

        Returns list of dicts with:
        - company: str
        - title: str
        - start_date: str (YYYY-MM-DD)
        - end_date: str or None (YYYY-MM-DD)
        - is_current: bool
        - description: str
        """
        experiences = []

        # Find experience section
        experience_section = None
        for header in ResumeParser.EXPERIENCE_HEADERS:
            # Match header and capture until next major section
            pattern = rf'\b{header}\b.*?(?=\n\s*\n[A-Z][A-Z\s]+\n|$)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                experience_section = match.group(0)
                break

        if not experience_section:
            return experiences

        # Split into individual job entries (rough heuristic)
        # Look for patterns like "Company Name" followed by dates
        job_pattern = r'([^\n]+)\n([^\n]+)\n((?:[A-Za-z]+\s+\d{4}|\d{4}).*?(?:Present|Current|[A-Za-z]+\s+\d{4}|\d{4}))'
        matches = re.findall(job_pattern, experience_section, re.IGNORECASE)

        for i, match in enumerate(matches[:10]):  # Limit to 10 experiences
            try:
                line1, line2, date_range = match

                # Determine which line is company vs title
                # Usually: Title at Company or Company - Title
                if ' at ' in line1.lower():
                    title, company = line1.split(' at ', 1)
                elif '-' in line1:
                    parts = line1.split('-', 1)
                    title = parts[0]
                    company = parts[1] if len(parts) > 1 else line2
                else:
                    title = line1.strip()
                    company = line2.strip()

                # Parse dates
                date_parts = re.split(r'[-–—to]', date_range, maxsplit=1)
                start_date_str = date_parts[0].strip()
                end_date_str = date_parts[1].strip() if len(date_parts) > 1 else None

                start_date = ResumeParser.parse_date(start_date_str)
                end_date = ResumeParser.parse_date(end_date_str) if end_date_str else None
                is_current = end_date is None and end_date_str and any(
                    word in end_date_str.lower() for word in ['present', 'current', 'now']
                )

                if start_date:  # Only add if we found a valid start date
                    experiences.append({
                        'company': company.strip(),
                        'title': title.strip(),
                        'start_date': start_date,
                        'end_date': end_date,
                        'is_current': is_current,
                        'description': '',  # Could extract bullet points here
                    })
            except Exception as e:
                logger.warning(f"Failed to parse experience entry {i}: {e}")
                continue

        return experiences

    @staticmethod
    def extract_education(text: str) -> List[Dict]:
        """
        Extract education entries from resume text.

        Returns list of dicts with:
        - institution: str
        - degree: str
        - field_of_study: str
        - start_date: str or None
        - end_date: str or None
        - gpa: float or None
        """
        education_entries = []

        # Find education section
        education_section = None
        for header in ResumeParser.EDUCATION_HEADERS:
            pattern = rf'\b{header}\b.*?(?=\n\s*\n[A-Z][A-Z\s]+\n|$)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                education_section = match.group(0)
                break

        if not education_section:
            return education_entries

        # Look for degree keywords
        for degree_keyword in ResumeParser.DEGREE_KEYWORDS:
            pattern = rf'({degree_keyword}[^\n]*)\n?([^\n]*)\n?((?:[A-Za-z]+\s+)?\d{{4}}(?:\s*[-–]\s*\d{{4}})?)?'
            matches = re.finditer(pattern, education_section, re.IGNORECASE)

            for match in matches:
                try:
                    degree_line = match.group(1)
                    institution_line = match.group(2)
                    date_line = match.group(3) if match.group(3) else ""

                    # Extract GPA if present
                    gpa = None
                    gpa_match = re.search(r'GPA[:\s]*([\d.]+)', degree_line, re.IGNORECASE)
                    if gpa_match:
                        try:
                            gpa = float(gpa_match.group(1))
                        except ValueError:
                            pass

                    # Parse dates
                    dates = re.findall(r'\d{4}', date_line)
                    start_date = f"{dates[0]}-01-01" if len(dates) > 0 else None
                    end_date = f"{dates[1]}-01-01" if len(dates) > 1 else start_date

                    # Extract field of study (usually after "in" or "of")
                    field_match = re.search(r'\b(?:in|of)\s+([A-Z][^\n,]+)', degree_line)
                    field_of_study = field_match.group(1).strip() if field_match else ""

                    education_entries.append({
                        'institution': institution_line.strip(),
                        'degree': degree_line.split(',')[0].strip(),  # Remove GPA part
                        'field_of_study': field_of_study,
                        'start_date': start_date,
                        'end_date': end_date,
                        'gpa': gpa,
                    })

                except Exception as e:
                    logger.warning(f"Failed to parse education entry: {e}")
                    continue

        return education_entries[:5]  # Limit to 5 entries

    @classmethod
    def parse_resume(cls, resume_file: UploadedFile) -> Dict:
        """
        Main entry point: Parse resume file and extract all structured data.

        Args:
            resume_file: Uploaded resume file (PDF)

        Returns:
            Dictionary with extracted data:
            {
                'summary': str,
                'skills': List[str],
                'experiences': List[Dict],
                'education': List[Dict],
                'contact': Dict,
                'raw_text': str
            }
        """
        logger.info(f"Starting resume parse for: {resume_file.name}")

        # Extract raw text
        text = cls.extract_text_from_pdf(resume_file)

        if not text:
            logger.warning(f"No text extracted from resume: {resume_file.name}")
            return {
                'summary': '',
                'skills': [],
                'experiences': [],
                'education': [],
                'contact': {},
                'raw_text': '',
            }

        # Extract all components
        contact = {
            'email': cls.extract_email(text),
            'phone': cls.extract_phone(text),
            'linkedin': cls.extract_linkedin(text),
            'location': cls.extract_location(text),
        }

        skills = cls.extract_skills(text)
        experiences = cls.extract_work_experience(text)
        education = cls.extract_education(text)

        # Extract summary (first few lines, up to 300 chars)
        lines = text.split('\n')
        summary_lines = []
        for line in lines[3:10]:  # Skip first few lines (usually name/contact)
            if line.strip() and len(line) > 20:
                summary_lines.append(line.strip())
                if len(' '.join(summary_lines)) > 300:
                    break

        summary = ' '.join(summary_lines)[:300]

        result = {
            'summary': summary,
            'skills': skills,
            'experiences': experiences,
            'education': education,
            'contact': contact,
            'raw_text': text[:5000],  # Store first 5000 chars
        }

        logger.info(
            f"Resume parsed successfully: {len(skills)} skills, "
            f"{len(experiences)} experiences, {len(education)} education entries"
        )

        return result
