from pypdf import PdfWriter
from pypdf.annotations import FreeText

# Create a PDF using reportlab or minimal PDF object if available, or write a clean PDF generator script
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    def make_pdf(filename):
        c = canvas.Canvas(filename, pagesize=letter)
        c.drawString(100, 750, "Sarah Connor")
        c.drawString(100, 735, "Email: sarah.connor@devops.net")
        c.drawString(100, 700, "SUMMARY")
        c.drawString(100, 685, "DevOps Engineer with 4 years experience in Docker, Kubernetes, AWS, Python, and CI/CD.")
        c.drawString(100, 650, "EXPERIENCE")
        c.drawString(100, 635, "DevOps Specialist - Cyberdyne Inc (2020 - Present)")
        c.drawString(100, 620, "- Managed Kubernetes clusters and AWS infrastructure using Terraform.")
        c.drawString(100, 605, "- Automated Python backend test suites and Docker build pipelines.")
        c.drawString(100, 570, "SKILLS")
        c.drawString(100, 555, "Docker, Kubernetes, AWS, Python, CI/CD, Terraform, Linux, Git, SQL")
        c.drawString(100, 520, "EDUCATION")
        c.drawString(100, 505, "B.S. Information Technology - MIT (2020)")
        c.save()

    make_pdf("samples/resumes/sarah_connor_devops.pdf")
    print("Created PDF resume successfully using reportlab!")
except ImportError:
    # If reportlab isn't installed, let's install reportlab or generate raw minimal PDF bytes
    import sys
    print("Reportlab not installed, installing reportlab...")
