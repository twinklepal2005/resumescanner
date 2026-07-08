
AI Resume Analyzer

Overview
AI Resume Analyzer is a Streamlit based web application that evaluates resumes against a given job description using Google's Gemini API. The application supports both job seekers and recruiters by providing resume analysis, eligibility scoring, skill gap analysis, and personalized recommendations.
The application accepts resumes in PDF, DOCX, JPG, and PNG formats. It extracts text using OCR when necessary and generates detailed reports that can be downloaded as PDF files.

Features
Two user modes: Job Seeker and Recruiter
Resume upload support
PDF
DOCX
JPG
PNG
OCR based text extraction for scanned resumes
AI powered resume evaluation using Gemini
Eligibility score calculation
Skills assessment
Experience assessment
Education assessment
Skill gap analysis
Improvement suggestions
Recruiter dashboard for ranking multiple candidates
Downloadable PDF reports

Technology Stack
Python
Streamlit
Google Gemini API
pdfplumber
docx2txt
pdf2image
Pytesseract OCR
Pillow
ReportLab
Requests
JSON
Regular Expressions

Project Structure


Resume-Analyzer/
│
├── app.py
├── .env
├── requirements.txt
├── recruiter_report.pdf
├── job_seeker_report.pdf
└── README.md


Application Workflow

Job Seeker
Upload a resume.
Enter the job description.
The application extracts text from the resume.
Gemini analyzes the resume against the job description.
The application displays:
Eligibility Score
Skills Score
Experience Score
Education Score
Reason for Evaluation
Skill Gap Analysis
Suggestions for Improvement
The user can download a personalized PDF report.

Recruiter
Upload multiple resumes.
Enter the job description.
Each resume is analyzed using Gemini.
Candidates are ranked according to their eligibility score.
A recruiter report containing candidate summaries is generated and can be downloaded.
Supported File Formats
PDF
DOCX
JPG
PNG
OCR Support
For scanned PDF files and images, the application uses Tesseract OCR to extract text before analysis.

Requirements
Python 3.9 or later
Tesseract OCR installed on the system
Google Gemini API Key
Installation

Clone the repository.
git clone https://github.com/twinklepal2005/<repository-name>.git

Move into the project directory.
cd <repository-name>

Install the required dependencies.
pip install -r requirements.txt

Create a .env file.
GEMINI_API_KEY=your_api_key_here

Update the Tesseract path if required.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

Running the Application

Start the Streamlit application.
streamlit run app.py


The application will open in your default browser.

Repository Contents

Included
Application source code
PDF report generation
OCR support
Gemini integration
Documentation

Not Included
Google Gemini API Key
Sample resumes
Future Enhancements
Support for additional resume formats
Resume keyword optimization
ATS compatibility analysis
Resume parsing using structured extraction
Resume comparison dashboard
Interview question generation
Candidate analytics dashboard

Author

Twinkle Pal

BCA Student

CHRIST (Deemed to be University)

License

This project is intended for educational and research purposes.

