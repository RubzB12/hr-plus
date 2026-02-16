"""
Test script for resume parsing functionality.

This script tests the resume parser with sample text data.
"""

import os
import sys
from io import BytesIO

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.resume_parser import ResumeParser


def create_sample_resume_pdf():
    """Create a sample PDF resume for testing."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Sample resume content
    resume_text = [
        "JOHN DOE",
        "john.doe@example.com | (555) 123-4567",
        "San Francisco, CA",
        "linkedin.com/in/johndoe",
        "",
        "PROFESSIONAL SUMMARY",
        "Experienced Senior Software Engineer with 8+ years of experience in full-stack",
        "web development. Expertise in Python, JavaScript, and cloud technologies.",
        "",
        "SKILLS",
        "Python, Django, React, Node.js, PostgreSQL, AWS, Docker, Kubernetes,",
        "REST API, GraphQL, Git, CI/CD, Agile, Scrum, Machine Learning, TensorFlow",
        "",
        "WORK EXPERIENCE",
        "",
        "Senior Software Engineer at Tech Corp",
        "January 2020 - Present",
        "• Led development of microservices architecture serving 1M+ users",
        "• Implemented CI/CD pipeline reducing deployment time by 60%",
        "• Mentored team of 5 junior developers",
        "",
        "Software Engineer at Startup Inc",
        "June 2016 - December 2019",
        "• Built REST APIs using Django and PostgreSQL",
        "• Developed React frontend applications",
        "• Integrated third-party payment gateways",
        "",
        "EDUCATION",
        "",
        "Bachelor of Science in Computer Science",
        "University of California, Berkeley",
        "2012 - 2016, GPA: 3.8",
        "",
        "Master of Science in Computer Science",
        "Stanford University",
        "2016 - 2018",
    ]

    y = height - 40
    for line in resume_text:
        c.drawString(40, y, line)
        y -= 15
        if y < 40:
            break

    c.save()
    buffer.seek(0)
    return buffer


def test_resume_parser():
    """Test the ResumeParser with sample data."""
    print("=" * 60)
    print("Resume Parser Test")
    print("=" * 60)

    # Create sample PDF
    print("\n1. Creating sample resume PDF...")
    pdf_buffer = create_sample_resume_pdf()
    resume_file = SimpleUploadedFile(
        "sample_resume.pdf",
        pdf_buffer.read(),
        content_type="application/pdf"
    )
    pdf_buffer.seek(0)  # Reset for re-reading
    print(f"   ✓ Created PDF ({len(pdf_buffer.getvalue())} bytes)")

    # Parse the resume
    print("\n2. Parsing resume...")
    result = ResumeParser.parse_resume(resume_file)

    # Display results
    print("\n3. Parsing Results:")
    print("-" * 60)

    print("\n📧 CONTACT INFORMATION:")
    contact = result['contact']
    print(f"   Email: {contact.get('email') or 'Not found'}")
    print(f"   Phone: {contact.get('phone') or 'Not found'}")
    print(f"   LinkedIn: {contact.get('linkedin') or 'Not found'}")
    print(f"   Location: {contact.get('location') or 'Not found'}")

    print("\n💼 WORK EXPERIENCE:")
    experiences = result['experiences']
    if experiences:
        for i, exp in enumerate(experiences, 1):
            print(f"\n   {i}. {exp.get('title', 'N/A')}")
            print(f"      Company: {exp.get('company', 'N/A')}")
            print(f"      Dates: {exp.get('start_date', 'N/A')} to {exp.get('end_date') or 'Present'}")
            print(f"      Current: {exp.get('is_current', False)}")
    else:
        print("   No work experience found")

    print("\n🎓 EDUCATION:")
    education = result['education']
    if education:
        for i, edu in enumerate(education, 1):
            print(f"\n   {i}. {edu.get('degree', 'N/A')}")
            print(f"      Institution: {edu.get('institution', 'N/A')}")
            print(f"      Field: {edu.get('field_of_study', 'N/A')}")
            print(f"      Dates: {edu.get('start_date', 'N/A')} to {edu.get('end_date', 'N/A')}")
            if edu.get('gpa'):
                print(f"      GPA: {edu['gpa']}")
    else:
        print("   No education found")

    print("\n🛠️ SKILLS:")
    skills = result['skills']
    if skills:
        print(f"   Found {len(skills)} skills:")
        for skill in sorted(skills):
            print(f"   • {skill}")
    else:
        print("   No skills found")

    print("\n📄 SUMMARY:")
    summary = result.get('summary', '')
    if summary:
        print(f"   {summary[:200]}...")
    else:
        print("   No summary extracted")

    print("\n📝 RAW TEXT (first 500 chars):")
    raw_text = result.get('raw_text', '')
    if raw_text:
        print(f"   {raw_text[:500]}...")
    else:
        print("   No text extracted")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✓ Contact fields extracted: {sum(1 for v in contact.values() if v)}/4")
    print(f"✓ Work experiences found: {len(experiences)}")
    print(f"✓ Education entries found: {len(education)}")
    print(f"✓ Skills extracted: {len(skills)}")
    print(f"✓ Summary length: {len(summary)} characters")
    print(f"✓ Raw text length: {len(raw_text)} characters")

    # Validation
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)

    passed = 0
    total = 6

    if contact.get('email') == 'john.doe@example.com':
        print("✓ Email extraction: PASS")
        passed += 1
    else:
        print(f"✗ Email extraction: FAIL (got: {contact.get('email')})")

    if contact.get('phone'):
        print(f"✓ Phone extraction: PASS (got: {contact.get('phone')})")
        passed += 1
    else:
        print("✗ Phone extraction: FAIL")

    if contact.get('linkedin'):
        print(f"✓ LinkedIn extraction: PASS (got: {contact.get('linkedin')})")
        passed += 1
    else:
        print("✗ LinkedIn extraction: FAIL")

    if len(skills) >= 5:
        print(f"✓ Skills extraction: PASS ({len(skills)} skills)")
        passed += 1
    else:
        print(f"✗ Skills extraction: FAIL (only {len(skills)} skills)")

    if len(experiences) >= 1:
        print(f"✓ Experience extraction: PASS ({len(experiences)} entries)")
        passed += 1
    else:
        print("✗ Experience extraction: FAIL")

    if len(education) >= 1:
        print(f"✓ Education extraction: PASS ({len(education)} entries)")
        passed += 1
    else:
        print("✗ Education extraction: FAIL")

    print("\n" + "=" * 60)
    print(f"FINAL RESULT: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 60)

    return passed == total


if __name__ == '__main__':
    try:
        success = test_resume_parser()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
