import os

# Sample Job Description 1: Senior Backend Engineer
jd_backend = """Title: Senior Backend Engineer
Company: CloudScale Systems

Job Overview:
We are looking for a Senior Backend Engineer to join our high-scale cloud platform engineering team. You will be responsible for building robust REST microservices, optimizing database queries, and maintaining containerized deployment pipelines.

Key Responsibilities:
- Design and develop scalable backend APIs using Python and FastAPI / Flask.
- Manage and optimize PostgreSQL and Redis datastores.
- Containerize application workloads using Docker and deploy on AWS / Kubernetes.
- Collaborate with frontend engineers and maintain CI/CD automation pipelines.

Requirements & Qualifications:
- 4+ years of hands-on experience in Python backend development.
- Strong proficiency with SQL databases (PostgreSQL), Docker, and REST APIs.
- Experience with Cloud Platforms (AWS or GCP) and Git version control.
- Bachelor's degree in Computer Science or Software Engineering.
"""

# Sample Job Description 2: Lead Data Scientist
jd_ds = """Title: Lead Data Scientist
Company: Insight AI

Job Overview:
Insight AI is seeking a Lead Data Scientist to drive machine learning model development, natural language processing pipelines, and data analytics architectures.

Key Responsibilities:
- Build, evaluate, and deploy Machine Learning and NLP models in Python.
- Analyze large datasets using PyTorch, TensorFlow, Pandas, and Scikit-Learn.
- Build automated feature engineering and model scoring pipelines on AWS.

Requirements & Qualifications:
- Master's or PhD in Data Science, Computer Science, or Statistics.
- 5+ years of ML modeling experience in Python, PyTorch, SQL, and NLP.
- Strong background in data modeling and statistics.
"""

os.makedirs("samples/job_descriptions", exist_ok=True)
os.makedirs("samples/resumes", exist_ok=True)

with open("samples/job_descriptions/senior_backend_engineer.txt", "w") as f:
    f.write(jd_backend)

with open("samples/job_descriptions/lead_data_scientist.txt", "w") as f:
    f.write(jd_ds)

# Resume 1: Strong Backend Engineer (TXT)
r1 = """John Doe
Email: john.doe@email.com
Phone: (555) 123-4567

PROFESSIONAL SUMMARY
Senior Backend Engineer with 5+ years of experience designing scalable microservices in Python, FastAPI, and PostgreSQL. Proven track record in Docker containerization, AWS cloud deployments, and CI/CD pipelines.

WORK EXPERIENCE
Senior Backend Developer | TechCorp Inc. (2021 - Present)
- Developed and maintained 15+ FastAPI REST microservices serving 2M daily active users.
- Optimized PostgreSQL database queries, reducing API latency by 45%.
- Implemented Docker containerization and automated deployments using Git and AWS.

Software Engineer | CodeLabs Solutions (2019 - 2021)
- Built Python and Flask backend services for enterprise e-commerce platform.
- Managed Redis caching layers and REST API endpoints.

SKILLS
Technical Skills: Python, FastAPI, Flask, PostgreSQL, SQL, Docker, Redis, REST API, Git, AWS, CI/CD, Microservices
Soft Skills: Leadership, Problem Solving, Agile, Communication

EDUCATION
B.S. in Computer Science | Stanford University (2019)
"""

# Resume 2: Moderate Match / Data Engineer (TXT)
r2 = """Alice Smith
Email: alice.smith@datapipeline.io

SUMMARY
Data Engineer with 3 years of experience in Python, Apache Spark, and SQL database pipelines. Interested in transitioning into backend API engineering.

EXPERIENCE
Data Engineer | BigData Corp (2021 - Present)
- Built ETL pipelines using Python, SQL, and PostgreSQL.
- Utilized Docker for local data pipeline orchestration and Git for version control.

SKILLS
Python, SQL, PostgreSQL, Docker, Git, Pandas, PySpark, Data Pipelines

EDUCATION
M.S. in Data Analytics | UC Berkeley (2021)
"""

# Resume 3: Weak Match / Frontend Developer (TXT)
r3 = """Bob Johnson
Email: bob.j@designstudio.org

SUMMARY
Frontend UI Developer with 2 years of experience crafting responsive web apps using HTML5, CSS3, React, and JavaScript.

WORK EXPERIENCE
Frontend Developer | WebCraft Studio (2022 - Present)
- Designed user interfaces in React.js and CSS.
- Collaborated with designers to deliver responsive web applications.

SKILLS
React, JavaScript, HTML5, CSS3, Vue.js, UI/UX Design, Figma

EDUCATION
B.A. in Visual Design | New York University (2022)
"""

with open("samples/resumes/john_doe_backend.txt", "w") as f:
    f.write(r1)

with open("samples/resumes/alice_smith_data.txt", "w") as f:
    f.write(r2)

with open("samples/resumes/bob_johnson_frontend.txt", "w") as f:
    f.write(r3)

print("Sample dataset created successfully!")
